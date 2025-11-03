"""Structured output models for quotation, invoice, and project brief."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class Party(BaseModel):
    """Minimal party representation for generated documents."""

    name: str
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None


class DocMeta(BaseModel):
    doc_no: Optional[str] = None
    ref_no: Optional[str] = None
    po_no: Optional[str] = None


class InvoiceDocMeta(DocMeta):
    doc_no: str


class DatesQuotation(BaseModel):
    issue_date: date
    valid_till: Optional[date] = None


class DatesInvoice(BaseModel):
    issue_date: date
    due_date: Optional[date] = None


class Item(BaseModel):
    description: str
    qty: float
    unit_price: float
    unit: str = "pcs"
    discount: float = 0.0
    tax_rate: float = 0.0
    hsn_sac: Optional[str] = None

    @field_validator("qty", "unit_price", "discount", "tax_rate", mode="before")
    @classmethod
    def _ensure_number(cls, value):
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


class Totals(BaseModel):
    subtotal: float
    discount_total: float
    tax_total: float
    shipping: float = 0.0
    round_off: float = 0.0
    grand_total: float
    amount_in_words: Optional[str] = None

    @field_validator("subtotal", "discount_total", "tax_total", "shipping", "round_off", "grand_total", mode="before")
    @classmethod
    def _coerce_float(cls, value):
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


class Terms(BaseModel):
    title: str = "Terms & Conditions"
    bullets: List[str]

    @model_validator(mode="after")
    def _ensure_bullets(self) -> "Terms":
        if not self.bullets:
            raise ValueError("terms.bullets must not be empty")
        return self


class Payment(BaseModel):
    mode: Optional[str] = Field(default=None, pattern="^(UPI|BANK_TRANSFER|OTHER)$")
    upi_deeplink: Optional[str] = None
    instructions: Optional[str] = None


class GSTBreakup(BaseModel):
    mode: Optional[str] = Field(default=None, pattern="^(INTRA|INTER)$")
    cgst: float = 0.0
    sgst: float = 0.0
    igst: float = 0.0
    place_of_supply: Optional[str] = None

    @field_validator("cgst", "sgst", "igst", mode="before")
    @classmethod
    def _coerce_float(cls, value):
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


class QuotationOutput(BaseModel):
    doc_type: str = Field(default="QUOTATION", pattern="^QUOTATION$")
    currency: str = "INR"
    locale: str = "en-IN"
    seller: Party
    buyer: Party
    doc_meta: Optional[DocMeta] = None
    dates: DatesQuotation
    items: List[Item]
    totals: Totals
    terms: Terms
    notes: Optional[str] = None
    payment: Optional[Payment] = None


class TaxInvoiceOutput(BaseModel):
    doc_type: str = Field(default="TAX_INVOICE", pattern="^TAX_INVOICE$")
    currency: str = "INR"
    locale: str = "en-IN"
    seller: Party
    buyer: Party
    doc_meta: InvoiceDocMeta
    dates: DatesInvoice
    items: List[Item]
    totals: Totals
    terms: Terms
    payment: Optional[Payment] = None
    gst: Optional[GSTBreakup] = None


class Milestone(BaseModel):
    name: str
    start: date
    end: date
    fee: float = 0.0


class BillingPart(BaseModel):
    when: str
    percent: int = Field(ge=0, le=100)


class ProjectBriefOutput(BaseModel):
    title: str
    objective: str
    scope: List[str]
    deliverables: List[str]
    assumptions: List[str] = Field(default_factory=list)
    milestones: List[Milestone]
    timeline_days: int = Field(ge=1)
    billing_plan: List[BillingPart]
    risks: List[str] = Field(default_factory=list)
    seller: Optional[Party] = None
    buyer: Optional[Party] = None

    @model_validator(mode="after")
    def _billing_total(self) -> "ProjectBriefOutput":
        total = sum(part.percent for part in self.billing_plan)
        if total != 100:
            raise ValueError("billing_plan percentages must total 100")
        return self
