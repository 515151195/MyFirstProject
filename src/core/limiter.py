from fastapi import FastAPI
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.exceptions import rate_limit_handler
from settings import settings


limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=(
        f"redis://{settings.REDIS_HOST}:"
        f"{settings.REDIS_PORT}/{settings.REDIS_DB}"
    ),
)

def register_limiter(app: FastAPI):
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)