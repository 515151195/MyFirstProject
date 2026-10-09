from pydantic import BaseModel, EmailStr
from datetime import datetime

from models.organization import OrgMemberRole, InvitationStatus

class InvitationCreate(BaseModel):
    org_id: int
    invitee_email: EmailStr
    role: OrgMemberRole
    expire_at: datetime


class InvitationOut(BaseModel):
    org_name: str
    inviter_name: str
    invitee_email: EmailStr
    role: OrgMemberRole
    expire_at: datetime
    status: InvitationStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True