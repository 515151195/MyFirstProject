from settings import settings
from tortoise import Tortoise
from models import User, Role
from repositories import user_repository
from fastapi.middleware import Middleware
from schemas.users import UserCreate
from .middlewares import RequestLoggingMiddleware, IdempotencyMiddleware
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from .exceptions import (HttpExcHandle, DoesNotExistHandle, IntegrityHandle,
                         RequestValidationHandle, ResponseValidationHandle, UnhandledExceptionHandle)
from tortoise.exceptions import DoesNotExist, IntegrityError
from fastapi.exceptions import RequestValidationError, ResponseValidationError

import logging
logger = logging.getLogger(__name__)


def make_middlewares():
    middleware = [
        Middleware(RequestLoggingMiddleware),
        Middleware(IdempotencyMiddleware)
    ]
    return middleware

def register_exceptions(app: FastAPI):
    app.add_exception_handler(HTTPException, HttpExcHandle)
    app.add_exception_handler(DoesNotExist, DoesNotExistHandle)
    app.add_exception_handler(IntegrityError, IntegrityHandle)
    app.add_exception_handler(RequestValidationError, RequestValidationHandle)
    app.add_exception_handler(ResponseValidationError, ResponseValidationHandle)
    app.add_exception_handler(Exception, UnhandledExceptionHandle)

async def init_db() -> None:
    logger.info("Start database initial")
    await Tortoise.init(config=settings.TORTOISE_ORM, _enable_global_fallback=True)
    logger.info("Database initialized success")

async def init_admin() -> None:
    admin_role = await Role.filter(name="admin").first()
    if admin_role is None:
        admin_role = await Role.create(name="admin", desc="Administrator")

    user_role = await Role.filter(name="user").first()
    if user_role is None:
        user_role = await Role.create(name="user", desc="Normal user")

    admin = await User.filter(username="admin").first()
    if admin is None:
        admin = await user_repository.create_user(
            UserCreate(
                username="admin",
                email="admin@example.com",
                password="abcd1234",
                is_active=True,
                is_superuser=True,
            )
        )

    if not await admin.roles.filter(id=admin_role.id).exists():
        await admin.roles.add(admin_role)
    if not await admin.roles.filter(id=user_role.id).exists():
        await admin.roles.add(user_role)

async def init_data(routes: list) ->None :
    await init_db()
    await init_admin()
