from fastapi import APIRouter, Depends, HTTPException, Body

from schemas.organization import OrgCreate, OrgOut
from schemas.membership import MembershipOut
from schemas.base import ResponseBase
from schemas.users import UserOut
from core.dependencies import get_current_user, require_admin
from services import org_service
from models import Organization, User
from core.permissions import require_org_role, require_org_owner, require_org_members


router = APIRouter()

@router.post("/organization", summary="Create new organization")
async def create_organization(org_in: OrgCreate, user = Depends(get_current_user)) -> ResponseBase[OrgOut]:
    data: OrgOut = await org_service.create_org(org_in, user)
    return ResponseBase[OrgOut](code=201, msg="Organization created success", data=data)

@router.get("/organization/information", summary="Get information by name of organization")
async def get_info_org(org_id: int, user = Depends(get_current_user)) -> ResponseBase[OrgOut]:
    if await require_org_members(user.id, org_id):
        org = await Organization.filter(id=org_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization Not Found")
        data = OrgOut.model_validate(org)
        return ResponseBase(msg="Organization information is listed", data=data)
    else:
        raise HTTPException(403, "No permission")

@router.get("/organization/{org_id}/members", summary="Get users of organization by id")
async def get_org_members(org_id: int, user = Depends(get_current_user)) -> ResponseBase[list[UserOut]]:
    if await require_org_role(user.id, org_id):
        data = await org_service.get_org_users(org_id)
        return ResponseBase(msg="Users as list", data=data)
    else:
        raise HTTPException(403, "No permission to do this")

@router.get("/me/organizations", summary="Get organizations of user by id")
async def get_my_orgs(user = Depends(get_current_user)) -> ResponseBase[list[OrgOut]]:
    data = await org_service.get_user_orgs(user.id)
    return ResponseBase(msg="Organizations as list", data=data)

@router.patch("/organization/{org_id}/name", summary="Change organization name")
async def change_org_name(org_id: int, new_name: str = Body(), user = Depends(get_current_user)) -> ResponseBase[OrgOut]:
    if await require_org_owner(user_id=user.id, org_id=org_id):
        data = await org_service.change_name_org(new_name, org_id)
        return ResponseBase(msg="Name changed successfully", data=data)
    else:
        raise HTTPException(status_code=403, detail="No Permission")

@router.patch("/organization/{org_id}/user/{user_id}/admin", summary="Set organization admin")
async def set_org_admin(
        org_id: int,
        user_id: int,
        user: User = Depends(get_current_user)
) -> ResponseBase[MembershipOut]:
    if await require_org_role(user.id, org_id):
        data = await org_service.set_admin(org_id, user_id)
        return ResponseBase(msg="Admin set successfully", data=data)
    else:
        raise HTTPException(403, "No permission")

@router.delete("/organization/{org_id}/members/{user_id}", summary="Kick the member from your organization")
async def remove_org_member(
        org_id: int,
        user_id: int,
        user: User = Depends(get_current_user)
):
    if not await require_org_role(user.id, org_id):
        raise HTTPException(403, "You have no right to remove members")
    await org_service.remove_member(org_id, user_id)

@router.delete("/organization/{org_id}", summary="Delete your organization")
async def delete_org(
        org_id: int,
        user: User = Depends(get_current_user)
) -> ResponseBase:
    if await require_org_owner(user.id, org_id):
        await org_service.delete_my_org(org_id)
        return ResponseBase(code=200, msg="Delete success")
    else:
        raise HTTPException(403, "No permission to delete it")