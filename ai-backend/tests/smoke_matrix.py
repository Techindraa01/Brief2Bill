"""
Comprehensive smoke test matrix for Brief2Bill AI Backend
Executes all acceptance criteria from the test plan
"""
import httpx
import json
import sys
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

class TestResult:
    def __init__(self, section: str, test: str):
        self.section = section
        self.test = test
        self.passed = False
        self.error = None
        self.details = None

class SmokeTestMatrix:
    def __init__(self):
        self.results: List[TestResult] = []
        self.client = httpx.Client(base_url=BASE_URL, timeout=TIMEOUT)
        self.enabled_providers = []
        self.provider_models = {}
        
    def log(self, msg: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level:5s} | {msg}")
    
    def add_result(self, section: str, test: str, passed: bool, error: str = None, details: Any = None):
        result = TestResult(section, test)
        result.passed = passed
        result.error = error
        result.details = details
        self.results.append(result)
        
        status = "✓ PASS" if passed else "✗ FAIL"
        self.log(f"{status} | {section} | {test}")
        if error:
            self.log(f"  Error: {error}", "ERROR")
    
    # Section 0: Preflight
    def test_0_preflight(self):
        section = "0_PREFLIGHT"
        
        # Test health endpoint
        try:
            resp = self.client.get("/v1/healthz")
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            data = resp.json()
            assert data.get("ok") is True, "Health check failed"
            assert "version" in data, "Version missing from health response"
            self.log(f"Server version: {data.get('version')}")
            self.add_result(section, "health_endpoint", True)
        except Exception as e:
            self.add_result(section, "health_endpoint", False, str(e))
            return False
        
        return True
    
    # Section 1: Discovery
    def test_1_discovery(self):
        section = "1_DISCOVERY"
        
        try:
            resp = self.client.get("/v1/providers")
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            data = resp.json()
            
            assert "providers" in data, "Missing 'providers' key"
            providers = data["providers"]
            
            # Build enabled providers list
            for p in providers:
                if p.get("enabled"):
                    name = p["name"]
                    self.enabled_providers.append(name)
                    
                    # Select known-good model
                    models = p.get("models", [])
                    if name == "openai":
                        model = next((m["id"] for m in models if "gpt-4o-mini" in m["id"]), None)
                    elif name == "openrouter":
                        model = next((m["id"] for m in models if "openai/gpt-4o" in m["id"]), None)
                    elif name == "groq":
                        model = next((m["id"] for m in models if "llama-3.3-70b" in m["id"] or "llama-3.1-70b" in m["id"]), None)
                    elif name == "gemini":
                        model = next((m["id"] for m in models if "gemini-2.5-flash" in m["id"] or "gemini-1.5-flash" in m["id"]), None)
                    else:
                        model = models[0]["id"] if models else None
                    
                    if model:
                        self.provider_models[name] = model
                        self.log(f"Provider {name}: {model}")
            
            if not self.enabled_providers:
                self.add_result(section, "providers_discovery", False, "No enabled providers found")
                return False
            
            self.add_result(section, "providers_discovery", True, details=self.enabled_providers)
            return True
            
        except Exception as e:
            self.add_result(section, "providers_discovery", False, str(e))
            return False
    
    # Section 2: Memory/Workspace selection
    def test_2_memory(self):
        section = "2_MEMORY"
        
        if "groq" not in self.provider_models or "openai" not in self.provider_models:
            self.add_result(section, "workspace_isolation", False, "Need both groq and openai enabled")
            return False
        
        try:
            # Select groq for workspace A
            resp = self.client.post("/v1/providers/select", json={
                "provider": "groq",
                "model": self.provider_models["groq"],
                "workspace_id": "wA"
            })
            assert resp.status_code == 200, f"Select failed: {resp.status_code}"
            
            # Verify workspace A
            resp = self.client.get("/v1/providers/active", params={"workspace_id": "wA"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["provider"] == "groq", f"Expected groq, got {data['provider']}"
            
            # Select openai for workspace B
            resp = self.client.post("/v1/providers/select", json={
                "provider": "openai",
                "model": self.provider_models["openai"],
                "workspace_id": "wB"
            })
            assert resp.status_code == 200
            
            # Verify workspace B
            resp = self.client.get("/v1/providers/active", params={"workspace_id": "wB"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["provider"] == "openai", f"Expected openai, got {data['provider']}"
            
            # Re-verify workspace A still groq
            resp = self.client.get("/v1/providers/active", params={"workspace_id": "wA"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["provider"] == "groq", f"Workspace A changed unexpectedly"
            
            self.add_result(section, "workspace_isolation", True)
            return True
            
        except Exception as e:
            self.add_result(section, "workspace_isolation", False, str(e))
            return False
    
    # Section 3: Structured output enforcement
    def test_3_structured_output(self):
        section = "3_STRUCTURED_OUTPUT"
        
        base_request = {
            "prompt": "Build a 1-page product landing in Next.js, 2-week timeline, budget 40–45k INR. Include 3-month maintenance as optional line. Buyer: Indigo Retail Pvt Ltd. UPI preferred.",
            "prefer": ["QUOTATION", "PROJECT_BRIEF"],
            "currency": "INR",
            "defaults": {
                "seller": {
                    "name": "Acme Solutions",
                    "gstin": "24ABCDE1234F1Z5",
                    "bank": {"upi_id": "acme@upi"}
                }
            },
            "workspace_id": "wA"
        }
        
        for provider in self.enabled_providers:
            if provider not in self.provider_models:
                continue
            
            try:
                model = self.provider_models[provider]
                headers = {
                    "X-Provider": provider,
                    "X-Model": model
                }
                
                resp = self.client.post("/v1/draft", json=base_request, headers=headers)
                assert resp.status_code == 200, f"Draft failed: {resp.status_code} - {resp.text}"
                
                bundle = resp.json()
                
                # Validate structure
                assert "drafts" in bundle, "Missing 'drafts' key"
                assert len(bundle["drafts"]) > 0, "No drafts returned"
                
                draft = bundle["drafts"][0]
                assert draft.get("doc_type") == "QUOTATION", f"Expected QUOTATION, got {draft.get('doc_type')}"
                assert "dates" in draft, "Missing dates"
                assert "issue_date" in draft["dates"], "Missing issue_date"
                assert "valid_till" in draft["dates"], "Missing valid_till"
                assert "items" in draft, "Missing items"
                assert len(draft["items"]) > 0, "No items"
                
                # Check numeric fields
                item = draft["items"][0]
                assert isinstance(item.get("unit_price"), (int, float)), "unit_price not numeric"
                assert isinstance(item.get("qty"), (int, float)), "qty not numeric"
                
                # Check totals
                if "totals" in draft:
                    totals = draft["totals"]
                    assert isinstance(totals.get("grand_total"), (int, float)), "grand_total not numeric"
                
                self.add_result(section, f"{provider}_structured_output", True)
                
            except Exception as e:
                self.add_result(section, f"{provider}_structured_output", False, str(e))
        
        return True
    
    # Section 5: Validate and repair
    def test_5_validate_repair(self):
        section = "5_VALIDATE_REPAIR"
        
        # Create a corrupted bundle
        corrupted = {
            "drafts": [{
                "doc_type": "QUOTATION",
                "seller": {"name": "Test"},
                "buyer": {"name": "Buyer"},
                "dates": {"issue_date": "2025-01-15"},  # Missing valid_till
                "items": [{
                    "description": "Item 1",
                    "quantity": 1,
                    "unit_price": "28000",  # String instead of number
                    "tax_rate": 18
                }],
                "totals": {}
            }]
        }
        
        try:
            # Validate - should fail
            resp = self.client.post("/v1/validate", json={"bundle": corrupted})
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("ok") is False, "Validation should have failed"
            assert len(data.get("errors", [])) > 0, "Should have errors"
            
            self.add_result(section, "validate_detects_errors", True)
            
        except Exception as e:
            self.add_result(section, "validate_detects_errors", False, str(e))
            return False
        
        try:
            # Repair
            resp = self.client.post("/v1/repair", json={"bundle": corrupted})
            assert resp.status_code == 200
            repaired = resp.json()
            
            # Validate repaired
            resp = self.client.post("/v1/validate", json={"bundle": repaired})
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("ok") is True, f"Repaired bundle still invalid: {data.get('errors')}"
            
            # Check repairs
            draft = repaired["drafts"][0]
            assert isinstance(draft["items"][0]["unit_price"], (int, float)), "unit_price not repaired to number"
            assert "valid_till" in draft["dates"], "valid_till not added"
            
            self.add_result(section, "repair_fixes_errors", True)
            
        except Exception as e:
            self.add_result(section, "repair_fixes_errors", False, str(e))
            return False
        
        return True
    
    # Section 6: UPI deeplink
    def test_6_upi_deeplink(self):
        section = "6_UPI_DEEPLINK"
        
        try:
            payload = {
                "upi_id": "acme@upi",
                "payee_name": "Acme Solutions",
                "amount": 43660,
                "currency": "INR",
                "note": "Advance 50%",
                "txn_ref": "INV-2025-0041"
            }
            
            resp = self.client.post("/v1/upi/deeplink", json=payload)
            assert resp.status_code == 200, f"UPI deeplink failed: {resp.status_code}"
            
            data = resp.json()
            assert "deeplink" in data, "Missing deeplink"
            assert data["deeplink"].startswith("upi://pay?"), f"Invalid deeplink format: {data['deeplink']}"
            # Check for URL-encoded UPI ID (@ becomes %40)
            assert "pa=acme%40upi" in data["deeplink"] or "pa=acme@upi" in data["deeplink"], f"Missing UPI ID in deeplink: {data['deeplink']}"
            assert "qr_payload" in data, "Missing qr_payload"
            
            self.add_result(section, "upi_deeplink_generation", True)
            return True
            
        except Exception as e:
            self.add_result(section, "upi_deeplink_generation", False, str(e))
            return False
    
    # Section 8: Error envelope
    def test_8_error_envelope(self):
        section = "8_ERROR_ENVELOPE"
        
        try:
            # Empty body should fail validation
            resp = self.client.post("/v1/draft", json={})
            assert resp.status_code in [400, 422], f"Expected 400/422, got {resp.status_code}"
            
            data = resp.json()
            assert "error" in data, "Missing error envelope"
            error = data["error"]
            assert "code" in error, "Missing error code"
            assert "message" in error, "Missing error message"
            assert "request_id" in error, "Missing request_id"
            
            self.add_result(section, "error_envelope_structure", True)
            return True
            
        except Exception as e:
            self.add_result(section, "error_envelope_structure", False, str(e))
            return False
    
    def print_summary(self):
        print("\n" + "="*70)
        print("SMOKE TEST MATRIX SUMMARY")
        print("="*70)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} ({100*passed//total if total else 0}%)")
        print(f"Failed: {failed}")
        
        if failed > 0:
            print("\nFailed Tests:")
            for r in self.results:
                if not r.passed:
                    print(f"  ✗ {r.section} | {r.test}")
                    if r.error:
                        print(f"    {r.error}")
        
        print("\nEnabled Providers:", ", ".join(self.enabled_providers) if self.enabled_providers else "None")
        print("="*70)
        
        return failed == 0
    
    def run_all(self):
        self.log("Starting smoke test matrix...")
        
        # Run tests in order
        if not self.test_0_preflight():
            self.log("Preflight failed, aborting", "ERROR")
            return False
        
        if not self.test_1_discovery():
            self.log("Discovery failed, aborting", "ERROR")
            return False
        
        self.test_2_memory()
        self.test_3_structured_output()
        self.test_5_validate_repair()
        self.test_6_upi_deeplink()
        self.test_8_error_envelope()
        
        return self.print_summary()

if __name__ == "__main__":
    matrix = SmokeTestMatrix()
    success = matrix.run_all()
    sys.exit(0 if success else 1)

