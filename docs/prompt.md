Brief2Bill Backend — Provider-Agnostic, Schema-First, LangChain-Ready
Implement a FastAPI backend that:


Converts messy requirements into strict JSON documents: Quotation, Tax Invoice, Project Brief


Supports provider selection and model switching at runtime: openrouter, groq, openai, gemini


Enforces structured output (LangChain v1 “Structured output” and native provider JSON modes), with robust server-side validation and repair


Generates UPI deeplinks and optional QR payloads


Exposes a clean REST surface with stable error envelopes, JSON logging, and rate limiting


This is a Python project. Everything happens inside a virtual environment. Never pin versions. Always check venv before running anything.

0) Non-negotiable runtime rules


Before any pip install or run, check that venv is active; if not, activate:


Windows: venv\Scripts\activate


POSIX: source venv/bin/activate




Install libraries by name only: fastapi, uvicorn[standard], pydantic, pydantic-settings, httpx, orjson, jsonschema, structlog, slowapi, redis, google-generativeai, langchain, langchain-openai, langchain-google-genai, langchain_groq (name may appear as langchain-groq), langchain-community


Start server with:
python -m uvicorn main:app --reload



Use structured JSON logging with request IDs and latency. All errors return the standard error envelope. No stack traces to clients.



1) Project layout (the scaffold already exists; fill it in)


main.py (root): thin shim exporting app = create_app()


app/main.py: app factory; mount router; register middleware/handlers


app/api/v1/: router.py, health.py, version.py, providers.py, draft.py, validate.py, repair.py, totals.py, upi.py, deps.py, errors.py, middleware.py


app/core/: config.py, logging.py, rate_limit.py, security.py, lifecycles.py


app/models/: document_models.py (Pydantic v2)


app/schemas/: document_bundle.schema.json (JSON Schema, source of truth for tool/LLM)


app/services/: drafting_service.py, validation.py, repair.py, totals.py, upi.py, provider_service.py


app/providers/: base.py, openai.py, openrouter.py, groq.py, gemini.py


app/adapters/: http.py, cache.py, queue.py (lightweight, mostly stubs now)


app/utils/: json_tools.py, time.py, ids.py


tests/: test_health.py, test_providers.py, test_draft_e2e.py, fixtures/


If any file is missing, create it.

2) Config and environment


Support these env vars:


DEFAULT_PROVIDER in {"openrouter","groq","openai","gemini"}


DEFAULT_MODEL string


OPENAI_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY, GEMINI_API_KEY or GOOGLE_API_KEY


RATE_LIMIT_PER_MIN (default 5)


APP_ENV, LOG_LEVEL



app/core/config.py uses pydantic-settings.


app/core/logging.py sets JSON logs via structlog.


app/core/lifecycles.py wires httpx client(s), optional Redis for rate-limit/cache.



3) HTTP surface (routes and schemas)
Return JSON only. Standard error envelope:
{
  "error": {
    "code": "STRING_ENUM",
    "message": "human-readable summary",
    "request_id": "uuid",
    "details": {}
  }
}


Headers accepted on all mutation/read routes:


X-Provider: openrouter|groq|openai|gemini (override)


X-Model: <model-id> (override)


X-Workspace-Id: <string> (scopes selection; default “default”)


X-Request-Id: <uuid> (generate if absent)


GET /v1/healthz


200: {"ok": true, "version": "1.0.0"}


GET /v1/version


200: {"name":"ai-draft-backend","version":"1.0.0","default_provider":"openrouter","default_model":"openrouter/auto"}


GET /v1/providers


Returns enabled providers and advisory model list (per available keys).


Response schema:


{
  "providers":[
    {
      "name":"openrouter","enabled":true,
      "models":[{"id":"openai/gpt-4o","family":"gpt","supports_json_schema":true}]
    }
  ]
}


POST /v1/providers/select


Body:


{"provider":"groq","model":"llama-3.1-70b","workspace_id":"default"}



200:


{"ok":true,"active":{"provider":"groq","model":"llama-3.1-70b","workspace_id":"default"}}


GET /v1/providers/active?workspace_id=default


200:


