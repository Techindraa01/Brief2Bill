"""Provider discovery and selection endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from ...api.deps import get_provider_service
from ...api.errors import APIError
from ...services.provider_service import ProviderService

router = APIRouter()


class ProviderDescriptor(BaseModel):
    name: str
    enabled: bool
    models: list[Dict[str, Any]]


class ProvidersResponse(BaseModel):
    providers: list[ProviderDescriptor]


class ProviderSelectRequest(BaseModel):
    provider: str = Field(pattern="^(openrouter|groq|openai|gemini)$")
    model: str
    workspace_id: str = "default"


class ProviderSelectResponse(BaseModel):
    ok: bool = True
    active: Dict[str, str]


@router.get("/providers", response_model=ProvidersResponse)
async def list_providers(provider_service: ProviderService = Depends(get_provider_service)) -> ProvidersResponse:
    providers = await provider_service.describe_providers()
    return ProvidersResponse(providers=providers)


@router.post("/providers/select", response_model=ProviderSelectResponse)
async def select_provider(request: ProviderSelectRequest, provider_service: ProviderService = Depends(get_provider_service)) -> ProviderSelectResponse:
    try:
        provider_service.set_selection(request.provider, request.model, request.workspace_id)
    except ValueError as exc:  # provider not enabled
        raise APIError(code="INVALID_PROVIDER", message=str(exc), status_code=400) from exc
    return ProviderSelectResponse(active={"provider": request.provider, "model": request.model, "workspace_id": request.workspace_id})


@router.get("/providers/active")
async def get_active_provider(
    workspace_id: str = Query(default="default"),
    provider_service: ProviderService = Depends(get_provider_service),
) -> Dict[str, str]:
    selection = provider_service.get_selection(workspace_id)
    return {"provider": selection.provider, "model": selection.model, "workspace_id": selection.workspace_id}
