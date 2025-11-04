"""Test schema validation for updated models."""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.outputs import ProjectBriefOutput, Scope, Deliverable, Milestone, BillingPart, Risk


def test_project_brief_with_new_format():
    """Test project brief with new detailed format."""
    print("=" * 80)
    print("TESTING PROJECT BRIEF WITH NEW FORMAT")
    print("=" * 80)
    
    # Sample data matching what the AI generates
    data = {
        "title": "E-commerce Platform Development",
        "objective": "Build a modern e-commerce platform",
        "scope": {
            "in_scope": [
                "UI/UX design",
                "Frontend development",
                "Backend API"
            ],
            "out_of_scope": [
                "Content creation",
                "Marketing"
            ],
            "assumptions": [
                "Client provides product data"
            ],
            "dependencies": [
                "Third-party payment gateway"
            ]
        },
        "deliverables": [
            {
                "name": "Design Mockups",
                "description": "Complete UI/UX designs",
                "format": "Figma files",
                "acceptance_criteria": "Approved by stakeholder"
            }
        ],
        "milestones": [
            {
                "name": "Design Approval",
                "description": "UI/UX designs approved",
                "days_from_start": 15,
                "dependencies": []
            }
        ],
        "timeline_days": 60,
        "billing_plan": [
            {
                "milestone": "Project Kickoff",
                "percentage": 30,
                "description": "Advance payment"
            },
            {
                "milestone": "Go-Live",
                "percentage": 70,
                "description": "Final payment"
            }
        ],
        "risks": [
            {
                "description": "Delay in content provision",
                "impact": "Medium",
                "probability": "High",
                "mitigation": "Allocate buffer time in schedule"
            }
        ],
        "commercial_terms": {
            "payment_terms": "As per billing plan",
            "payment_methods": "Bank transfer, UPI",
            "ip_rights": "All deliverables become client property"
        }
    }
    
    try:
        # Validate using Pydantic model
        brief = ProjectBriefOutput.model_validate(data, strict=False)
        
        print("\n✅ Validation PASSED!")
        print(f"\n📋 Project Brief:")
        print(f"   Title: {brief.title}")
        print(f"   Timeline: {brief.timeline_days} days")
        print(f"   Scope type: {type(brief.scope).__name__}")
        print(f"   Deliverables type: {type(brief.deliverables).__name__}")
        print(f"   Risks type: {type(brief.risks).__name__}")
        
        if isinstance(brief.scope, Scope):
            print(f"   In-scope items: {len(brief.scope.in_scope)}")
            print(f"   Out-of-scope items: {len(brief.scope.out_of_scope)}")
        
        if isinstance(brief.deliverables, list) and len(brief.deliverables) > 0:
            if isinstance(brief.deliverables[0], Deliverable):
                print(f"   Deliverables: {len(brief.deliverables)} detailed items")
        
        if isinstance(brief.risks, list) and len(brief.risks) > 0:
            if isinstance(brief.risks[0], Risk):
                print(f"   Risks: {len(brief.risks)} detailed risk assessments")
        
        print(f"   Billing plan total: {sum(bp.percentage for bp in brief.billing_plan)}%")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Validation FAILED!")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_project_brief_with_legacy_format():
    """Test project brief with legacy simple format."""
    print("\n" + "=" * 80)
    print("TESTING PROJECT BRIEF WITH LEGACY FORMAT")
    print("=" * 80)
    
    # Sample data in old format (arrays of strings)
    data = {
        "title": "Website Development",
        "objective": "Build a website",
        "scope": [
            "Design",
            "Development",
            "Testing"
        ],
        "deliverables": [
            "Website design",
            "Developed website",
            "Documentation"
        ],
        "milestones": [
            {
                "name": "Design Complete",
                "days_from_start": 10
            }
        ],
        "timeline_days": 30,
        "billing_plan": [
            {
                "milestone": "Start",
                "percentage": 50
            },
            {
                "milestone": "End",
                "percentage": 50
            }
        ],
        "risks": [
            "Delay in approvals",
            "Technical challenges"
        ]
    }
    
    try:
        # Validate using Pydantic model
        brief = ProjectBriefOutput.model_validate(data, strict=False)
        
        print("\n✅ Validation PASSED!")
        print(f"\n📋 Project Brief:")
        print(f"   Title: {brief.title}")
        print(f"   Timeline: {brief.timeline_days} days")
        print(f"   Scope type: {type(brief.scope).__name__}")
        print(f"   Deliverables type: {type(brief.deliverables).__name__}")
        print(f"   Risks type: {type(brief.risks).__name__}")
        
        if isinstance(brief.scope, list):
            print(f"   Scope items: {len(brief.scope)}")
        
        if isinstance(brief.deliverables, list):
            print(f"   Deliverables: {len(brief.deliverables)}")
        
        if isinstance(brief.risks, list):
            print(f"   Risks: {len(brief.risks)}")
        
        print(f"   Billing plan total: {sum(bp.percentage for bp in brief.billing_plan)}%")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Validation FAILED!")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n🧪 TESTING UPDATED SCHEMA VALIDATION")
    print("=" * 80)
    print("This script verifies that the updated models support both new and legacy formats.")
    print("=" * 80)
    
    results = []
    
    # Test new format
    results.append(test_project_brief_with_new_format())
    
    # Test legacy format
    results.append(test_project_brief_with_legacy_format())
    
    print("\n" + "=" * 80)
    if all(results):
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)
        print("\n✅ Summary:")
        print("   - New detailed format: ✅ WORKING")
        print("   - Legacy simple format: ✅ WORKING")
        print("   - Backward compatibility: ✅ MAINTAINED")
        print("\n🚀 The updated models support both formats!")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())

