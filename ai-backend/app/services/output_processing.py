"""Helpers for normalising and repairing structured model outputs."""

from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
from typing import Any, Dict, Iterable, List, Optional

from pydantic import ValidationError

from ..models.generation import GenerationRequest, HintItem
from ..models.inputs import Address
from ..models.outputs import (
    Item,
    Payment,
    ProjectBriefOutput,
    QuotationOutput,
    TaxInvoiceOutput,
    Terms,
    Totals,
    GSTBreakup,
)
from ..services.totals import number_to_words_indian
from ..services.upi import generate_upi_deeplink

_DEFAULT_TERMS = [
    "Prices exclusive of applicable taxes unless stated otherwise",
    "Payment terms as per agreement",
]


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _format_address(address: Optional[Address]) -> Optional[str]:
    if address is None:
        return None
    parts = [
        address.line1,
        address.line2,
        address.city,
        address.state,
        address.postal_code,
        address.country,
    ]
    formatted = ", ".join(part for part in parts if part)
    return formatted or None


def _ensure_party(raw: Any, fallback) -> Dict[str, Any]:
    payload = raw if isinstance(raw, dict) else {}
    address_source = getattr(fallback, "billing_address", None) or getattr(fallback, "shipping_address", None)
    return {
        "name": payload.get("name") or fallback.name,
        "address": payload.get("address") or _format_address(address_source),
        "email": payload.get("email") or getattr(fallback, "email", None),
        "phone": payload.get("phone") or getattr(fallback, "phone", None),
        "gstin": payload.get("gstin") or getattr(fallback, "gstin", None),
        "pan": payload.get("pan") or getattr(fallback, "pan", None),
    }


def _ensure_terms(raw: Any, hints) -> Terms:
    source = raw if isinstance(raw, dict) else {}
    title = source.get("title") or (hints.title if hints and hints.title else "Terms & Conditions")
    bullets = source.get("bullets")
    if not isinstance(bullets, list) or not bullets:
        bullets = hints.bullets if hints and hints.bullets else _DEFAULT_TERMS
    return Terms(title=title, bullets=bullets)


def _ensure_items(raw_items: Any, hints: Optional[List[HintItem]], request: GenerationRequest) -> List[Item]:
    seed: List[Dict[str, Any]] = []
    if isinstance(raw_items, list):
        seed = [deepcopy(item) if isinstance(item, dict) else {} for item in raw_items]
    if not seed and hints:
        seed = [hint.model_dump(exclude_none=True) for hint in hints if hint]
    if not seed:
        seed = [
            {
                "description": request.requirement.strip() or "Professional services",
                "qty": 1,
                "unit_price": 0.0,
                "unit": "pcs",
                "discount": 0.0,
                "tax_rate": 0.0,
            }
        ]

    items: List[Item] = []
    for entry in seed:
        description = entry.get("description") or request.requirement or "Line item"
        qty = max(_to_float(entry.get("qty"), 1.0), 0.0)
        if qty == 0:
            qty = 1.0
        unit_price = max(_to_float(entry.get("unit_price"), 0.0), 0.0)
        discount = max(_to_float(entry.get("discount"), 0.0), 0.0)
        tax_rate = max(_to_float(entry.get("tax_rate"), 0.0), 0.0)
        unit = entry.get("unit") or "pcs"
        hsn_sac = entry.get("hsn_sac") or None
        items.append(
            Item(
                description=description,
                qty=qty,
                unit_price=unit_price,
                unit=unit,
                discount=discount,
                tax_rate=tax_rate,
                hsn_sac=hsn_sac,
            )
        )
    return items


