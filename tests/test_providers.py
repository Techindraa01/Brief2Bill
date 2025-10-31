import pathlib
import sys

from fastapi.testclient import TestClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "ai-backend"))
from app.main import create_app


def test_providers_list():
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/v1/providers")
    assert response.status_code == 200
    data = response.json()
    assert "providers" in data
    assert isinstance(data["providers"], list)
