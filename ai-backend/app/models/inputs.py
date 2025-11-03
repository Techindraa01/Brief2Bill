"""Pydantic models mirroring TO/FROM request schemas."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Address(BaseModel):
    """Postal address for billing or shipping."""

    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    state_code: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "India"
    country_code: str = "IN"


class BankDetails(BaseModel):
    """Banking block used for payment instructions."""

    bank_name: Optional[str] = None
    branch: Optional[str] = None
    account_name: Optional[str] = None
    account_no: Optional[str] = None
    ifsc: Optional[str] = None
    swift: Optional[str] = None
    iban: Optional[str] = None
    upi_id: Optional[str] = None


class TaxPreferences(BaseModel):
    """Seller-side tax preferences."""

    place_of_supply: Optional[str] = None
    reverse_charge: bool = False
    e_invoice: bool = False


class Branding(BaseModel):
    """Branding hints for generated documents."""

    logo_url: Optional[str] = None
    accent_color: Optional[str] = None
    footer_text: Optional[str] = None


class PartyBase(BaseModel):
    """Shared party fields for TO and FROM."""

    name: str = Field(min_length=2, max_length=120)
    contact_person: Optional[str] = None
    email: Optional[str] = Field(default=None, min_length=3)
    phone: Optional[str] = None
    website: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=1000)


class TOPartyInput(PartyBase):
    """Recipient information for a generated document."""

    billing_address: Optional[Address] = None
    shipping_address: Optional[Address] = None
    place_of_supply: Optional[str] = Field(default=None, description="State/UT for GST logic, e.g., GJ, MH")


class FROMPartyInput(PartyBase):
    """Issuer information for a generated document."""

    cin: Optional[str] = None
    billing_address: Optional[Address] = None
    bank: Optional[BankDetails] = None
    tax_prefs: Optional[TaxPreferences] = None
    branding: Optional[Branding] = None
