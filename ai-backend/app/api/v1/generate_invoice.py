"""Tax invoice generation endpoint."""

from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, Depends, Header, Request

from ...api.deps import get_provider_service
from ...api.errors import APIError
from ...core.logging import get_logger
from ...models.generation import GenerationRequest
from ...models.outputs import TaxInvoiceOutput
from ...prompts.prompt import build_invoice_prompt
from ...providers.base import PromptPacket
from ...services.output_processing import build_invoice_output
from ...services.provider_service import ProviderService
from ...utils.json_extractor import extract_json

router = APIRouter()
logger = get_logger(__name__)


@router.post("/generate/invoice", response_model=TaxInvoiceOutput)
async def generate_invoice(
    payload: GenerationRequest,
    request: Request,
    provider_service: ProviderService = Depends(get_provider_service),
    x_provider: Optional[str] = Header(default=None, alias="X-Provider"),
    x_model: Optional[str] = Header(default=None, alias="X-Model"),
    x_workspace: Optional[str] = Header(default=None, alias="X-Workspace-Id"),
) -> dict:
    workspace_id = x_workspace or payload.workspace_id or "default"
    selection = provider_service.resolve(
        workspace_id=workspace_id,
        provider_override=x_provider,
        model_override=x_model,
    )

    provider = provider_service.get_provider(selection.provider)
    if provider is None:
        raise APIError(
            code="PROVIDER_ERROR",
            message=f"Provider {selection.provider} is not available",
            status_code=503,
        )

    system_prompt, user_prompt, schema = build_invoice_prompt(payload)
    response_format = None
    capabilities = provider.capabilities()
    if capabilities.supports_json_schema:
        response_format = {
            "type": "json_schema",
            "json_schema": {"name": schema.get("title", "TaxInvoiceOutput"), "schema": schema},
        }
    elif capabilities.supports_plain_json:
        response_format = {"type": "json_object"}

    packet = PromptPacket(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=selection.model,
        temperature=0.2,
        response_format=response_format,
    )

    start = time.perf_counter()
    try:
        result = await provider.generate(packet)
    except Exception as exc:  # pragma: no cover
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(
            "invoice_generation_failed",
            provider=selection.provider,
            model=selection.model,
            workspace_id=workspace_id,
            request_id=request_id,
            error=str(exc),
        )
        raise APIError("PROVIDER_ERROR", "Failed to generate invoice", status_code=502) from exc

    latency_ms = int((time.perf_counter() - start) * 1000)

    try:
        raw_payload = extract_json(result.content)
    except ValueError as exc:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(
            "invoice_invalid_json",
            provider=selection.provider,
            model=selection.model,
            workspace_id=workspace_id,
            request_id=request_id,
        )
        raise APIError("PROVIDER_ERROR", "Provider returned invalid JSON", status_code=502) from exc

    output_model = build_invoice_output(raw_payload, payload)

    logger.info(
        "invoice_generated",
        provider=selection.provider,
        model=selection.model,
        latency_ms=latency_ms,
        workspace_id=workspace_id,
        request_id=getattr(request.state, "request_id", "unknown"),
    )

    return output_model.model_dump(exclude_none=True)
