# 🧪 Test All Features - Complete Guide

## 🎯 Testing Workflow

This guide will help you test all three document types in the Streamlit UI.

---

## 🚀 Setup (Do This First)

### Step 1: Start Backend
```bash
cd ai-backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 2: Start Streamlit
```bash
# In a new terminal
cd ai-backend
venv\Scripts\activate
streamlit run streamlit_app.py
```

**Expected Output:**
```
Local URL: http://localhost:8501
```

### Step 3: Configure
1. Open http://localhost:8501
2. Click "Check API Health" → Should show ✅
3. Click "Fetch Providers" → Should show "Providers loaded!"
4. Select Provider: **groq**
5. Select Model: **llama-3.3-70b-versatile**

---

## 📋 Test 1: Quotation Generator

### Scenario: Website Development Quotation

**Steps:**
1. Go to **"📋 Quotation"** tab
2. Review the pre-filled data (or customize)
3. Update the requirement to:
   ```
   Create a quotation for website development including:
   - 5 page responsive website
   - Contact form integration
   - SEO optimization
   - 3 months maintenance
   Total budget: ₹50,000
   ```
4. Click **"🚀 Generate Quotation"**

**Expected Result:**
- ✅ Status Code: 200
- ✅ Green success box
- ✅ JSON response with:
  - `doc_type`: "QUOTATION"
  - `currency`: "INR"
  - `seller`: Acme Solutions details
  - `buyer`: Indigo Retail details
  - `items`: Array of line items (website pages, SEO, maintenance)
  - `totals`: Subtotal, tax, grand total
  - `terms`: Payment terms
  - `payment`: UPI deeplink

**Sample Items Generated:**
```json
{
  "items": [
    {
      "description": "5-page responsive website design and development",
      "qty": 1,
      "unit_price": 25000,
      "tax_rate": 18
    },
    {
      "description": "Contact form integration with email notifications",
      "qty": 1,
      "unit_price": 5000,
      "tax_rate": 18
    },
    {
      "description": "SEO optimization (on-page and technical)",
      "qty": 1,
      "unit_price": 10000,
      "tax_rate": 18
    },
    {
      "description": "3 months maintenance and support",
      "qty": 1,
      "unit_price": 10000,
      "tax_rate": 18
    }
  ]
}
```

**Verification:**
- [ ] Total should be around ₹50,000 + GST
- [ ] All 4 items should be present
- [ ] UPI deeplink should be generated
- [ ] Download button works

---

## 🧾 Test 2: Invoice Generator

### Scenario: Milestone Payment Invoice

**Steps:**
1. Go to **"🧾 Invoice"** tab
2. Review the pre-filled data
3. Update the requirement to:
   ```
   Invoice for website redesign project - Milestone 2 completion:
   - Frontend development completed
   - Backend API integration done
   - Testing and QA completed
   Amount: ₹37,000 + GST
   ```
4. Update Invoice Number to: `INV-2025-0500`
5. Update PO Number to: `CLIENT-PO-2025-100`
6. Click **"🚀 Generate Invoice"**

**Expected Result:**
- ✅ Status Code: 200
- ✅ Green success box
- ✅ JSON response with:
  - `doc_type`: "TAX_INVOICE"
  - `currency`: "INR"
  - `seller`: Acme Solutions with CIN
  - `buyer`: Indigo Retail with place of supply
  - `items`: Milestone items
  - `totals`: Subtotal, CGST, SGST, grand total
  - `tax_breakdown`: Detailed tax calculation
  - `payment`: Bank transfer details

**Sample Items Generated:**
```json
{
  "items": [
    {
      "description": "Frontend development - Milestone 2",
      "hsn_sac": "998313",
      "qty": 1,
      "unit_price": 20000,
      "tax_rate": 18
    },
    {
      "description": "Backend API integration",
      "hsn_sac": "998313",
      "qty": 1,
      "unit_price": 12000,
      "tax_rate": 18
    },
    {
      "description": "Testing and QA",
      "hsn_sac": "998313",
      "qty": 1,
      "unit_price": 5000,
      "tax_rate": 18
    }
  ]
}
```

**Verification:**
- [ ] Invoice number is INV-2025-0500
- [ ] PO number is CLIENT-PO-2025-100
- [ ] CIN is present in seller details
- [ ] Tax breakdown shows CGST and SGST
- [ ] Due date is 15 days from issue date
- [ ] Download button works

---

## 📝 Test 3: Project Brief Generator

### Scenario: E-commerce Platform Project

**Steps:**
1. Go to **"📝 Project Brief"** tab
2. Review the pre-filled data
3. Update the requirement to:
   ```
   Comprehensive project brief for building a complete e-commerce platform:
   
   Scope:
   - Customer-facing web application (React)
   - Mobile apps (iOS and Android)
   - Admin dashboard for inventory management
   - Payment gateway integration (Razorpay, Stripe)
   - Order tracking and notifications
   - Analytics and reporting
   
   Timeline: 6 months
   Budget: ₹25,00,000
   
   Deliverables:
   - Phase 1: Core platform (3 months)
   - Phase 2: Mobile apps (2 months)
   - Phase 3: Advanced features (1 month)
   ```
4. Set Payment Mode to: **MILESTONE**
5. Click **"🚀 Generate Project Brief"**

**Expected Result:**
- ✅ Status Code: 200
- ✅ Green success box
- ✅ JSON response with:
  - `doc_type`: "PROJECT_BRIEF"
  - `currency`: "INR"
  - `provider`: Acme Solutions
  - `client`: Indigo Retail
  - `project_overview`: Detailed description
  - `scope`: In-scope and out-of-scope items
  - `deliverables`: Phased deliverables
  - `timeline`: Milestones with dates
  - `budget`: Breakdown by phase
  - `success_metrics`: KPIs and metrics
  - `risks`: Risk assessment
  - `assumptions`: Project assumptions

**Sample Output Structure:**
```json
{
  "doc_type": "PROJECT_BRIEF",
  "project_overview": {
    "title": "E-commerce Platform Development",
    "description": "...",
    "objectives": [...]
  },
  "scope": {
    "in_scope": [
      "Customer-facing web application",
      "iOS and Android mobile apps",
      "Admin dashboard",
      "Payment integration",
      "Order tracking"
    ],
    "out_of_scope": [
      "Third-party logistics integration",
      "Custom ERP integration"
    ]
  },
  "deliverables": [
    {
      "phase": "Phase 1",
      "name": "Core Platform",
      "duration": "3 months",
      "items": [...]
    }
  ],
  "timeline": {
    "total_duration": "6 months",
    "milestones": [...]
  },
  "budget": {
    "total": 2500000,
    "breakdown": [...]
  }
}
```

**Verification:**
- [ ] Project overview is comprehensive
- [ ] Scope clearly defines in-scope and out-of-scope
- [ ] 3 phases are defined
- [ ] Timeline shows 6 months
- [ ] Budget is around ₹25,00,000
- [ ] Success metrics are included
- [ ] Risks and assumptions are listed
- [ ] Download button works

---

## 🔄 Test 4: Provider Comparison

### Test Different AI Providers

**Steps:**
1. Generate a quotation with **groq** / **llama-3.3-70b-versatile**
2. Download the response
3. Switch to **openai** / **gpt-4-turbo-preview** (if available)
4. Generate the same quotation
5. Download the response
6. Compare the two outputs

**What to Compare:**
- Line item descriptions
- Pricing structure
- Terms and conditions
- Level of detail
- Creativity in item generation

---

## 🎨 Test 5: UI Features

### Test All UI Components

**Sidebar:**
- [ ] API URL can be changed
- [ ] API Key field works (password type)
- [ ] Health check button responds
- [ ] Provider fetch button works
- [ ] Provider dropdown populates
- [ ] Model dropdown populates
- [ ] Current selection displays correctly

**Forms:**
- [ ] All text inputs are editable
- [ ] Date pickers work
- [ ] Dropdowns work
- [ ] Text areas expand
- [ ] Number inputs validate
- [ ] Expanders open/close

**Response Display:**
- [ ] Success box shows for 200
- [ ] Error box shows for errors
- [ ] JSON is formatted
- [ ] JSON is collapsible
- [ ] Status code is displayed

**Download:**
- [ ] Download button appears
- [ ] Filename has timestamp
- [ ] File is valid JSON
- [ ] File contains full response

---

## 🐛 Test 6: Error Handling

### Test Error Scenarios

**Test 1: Backend Not Running**
1. Stop the backend server
2. Try to generate a quotation
3. **Expected:** Error message with connection details

**Test 2: Invalid API Key**
1. Enter a wrong API key in sidebar
2. Try to generate a document
3. **Expected:** 401 or 403 error

**Test 3: Invalid Provider**
1. Manually set provider to "invalid"
2. Try to generate a document
3. **Expected:** Provider error message

**Test 4: Empty Required Fields**
1. Clear a required field (marked with *)
2. Try to generate
3. **Expected:** Validation error or empty field in response

---

## 📊 Test 7: Performance

### Measure Response Times

**Test Each Document Type:**

| Document Type | Expected Time | Actual Time | Status |
|---------------|---------------|-------------|--------|
| Quotation | 2-5 seconds | _____ | ⬜ |
| Invoice | 2-5 seconds | _____ | ⬜ |
| Project Brief | 3-7 seconds | _____ | ⬜ |

**Notes:**
- Project Brief takes longer due to more complex output
- Time varies by AI provider
- Network latency affects timing

---

## ✅ Final Checklist

### All Features Working
- [ ] Quotation generation works
- [ ] Invoice generation works
- [ ] Project Brief generation works
- [ ] Health check works
- [ ] Provider fetching works
- [ ] Provider selection works
- [ ] Model selection works
- [ ] Download works for all types
- [ ] Error handling works
- [ ] Session state preserved
- [ ] UI is responsive
- [ ] All forms are editable

### Documentation Complete
- [ ] README.md updated
- [ ] QUICK_START.md created
- [ ] HOW_TO_USE_STREAMLIT.md created
- [ ] STREAMLIT_FEATURES.md created
- [ ] STREAMLIT_COMPLETE.md created
- [ ] TEST_ALL_FEATURES.md created (this file)

---

## 🎉 Success Criteria

**All tests pass if:**
1. ✅ All three document types generate successfully
2. ✅ Responses are valid JSON
3. ✅ AI generates appropriate content
4. ✅ Download functionality works
5. ✅ Error handling is graceful
6. ✅ UI is user-friendly
7. ✅ Performance is acceptable

---

## 📝 Test Results Template

```
Date: ___________
Tester: ___________

Quotation Test: ⬜ Pass ⬜ Fail
Invoice Test: ⬜ Pass ⬜ Fail
Project Brief Test: ⬜ Pass ⬜ Fail
Provider Comparison: ⬜ Pass ⬜ Fail
UI Features: ⬜ Pass ⬜ Fail
Error Handling: ⬜ Pass ⬜ Fail
Performance: ⬜ Pass ⬜ Fail

Overall: ⬜ Pass ⬜ Fail

Notes:
_________________________________
_________________________________
_________________________________
```

---

**Ready to test? Start with Setup and work through each test! 🚀**

