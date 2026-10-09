from fastapi import APIRouter, Depends, HTTPException
from core.dependencies import require_admin
from models.admin import User, Role
from schemas.roles import RoleCreate, RoleOut
from repositories.role import role_repository
from core.dependencies import require_admin
from schemas.base import ResponseBase

router = APIRouter()

@router.get("/role_desc")
async def get_desc(name: str, user: User = Depends(require_admin)) -> ResponseBase[str]:
    role = await Role.filter(name=name).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role Not Found")
    data = role.desc
    return ResponseBase[str](msg="success", data=data)

@router.post("/role")
async def create_role(role_in: RoleCreate, user: User = Depends(require_admin)) -> ResponseBase[RoleOut]:
    if await Role.filter(name=role_in.name).exists():
        raise HTTPException(status_code=400, detail="Role already exists")
    role = await role_repository.create_role(role_in)
    data = RoleOut.model_validate(role)
    return ResponseBase[RoleOut](code=201, msg="created success", data=data)

"""
@router.patch("/name")
async def change_role_name(old_name: str, new_name: str, user: User = Depends(require_admin)) -> ResponseBase[RoleOut]:
    if old_name == "admin":
        raise HTTPException(status_code=403, detail="You can't change admin role name")
    role = await Role.filter(name=old_name).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role Not Found")
    new_create = RoleCreate(name=new_name, desc="This is just a try")
    if await Role.filter(name=new_name).exists():
        raise HTTPException(status_code=400, detail="Role already exists")
    role.name = new_name
    await role.save()
    data=RoleOut.model_validate(role)
    return ResponseBase[RoleOut](code=201, msg="change name success", data=data)
"""

@router.patch("/desc")
async def change_role_desc(name: str, new_desc: str, user: User = Depends(require_admin)) -> ResponseBase[RoleOut]:
    role = await Role.filter(name=name).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role Not Found")
    new_create = RoleCreate(name="try_name", desc=new_desc)
    role.desc = new_desc
    await role.save()
    data = RoleOut.model_validate(role)
    return ResponseBase[RoleOut](code=201, msg="change desc success", data=data)

"""
@router.delete("/role")
async def delete_role(name: str, user: User = Depends(require_admin)) -> ResponseBase:
    role = await Role.filter(name=name).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role Not Found")
    user_count = await User.filter(roles=role).count()
    if user_count > 0:
        raise HTTPException(status_code=400, detail="This role is being used, cannot be deleted")
    await role.delete()
    return ResponseBase(code=204, msg="deleted success")
"""
