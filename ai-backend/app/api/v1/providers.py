"""Provider management endpoints"""
from fastapi import APIRouter, Depends
from typing import List
from pydantic import BaseModel
from ...services.provider_service import ProviderService
from ...api.deps import get_provider_service


router = APIRouter()


class ProviderSelectRequest(BaseModel):
    """Request to select provider/model"""
    provider: str
    model: str
    workspace_id: str = "default"


class ProviderSelectResponse(BaseModel):
    """Response from provider selection"""
    ok: bool
    active: dict


@router.get("/providers")
async def list_providers(
    provider_service: ProviderService = Depends(get_provider_service)
) -> List[str]:
    """List all enabled provider names"""

    return provider_service.list_provider_names()


@router.get("/providers/{provider_name}/models")
async def list_provider_models(
    provider_name: str,
    provider_service: ProviderService = Depends(get_provider_service)
):
    """List available models for a specific provider"""
    from ...api.errors import APIError

    # Check if provider is enabled
    if not provider_service.is_provider_enabled(provider_name):
        raise APIError(
            code="PROVIDER_NOT_ENABLED",
            message=f"Provider '{provider_name}' is not enabled or does not exist",
            status_code=404
        )

    # Get provider instance
    provider = provider_service.get_provider(provider_name)

    # Fetch models from provider
    models = await provider.list_models()

    return {
        "provider": provider_name,
        "models": [m.model_dump() for m in models]
    }


@router.post("/providers/select")
async def select_provider(
    request: ProviderSelectRequest,
    provider_service: ProviderService = Depends(get_provider_service)
):
    """Set active provider/model for workspace"""
    try:
        provider_service.set_selection(
            provider=request.provider,
            model=request.model,
            workspace_id=request.workspace_id
        )
        
        return {
            "ok": True,
            "active": {
                "provider": request.provider,
                "model": request.model,
                "workspace_id": request.workspace_id
            }
        }
    except ValueError as e:
        from ...api.errors import APIError
        raise APIError(
            code="INVALID_PROVIDER",
            message=str(e),
            status_code=400
        )


@router.get("/providers/active")
async def get_active_provider(
    workspace_id: str = "default",
    provider_service: ProviderService = Depends(get_provider_service)
):
    """Get active provider/model for workspace"""
    selection = provider_service.get_selection(workspace_id)
    
    return {
        "provider": selection.provider,
        "model": selection.model,
        "workspace_id": selection.workspace_id
    }

