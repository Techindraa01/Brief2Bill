"""Pydantic models mirroring the DocumentBundle schema."""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from ..services.totals import compute_totals


class BankDetails(BaseModel):
    account_name: Optional[str] = None
    account_no: Optional[str] = None
    ifsc: Optional[str] = None
    upi_id: Optional[str] = None


class Party(BaseModel):
    name: str
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    bank: Optional[BankDetails] = None


class DocMeta(BaseModel):
    doc_no: Optional[str] = None
    ref_no: Optional[str] = None
    po_no: Optional[str] = None


class Dates(BaseModel):
    issue_date: date
    due_date: Optional[date] = None
    valid_till: Optional[date] = None


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
    def _coerce_numbers(cls, value):
        if value is None:
            return 0
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


class Terms(BaseModel):
    title: str = "Terms & Conditions"
    bullets: List[str]

    @model_validator(mode="after")
    def _ensure_bullets(self):
        if not self.bullets:
            raise ValueError("terms.bullets must contain at least one entry")
        return self


class Payment(BaseModel):
    mode: Optional[str] = Field(default=None, pattern="^(UPI|BANK_TRANSFER|OTHER)$")
    upi_deeplink: Optional[str] = None
    instructions: Optional[str] = None


class DocDraft(BaseModel):
    doc_type: str = Field(pattern="^(QUOTATION|TAX_INVOICE)$")
    locale: str = "en-IN"
    currency: str = "INR"
    seller: Party
    buyer: Party
    doc_meta: Optional[DocMeta] = None
    dates: Dates
    items: List[Item]
    totals: Totals
    terms: Terms
    notes: Optional[str] = None
    payment: Optional[Payment] = None

    @model_validator(mode="after")
    def _apply_default_dates(self):
        issue_date = self.dates.issue_date
        if self.doc_type == "TAX_INVOICE" and not self.dates.due_date:
            self.dates.due_date = issue_date + timedelta(days=7)
        if self.doc_type == "QUOTATION" and not self.dates.valid_till:
            self.dates.valid_till = issue_date + timedelta(days=15)
        return self

    @model_validator(mode="after")
    def _compute_totals(self):
        self.totals = compute_totals(self)
        return self


class Milestone(BaseModel):
    name: str
    start: date
    end: date
    fee: float = 0.0


class BillingPart(BaseModel):
    when: str
    percent: int = Field(ge=0, le=100)


class ProjectBrief(BaseModel):
    title: str
    objective: str
    scope: List[str]
    assumptions: List[str] = Field(default_factory=list)
    deliverables: List[str]
    milestones: List[Milestone]
    timeline_days: int
    billing_plan: List[BillingPart]
    risks: List[str] = Field(default_factory=list)


class DocumentBundle(BaseModel):
    drafts: List[DocDraft]
    project_brief: Optional[ProjectBrief] = None

    @model_validator(mode="after")
    def _recompute(self):
        for idx, draft in enumerate(self.drafts):
            self.drafts[idx].totals = compute_totals(draft)
        return self