def _calculate_totals(items: Iterable[Item], shipping: float) -> Totals:
    subtotal = 0.0
    discount_total = 0.0
    tax_total = 0.0
    for item in items:
        qty = float(item.qty)
        unit_price = float(item.unit_price)
        gross = qty * unit_price
        discount = min(float(item.discount or 0.0), gross)
        net = max(gross - discount, 0.0)
        tax_rate = max(float(item.tax_rate or 0.0), 0.0)
        subtotal += gross
        discount_total += discount
        tax_total += net * (tax_rate / 100.0)
    subtotal = round(subtotal, 2)
    discount_total = round(discount_total, 2)
    tax_total = round(tax_total, 2)
    shipping = round(float(shipping), 2)
    pre_round = subtotal - discount_total + tax_total + shipping
    rounded = round(pre_round)
    round_off = round(rounded - pre_round, 2)
    grand_total = round(pre_round + round_off, 2)
    return Totals(
        subtotal=subtotal,
        discount_total=discount_total,
        tax_total=tax_total,
        shipping=shipping,
        round_off=round_off,
        grand_total=grand_total,
        amount_in_words=number_to_words_indian(grand_total),
    )


def _resolve_issue_date(request: GenerationRequest, raw_dates: Any) -> date:
    if isinstance(raw_dates, dict) and raw_dates.get("issue_date"):
        try:
            return date.fromisoformat(str(raw_dates["issue_date"]))
        except ValueError:
            pass
    if request.hints and request.hints.dates and request.hints.dates.issue_date:
        return request.hints.dates.issue_date
    return date.today()


def _resolve_valid_till(issue_date: date, request: GenerationRequest, raw_dates: Any) -> Optional[date]:
    if isinstance(raw_dates, dict) and raw_dates.get("valid_till"):
        try:
            return date.fromisoformat(str(raw_dates["valid_till"]))
        except ValueError:
            pass
    if request.hints and request.hints.dates and request.hints.dates.valid_till:
        return request.hints.dates.valid_till
    return issue_date + timedelta(days=15)


def _resolve_due_date(issue_date: date, request: GenerationRequest, raw_dates: Any) -> date:
    if isinstance(raw_dates, dict) and raw_dates.get("due_date"):
        try:
            return date.fromisoformat(str(raw_dates["due_date"]))
        except ValueError:
            pass
    if request.hints and request.hints.dates and request.hints.dates.due_date:
        return request.hints.dates.due_date
    return issue_date + timedelta(days=7)


def _ensure_doc_meta(raw: Any, request: GenerationRequest, require_doc_no: bool, prefix: str) -> Dict[str, Any]:
    data = raw if isinstance(raw, dict) else {}
    hints = request.hints.doc_meta.model_dump(exclude_none=True) if request.hints and request.hints.doc_meta else {}
    merged = {**hints, **data}
    if require_doc_no and not merged.get("doc_no"):
        merged["doc_no"] = f"{prefix}-{date.today():%Y%m%d}"
    return merged


def _ensure_payment(raw: Any, request: GenerationRequest) -> Optional[Payment]:
    data = raw if isinstance(raw, dict) else {}
    hints = request.hints.payment if request.hints and request.hints.payment else None
    if hints:
        if hints.mode:
            data.setdefault("mode", hints.mode)
        if hints.instructions and not data.get("instructions"):
            data["instructions"] = hints.instructions
    if not data:
        return None
    return Payment.model_validate(data)


def _ensure_gst(raw: Any, request: GenerationRequest) -> Optional[GSTBreakup]:
    if raw is None and not request.seller.tax_prefs:
        return None
    data = raw if isinstance(raw, dict) else {}
    place_of_supply = data.get("place_of_supply")
    if not place_of_supply and request.seller.tax_prefs and request.seller.tax_prefs.place_of_supply:
        place_of_supply = request.seller.tax_prefs.place_of_supply
    mode = data.get("mode")
    if not mode and place_of_supply and request.buyer.place_of_supply:
        mode = "INTRA" if place_of_supply == request.buyer.place_of_supply else "INTER"
    base = {
        "mode": mode,
        "cgst": data.get("cgst"),
        "sgst": data.get("sgst"),
        "igst": data.get("igst"),
        "place_of_supply": place_of_supply,
    }
    if any(value is not None for value in base.values()):
        return GSTBreakup.model_validate(base)
    return None


def _post_payment(payment: Optional[Payment], request: GenerationRequest, totals: Totals) -> Optional[Payment]:
    if payment is None:
        return None
    if payment.mode == "UPI":
        upi_id = request.seller.bank.upi_id if request.seller.bank else None
        if upi_id:
            payment.upi_deeplink = generate_upi_deeplink(
                upi_id=upi_id,
                payee_name=request.seller.name,
                amount=totals.grand_total,
                currency=request.currency,
                note=request.requirement[:50],
                txn_ref=(request.hints.doc_meta.doc_no if request.hints and request.hints.doc_meta else None),
            )
    return payment


