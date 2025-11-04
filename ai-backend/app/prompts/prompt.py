    """Prompt builders for dedicated generation endpoints."""

    from __future__ import annotations

    import json
    from datetime import date, datetime
    from pathlib import Path
    from typing import Any, Dict, Tuple

    from ..models.generation import GenerationRequest

    _SYSTEM_PROMPT = (
        "You are an expert commercial-docs drafter for India-focused SMEs.\n"
        "Output STRICT JSON matching the provided JSON Schema. No markdown, no comments, no extra keys.\n"
        "Prefer INR context and GST. For quotations set valid_till = issue_date + 14..15 days; for invoices set due_date = issue_date + 7 days unless specified. Use conservative defaults when ambiguous."
    )

    _QUOTATION_TEMPLATE = (
        "Task: Generate a QUOTATION with line items, totals, terms, and optional UPI payment.\n"
        "Inputs:\n"
        "- Seller (FROM): {from_json}\n"
        "- Buyer (TO): {to_json}\n"
        "- Currency: {currency}\n"
        "- Locale: {locale}\n"
        "- Hints: {hints_json}\n"
        "- Requirement: {requirement_text}\n"
        "Return a single JSON object obeying quotation_output.schema.json."
    )

    _INVOICE_TEMPLATE = (
        "Task: Generate a TAX_INVOICE suitable for GST in India with due date, GST breakup, totals, and payment block.\n"
        "Inputs:\n"
        "- Seller (FROM): {from_json}\n"
        "- Buyer (TO): {to_json}\n"
        "- Currency: {currency}\n"
        "- Locale: {locale}\n"
        "- Hints: {hints_json}\n"
        "- Requirement: {requirement_text}\n"
        "Return a single JSON object obeying tax_invoice_output.schema.json."
    )

    _PROJECT_TEMPLATE = (
        "Task: Generate a PROJECT BRIEF with title, objective, scope, deliverables, milestones, billing plan totaling 100%, risks, and timeline_days.\n"
        "Inputs:\n"
        "- Seller (FROM): {from_json}\n"
        "- Buyer (TO): {to_json}\n"
        "- Currency: {currency}\n"
        "- Locale: {locale}\n"
        "- Hints: {hints_json}\n"
        "- Requirement: {requirement_text}\n"
        "Return a single JSON object obeying project_brief_output.schema.json."
    )

    _SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas" / "outputs"


    def _load_schema(filename: str) -> Dict[str, Any]:
        with (_SCHEMA_DIR / filename).open("r", encoding="utf-8") as handle:
            return json.load(handle)


    def _json_dump(data: Any) -> str:
        """Serialize data to JSON, handling date/datetime objects."""

        def default_serializer(obj: Any) -> str:
            """Custom serializer for non-JSON-serializable objects."""
            if isinstance(obj, (date, datetime)):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

        return json.dumps(data, ensure_ascii=False, sort_keys=True, default=default_serializer)


    def build_quotation_prompt(request: GenerationRequest) -> Tuple[str, str, Dict[str, Any]]:
        schema = _load_schema("quotation_output.schema.json")
        hints = request.hints.model_dump(exclude_none=True) if request.hints else {}
        user = _QUOTATION_TEMPLATE.format(
            from_json=_json_dump(request.seller.model_dump(exclude_none=True)),
            to_json=_json_dump(request.buyer.model_dump(exclude_none=True)),
            currency=request.currency,
            locale=request.locale,
            hints_json=_json_dump(hints),
            requirement_text=request.requirement,
        )
        return _SYSTEM_PROMPT, user, schema


    def build_invoice_prompt(request: GenerationRequest) -> Tuple[str, str, Dict[str, Any]]:
        schema = _load_schema("tax_invoice_output.schema.json")
        hints = request.hints.model_dump(exclude_none=True) if request.hints else {}
        user = _INVOICE_TEMPLATE.format(
            from_json=_json_dump(request.seller.model_dump(exclude_none=True)),
            to_json=_json_dump(request.buyer.model_dump(exclude_none=True)),
            currency=request.currency,
            locale=request.locale,
            hints_json=_json_dump(hints),
            requirement_text=request.requirement,
        )
        return _SYSTEM_PROMPT, user, schema


    def build_project_brief_prompt(request: GenerationRequest) -> Tuple[str, str, Dict[str, Any]]:
        schema = _load_schema("project_brief_output.schema.json")
        hints = request.hints.model_dump(exclude_none=True) if request.hints else {}
        user = _PROJECT_TEMPLATE.format(
            from_json=_json_dump(request.seller.model_dump(exclude_none=True)),
            to_json=_json_dump(request.buyer.model_dump(exclude_none=True)),
            currency=request.currency,
            locale=request.locale,
            hints_json=_json_dump(hints),
            requirement_text=request.requirement,
        )
        return _SYSTEM_PROMPT, user, schema
