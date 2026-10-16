from .base import BaseModel, TimestampMixin, IdeStatus

from tortoise import fields

class IdempotencyRecord(BaseModel, TimestampMixin):
    idempotency_key = fields.CharField(max_length=64, unique=True, index=True)
    request_digest = fields.TextField()
    response_data = fields.JSONField(null=True)
    status = fields.CharEnumField(IdeStatus)

    class Meta:
        table = "idempotency_record"