"""Validation service using jsonschema"""
import json
import jsonschema
from typing import List, Dict, Any
from pathlib import Path


class ValidationError:
    """Validation error detail"""
    def __init__(self, path: str, message: str):
        self.path = path
        self.message = message

    def to_dict(self) -> Dict[str, str]:
        return {"path": self.path, "message": self.message}


class ValidationService:
    """Validates documents against JSON schema"""

    def __init__(self):
        # Load schema from file
        schema_path = Path(__file__).parent.parent / "schemas" / "document_bundle.schema.json"
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

    def validate(self, bundle: Dict[str, Any]) -> tuple[bool, List[ValidationError]]:
        """Validate bundle against schema, return (is_valid, errors)"""
        errors = []

        try:
            jsonschema.validate(instance=bundle, schema=self.schema)
            return True, []
        except jsonschema.ValidationError as e:
            # Convert jsonschema error to our format
            path = "/" + "/".join(str(p) for p in e.absolute_path)
            errors.append(ValidationError(path, e.message))
            return False, errors
        except jsonschema.SchemaError as e:
            errors.append(ValidationError("/", f"Schema error: {e.message}"))
            return False, errors

    def validate_draft(self, draft: Dict[str, Any]) -> tuple[bool, List[ValidationError]]:
        """Validate a single draft against DocDraft schema"""
        errors = []

        try:
            # Validate against the DocDraft definition
            draft_schema = {
                "$ref": "#/$defs/DocDraft",
                "$defs": self.schema.get("$defs", {})
            }
            jsonschema.validate(instance=draft, schema=draft_schema)
            return True, []
        except jsonschema.ValidationError as e:
            path = "/" + "/".join(str(p) for p in e.absolute_path)
            errors.append(ValidationError(path, e.message))
            return False, errors
        except jsonschema.SchemaError as e:
            errors.append(ValidationError("/", f"Schema error: {e.message}"))
            return False, errors
