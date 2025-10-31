"""Draft generation endpoint"""
from fastapi import APIRouter, Depends, Header
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from ...services.provider_service import ProviderService
from ...services.drafting_service import DraftingService
from ...api.deps import get_provider_service, get_drafting_service
from ...api.errors import APIError
import json
from pathlib import Path


router = APIRouter()


class DraftRequest(BaseModel):
    """Request to generate document bundle"""
    prompt: str = Field(..., min_length=5)
    prefer: Optional[List[str]] = None
    currency: str = "INR"
    defaults: Optional[Dict[str, Any]] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    workspace_id: str = "default"


@router.post("/draft")
async def create_draft(
    request: DraftRequest,
    provider_service: ProviderService = Depends(get_provider_service),
    drafting_service: DraftingService = Depends(get_drafting_service),
    x_provider: Optional[str] = Header(None),
    x_model: Optional[str] = Header(None),
    x_workspace_id: Optional[str] = Header(None)
):
    """Generate document bundle from requirement"""

    # Resolve provider and model with precedence
    workspace_id = request.workspace_id or x_workspace_id or "default"
    provider_name = request.provider or x_provider
    model_name = request.model or x_model

    provider_name, model_name = provider_service.resolve_provider_and_model(
        provider_override=provider_name,
        model_override=model_name,
        workspace_id=workspace_id
    )

    # Get provider instance
    provider = provider_service.get_provider(provider_name)
    if not provider:
        raise APIError(
            code="PROVIDER_NOT_ENABLED",
            message=f"Provider {provider_name} is not enabled. Check API key configuration.",
            status_code=400
        )

    # Generate bundle using provider capabilities for structured output
    try:
        bundle = await drafting_service.generate_bundle(
            provider=provider,
            model=model_name,
            requirement=request.prompt,
            doc_types=request.prefer,
            currency=request.currency,
            seller_defaults=request.defaults
        )

        return bundle

    except Exception as e:
        raise APIError(
            code="GENERATION_FAILED",
            message=f"Failed to generate document: {str(e)}",
            status_code=500
        )
