import pathlib
import sys

from fastapi.testclient import TestClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "ai-backend"))
from app.main import create_app


def test_draft_fallback_flow():
    app = create_app()
    with TestClient(app) as client:
        payload = {"prompt": "Need a basic quotation for website revamp"}
        response = client.post("/v1/draft", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "drafts" in data
        assert len(data["drafts"]) >= 1

        validate = client.post("/v1/validate", json={"bundle": data})
        assert validate.status_code == 200
        assert validate.json()["ok"] is True

        draft = data["drafts"][0]
        totals = client.post("/v1/compute/totals", json={"draft": draft})
        assert totals.status_code == 200
        assert "draft" in totals.json()
