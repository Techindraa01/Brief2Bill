"""Safe JSON extraction from messy LLM text (placeholder)"""
import json

def extract_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None