{"provider":"groq","model":"llama-3.1-70b","workspace_id":"default"}


POST /v1/draft


Body:


{
  "prompt":"free-text requirement...",
  "prefer":["QUOTATION","PROJECT_BRIEF"],
  "currency":"INR",
  "defaults":{},
  "provider":"openrouter",
  "model":"openai/gpt-4o",
  "workspace_id":"default"
}



200: DocumentBundle JSON (see §Schemas)


Behavior: choose provider/model (override > active > default), perform schema-constrained generation if supported, else JSON-only mode, then validate + repair.


POST /v1/validate


Body: { "bundle": <DocumentBundle> }


200 OK:


{"ok":true,"errors":[]}



Or:


{"ok":false,"errors":[{"path":"/drafts/0/items/0/unit_price","message":"must be number"}]}


POST /v1/repair


Body: { "bundle": { ...anything... } }


200: repaired DocumentBundle


POST /v1/compute/totals


Body: { "draft": <DocDraft> }


200: { "draft": <DocDraft with recomputed totals> }


POST /v1/upi/deeplink


Body:


{"upi_id":"acme@upi","payee_name":"Acme","amount":43660,"currency":"INR","note":"Advance 50%","txn_ref":"INV-2025-0041"}



200:


{"deeplink":"upi://pay?...","qr_payload":"upi://pay?..."}


4) Document schemas (authoritative)


Place full JSON Schema at app/schemas/document_bundle.schema.json. It must define:


Root DocumentBundle with drafts: DocDraft[] and optional project_brief: ProjectBrief


DocDraft with doc_type enum ["QUOTATION","TAX_INVOICE"], seller, buyer, dates (ISO dates), items, totals, terms, optional payment


Numeric money fields as numbers; do not use strings



Pydantic v2 models in app/models/document_models.py must mirror the schema and recompute totals when missing.


If any schema file is missing, create it from the spec already given in earlier messages. Keep enums and required fields identical.

5) Provider abstraction and capabilities
Define app/providers/base.py interface:


generate(prompt_packet: PromptPacket) -> LLMRawResponse


capabilities() -> ProviderCapabilities with flags: json_schema, json_object, tools


list_models() -> list[ModelDescriptor]


Implement:


OpenAI


Base: https://api.openai.com/v1/chat/completions


Auth: Authorization: Bearer ${OPENAI_API_KEY}


Preferred: response_format: {"type":"json_schema","json_schema": <DocumentBundle schema>}


Fallback: response_format: {"type":"json_object"} then validate/repair


LangChain path: langchain_openai.ChatOpenAI with .with_structured_output(DocumentBundle) where feasible; else raw + validation.




OpenRouter


Base: https://openrouter.ai/api/v1/chat/completions


Auth: Authorization: Bearer ${OPENROUTER_API_KEY}


Optional headers: HTTP-Referer, X-Title


Use OpenAI-compatible body. If chosen model supports structured outputs, use it; else JSON-only + validation.


LangChain path: ChatOpenAI with base_url="https://openrouter.ai/api/v1".




Groq


Base: https://api.groq.com/openai/v1/chat/completions


Auth: Authorization: Bearer ${GROQ_API_KEY}


OpenAI-compatible; schema enforcement may be absent. Use JSON-only + validation.


LangChain path: langchain_groq.ChatGroq if available; otherwise OpenAI-compatible client.




Gemini


SDK: google-generativeai (import google.generativeai as genai)


Key: GEMINI_API_KEY or GOOGLE_API_KEY


Use genai.GenerativeModel(model=...) and generate_content with:


generation_config={"response_mime_type":"application/json"}


If supported, set response_schema=<DocumentBundle schema>; else prompt JSON-only then validate/repair



LangChain path: langchain_google_genai.ChatGoogleGenerativeAI with structured output if supported; else raw + validation.




Selection precedence per request:


Body/header override


Active selection per workspace_id (in-memory/Redis)


Defaults from env



