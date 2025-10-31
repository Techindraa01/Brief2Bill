"""Startup/shutdown lifecycle hooks"""
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .core.config import get_settings
from .services.provider_service import ProviderService
from .services.validation import ValidationService
from .services.drafting_service import DraftingService
from .core.logging import get_logger


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""

    # Startup
    logger.info("application_starting")

    settings = get_settings()

    # Create HTTP client
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(60.0),
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
    )
    app.state.http_client = http_client

    # Initialize services
    provider_service = ProviderService(settings, http_client)
    validation_service = ValidationService()
    drafting_service = DraftingService(validation_service)

    app.state.provider_service = provider_service
    app.state.validation_service = validation_service
    app.state.drafting_service = drafting_service

    logger.info("application_started", providers=len(provider_service._providers))

    yield

    # Shutdown
    logger.info("application_shutting_down")

    await http_client.aclose()

    logger.info("application_shutdown_complete")
