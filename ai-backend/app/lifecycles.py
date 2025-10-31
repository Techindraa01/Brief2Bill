"""Application lifespan management."""

from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from .core.config import get_settings
from .core.logging import get_logger
from .core.rate_limit import RateLimiter
from .services.provider_service import ProviderService
from .services.validation import ValidationService
from .services.drafting_service import DraftingService

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("application_startup")

    http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
    app.state.http_client = http_client

    provider_service = ProviderService(settings=settings, http_client=http_client)
    validation_service = ValidationService()
    drafting_service = DraftingService(validation_service)
    rate_limiter = RateLimiter(per_minute=settings.rate_limit_per_minute)

    app.state.provider_service = provider_service
    app.state.validation_service = validation_service
    app.state.drafting_service = drafting_service
    app.state.rate_limiter = rate_limiter

    try:
        yield
    finally:
        logger.info("application_shutdown")
        await http_client.aclose()
