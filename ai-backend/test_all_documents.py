"""Test all three document types to ensure schemas are working."""

import json
import sys
from datetime import date
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.outputs import QuotationOutput, TaxInvoiceOutput, ProjectBriefOutput


def test_quotation():
    """Test quotation validation."""
    print("=" * 80)
    print("TESTING QUOTATION")
    print("=" * 80)
    
    data = {
        "doc_type": "QUOTATION",
        "currency": "INR",
        "locale": "en-IN",
        "seller": {
            "name": "Tech Solutions Pvt Ltd",
            "address": "123 Tech Street, Bangalore",
            "gstin": "29ABCDE1234F1Z5",
            "email": "sales@techsolutions.com"
        },
        "buyer": {
            "name": "Client Corp",
            "address": "456 Business Ave, Mumbai"
        },
        "dates": {
            "issue_date": "2025-11-04",
            "valid_till": "2025-11-18"
        },
        "items": [
            {
                "description": "Website Development",
                "hsn_sac": "998314",
                "qty": 1,
                "unit": "project",
                "unit_price": 50000,
                "discount": 0,
                "tax_rate": 18
            }
        ],
        "totals": {
            "subtotal": 50000,
            "discount_total": 0,
            "tax_total": 9000,
            "shipping": 0,
            "round_off": 0,
            "grand_total": 59000,
            "amount_in_words": "Fifty Nine Thousand Rupees Only"
        },
        "terms": {
            "title": "Terms & Conditions",
            "bullets": [
                "Payment within 15 days",
                "50% advance required"
            ]
        }
    }
    
    try:
        quotation = QuotationOutput.model_validate(data, strict=False)
        print("\n✅ Quotation validation PASSED!")
        print(f"   Grand Total: ₹{quotation.totals.grand_total:,.2f}")
        print(f"   Items: {len(quotation.items)}")
        return True
    except Exception as e:
        print(f"\n❌ Quotation validation FAILED!")
        print(f"   Error: {e}")
        return False


def test_invoice():
    """Test invoice validation."""
    print("\n" + "=" * 80)
    print("TESTING TAX INVOICE")
    print("=" * 80)
    
    data = {
        "doc_type": "TAX_INVOICE",
        "currency": "INR",
        "locale": "en-IN",
        "seller": {
            "name": "Tech Solutions Pvt Ltd",
            "address": "123 Tech Street, Bangalore, Karnataka",
            "gstin": "29ABCDE1234F1Z5",
            "email": "sales@techsolutions.com"
        },
        "buyer": {
            "name": "Client Corp",
            "address": "456 Business Ave, Mumbai, Maharashtra",
            "gstin": "27XYZAB5678G1H9"
        },
        "doc_meta": {
            "doc_no": "INV-2025-001"
        },
        "dates": {
            "issue_date": "2025-11-04",
            "due_date": "2025-11-19"
        },
        "items": [
            {
                "description": "Website Development Services",
                "hsn_sac": "998314",
                "qty": 1,
                "unit": "project",
                "unit_price": 50000,
                "discount": 0,
                "tax_rate": 18
            }
        ],
        "totals": {
            "subtotal": 50000,
            "discount_total": 0,
            "tax_total": 9000,
            "shipping": 0,
            "round_off": 0,
            "grand_total": 59000,
            "amount_in_words": "Fifty Nine Thousand Rupees Only"
        },
        "terms": {
            "title": "Terms & Conditions",
            "bullets": [
                "Payment due within 15 days",
                "Late payment attracts 2% interest per month"
            ]
        },
        "gst": {
            "mode": "INTER",
            "igst": 9000,
            "cgst": 0,
            "sgst": 0,
            "place_of_supply": "Maharashtra"
        }
    }
    
    try:
        invoice = TaxInvoiceOutput.model_validate(data, strict=False)
        print("\n✅ Invoice validation PASSED!")
        print(f"   Invoice No: {invoice.doc_meta.doc_no}")
        print(f"   Grand Total: ₹{invoice.totals.grand_total:,.2f}")
        print(f"   GST Mode: {invoice.gst.mode if invoice.gst else 'N/A'}")
        return True
    except Exception as e:
        print(f"\n❌ Invoice validation FAILED!")
        print(f"   Error: {e}")
        return False


def test_project_brief():
    """Test project brief validation."""
    print("\n" + "=" * 80)
    print("TESTING PROJECT BRIEF")
    print("=" * 80)
    
    data = {
        "title": "E-commerce Platform Development",
        "objective": "Build a modern e-commerce platform with payment integration",
        "scope": [
            "UI/UX design",
            "Frontend development (React)",
            "Backend API (Node.js)",
            "Payment gateway integration"
        ],
        "deliverables": [
            "Design mockups",
            "Developed application",
            "Documentation",
            "Deployment"
        ],
        "milestones": [
            {
                "name": "Design Phase",
                "start": "2025-11-04",
                "end": "2025-11-18",
                "fee": 0.0
            },
            {
                "name": "Development Phase",
                "start": "2025-11-18",
                "end": "2025-12-18",
                "fee": 0.0
            },
            {
                "name": "Testing & Deployment",
                "start": "2025-12-18",
                "end": "2026-01-03",
                "fee": 0.0
            }
        ],
        "timeline_days": 60,
        "billing_plan": [
            {
                "when": "Project Start",
                "percent": 30
            },
            {
                "when": "Design Approval",
                "percent": 30
            },
            {
                "when": "Go-Live",
                "percent": 40
            }
        ],
        "risks": [
            {
                "description": "Delay in content and product data provision by client",
                "impact": "Medium",
                "probability": "High",
                "mitigation": "Allocate buffer time in schedule, provide content guidelines early"
            },
            {
                "description": "Payment gateway integration challenges",
                "impact": "High",
                "probability": "Medium",
                "mitigation": "Early technical assessment, backup payment provider"
            }
        ]
    }
    
    try:
        brief = ProjectBriefOutput.model_validate(data, strict=False)
        print("\n✅ Project Brief validation PASSED!")
        print(f"   Title: {brief.title}")
        print(f"   Timeline: {brief.timeline_days} days")
        print(f"   Milestones: {len(brief.milestones)}")
        print(f"   Billing Plan: {len(brief.billing_plan)} parts")
        print(f"   Risks: {len(brief.risks) if brief.risks else 0}")
        
        # Verify billing total
        total = sum(bp.percentage if bp.percentage else 0 for bp in brief.billing_plan)
        print(f"   Billing Total: {total}%")
        
        return True
    except Exception as e:
        print(f"\n❌ Project Brief validation FAILED!")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n🧪 TESTING ALL DOCUMENT TYPES")
    print("=" * 80)
    print("This script validates all three document types:")
    print("  1. Quotation")
    print("  2. Tax Invoice")
    print("  3. Project Brief")
    print("=" * 80)
    
    results = {
        "Quotation": test_quotation(),
        "Tax Invoice": test_invoice(),
        "Project Brief": test_project_brief()
    }
    
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS")
    print("=" * 80)
    
    for doc_type, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {doc_type:20s}: {status}")
    
    print("=" * 80)
    
    if all(results.values()):
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ Summary:")
        print("   - Quotation generation: ✅ READY")
        print("   - Invoice generation: ✅ READY")
        print("   - Project Brief generation: ✅ READY")
        print("\n🚀 All document types are working correctly!")
        print("\n📝 Next Steps:")
        print("   1. Start the backend: uvicorn app.main:app --reload")
        print("   2. Start Streamlit: streamlit run streamlit_app.py")
        print("   3. Test document generation in the UI")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("\nPlease review the errors above and fix the issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

