import pytest
import pytest_asyncio
from httpx import AsyncClient

from models import Role, User
from tests.factories import create_user
from tests.helpers.auth import auth_headers


pytestmark = pytest.mark.integration


@pytest_asyncio.fixture(loop_scope="session")
async def admin_user(seeded_roles) -> User:
    return await create_user(
        username="role_admin",
        email="role_admin@example.com",
        role=seeded_roles.admin,
        is_superuser=True,
    )


@pytest_asyncio.fixture(loop_scope="session")
async def normal_user(seeded_roles) -> User:
    return await create_user(
        username="role_user",
        email="role_user@example.com",
        role=seeded_roles.user,
    )


async def test_admin_can_read_role_description(
    client: AsyncClient,
    admin_user: User,
):
    response = await client.get(
        "/api/v1/roles/role_desc",
        params={"name": "admin"},
        headers=auth_headers(admin_user),
    )

    assert response.status_code == 200
    assert response.json()["data"] == "Administrator"


async def test_normal_user_cannot_read_role_description(
    client: AsyncClient,
    normal_user: User,
):
    response = await client.get(
        "/api/v1/roles/role_desc",
        params={"name": "admin"},
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 403


async def test_admin_can_create_role(
    client: AsyncClient,
    admin_user: User,
):
    response = await client.post(
        "/api/v1/roles/role",
        json={"name": "auditor", "desc": "Read-only auditor"},
        headers=auth_headers(admin_user),
    )

    assert response.status_code == 200
    assert response.json()["code"] == 201
    assert await Role.filter(name="auditor", desc="Read-only auditor").exists()


async def test_admin_cannot_create_duplicate_role(
    client: AsyncClient,
    admin_user: User,
):
    response = await client.post(
        "/api/v1/roles/role",
        json={"name": "admin", "desc": "Duplicate"},
        headers=auth_headers(admin_user),
    )

    assert response.status_code == 400
