import asyncio
from types import SimpleNamespace

import pytest
import pytest_asyncio
from httpx import AsyncClient

from models import Membership
from tests.factories import add_member, create_invitation, create_org, create_user
from tests.helpers.auth import auth_headers


pytestmark = [pytest.mark.integration, pytest.mark.concurrency]


@pytest_asyncio.fixture(loop_scope="session")
async def invitation_context(seeded_roles) -> SimpleNamespace:
    owner = await create_user(
        username="accept_owner",
        email="accept_owner@example.com",
        role=seeded_roles.user,
    )
    invitee = await create_user(
        username="accept_invitee",
        email="accept_invitee@example.com",
        role=seeded_roles.user,
    )
    organization = await create_org("accept_org", owner)
    return SimpleNamespace(
        owner=owner,
        invitee=invitee,
        organization=organization,
    )


async def test_concurrent_invitation_acceptance_creates_one_membership(
    client: AsyncClient,
    invitation_context: SimpleNamespace,
):
    context = invitation_context
    invitation, token = await create_invitation(
        context.organization,
        context.owner,
        context.invitee.email,
    )
    headers = auth_headers(context.invitee)

    responses = await asyncio.gather(
        client.patch(
            f"/api/v1/invitations/invitation/{invitation.id}/accept",
            json=token,
            headers=headers,
        ),
        client.patch(
            f"/api/v1/invitations/invitation/{invitation.id}/accept",
            json=token,
            headers=headers,
        ),
    )

    assert sorted(response.status_code for response in responses) == [200, 400]
    assert await Membership.filter(
        user=context.invitee,
        org=context.organization,
    ).count() == 1
