import json
import pathlib
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "ai-backend"))

from app.main import create_app  # noqa: E402
from app.providers.base import LLMProvider, LLMRawResponse, PromptPacket, ProviderCapabilities  # noqa: E402


class StubProvider(LLMProvider):
    def __init__(self) -> None:
        super().__init__(api_key="stub")

    async def generate(self, prompt: PromptPacket) -> LLMRawResponse:  # type: ignore[override]
        if "tax_invoice_output" in prompt.user_prompt:
            content = json.dumps(
                {
                    "doc_type": "TAX_INVOICE",
                    "seller": {"name": "Acme Pvt Ltd"},
                    "buyer": {"name": "Client Co"},
                    "currency": "INR",
                    "locale": "en-IN",
                    "doc_meta": {},
                    "dates": {"issue_date": "2024-02-01"},
                    "items": [
                        {"description": "Monthly retainer", "qty": 1, "unit_price": 25000, "tax_rate": 18}
                    ],
                    "totals": {"subtotal": 0, "discount_total": 0, "tax_total": 0, "shipping": 0, "round_off": 0, "grand_total": 0},
                    "terms": {"bullets": ["GST as applicable"]},
                    "payment": {"mode": "BANK_TRANSFER"},
                }
            )
        elif "project_brief_output" in prompt.user_prompt:
            content = json.dumps(
                {
                    "title": "Website Revamp",
                    "objective": "",
                    "scope": [],
                    "deliverables": [],
                    "milestones": [{"name": "Phase 1", "start": "2024-03-01", "end": "2024-03-10"}],
                    "timeline_days": 0,
                    "billing_plan": [{"when": "Kickoff", "percent": 30}, {"when": "Final", "percent": 30}],
                    "risks": [],
                }
            )
        else:
            content = json.dumps(
                {
                    "doc_type": "QUOTATION",
                    "seller": {"name": "Acme Pvt Ltd"},
                    "buyer": {"name": "Client Co"},
                    "currency": "INR",
                    "locale": "en-IN",
                    "dates": {"issue_date": "2024-01-01"},
                    "items": [
                        {
                            "description": "Website redesign",
                            "qty": 2,
                            "unit_price": 50000,
                            "discount": 1000,
                            "tax_rate": 18,
                        }
                    ],
                    "totals": {"subtotal": 0, "discount_total": 0, "tax_total": 0, "shipping": 0, "round_off": 0, "grand_total": 0},
                    "terms": {"bullets": ["Payment within 15 days"]},
                    "payment": {"mode": "UPI"},
                }
            )
        return LLMRawResponse(content=content, model=prompt.model, provider="stub")

    def capabilities(self) -> ProviderCapabilities:  # type: ignore[override]
        return ProviderCapabilities(supports_json_schema=True, supports_plain_json=True)

    async def list_models(self):  # type: ignore[override]
        return []


@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app) as client:
        provider = StubProvider()
        client.app.state.provider_service._providers["openrouter"] = provider
        yield client


def _base_payload():
    return {
        "to": {
            "name": "Client Co",
            "email": "client@example.com",
            "place_of_supply": "KA",
        },
        "from": {
            "name": "Acme Pvt Ltd",
            "email": "sales@acme.test",
            "tax_prefs": {"place_of_supply": "KA"},
            "bank": {"upi_id": "acme@upi"},
        },
        "requirement": "Website redesign and support",
    }


def test_generate_quotation(client):
    payload = _base_payload()
    response = client.post("/v1/generate/quotation", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["doc_type"] == "QUOTATION"
    assert data["totals"]["grand_total"] > 0
    assert data["payment"]["mode"] == "UPI"
    assert data["payment"]["upi_deeplink"].startswith("upi://")


def test_generate_invoice(client):
    payload = _base_payload()
    response = client.post("/v1/generate/invoice", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["doc_type"] == "TAX_INVOICE"
    assert data["doc_meta"]["doc_no"]
    assert data["totals"]["grand_total"] > 0


def test_generate_project_brief(client):
    payload = _base_payload()
    response = client.post("/v1/generate/project-brief", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"]
    assert sum(part["percent"] for part in data["billing_plan"]) == 100
