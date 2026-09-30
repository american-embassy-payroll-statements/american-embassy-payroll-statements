import streamlit as st

st.set_page_config(
    page_title="U.S. Embassy Cairo - Payroll System",
    page_icon="🏛️",
    layout="wide"
)

st.markdown("""
<style>
    /* Force Light Mode & Disable Dark Theme Overrides */
    :root {
        color-scheme: light !important;
    }

    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #f8fafc !important;
        color: #1e293b !important;
    }

    /* Container Max-Width Settings (Centered Wide Layout) */
    .block-container {
        max-width: 1200px !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        margin: 0 auto !important;
    }

    /* Main Header Styling */
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        color: #ffffff;
        padding: 24px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 25px;
    }
    .main-header h1 {
        color: #ffffff !important;
        font-size: 26px;
        font-weight: 700;
        letter-spacing: 1px;
        margin: 0;
    }
    .main-header p {
        color: #93c5fd !important;
        font-size: 14px;
        margin-top: 6px;
        margin-bottom: 0;
    }

    /* Card Panels Styling */
    div[data-testid="stVerticalBlock"] > div {
        border-radius: 10px;
    }

    /* Input Fields & Text Areas */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }

    /* Primary Dispatch Button */
    .stButton > button {
        width: 100%;
        background-color: #1e3a8a !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #1e40af !important;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.25) !important;
        transform: translateY(-1px);
    }

    /* File Uploaders */
    div[data-testid="stFileUploader"] {
        background-color: #ffffff !important;
        border: 1px dashed #94a3b8 !important;
        border-radius: 10px !important;
        padding: 10px !important;
    }

    /* Footer Styling */
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

st.markdown("""
<div class="main-header">
    <h1>U.S. EMBASSY CAIRO</h1>
    <p>Automated Individual Payroll Statements Dispatch System</p>
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