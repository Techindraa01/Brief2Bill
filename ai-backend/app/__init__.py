"""Compatibility shim that mirrors the top-level app package."""
from importlib import import_module
from pathlib import Path

__path__ = [str(Path(__file__).resolve().parents[2] / "app")]
create_app = import_module("app.main").create_app
__all__ = ["create_app"]
