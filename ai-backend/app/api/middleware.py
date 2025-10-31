"""Middleware for request ID tracking and logging"""
import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog


logger = structlog.get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add request ID to all requests and responses"""

    async def dispatch(self, request: Request, call_next):
        # Get or generate request ID
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))

        # Store in request state
        request.state.request_id = request_id

        # Bind to logger context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-Id"] = request_id

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Get request details
        request_id = getattr(request.state, "request_id", "unknown")
        method = request.method
        path = request.url.path

        # Log request
        logger.info(
            "request_started",
            method=method,
            path=path,
            request_id=request_id
        )

        # Process request
        response = await call_next(request)

        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000

        # Log response
        logger.info(
            "request_completed",
            method=method,
            path=path,
            status_code=response.status_code,
            latency_ms=round(latency_ms, 2),
            request_id=request_id
        )

        return response
