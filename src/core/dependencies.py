from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.my_jwt import decode_token
from fastapi import Depends, HTTPException, status
from models import User

import jwt

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="failed"
    )
    try:
        token = credentials.credentials
        payload = decode_token(token, "access")
        if payload.user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = await User.filter(id=payload.user_id).prefetch_related("roles").first()
    if user is None:
        raise credentials_exception
    elif not user.is_active:
        raise credentials_exception
    return user

async def require_admin(current_user: User = Depends(get_current_user)):
    the_roles = [roles.name for roles in current_user.roles]
    if "admin" not in the_roles:
        raise HTTPException(status_code=403, detail="You're just nobody, please call your parents")
    return current_user
