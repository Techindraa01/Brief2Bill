"""FastAPI application factory."""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api.errors import (
    APIError,
    api_error_handler,
    general_exception_handler,
    http_exception_handler,
    validation_error_handler,
)
from .api.middleware import LoggingMiddleware, RequestIDMiddleware
from .api.v1.router import create_v1_router
from .core.config import get_settings
from .core.logging import setup_logging
from .core.security import enforce_api_key
from .lifecycles import lifespan


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_json)

    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan, dependencies=[Depends(enforce_api_key)])

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    app.include_router(create_v1_router())
    return app
