from fastapi import APIRouter,HTTPException, Depends, Query, Body
from pydantic import BaseModel, EmailStr

from models import User, Role
from schemas.base import ResponseBase
from schemas.users import UserOut, User_info_change
from core.dependencies import require_admin, get_current_user
from typing import Literal
from schemas.roles import RoleOut

router = APIRouter()

@router.get("/me")
async def get_me_info(user: User = Depends(get_current_user)) -> ResponseBase[dict]:
    user_out = UserOut.model_validate(user)
    data = user_out.model_dump()
    return ResponseBase(code=200, msg="Get information successfully", data=data)

@router.get("/user")
async def search_user(user_id: int | None = Query(None, description="user's id, fill this info or username"),
                      username: str | None = Query(None, description="username, fill this info or user_id"),
                      user_me: User = Depends(get_current_user),
                      ) -> ResponseBase[UserOut]:
    if not username and not user_id:
        raise HTTPException(status_code=400, detail="Must provide user_id or username")
    if not user_id :
        user = await User.filter(username=username).first()
    elif user_id and not username:
        user=await User.filter(id=user_id).first()
    else:
        user=await User.filter(id=user_id).first()
        if not user or user.username != username:
            raise HTTPException(status_code=400, detail="Wrong id or username")
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")
    data = UserOut.model_validate(user)
    return ResponseBase[UserOut](msg="search success", data=data)

@router.get("/users")
async def search_users(
        keyword: str | None = Query(None, description="the keyword of user"),
        page: int = Query(1, description="which page"),
        page_size: int = Query(10, ge=1, le=50, description="page size"),
        user_me: User = Depends(get_current_user),
) -> ResponseBase[list[UserOut]]:
    queryset = User.all()
    if keyword:
        queryset = queryset.filter(username__icontains=keyword)
    total = await queryset.count()
    offset = (page-1)*page_size
    user_list = await queryset.offset(offset).limit(page_size).prefetch_related("roles").all()
    data = [UserOut.model_validate(each) for each in user_list]
    return ResponseBase[list[UserOut]](msg="users get successfully", data=data, extra_data=total)

@router.patch("/username")
async def change_username(new_username: str = Body(...), user: User = Depends(get_current_user)) -> ResponseBase[UserOut]:
    try_name = User_info_change(username=new_username)
    if await User.filter(username=new_username).exists():
        raise HTTPException(status_code=400, detail="Username already exists")
    user.username = new_username
    await user.save()
    data = UserOut.model_validate(user)
    return ResponseBase[UserOut](code=200, msg="username change success", data=data)

@router.patch("/email")
async def change_email(new_email: EmailStr = Body(...), user: User = Depends(get_current_user)) -> ResponseBase[UserOut]:
    if await User.filter(email=new_email).exists():
        raise HTTPException(status_code=400, detail="Email already exists")
    user.email = new_email
    await user.save()
    data = UserOut.model_validate(user)
    return ResponseBase[UserOut](code=200, msg="email changed", data=data)

@router.patch("/disable-user/{username}")
async def disable_user(username: str, user: User = Depends(require_admin)) -> ResponseBase[UserOut]:
    if username == user.username:
        raise HTTPException(status_code=400, detail="You cannot disable yourself")
    chosen_user = await User.filter(username=username).first()
    if not chosen_user:
        raise HTTPException(status_code=404, detail="User Not Found")
    chosen_user.is_active = False
    await chosen_user.save()
    data = UserOut.model_validate(chosen_user)
    return ResponseBase[UserOut](msg="Disabled success", data=data)

@router.patch("/set-superuser/{username}")
async def set_superuser(username: str, user: User = Depends(require_admin)) -> ResponseBase:
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

@router.patch("/remove_superuser/{username}")
async def remove_superuser(username: str, user: User = Depends(require_admin)) -> ResponseBase:
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

@router.delete("/delete/{user_id}")
async def user_delete(user_id: int, user_me: User = Depends(require_admin)):
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

@router.delete("/delete-me")
async def delete_me(
        confirmation: Literal["yes", "no"] = Query(description="Supported words: yes or no"),
        user: User = Depends(get_current_user)
) -> ResponseBase:
    if confirmation == "yes":
        await user.delete()
        return ResponseBase(msg="deleted successfully")
    elif confirmation == "no":
        return ResponseBase(msg="Delete operation cancelled")
    else:
        raise HTTPException(status_code=400, detail="Unsupported word, please try 'yes' or 'no'")

@router.patch("/SetRole")
async def SetRole(username: str, role_name: str, user_me: User = Depends(require_admin)) -> ResponseBase[list[RoleOut]]:
    user = await User.filter(username=username).first()
    role = await Role.filter(name=role_name).first()
    if not user or not role:
        raise HTTPException(status_code=404, detail="User or Role Not Found")
    if await user.roles.filter(name=role_name).exists():
        raise HTTPException(status_code=400, detail="User already had this role")
    await user.roles.add(role)
    data = [RoleOut.model_validate(each) for each in await user.roles.all()]
    return ResponseBase[list[RoleOut]](code=200, msg="SetRole success", data=data)