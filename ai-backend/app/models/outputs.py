"""Structured output models for quotation, invoice, and project brief."""

from __future__ import annotations

from datetime import date
from typing import List, Optional, Union

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


class Scope(BaseModel):
    """Detailed project scope with in-scope, out-of-scope, assumptions, and dependencies."""
    in_scope: List[str] = Field(default_factory=list, description="Activities and deliverables included in the project")
    out_of_scope: List[str] = Field(default_factory=list, description="Explicitly excluded items")
    assumptions: Optional[List[str]] = Field(default=None, description="Key assumptions the project is based on")
    dependencies: Optional[List[str]] = Field(default=None, description="External dependencies")


class Deliverable(BaseModel):
    """Detailed deliverable specification."""
    name: str = Field(description="Name of the deliverable")
    description: str = Field(description="Detailed description of the deliverable")
    format: Optional[str] = Field(default=None, description="Format or specifications (e.g., 'Figma files', 'React codebase')")
    acceptance_criteria: Optional[str] = Field(default=None, description="Criteria for accepting the deliverable")


class Milestone(BaseModel):
    """Project milestone with timeline and dependencies."""
    name: str = Field(description="Milestone name")
    description: Optional[str] = Field(default=None, description="Detailed description of the milestone")
    # Support both new and legacy formats
    days_from_start: Optional[int] = Field(default=None, ge=0, description="Number of days from project start")
    dependencies: Optional[List[str]] = Field(default=None, description="Names of milestones this depends on")
    # Legacy fields for backward compatibility
    start: Optional[date] = Field(default=None, description="Start date (legacy)")
    end: Optional[date] = Field(default=None, description="End date (legacy)")
    fee: Optional[float] = Field(default=None, description="Fee associated with milestone (legacy)")


class BillingPart(BaseModel):
    """Billing plan component."""
    # Support both new and legacy formats
    milestone: Optional[str] = Field(default=None, description="Milestone or event triggering payment")
    percentage: Optional[int] = Field(default=None, ge=0, le=100, description="Percentage of total project value")
    description: Optional[str] = Field(default=None, description="Payment conditions and details")
    # Legacy fields for backward compatibility
    when: Optional[str] = Field(default=None, description="When payment is due (legacy)")
    percent: Optional[int] = Field(default=None, ge=0, le=100, description="Percentage (legacy)")

    @model_validator(mode="after")
    def _sync_fields(self) -> "BillingPart":
        """Sync new and legacy fields for backward compatibility."""
        # If using legacy format, copy to new fields
        if self.milestone is None and self.when:
            self.milestone = self.when
        if self.percentage is None and self.percent is not None:
            self.percentage = self.percent
        # If using new format, copy to legacy fields
        if self.when is None and self.milestone:
            self.when = self.milestone
        if self.percent is None and self.percentage is not None:
            self.percent = self.percentage
        return self


class Risk(BaseModel):
    """Project risk assessment."""
    description: str = Field(description="Description of the risk")
    impact: str = Field(description="Impact level: High, Medium, or Low")
    probability: str = Field(description="Probability: High, Medium, or Low")
    mitigation: str = Field(description="Mitigation strategy")


class CommercialTerms(BaseModel):
    """Commercial terms for the project."""
    payment_terms: Optional[str] = Field(default=None, description="Payment terms and schedule")
    payment_methods: Optional[str] = Field(default=None, description="Accepted payment methods")
    change_requests: Optional[str] = Field(default=None, description="Change request process")
    ip_rights: Optional[str] = Field(default=None, description="Intellectual property rights")
    warranty: Optional[str] = Field(default=None, description="Warranty and support terms")
    termination: Optional[str] = Field(default=None, description="Termination clauses")


class ProjectBriefOutput(BaseModel):
    title: str
    objective: str
    # Support both old (List[str]) and new (Scope object) formats
    scope: Union[List[str], Scope]
    # Support both old (List[str]) and new (List[Deliverable]) formats
    deliverables: Union[List[str], List[Deliverable]]
    assumptions: Optional[List[str]] = Field(default=None)
    milestones: List[Milestone]
    timeline_days: int = Field(ge=1)
    billing_plan: List[BillingPart]
    # Support both old (List[str]) and new (List[Risk]) formats
    risks: Optional[Union[List[str], List[Risk]]] = Field(default=None)
    commercial_terms: Optional[CommercialTerms] = Field(default=None, description="Commercial terms and conditions")
    seller: Optional[Party] = None
    buyer: Optional[Party] = None

    @model_validator(mode="after")
    def _billing_total(self) -> "ProjectBriefOutput":
        total = sum(part.percentage if part.percentage else (part.percent or 0) for part in self.billing_plan)
        if total != 100:
            raise ValueError("billing_plan percentages must total 100")
        return self
