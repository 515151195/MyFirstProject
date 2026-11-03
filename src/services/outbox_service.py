import json

from models import OutboxMessage
from models.base import OutboxStatus
from core.queue import get_redis_pool

from tortoise.transactions import in_transaction


class OutboxService:
    @staticmethod
    async def publish_event(
            event_type: str,
            payload: dict,
            max_retry: int = 3,
    ):
        async with in_transaction():
            outbox_record = await OutboxMessage.create(
                event_type=event_type,
                payload=json.dumps(payload, ensure_ascii=False),
                status=OutboxStatus.PENDING,
                max_retry=max_retry,
            )

        redis = await get_redis_pool()
        await redis.enqueue_job(
            "consume_single_outbox",
            outbox_record.id,
        )

outbox_service = OutboxService()