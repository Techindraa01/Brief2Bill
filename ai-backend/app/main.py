"""FastAPI app factory (placeholder)"""
from typing import Callable

def create_app() -> object:
    """Return an ASGI app or placeholder object.

    Replace with FastAPI() and real wiring.
    """
    class AppPlaceholder:
        def __init__(self):
            self.name = "ai-backend-placeholder"

    return AppPlaceholder()


if __name__ == "__main__":
    app = create_app()
    print("Created app:", app.name)
