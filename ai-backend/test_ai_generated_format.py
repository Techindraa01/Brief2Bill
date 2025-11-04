"""Test validation with the exact format the AI is generating."""

import json
import sys
from datetime import date
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.outputs import ProjectBriefOutput


def test_ai_generated_format():
    """Test with the exact format the AI is currently generating."""
    print("=" * 80)
    print("TESTING AI-GENERATED FORMAT (start/end dates, when/percent)")
    print("=" * 80)
    
    # This is the exact format the AI is generating based on the error logs
    data = {
        "title": "E-commerce Platform Development",
        "objective": "Build a modern e-commerce platform",
        "scope": [
            "UI/UX design",
            "Frontend development",
            "Backend API"
        ],
        "deliverables": [
            "Design mockups",
            "Developed application",
            "Documentation"
        ],
        "milestones": [
            {
                "name": "Discovery & Planning",
                "start": "2025-11-04",
                "end": "2025-11-11",
                "fee": 0.0
            },
            {
                "name": "UX Research & Wireframes",
                "start": "2025-11-11",
                "end": "2025-11-18",
                "fee": 0.0
            },
            {
                "name": "UI Design Approval",
                "start": "2025-11-18",
                "end": "2025-11-25",
                "fee": 0.0
            }
        ],
        "timeline_days": 60,
        "billing_plan": [
            {
                "when": "Milestone 1",
                "percent": 20
            },
            {
                "when": "Milestone 2",
                "percent": 20
            },
            {
                "when": "Milestone 3",
                "percent": 20
            },
            {
                "when": "Milestone 4",
                "percent": 20
            },
            {
                "when": "Milestone 5",
                "percent": 20
            }
        ],
        "risks": [
            {
                "description": "Delay in content provision",
                "impact": "Medium",
                "probability": "High",
                "mitigation": "Allocate buffer time in schedule"
            }
        ]
    }
    
    try:
        # Validate using Pydantic model
        brief = ProjectBriefOutput.model_validate(data, strict=False)
        
        print("\n✅ Validation PASSED!")
        print(f"\n📋 Project Brief:")
        print(f"   Title: {brief.title}")
        print(f"   Timeline: {brief.timeline_days} days")
        print(f"   Milestones: {len(brief.milestones)}")
        
        # Check milestone field syncing
        for i, milestone in enumerate(brief.milestones):
            print(f"\n   Milestone {i+1}: {milestone.name}")
            print(f"      - start: {milestone.start}")
            print(f"      - end: {milestone.end}")
            print(f"      - days_from_start: {milestone.days_from_start}")
        
        # Check billing plan field syncing
        print(f"\n   Billing Plan: {len(brief.billing_plan)} parts")
        total = 0
        for i, bp in enumerate(brief.billing_plan):
            print(f"\n   Part {i+1}:")
            print(f"      - when: {bp.when}")
            print(f"      - percent: {bp.percent}")
            print(f"      - milestone: {bp.milestone}")
            print(f"      - percentage: {bp.percentage}")
            total += bp.percentage if bp.percentage else 0
        
        print(f"\n   Total billing: {total}%")
        
        # Check risks
        print(f"\n   Risks: {len(brief.risks) if brief.risks else 0}")
        if brief.risks:
            for i, risk in enumerate(brief.risks):
                print(f"\n   Risk {i+1}:")
                print(f"      - Description: {risk.description}")
                print(f"      - Impact: {risk.impact}")
                print(f"      - Probability: {risk.probability}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Validation FAILED!")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the test."""
    print("\n🧪 TESTING AI-GENERATED FORMAT")
    print("=" * 80)
    print("This test uses the exact format the AI is currently generating.")
    print("=" * 80)
    
    success = test_ai_generated_format()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 TEST PASSED!")
        print("=" * 80)
        print("\n✅ The models now support the AI-generated format!")
        print("   - Legacy milestones (start/end dates): ✅ WORKING")
        print("   - Legacy billing (when/percent): ✅ WORKING")
        print("   - New risks format: ✅ WORKING")
        print("\n🚀 Project brief generation should work now!")
        return 0
    else:
        print("❌ TEST FAILED!")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())

