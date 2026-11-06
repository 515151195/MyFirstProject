from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
import pytest_asyncio
from httpx import AsyncClient

from models import Invitation, Membership, User
from models.base import (
    InvitationStatus,
    MembershipStatus,
    OrgMemberRole,
    OrgStatus,
)
from tests.factories import add_member, create_invitation, create_org, create_user
from tests.helpers.auth import auth_headers


pytestmark = pytest.mark.integration


@pytest_asyncio.fixture(loop_scope="session")
async def invitation_context(seeded_roles) -> SimpleNamespace:
    owner = await create_user(
        username="invite_owner",
        email="invite_owner@example.com",
        role=seeded_roles.user,
    )
    member = await create_user(
        username="invite_member",
        email="invite_member@example.com",
        role=seeded_roles.user,
    )
    invitee = await create_user(
        username="invite_target",
        email="invite_target@example.com",
        role=seeded_roles.user,
    )
    organization = await create_org("invite_org", owner)
    await add_member(organization, member)
    return SimpleNamespace(
        owner=owner,
        member=member,
        invitee=invitee,
        organization=organization,
    )


def invitation_payload(
    organization_id: int,
    email: str,
    role: str = "member",
    *,
    expires_in_days: int = 1,
) -> dict:
    return {
        "org_id": organization_id,
        "invitee_email": email,
        "role": role,
        "expire_at": (
            datetime.now(UTC) + timedelta(days=expires_in_days)
        ).isoformat(),
    }


async def test_owner_can_create_invitation(
    client: AsyncClient,
    invitation_context: SimpleNamespace,
):
    context = invitation_context
    response = await client.post(
        "/api/v1/invitations/organization/invitation",
        json=invitation_payload(context.organization.id, context.invitee.email),
        headers=auth_headers(context.owner),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 201
    assert body["extra_data"]
    invitation = await Invitation.get(invitee_email=context.invitee.email)
    assert invitation.role == OrgMemberRole.MEMBER
    assert invitation.status == InvitationStatus.PENDING


async def test_regular_member_cannot_create_invitation(
    client: AsyncClient,
    invitation_context: SimpleNamespace,
):
    context = invitation_context
    response = await client.post(
        "/api/v1/invitations/organization/invitation",
        json=invitation_payload(context.organization.id, context.invitee.email),
        headers=auth_headers(context.member),
    )

    assert response.status_code == 403


async def test_invitation_cannot_assign_owner_role(
    client: AsyncClient,
    invitation_context: SimpleNamespace,
):
    context = invitation_context
    response = await client.post(
        "/api/v1/invitations/organization/invitation",
        json=invitation_payload(
            context.organization.id,
            context.invitee.email,
            role="owner",
        ),
        headers=auth_headers(context.owner),
    )

    assert response.status_code == 422


async def test_invitee_can_accept_invitation(
    client: AsyncClient,
    invitation_context: SimpleNamespace,
):
    context = invitation_context
    invitation, token = await create_invitation(
        context.organization,
        context.owner,
        context.invitee.email,
    )

    response = await client.patch(
        f"/api/v1/invitations/invitation/{invitation.id}/accept",
        json=token,
        headers=auth_headers(context.invitee),
    )

    assert response.status_code == 200
    assert await Membership.filter(
        user=context.invitee,
        org=context.organization,
        status=MembershipStatus.ACTIVE,
    ).exists()
    await invitation.refresh_from_db()
    assert invitation.status == InvitationStatus.USED


async def test_invitation_rejects_wrong_email(
    client: AsyncClient,
    invitation_context: SimpleNamespace,
):
    context = invitation_context
    invitation, token = await create_invitation(
        context.organization,
        context.owner,
        context.invitee.email,
    )

    response = await client.patch(
        f"/api/v1/invitations/invitation/{invitation.id}/accept",
        json=token,
        headers=auth_headers(context.member),
    )

    assert response.status_code == 403


async def test_invitation_rejects_wrong_token(
    client: AsyncClient,
    invitation_context: SimpleNamespace,
):
    context = invitation_context
    invitation, _ = await create_invitation(
        context.organization,
        context.owner,
        context.invitee.email,
    )

    response = await client.patch(
        f"/api/v1/invitations/invitation/{invitation.id}/accept",
        json="wrong-token",
        headers=auth_headers(context.invitee),
    )

    assert response.status_code == 401


async def test_expired_invitation_is_rejected(
    client: AsyncClient,
    invitation_context: SimpleNamespace,
):
    context = invitation_context
    invitation, token = await create_invitation(
        context.organization,
        context.owner,
        context.invitee.email,
        expire_at=datetime.now(UTC) - timedelta(minutes=1),
    )

    response = await client.patch(
        f"/api/v1/invitations/invitation/{invitation.id}/accept",
        json=token,
        headers=auth_headers(context.invitee),
    )

    assert response.status_code == 400


async def test_disabled_organization_rejects_invitation_acceptance(
    client: AsyncClient,
    invitation_context: SimpleNamespace,
):
    context = invitation_context
    invitation, token = await create_invitation(
        context.organization,
        context.owner,
        context.invitee.email,
    )
    context.organization.status = OrgStatus.DISABLED
    await context.organization.save()

    response = await client.patch(
        f"/api/v1/invitations/invitation/{invitation.id}/accept",
        json=token,
        headers=auth_headers(context.invitee),
    )

    assert response.status_code == 400


async def test_owner_can_revoke_invitation(
    client: AsyncClient,
    invitation_context: SimpleNamespace,
):
    context = invitation_context
    invitation, _ = await create_invitation(
        context.organization,
        context.owner,
        context.invitee.email,
    )

    response = await client.patch(
        f"/api/v1/invitations/invitation/{invitation.id}/disable",
        headers=auth_headers(context.owner),
    )

    assert response.status_code == 200
    await invitation.refresh_from_db()
    assert invitation.status == InvitationStatus.REVOKED
