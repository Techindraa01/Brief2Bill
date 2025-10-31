"""ID generators (INV-YYYY-####) placeholder"""
from datetime import datetime

def generate_invoice_id(seq: int) -> str:
    year = datetime.utcnow().year
    return f"INV-{year}-{seq:04d}"
