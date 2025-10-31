"""Repair endpoint."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from ...services.repair import repair_bundle

router = APIRouter()


class RepairRequest(BaseModel):
    bundle: Dict[str, Any]


@router.post("/repair")
async def repair_bundle_endpoint(payload: RepairRequest) -> Dict[str, Any]:
    return repair_bundle(payload.bundle)
