from pydantic import BaseModel
from datetime import datetime
from models.base import ApprovalStatus


class ApprovalCreate(BaseModel):
    approver_id: int
    title: str
    content: str | None = None

class ApprovalRequestOut(BaseModel):
    id: int
    applicant_id: int
    approver_id: int
    status: ApprovalStatus
    title: str
    content: str | None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class ApprovalRecordOut(BaseModel):
    id: int
    approval_id: int
    operator_id: int
    action: str
    comment: str | None
    operate_at: datetime
    class Config:
        from_attributes = True