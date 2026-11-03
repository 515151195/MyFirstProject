from .base import BaseModel, TimestampMixin

from tortoise import fields

class Notification(BaseModel, TimestampMixin):
    user_id = fields.IntField(index=True)
    title = fields.CharField(max_length=255)
    content = fields.TextField()
    is_read = fields.BooleanField(default=False, index=True)
    source_event_id = fields.IntField(max_length=64, unique=True, index=True)
    read_at = fields.DatetimeField(null=True)

    class Meta:
        table = "notification"