from core.curd import CURDBase
from datetime import datetime

from models import User, Role
from schemas.users import UserCreate
from utils.password import hash_password, verify_password
from schemas.auth import Credentials
from fastapi import HTTPException

class UserRepository(CURDBase[User, UserCreate, UserCreate]):
    def __init__(self):
        super().__init__(User)

    async def create_user(self, user_in : UserCreate) -> User:
        data = user_in.model_dump(exclude={"roles_id"})
        data["password"] = hash_password(password=user_in.password)
        user = await User.create(**data)
        normal_user_role = await Role.filter(name="user").first()
        await user.roles.add(normal_user_role)
        return user

    async def get_user_by_name(self, username: str) -> User|None:
        return await User.filter(username=username).first()

    async def authenticate(self, credentials: Credentials) -> User:
        user = await self.get_user_by_name(credentials.username)
        if user is None or not verify_password(credentials.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="user is disabled")
        return user

    async def update_last_login(self, user: User):
        user.last_login = datetime.now()
        await user.save(update_fields=["last_login"])

user_repository = UserRepository()
