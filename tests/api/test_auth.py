from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient

from models import User
from tests.factories import DEFAULT_PASSWORD, create_user
from tests.helpers.auth import auth_headers, refresh_token_for_user
from utils.password import verify_password


pytestmark = pytest.mark.integration


@pytest_asyncio.fixture(loop_scope="session")
async def normal_user(seeded_roles) -> User:
    return await create_user(
        username="auth_user",
        email="auth_user@example.com",
        role=seeded_roles.user,
    )


async def test_signup_creates_user_with_normal_role(client: AsyncClient):
    response = await client.post(
        "/api/v1/base/signup",
        json={
            "username": "new_user",
            "email": "new_user@example.com",
            "password": DEFAULT_PASSWORD,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["username"] == "new_user"
    user = await User.get(id=data["id"])
    assert await user.roles.filter(name="user").exists()


async def test_signup_rejects_duplicate_username(
    client: AsyncClient,
    normal_user: User,
):
    response = await client.post(
        "/api/v1/base/signup",
        json={
            "username": normal_user.username,
            "email": "another@example.com",
            "password": DEFAULT_PASSWORD,
        },
    )

    assert response.status_code == 400


async def test_login_returns_access_and_refresh_tokens(
    client: AsyncClient,
    normal_user: User,
):
    response = await client.post(
        "/api/v1/base/login",
        json={
            "username": normal_user.username,
            "password": DEFAULT_PASSWORD,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]


async def test_login_rejects_wrong_password(
    client: AsyncClient,
    normal_user: User,
):
    response = await client.post(
        "/api/v1/base/login",
        json={
            "username": normal_user.username,
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401


async def test_refresh_token_returns_new_token_pair(
    client: AsyncClient,
    normal_user: User,
):
    response = await client.post(
        "/api/v1/base/refresh_token",
        json={"refresh_token": refresh_token_for_user(normal_user)},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["access_token"]
    assert data["refresh_token"]


async def test_access_token_cannot_be_used_for_refresh(
    client: AsyncClient,
    normal_user: User,
):
    response = await client.post(
        "/api/v1/base/refresh_token",
        json={
            "refresh_token": auth_headers(normal_user)["Authorization"].split()[1]
        },
    )

    assert response.status_code == 401


async def test_protected_endpoint_requires_access_token(
    client: AsyncClient,
    normal_user: User,
):
    unauthenticated = await client.get("/api/v1/users/me")
    authenticated = await client.get(
        "/api/v1/users/me",
        headers=auth_headers(normal_user),
    )

    assert unauthenticated.status_code in (401, 403)
    assert authenticated.status_code == 200


async def test_change_password_requires_correct_old_password(
    client: AsyncClient,
    normal_user: User,
):
    response = await client.post(
        "/api/v1/base/change-password",
        json={
            "old_password": "WrongPassword123",
            "new_password": "NewPassword123",
            "new_password_again": "NewPassword123",
        },
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 400


async def test_change_password_rejects_mismatched_confirmation(
    client: AsyncClient,
    normal_user: User,
):
    response = await client.post(
        "/api/v1/base/change-password",
        json={
            "old_password": DEFAULT_PASSWORD,
            "new_password": "NewPassword123",
            "new_password_again": "DifferentPassword123",
        },
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 400


async def test_change_password_updates_the_hash(
    client: AsyncClient,
    normal_user: User,
):
    new_password = "NewPassword123"
    response = await client.post(
        "/api/v1/base/change-password",
        json={
            "old_password": DEFAULT_PASSWORD,
            "new_password": new_password,
            "new_password_again": new_password,
        },
        headers=auth_headers(normal_user),
    )

    assert response.status_code == 200
    await normal_user.refresh_from_db()
    assert verify_password(new_password, normal_user.password)