def build_quotation_output(raw: Dict[str, Any], request: GenerationRequest) -> QuotationOutput:
    data = deepcopy(raw) if isinstance(raw, dict) else {}
    data.setdefault("doc_type", "QUOTATION")
    issue_date = _resolve_issue_date(request, data.get("dates"))
    valid_till = _resolve_valid_till(issue_date, request, data.get("dates"))
    items = _ensure_items(data.get("items"), request.hints.items if request.hints else None, request)
    shipping = _to_float((data.get("totals") or {}).get("shipping"), 0.0)
    totals = _calculate_totals(items, shipping)
    terms = _ensure_terms(data.get("terms"), request.hints.terms if request.hints else None)
    payment = _ensure_payment(data.get("payment"), request)
    party_seller = _ensure_party(data.get("seller"), request.seller)
    party_buyer = _ensure_party(data.get("buyer"), request.buyer)
    doc_meta = _ensure_doc_meta(data.get("doc_meta"), request, False, "QUO")

    payload = {
        "doc_type": "QUOTATION",
        "currency": data.get("currency") or request.currency,
        "locale": data.get("locale") or request.locale,
        "seller": party_seller,
        "buyer": party_buyer,
        "doc_meta": doc_meta,
        "dates": {"issue_date": issue_date, "valid_till": valid_till},
        "items": [item.model_dump() for item in items],
        "totals": totals.model_dump(),
        "terms": terms.model_dump(),
        "notes": data.get("notes") or request.seller.notes,
        "payment": payment.model_dump(exclude_none=True) if payment else None,
    }

    try:
        model = QuotationOutput.model_validate(payload)
    except ValidationError:
        model = QuotationOutput.model_validate(payload, strict=False)

    model.totals = totals
    model.payment = _post_payment(model.payment, request, totals)
    model.dates.valid_till = model.dates.valid_till or valid_till
    return model


def build_invoice_output(raw: Dict[str, Any], request: GenerationRequest) -> TaxInvoiceOutput:
    data = deepcopy(raw) if isinstance(raw, dict) else {}
    data.setdefault("doc_type", "TAX_INVOICE")
    issue_date = _resolve_issue_date(request, data.get("dates"))
    due_date = _resolve_due_date(issue_date, request, data.get("dates"))
    items = _ensure_items(data.get("items"), request.hints.items if request.hints else None, request)
    shipping = _to_float((data.get("totals") or {}).get("shipping"), 0.0)
    totals = _calculate_totals(items, shipping)
    terms = _ensure_terms(data.get("terms"), request.hints.terms if request.hints else None)
    payment = _ensure_payment(data.get("payment"), request)
    gst = _ensure_gst(data.get("gst"), request)
    party_seller = _ensure_party(data.get("seller"), request.seller)
    party_buyer = _ensure_party(data.get("buyer"), request.buyer)
    doc_meta = _ensure_doc_meta(data.get("doc_meta"), request, True, "INV")

    payload = {
        "doc_type": "TAX_INVOICE",
        "currency": data.get("currency") or request.currency,
        "locale": data.get("locale") or request.locale,
        "seller": party_seller,
        "buyer": party_buyer,
        "doc_meta": doc_meta,
        "dates": {"issue_date": issue_date, "due_date": due_date},
        "items": [item.model_dump() for item in items],
        "totals": totals.model_dump(),
        "terms": terms.model_dump(),
        "payment": payment.model_dump(exclude_none=True) if payment else None,
        "gst": gst.model_dump(exclude_none=True) if gst else None,
    }

    try:
        model = TaxInvoiceOutput.model_validate(payload)
    except ValidationError:
        model = TaxInvoiceOutput.model_validate(payload, strict=False)

    model.totals = totals
    model.payment = _post_payment(model.payment, request, totals)
    model.dates.due_date = model.dates.due_date or due_date
    model.gst = gst
    return model


