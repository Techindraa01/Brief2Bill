"""Totals recomputation endpoint."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from ...services.totals import recompute_totals_from_dict

router = APIRouter()


class TotalsRequest(BaseModel):
    draft: Dict[str, Any]


class TotalsResponse(BaseModel):
    draft: Dict[str, Any]


@router.post("/compute/totals", response_model=TotalsResponse)
async def compute_totals(payload: TotalsRequest) -> TotalsResponse:
    recomputed = recompute_totals_from_dict(payload.draft)
    return TotalsResponse(draft=recomputed)
