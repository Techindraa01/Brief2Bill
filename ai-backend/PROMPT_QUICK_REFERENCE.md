# 🚀 AI Prompt Quick Reference - Brief2Bill

## 📊 Prompt Statistics

| Document Type | System Prompt | User Prompt | Total | Schema |
|--------------|---------------|-------------|-------|--------|
| **Quotation** | 1,997 chars | 3,412 chars | 5,409 chars | ✅ |
| **Invoice** | 1,997 chars | 4,263 chars | 6,260 chars | ✅ |
| **Project Brief** | 1,997 chars | 8,728 chars | 10,725 chars | ✅ |

**Total Enhancement:** 114 lines → 467 lines (4x increase)

---

## 🎯 Key Features by Document Type

### 1. Quotation Prompts

**Focus:** Professional pricing proposals with GST compliance

**Key Instructions:**
- ✅ Parse requirements to extract line items
- ✅ Use HSN/SAC codes (998313-998316 for IT services)
- ✅ Calculate accurate GST (CGST+SGST or IGST)
- ✅ Include professional terms and conditions
- ✅ Generate UPI deeplinks for payment
- ✅ Set validity period (14-15 days)

**Example Output:**
```json
{
  "description": "5-page responsive website development",
  "qty": 5,
  "unit_price": 8000.00,
  "unit": "pages",
  "tax_rate": 18,
  "hsn_sac": "998314"
}
```

---

### 2. Invoice Prompts

**Focus:** GST-compliant tax invoices with accurate calculations

**Key Instructions:**
- ✅ MANDATORY HSN/SAC codes for all items
- ✅ Accurate CGST/SGST/IGST calculation
- ✅ Intra-state vs inter-state determination
- ✅ GST declarations and compliance statements
- ✅ Due date calculation (7 days default)
- ✅ Proper tax breakdowns

**GST Calculation Rules:**

**Intra-State (Same State):**
```
Taxable Value: ₹10,000
CGST @ 9%: ₹900
SGST @ 9%: ₹900
IGST: ₹0
Total: ₹11,800
```

**Inter-State (Different States):**
```
Taxable Value: ₹10,000
CGST: ₹0
SGST: ₹0
IGST @ 18%: ₹1,800
Total: ₹11,800
```

---

### 3. Project Brief Prompts

**Focus:** Comprehensive project documentation with risk management

**Key Instructions:**
- ✅ Detailed scope (in-scope, out-of-scope, assumptions, dependencies)
- ✅ Specific deliverables with acceptance criteria
- ✅ Realistic milestones with dependencies
- ✅ Structured billing plan (must total 100%)
- ✅ Risk assessment (impact, probability, mitigation)
- ✅ Timeline with 20% buffer
- ✅ Commercial terms

**Example Billing Plan:**
```json
[
  {"milestone": "Project Kickoff", "percentage": 30},
  {"milestone": "Design Approval", "percentage": 30},
  {"milestone": "Development Complete", "percentage": 25},
  {"milestone": "Go-Live", "percentage": 15}
]
```

---

## 📋 Common GST Rates (India)

| Category | GST Rate | HSN/SAC Code Examples |
|----------|----------|----------------------|
| IT Consulting | 18% | 998313 |
| Software Development | 18% | 998314 |
| Software Maintenance | 18% | 998316 |
| Digital Products | 18% | 998311 |
| Physical Products | 28% | Varies by category |
| Exempt Services | 0% | Varies |

---

## 🔧 Calculation Formulas

### Financial Calculations
```
Subtotal = Σ(quantity × unit_price)
Discount Amount = (Subtotal × discount_percentage) ÷ 100
Taxable Value = Subtotal - Discount Amount
GST Amount = Taxable Value × (GST rate ÷ 100)
Grand Total = Taxable Value + GST Amount
```

### GST Breakup
```
Intra-State:
  CGST = (Taxable Value × GST rate) ÷ 2
  SGST = (Taxable Value × GST rate) ÷ 2
  IGST = 0

Inter-State:
  CGST = 0
  SGST = 0
  IGST = Taxable Value × GST rate
```

