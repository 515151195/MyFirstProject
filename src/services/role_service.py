from schemas.base import ResponseBase
from schemas.roles import RoleCreate, RoleOut
from models import Role
from repositories.role import role_repository

from fastapi import HTTPException

class RoleService:
    async def get_desc_by_name(self, name: str) -> ResponseBase[str]:
        role = await Role.filter(name=name).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role Not Found")
        data = role.desc
        return ResponseBase[str](msg="success", data=data)


    async def create_new_role(self, role_in: RoleCreate) -> ResponseBase[RoleOut]:
        if await Role.filter(name=role_in.name).exists():
            raise HTTPException(status_code=400, detail="Role already exists")
        role = await role_repository.create_role(role_in)
        data = RoleOut.model_validate(role)
        return ResponseBase[RoleOut](code=201, msg="created success", data=data)




role_service = RoleService()
