from models import Organization, User, Membership
from models.base import OrgMemberRole, MembershipStatus, OrgStatus

from fastapi import HTTPException


async def require_org_role(user_id: int, org_id: int) -> bool:
    org = await Organization.filter(id=org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Invalid organization id")
    if org.status != OrgStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Disabled organization")
    mem = await Membership.filter(user__id=user_id, org__id=org_id).first()
    if not mem:
        raise HTTPException(status_code=404, detail="Invalid relationship of user and organization")
    if mem.status == MembershipStatus.DISABLED:
        raise HTTPException(status_code=403, detail="No permission, your status is disabled")
    if mem.role == OrgMemberRole.OWNER or mem.role == OrgMemberRole.ADMIN:
        return True
    else:
        return False

async def require_org_owner(user_id: int, org_id: int) -> bool:
    org = await Organization.filter(id=org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Invalid organization id")
    if org.status != OrgStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Disabled organization")
    mem = await Membership.filter(user__id=user_id, org__id=org_id).first()
    if not mem:
        raise HTTPException(404, "Invalid parameter")
    if mem.status == MembershipStatus.DISABLED:
        raise HTTPException(status_code=403, detail="No permission, your status is disabled")
    if mem.role == OrgMemberRole.OWNER:
        return True
    else:
        return False

async def require_org_members(user_id: int, org_id: int) -> bool:
    org = await Organization.filter(id=org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Invalid organization id")
    if org.status != OrgStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Disabled organization")
    mem = await Membership.filter(user__id=user_id, org__id=org_id).first()
    if not mem:
        raise HTTPException(404, "Invalid parameter")
    if mem.status == MembershipStatus.DISABLED:
        raise HTTPException(status_code=403, detail="No permission, your status is disabled")
    if mem:
        return True
    return False