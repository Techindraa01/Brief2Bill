"""Simple terminal UI for exercising Brief2Bill API endpoints."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


@dataclass
class LastState:
    """Holds the latest payloads fetched through the UI for reuse."""

    bundle: Optional[Dict[str, Any]] = None
    draft: Optional[Dict[str, Any]] = None


class TerminalUI:
    """Blocking terminal UI for manually testing the FastAPI backend."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=30.0)
        self.state = LastState()

    def run(self) -> None:
        try:
            while True:
                self._print_menu()
                choice = input("Select option: ").strip().lower()
                if choice in {"q", "quit", "exit"}:
                    print("Exiting.")
                    return
                handler = {
                    "1": self.check_health,
                    "2": self.list_providers,
                    "3": self.select_provider,
                    "4": self.get_active_provider,
                    "5": self.create_draft,
                    "6": self.validate_bundle,
                    "7": self.repair_bundle,
                    "8": self.compute_totals,
                    "9": self.generate_upi,
                }.get(choice)
                if handler is None:
                    print("Unknown option. Try again.\n")
                    continue
                try:
                    handler()
                except httpx.HTTPError as exc:
                    print(f"HTTP error: {exc}")
                except Exception as exc:  # noqa: BLE001 - surface unexpected issues interactively
                    print(f"Error: {exc}")
        finally:
            self.client.close()

    def _print_menu(self) -> None:
        print(
            """
=================== Brief2Bill Terminal UI ===================
1) GET  /v1/healthz
2) GET  /v1/providers
3) POST /v1/providers/select
4) GET  /v1/providers/active
5) POST /v1/draft
6) POST /v1/validate
7) POST /v1/repair
8) POST /v1/compute/totals
9) POST /v1/upi/deeplink
q) Quit
==============================================================
"""
        )

    def _print_response(self, response: httpx.Response) -> None:
        print(f"Status: {response.status_code}")
        try:
            data = response.json()
        except json.JSONDecodeError:
            print(response.text)
            return
        print(json.dumps(data, indent=2, ensure_ascii=False))

    def check_health(self) -> None:
        response = self.client.get("/v1/healthz")
        self._print_response(response)

    def list_providers(self) -> None:
        response = self.client.get("/v1/providers")
        self._print_response(response)

    def select_provider(self) -> None:
        provider = input("Provider (openrouter/groq/openai/gemini): ").strip() or "openai"
        model = input("Model identifier: ").strip() or "gpt-4o-mini"
        workspace = input("Workspace id [default]: ").strip() or "default"
        response = self.client.post(
            "/v1/providers/select",
            json={"provider": provider, "model": model, "workspace_id": workspace},
        )
        self._print_response(response)

    def get_active_provider(self) -> None:
        workspace = input("Workspace id [default]: ").strip() or "default"
        response = self.client.get("/v1/providers/active", params={"workspace_id": workspace})
        self._print_response(response)

    def create_draft(self) -> None:
        prompt = input("Requirement prompt: ").strip()
        if not prompt:
            print("Prompt is required. Aborting.")
            return
        prefer = input("Preferred doc types (comma separated, optional): ").strip()
        prefer_list = [item.strip().upper() for item in prefer.split(",") if item.strip()] if prefer else None
        currency = input("Currency [INR]: ").strip() or "INR"
        provider = input("Override provider (blank to skip): ").strip() or None
        model = input("Override model (blank to skip): ").strip() or None
        workspace = input("Workspace id [default]: ").strip() or "default"

        payload: Dict[str, Any] = {
            "prompt": prompt,
            "currency": currency,
            "workspace_id": workspace,
        }
        if prefer_list:
            payload["prefer"] = prefer_list
        if provider:
            payload["provider"] = provider
        if model:
            payload["model"] = model

        response = self.client.post("/v1/draft", json=payload)
        self._print_response(response)
        if response.status_code == 200:
            try:
                data = response.json()
            except json.JSONDecodeError:
                return
            self.state.bundle = data
            if data.get("drafts"):
                self.state.draft = data["drafts"][0]

    def validate_bundle(self) -> None:
        bundle = self._get_bundle_input()
        if bundle is None:
            return
        response = self.client.post("/v1/validate", json={"bundle": bundle})
        self._print_response(response)

    def repair_bundle(self) -> None:
        print("Supply bundle JSON or press Enter to reuse last bundle.")
        bundle = self._get_bundle_input(allow_empty=True)
        if bundle is None:
            return
        response = self.client.post("/v1/repair", json={"bundle": bundle})
        self._print_response(response)
        if response.status_code == 200:
            try:
                data = response.json()
            except json.JSONDecodeError:
                return
            self.state.bundle = data
            if data.get("drafts"):
                self.state.draft = data["drafts"][0]

    def compute_totals(self) -> None:
        draft = self._get_draft_input()
        if draft is None:
            return
        response = self.client.post("/v1/compute/totals", json={"draft": draft})
        self._print_response(response)
        if response.status_code == 200:
            try:
                data = response.json()
            except json.JSONDecodeError:
                return
            if "draft" in data:
                self.state.draft = data["draft"]

    def generate_upi(self) -> None:
        upi_id = input("UPI ID: ").strip()
        payee = input("Payee name: ").strip()
        amount_text = input("Amount (blank to omit): ").strip()
        note = input("Note (optional): ").strip()
        txn_ref = input("Transaction ref (optional): ").strip()
        callback = input("Callback URL (optional): ").strip()
        if not upi_id or not payee:
            print("UPI ID and Payee name are required.")
            return
        payload: Dict[str, Any] = {"upi_id": upi_id, "payee_name": payee}
        if amount_text:
            try:
                payload["amount"] = float(amount_text)
            except ValueError:
                print("Invalid amount. Use numeric values.")
                return
        if note:
            payload["note"] = note
        if txn_ref:
            payload["txn_ref"] = txn_ref
        if callback:
            payload["callback_url"] = callback
        response = self.client.post("/v1/upi/deeplink", json=payload)
        self._print_response(response)

    def _get_bundle_input(self, allow_empty: bool = False) -> Optional[Dict[str, Any]]:
        if self.state.bundle and allow_empty:
            raw = input("Bundle JSON (Enter to use last bundle): ").strip()
            if not raw:
                return self.state.bundle
        elif self.state.bundle:
            use_saved = input("Use last bundle? [Y/n]: ").strip().lower()
            if use_saved in {"", "y", "yes"}:
                return self.state.bundle
            raw = input("Bundle JSON: ").strip()
        else:
            raw = input("Bundle JSON: ").strip()
        if not raw:
            print("No bundle supplied.")
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON: {exc}")
            return None

    def _get_draft_input(self) -> Optional[Dict[str, Any]]:
        if self.state.draft:
            use_saved = input("Use last draft? [Y/n]: ").strip().lower()
            if use_saved in {"", "y", "yes"}:
                return self.state.draft
        raw = input("Draft JSON: ").strip()
        if not raw:
            print("No draft supplied.")
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON: {exc}")
            return None


def main() -> None:
    base_url = input("Base URL [http://localhost:8000]: ").strip() or "http://localhost:8000"
    ui = TerminalUI(base_url)
    ui.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
