import streamlit as st

st.set_page_config(
    page_title="U.S. Embassy Cairo - Payroll System",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Force Light Theme Globally */
    :root {
        color-scheme: light !important;
    }

    html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }

    /* Hide Streamlit Header, Main Menu, Footer, and Fork Button */
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    a[href*="github.com"], a[href*="fork"] {display: none !important;}

    /* Force Light Backgrounds on Inputs, Textareas, & Containers */
    input, textarea, select, div[role="listbox"], div[data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }

    /* Center Page Container & Fix Max Width */
    .block-container {
        max-width: 1100px !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        margin: 0 auto !important;
    }

    /* Main Embassy Header Styling */
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%) !important;
        padding: 25px !important;
        border-radius: 12px !important;
        text-align: center !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        margin-bottom: 25px !important;
    }

    /* Direct Styling for Title Text - Overriding Streamlit Defaults */
    .main-header-title {
        color: #FFFFFF !important;
        font-size: 28px !important;
        font-weight: 800 !important;
        letter-spacing: 1.5px !important;
        margin: 0 !important;
        padding: 0 !important;
        display: block !important;
    }

    .main-header-subtitle {
        color: #93c5fd !important;
        font-size: 14px !important;
        margin-top: 6px !important;
        margin-bottom: 0 !important;
        display: block !important;
    }

    /* Green Dispatch Button Styling */
    div.stButton > button {
        width: 100% !important;
        background-color: #16a34a !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button:hover {
        background-color: #15803d !important;
        box-shadow: 0 4px 12px rgba(22, 163, 74, 0.3) !important;
        transform: translateY(-1px);
    }
    div.stButton > button * {
        color: #ffffff !important;
    }

    /* File Uploader Light Force */
    div[data-testid="stFileUploader"] {
        background-color: #ffffff !important;
        border: 1px dashed #94a3b8 !important;
        border-radius: 10px !important;
        padding: 10px !important;
    }

    /* Custom Footer */
    .custom-footer {
        text-align: center;
        color: #64748b !important;
        font-size: 12px;
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Main Header Container
st.markdown("""
<div class="main-header">
    <span class="main-header-title">U.S. EMBASSY CAIRO</span>
    <span class="main-header-subtitle">Automated Individual Payroll Statements Dispatch System</span>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Authentication")
    sender_email = st.text_input("Sender Gmail Address", placeholder="e.g. hr-payroll@embassy.gov")
    app_password = st.text_input("Google App Password (16 digits)", type="password")
    
    st.subheader("Execution Mode")
    dry_run = st.checkbox("Dry Run (Simulation Mode)", value=True)
    
    st.subheader("Quick Guide")
    st.info("""
    1. Fill in Gmail & App Password.
    2. Upload Master PDF & Mapping Sheet.
    3. Run Dry Run first to inspect matches.
    4. Switch off Dry Run & Dispatch.
    """)

with col2:
    st.subheader("1. Upload multi-page Payroll PDF")
    pdf_file = st.file_uploader("Upload PDF file", type=["pdf"])
    
    st.subheader("2. Employee Mapping")
    mapping_file = st.file_uploader("Upload Excel or CSV mapping file", type=["xlsx", "csv"])
    
    st.subheader("Email Subject & Template Settings")
    email_subject = st.text_input("Email Subject", value="Official Payroll Statement - Ref: {ref}")
    email_body = st.text_area("Email Body Template", value="Dear {name},\n\nPlease find attached your official U.S. Embassy Cairo Payroll Statement for Reference Number: {ref}.\n\nBest regards,\nHuman Resources Department\nU.S. Embassy Cairo", height=150)
    
    if st.button("Start Payroll Dispatch Process"):
        st.success("Process started successfully.")

st.markdown("""
<div class="custom-footer">
    © 2026 American Embassy Payroll Statements. All Rights Reserved.<br>
    Confidential & Internal Use Only.
</div>
""", unsafe_allow_html=True)