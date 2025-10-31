"""Main entry point - thin shim for uvicorn"""
from app.main import create_app

app = create_app()

