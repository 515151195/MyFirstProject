from schemas.base import ResponseBase
from models import User, Invitation
from schemas.invitation import InvitationOut, InvitationCreate
from schemas.membership import MembershipOut
from core.dependencies import get_current_user, require_admin
from core.permissions import require_org_owner, require_org_role
from services import inv_service
from core.limiter import limiter

from fastapi import APIRouter, Depends, HTTPException, Body, Request
from slowapi.util import get_remote_address


router = APIRouter()

def invite_key(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        return get_remote_address(request)
    return f"invite:uid:{user.id}"

@router.post("/organization/invitation", summary="Invite user")
@limiter.limit(
    "3/minute",
    key_func=invite_key
)
async def invite(
        request: Request,
        inv_info: InvitationCreate,
        user: User = Depends(get_current_user)
) -> ResponseBase[InvitationOut]:
    if await require_org_role(user_id=user.id, org_id=inv_info.org_id):
        data, token=await inv_service.create_inv(inv_info, user)
        return ResponseBase(code=201, msg="Invitation created success", data=data, extra_data=token)
    else:
        raise HTTPException(403, "No permission")

@router.patch("/invitation/{inv_id}/accept", summary="Accept invitation")
async def accept_invitation(
        inv_id: int,
        token: str = Body(),
        user: User = Depends(get_current_user),
) -> ResponseBase[MembershipOut]:
    mem_out = await inv_service.accept_inv(user, token, inv_id)
    return ResponseBase(code=201, msg="Membership created success", data=mem_out)

@router.patch("/invitation/{inv_id}/disable", summary="Disable invitation")
async def disable_invitation(
        inv_id: int,
        user: User = Depends(get_current_user)
) -> ResponseBase[InvitationOut]:
    data: InvitationOut = await inv_service.disable_inv(inv_id, user)
    return ResponseBase(code=200, msg="Disable invitation success", data=data)