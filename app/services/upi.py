"""UPI deep link generation service"""
from urllib.parse import quote
from typing import Optional


def generate_upi_deeplink(
    upi_id: str,
    payee_name: str,
    amount: Optional[float] = None,
    currency: str = "INR",
    note: Optional[str] = None,
    txn_ref: Optional[str] = None,
    callback_url: Optional[str] = None
) -> str:
    """Generate UPI deep link according to UPI specification"""

    # Build UPI URL
    parts = [f"upi://pay?pa={quote(upi_id)}"]
    parts.append(f"pn={quote(payee_name)}")

    if amount is not None:
        parts.append(f"am={amount:.2f}")

    parts.append(f"cu={currency}")

    if note:
        parts.append(f"tn={quote(note)}")

    if txn_ref:
        parts.append(f"tr={quote(txn_ref)}")

    if callback_url:
        parts.append(f"url={quote(callback_url)}")

    return "&".join(parts)


def generate_upi_qr_payload(
    upi_id: str,
    payee_name: str,
    amount: Optional[float] = None,
    currency: str = "INR",
    note: Optional[str] = None,
    txn_ref: Optional[str] = None,
    callback_url: Optional[str] = None
) -> str:
    """Generate UPI QR payload (same as deep link for standard UPI)"""
    return generate_upi_deeplink(
        upi_id=upi_id,
        payee_name=payee_name,
        amount=amount,
        currency=currency,
        note=note,
        txn_ref=txn_ref,
        callback_url=callback_url
    )