6) Prompting and content engineering
System message (use verbatim):
You are an expert commercial-docs drafter for India-focused SMEs.
Output STRICT JSON matching the provided JSON Schema for DocumentBundle.
No markdown, no comments, no extra keys.
Prefer INR context and GST. For quotations set valid_till = issue_date + 14..15 days; for invoices set due_date = issue_date + 7 days unless specified.
Use conservative defaults when ambiguous.


User template:
Requirement:
{{free_text_requirement}}

Preferences:
- doc_types: {{["QUOTATION"] or ["QUOTATION","TAX_INVOICE","PROJECT_BRIEF"]}}
- currency: {{currency or "INR"}}
- seller_defaults: {{JSON or null}}
- buyer_hint: {{text or null}}

Return exactly one JSON object of type DocumentBundle.
Schema name: DocumentBundle


LangChain integration:


Provide a chain that uses with_structured_output(DocumentBundle) when available for OpenAI/OpenRouter; for Groq/Gemini, fall back to PydanticOutputParser or plain JSON + schema validation.


Add few-shot exemplars for line-items shape, terms bullets, and date defaults. Keep temperature ≤ 0.3.



7) Validation, repair, totals, UPI
Validation pipeline (app/services/validation.py):


Try to parse JSON directly


If fails, extract the largest {...} block


Validate against document_bundle.schema.json (jsonschema)


On failure, return structured error list (path, message)



Repair (app/services/repair.py):


Fill required keys with safe defaults


Coerce number strings to numbers


If doc_type == TAX_INVOICE and due_date missing, set issue_date + 7


If doc_type == QUOTATION and valid_till missing, set issue_date + 15


Recompute totals with server math



Totals (app/services/totals.py):


line_total = qty * unit_price - discount


line_tax = line_total * (tax_rate/100)


subtotal = Σ line_total


discount_total = Σ discount


tax_total = Σ line_tax


grand_total = subtotal - discount_total + tax_total + shipping + round_off


round_off = round(grand_total) - grand_total


Provide amount_in_words with Indian grouping (thousand, lakh, crore)



UPI (app/services/upi.py):


Build:
upi://pay?pa={VPA}&pn={Name}&am={Amount}&cu=INR&tn={Note}&tr={TxnRef}&url={CallbackURL}


URL-encode parameters


Return identical string for QR payload



8) Middleware, errors, and rate limit


Add CORS for mobile dev


Request ID middleware; generate UUID if missing


JSON logging: include ts, level, request_id, route, provider, model, latency_ms, status


Exception handlers:


Validation errors → VALIDATION_ERROR envelope


Provider failures/timeouts → PROVIDER_ERROR or TIMEOUT


Unhandled → INTERNAL



Rate limit /v1/draft with SlowAPI token bucket: default 5/min per IP + workspace



9) Tests
Minimal E2E tests in tests/:


test_health.py: /v1/healthz returns 200


test_providers.py: /v1/providers reflects enabled keys


test_draft_e2e.py:


If OPENAI_API_KEY present, call /v1/draft with provider=openai&model=gpt-4o-mini and a short requirement; assert a JSON object with drafts and at least one doc_type.


Validate returned bundle with /v1/validate → ok: true


Call /v1/compute/totals on first draft; assert grand_total is numeric



Tests must run with venv active.

10) Acceptance checks (manual)


Server starts with python -m uvicorn main:app --reload


/v1/healthz returns {"ok": true, ...}


/v1/providers lists providers; enabled set reflects provided keys


/v1/providers/select updates active selection; /v1/providers/active returns it


/v1/draft returns DocumentBundle for a sane requirement


/v1/upi/deeplink returns a valid deeplink string


Logs are JSON; error envelopes are consistent



11) Implementation notes


Don’t pin versions. Install by name only.


Keep providers swappable via provider_service.py and a simple registry.


Prefer native structured outputs where a provider supports JSON Schema or JSON mode; otherwise force JSON-only via prompt and repair server-side.


Do not log PII or raw prompts.



Deliverables: working FastAPI app with the routes and behaviors above, passing the tests, and running under the specified command.



env file:# Example env variables for ai-backend
APP_ENV=development
API_KEY=
OPENAI_API_KEY=
OPENROUTER_API_KEY=
GROQ_API_KEY=
GEMINI_API_KEY=
