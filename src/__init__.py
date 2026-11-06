import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Request
from tortoise import Tortoise
from settings import settings
from core.init_app import init_data, make_middlewares
from api import api_router
from fastapi.responses import JSONResponse
from log.logging_config import set_up_logging
from core.init_app import register_exceptions
from core.limiter import register_limiter

set_up_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_data(app.routes)
    try:
        yield
    finally:
        await Tortoise.close_connections()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_TITLE,
        version=settings.VERSION,
        lifespan=lifespan,
        middleware=make_middlewares(),
    )
    register_exceptions(app=app)

    register_limiter(app=app)

    app.include_router(api_router, prefix="/api")
    return app

app = create_app()
