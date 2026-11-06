from __future__ import annotations

from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient

from models import Role, User
from tests.helpers.auth import auth_headers
from utils.password import hash_password


pytestmark = pytest.mark.integration

DEFAULT_PASSWORD = "Password123"


async def create_user(
    username: str,
    email: str,
    role: Role,
    *,
    is_active: bool = True,
    is_superuser: bool = False,
) -> User:
    user = await User.create(
        username=username,
        email=email,
        password=hash_password(DEFAULT_PASSWORD),
        is_active=is_active,
        is_superuser=is_superuser,
    )
    await user.roles.add(role)
    return user


@pytest_asyncio.fixture(loop_scope="session")
async def admin_user(seeded_roles) -> User:
    return await create_user(
        username="admin_test",
        email="admin_test@example.com",
        role=seeded_roles.admin,
        is_superuser=True,
    )


@pytest_asyncio.fixture(loop_scope="session")
async def normal_user(seeded_roles) -> User:
    return await create_user(
        username="alice",
        email="alice@example.com",
        role=seeded_roles.user,
    )


@pytest_asyncio.fixture(loop_scope="session")
async def other_user(seeded_roles) -> User:
    return await create_user(
        username="bob",
        email="bob@example.com",
        role=seeded_roles.user,
    )


def response_data(response) -> Any:
    body = response.json()
    assert body["code"] == response.status_code
    return body["data"]


async def test_current_user_requires_authentication(client: AsyncClient):
    response = await client.get("/api/v1/users/me")

    assert response.status_code in (401, 403)


async def test_get_current_user_info(
    client: AsyncClient,
    normal_user: User,
):
    response = await client.get(
        "/api/v1/users/me",
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 200
    data = response_data(response)
    assert data["id"] == normal_user.id
    assert data["username"] == normal_user.username
    assert data["email"] == normal_user.email
    assert "password" not in data


async def test_search_user_by_id(
    client: AsyncClient,
    normal_user: User,
):
    response = await client.get(
        "/api/v1/users/user",
        params={"user_id": normal_user.id},
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 200
    assert response_data(response)["username"] == normal_user.username


async def test_search_user_by_username(
    client: AsyncClient,
    normal_user: User,
):
    response = await client.get(
        "/api/v1/users/user",
        params={"username": normal_user.username},
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 200
    assert response_data(response)["id"] == normal_user.id


async def test_search_user_requires_an_identifier(
    client: AsyncClient,
    normal_user: User,
):
    response = await client.get(
        "/api/v1/users/user",
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 400


async def test_list_users_with_keyword_and_pagination(
    client: AsyncClient,
    normal_user: User,
    other_user: User,
):
    response = await client.get(
        "/api/v1/users/users",
        params={"keyword": "ali", "page": 1, "page_size": 1},
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["extra_data"] == 1
    assert [item["username"] for item in body["data"]] == ["alice"]


async def test_change_username(
    client: AsyncClient,
    normal_user: User,
):
    response = await client.patch(
        "/api/v1/users/username",
        json="alice_renamed",
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 200
    assert response_data(response)["username"] == "alice_renamed"
    assert await User.filter(id=normal_user.id, username="alice_renamed").exists()


async def test_change_username_rejects_duplicate(
    client: AsyncClient,
    normal_user: User,
    other_user: User,
):
    response = await client.patch(
        "/api/v1/users/username",
        json=other_user.username,
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 400


async def test_change_email(
    client: AsyncClient,
    normal_user: User,
):
    response = await client.patch(
        "/api/v1/users/email",
        json="alice_new@example.com",
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 200
    assert response_data(response)["email"] == "alice_new@example.com"
    assert await User.filter(
        id=normal_user.id,
        email="alice_new@example.com",
    ).exists()


async def test_change_email_rejects_duplicate(
    client: AsyncClient,
    normal_user: User,
    other_user: User,
):
    response = await client.patch(
        "/api/v1/users/email",
        json=other_user.email,
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 400


async def test_normal_user_cannot_disable_another_user(
    client: AsyncClient,
    normal_user: User,
    other_user: User,
):
    response = await client.patch(
        f"/api/v1/users/disable-user/{other_user.username}",
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 403


async def test_admin_can_disable_user(
    client: AsyncClient,
    admin_user: User,
    other_user: User,
):
    response = await client.patch(
        f"/api/v1/users/disable-user/{other_user.username}",
        headers=auth_headers(admin_user),
    )

    assert response.status_code == 200
    await other_user.refresh_from_db()
    assert other_user.is_active is False


async def test_admin_cannot_disable_self(
    client: AsyncClient,
    admin_user: User,
):
    response = await client.patch(
        f"/api/v1/users/disable-user/{admin_user.username}",
        headers=auth_headers(admin_user),
    )

    assert response.status_code == 400


async def test_admin_can_promote_user_to_superuser(
    client: AsyncClient,
    admin_user: User,
    normal_user: User,
):
    response = await client.patch(
        f"/api/v1/users/set-superuser/{normal_user.username}",
        headers=auth_headers(admin_user),
    )

    assert response.status_code == 200
    await normal_user.refresh_from_db()
    assert normal_user.is_superuser is True
    assert await normal_user.roles.filter(name="admin").exists()


async def test_admin_can_delete_normal_user(
    client: AsyncClient,
    admin_user: User,
    other_user: User,
):
    response = await client.delete(
        f"/api/v1/users/delete/{other_user.id}",
        headers=auth_headers(admin_user),
    )

    assert response.status_code == 200
    assert not await User.filter(id=other_user.id).exists()


async def test_admin_cannot_delete_self(
    client: AsyncClient,
    admin_user: User,
):
    response = await client.delete(
        f"/api/v1/users/delete/{admin_user.id}",
        headers=auth_headers(admin_user),
    )

    assert response.status_code == 400
    assert await User.filter(id=admin_user.id).exists()


async def test_normal_user_cannot_delete_users(
    client: AsyncClient,
    normal_user: User,
    other_user: User,
):
    response = await client.delete(
        f"/api/v1/users/delete/{other_user.id}",
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 403
    assert await User.filter(id=other_user.id).exists()


async def test_delete_me_can_be_cancelled(
    client: AsyncClient,
    normal_user: User,
):
    response = await client.delete(
        "/api/v1/users/delete-me",
        params={"confirmation": "no"},
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 200
    assert await User.filter(id=normal_user.id).exists()


async def test_delete_me_removes_current_user(
    client: AsyncClient,
    normal_user: User,
):
    response = await client.delete(
        "/api/v1/users/delete-me",
        params={"confirmation": "yes"},
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 200
    assert not await User.filter(id=normal_user.id).exists()
