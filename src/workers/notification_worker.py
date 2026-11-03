import json
from arq.connections import ArqRedis
from tortoise.transactions import in_transaction
from src.models import OutboxMessage
from models.base import OutboxStatus
from src.services.not_service import notification_service


async def consume_single_outbox(ctx: dict, outbox_id: int):
    """【实时消费任务】只消费指定id的一条outbox记录，publish_event触发调用"""
    arq_redis: ArqRedis = ctx["arq_redis"]
    # 加行锁，防止并发重复消费
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
    """【兜底轮询任务】低频扫描，捞Redis丢任务、ARQ崩溃漏掉的pending消息"""
    pending_events = await OutboxMessage.filter(
        status=OutboxStatus.PENDING
    ).limit(10).order_by("created_at")

    for event in pending_events:
        redis: ArqRedis = ctx["arq_redis"]
        await redis.enqueue_job("consume_single_outbox", event.id)
