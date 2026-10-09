import logging
import traceback
import json

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


async def HttpExcHandle(request: Request, exc: HTTPException):
    error_details = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "status_code": exc.status_code,
        "exception_type": type(exc).__name__,
        "exception_msg": str(exc.detail),
        "traceback": traceback.format_exc(),
    }

    if exc.status_code >= 500:
        logger.error(f"HTTP {exc.status_code}exception: {request.method} {request.url.path} - {exc.detail} error_details: {error_details}")
    elif exc.status_code >= 400:
        logger.warning(f"HTTP{exc.status_code}exception: {request.method} {request.url.path} - {exc.detail} error_details: {error_details}")

    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "msg": exc.detail, "data": None},
    )