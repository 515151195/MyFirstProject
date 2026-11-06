import asyncio
from types import SimpleNamespace

import pytest
import pytest_asyncio
from httpx import AsyncClient

from models import ApprovalRecord, ApprovalRequest, OutboxMessage
from models.base import ApprovalStatus
from tests.factories import add_member, create_approval, create_org, create_user
from tests.helpers.auth import auth_headers


pytestmark = [pytest.mark.integration, pytest.mark.concurrency]


@pytest_asyncio.fixture(loop_scope="session")
async def concurrency_context(seeded_roles) -> SimpleNamespace:
    applicant = await create_user(
        username="race_applicant",
        email="race_applicant@example.com",
        role=seeded_roles.user,
    )
    approver = await create_user(
        username="race_approver",
        email="race_approver@example.com",
        role=seeded_roles.user,
    )
    organization = await create_org("race_org", applicant)
    await add_member(organization, approver)
    return SimpleNamespace(
        applicant=applicant,
        approver=approver,
        organization=organization,
    )


async def test_concurrent_approvals_create_one_record(
    client: AsyncClient,
    concurrency_context: SimpleNamespace,
    fake_redis,
):
    context = concurrency_context
    approval = await create_approval(
        context.organization,
        context.applicant,
        context.approver,
        status=ApprovalStatus.PENDING,
    )
    headers = auth_headers(context.approver)

    responses = await asyncio.gather(
        client.post(
            f"/api/v1/approvals/{approval.id}/approve",
            headers=headers,
        ),
        client.post(
            f"/api/v1/approvals/{approval.id}/approve",
            headers=headers,
        ),
    )

    assert sorted(response.status_code for response in responses) == [200, 400]
    assert await ApprovalRecord.filter(
        approval_request_id=approval.id,
    ).count() == 1
    assert await OutboxMessage.filter(event_type="approval.passed").count() == 1
    await approval.refresh_from_db()
    assert approval.status == ApprovalStatus.APPROVED


async def test_concurrent_approve_and_cancel_have_one_winner(
    client: AsyncClient,
    concurrency_context: SimpleNamespace,
    fake_redis,
):
    context = concurrency_context
    approval = await create_approval(
        context.organization,
        context.applicant,
        context.approver,
        status=ApprovalStatus.PENDING,
    )

    responses = await asyncio.gather(
        client.post(
            f"/api/v1/approvals/{approval.id}/approve",
            headers=auth_headers(context.approver),
        ),
        client.post(
            f"/api/v1/approvals/{approval.id}/cancel",
            headers=auth_headers(context.applicant),
        ),
    )

    assert sorted(response.status_code for response in responses) == [200, 400]
    await approval.refresh_from_db()
    assert approval.status in (
        ApprovalStatus.APPROVED,
        ApprovalStatus.CANCELLED,
    )
    assert await ApprovalRecord.filter(
        approval_request_id=approval.id,
    ).count() == 1
