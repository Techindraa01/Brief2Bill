"""Quick API test script"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/v1/health")
    print(f"Health: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_version():
    """Test version endpoint"""
    response = requests.get(f"{BASE_URL}/v1/version")
    print(f"Version: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_providers():
    """Test providers endpoint"""
    response = requests.get(f"{BASE_URL}/v1/providers")
    print(f"Providers: {response.status_code}")
    providers = response.json()  # Now returns a list of provider names directly
    print(f"Enabled providers: {providers}")
    print()

def test_provider_models():
    """Test provider models endpoint"""
    # First get list of providers
    response = requests.get(f"{BASE_URL}/v1/providers")
    providers = response.json()

    if providers:
        # Test models endpoint for first provider
        provider_name = providers[0]
        response = requests.get(f"{BASE_URL}/v1/providers/{provider_name}/models")
        print(f"Models for {provider_name}: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Provider: {data.get('provider')}")
            models = data.get('models', [])
            print(f"Found {len(models)} models")
            if models:
                print(f"Sample model: {models[0].get('id')}")
        else:
            print(f"Error: {response.text}")
    print()

def test_draft():
    """Test draft generation endpoint"""
    payload = {
        "prompt": "Create a quotation for web development services: 3 pages at 15000 each, SEO optimization 10000, hosting setup 5000. Client is ABC Corp, seller is XYZ Solutions.",
        "prefer": ["QUOTATION"],
        "currency": "INR",
        "workspace_id": "test",
        "provider": "openai",
        "model": "gpt-4o-mini"
    }
    
    print("Testing draft generation...")
    print(f"Prompt: {payload['prompt']}")
    
    response = requests.post(f"{BASE_URL}/v1/draft", json=payload)
    print(f"Draft: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Generated {len(data.get('drafts', []))} draft(s)")
        if data.get('drafts'):
            draft = data['drafts'][0]
            print(f"Doc Type: {draft.get('doc_type')}")
            print(f"Items: {len(draft.get('items', []))}")
            print(f"Grand Total: {draft.get('totals', {}).get('grand_total')}")
    else:
        print(f"Error: {response.text}")
    print()

def test_validate():
    """Test validation endpoint"""
    # Create a minimal valid bundle
    bundle = {
        "drafts": [
            {
                "doc_type": "QUOTATION",
                "doc_meta": {
                    "doc_id": "QUO-2025-0001",
                    "issue_date": "2025-10-31",
                    "valid_till": "2025-11-15"
                },
                "parties": {
                    "seller": {"name": "Test Seller"},
                    "buyer": {"name": "Test Buyer"}
                },
                "items": [
                    {
                        "description": "Test Item",
                        "qty": 1,
                        "unit_price": 1000,
                        "line_total": 1000
                    }
                ],
                "totals": {
                    "subtotal": 1000,
                    "grand_total": 1000
                }
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/v1/validate", json={"bundle": bundle})
    print(f"Validate: {response.status_code}")
    data = response.json()
    print(f"Valid: {data.get('ok')}")
    if not data.get('ok'):
        print(f"Errors: {len(data.get('errors', []))}")
    print()

if __name__ == "__main__":
    print("=== Brief2Bill API Tests ===\n")
    
    test_health()
    test_version()
    test_providers()
    test_validate()
    
    # Only test draft if we have an API key
    import os
    if os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("GROQ_API_KEY"):
        test_draft()
    else:
        print("Skipping draft test - no API keys configured")