def _normalise_billing_plan(raw_parts: Any) -> List[Dict[str, Any]]:
    parts: List[Dict[str, Any]] = []
    if isinstance(raw_parts, list):
        parts = [part if isinstance(part, dict) else {} for part in raw_parts]
    if not parts:
        parts = [{"when": "Project kickoff", "percent": 40}, {"when": "Midway", "percent": 40}, {"when": "Completion", "percent": 20}]
    total = sum(_to_int(part.get("percent"), 0) for part in parts)
    if total == 0:
        equal = round(100 / len(parts)) if parts else 100
        parts = [{"when": part.get("when") or f"Milestone {idx+1}", "percent": equal} for idx, part in enumerate(parts)]
        total = sum(part["percent"] for part in parts)
    if total != 100 and parts:
        scaled: List[Dict[str, Any]] = []
        remainder = 100
        for idx, part in enumerate(parts):
            if idx == len(parts) - 1:
                percent = remainder
            else:
                percent = max(round(_to_int(part.get("percent"), 0) * 100 / total), 0)
                remainder -= percent
            scaled.append({"when": part.get("when") or f"Milestone {idx+1}", "percent": percent})
        parts = scaled
    return parts


def _ensure_milestones(raw: Any, request: GenerationRequest) -> List[Dict[str, Any]]:
    milestones: List[Dict[str, Any]] = []
    if isinstance(raw, list):
        milestones = [deepcopy(item) if isinstance(item, dict) else {} for item in raw]
    if not milestones:
        today = date.today()
        milestones = [
            {"name": "Discovery", "start": today, "end": today + timedelta(days=7), "fee": 0.0},
            {"name": "Execution", "start": today + timedelta(days=8), "end": today + timedelta(days=30), "fee": 0.0},
        ]
    normalised: List[Dict[str, Any]] = []
    for entry in milestones:
        start = entry.get("start")
        end = entry.get("end")
        try:
            start_date = start if isinstance(start, date) else date.fromisoformat(str(start))
        except (TypeError, ValueError):
            start_date = date.today()
        try:
            end_date = end if isinstance(end, date) else date.fromisoformat(str(end))
        except (TypeError, ValueError):
            end_date = start_date + timedelta(days=7)
        if end_date < start_date:
            end_date = start_date
        normalised.append(
            {
                "name": entry.get("name") or "Milestone",
                "start": start_date,
                "end": end_date,
                "fee": _to_float(entry.get("fee"), 0.0),
            }
        )
    return normalised


def _ensure_scope(raw: Any, fallback: str) -> List[str]:
    if isinstance(raw, list):
        cleaned = [str(item).strip() for item in raw if str(item).strip()]
        if cleaned:
            return cleaned
    text = fallback.strip()
    if text:
        return [text]
    return ["Scope as per requirement"]


def build_project_brief_output(raw: Dict[str, Any], request: GenerationRequest) -> ProjectBriefOutput:
    data = deepcopy(raw) if isinstance(raw, dict) else {}
    scope = _ensure_scope(data.get("scope"), request.requirement)
    deliverables = _ensure_scope(data.get("deliverables"), request.requirement)
    assumptions = data.get("assumptions") if isinstance(data.get("assumptions"), list) else []
    risks = data.get("risks") if isinstance(data.get("risks"), list) else []
    milestones = _ensure_milestones(data.get("milestones"), request)
    billing_plan = _normalise_billing_plan(data.get("billing_plan"))
    timeline_days = _to_int(data.get("timeline_days"), 30)
    title = data.get("title") or f"{request.seller.name} - Project Brief"
    objective = data.get("objective") or request.requirement
    seller = _ensure_party(data.get("seller"), request.seller)
    buyer = _ensure_party(data.get("buyer"), request.buyer)

    payload = {
        "title": title,
        "objective": objective,
        "scope": scope,
        "deliverables": deliverables,
        "assumptions": assumptions,
        "milestones": milestones,
        "timeline_days": max(timeline_days, 1),
        "billing_plan": billing_plan,
        "risks": risks,
        "seller": seller,
        "buyer": buyer,
    }

    try:
        model = ProjectBriefOutput.model_validate(payload)
    except ValidationError:
        model = ProjectBriefOutput.model_validate(payload, strict=False)
    return model
