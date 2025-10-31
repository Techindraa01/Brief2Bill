"""Validation helpers: jsonschema + pydantic double-check (placeholder)"""
import jsonschema

def validate_schema(instance: dict, schema: dict) -> None:
    jsonschema.validate(instance, schema)
