import logging
import time
import hashlib
import json

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.responses import Response

from models import IdempotencyRecord
from models.base import IdeStatus
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


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        body_bytes = await request.body()
        req_info = f"{request.method}{request.url.path}{body_bytes.decode('utf-8')}"
        request_digest = hashlib.sha256(req_info.encode()).hexdigest()

        record = await IdempotencyRecord.get_or_none(idempotency_key=idempotency_key)
        if record:
            if record.status == IdeStatus.SUCCESS:
                return JSONResponse(content=record.response_data)
            elif record.status == IdeStatus.PENDING:
                return HTTPException(status_code=409, detail="Request is processing, please retry later")
            elif record.status == IdeStatus.FAILED:
                raise HTTPException(status_code=400, detail="This idempotency key already failed, please use new key")
        record = await IdempotencyRecord.create(
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            response_data=None,
            status=IdeStatus.PENDING,
        )
        response = await call_next(request)

        resp_body = b""
        async for chunk in response.body_iterator:
            resp_body += chunk
        response.body_iterator = iter([resp_body])
        resp_json = json.loads(resp_body)

        record.status = IdeStatus.SUCCESS
        record.response_data = resp_json
        await record.save()
        return response