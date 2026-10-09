import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.responses import Response

from log.context import reset_request_id, set_request_id


logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id, token = set_request_id(request.headers.get("x-request-id"))
        started_at = time.perf_counter()
        logger.info(
            "request started method=%s, path=%s",
            request.method,
            request.url.path
        )

        try:
            response = await call_next(request)
            elapsed_ms = (time.perf_counter()-started_at) * 1000
            response.headers["X-Request-ID"] = request_id
            logger.info(
                "request finished method=%s path=%s elapsed_ms=%.2f",
                request.method,
                request.url.path,
                elapsed_ms
            )
            return response
        except Exception:
            elapsed_ms = (time.perf_counter()-started_at) * 1000
            logger.exception(
                "request failed method=%s path=%s elapsed_ms=%.2f",
                request.method,
                request.url.path,
                elapsed_ms
            )
            response = JSONResponse(
                status_code=500,
                content={"code": 500, "msg": "internal server error"},
            )
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            reset_request_id(token)