"""Draft generation endpoint."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field

from ...api.deps import get_drafting_service, get_provider_service
from ...api.errors import APIError
from ...core.rate_limit import get_rate_limiter
from ...services.drafting_service import DraftingService
from ...services.provider_service import ProviderSelection, ProviderService

router = APIRouter()


class DraftRequest(BaseModel):
    prompt: str = Field(min_length=5)
    prefer: Optional[List[str]] = None
    currency: str = "INR"
    defaults: Optional[Dict[str, Any]] = None
    provider: Optional[str] = Field(default=None, pattern="^(openrouter|groq|openai|gemini)?$")
    model: Optional[str] = None
    workspace_id: str = "default"


@router.post("/draft")
async def create_draft(
    payload: DraftRequest,
    request: Request,
    provider_service: ProviderService = Depends(get_provider_service),
    drafting_service: DraftingService = Depends(get_drafting_service),
    x_provider: Optional[str] = Header(default=None, alias="X-Provider"),
    x_model: Optional[str] = Header(default=None, alias="X-Model"),
    x_workspace: Optional[str] = Header(default=None, alias="X-Workspace-Id"),
):
    workspace_id = payload.workspace_id or x_workspace or "default"
    limiter = get_rate_limiter(request.app)
    client_host = request.client.host if request.client else "anonymous"
    if not limiter.allow(f"{workspace_id}:{client_host}"):
        raise APIError(code="RATE_LIMIT", message="Rate limit exceeded", status_code=429)

    selection: ProviderSelection = provider_service.resolve(
        workspace_id=workspace_id,
        provider_override=payload.provider or x_provider,
        model_override=payload.model or x_model,
    )

    provider = provider_service.get_provider(selection.provider)

    bundle = await drafting_service.generate_bundle(
        provider=provider,
        model=selection.model,
        requirement=payload.prompt,
        doc_types=payload.prefer,
        currency=payload.currency,
        seller_defaults=payload.defaults,
    )
    return bundle
