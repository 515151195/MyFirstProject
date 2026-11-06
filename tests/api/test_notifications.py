import pytest
import pytest_asyncio
from httpx import AsyncClient

from models import Notification, User
from tests.factories import create_notification, create_user
from tests.helpers.auth import auth_headers


pytestmark = pytest.mark.integration


@pytest_asyncio.fixture(loop_scope="session")
async def normal_user(seeded_roles) -> User:
    return await create_user(
        username="notification_user",
        email="notification_user@example.com",
        role=seeded_roles.user,
    )


@pytest_asyncio.fixture(loop_scope="session")
async def other_user(seeded_roles) -> User:
    return await create_user(
        username="notification_other",
        email="notification_other@example.com",
        role=seeded_roles.user,
    )


async def test_list_current_user_notifications(
    client: AsyncClient,
    normal_user: User,
    other_user: User,
):
    await create_notification(normal_user, title="For current user")
    await create_notification(other_user, title="For another user")

    response = await client.get(
        "/api/v1/notifications/notifications",
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert [item["title"] for item in data] == ["For current user"]


async def test_empty_notification_list_returns_404(
    client: AsyncClient,
    normal_user: User,
):
    response = await client.get(
        "/api/v1/notifications/notifications",
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 404


async def test_user_can_mark_own_notification_as_read(
    client: AsyncClient,
    normal_user: User,
):
    notification = await create_notification(normal_user)

    response = await client.patch(
        f"/api/v1/notifications/{notification.id}/read",
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 200
    await notification.refresh_from_db()
    assert notification.is_read is True


async def test_user_cannot_mark_another_users_notification_as_read(
    client: AsyncClient,
    normal_user: User,
    other_user: User,
):
    notification = await create_notification(other_user)

    response = await client.patch(
        f"/api/v1/notifications/{notification.id}/read",
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 403
    await notification.refresh_from_db()
    assert notification.is_read is False


async def test_missing_notification_returns_404(
    client: AsyncClient,
    normal_user: User,
):
    response = await client.patch(
        "/api/v1/notifications/999999/read",
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 404
