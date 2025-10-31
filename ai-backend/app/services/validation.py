"""Validation helpers for DocumentBundle payloads."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import jsonschema


class ValidationErrorDict(Dict[str, Any]):
    path: str
    message: str


class ValidationService:
    """Validate payloads against the DocumentBundle schema."""

    def __init__(self) -> None:
        schema_path = Path(__file__).parent.parent / "schemas" / "document_bundle.schema.json"
        with schema_path.open("r", encoding="utf-8") as handle:
            self.schema = json.load(handle)

        self._resolver = jsonschema.validators.RefResolver.from_schema(self.schema)
        self._validator = jsonschema.validators.Draft202012Validator(
            self.schema, resolver=self._resolver
        )

    def extract_json(self, raw: str) -> Dict[str, Any]:
        """Extract a JSON document from raw model output."""

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        block = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
        if block:
            candidate = block.group(1)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        brace_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError("Could not extract JSON from provider response")

    def validate(self, payload: Dict[str, Any]) -> Tuple[bool, List[Dict[str, str]]]:
        errors: List[Dict[str, str]] = []

        for error in self._validator.iter_errors(payload):
            path = "/" + "/".join(str(part) for part in error.absolute_path)
            errors.append({"path": path or "/", "message": error.message})

        return not errors, errors

    def validate_draft(self, draft: Dict[str, Any]) -> Tuple[bool, List[Dict[str, str]]]:
        draft_schema = {"$ref": "#/$defs/DocDraft", "$defs": self.schema.get("$defs", {})}
        validator = jsonschema.validators.Draft202012Validator(draft_schema, resolver=self._resolver)
        errors = []
        for error in validator.iter_errors(draft):
            path = "/" + "/".join(str(part) for part in error.absolute_path)
            errors.append({"path": path or "/", "message": error.message})
        return not errors, errors
