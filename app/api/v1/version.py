"""Version metadata endpoint."""

from fastapi import APIRouter, Depends

from ...core.config import Settings, get_settings


router = APIRouter()


@router.get("/version")
async def version(settings: Settings = Depends(get_settings)) -> dict:
    """Return service version and default provider/model."""

    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "default_provider": settings.default_provider,
        "default_model": settings.default_model,
    }
