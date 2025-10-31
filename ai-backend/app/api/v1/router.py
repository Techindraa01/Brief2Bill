"""V1 API router aggregation"""
from fastapi import APIRouter
"""Versioned API router registration."""

from fastapi import APIRouter

from .health import router as health_router
from .providers import router as providers_router
from .draft import router as draft_router
from .validate import router as validate_router
from .repair import router as repair_router
from .totals import router as totals_router
from .upi import router as upi_router
from .version import router as version_router


def create_v1_router() -> APIRouter:
    """Create and configure v1 API router"""
    router = APIRouter(prefix="/v1")

    # Include all sub-routers
    router.include_router(health_router, tags=["health"])
    router.include_router(version_router, tags=["health"])
    router.include_router(providers_router, tags=["providers"])
    router.include_router(draft_router, tags=["draft"])
    router.include_router(validate_router, tags=["validation"])
    router.include_router(repair_router, tags=["validation"])
    router.include_router(totals_router, tags=["totals"])
    router.include_router(upi_router, tags=["upi"])

    return router
