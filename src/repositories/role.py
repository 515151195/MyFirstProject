from core.curd import CURDBase
from models.admin import Role
from schemas.roles import RoleCreate

class RoleRepositories(CURDBase[Role, RoleCreate, RoleCreate]):
    def __init__(self):
        super().__init__(Role)

    async def create_role(self, role_in: RoleCreate) -> Role:
        data = role_in.model_dump()
        find_same_role = await Role.filter(name=role_in.name).first()
        if find_same_role:
            raise ValueError("A role with the same name already exists")
        role = await Role.create(**data)
        return role

role_repository = RoleRepositories()