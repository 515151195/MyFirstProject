from .base import router as base_router
from .users import router as users_router
from .roles import router as roles_router

from fastapi import APIRouter

v1_router = APIRouter()
v1_router.include_router(base_router, prefix="/base", tags=["base"])
v1_router.include_router(users_router, prefix="/users", tags=["users"])
v1_router.include_router(roles_router, prefix="/roles", tags=["roles"])