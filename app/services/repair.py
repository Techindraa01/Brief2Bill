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


def _coerce_item(raw: Dict[str, Any]) -> Dict[str, Any]:
    data = {
        "description": raw.get("description") or "Line item",
        "qty": raw.get("qty", 1),
        "unit_price": raw.get("unit_price", 0),
        "unit": raw.get("unit", "pcs"),
        "discount": raw.get("discount", 0),
        "tax_rate": raw.get("tax_rate", 0),
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
    draft.setdefault("doc_type", "QUOTATION")
    draft.setdefault("locale", "en-IN")
    draft.setdefault("currency", "INR")
    draft.setdefault("seller", {"name": draft.get("seller", {}).get("name", "Seller")})
    draft.setdefault("buyer", {"name": draft.get("buyer", {}).get("name", "Buyer")})
    draft.setdefault("terms", {"title": "Terms & Conditions", "bullets": DEFAULT_TERMS})
    draft.setdefault("totals", {"subtotal": 0, "discount_total": 0, "tax_total": 0, "grand_total": 0, "round_off": 0})

    _repair_dates(draft)

    raw_items = _ensure_list(draft.get("items")) or [
        {
            "description": "Consulting services",
            "qty": 1,
            "unit_price": 0,
        }
    ]
    draft["items"] = [_coerce_item(item) for item in raw_items]

    validated = DocDraft.model_validate(draft)
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
