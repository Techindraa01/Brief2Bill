"""Health and version endpoints"""
from fastapi import APIRouter, Depends
from ...core.config import Settings, get_settings


router = APIRouter()


@router.get("/health")
async def health():
    """Liveness check"""
    return {"ok": True, "version": "1.0.0"}


@router.get("/version")
async def version(settings: Settings = Depends(get_settings)):
    """Version and defaults info"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "default_provider": settings.default_provider,
        "default_model": settings.default_model
    }
