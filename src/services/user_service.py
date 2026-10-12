from schemas.users import UserOut, User_info_change
from schemas.base import ResponseBase
from models import User, Role

from fastapi import HTTPException

class UserService:
    async def get_user_by_id(self, user_id: int) -> ResponseBase[UserOut]:
        user = await User.filter(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User Not Found")
        data = UserOut.model_validate(user)
        return ResponseBase[UserOut](msg="search success", data=data)

    async def get_user_by_username(self, username: str) -> ResponseBase[UserOut]:
        user = await User.filter(id=username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User Not Found")
        data = UserOut.model_validate(user)
        return ResponseBase[UserOut](msg="search success", data=data)

    async def get_users_list(self,
                             keyword: str|None,
                             page: int,
                             page_size: int,
    ) -> ResponseBase[list[UserOut]]:
        queryset = User.all()
        if keyword:
            queryset = queryset.filter(username__icontains=keyword)
        total = await queryset.count()
        offset = (page - 1) * page_size
        user_list = await queryset.offset(offset).limit(page_size).prefetch_related("roles").all()
        data = [UserOut.model_validate(each) for each in user_list]
        return ResponseBase[list[UserOut]](msg="users get successfully", data=data, extra_data=total)

    async def change_username(self,
                              user: User,
                              new_username,
    ) -> ResponseBase[UserOut]:
        try_name = User_info_change(username=new_username)
        if await User.filter(username=new_username).exists():
            raise HTTPException(status_code=400, detail="Username already exists")
        user.username = new_username
        await user.save()
        data = UserOut.model_validate(user)
        return ResponseBase[UserOut](msg="username change success", data=data)

    async def change_email(self,
                           user: User,
                           new_email: str,
    ) -> ResponseBase[UserOut]:
        if await User.filter(email=new_email).exists():
            raise HTTPException(status_code=400, detail="Email already exists")
        user.email = new_email
        await user.save()
        data = UserOut.model_validate(user)
        return ResponseBase[UserOut](code=200, msg="email changed", data=data)

    async def disable_user(self,
                           username: str,
                           user: User
    ) -> ResponseBase[UserOut]:
        if username == user.username:
            raise HTTPException(status_code=400, detail="You cannot disable yourself")
        chosen_user = await User.filter(username=username).first()
        if not chosen_user:
            raise HTTPException(status_code=404, detail="User Not Found")
        chosen_user.is_active = False
        await chosen_user.save()
        data = UserOut.model_validate(chosen_user)
        return ResponseBase[UserOut](msg="Disabled success", data=data)

    async def set_superuser(self,
                            username: str
    ) -> ResponseBase[UserOut]:
        chosen_user = await User.filter(username=username).prefetch_related("roles").first()
        if not chosen_user:
            raise HTTPException(status_code=404, detail="User doesn't exist")
        admin_role = await Role.filter(name="admin").first()
        if not admin_role:
            raise HTTPException(status_code=404, detail="Role Not Found")
        chosen_user.is_superuser = True
        await chosen_user.roles.add(admin_role)
        await chosen_user.save()
        return ResponseBase(msg="Set superuser success")

    async def remove_superuser(self,
                               username: str,
                               user: User
    ) -> ResponseBase[UserOut]:
        chosen_user = await User.filter(username=username).prefetch_related("roles").first()
        if not chosen_user:
            raise HTTPException(status_code=404, detail="User Not Found")
        if chosen_user.username == user.username:
            raise HTTPException(status_code=400, detail="Cannot remove yourself! ")
        if not chosen_user.is_superuser:
            raise HTTPException(status_code=400, detail="The chosen user is not superuser! ")
        admin_role = await Role.filter(name="admin").first()
        if not admin_role:
            raise HTTPException(status_code=404, detail="Role Not Found")
        chosen_user.is_superuser = False
        await chosen_user.roles.remove(admin_role)
        await chosen_user.save()
        return ResponseBase(msg="The superuser removed successfully")

    async def user_delete(self,
                          user_id: int,
                          user_me: User
    ) -> ResponseBase:
        if user_id == user_me.id:
            raise HTTPException(status_code=400, detail="You cannot delete yourself")
        user = await User.filter(id=user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User doesn't exist")
        elif user.is_superuser:
            raise HTTPException(status_code=403, detail="You have no right to do this")
        else:
            await user.delete()
            return ResponseBase(code=200, msg="Deleted successfully", data=None)








user_service = UserService()