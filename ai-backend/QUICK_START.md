# 🚀 Quick Start Guide - Brief2Bill Streamlit UI

## Step-by-Step Setup

### 1️⃣ Install Streamlit

Open your terminal in the `ai-backend` directory and run:

```bash
# Activate virtual environment
venv\Scripts\activate

# Install Streamlit
pip install streamlit
```

### 2️⃣ Start the Backend Server

In **Terminal 1**, run:

```bash
cd ai-backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### 3️⃣ Start the Streamlit UI

In **Terminal 2** (new terminal), run:

```bash
cd ai-backend
venv\Scripts\activate
streamlit run streamlit_app.py
```

Or simply double-click: `run_streamlit.bat`

You should see:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

### 4️⃣ Open in Browser

The browser should open automatically to `http://localhost:8501`

If not, manually open: **http://localhost:8501**

## 🎯 First Test

1. **Check Health**: Click "Check API Health" in the sidebar
   - Should show "✅ API is healthy!"

2. **Load Providers**: Click "Fetch Providers" in the sidebar
   - Select "groq" from the dropdown
   - Select "llama-3.3-70b-versatile" as the model

3. **Generate Quotation**: 
   - The form is pre-filled with sample data
   - Click "🚀 Generate Quotation"
   - Wait for the AI to generate the response
   - View the formatted JSON output

## 📸 What You'll See

### Sidebar (Left)
- ⚙️ Configuration section
- 🏥 Health check button
- 🤖 AI Provider selection
- 📊 Current selection display

### Main Area (Center)
- 📋 Quotation tab (active)
- 🧾 Invoice tab (coming soon)
- 📝 Project Brief tab (coming soon)
- 🔍 View Response tab

### Quotation Form
- 👤 Seller Information (left column)
- 🏢 Buyer Information (right column)
- 📄 Document Details (3 columns)
- 📝 Requirement Description
- 📦 Optional Line Items
- 🚀 Generate Button

## ✅ Success Indicators

- **Green box**: "✅ Request Successful"
- **Status Code**: `200`
- **JSON Response**: Formatted document with all fields

## ❌ Common Issues

### Issue: "Connection refused"
**Solution**: Make sure the backend is running on port 8000

### Issue: "Module not found: streamlit"
**Solution**: Run `pip install streamlit`

### Issue: "Port 8501 already in use"
**Solution**: Run with different port:
```bash
streamlit run streamlit_app.py --server.port 8502
```

### Issue: "API Key required"
**Solution**: Add your API key in the sidebar or configure `.env` file

## 🎨 UI Features

- **Auto-fill**: Default values for quick testing
- **Real-time**: Instant response display
- **Download**: Save responses as JSON
- **Beautiful**: Modern, clean interface
- **Responsive**: Works on different screen sizes

## 🔄 Workflow

```
1. Configure API URL & Key (sidebar)
   ↓
2. Check API Health
   ↓
3. Fetch & Select AI Provider
   ↓
4. Fill Form (or use defaults)
   ↓
5. Click Generate
   ↓
6. View Response
   ↓
7. Download JSON (optional)
```

## 💡 Pro Tips

1. **Use Defaults**: The form comes pre-filled for quick testing
2. **Switch Providers**: Test the same request with different AI models
3. **Save Responses**: Download JSON for later use
4. **Check Logs**: Watch the backend terminal for detailed logs
5. **Experiment**: Try different requirements to see AI creativity

## 🎓 Example Requirements

Try these in the "Requirement Description" field:

**Simple:**
```
Website development with 5 pages and contact form
```

**Detailed:**
```
E-commerce platform with product catalog, shopping cart, 
payment integration, admin dashboard, and mobile app
```

**Service-based:**
```
Digital marketing package including SEO, social media 
management, and content creation for 3 months
```

**Consulting:**
```
Business consulting services for startup including 
market research, business plan, and investor pitch deck
```

## 📊 Understanding the Response

The generated quotation includes:

- **doc_type**: "QUOTATION"
- **seller/buyer**: Party information
- **doc_meta**: Document numbers and references
- **dates**: Issue date and validity
- **items**: Line items with pricing
- **totals**: Calculated subtotal, tax, and grand total
- **terms**: Terms and conditions
- **payment**: Payment instructions and UPI link

## 🎉 You're Ready!

You now have a fully functional web UI for testing Brief2Bill!

Enjoy generating professional documents with AI! 🚀

---

**Need Help?** Check `STREAMLIT_UI_README.md` for detailed documentation.

