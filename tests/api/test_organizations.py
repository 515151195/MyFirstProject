from types import SimpleNamespace

import pytest
import pytest_asyncio
from httpx import AsyncClient

from models import Membership, Organization, User
from models.base import MembershipStatus, OrgMemberRole, OrgStatus
from tests.factories import add_member, create_org, create_user
from tests.helpers.auth import auth_headers


pytestmark = pytest.mark.integration


@pytest_asyncio.fixture(loop_scope="session")
async def organization_context(seeded_roles) -> SimpleNamespace:
    owner = await create_user(
        username="org_owner",
        email="org_owner@example.com",
        role=seeded_roles.user,
    )
    member = await create_user(
        username="org_member",
        email="org_member@example.com",
        role=seeded_roles.user,
    )
    outsider = await create_user(
        username="org_outsider",
        email="org_outsider@example.com",
        role=seeded_roles.user,
    )
    organization = await create_org("test_org", owner)
    await add_member(organization, member)
    return SimpleNamespace(
        owner=owner,
        member=member,
        outsider=outsider,
        organization=organization,
    )


async def test_create_organization_creates_owner_membership(
    client: AsyncClient,
    seeded_roles,
):
    user = await create_user(
        username="new_org_owner",
        email="new_org_owner@example.com",
        role=seeded_roles.user,
    )

    response = await client.post(
        "/api/v1/organizations/organization",
        json={"name": "created_org", "desc": "Created from API"},
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    assert response.json()["code"] == 201
    organization = await Organization.get(name="created_org")
    membership = await Membership.get(user=user, org=organization)
    assert membership.role == OrgMemberRole.OWNER
    assert membership.status == MembershipStatus.ACTIVE


async def test_organization_info_is_visible_to_members_only(
    client: AsyncClient,
    organization_context: SimpleNamespace,
):
    organization = organization_context.organization
    member_response = await client.get(
        "/api/v1/organizations/organization/information",
        params={"org_id": organization.id},
        headers=auth_headers(organization_context.member),
    )
    outsider_response = await client.get(
        "/api/v1/organizations/organization/information",
        params={"org_id": organization.id},
        headers=auth_headers(organization_context.outsider),
    )

    assert member_response.status_code == 200
    assert outsider_response.status_code == 404


async def test_only_org_admin_can_list_members(
    client: AsyncClient,
    organization_context: SimpleNamespace,
):
    organization = organization_context.organization
    owner_response = await client.get(
        f"/api/v1/organizations/organization/{organization.id}/members",
        headers=auth_headers(organization_context.owner),
    )
    member_response = await client.get(
        f"/api/v1/organizations/organization/{organization.id}/members",
        headers=auth_headers(organization_context.member),
    )

    assert owner_response.status_code == 200
    assert member_response.status_code == 403


async def test_current_user_organization_list(
    client: AsyncClient,
    organization_context: SimpleNamespace,
):
    response = await client.get(
        "/api/v1/organizations/me/organizations",
        headers=auth_headers(organization_context.member),
    )
    outsider_response = await client.get(
        "/api/v1/organizations/me/organizations",
        headers=auth_headers(organization_context.outsider),
    )

    assert response.status_code == 200
    assert [item["name"] for item in response.json()["data"]] == ["test_org"]
    assert outsider_response.json()["data"] == []


async def test_owner_can_change_organization_name(
    client: AsyncClient,
    organization_context: SimpleNamespace,
):
    organization = organization_context.organization
    response = await client.patch(
        f"/api/v1/organizations/organization/{organization.id}/name",
        json="renamed_org",
        headers=auth_headers(organization_context.owner),
    )

    assert response.status_code == 200
    await organization.refresh_from_db()
    assert organization.name == "renamed_org"


async def test_owner_can_promote_member_to_admin(
    client: AsyncClient,
    organization_context: SimpleNamespace,
):
    organization = organization_context.organization
    member = organization_context.member
    response = await client.patch(
        f"/api/v1/organizations/organization/{organization.id}/user/{member.id}/admin",
        headers=auth_headers(organization_context.owner),
    )

    assert response.status_code == 200
    membership = await Membership.get(user=member, org=organization)
    assert membership.role == OrgMemberRole.ADMIN


async def test_owner_can_remove_regular_member(
    client: AsyncClient,
    organization_context: SimpleNamespace,
):
    organization = organization_context.organization
    member = organization_context.member
    response = await client.delete(
        f"/api/v1/organizations/organization/{organization.id}/members/{member.id}",
        headers=auth_headers(organization_context.owner),
    )

    assert response.status_code == 200
    assert not await Membership.filter(user=member, org=organization).exists()


async def test_disabled_organization_rejects_member_access(
    client: AsyncClient,
    organization_context: SimpleNamespace,
):
    organization = organization_context.organization
    organization.status = OrgStatus.DISABLED
    await organization.save()

    response = await client.get(
        "/api/v1/organizations/organization/information",
        params={"org_id": organization.id},
        headers=auth_headers(organization_context.member),
    )

    assert response.status_code == 400
