import pytest

from models import Notification, OutboxMessage
from models.base import OutboxStatus
from src.workers.notification_worker import (
    backfill_poll_outbox,
    consume_single_outbox,
)
from tests.factories import create_outbox, create_user
from tests.helpers.redis import make_worker_context


pytestmark = [pytest.mark.integration, pytest.mark.worker]


async def test_worker_creates_notification_for_submit_event(
    seeded_roles,
):
    approver = await create_user(
        username="worker_approver",
        email="worker_approver@example.com",
        role=seeded_roles.user,
    )
    event = await create_outbox(
        "approval.submit",
        {
            "approval_id": 1,
            "applicant_id": 99,
            "approver_id": approver.id,
            "title": "Worker event",
        },
    )
    context = make_worker_context()

    await consume_single_outbox(context, event.id)

    await event.refresh_from_db()
    assert event.status == OutboxStatus.DELIVERED
    notification = await Notification.get(source_event_id=event.id)
    assert notification.user_id == approver.id
    assert notification.title == "New approval submit"


async def test_worker_does_not_duplicate_notification(
    seeded_roles,
):
    approver = await create_user(
        username="worker_duplicate",
        email="worker_duplicate@example.com",
        role=seeded_roles.user,
    )
    event = await create_outbox(
        "approval.submit",
        {
            "approval_id": 2,
            "applicant_id": 99,
            "approver_id": approver.id,
            "title": "Duplicate event",
        },
    )
    context = make_worker_context()

    await consume_single_outbox(context, event.id)
    await consume_single_outbox(context, event.id)

    assert await Notification.filter(source_event_id=event.id).count() == 1


@pytest.mark.parametrize(
    ("event_type", "payload", "expected_title"),
    [
        (
            "approval.passed",
            {"approval_id": 1, "applicant_id": 1, "approver_id": 2, "title": "Passed"},
            "Approval success",
        ),
        (
            "approval.rejected",
            {"approval_id": 2, "applicant_id": 1, "approver_id": 2, "title": "Rejected"},
            "Approval failed",
        ),
    ],
)
async def test_worker_handles_events_published_by_approval_service(
    seeded_roles,
    event_type: str,
    payload: dict,
    expected_title: str,
):
    applicant = await create_user(
        username=f"worker_{event_type.replace('.', '_')}",
        email=f"{event_type.replace('.', '_')}@example.com",
        role=seeded_roles.user,
    )
    payload = {**payload, "applicant_id": applicant.id}
    event = await create_outbox(event_type, payload)

    await consume_single_outbox(make_worker_context(), event.id)

    notification = await Notification.get(source_event_id=event.id)
    assert notification.title == expected_title


async def test_failed_event_is_retried(
    seeded_roles,
):
    event = await create_outbox(
        "approval.submit",
        {"approval_id": 1},
        max_retry=3,
    )
    context = make_worker_context()

    await consume_single_outbox(context, event.id)

    await event.refresh_from_db()
    assert event.status == OutboxStatus.PENDING
    assert event.retry_count == 1
    assert len(context["arq_redis"].jobs_for("consume_single_outbox")) == 1


async def test_event_is_marked_failed_after_max_retries(
    seeded_roles,
):
    event = await create_outbox(
        "approval.submit",
        {"approval_id": 1},
        retry_count=2,
        max_retry=2,
    )

    with pytest.raises(KeyError):
        await consume_single_outbox(make_worker_context(), event.id)

    await event.refresh_from_db()
    assert event.status == OutboxStatus.FAILED


async def test_backfill_enqueues_pending_events(
    seeded_roles,
):
    first = await create_outbox("approval.submit", {"approver_id": 1})
    second = await create_outbox("approval.submit", {"approver_id": 2})
    delivered = await create_outbox(
        "approval.submit",
        {"approver_id": 3},
        status=OutboxStatus.DELIVERED,
    )
    context = make_worker_context()

    await backfill_poll_outbox(context)

    jobs = context["arq_redis"].jobs_for("consume_single_outbox")
    enqueued_ids = {job.args[0] for job in jobs}
    assert enqueued_ids == {first.id, second.id}
    assert delivered.id not in enqueued_ids
