import pathlib
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "ai-backend"))
from app.main import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as client:
        yield client


def test_healthz(client):
    response = client.get("/v1/healthz")
    assert response.status_code == 200
    assert response.json()["ok"] is True
