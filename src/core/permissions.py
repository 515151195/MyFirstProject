from models import Organization, User, Membership
from models.base import OrgMemberRole

from fastapi import HTTPException


async def require_org_role(user_id: int, org_id: int) -> bool:
    mem = await Membership.filter(user__id=user_id, org__id=org_id).first()
    if not mem:
        raise HTTPException(status_code=404, detail="Invalid relationship of user and organization")
    if mem.role == OrgMemberRole.OWNER or mem.role == OrgMemberRole.ADMIN:
        return True
    else:
        return False

async def require_org_owner(user_id: int, org_id: int) -> bool:
    mem = await Membership.filter(user__id=user_id, org__id=org_id).first()
    if not mem:
        raise HTTPException(404, "Invalid parameter")
    if mem.role == OrgMemberRole.OWNER:
        return True
    else:
        return False