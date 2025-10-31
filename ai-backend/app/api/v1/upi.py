"""UPI deeplink endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ...services.upi import generate_upi_deeplink, generate_upi_qr_payload

router = APIRouter()


class UPIDeeplinkRequest(BaseModel):
    upi_id: str
    payee_name: str
    amount: Optional[float] = None
    currency: str = "INR"
    note: Optional[str] = None
    txn_ref: Optional[str] = None
    callback_url: Optional[str] = None


class UPIDeeplinkResponse(BaseModel):
    deeplink: str
    qr_payload: str


@router.post("/upi/deeplink", response_model=UPIDeeplinkResponse)
async def create_upi_deeplink(payload: UPIDeeplinkRequest) -> UPIDeeplinkResponse:
    deeplink = generate_upi_deeplink(
        upi_id=payload.upi_id,
        payee_name=payload.payee_name,
        amount=payload.amount,
        currency=payload.currency,
        note=payload.note,
        txn_ref=payload.txn_ref,
        callback_url=payload.callback_url,
    )
    qr_payload = generate_upi_qr_payload(
        upi_id=payload.upi_id,
        payee_name=payload.payee_name,
        amount=payload.amount,
        currency=payload.currency,
        note=payload.note,
        txn_ref=payload.txn_ref,
        callback_url=payload.callback_url,
    )
    return UPIDeeplinkResponse(deeplink=deeplink, qr_payload=qr_payload)
