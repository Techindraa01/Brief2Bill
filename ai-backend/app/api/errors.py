"""Standardised error handling for the API."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..core.logging import get_logger

logger = get_logger(__name__)


class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


def create_error_response(code: str, message: str, request_id: str, status_code: int, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
                "details": details or {},
            }
        },
    )


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error("api_error", code=exc.code, message=exc.message, request_id=request_id)
    return create_error_response(exc.code, exc.message, request_id, exc.status_code, exc.details)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning("validation_error", request_id=request_id, errors=exc.errors())
    return create_error_response(
        "VALIDATION_ERROR",
        "Request validation failed",
        request_id,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        {"errors": exc.errors()},
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning("http_exception", request_id=request_id, status=exc.status_code)
    return create_error_response("HTTP_ERROR", str(exc.detail), request_id, exc.status_code)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error("unhandled_exception", request_id=request_id, exc_info=exc)
    return create_error_response("INTERNAL", "An internal error occurred", request_id, status.HTTP_500_INTERNAL_SERVER_ERROR)
