"""UPI deeplink/QR helpers (placeholder)"""
def make_upi_link(payee_vpa: str, amount: float) -> str:
    return f"upi://pay?pa={payee_vpa}&am={amount}"
