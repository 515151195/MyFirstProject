from .base import (ApprovalStatus, BaseModel, TimestampMixin,
                   ApprovalAction,)

from tortoise import fields

class ApprovalRequest(BaseModel, TimestampMixin):
    applicant = fields.ForeignKeyField("models.User", related_name="my_approval_requests")
    approver = fields.ForeignKeyField("models.User", related_name="to_approve_requests", null=True)
    organization = fields.ForeignKeyField("models.Organization", related_name="approvals_of_org")
    status = fields.CharEnumField(ApprovalStatus, default=ApprovalStatus.DRAFT)
    title = fields.CharField(max_length=200)
    content = fields.TextField(null=True)

    class Meta:
        table = "approval_request"

class ApprovalRecord(BaseModel, TimestampMixin):
    approval_request = fields.ForeignKeyField("models.ApprovalRequest", related_name="records")
    operator = fields.ForeignKeyField("models.User", related_name="approved_record")
    action = fields.CharEnumField(ApprovalAction)
    comment = fields.TextField(null=True)
    operate_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "approval_record"