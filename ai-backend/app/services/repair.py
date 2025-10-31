"""Repair service for fixing invalid/incomplete bundles"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from .totals import recompute_draft_totals


def repair_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Repair a bundle with missing or invalid fields"""

    # Ensure drafts array exists
    if "drafts" not in bundle or not isinstance(bundle["drafts"], list):
        bundle["drafts"] = []

    # Repair each draft
    for i, draft in enumerate(bundle["drafts"]):
        bundle["drafts"][i] = repair_draft(draft)

    return bundle


def repair_draft(draft: Dict[str, Any]) -> Dict[str, Any]:
    """Repair a single draft with missing or invalid fields"""

    # Ensure doc_type
    if "doc_type" not in draft:
        draft["doc_type"] = "QUOTATION"

    # Ensure doc_meta
    if "doc_meta" not in draft or not isinstance(draft["doc_meta"], dict):
        draft["doc_meta"] = {}

    draft["doc_meta"] = repair_doc_meta(draft["doc_meta"], draft["doc_type"])

    # Ensure parties
    if "parties" not in draft or not isinstance(draft["parties"], dict):
        draft["parties"] = {"seller": {}, "buyer": {}}

    draft["parties"] = repair_parties(draft["parties"])

    # Ensure items
    if "items" not in draft or not isinstance(draft["items"], list):
        draft["items"] = []

    draft["items"] = repair_items(draft["items"])

    # Recompute totals
    draft = recompute_draft_totals(draft)

    # Ensure terms array
    if "terms" not in draft or not isinstance(draft["terms"], list):
        draft["terms"] = []

    # Ensure payment object
    if "payment" not in draft or not isinstance(draft["payment"], dict):
        draft["payment"] = {}

    return draft


def repair_doc_meta(meta: Dict[str, Any], doc_type: str) -> Dict[str, Any]:
    """Repair doc_meta with defaults"""

    # Ensure doc_id
    if "doc_id" not in meta or not meta["doc_id"]:
        prefix = "QT" if doc_type == "QUOTATION" else "INV"
        today = datetime.now()
        meta["doc_id"] = f"{prefix}-{today.year}-{today.month:02d}{today.day:02d}-001"

    # Ensure issue_date
    if "issue_date" not in meta or not meta["issue_date"]:
        meta["issue_date"] = datetime.now().strftime("%Y-%m-%d")

    # Parse issue_date for calculations
    try:
        issue_date = datetime.strptime(meta["issue_date"], "%Y-%m-%d")
    except (ValueError, TypeError):
        issue_date = datetime.now()
        meta["issue_date"] = issue_date.strftime("%Y-%m-%d")

    # Set due_date for invoices (7 days)
    if doc_type == "TAX_INVOICE" and ("due_date" not in meta or not meta["due_date"]):
        due_date = issue_date + timedelta(days=7)
        meta["due_date"] = due_date.strftime("%Y-%m-%d")

    # Set valid_till for quotations (15 days)
    if doc_type == "QUOTATION" and ("valid_till" not in meta or not meta["valid_till"]):
        valid_till = issue_date + timedelta(days=15)
        meta["valid_till"] = valid_till.strftime("%Y-%m-%d")

    return meta


def repair_parties(parties: Dict[str, Any]) -> Dict[str, Any]:
    """Repair parties with defaults"""

    if "seller" not in parties or not isinstance(parties["seller"], dict):
        parties["seller"] = {}

    if "buyer" not in parties or not isinstance(parties["buyer"], dict):
        parties["buyer"] = {}

    # Ensure name for both parties
    if "name" not in parties["seller"] or not parties["seller"]["name"]:
        parties["seller"]["name"] = "Seller Name"

    if "name" not in parties["buyer"] or not parties["buyer"]["name"]:
        parties["buyer"]["name"] = "Buyer Name"

    # Ensure country defaults to India
    for party_key in ["seller", "buyer"]:
        if "country" not in parties[party_key]:
            parties[party_key]["country"] = "India"

    return parties


def repair_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Repair items with defaults"""

    repaired = []

    for item in items:
        if not isinstance(item, dict):
            continue

        # Ensure required fields
        if "description" not in item or not item["description"]:
            item["description"] = "Item"

        # Coerce numbers from strings
        for field in ["qty", "unit_price", "discount", "tax_rate"]:
            if field in item:
                try:
                    item[field] = float(item[field])
                except (ValueError, TypeError):
                    item[field] = 0.0

        # Set defaults
        if "qty" not in item:
            item["qty"] = 1.0
        if "unit_price" not in item:
            item["unit_price"] = 0.0
        if "discount" not in item:
            item["discount"] = 0.0
        if "tax_rate" not in item:
            item["tax_rate"] = 0.0
        if "unit" not in item:
            item["unit"] = "nos"

        # line_total and line_tax will be computed by totals service
        item["line_total"] = 0.0
        item["line_tax"] = 0.0

        repaired.append(item)

    return repaired
