import asyncio

import pytest
import pytest_asyncio
from httpx import AsyncClient

from models import Organization, User
from tests.factories import create_user
from tests.helpers.auth import auth_headers


pytestmark = [pytest.mark.integration, pytest.mark.concurrency]


@pytest_asyncio.fixture(loop_scope="session")
async def normal_user(seeded_roles) -> User:
    return await create_user(
        username="idempotency_user",
        email="idempotency_user@example.com",
        role=seeded_roles.user,
    )


async def test_concurrent_requests_apply_one_business_effect(
    client: AsyncClient,
    normal_user: User,
):
    headers = {
        **auth_headers(normal_user),
        "Idempotency-Key": "concurrent-org-creation",
    }
    body = {"name": "idempotent_org", "desc": "Only once"}

    responses = await asyncio.gather(
        client.post(
            "/api/v1/organizations/organization",
            json=body,
            headers=headers,
        ),
        client.post(
            "/api/v1/organizations/organization",
            json=body,
            headers=headers,
        ),
    )

    assert sorted(response.status_code for response in responses) == [200, 409]
    assert await Organization.filter(name="idempotent_org").count() == 1


async def test_same_key_with_different_body_is_rejected(
    client: AsyncClient,
    normal_user: User,
):
    headers = {
        **auth_headers(normal_user),
        "Idempotency-Key": "different-body-key",
    }
    first = await client.post(
        "/api/v1/organizations/organization",
        json={"name": "first_idempotent_org", "desc": "First"},
        headers=headers,
    )
    second = await client.post(
        "/api/v1/organizations/organization",
        json={"name": "second_idempotent_org", "desc": "Second"},
        headers=headers,
    )

    assert first.status_code == 200
    assert second.status_code == 409
    assert await Organization.filter(name="first_idempotent_org").exists()
    assert not await Organization.filter(name="second_idempotent_org").exists()


async def test_repeated_request_replays_the_cached_response(
    client: AsyncClient,
    normal_user: User,
):
    headers = {
        **auth_headers(normal_user),
        "Idempotency-Key": "replay-key",
    }
    body = {"name": "replayed_org", "desc": "Replay"}

    first = await client.post(
        "/api/v1/organizations/organization",
        json=body,
        headers=headers,
    )
    second = await client.post(
        "/api/v1/organizations/organization",
        json=body,
        headers=headers,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert await Organization.filter(name="replayed_org").count() == 1
