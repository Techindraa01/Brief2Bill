"""Repair routines for partially valid payloads."""

from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
from typing import Any, Dict, List

from ..models.document_models import DocumentBundle, DocDraft, Item
from .totals import compute_totals


DEFAULT_TERMS = [
    "Prices exclusive of applicable taxes unless stated otherwise",
    "Payment due within agreed timeline",
]


def _ensure_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _coerce_number(value: Any, default: float = 0.0) -> float:
    """Coerce any value to a float, handling strings and None."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
    return default


def _coerce_item(raw: Dict[str, Any]) -> Dict[str, Any]:
    data = {
        "description": raw.get("description") or "Line item",
        "qty": _coerce_number(raw.get("qty"), 1.0),
        "unit_price": _coerce_number(raw.get("unit_price"), 0.0),
        "unit": raw.get("unit", "pcs"),
        "discount": _coerce_number(raw.get("discount"), 0.0),
        "tax_rate": _coerce_number(raw.get("tax_rate"), 0.0),
        "hsn_sac": raw.get("hsn_sac"),
    }
    return Item.model_validate(data).model_dump()


def _repair_dates(draft: Dict[str, Any]) -> Dict[str, Any]:
    dates = draft.setdefault("dates", {})
    issue_raw = dates.get("issue_date") or date.today().isoformat()
    try:
        issue_date = date.fromisoformat(str(issue_raw))
    except ValueError:
        issue_date = date.today()
    dates["issue_date"] = issue_date.isoformat()

    if draft.get("doc_type") == "TAX_INVOICE" and not dates.get("due_date"):
        dates["due_date"] = (issue_date + timedelta(days=7)).isoformat()
    if draft.get("doc_type") == "QUOTATION" and not dates.get("valid_till"):
        dates["valid_till"] = (issue_date + timedelta(days=15)).isoformat()
    return draft


def repair_draft(draft: Dict[str, Any]) -> Dict[str, Any]:
    draft = deepcopy(draft)

    # Fix invalid doc_type values - map PROJECT_BRIEF to QUOTATION
    doc_type = draft.get("doc_type", "QUOTATION")
    if doc_type not in ("QUOTATION", "TAX_INVOICE"):
        # Map invalid doc_types to QUOTATION as default
        draft["doc_type"] = "QUOTATION"
    else:
        draft["doc_type"] = doc_type

    draft.setdefault("locale", "en-IN")
    draft.setdefault("currency", "INR")
    draft.setdefault("seller", {"name": draft.get("seller", {}).get("name", "Seller")})
    draft.setdefault("buyer", {"name": draft.get("buyer", {}).get("name", "Buyer")})

    # Ensure terms has bullets array
    terms = draft.get("terms", {})
    if not isinstance(terms, dict):
        terms = {}
    terms.setdefault("title", "Terms & Conditions")
    terms.setdefault("bullets", DEFAULT_TERMS)
    # Ensure bullets is a list
    if not isinstance(terms.get("bullets"), list):
        terms["bullets"] = DEFAULT_TERMS
    draft["terms"] = terms

    # Ensure totals exists with all required fields and coerce to numbers
    totals = draft.get("totals", {})
    if not isinstance(totals, dict):
        totals = {}
    # Coerce all total fields to numbers
    totals["subtotal"] = _coerce_number(totals.get("subtotal"), 0.0)
    totals["discount_total"] = _coerce_number(totals.get("discount_total"), 0.0)
    totals["tax_total"] = _coerce_number(totals.get("tax_total"), 0.0)
    totals["grand_total"] = _coerce_number(totals.get("grand_total"), 0.0)
    totals["round_off"] = _coerce_number(totals.get("round_off"), 0.0)
    if "shipping" in totals:
        totals["shipping"] = _coerce_number(totals.get("shipping"), 0.0)
    draft["totals"] = totals

    _repair_dates(draft)

    raw_items = _ensure_list(draft.get("items")) or [
        {
            "description": "Consulting services",
            "qty": 1,
            "unit_price": 0,
        }
    ]
    draft["items"] = [_coerce_item(item) for item in raw_items]

    # Now validate after all repairs
    validated = DocDraft.model_validate(draft)
    # Recompute totals to ensure accuracy
    totals = compute_totals(validated)
    validated.totals = totals
    return validated.model_dump()


def repair_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    bundle = deepcopy(bundle or {})
    raw_drafts = bundle.get("drafts")
    if not isinstance(raw_drafts, list) or not raw_drafts:
        raw_drafts = [repair_draft({})]
    else:
        raw_drafts = [repair_draft(d) for d in raw_drafts]

    project_brief = bundle.get("project_brief")
    payload = {"drafts": raw_drafts}
    if project_brief:
        payload["project_brief"] = project_brief
    repaired = DocumentBundle.model_validate(payload)
    return repaired.model_dump(exclude_none=True)
