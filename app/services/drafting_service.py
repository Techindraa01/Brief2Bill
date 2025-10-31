"""Draft orchestration and structured bundle generation."""

from __future__ import annotations

from datetime import date, timedelta
import math
import re
from typing import Dict, List, Optional, Tuple

from ..models.document_models import (
    BillingPart,
    DocumentBundle,
    DocDraft,
    DocMeta,
    Item,
    Milestone,
    Party,
    Payment,
    ProjectBrief,
    Terms,
    Totals,
    Dates,
)
from ..providers.base import LLMProvider, PromptPacket
from .repair import repair_bundle
from .upi import generate_upi_deeplink
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

        doc_types = doc_types or ["QUOTATION"]
        defaults_payload = seller_defaults or {}
        seller_profile = (
            defaults_payload.get("seller")
            if isinstance(defaults_payload, dict)
            else defaults_payload
        )
        buyer_profile = (
            defaults_payload.get("buyer")
            if isinstance(defaults_payload, dict)
            else None
        )

        if provider is None:
            return self._structured_bundle(
                requirement=requirement,
                doc_types=doc_types,
                currency=currency,
                seller_defaults=seller_profile,
                buyer_hint=self._resolve_buyer_hint(buyer_hint, buyer_profile),
            )

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
            payload = self._structured_bundle(
                requirement=requirement,
                doc_types=doc_types,
                currency=currency,
                seller_defaults=seller_profile,
                buyer_hint=self._resolve_buyer_hint(buyer_hint, buyer_profile),
            )

        is_valid, errors = self.validation.validate(payload)
        if not is_valid:
            payload = repair_bundle(payload)

        return payload

    def _structured_bundle(
        self,
        requirement: str,
        doc_types: List[str],
        currency: str,
        seller_defaults: Optional[Dict[str, str]],
        buyer_hint: Optional[str],
    ) -> Dict[str, any]:
        issue_date = date.today()
        valid_doc_types = [dt for dt in doc_types if dt in {"QUOTATION", "TAX_INVOICE"}]
        primary_doc_type = valid_doc_types[0] if valid_doc_types else "QUOTATION"

        seller_info = seller_defaults or {}
        seller_party = Party.model_validate({"name": seller_info.get("name", "Seller"), **seller_info})

        buyer_name = self._extract_buyer(requirement) or buyer_hint or "Client"
        buyer_party = Party.model_validate({"name": buyer_name})

        lower_amount, upper_amount = self._parse_budget(requirement)
        if lower_amount == 0 and upper_amount == 0:
            lower_amount, upper_amount = 35000.0, 45000.0

        average_amount = (lower_amount + upper_amount) / 2 if upper_amount else lower_amount
        average_amount = max(average_amount, 15000.0)

        optional_amount = max(upper_amount - lower_amount, average_amount * 0.2)

        scope_summary = self._summarise_scope(requirement)

        main_item = Item(
            description=scope_summary,
            qty=1,
            unit_price=round(average_amount * 0.85, 2),
            unit="package",
            tax_rate=18.0,
            discount=0.0,
        )

        maintenance_item = Item(
            description="Post-launch maintenance (3 months)",
            qty=1,
            unit_price=round(optional_amount * 0.5, 2),
            unit="package",
            tax_rate=18.0,
            discount=round(optional_amount * 0.1, 2),
        ) if "maintenance" in requirement.lower() or "support" in requirement.lower() else None

        items = [main_item]
        if maintenance_item:
            items.append(maintenance_item)

        totals_placeholder = Totals(
            subtotal=0,
            discount_total=0,
            tax_total=0,
            shipping=0,
            grand_total=0,
            round_off=0,
        )

        terms = Terms(
            title="Terms & Conditions",
            bullets=self._build_terms(requirement, buyer_name),
        )

        payment = None
        upi_id = (seller_info.get("bank") or {}).get("upi_id")
        if upi_id:
            deeplink = generate_upi_deeplink(
                upi_id=upi_id,
                payee_name=seller_party.name,
                amount=round(average_amount, 2),
                currency=currency,
                note="Advance 50%",
                txn_ref=f"QUO-{issue_date.strftime('%Y%m%d')}"
            )
            payment = Payment(mode="UPI", upi_deeplink=deeplink)

        doc_meta = DocMeta(
            doc_no=f"INV-{issue_date.strftime('%Y%m%d')}" if primary_doc_type == "TAX_INVOICE" else None,
            ref_no=f"REF-{issue_date.strftime('%Y%m%d')}"
        )

        draft = DocDraft(
            doc_type=primary_doc_type,
            seller=seller_party,
            buyer=buyer_party,
            doc_meta=doc_meta,
            dates=Dates(issue_date=issue_date),
            items=items,
            totals=totals_placeholder,
            terms=terms,
            notes=f"Estimated delivery timeline of {self._infer_timeline_phrase(requirement)}.",
            payment=payment,
            currency=currency,
        )

        bundle = DocumentBundle(drafts=[draft])

        if "PROJECT_BRIEF" in doc_types:
            bundle.project_brief = self._build_project_brief(requirement, buyer_name, issue_date, bundle.drafts[0])

        return bundle.model_dump(exclude_none=True)

    def _resolve_buyer_hint(self, buyer_hint: Optional[str], buyer_profile: Optional[Dict[str, str]]) -> Optional[str]:
        if buyer_hint:
            return buyer_hint
        if isinstance(buyer_profile, dict):
            return buyer_profile.get("name")
        return None

    def _extract_buyer(self, requirement: str) -> Optional[str]:
        match = re.search(r"buyer\s*[:\-]\s*([^\n\r]+)", requirement, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        match = re.search(r"buyer\s+([A-Za-z0-9 &.,]+)", requirement, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _parse_budget(self, requirement: str) -> Tuple[float, float]:
        text = requirement.replace("–", "-").replace("—", "-")
        pattern = re.compile(
            r"(budget|cost|pricing|price|estimate)[^0-9]*(\d+(?:\.\d+)?)\s*(?:[-to]{1,3}\s*(\d+(?:\.\d+)?))?\s*([kKlL]|lakh|crore|cr)?",
            re.IGNORECASE,
        )
        for match in pattern.finditer(text):
            start_value = float(match.group(2))
            end_value = float(match.group(3)) if match.group(3) else start_value
            unit = match.group(4)
            multiplier = self._unit_multiplier(unit)
            return start_value * multiplier, end_value * multiplier
        fallback_numbers = re.findall(r"(\d+(?:\.\d+)?)\s*(k|l|cr|lakh|crore)?", text, re.IGNORECASE)
        if fallback_numbers:
            value, unit = fallback_numbers[0]
            multiplier = self._unit_multiplier(unit)
            amount = float(value) * multiplier
            return amount, amount
        return 0.0, 0.0

    @staticmethod
    def _unit_multiplier(unit: Optional[str]) -> float:
        if not unit:
            return 1.0
        unit = unit.lower()
        if unit in {"k"}:
            return 1_000.0
        if unit in {"l", "lakh"}:
            return 100_000.0
        if unit in {"cr", "crore"}:
            return 10_000_000.0
        return 1.0

    def _summarise_scope(self, requirement: str) -> str:
        sentences = re.split(r"[.!?]", requirement)
        for sentence in sentences:
            cleaned = sentence.strip()
            if cleaned:
                return cleaned[:120]
        return requirement[:120] or "Project scope"

    def _build_terms(self, requirement: str, buyer_name: str) -> List[str]:
        inferred_timeline = self._infer_timeline_phrase(requirement)
        bullets = [
            f"Quotation valid for 15 days from issue date",
            "50% advance via UPI, balance on delivery",
            f"Project timeline: {inferred_timeline}",
            f"Work executed for {buyer_name} with GST @18% applied",
        ]
        if "maintenance" in requirement.lower():
            bullets.append("Maintenance billed separately post launch")
        return bullets

    def _infer_timeline_phrase(self, requirement: str) -> str:
        days = self._extract_timeline_days(requirement)
        if days <= 7:
            return "1 week"
        if days <= 14:
            return "2 weeks"
        if days <= 30:
            return "1 month"
        weeks = math.ceil(days / 7)
        return f"{weeks} weeks"

    def _extract_timeline_days(self, requirement: str) -> int:
        text = requirement.lower()
        pattern = re.compile(r"(\d+(?:\.\d+)?)\s*(day|days|week|weeks|month|months|sprint|sprints)")
        for match in pattern.finditer(text):
            value = float(match.group(1))
            unit = match.group(2)
            if unit.startswith("day"):
                return max(int(math.ceil(value)), 1)
            if unit.startswith("week"):
                return max(int(math.ceil(value * 7)), 7)
            if unit.startswith("month"):
                return max(int(math.ceil(value * 30)), 14)
            if unit.startswith("sprint"):
                return max(int(math.ceil(value * 14)), 14)
        return 14

    def _build_project_brief(
        self,
        requirement: str,
        buyer_name: str,
        issue_date: date,
        reference_draft: DocDraft,
    ) -> ProjectBrief:
        timeline_days = self._extract_timeline_days(requirement)
        billing_parts = self._extract_billing_plan(requirement)
        total_amount = reference_draft.totals.grand_total or reference_draft.totals.subtotal

        milestone_titles = [
            "Discovery & Planning",
            "Development & Integration",
            "Launch & Handover",
        ]
        milestone_duration = max(timeline_days // len(milestone_titles), 3)

        milestones: List[Milestone] = []
        start = issue_date
        for idx, title in enumerate(milestone_titles):
            end = start + timedelta(days=milestone_duration - 1)
            percent = billing_parts[idx].percent if idx < len(billing_parts) else billing_parts[-1].percent
            fee = round(total_amount * (percent / 100.0), 2)
            milestones.append(
                Milestone(
                    name=title,
                    start=start,
                    end=end,
                    fee=fee,
                )
            )
            start = end + timedelta(days=1)

        scope_points = [
            "Requirement analysis and UX planning",
            "Responsive Next.js landing page build",
            "Performance optimisation and analytics setup",
        ]
        deliverables = [
            "High fidelity landing page",
            "Content sections tailored to offerings",
            "Deployment checklist and handover",
        ]
        assumptions = [
            "Buyer shares brand assets within 3 days of kickoff",
            "One consolidated feedback cycle per milestone",
        ]
        risks = [
            "Delays in feedback may extend the schedule",
            "Scope additions beyond agreed features require change request",
        ]

        brief = ProjectBrief(
            title=f"{reference_draft.seller.name} x {buyer_name} Delivery Plan",
            objective=self._summarise_scope(requirement),
            scope=scope_points,
            deliverables=deliverables,
            assumptions=assumptions,
            timeline_days=timeline_days,
            milestones=milestones,
            billing_plan=billing_parts,
            risks=risks,
        )
        return brief

    def _extract_billing_plan(self, requirement: str) -> List[BillingPart]:
        text = requirement.replace("–", "-").replace("—", "-")
        slash_match = re.search(r"(\d{1,3})(?:\s*/\s*(\d{1,3}))(?:\s*/\s*(\d{1,3}))", text)
        parts: List[int] = []
        if slash_match:
            parts = [int(p) for p in slash_match.groups() if p]
        else:
            percent_numbers = [int(p) for p in re.findall(r"(\d{1,3})%", text)]
            if percent_numbers and sum(percent_numbers) == 100:
                parts = percent_numbers
        if not parts:
            parts = [40, 40, 20]
        total = sum(parts)
        if total != 100:
            parts = [round(p * 100 / total) for p in parts]
            diff = 100 - sum(parts)
            if diff:
                parts[-1] += diff
        labels = ["Advance", "Mid Project", "Before Launch"]
        billing = []
        for idx, value in enumerate(parts):
            label = labels[idx] if idx < len(labels) else f"Payment {idx+1}"
            billing.append(BillingPart(when=label, percent=int(value)))
        return billing
