"""FastAPI application factory."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
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

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _build_links(base_url: str) -> Iterable[tuple[str, dict[str, str]]]:
    """Return the curated list of root endpoint links."""

    def absolute(path: str) -> str:
        return f"{base_url}{path.lstrip('/')}"

    entries = (
        ("docs", {"label": "Interactive API docs", "path": "docs"}),
        ("redoc", {"label": "Reference documentation", "path": "redoc"}),
        ("health", {"label": "Service health", "path": "v1/health"}),
        ("providers", {"label": "Provider catalogue", "path": "v1/providers"}),
        ("version", {"label": "Service version", "path": "v1/version"}),
    )

    return tuple(
        (
            key,
            {
                "label": data["label"],
                "url": absolute(data["path"]),
            },
        )
        for key, data in entries
    )


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_json)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        dependencies=[Depends(enforce_api_key)],
    )

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

    @app.get("/", include_in_schema=False)
    async def root(request: Request) -> Response:
        """Serve a welcoming landing page or JSON based on the request."""

        base_url = str(request.base_url)
        if not base_url.endswith("/"):
            base_url = f"{base_url}/"

        links = _build_links(base_url)

        accepts = request.headers.get("accept", "").lower()
        wants_json = "application/json" in accepts and "text/html" not in accepts

        if wants_json:
            return JSONResponse(
                {
                    "status": "available",
                    "service": settings.app_name,
                    "version": settings.app_version,
                    "links": {name: link["url"] for name, link in links},
                }
            )

        context = {
            "request": request,
            "service_name": settings.app_name,
            "service_version": settings.app_version,
            "links": links,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
        return templates.TemplateResponse("home.html", context)

    app.include_router(create_v1_router())
    return app
