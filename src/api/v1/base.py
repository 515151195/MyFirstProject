from fastapi import APIRouter, HTTPException, Depends
from schemas.auth import Credentials, RefreshRequest, ChangePassword
from repositories import user_repository
from settings.config import settings
from utils.my_jwt import create_token_pair, decode_token
from schemas.users import UserCreate, UserOut, UserSignUp
from models import User
from schemas.base import ResponseBase
from core.dependencies import get_current_user
from utils.password import verify_password, hash_password

from tortoise.expressions import Q

router = APIRouter()

@router.post("/login")
async def login(credentials: Credentials):
    user = await user_repository.authenticate(credentials)
    await user_repository.update_last_login(user)
    access_token, refresh_token = create_token_pair(user.id)
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }
    return ResponseBase[dict](code=200, msg="login success", data=data)

@router.post("/refresh_token")
async def refresh_token(body: RefreshRequest) -> ResponseBase[dict]:
    try:
        payload = decode_token(body.refresh_token, "refresh")
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = await user_repository.get(payload.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User is unavailable")

    access_token, refresh_token = create_token_pair(user.id)
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }
    return ResponseBase[dict](code=200, msg="refresh token success", data=data)

@router.post("/signup")
async def signup(user_data: UserSignUp) -> ResponseBase[UserOut]:
    user = await User.filter(Q(username=user_data.username) | Q(email=user_data.email)).first()
    if user:
        raise HTTPException(status_code=400, detail="The username or email has existed")
    else:
        user_create = UserCreate(username=user_data.username,
                                 email=user_data.email,
                                 password=user_data.password)
        user = await user_repository.create_user(user_create)
    return ResponseBase[UserOut](code=200,
                                 msg="signup success",
                                 data=UserOut(
                                     id=user.id,
                                     username=user.username,
                                     email=user.email,
                                     created_at=user.created_at,
                                    )
                                 )

@router.post("/change-password")
async def change_password(three_password: ChangePassword, user: User = Depends(get_current_user)) -> ResponseBase:
    if not verify_password(three_password.old_password, user.password):
        raise HTTPException(status_code=400, detail="Wrong password, aren't you the owner of this account?")
    if three_password.new_password != three_password.new_password_again:
        raise HTTPException(status_code=400, detail="The two new password should be the same")
    user.password = hash_password(three_password.new_password)
    await user.save()
    return ResponseBase(code=200, msg="Password has been changed successfully!")

"""
@router.post("/reset_password")
async def reset_password()
"""