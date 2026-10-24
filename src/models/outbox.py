from .base import BaseModel, TimestampMixin, OutboxStatus

from tortoise import fields

class OutboxMessage(BaseModel, TimestampMixin):
    event_id = fields.CharField(max_length=64, unique=True, index=True)
    event_type = fields.CharField(max_length=128, index=True)
    payload = fields.TextField()
    status = fields.CharEnumField(OutboxStatus, default=OutboxStatus.PENDING, index=True)
    retry_count = fields.IntField(default=0)
    max_retry = fields.IntField(default=3)

    class Meta:
        table = "outbox_message"
        indexes = [
            ("status", "created_at")  # 给worker查询pending事件加索引
        ]