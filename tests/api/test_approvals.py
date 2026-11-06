from types import SimpleNamespace

import pytest
import pytest_asyncio
from httpx import AsyncClient

from models import ApprovalRecord, ApprovalRequest, OutboxMessage, User
from models.base import ApprovalStatus, OutboxStatus
from tests.factories import add_member, create_approval, create_org, create_user
from tests.helpers.auth import auth_headers


pytestmark = pytest.mark.integration


@pytest_asyncio.fixture(loop_scope="session")
async def approval_context(seeded_roles) -> SimpleNamespace:
    applicant = await create_user(
        username="approval_applicant",
        email="approval_applicant@example.com",
        role=seeded_roles.user,
    )
    approver = await create_user(
        username="approval_approver",
        email="approval_approver@example.com",
        role=seeded_roles.user,
    )
    outsider = await create_user(
        username="approval_outsider",
        email="approval_outsider@example.com",
        role=seeded_roles.user,
    )
    organization = await create_org("approval_org", applicant)
    await add_member(organization, approver)
    await add_member(organization, outsider)
    return SimpleNamespace(
        applicant=applicant,
        approver=approver,
        outsider=outsider,
        organization=organization,
    )


async def test_create_approval_draft(
    client: AsyncClient,
    approval_context: SimpleNamespace,
):
    context = approval_context
    response = await client.post(
        f"/api/v1/approvals/organization/{context.organization.id}/draft",
        json={
            "approver_id": context.approver.id,
            "title": "Travel expense",
            "content": "Taxi and hotel",
        },
        headers=auth_headers(context.applicant),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 201
    assert body["data"]["status"] == ApprovalStatus.DRAFT
    assert await ApprovalRequest.filter(
        applicant_id=context.applicant.id,
        approver_id=context.approver.id,
    ).exists()


async def test_cannot_choose_self_as_approver(
    client: AsyncClient,
    approval_context: SimpleNamespace,
):
    context = approval_context
    response = await client.post(
        f"/api/v1/approvals/organization/{context.organization.id}/draft",
        json={"approver_id": context.applicant.id, "title": "Invalid"},
        headers=auth_headers(context.applicant),
    )

    assert response.status_code == 400


async def test_approver_must_be_an_active_member(
    client: AsyncClient,
    approval_context: SimpleNamespace,
    seeded_roles,
):
    context = approval_context
    non_member = await create_user(
        username="non_member",
        email="non_member@example.com",
        role=seeded_roles.user,
    )
    response = await client.post(
        f"/api/v1/approvals/organization/{context.organization.id}/draft",
        json={"approver_id": non_member.id, "title": "Invalid"},
        headers=auth_headers(context.applicant),
    )

    assert response.status_code == 400


async def test_applicant_can_submit_and_create_outbox(
    client: AsyncClient,
    approval_context: SimpleNamespace,
    fake_redis,
):
    context = approval_context
    approval = await create_approval(
        context.organization,
        context.applicant,
        context.approver,
    )

    response = await client.post(
        f"/api/v1/approvals/{approval.id}/submit",
        headers=auth_headers(context.applicant),
    )

    assert response.status_code == 200
    await approval.refresh_from_db()
    assert approval.status == ApprovalStatus.PENDING
    assert await ApprovalRecord.filter(approval_request_id=approval.id).exists()
    assert await OutboxMessage.filter(
        event_type="approval.submit",
        status=OutboxStatus.PENDING,
    ).exists()
    assert len(fake_redis.jobs) == 1


async def test_non_applicant_cannot_submit(
    client: AsyncClient,
    approval_context: SimpleNamespace,
):
    context = approval_context
    approval = await create_approval(
        context.organization,
        context.applicant,
        context.approver,
    )

    response = await client.post(
        f"/api/v1/approvals/{approval.id}/submit",
        headers=auth_headers(context.approver),
    )

    assert response.status_code == 403


async def test_designated_approver_can_approve(
    client: AsyncClient,
    approval_context: SimpleNamespace,
    fake_redis,
):
    context = approval_context
    approval = await create_approval(
        context.organization,
        context.applicant,
        context.approver,
        status=ApprovalStatus.PENDING,
    )

    response = await client.post(
        f"/api/v1/approvals/{approval.id}/approve",
        headers=auth_headers(context.approver),
    )

    assert response.status_code == 200
    await approval.refresh_from_db()
    assert approval.status == ApprovalStatus.APPROVED
    assert len(fake_redis.jobs) == 1


async def test_non_designated_user_cannot_approve(
    client: AsyncClient,
    approval_context: SimpleNamespace,
    fake_redis,
):
    context = approval_context
    approval = await create_approval(
        context.organization,
        context.applicant,
        context.approver,
        status=ApprovalStatus.PENDING,
    )

    response = await client.post(
        f"/api/v1/approvals/{approval.id}/approve",
        headers=auth_headers(context.outsider),
    )

    assert response.status_code == 403
    await approval.refresh_from_db()
    assert approval.status == ApprovalStatus.PENDING


async def test_approved_request_cannot_be_approved_again(
    client: AsyncClient,
    approval_context: SimpleNamespace,
    fake_redis,
):
    context = approval_context
    approval = await create_approval(
        context.organization,
        context.applicant,
        context.approver,
        status=ApprovalStatus.APPROVED,
    )

    response = await client.post(
        f"/api/v1/approvals/{approval.id}/approve",
        headers=auth_headers(context.approver),
    )

    assert response.status_code == 400


async def test_designated_approver_can_reject(
    client: AsyncClient,
    approval_context: SimpleNamespace,
    fake_redis,
):
    context = approval_context
    approval = await create_approval(
        context.organization,
        context.applicant,
        context.approver,
        status=ApprovalStatus.PENDING,
    )

    response = await client.post(
        f"/api/v1/approvals/{approval.id}/reject",
        headers=auth_headers(context.approver),
    )

    assert response.status_code == 200
    await approval.refresh_from_db()
    assert approval.status == ApprovalStatus.REJECTED


async def test_applicant_can_cancel_pending_request(
    client: AsyncClient,
    approval_context: SimpleNamespace,
):
    context = approval_context
    approval = await create_approval(
        context.organization,
        context.applicant,
        context.approver,
        status=ApprovalStatus.PENDING,
    )

    response = await client.post(
        f"/api/v1/approvals/{approval.id}/cancel",
        headers=auth_headers(context.applicant),
    )

    assert response.status_code == 200
    await approval.refresh_from_db()
    assert approval.status == ApprovalStatus.CANCELLED


async def test_only_participants_can_read_approval(
    client: AsyncClient,
    approval_context: SimpleNamespace,
):
    context = approval_context
    approval = await create_approval(
        context.organization,
        context.applicant,
        context.approver,
    )

    participant = await client.get(
        f"/api/v1/approvals/{approval.id}",
        headers=auth_headers(context.applicant),
    )
    outsider = await client.get(
        f"/api/v1/approvals/{approval.id}",
        headers=auth_headers(context.outsider),
    )

    assert participant.status_code == 200
    assert outsider.status_code == 403


async def test_list_applicant_and_approver_views(
    client: AsyncClient,
    approval_context: SimpleNamespace,
):
    context = approval_context
    await create_approval(
        context.organization,
        context.applicant,
        context.approver,
        status=ApprovalStatus.PENDING,
    )

    applicant_response = await client.get(
        "/api/v1/approvals/list",
        params={"is_applicant": True},
        headers=auth_headers(context.applicant),
    )
    approver_response = await client.get(
        "/api/v1/approvals/list",
        params={"is_applicant": False},
        headers=auth_headers(context.approver),
    )

    assert applicant_response.status_code == 200
    assert len(applicant_response.json()["data"]) == 1
    assert approver_response.status_code == 200
    assert len(approver_response.json()["data"]) == 1
