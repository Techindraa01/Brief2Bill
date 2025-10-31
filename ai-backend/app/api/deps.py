"""Request-scoped dependencies (placeholders)"""
from typing import Dict

def get_settings() -> Dict:
    return {"env": "development"}
