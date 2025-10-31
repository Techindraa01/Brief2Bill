"""FastAPI app factory"""
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from .core.config import get_settings
from .core.logging import setup_logging
from .lifecycles import lifespan
from .api.v1.router import create_v1_router
from .api.middleware import RequestIDMiddleware, LoggingMiddleware
from .api.errors import (
    APIError,
    api_error_handler,
    validation_error_handler,
    http_exception_handler,
    general_exception_handler
)


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    settings = get_settings()

    # Setup logging
    setup_logging(log_level=settings.log_level, json_logs=settings.log_json)

    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan
    )

    # Add middleware (order matters - first added is outermost)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # Register exception handlers
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Include routers
    v1_router = create_v1_router()
    app.include_router(v1_router)

    return app


if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
