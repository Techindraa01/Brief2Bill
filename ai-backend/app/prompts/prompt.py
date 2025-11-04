"""Prompt builders for dedicated generation endpoints."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Tuple

from ..models.generation import GenerationRequest

_SYSTEM_PROMPT = """You are an expert commercial document drafter specializing in Indian business documentation with deep knowledge of GST regulations, commercial practices, and legal requirements for Indian SMEs.

Your role is to generate professional, accurate, and legally compliant documents including quotations, tax invoices, and project briefs.

CRITICAL GUIDELINES:
1. Output STRICT JSON matching the provided JSON Schema. No markdown, no comments, no extra keys, no explanations.
2. Follow Indian GST regulations and business practices:
   - For quotations: Set valid_till = issue_date + 14 to 15 days
   - For invoices: Set due_date = issue_date + 7 days unless specified otherwise
   - Apply appropriate GST rates based on HSN/SAC codes:
     * Services (HSN 99xxxx): Typically 18%
     * Products: 0%, 5%, 12%, 18%, or 28% based on category
   - For intra-state supply (same state): Show CGST and SGST separately (each = GST rate ÷ 2)
   - For inter-state supply (different states): Show IGST only (= full GST rate)
3. Use conservative, realistic defaults when information is ambiguous:
   - Default GST rate: 18% for services, 28% for products
   - Default payment terms: 50% advance, 50% on completion
   - Default project timeline: Add 20% buffer to estimated duration
4. Ensure all financial calculations are mathematically accurate:
   - Subtotal = sum of (quantity × unit_price) for all line items
   - Discount amount = (subtotal × discount_percentage) ÷ 100
   - Taxable value = subtotal - discount amount
   - GST amount = taxable value × (GST rate ÷ 100)
   - Grand total = taxable value + GST amount
   - Round all amounts to 2 decimal places, final total to nearest rupee
5. Include all required fields for each document type with professional content
6. Use formal, professional business language appropriate for Indian SMEs
7. Ensure all documents are legally compliant and commercially sound
8. Parse requirements intelligently to extract specific line items, quantities, and pricing hints
"""

_QUOTATION_TEMPLATE = """Task: Generate a comprehensive, professional QUOTATION that follows Indian business practices and GST regulations.

INSTRUCTIONS:
1. Parse the requirement description to extract specific services/products with quantities and pricing hints
2. Create detailed line items with:
   - Clear, professional descriptions of each service/product
   - Appropriate HSN/SAC codes (998313-998316 for IT/consulting services, 998311 for software development)
   - Realistic unit prices based on market rates and requirement complexity
   - Quantities as specified or intelligently inferred from requirement
   - Appropriate units (pcs, hours, days, months, lot, job, etc.)
   - GST rates: 18% for services, 28% for products, or as appropriate for the category
   - Discounts if mentioned in hints or requirement
3. Calculate accurate totals:
   - Subtotal: Sum of (quantity × unit_price) for all line items
   - Discount: Apply if specified in hints
   - Taxable value: Subtotal - discount
   - GST breakup: CGST + SGST (for intra-state) OR IGST (for inter-state)
   - Grand total: Taxable value + total GST
   - Amount in words: Professional format (e.g., "Forty Eight Thousand Three Hundred Eighty Rupees Only")
4. Include professional terms and conditions:
   - Payment terms (e.g., "50% advance on order confirmation, 50% on delivery")
   - Validity period: 14-15 days from issue date
   - Delivery/completion timeline based on requirement complexity
   - Cancellation policy (e.g., "Cancellation charges apply after advance payment")
   - Warranty/guarantee terms if applicable
   - Scope of work clearly defined
5. Create clear payment instructions:
   - Payment modes accepted (UPI, Bank Transfer, etc.)
   - UPI deeplink if UPI ID is provided in seller bank details
   - Bank account details if provided
6. Set appropriate dates:
   - issue_date: Use from hints or current date
   - valid_till: issue_date + 14 to 15 days
7. Use professional, formal business language throughout

INPUTS:
- Seller (FROM): {from_json}
- Buyer (TO): {to_json}
- Currency: {currency}
- Locale: {locale}
- Hints: {hints_json}
- Requirement: {requirement_text}

EXAMPLE LINE ITEM STRUCTURE:
{{
  "description": "5-page responsive website development with modern UI/UX design, mobile optimization, and SEO-friendly structure",
  "qty": 5,
  "unit_price": 8000.00,
  "unit": "pages",
  "discount": 0,
  "tax_rate": 18,
  "hsn_sac": "998314"
}}

