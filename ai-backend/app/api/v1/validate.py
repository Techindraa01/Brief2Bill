"""Validation and repair endpoints"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
from pydantic import BaseModel
from ...services.validation import ValidationService
from ...services.repair import repair_bundle, repair_draft
from ...services.totals import recompute_draft_totals
from ...api.deps import get_validation_service


router = APIRouter()


class ValidateRequest(BaseModel):
    """Request to validate a bundle"""
    bundle: Dict[str, Any]


class ValidateResponse(BaseModel):
    """Response from validation"""
    ok: bool
    errors: list


class RepairRequest(BaseModel):
    """Request to repair a bundle"""
    bundle: Dict[str, Any]


class ComputeTotalsRequest(BaseModel):
    """Request to compute totals for a draft"""
    draft: Dict[str, Any]


class ComputeTotalsResponse(BaseModel):
    """Response with recomputed draft"""
    draft: Dict[str, Any]


@router.post("/validate", response_model=ValidateResponse)
async def validate_bundle(
    request: ValidateRequest,
    validation_service: ValidationService = Depends(get_validation_service)
):
    """Validate a document bundle against schema"""
    is_valid, errors = validation_service.validate(request.bundle)
    
    return {
        "ok": is_valid,
        "errors": [e.to_dict() for e in errors]
    }


@router.post("/repair")
async def repair_bundle_endpoint(
    request: RepairRequest
):
    """Repair a bundle with missing or invalid fields"""
    repaired = repair_bundle(request.bundle)
    return repaired


@router.post("/compute/totals", response_model=ComputeTotalsResponse)
async def compute_totals(
    request: ComputeTotalsRequest
):
    """Recompute totals for a draft"""
    recomputed = recompute_draft_totals(request.draft)
    return {"draft": recomputed}

