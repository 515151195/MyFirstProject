from pydantic import BaseModel, Field
from datetime import datetime

from models.organization import OrgMemberRole, MembershipStatus

class MembershipCreate(BaseModel):
    user_id: int
    org_id: int
    role: OrgMemberRole


class MembershipOut(BaseModel):
    id: int
    user_id: int
    org_id: int
    role: OrgMemberRole
    status: MembershipStatus
    created_at: datetime

    class Config:
        from_attributes = True