Return a single JSON object strictly obeying quotation_output.schema.json. No markdown, no explanations, only valid JSON.
"""

_INVOICE_TEMPLATE = """Task: Generate a GST-compliant TAX INVOICE that meets all legal requirements for Indian businesses under GST regulations.

INSTRUCTIONS:
1. Parse the requirement to extract taxable supplies/services that have been delivered or completed
2. Create detailed line items with MANDATORY GST compliance:
   - Clear descriptions of goods/services supplied
   - CORRECT HSN/SAC codes (MANDATORY for GST compliance):
     * Services: 998313 (IT consulting), 998314 (software development), 998316 (maintenance)
     * Products: Use appropriate 6-8 digit HSN codes
   - Quantities and appropriate units
   - Unit prices excluding GST
   - Line-wise totals (quantity × unit_price)
   - Appropriate GST rates based on HSN/SAC:
     * 0% for exempt supplies
     * 5%, 12%, 18%, 28% as per GST schedule
   - Taxable value for each line item
3. Calculate ACCURATE GST breakup (CRITICAL for compliance):
   - Determine if supply is intra-state or inter-state:
     * Intra-state (seller and buyer in same state): CGST + SGST
       - CGST = (Taxable value × GST rate) ÷ 2
       - SGST = (Taxable value × GST rate) ÷ 2
       - IGST = 0
     * Inter-state (seller and buyer in different states): IGST only
       - IGST = Taxable value × GST rate
       - CGST = 0
       - SGST = 0
   - For exempt supplies (0% GST): All GST amounts = 0
4. Calculate accurate totals with proper rounding:
   - Taxable value: Sum of all line item totals (before GST)
   - Total CGST: Sum of CGST for all items
   - Total SGST: Sum of SGST for all items
   - Total IGST: Sum of IGST for all items
   - Total GST: CGST + SGST + IGST
   - Grand total: Taxable value + Total GST
   - Round to 2 decimal places, final total to nearest rupee
   - Amount in words: Professional format
5. Set appropriate dates:
   - issue_date: Use from hints or current date
   - due_date: issue_date + 7 days (or as specified in payment terms)
