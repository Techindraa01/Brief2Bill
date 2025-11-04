# 📖 How to Use the Streamlit UI - Step by Step

## 🎯 Complete Tutorial

### Prerequisites ✅

Before starting, make sure you have:
- [x] Python 3.13+ installed
- [x] Virtual environment activated
- [x] Backend server running on port 8000
- [x] Streamlit installed (`pip install streamlit`)

---

## 🚀 Step 1: Start the Backend Server

Open **Terminal 1** (PowerShell or Command Prompt):

```powershell
# Navigate to the backend directory
cd D:\playsotre-ideas\Brief2Bill\ai-backend

# Activate virtual environment
venv\Scripts\activate

# Start the backend server
uvicorn app.main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [67890]
INFO:     Application startup complete.
```

✅ **Backend is now running!**

---

## 🎨 Step 2: Start the Streamlit UI

### Option A: Using the Batch Script (Easiest)

1. Open **Terminal 2** (new PowerShell window)
2. Navigate to the backend directory:
   ```powershell
   cd D:\playsotre-ideas\Brief2Bill\ai-backend
   ```
3. Double-click `run_streamlit.bat` or run:
   ```powershell
   .\run_streamlit.bat
   ```

### Option B: Manual Start

Open **Terminal 2**:

```powershell
# Navigate to the backend directory
cd D:\playsotre-ideas\Brief2Bill\ai-backend

# Activate virtual environment
venv\Scripts\activate

# Start Streamlit
streamlit run streamlit_app.py
```

**Expected Output:**
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.100:8501
```

✅ **Streamlit UI is now running!**

The browser should automatically open to `http://localhost:8501`

---

## 🖥️ Step 3: Configure the UI

### 3.1 Check API Connection

In the **Sidebar** (left side):

1. Verify **API Base URL** is set to: `http://localhost:8000`
2. Click the **"Check API Health"** button
3. You should see: ✅ **"API is healthy!"**

If you see an error:
- ❌ Make sure the backend is running (Step 1)
- ❌ Check the URL is correct
- ❌ Verify port 8000 is not blocked

---

### 3.2 Load AI Providers

In the **Sidebar**:

1. Click **"Fetch Providers"** button
2. Wait 1-2 seconds
3. You should see: ✅ **"Providers loaded!"**

Now you'll see dropdown menus:
- **Select Provider**: Choose from openrouter, groq, openai, gemini
- **Select Model**: Choose a specific model

**Recommended for Testing:**
- Provider: **groq**
- Model: **llama-3.3-70b-versatile**

---

## 📋 Step 4: Generate Your First Quotation

### 4.1 Review Pre-filled Data

The form comes with sample data already filled in:

**Seller (Left Column):**
- Company: Acme Solutions Pvt Ltd
- Email: sales@acmesolutions.in
- Phone: +91-9800000000
- GSTIN: 24ABCDE1234F1Z5
- Address: 401, Skyline Tech Park...

**Buyer (Right Column):**
- Company: Indigo Retail Pvt Ltd
- Email: procurement@indigoretail.in
- Phone: +91-9810000000
- GSTIN: 27PQRSX1234A1Z2
- Address: 5th Floor, Horizon Plaza...

**Document Details:**
- Quotation Number: QTN-2025-0008
- Currency: INR
- Issue Date: Today
- Valid Till: Today + 21 days

**Requirement:**
```
Quotation for redesigning Indigo Retail's e-commerce 
storefront with optional maintenance retainer.
```

---

### 4.2 Generate the Quotation

