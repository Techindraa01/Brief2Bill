"""Custom middleware for request IDs and structured logging."""

from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..core.logging import get_logger

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response: Response = await call_next(request)
        latency_ms = round((time.time() - start) * 1000, 2)
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            latency_ms=latency_ms,
            request_id=getattr(request.state, "request_id", "unknown"),
        )
        return response