6. Include MANDATORY GST declarations:
   - "This is a computer-generated invoice and does not require signature"
   - "Subject to [City] jurisdiction" (seller's city)
   - If reverse charge applicable: "Supply is liable for GST reverse charge - Yes"
   - If not reverse charge: "Supply is liable for GST reverse charge - No"
7. Include professional payment terms:
   - Payment due date clearly stated
   - Late payment charges if applicable (e.g., "1.5% per month after due date")
   - Accepted payment modes (Bank Transfer, UPI, Cheque, etc.)
   - Bank account details from seller information
   - UPI deeplink if UPI ID provided
8. Add invoice-specific details:
   - Invoice number from hints (doc_no)
   - PO number if provided in hints
   - Reference number if provided
   - Place of supply (buyer's state)
   - Tax preferences from seller (reverse charge, e-invoice status)

INPUTS:
- Seller (FROM): {from_json}
- Buyer (TO): {to_json}
- Currency: {currency}
- Locale: {locale}
- Hints: {hints_json}
- Requirement: {requirement_text}

EXAMPLE GST CALCULATION:
For intra-state supply (Gujarat to Gujarat) with 18% GST on ₹10,000:
- Taxable value: ₹10,000
- CGST @ 9%: ₹900
- SGST @ 9%: ₹900
- IGST: ₹0
- Total GST: ₹1,800
- Grand total: ₹11,800

For inter-state supply (Gujarat to Maharashtra) with 18% GST on ₹10,000:
- Taxable value: ₹10,000
- CGST: ₹0
- SGST: ₹0
- IGST @ 18%: ₹1,800
- Total GST: ₹1,800
- Grand total: ₹11,800

Return a single JSON object strictly obeying tax_invoice_output.schema.json. No markdown, no explanations, only valid JSON.
"""

_PROJECT_TEMPLATE = """Task: Generate a comprehensive PROJECT BRIEF that clearly outlines scope, deliverables, timeline, commercial terms, and risk management for a professional services engagement.

INSTRUCTIONS:
1. Create a compelling, professional project title based on the requirement (e.g., "E-commerce Platform Development and Deployment")

2. Define clear, measurable project objectives:
   - What the project aims to achieve
   - Expected business outcomes
   - Success criteria
   - Alignment with client's business goals

3. Develop detailed scope of work:
   - IN-SCOPE: List all activities, deliverables, and services included
     * Be specific and comprehensive
     * Include technical specifications
     * Define boundaries clearly
   - OUT-OF-SCOPE: Explicitly list what is NOT included
     * Prevent scope creep
     * Set clear expectations
     * Identify potential add-ons
   - ASSUMPTIONS: List key assumptions the project is based on
     * Client responsibilities
     * Resource availability
     * Technical prerequisites
   - DEPENDENCIES: Identify external dependencies
     * Third-party services
     * Client inputs
     * Infrastructure requirements

4. Define specific, measurable deliverables:
   - Clear description of each deliverable
   - Format and specifications (e.g., "Figma design files", "React codebase")
   - Acceptance criteria for each deliverable
   - Quality standards to be met
   - Documentation requirements

5. Create realistic milestones with dependencies:
   - Milestone name and description
   - Target completion in days from project start
   - Dependencies on other milestones
   - Key activities in each milestone
   - Review/approval points
   - Example: "Design Approval" at day 15, depends on "Requirements Finalization"

6. Develop a structured billing plan that totals exactly 100%:
   - Link payments to specific milestones or deliverables
   - Percentage of total project value for each payment
   - Payment conditions (e.g., "Upon approval of designs")
   - Typical structure:
     * 20-30% advance on project commencement
     * 30-40% on mid-project milestone
     * 20-30% on delivery
     * 10-20% on final acceptance/go-live
   - MUST total exactly 100%

7. Identify and assess potential risks:
   - Risk description (what could go wrong)
   - Impact assessment: High/Medium/Low
     * High: Could derail project or cause major delays
     * Medium: Could cause delays or quality issues
     * Low: Minor inconvenience
   - Probability assessment: High/Medium/Low
     * High: Likely to occur
     * Medium: May occur
     * Low: Unlikely to occur
   - Mitigation strategies (how to prevent or minimize)
   - Common risks: Scope creep, resource unavailability, technical challenges, client delays

8. Set realistic timeline:
   - Total project duration in days
   - Account for:
     * Complexity of requirements
     * Number of deliverables
     * Review and approval cycles
     * Testing and quality assurance
     * Buffer time (add 20% for contingencies)
   - Break down into phases if project > 60 days

9. Include commercial terms:
   - Payment terms and schedule
   - Payment methods accepted
   - Change request process and pricing
   - Termination clauses
   - Intellectual property rights
   - Confidentiality requirements
   - Warranty and support terms

10. Use professional project management language throughout

INPUTS:
- Service Provider (FROM): {from_json}
- Client (TO): {to_json}
- Currency: {currency}
- Locale: {locale}
- Hints: {hints_json}
- Requirement: {requirement_text}

EXAMPLE STRUCTURE:
{{
  "title": "E-commerce Website Redesign and Development Project",
  "objective": "To redesign and develop a modern, responsive e-commerce website for Indigo Retail with improved user experience, mobile optimization, and conversion rate optimization to increase online sales by 30%",
  "scope": {{
    "in_scope": [
      "UI/UX design for 5 main pages (Home, Product Listing, Product Detail, Cart, Checkout)",
      "Responsive frontend development using React.js",
      "Payment gateway integration (Razorpay)",
      "Product catalog setup and migration",
      "SEO optimization and meta tags",
      "3 months post-launch support"
    ],
    "out_of_scope": [
      "Content creation and copywriting",
      "Product photography",
      "Digital marketing and advertising",
      "Ongoing maintenance beyond 3 months",
      "Custom ERP integration"
    ],
    "assumptions": [
      "Client will provide product data in agreed format",
      "Client has necessary licenses for third-party tools",
      "Timely feedback and approvals from client stakeholders"
    ],
    "dependencies": [
      "Access to existing website and hosting",
      "Razorpay merchant account setup by client",
      "Brand guidelines and assets from client"
    ]
  }},
  "deliverables": [
    {{
      "name": "UI/UX Design Mockups",
      "description": "Complete design mockups for all 5 pages with responsive layouts for desktop, tablet, and mobile",
      "format": "Figma files with design system and component library",
      "acceptance_criteria": "Approved by client stakeholder with sign-off"
    }},
    {{
      "name": "Developed Website",
      "description": "Fully functional e-commerce website with all features implemented",
      "format": "React.js codebase deployed on client's hosting",
      "acceptance_criteria": "All features working as per specifications, passed UAT"
    }}
  ],
  "milestones": [
    {{
      "name": "Requirements Finalization",
      "description": "Complete requirements gathering and documentation",
      "days_from_start": 7,
      "dependencies": []
    }},
    {{
      "name": "Design Approval",
      "description": "UI/UX designs approved by client",
      "days_from_start": 21,
      "dependencies": ["Requirements Finalization"]
    }},
    {{
      "name": "Development Complete",
      "description": "All features developed and ready for testing",
      "days_from_start": 50,
      "dependencies": ["Design Approval"]
    }},
    {{
      "name": "Go-Live",
      "description": "Website deployed to production and live",
      "days_from_start": 60,
      "dependencies": ["Development Complete"]
    }}
  ],
  "billing_plan": [
    {{
      "milestone": "Project Kickoff",
      "percentage": 30,
      "description": "Advance payment on project commencement and contract signing"
    }},
    {{
      "milestone": "Design Approval",
      "percentage": 30,
      "description": "Payment on approval of UI/UX designs"
    }},
    {{
      "milestone": "Development Complete",
      "percentage": 25,
      "description": "Payment on completion of development and successful UAT"
    }},
    {{
      "milestone": "Go-Live",
      "percentage": 15,
      "description": "Final payment on successful deployment and go-live"
    }}
  ],
  "risks": [
    {{
      "description": "Delay in content and product data provision by client",
      "impact": "Medium",
      "probability": "High",
      "mitigation": "Allocate buffer time, provide content guidelines early, set clear deadlines for client inputs"
    }},
    {{
      "description": "Technical challenges with payment gateway integration",
      "impact": "High",
      "probability": "Low",
      "mitigation": "Early technical assessment, sandbox testing, fallback payment options"
    }},
    {{
      "description": "Scope creep due to additional feature requests",
      "impact": "High",
      "probability": "Medium",
      "mitigation": "Clear scope documentation, change request process with additional cost estimation"
    }}
  ],
  "timeline_days": 60,
  "commercial_terms": {{
    "payment_terms": "As per billing plan linked to milestones",
    "payment_methods": "Bank transfer, UPI, or cheque",
    "change_requests": "Additional features will be quoted separately and may impact timeline",
    "ip_rights": "All deliverables become client property upon full payment",
    "warranty": "3 months bug-fix warranty post go-live"
  }}
}}

Return a single JSON object strictly obeying project_brief_output.schema.json. No markdown, no explanations, only valid JSON.
"""

_SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas" / "outputs"


def _load_schema(filename: str) -> Dict[str, Any]:
    with (_SCHEMA_DIR / filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _json_dump(data: Any) -> str:
    """Serialize data to JSON, handling date/datetime objects."""

    def default_serializer(obj: Any) -> str:
        """Custom serializer for non-JSON-serializable objects."""
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    return json.dumps(data, ensure_ascii=False, sort_keys=True, default=default_serializer)


def build_quotation_prompt(request: GenerationRequest) -> Tuple[str, str, Dict[str, Any]]:
    schema = _load_schema("quotation_output.schema.json")
    hints = request.hints.model_dump(exclude_none=True) if request.hints else {}
    user = _QUOTATION_TEMPLATE.format(
        from_json=_json_dump(request.seller.model_dump(exclude_none=True)),
        to_json=_json_dump(request.buyer.model_dump(exclude_none=True)),
        currency=request.currency,
        locale=request.locale,
        hints_json=_json_dump(hints),
        requirement_text=request.requirement,
    )
    return _SYSTEM_PROMPT, user, schema


def build_invoice_prompt(request: GenerationRequest) -> Tuple[str, str, Dict[str, Any]]:
    schema = _load_schema("tax_invoice_output.schema.json")
    hints = request.hints.model_dump(exclude_none=True) if request.hints else {}
    user = _INVOICE_TEMPLATE.format(
        from_json=_json_dump(request.seller.model_dump(exclude_none=True)),
        to_json=_json_dump(request.buyer.model_dump(exclude_none=True)),
        currency=request.currency,
        locale=request.locale,
        hints_json=_json_dump(hints),
        requirement_text=request.requirement,
    )
    return _SYSTEM_PROMPT, user, schema


def build_project_brief_prompt(request: GenerationRequest) -> Tuple[str, str, Dict[str, Any]]:
    schema = _load_schema("project_brief_output.schema.json")
    hints = request.hints.model_dump(exclude_none=True) if request.hints else {}
    user = _PROJECT_TEMPLATE.format(
        from_json=_json_dump(request.seller.model_dump(exclude_none=True)),
        to_json=_json_dump(request.buyer.model_dump(exclude_none=True)),
        currency=request.currency,
        locale=request.locale,
        hints_json=_json_dump(hints),
        requirement_text=request.requirement,
    )
    return _SYSTEM_PROMPT, user, schema