### Rounding Rules
- All amounts: 2 decimal places
- Final total: Nearest rupee

---

## 🎯 Default Values

| Parameter | Default Value | Notes |
|-----------|---------------|-------|
| GST Rate (Services) | 18% | For IT/consulting services |
| GST Rate (Products) | 28% | For physical goods |
| Quotation Validity | 14-15 days | From issue date |
| Invoice Due Date | 7 days | From issue date |
| Payment Terms | 50% advance, 50% on completion | Conservative default |
| Project Buffer | 20% | Added to estimated timeline |

---

## 📝 Professional Language Guidelines

### Terms and Conditions Templates

**Quotation:**
- Payment terms: "50% advance on order confirmation, 50% on delivery"
- Validity: "This quotation is valid for 15 days from the date of issue"
- Cancellation: "Cancellation charges apply after advance payment"
- Warranty: "3 months warranty on all deliverables"

**Invoice:**
- Due date: "Payment due within 7 days from invoice date"
- Late payment: "1.5% per month late payment charges applicable"
- Jurisdiction: "Subject to [City] jurisdiction"
- Reverse charge: "Supply is liable for GST reverse charge - No"

**Project Brief:**
- IP rights: "All deliverables become client property upon full payment"
- Change requests: "Additional features will be quoted separately"
- Warranty: "3 months bug-fix warranty post go-live"
- Termination: "30 days notice required for termination"

---

## 🧪 Testing Scenarios

### Test Case 1: Intra-State Quotation
- **Seller:** Gujarat
- **Buyer:** Gujarat
- **Expected:** CGST + SGST breakdown
- **Validity:** 14-15 days from issue date

### Test Case 2: Inter-State Invoice
- **Seller:** Gujarat
- **Buyer:** Maharashtra
- **Expected:** IGST only, no CGST/SGST
- **Due Date:** 7 days from issue date

### Test Case 3: Complex Project Brief
- **Requirement:** Multi-phase project
- **Expected:** 
  - Detailed scope (in/out)
  - Multiple milestones with dependencies
  - Billing plan totaling 100%
  - Risk assessment with mitigation

---

## 🚀 Usage in Code

```python
from app.prompts.prompt import (
    build_quotation_prompt,
    build_invoice_prompt,
    build_project_brief_prompt
)

# Generate prompts
system_prompt, user_prompt, schema = build_quotation_prompt(request)

# Prompt lengths
# - System: ~2,000 characters (shared across all types)
# - User: 3,400-8,700 characters (varies by document type)
# - Total: 5,400-10,700 characters
```

---

## 📚 Related Files

| File | Purpose |
|------|---------|
| `ai-backend/app/prompts/prompt.py` | Main prompt builder (467 lines) |
| `ai-backend/app/schemas/outputs/` | JSON schemas for validation |
| `ai-backend/app/models/generation.py` | Request models |
| `ai-backend/PROMPT_IMPROVEMENTS.md` | Detailed documentation |

---

## ✅ Quality Checklist

Before deploying, verify:

- [ ] All financial calculations are accurate
- [ ] GST breakup is correct (CGST+SGST or IGST)
- [ ] HSN/SAC codes are appropriate
- [ ] Dates are calculated correctly
- [ ] Terms and conditions are professional
- [ ] JSON output matches schema
- [ ] No markdown or extra formatting
- [ ] Amounts are properly rounded

---

## 🎉 Summary

**Improvements Made:**
- ✅ 4x more detailed prompts
- ✅ Comprehensive GST compliance
- ✅ Precise calculation formulas
- ✅ Professional business language
- ✅ Indian business context
- ✅ Example structures
- ✅ Legal compliance emphasis

**Result:**
- Higher quality documents
- Accurate GST calculations
- Professional presentation
- Legal compliance
- Production-ready output

---

**The AI will now generate significantly better documents! 🚀**

