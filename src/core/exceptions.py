import logging
import traceback
import json

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from tortoise.exceptions import DoesNotExist, IntegrityError
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from settings import settings


logger = logging.getLogger(__name__)


async def DoesNotExistHandle(request: Request, exc: DoesNotExist):
    error_details = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "exception_type": type(exc).__name__,
        "traceback": traceback.format_exc(),
    }

    error_message = f"DoesNotExist异常: {request.method} {request.url.path} - {exc}\n"
    error_message += f"Exception Type: {type(exc).__name__}\n"
    error_message += f"Exception Message: {str(exc)}\n"
    error_message += (
        f"\nStack Trace:\n{error_details.get('traceback', 'No traceback available')}\n"
    )
    error_message += "\nRequest Context:\n"
    for key, value in error_details.items():
        if key != "traceback":
            if isinstance(value, dict):
                error_message += (
                    f"  {key}: {json.dumps(value, indent=2, ensure_ascii=False)}\n"
                )
            else:
                error_message += f"  {key}: {value}\n"
    error_message += "=" * 80

    logger.error(error_message)

    if settings.DEBUG:
        msg = f"Object not found: {exc}, query_params: {request.query_params}"
    else:
        msg = "The requested resource cannot be found"

    content = {"code": 404, "msg": msg}
    return JSONResponse(content=content, status_code=404)



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

async def IntegrityHandle(request: Request, exc: IntegrityError):
    error_details = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "exception_type": type(exc).__name__,
        "exception_msg": str(exc),
        "traceback": traceback.format_exc(),
    }

    logger.error(f"Exception：{exc}", extra=error_details)
    if settings.DEBUG:
        msg = f"IntegrityError: {exc}"
    else:
        msg = "Data integrity error, please check your input data."

    content = {"code": 500, "msg": msg}
    return JSONResponse(content=content, status_code=500)

async def RequestValidationHandle(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    error_details = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "exception_type": type(exc).__name__,
        "exception_msg": str(exc),
        "validation_errors": exc.errors(),
        "traceback": traceback.format_exc(),
    }

    logger.warning(
        f"Request validation failed: {request.method} {request.url.path} - {len(exc.errors())} error(s)",
        extra=error_details
    )
    if settings.DEBUG:
        msg = f"RequestValidationError: {exc.errors()}"
    else:
        msg = "Input validation failed, please check your input format."

    content = {"code": 422, "msg": msg}
    return JSONResponse(content=content, status_code=422)


async def ResponseValidationHandle(
    request: Request, exc: ResponseValidationError
) -> JSONResponse:
    # 记录响应验证错误详情
    error_details = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "exception_type": type(exc).__name__,
        "exception_msg": str(exc),
        "validation_errors": exc.errors(),
        "traceback": traceback.format_exc(),
    }

    logger.warning(
        f"Request validation failed: {request.method} {request.url.path} - {len(exc.errors())} error(s)",
        extra=error_details
    )

    if settings.DEBUG:
        msg = f"ResponseValidationError: {exc.errors()}"
    else:
        msg = "The response format wrong"

    content = {"code": 500, "msg": msg}
    return JSONResponse(content=content, status_code=500)

async def UnhandledExceptionHandle(request: Request, exc: Exception) -> JSONResponse:
    """处理所有未捕获的异常"""
    # 记录未处理异常的详细信息
    error_details = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "exception_type": type(exc).__name__,
        "exception_msg": str(exc),
        "exception_module": getattr(exc, "__module__", "unknown"),
        "traceback": traceback.format_exc(),
    }

    # 尝试获取请求体信息（如果可能）
    try:
        if hasattr(request, "_body"):
            error_details["request_body_size"] = (
                len(request._body) if request._body else 0
            )
    except Exception:
        pass

    logger.critical(
        f"Unhandled exception: {request.method} {request.url.path} - {type(exc).__name__}: {exc}",
        extra=error_details
    )

    if settings.DEBUG:
        msg = f"Unhandled exception: {type(exc).__name__}: {exc}"
    else:
        msg = "Server internal error, please try again later."

    content = {"code": 500, "msg": msg}
    return JSONResponse(content=content, status_code=500)