from .v1 import v1_router

from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(v1_router, prefix="/v1")