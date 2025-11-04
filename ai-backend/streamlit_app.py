"""
Streamlit Web UI for Brief2Bill API Testing
A beautiful, interactive interface for testing document generation endpoints.
"""

import json
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional

import httpx
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Brief2Bill - Document Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'api_url' not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'last_response' not in st.session_state:
    st.session_state.last_response = None
if 'provider' not in st.session_state:
    st.session_state.provider = "groq"
if 'model' not in st.session_state:
    st.session_state.model = "llama-3.3-70b-versatile"


def make_request(endpoint: str, method: str = "GET", data: Optional[Dict] = None, headers: Optional[Dict] = None) -> tuple:
    """Make HTTP request to the API."""
    url = f"{st.session_state.api_url}{endpoint}"
    
    request_headers = {}
    if st.session_state.api_key:
        request_headers["X-API-Key"] = st.session_state.api_key
    if headers:
        request_headers.update(headers)
    
    try:
        with httpx.Client(timeout=60.0) as client:
            if method == "GET":
                response = client.get(url, headers=request_headers)
            elif method == "POST":
                response = client.post(url, json=data, headers=request_headers)
            else:
                return None, f"Unsupported method: {method}"
            
            return response, None
    except Exception as e:
        return None, str(e)


def display_response(response):
    """Display API response in a formatted way."""
    if response is None:
        return
    
    st.markdown(f"**Status Code:** `{response.status_code}`")
    
    if response.status_code == 200:
        st.markdown('<div class="success-box">✅ Request Successful</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="error-box">❌ Request Failed: {response.status_code}</div>', unsafe_allow_html=True)
    
    try:
        json_data = response.json()
        st.json(json_data)
        st.session_state.last_response = json_data
        return json_data
    except:
        st.code(response.text)
        return None


# Sidebar - Configuration
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    
    st.session_state.api_url = st.text_input(
        "API Base URL",
        value=st.session_state.api_url,
        help="Base URL of the Brief2Bill API"
    )
    
    st.session_state.api_key = st.text_input(
        "API Key (Optional)",
        value=st.session_state.api_key,
        type="password",
        help="Leave blank if API key is not required"
    )
    
    st.markdown("---")
    
    # Health Check
    st.markdown("### 🏥 Health Check")
    if st.button("Check API Health", use_container_width=True):
        response, error = make_request("/v1/healthz")
        if error:
            st.error(f"Error: {error}")
        elif response:
            if response.status_code == 200:
                st.success("✅ API is healthy!")
            else:
                st.error(f"❌ API returned status {response.status_code}")
    
    st.markdown("---")
    
    # Provider Selection
    st.markdown("### 🤖 AI Provider")
    
    if st.button("Fetch Providers", use_container_width=True):
        response, error = make_request("/v1/providers")
        if error:
            st.error(f"Error: {error}")
        elif response and response.status_code == 200:
            providers_data = response.json()
            st.session_state.providers_list = providers_data.get("providers", [])
            st.success("Providers loaded!")
    
    if 'providers_list' in st.session_state:
        provider_names = [p["name"] for p in st.session_state.providers_list]
        selected_provider = st.selectbox(
            "Select Provider",
            options=provider_names,
            index=provider_names.index(st.session_state.provider) if st.session_state.provider in provider_names else 0
        )
        
        # Get models for selected provider
        provider_data = next((p for p in st.session_state.providers_list if p["name"] == selected_provider), None)
        if provider_data:
            model_options = [m["id"] for m in provider_data.get("models", [])]
            if model_options:
                selected_model = st.selectbox(
                    "Select Model",
                    options=model_options,
                    index=model_options.index(st.session_state.model) if st.session_state.model in model_options else 0
                )
                
                st.session_state.provider = selected_provider
                st.session_state.model = selected_model
    
    st.markdown("---")
    st.markdown("### 📊 Current Selection")
    st.info(f"**Provider:** {st.session_state.provider}\n\n**Model:** {st.session_state.model}")


# Main Content
st.markdown('<h1 class="main-header">📄 Brief2Bill Document Generator</h1>', unsafe_allow_html=True)

