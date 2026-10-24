import json
import uuid

from models import OutboxMessage
from models.base import OutboxStatus


class OutboxService:
    @staticmethod
    async def publish_event(event_type: str, payload: dict) -> str:
        event_id = str(uuid.uuid4())
        await OutboxMessage.create(
            event_id=event_id,
            event_type=event_type,
            payload=json.dumps(payload, ensure_ascii=False),
            status=OutboxStatus.PENDING
        )
        return event_id

outbox_service = OutboxService()