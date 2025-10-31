"""Custom exceptions and error handling"""
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import structlog


logger = structlog.get_logger(__name__)


class APIError(Exception):
    """Base API error with error envelope"""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


def create_error_response(
    code: str,
    message: str,
    request_id: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 400
) -> JSONResponse:
    """Create standardized error response"""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
                "details": details or {}
            }
        }
    )


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle APIError exceptions"""
    request_id = request.state.request_id if hasattr(request.state, "request_id") else "unknown"

    logger.error(
        "api_error",
        code=exc.code,
        message=exc.message,
        request_id=request_id,
        path=request.url.path
    )

    return create_error_response(
        code=exc.code,
        message=exc.message,
        request_id=request_id,
        details=exc.details,
        status_code=exc.status_code
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    request_id = request.state.request_id if hasattr(request.state, "request_id") else "unknown"

    logger.warning(
        "validation_error",
        errors=exc.errors(),
        request_id=request_id,
        path=request.url.path
    )

    return create_error_response(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        request_id=request_id,
        details={"errors": exc.errors()},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions"""
    request_id = request.state.request_id if hasattr(request.state, "request_id") else "unknown"

    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        request_id=request_id,
        path=request.url.path
    )

    return create_error_response(
        code="HTTP_ERROR",
        message=str(exc.detail),
        request_id=request_id,
        status_code=exc.status_code
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    request_id = request.state.request_id if hasattr(request.state, "request_id") else "unknown"

    logger.error(
        "unhandled_exception",
        exc_info=exc,
        request_id=request_id,
        path=request.url.path
    )

    return create_error_response(
        code="INTERNAL_ERROR",
        message="An internal error occurred",
        request_id=request_id,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
