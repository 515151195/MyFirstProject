from .base import router as base_router
from .users import router as users_router
from .roles import router as roles_router
from .invitation import router as inv_router
from .organizations import router as org_router
from .approval import router as approval_router

from fastapi import APIRouter

v1_router = APIRouter()
v1_router.include_router(base_router, prefix="/base", tags=["base"])
v1_router.include_router(users_router, prefix="/users", tags=["users"])
v1_router.include_router(roles_router, prefix="/roles", tags=["roles"])
v1_router.include_router(inv_router, prefix="/invitations", tags=["invitations"])
v1_router.include_router(org_router, prefix="/organizations", tags=["organizations"])
v1_router.include_router(approval_router, prefix="/approvals", tags=["approvals"])