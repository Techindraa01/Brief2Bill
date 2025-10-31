"""UPI deep link generation endpoint"""
from fastapi import APIRouter
from typing import Optional
from pydantic import BaseModel
from ...services.upi import generate_upi_deeplink, generate_upi_qr_payload


router = APIRouter()


class UPIDeeplinkRequest(BaseModel):
    """Request to generate UPI deep link"""
    upi_id: str
    payee_name: str
    amount: Optional[float] = None
    currency: str = "INR"
    note: Optional[str] = None
    txn_ref: Optional[str] = None
    callback_url: Optional[str] = None


class UPIDeeplinkResponse(BaseModel):
    """Response with UPI deep link and QR payload"""
    deeplink: str
    qr_payload: str


@router.post("/upi/deeplink", response_model=UPIDeeplinkResponse)
async def create_upi_deeplink(request: UPIDeeplinkRequest):
    """Generate UPI deep link and QR payload"""
    
    deeplink = generate_upi_deeplink(
        upi_id=request.upi_id,
        payee_name=request.payee_name,
        amount=request.amount,
        currency=request.currency,
        note=request.note,
        txn_ref=request.txn_ref,
        callback_url=request.callback_url
    )
    
    qr_payload = generate_upi_qr_payload(
        upi_id=request.upi_id,
        payee_name=request.payee_name,
        amount=request.amount,
        currency=request.currency,
        note=request.note,
        txn_ref=request.txn_ref,
        callback_url=request.callback_url
    )
    
    return {
        "deeplink": deeplink,
        "qr_payload": qr_payload
    }

