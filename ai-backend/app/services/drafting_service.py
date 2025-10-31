"""Drafting service: orchestrates LLM calls with prompts"""
import json
import re
from typing import Dict, Any, List, Optional
from ..providers.base import LLMProvider, PromptPacket
from .validation import ValidationService
from .repair import repair_bundle


# System prompt as per spec
SYSTEM_PROMPT = """You are an expert commercial documents drafter for India-focused SMEs.
Output STRICT JSON matching the provided JSON Schema for DocumentBundle.
Do not include markdown, comments, or extra keys.
Prefer INR context, GST where applicable, 14–15 day validity for quotations, and 7-day due date for invoices unless user specifies otherwise.
Use conservative defaults when ambiguous."""


class DraftingService:
    """Service for generating document bundles from requirements"""

    def __init__(self, validation_service: ValidationService):
        self.validation_service = validation_service
        self.document_schema = validation_service.schema

    def build_user_prompt(
        self,
        requirement: str,
        doc_types: Optional[List[str]] = None,
        currency: str = "INR",
        seller_defaults: Optional[Dict[str, Any]] = None,
        buyer_hint: Optional[str] = None
    ) -> str:
        """Build user prompt from requirements"""

        if doc_types is None:
            doc_types = ["QUOTATION"]

        prompt = f"""Requirement:
{requirement}

Preferences:
- doc_types: {json.dumps(doc_types)}
- currency: {currency}
- seller_defaults: {json.dumps(seller_defaults) if seller_defaults else "null"}
- buyer_hint: {buyer_hint if buyer_hint else "null"}

Return: a single JSON object of type DocumentBundle.
Schema name: DocumentBundle"""

        return prompt

    async def generate_bundle(
        self,
        provider: LLMProvider,
        model: str,
        requirement: str,
        doc_types: Optional[List[str]] = None,
        currency: str = "INR",
        seller_defaults: Optional[Dict[str, Any]] = None,
        buyer_hint: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate document bundle from requirement"""

        # Build prompts
        user_prompt = self.build_user_prompt(
            requirement=requirement,
            doc_types=doc_types,
            currency=currency,
            seller_defaults=seller_defaults,
            buyer_hint=buyer_hint
        )

        # Prepare prompt packet
        schema_to_use = schema or self.document_schema
        capabilities = provider.capabilities()

        response_format = None
        if schema_to_use and capabilities.supports_json_schema:
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "DocumentBundle",
                    "schema": schema_to_use,
                    "strict": True
                }
            }
        elif capabilities.supports_plain_json:
            response_format = {"type": "json_object"}

        prompt_packet = PromptPacket(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=model,
            temperature=0.2,
            response_format=response_format
        )

        # Call provider
        response = await provider.generate(prompt_packet)

        # Extract JSON from response
        bundle = self._extract_json(response.content)

        # Validate
        is_valid, errors = self.validation_service.validate(bundle)

        # If invalid, attempt repair
        if not is_valid:
            bundle = repair_bundle(bundle)

            # Validate again after repair
            is_valid, errors = self.validation_service.validate(bundle)

            if not is_valid:
                # Still invalid, but return repaired version
                # Caller can decide what to do
                pass

        return bundle

    def _extract_json(self, content: str) -> Dict[str, Any]:
        """Extract JSON from LLM response, handling markdown code blocks"""

        # Try direct parse first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code block
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find largest JSON object
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Fallback: return minimal valid bundle
        return {"drafts": []}
