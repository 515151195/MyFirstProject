from schemas.base import ResponseBase
from models import User, Invitation
from schemas.invitation import InvitationOut, InvitationCreate
from schemas.membership import MembershipOut
from core.dependencies import get_current_user, require_admin
from core.permissions import require_org_owner, require_org_role
from services import inv_service

from fastapi import APIRouter, Depends, HTTPException, Body


router = APIRouter()

@router.post("/organization/{org_id}/invitation/{member_id}", summary="Invite user")
async def invite(
        inv_info: InvitationCreate,
        user: User = Depends(get_current_user)
) -> ResponseBase[InvitationOut]:
    if await require_org_role(user_id=user.id, org_id=inv_info.org_id):
        data, token=inv_service.create_inv(inv_info)
        return ResponseBase(code=201, msg="Invitation created success", data=data, extra_data=token)
    else:
        raise HTTPException(403, "No permission")

@router.patch("/invitation/{inv_id}/accept", summary="Accept invitation")
async def accept_invitation(
        inv_id: int,
        token: str = Body(),
        user: User = Depends(get_current_user),
) -> ResponseBase[MembershipOut]:
    mem_out = inv_service.accept_inv(user, token, inv_id)
    return ResponseBase(code=201, msg="Membership created success", data=mem_out)