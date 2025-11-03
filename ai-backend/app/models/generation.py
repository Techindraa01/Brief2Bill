"""Request models for document generation endpoints."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .inputs import FROMPartyInput, TOPartyInput


class HintDocMeta(BaseModel):
    doc_no: Optional[str] = None
    po_no: Optional[str] = None
    ref_no: Optional[str] = None


class HintDates(BaseModel):
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    valid_till: Optional[date] = None


class HintItem(BaseModel):
    description: Optional[str] = None
    hsn_sac: Optional[str] = None
    qty: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    discount: Optional[float] = None
    tax_rate: Optional[float] = None


class HintTerms(BaseModel):
    title: Optional[str] = None
    bullets: Optional[List[str]] = None


class HintPayment(BaseModel):
    mode: Optional[str] = None
    instructions: Optional[str] = None
    upi_deeplink: Optional[str] = None


class GenerationHints(BaseModel):
    doc_meta: Optional[HintDocMeta] = None
    dates: Optional[HintDates] = None
    items: Optional[List[HintItem]] = None
    terms: Optional[HintTerms] = None
    payment: Optional[HintPayment] = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class GenerationRequest(BaseModel):
    """Payload accepted by the generation endpoints."""

    model_config = ConfigDict(populate_by_name=True)

    to: TOPartyInput
    from_: FROMPartyInput = Field(alias="from")
    currency: str = "INR"
    locale: str = "en-IN"
    requirement: str = Field(min_length=3)
    hints: Optional[GenerationHints] = None
    workspace_id: Optional[str] = None

    @property
    def seller(self) -> FROMPartyInput:
        return self.from_

    @property
    def buyer(self) -> TOPartyInput:
        return self.to
