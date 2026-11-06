import json
from arq.connections import ArqRedis
from tortoise.transactions import in_transaction
from src.models import OutboxMessage
from models.base import OutboxStatus
from src.services.not_service import notification_service


async def consume_single_outbox(ctx: dict, outbox_id: int):
    arq_redis: ArqRedis = ctx["arq_redis"]
    async with in_transaction():
        event = await OutboxMessage.select_for_update().get_or_none(
            id=outbox_id,
            status=OutboxStatus.PENDING
        )
        if not event:
            return

        try:
            payload = json.loads(event.payload)
            if event.event_type == "approval.success":
                await notification_service.handle_approval_success(
                    outbox_id=event.id,
                    payload=payload
                )
            if event.event_type == "approval.reject":
                await notification_service.handle_approval_reject(
                    outbox_id=event.id,
                    payload=payload
                )
            if event.event_type == "approval.submit":
                await notification_service.handle_approval_submit(
                    outbox_id=event.id,
                    payload=payload
                )

            event.status = OutboxStatus.DELIVERED
            await event.save()

        except Exception as e:
            event.retry_count += 1
            if event.retry_count >= event.max_retry:
                event.status = OutboxStatus.FAILED
                await event.save()
                raise e
            await event.save()
            redis = ctx["arq_redis"]
            await redis.enqueue_job("consume_single_outbox", outbox_id)


async def backfill_poll_outbox(ctx: dict):
    pending_events = await OutboxMessage.filter(
        status=OutboxStatus.PENDING
    ).limit(10).order_by("created_at")

    for event in pending_events:
        redis: ArqRedis = ctx["arq_redis"]
        await redis.enqueue_job("consume_single_outbox", event.id)
