# 🎨 Brief2Bill Streamlit Web UI

A beautiful, interactive web interface for testing the Brief2Bill API endpoints.

## 🌟 Features

- **Interactive Forms**: Easy-to-use forms for entering seller, buyer, and document details
- **Real-time Testing**: Test all API endpoints with live responses
- **AI Provider Selection**: Choose from multiple AI providers (OpenRouter, Groq, OpenAI, Gemini)
- **Model Selection**: Select specific models for each provider
- **Response Viewer**: View and download generated JSON responses
- **Health Monitoring**: Check API health status
- **Beautiful UI**: Modern, responsive design with custom styling

## 🚀 Quick Start

### Option 1: Using the Batch Script (Windows)

1. **Make sure the backend is running:**
   ```bash
   cd ai-backend
   venv\Scripts\activate
   uvicorn app.main:app --reload
   ```

2. **In a new terminal, run the Streamlit UI:**
   ```bash
   cd ai-backend
   run_streamlit.bat
   ```

3. **Open your browser** to `http://localhost:8501`

### Option 2: Manual Start

1. **Activate virtual environment:**
   ```bash
   cd ai-backend
   venv\Scripts\activate
   ```

2. **Install Streamlit (if not already installed):**
   ```bash
   pip install streamlit
   ```

3. **Run the Streamlit app:**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Open your browser** to `http://localhost:8501`

## 📋 Usage Guide

### 1. Configuration (Sidebar)

- **API Base URL**: Set the backend URL (default: `http://localhost:8000`)
- **API Key**: Enter your API key if required (optional)
- **Health Check**: Click to verify the backend is running
- **Provider Selection**: 
  - Click "Fetch Providers" to load available AI providers
  - Select your preferred provider (Groq, OpenAI, etc.)
  - Choose a specific model

### 2. Generate Quotation

**Seller Information:**
- Company Name, Email, Phone (required)
- GSTIN, PAN (optional)
- Address (required)
- UPI ID (optional)

**Buyer Information:**
- Company Name, Email, Phone (required)
- GSTIN, PAN (optional)
- Address (required)

**Document Details:**
- Quotation Number
- Reference Number
- Currency (INR, USD, EUR, GBP)
- Locale (en-IN, en-US, en-GB)
- Issue Date
- Valid Till Date

**Requirement Description:**
- Enter a natural language description of what you need
- The AI will generate appropriate line items

**Optional Manual Line Items:**
- Add specific line items manually
- Set quantity, unit price, tax rate, HSN/SAC codes

**Generate:**
- Click "🚀 Generate Quotation"
- View the AI-generated response
- Download the JSON if needed

### 3. View Response

- Switch to the "🔍 View Response" tab
- See the last generated response
- Download as JSON file

## 🎯 Example Workflow

1. **Start the backend server** (in terminal 1):
   ```bash
   cd ai-backend
   venv\Scripts\activate
   uvicorn app.main:app --reload
   ```

2. **Start the Streamlit UI** (in terminal 2):
   ```bash
   cd ai-backend
   run_streamlit.bat
   ```

3. **In the browser:**
   - Click "Check API Health" to verify connection
   - Click "Fetch Providers" to load AI providers
   - Select "groq" and "llama-3.3-70b-versatile"
   - Fill in the quotation form (or use default values)
   - Click "🚀 Generate Quotation"
   - View the generated document in the response section

## 🔧 Troubleshooting

### Backend Not Responding
- Ensure the backend is running on `http://localhost:8000`
- Check the API Base URL in the sidebar
- Click "Check API Health" to verify connection

### Provider List Not Loading
- Make sure you have API keys configured in the backend `.env` file
- Check backend logs for errors
- Verify the backend is running properly

### Streamlit Not Starting
- Make sure Streamlit is installed: `pip install streamlit`
- Check if port 8501 is available
- Try running with: `streamlit run streamlit_app.py --server.port 8502`

### Module Not Found Errors
- Activate the virtual environment first
- Install dependencies: `pip install -r requirements.txt`

## 📊 Available Tabs

### 📋 Quotation
Generate professional quotations with AI assistance

### 🧾 Invoice
Generate tax invoices (coming soon)

### 📝 Project Brief
Generate project briefs with milestones (coming soon)

### 🔍 View Response
View and download the last API response

## 🎨 UI Features

- **Responsive Design**: Works on desktop and tablet
- **Color-Coded Responses**: 
  - Green for successful requests
  - Red for errors
  - Blue for information
- **JSON Viewer**: Formatted JSON display with syntax highlighting
- **Download Support**: Download responses as JSON files
- **Form Validation**: Required fields are marked with *
- **Auto-Save**: Session state preserves your inputs

## 🔐 Security Notes

- API keys are stored in session state (not persisted)
- Use HTTPS in production
- Don't commit API keys to version control
- The UI is for testing purposes - not production-ready

## 🚀 Advanced Usage

### Custom API URL
Change the API Base URL to test against different environments:
- Local: `http://localhost:8000`
- Staging: `https://staging.yourdomain.com`
- Production: `https://api.yourdomain.com`

### Multiple Providers
Test the same request with different AI providers:
1. Generate with Groq
2. Switch to OpenAI
3. Generate again
4. Compare responses

### Batch Testing
Use the form to quickly test multiple scenarios:
- Different currencies
- Various tax rates
- Multiple line items
- Different date ranges

## 📝 Notes

- The UI automatically formats dates to ISO format
- All fields with * are required
- The AI will intelligently fill in missing details
- Responses are displayed in real-time
- Session state is preserved during the session

## 🤝 Contributing

To add new features to the UI:
1. Edit `streamlit_app.py`
2. Add new tabs or sections as needed
3. Follow the existing styling patterns
4. Test thoroughly before committing

## 📄 License

Same as the main Brief2Bill project.

---

**Made with ❤️ for Brief2Bill**

