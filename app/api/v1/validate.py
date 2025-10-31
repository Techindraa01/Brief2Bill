"""Validation endpoint."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ...api.deps import get_validation_service
from ...services.validation import ValidationService

router = APIRouter()


class ValidateRequest(BaseModel):
    bundle: Dict[str, Any]


class ValidateResponse(BaseModel):
    ok: bool
    errors: List[Dict[str, Any]]


@router.post("/validate", response_model=ValidateResponse)
async def validate_bundle(payload: ValidateRequest, validation_service: ValidationService = Depends(get_validation_service)) -> ValidateResponse:
    is_valid, errors = validation_service.validate(payload.bundle)
    return ValidateResponse(ok=is_valid, errors=errors)
