from fastapi import APIRouter,HTTPException, Depends, Query, Body
from pydantic import BaseModel, EmailStr

from models import User, Role
from schemas.base import ResponseBase
from schemas.users import UserOut, User_info_change
from core.dependencies import require_admin, get_current_user
from typing import Literal
from schemas.roles import RoleOut
from services.user_service import user_service

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
        return user_service.get_user_by_username(username=username)
    elif user_id and not username:
        return user_service.get_user_by_id(user_id=user_id)
    else:
        return user_service.get_user_by_id(user_id=user_id)

@router.get("/users")
async def search_users(
        keyword: str | None = Query(None, description="the keyword of user"),
        page: int = Query(1, description="which page"),
        page_size: int = Query(10, ge=1, le=50, description="page size"),
        user_me: User = Depends(get_current_user),
) -> ResponseBase[list[UserOut]]:
    return user_service.get_users_list(
        keyword= keyword,
        page= page,
        page_size= page_size
    )

@router.patch("/username")
async def change_username(new_username: str = Body(...), user: User = Depends(get_current_user)) -> ResponseBase[UserOut]:
    return user_service.change_username(user=user, new_username=new_username)

@router.patch("/email")
async def change_email(new_email: EmailStr = Body(...), user: User = Depends(get_current_user)) -> ResponseBase[UserOut]:
    return user_service.change_email(user=user, new_email=new_email)

@router.patch("/disable-user/{username}")
async def disable_user(username: str, user: User = Depends(require_admin)) -> ResponseBase[UserOut]:
    return user_service.disable_user(username=username, user=user)

@router.patch("/set-superuser/{username}")
async def set_superuser(username: str, user: User = Depends(require_admin)) -> ResponseBase:
    return user_service.set_superuser(username=username)

@router.patch("/remove_superuser/{username}")
async def remove_superuser(username: str, user: User = Depends(require_admin)) -> ResponseBase:
    return user_service.remove_superuser(username=username, user=user)

@router.delete("/delete/{user_id}")
async def user_delete(user_id: int, user_me: User = Depends(require_admin)):
    return user_service.user_delete(user_id, user_me)

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