# Tabs for different document types
tab1, tab2, tab3, tab4 = st.tabs(["📋 Quotation", "🧾 Invoice", "📝 Project Brief", "🔍 View Response"])

# Tab 1: Quotation Generator
with tab1:
    st.markdown('<div class="section-header">Generate Quotation</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 👤 Seller Information")
        seller_name = st.text_input("Company Name*", value="Acme Solutions Pvt Ltd", key="seller_name")
        seller_email = st.text_input("Email*", value="sales@acmesolutions.in", key="seller_email")
        seller_phone = st.text_input("Phone*", value="+91-9800000000", key="seller_phone")
        seller_gstin = st.text_input("GSTIN", value="24ABCDE1234F1Z5", key="seller_gstin")
        seller_pan = st.text_input("PAN", value="ABCDE1234F", key="seller_pan")
        seller_address = st.text_area(
            "Address*",
            value="401, Skyline Tech Park, City Light Road, Surat, Gujarat, 395007, India",
            key="seller_address"
        )
        seller_upi = st.text_input("UPI ID", value="acmesolutions@upi", key="seller_upi")
    
    with col2:
        st.markdown("#### 🏢 Buyer Information")
        buyer_name = st.text_input("Company Name*", value="Indigo Retail Pvt Ltd", key="buyer_name")
        buyer_email = st.text_input("Email*", value="procurement@indigoretail.in", key="buyer_email")
        buyer_phone = st.text_input("Phone*", value="+91-9810000000", key="buyer_phone")
        buyer_gstin = st.text_input("GSTIN", value="27PQRSX1234A1Z2", key="buyer_gstin")
        buyer_pan = st.text_input("PAN", value="PQRSX1234A", key="buyer_pan")
        buyer_address = st.text_area(
            "Address*",
            value="5th Floor, Horizon Plaza, Nariman Point, Mumbai, Maharashtra, 400021, India",
            key="buyer_address"
        )
    
    st.markdown('<div class="section-header">Document Details</div>', unsafe_allow_html=True)
    
    col3, col4, col5 = st.columns(3)
    with col3:
        doc_no = st.text_input("Quotation Number", value="QTN-2025-0008", key="doc_no")
        currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP"], index=0, key="currency")
    with col4:
        ref_no = st.text_input("Reference Number", value="", key="ref_no")
        locale = st.selectbox("Locale", ["en-IN", "en-US", "en-GB"], index=0, key="locale")
    with col5:
        issue_date = st.date_input("Issue Date", value=date.today(), key="issue_date")
        valid_till = st.date_input("Valid Till", value=date.today() + timedelta(days=21), key="valid_till")
    
    st.markdown('<div class="section-header">Requirement Description</div>', unsafe_allow_html=True)
    requirement = st.text_area(
        "Describe what you need (AI will generate line items)*",
        value="Quotation for redesigning Indigo Retail's e-commerce storefront with optional maintenance retainer.",
        height=100,
        key="requirement"
    )
    
    st.markdown('<div class="section-header">Optional: Manual Line Items</div>', unsafe_allow_html=True)
    
    num_items = st.number_input("Number of line items", min_value=0, max_value=10, value=2, key="num_items")
    
    items = []
    for i in range(int(num_items)):
        with st.expander(f"Item {i+1}", expanded=(i==0)):
            item_col1, item_col2, item_col3 = st.columns(3)
            with item_col1:
                desc = st.text_input("Description", value=f"Item {i+1}", key=f"item_desc_{i}")
                qty = st.number_input("Quantity", min_value=0.0, value=1.0, key=f"item_qty_{i}")
            with item_col2:
                unit = st.text_input("Unit", value="pcs", key=f"item_unit_{i}")
                unit_price = st.number_input("Unit Price", min_value=0.0, value=1000.0, key=f"item_price_{i}")
            with item_col3:
                hsn_sac = st.text_input("HSN/SAC", value="", key=f"item_hsn_{i}")
                tax_rate = st.number_input("Tax Rate (%)", min_value=0.0, max_value=100.0, value=18.0, key=f"item_tax_{i}")
            
            items.append({
                "description": desc,
                "qty": qty,
                "unit": unit,
                "unit_price": unit_price,
                "discount": 0,
                "tax_rate": tax_rate,
                "hsn_sac": hsn_sac
            })
    
    st.markdown("---")
    
    if st.button("🚀 Generate Quotation", type="primary", use_container_width=True):
        # Build request payload
        payload = {
            "from": {
                "name": seller_name,
                "email": seller_email,
                "phone": seller_phone,
                "gstin": seller_gstin,
                "pan": seller_pan,
                "billing_address": {
                    "line1": seller_address.split(',')[0] if ',' in seller_address else seller_address,
                    "city": "Surat",
                    "state": "Gujarat",
                    "country": "India"
                },
                "bank": {
                    "upi_id": seller_upi
                } if seller_upi else None
            },
            "to": {
                "name": buyer_name,
                "email": buyer_email,
                "phone": buyer_phone,
                "gstin": buyer_gstin,
                "pan": buyer_pan,
                "billing_address": {
                    "line1": buyer_address.split(',')[0] if ',' in buyer_address else buyer_address,
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "country": "India"
                }
            },
            "currency": currency,
            "locale": locale,
            "requirement": requirement,
            "hints": {
                "doc_meta": {
                    "doc_no": doc_no,
                    "ref_no": ref_no,
                    "po_no": ""
                },
                "dates": {
                    "issue_date": issue_date.isoformat(),
                    "valid_till": valid_till.isoformat()
                },
                "items": items if num_items > 0 else [],
                "payment": {
                    "mode": "UPI",
                    "instructions": "Pay 50% advance to initiate the project"
                }
            }
        }
        
        headers = {
            "X-Provider": st.session_state.provider,
            "X-Model": st.session_state.model
        }
        
        with st.spinner("🤖 Generating quotation with AI..."):
            response, error = make_request("/v1/generate/quotation", method="POST", data=payload, headers=headers)
            
            if error:
                st.error(f"❌ Error: {error}")
            elif response:
                st.markdown("### 📊 Response")
                display_response(response)

# Tab 2: Invoice Generator
with tab2:
    st.markdown('<div class="section-header">Generate Tax Invoice</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 👤 Seller Information")
        inv_seller_name = st.text_input("Company Name*", value="Acme Solutions Pvt Ltd", key="inv_seller_name")
        inv_seller_email = st.text_input("Email*", value="billing@acmesolutions.in", key="inv_seller_email")
        inv_seller_phone = st.text_input("Phone*", value="+91-9800000000", key="inv_seller_phone")
        inv_seller_gstin = st.text_input("GSTIN", value="24ABCDE1234F1Z5", key="inv_seller_gstin")
        inv_seller_pan = st.text_input("PAN", value="ABCDE1234F", key="inv_seller_pan")
        inv_seller_cin = st.text_input("CIN", value="U72900GJ2010PTC000123", key="inv_seller_cin")
        inv_seller_address = st.text_area(
            "Address*",
            value="401, Skyline Tech Park, City Light Road, Surat, Gujarat, 395007, India",
            key="inv_seller_address"
        )
        inv_seller_upi = st.text_input("UPI ID", value="acmesolutions@upi", key="inv_seller_upi")

    with col2:
        st.markdown("#### 🏢 Buyer Information")
        inv_buyer_name = st.text_input("Company Name*", value="Indigo Retail Pvt Ltd", key="inv_buyer_name")
        inv_buyer_email = st.text_input("Email*", value="accounts@indigoretail.in", key="inv_buyer_email")
        inv_buyer_phone = st.text_input("Phone*", value="+91-9810000000", key="inv_buyer_phone")
        inv_buyer_gstin = st.text_input("GSTIN", value="27PQRSX1234A1Z2", key="inv_buyer_gstin")
        inv_buyer_pan = st.text_input("PAN", value="PQRSX1234A", key="inv_buyer_pan")
        inv_buyer_address = st.text_area(
            "Address*",
            value="5th Floor, Horizon Plaza, Nariman Point, Mumbai, Maharashtra, 400021, India",
            key="inv_buyer_address"
        )
        inv_buyer_place_of_supply = st.text_input("Place of Supply", value="Maharashtra", key="inv_buyer_place")

    st.markdown('<div class="section-header">Document Details</div>', unsafe_allow_html=True)

    col3, col4, col5 = st.columns(3)
    with col3:
        inv_doc_no = st.text_input("Invoice Number*", value="INV-2025-0452", key="inv_doc_no")
        inv_currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP"], index=0, key="inv_currency")
    with col4:
        inv_po_no = st.text_input("PO Number", value="INDIGO-PO-1122", key="inv_po_no")
        inv_locale = st.selectbox("Locale", ["en-IN", "en-US", "en-GB"], index=0, key="inv_locale")
    with col5:
        inv_issue_date = st.date_input("Issue Date", value=date.today(), key="inv_issue_date")
        inv_due_date = st.date_input("Due Date", value=date.today() + timedelta(days=15), key="inv_due_date")

    st.markdown('<div class="section-header">Requirement Description</div>', unsafe_allow_html=True)
    inv_requirement = st.text_area(
        "Describe the invoice (AI will generate line items)*",
        value="Invoice for website redesign project milestone completion.",
        height=100,
        key="inv_requirement"
    )

    st.markdown('<div class="section-header">Optional: Manual Line Items</div>', unsafe_allow_html=True)

    inv_num_items = st.number_input("Number of line items", min_value=0, max_value=10, value=2, key="inv_num_items")

    inv_items = []
    for i in range(int(inv_num_items)):
        with st.expander(f"Item {i+1}", expanded=(i==0)):
            inv_item_col1, inv_item_col2, inv_item_col3 = st.columns(3)
            with inv_item_col1:
                inv_desc = st.text_input("Description", value=f"Service {i+1}", key=f"inv_item_desc_{i}")
                inv_qty = st.number_input("Quantity", min_value=0.0, value=1.0, key=f"inv_item_qty_{i}")
            with inv_item_col2:
                inv_unit = st.text_input("Unit", value="job", key=f"inv_item_unit_{i}")
                inv_unit_price = st.number_input("Unit Price", min_value=0.0, value=28000.0, key=f"inv_item_price_{i}")
            with inv_item_col3:
                inv_hsn_sac = st.text_input("HSN/SAC", value="998313", key=f"inv_item_hsn_{i}")
                inv_tax_rate = st.number_input("Tax Rate (%)", min_value=0.0, max_value=100.0, value=18.0, key=f"inv_item_tax_{i}")

            inv_items.append({
                "description": inv_desc,
                "qty": inv_qty,
                "unit": inv_unit,
                "unit_price": inv_unit_price,
                "discount": 0,
                "tax_rate": inv_tax_rate,
                "hsn_sac": inv_hsn_sac
            })

    st.markdown("---")

    if st.button("🚀 Generate Invoice", type="primary", use_container_width=True, key="gen_invoice_btn"):
        # Build request payload
        inv_payload = {
            "from": {
                "name": inv_seller_name,
                "email": inv_seller_email,
                "phone": inv_seller_phone,
                "gstin": inv_seller_gstin,
                "pan": inv_seller_pan,
                "cin": inv_seller_cin,
                "billing_address": {
                    "line1": inv_seller_address.split(',')[0] if ',' in inv_seller_address else inv_seller_address,
                    "city": "Surat",
                    "state": "Gujarat",
                    "country": "India"
                },
                "bank": {
                    "upi_id": inv_seller_upi
                } if inv_seller_upi else None,
                "tax_prefs": {
                    "place_of_supply": "Gujarat",
                    "reverse_charge": False,
                    "e_invoice": True
                }
            },
            "to": {
                "name": inv_buyer_name,
                "email": inv_buyer_email,
                "phone": inv_buyer_phone,
                "gstin": inv_buyer_gstin,
                "pan": inv_buyer_pan,
                "billing_address": {
                    "line1": inv_buyer_address.split(',')[0] if ',' in inv_buyer_address else inv_buyer_address,
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "country": "India"
                },
                "place_of_supply": inv_buyer_place_of_supply
            },
            "currency": inv_currency,
            "locale": inv_locale,
            "requirement": inv_requirement,
            "hints": {
                "doc_meta": {
                    "doc_no": inv_doc_no,
                    "po_no": inv_po_no,
                    "ref_no": ""
                },
                "dates": {
                    "issue_date": inv_issue_date.isoformat(),
                    "due_date": inv_due_date.isoformat()
                },
                "items": inv_items if inv_num_items > 0 else [],
                "payment": {
                    "mode": "BANK_TRANSFER",
                    "instructions": "Transfer to bank account or use UPI"
                }
            }
        }

        headers = {
            "X-Provider": st.session_state.provider,
            "X-Model": st.session_state.model
        }

        with st.spinner("🤖 Generating invoice with AI..."):
            response, error = make_request("/v1/generate/invoice", method="POST", data=inv_payload, headers=headers)

            if error:
                st.error(f"❌ Error: {error}")
            elif response:
                st.markdown("### 📊 Response")
                display_response(response)

# Tab 3: Project Brief Generator
with tab3:
    st.markdown('<div class="section-header">Generate Project Brief</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 👤 Service Provider Information")
        pb_seller_name = st.text_input("Company Name*", value="Acme Solutions Pvt Ltd", key="pb_seller_name")
        pb_seller_email = st.text_input("Email*", value="projects@acmesolutions.in", key="pb_seller_email")
        pb_seller_phone = st.text_input("Phone*", value="+91-9800000000", key="pb_seller_phone")
        pb_seller_gstin = st.text_input("GSTIN", value="24ABCDE1234F1Z5", key="pb_seller_gstin")
        pb_seller_address = st.text_area(
            "Address*",
            value="401, Skyline Tech Park, City Light Road, Surat, Gujarat, 395007, India",
            key="pb_seller_address"
        )

    with col2:
        st.markdown("#### 🏢 Client Information")
        pb_buyer_name = st.text_input("Company Name*", value="Indigo Retail Pvt Ltd", key="pb_buyer_name")
        pb_buyer_email = st.text_input("Email*", value="ops@indigoretail.in", key="pb_buyer_email")
        pb_buyer_phone = st.text_input("Phone*", value="+91-9810000000", key="pb_buyer_phone")
        pb_buyer_gstin = st.text_input("GSTIN", value="27PQRSX1234A1Z2", key="pb_buyer_gstin")
        pb_buyer_address = st.text_area(
            "Address*",
            value="5th Floor, Horizon Plaza, Nariman Point, Mumbai, Maharashtra, 400021, India",
            key="pb_buyer_address"
        )

    st.markdown('<div class="section-header">Project Details</div>', unsafe_allow_html=True)

    col3, col4, col5 = st.columns(3)
    with col3:
        pb_currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP"], index=0, key="pb_currency")
        pb_issue_date = st.date_input("Issue Date", value=date.today(), key="pb_issue_date")
    with col4:
        pb_locale = st.selectbox("Locale", ["en-IN", "en-US", "en-GB"], index=0, key="pb_locale")
        pb_due_date = st.date_input("Project Start Date", value=date.today() + timedelta(days=7), key="pb_due_date")
    with col5:
        pb_valid_till = st.date_input("Valid Till", value=date.today() + timedelta(days=30), key="pb_valid_till")

    st.markdown('<div class="section-header">Project Requirement</div>', unsafe_allow_html=True)
    pb_requirement = st.text_area(
        "Describe the project in detail (AI will generate comprehensive brief)*",
        value="Comprehensive project brief for Indigo Retail's e-commerce revamp including phased rollout and success metrics.",
        height=150,
        key="pb_requirement",
        help="Include project goals, scope, deliverables, timeline expectations, and any specific requirements"
    )

    st.markdown('<div class="section-header">Engagement Terms</div>', unsafe_allow_html=True)

    pb_engagement_col1, pb_engagement_col2 = st.columns(2)
    with pb_engagement_col1:
        pb_payment_mode = st.selectbox(
            "Payment Mode",
            ["MILESTONE", "HOURLY", "FIXED_PRICE", "RETAINER"],
            index=0,
            key="pb_payment_mode"
        )
    with pb_engagement_col2:
        pb_payment_instructions = st.text_input(
            "Payment Instructions",
            value="Billing aligned to milestone completion",
            key="pb_payment_instructions"
        )

    st.markdown('<div class="section-header">Optional: Key Deliverables/Milestones</div>', unsafe_allow_html=True)

    pb_num_items = st.number_input("Number of deliverables", min_value=0, max_value=10, value=1, key="pb_num_items")

    pb_items = []
    for i in range(int(pb_num_items)):
        with st.expander(f"Deliverable {i+1}", expanded=(i==0)):
            pb_item_col1, pb_item_col2 = st.columns(2)
            with pb_item_col1:
                pb_desc = st.text_input("Description", value=f"Milestone {i+1}", key=f"pb_item_desc_{i}")
                pb_qty = st.number_input("Quantity", min_value=0.0, value=1.0, key=f"pb_item_qty_{i}")
            with pb_item_col2:
                pb_unit = st.text_input("Unit", value="lot", key=f"pb_item_unit_{i}")
                pb_unit_price = st.number_input("Estimated Value", min_value=0.0, value=0.0, key=f"pb_item_price_{i}")

            pb_items.append({
                "description": pb_desc,
                "qty": pb_qty,
                "unit": pb_unit,
                "unit_price": pb_unit_price,
                "discount": 0,
                "tax_rate": 0,
                "hsn_sac": ""
            })

    st.markdown("---")

    if st.button("🚀 Generate Project Brief", type="primary", use_container_width=True, key="gen_pb_btn"):
        # Build request payload
        pb_payload = {
            "from": {
                "name": pb_seller_name,
                "email": pb_seller_email,
                "phone": pb_seller_phone,
                "gstin": pb_seller_gstin,
                "billing_address": {
                    "line1": pb_seller_address.split(',')[0] if ',' in pb_seller_address else pb_seller_address,
                    "city": "Surat",
                    "state": "Gujarat",
                    "country": "India"
                },
                "tax_prefs": {
                    "place_of_supply": "Gujarat",
                    "reverse_charge": False,
                    "e_invoice": False
                }
            },
            "to": {
                "name": pb_buyer_name,
                "email": pb_buyer_email,
                "phone": pb_buyer_phone,
                "gstin": pb_buyer_gstin,
                "billing_address": {
                    "line1": pb_buyer_address.split(',')[0] if ',' in pb_buyer_address else pb_buyer_address,
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "country": "India"
                },
                "place_of_supply": "Maharashtra"
            },
            "currency": pb_currency,
            "locale": pb_locale,
            "requirement": pb_requirement,
            "hints": {
                "doc_meta": {
                    "doc_no": "",
                    "po_no": "",
                    "ref_no": ""
                },
                "dates": {
                    "issue_date": pb_issue_date.isoformat(),
                    "due_date": pb_due_date.isoformat(),
                    "valid_till": pb_valid_till.isoformat()
                },
                "items": pb_items if pb_num_items > 0 else [],
                "terms": {
                    "title": "Engagement Notes",
                    "bullets": [
                        "Weekly progress reviews",
                        "Final acceptance on UAT sign-off"
                    ]
                },
                "payment": {
                    "mode": pb_payment_mode,
                    "instructions": pb_payment_instructions,
                    "upi_deeplink": ""
                }
            }
        }

        headers = {
            "X-Provider": st.session_state.provider,
            "X-Model": st.session_state.model
        }

        with st.spinner("🤖 Generating project brief with AI..."):
            response, error = make_request("/v1/generate/project-brief", method="POST", data=pb_payload, headers=headers)

            if error:
                st.error(f"❌ Error: {error}")
            elif response:
                st.markdown("### 📊 Response")
                display_response(response)

# Tab 4: View Last Response
with tab4:
    st.markdown('<div class="section-header">Last API Response</div>', unsafe_allow_html=True)
    
    if st.session_state.last_response:
        st.json(st.session_state.last_response)
        
        # Download button
        json_str = json.dumps(st.session_state.last_response, indent=2)
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name=f"brief2bill_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    else:
        st.info("No response yet. Generate a document to see the response here.")

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #7f8c8d; padding: 1rem;">'
    '📄 Brief2Bill - AI-Powered Document Generation | '
    f'Connected to: {st.session_state.api_url}'
    '</div>',
    unsafe_allow_html=True
)