1. Scroll to the bottom of the form
2. Click the big blue button: **🚀 Generate Quotation**
3. Wait 2-5 seconds (you'll see a spinner: "🤖 Generating quotation with AI...")

---

### 4.3 View the Response

After generation completes, you'll see:

**Success Indicator:**
```
✅ Request Successful
Status Code: 200
```

**JSON Response:**
A beautifully formatted JSON document with:
- Document type: QUOTATION
- Seller and buyer information
- Line items with pricing
- Calculated totals
- Tax breakdown
- Payment instructions
- UPI deep link

**Example Response Structure:**
```json
{
  "doc_type": "QUOTATION",
  "currency": "INR",
  "seller": { ... },
  "buyer": { ... },
  "items": [
    {
      "description": "Website redesign (desktop + mobile)",
      "qty": 1.0,
      "unit_price": 32000.0,
      "tax_rate": 18.0
    }
  ],
  "totals": {
    "subtotal": 41000.0,
    "tax_total": 7380.0,
    "grand_total": 48380.0
  }
}
```

---

## 💾 Step 5: Download the Response

1. Click on the **"🔍 View Response"** tab at the top
2. You'll see the full JSON response
3. Click the **"📥 Download JSON"** button
4. The file will be saved as: `brief2bill_response_YYYYMMDD_HHMMSS.json`

---

## 🎨 Step 6: Customize Your Quotation

### 6.1 Change Seller Information

1. Go back to the **"📋 Quotation"** tab
2. Modify the seller fields:
   - Change company name
   - Update email and phone
   - Edit address
   - Add UPI ID

### 6.2 Change Buyer Information

1. Update buyer details in the right column
2. All fields marked with * are required

### 6.3 Modify Document Details

1. Change the quotation number
2. Select different currency (USD, EUR, GBP)
3. Adjust dates using the date pickers
4. Add a reference number

### 6.4 Update Requirement

1. Clear the requirement text area
2. Enter your own description, for example:
   ```
   Mobile app development for iOS and Android with 
   backend API, user authentication, and payment gateway
   ```

### 6.5 Add Manual Line Items

1. Set "Number of line items" to 3
2. For each item, fill in:
   - Description
   - Quantity
   - Unit (pcs, hours, lot, etc.)
   - Unit Price
   - HSN/SAC code
   - Tax Rate (%)

### 6.6 Generate Again

1. Click **🚀 Generate Quotation**
2. View the new response
3. Compare with previous response

---

## 🔄 Step 7: Test Different AI Providers

### 7.1 Switch Provider

1. In the sidebar, change **Select Provider** to **openai**
2. Choose a model like **gpt-4-turbo-preview**
3. Generate the same quotation again
4. Compare the results

### 7.2 Compare Outputs

Different providers may:
- Generate different line items
- Use different descriptions
- Calculate differently
- Add more or fewer details

---

## 🎯 Step 8: Advanced Features

### 8.1 Use API Key (if required)

1. In the sidebar, find **"API Key (Optional)"**
2. Enter your API key
3. It will be included in all requests

### 8.2 Change API URL

1. Update **"API Base URL"** to point to:
   - Staging: `https://staging.yourdomain.com`
   - Production: `https://api.yourdomain.com`
   - Local: `http://localhost:8000`

### 8.3 Monitor Backend Logs

While generating, watch **Terminal 1** (backend) for logs:
```
INFO: quotation_generated provider=groq model=llama-3.3-70b-versatile latency_ms=2341
```

---

## ❌ Troubleshooting

### Problem: "Connection refused"

**Solution:**
1. Check if backend is running (Terminal 1)
2. Verify URL is `http://localhost:8000`
3. Try restarting the backend

### Problem: "API returned status 500"

**Solution:**
1. Check backend logs in Terminal 1
2. Look for error messages
3. Verify API keys are configured in `.env`
4. Check if the provider is enabled

### Problem: "Providers not loading"

**Solution:**
1. Ensure backend is running
2. Check if API keys are set in `.env` file
3. Click "Check API Health" first
4. Try refreshing the page

### Problem: "Streamlit won't start"

**Solution:**
1. Make sure Streamlit is installed: `pip install streamlit`
2. Check if port 8501 is available
3. Try a different port: `streamlit run streamlit_app.py --server.port 8502`

### Problem: "Module not found"

**Solution:**
1. Activate virtual environment: `venv\Scripts\activate`
2. Install dependencies: `pip install -r requirements.txt`

---

## 💡 Pro Tips

### Tip 1: Quick Testing
Use the default values for rapid testing - just click generate!

### Tip 2: Save Templates
Copy the JSON response and save it as a template for future use

### Tip 3: Experiment with Requirements
Try different requirement descriptions to see AI creativity:
- "Website with blog and e-commerce"
- "Mobile app with social features"
- "Consulting services for 6 months"

### Tip 4: Compare Providers
Generate the same quotation with different providers to compare quality

### Tip 5: Watch the Logs
Keep an eye on Terminal 1 to see what's happening behind the scenes

---

## 🎉 Success Checklist

After completing this tutorial, you should be able to:

- [x] Start the backend server
- [x] Launch the Streamlit UI
- [x] Check API health
- [x] Load AI providers
- [x] Select provider and model
- [x] Generate a quotation with default data
- [x] View the JSON response
- [x] Download the response
- [x] Customize seller/buyer information
- [x] Modify document details
- [x] Add manual line items
- [x] Test different AI providers
- [x] Troubleshoot common issues

---

## 🚀 Next Steps

Now that you know how to use the Streamlit UI:

1. **Explore Other Tabs**: Invoice and Project Brief (coming soon)
2. **Integrate with Frontend**: Use the API in your Flutter app
3. **Customize**: Modify `streamlit_app.py` to add features
4. **Deploy**: Host the UI for team access
5. **Automate**: Create scripts for batch generation

---

## 📚 Additional Resources

- **Full Documentation**: [STREAMLIT_UI_README.md](STREAMLIT_UI_README.md)
- **Features Overview**: [STREAMLIT_FEATURES.md](STREAMLIT_FEATURES.md)
- **Quick Start**: [QUICK_START.md](QUICK_START.md)
- **Main README**: [../README.md](../README.md)

---

**Happy Generating! 🎉**

If you have questions or issues, check the troubleshooting section or review the backend logs.

