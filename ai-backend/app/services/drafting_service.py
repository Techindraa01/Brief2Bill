"""Draft orchestration and structured bundle generation."""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from ..models.document_models import DocumentBundle, DocDraft, Item, Party, Terms, Totals, Dates
from ..providers.base import LLMProvider, PromptPacket
from .repair import repair_bundle
from .validation import ValidationService

SYSTEM_PROMPT = (
    "You are an expert commercial-docs drafter for India-focused SMEs.\n"
    "Output STRICT JSON matching the provided JSON Schema for DocumentBundle.\n"
    "No markdown, no comments, no extra keys.\n"
    "Prefer INR context and GST. For quotations set valid_till = issue_date + 14..15 days; "
    "for invoices set due_date = issue_date + 7 days unless specified.\n"
    "Use conservative defaults when ambiguous."
)


class DraftingService:
    """Coordinates prompt construction, provider invocation, and validation."""

    def __init__(self, validation: ValidationService) -> None:
        self.validation = validation
        self.schema = validation.schema

    def _build_user_prompt(
        self,
        requirement: str,
        doc_types: Optional[List[str]] = None,
        currency: str = "INR",
        defaults: Optional[Dict[str, str]] = None,
        buyer_hint: Optional[str] = None,
    ) -> str:
        doc_types = doc_types or ["QUOTATION"]
        return (
            f"Requirement:\n{requirement}\n\n"
            f"Preferences:\n"
            f"- doc_types: {doc_types}\n"
            f"- currency: {currency}\n"
            f"- seller_defaults: {defaults or None}\n"
            f"- buyer_hint: {buyer_hint or None}\n\n"
            "Return exactly one JSON object of type DocumentBundle.\n"
            "Schema name: DocumentBundle"
        )

    async def generate_bundle(
        self,
        provider: Optional[LLMProvider],
        model: str,
        requirement: str,
        doc_types: Optional[List[str]] = None,
        currency: str = "INR",
        seller_defaults: Optional[Dict[str, str]] = None,
        buyer_hint: Optional[str] = None,
    ) -> Dict[str, any]:
        """Generate a bundle using provider if available, else fallback blueprint."""

        if provider is None:
            return self._fallback_bundle(requirement, doc_types, currency, seller_defaults)

        user_prompt = self._build_user_prompt(
            requirement=requirement,
            doc_types=doc_types,
            currency=currency,
            defaults=seller_defaults,
            buyer_hint=buyer_hint,
        )

        response_format = None
        capabilities = provider.capabilities()
        if capabilities.supports_json_schema:
            response_format = {
                "type": "json_schema",
                "json_schema": {"name": "DocumentBundle", "schema": self.schema},
            }
        elif capabilities.supports_plain_json:
            response_format = {"type": "json_object"}

        packet = PromptPacket(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=model,
            temperature=0.2,
            response_format=response_format,
        )

        try:
            result = await provider.generate(packet)
            payload = self.validation.extract_json(result.content)
        except Exception:
            payload = self._fallback_bundle(requirement, doc_types, currency, seller_defaults)

        is_valid, errors = self.validation.validate(payload)
        if not is_valid:
            payload = repair_bundle(payload)

        return payload

    def _fallback_bundle(
        self,
        requirement: str,
        doc_types: Optional[List[str]],
        currency: str,
        seller_defaults: Optional[Dict[str, str]],
    ) -> Dict[str, any]:
        today = date.today()
        draft = DocDraft(
            doc_type=(doc_types or ["QUOTATION"])[0],
            seller=Party(name=(seller_defaults or {}).get("name", "Seller")),
            buyer=Party(name="Client"),
            dates=Dates(issue_date=today),
            items=[Item(description=requirement[:60] or "Scope", qty=1, unit_price=0)],
            totals=Totals(subtotal=0, discount_total=0, tax_total=0, grand_total=0, round_off=0),
            terms=Terms(bullets=["Payment due within 7 days"], title="Terms & Conditions"),
            currency=currency,
        )
        bundle = DocumentBundle(drafts=[draft])
        return bundle.model_dump(exclude_none=True)
