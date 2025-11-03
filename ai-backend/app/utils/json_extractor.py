"""Utility helpers for extracting JSON payloads from model responses."""

from __future__ import annotations

import json
import re
from typing import Dict

_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_OBJECT_MATCH = re.compile(r"\{.*\}", re.DOTALL)


def extract_json(text: str) -> Dict[str, object]:
    """Extract a JSON object from an arbitrary text snippet."""

    try:
        return json.loads(text)
    except (TypeError, json.JSONDecodeError):
        pass

    block = _JSON_BLOCK.search(text)
    if block:
        candidate = block.group(1)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    brace = _OBJECT_MATCH.search(text)
    if brace:
        snippet = brace.group(0)
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not extract JSON object from response")
