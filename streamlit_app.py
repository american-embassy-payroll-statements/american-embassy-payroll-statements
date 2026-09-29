import streamlit as st
import smtplib
import io
import pandas as pd
import pdfplumber
from pypdf import PdfWriter, PdfReader
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# 1. Page Configuration
st.set_page_config(
    page_title="U.S. Embassy Cairo - Payroll Dispatcher",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS Styling
st.markdown("""
    <style>
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    
    :root {
        --embassy-navy: #0B2238;
        --embassy-red: #A61C1E;
        --embassy-gold: #C5A059;
        --embassy-bg: #F8F9FA;
    }
     
    .stApp {
        background-color: #F4F6F8;
    }
     
    .header-box {
        background: linear-gradient(135deg, #0B2238 0%, #173753 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        text-align: center;
        border-bottom: 4px solid #A61C1E;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
        margin-bottom: 25px;
    }
     
    .header-title {
        font-size: 26px;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 5px;
        color: #FFFFFF !important;
    }
     
    .header-subtitle {
        font-size: 15px;
        color: #C5A059 !important;
        font-weight: 500;
    }
    
    /* Prominent Navy Titles for Web & Mobile */
    .navy-title {
        color: #0B2238 !important;
        font-size: 24px !important;
        font-weight: 800 !important;
        margin-top: 10px !important;
        margin-bottom: 16px !important;
        display: block !important;
        letter-spacing: 0.5px !important;
    }
     
    [data-testid="stSidebar"] {
        background-color: #0B2238;
        color: white;
    }
     
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }
     
    .stButton>button {
        background-color: #A61C1E !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 12px 28px !important;
        border: none !important;
        box-shadow: 0 4px 8px rgba(166, 28, 30, 0.3) !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
     
    .stButton>button:hover {
        background-color: #821416 !important;
        transform: translateY(-1px);
    }

    /* Custom Copyright Footer Bar */
    .custom-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0B2238;
        color: #FFFFFF;
        text-align: center;
        padding: 10px 0;
        font-size: 13px;
        font-weight: 500;
        letter-spacing: 0.5px;
        z-index: 9999;
        border-top: 2px solid #C5A059;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Header Section
st.markdown("""
    <div class="header-box">
        <div class="header-title">U.S. EMBASSY CAIRO</div>
        <div class="header-subtitle">Automated Individual Payroll Statements Dispatch System</div>
    </div>
""", unsafe_allow_html=True)

# 4. Sidebar Credentials Setup
with st.sidebar:
    st.title("Authentication")
    st.caption("Enter official credentials to enable SMTP dispatch.")
     
    sender_email = st.text_input("Sender Gmail Address", placeholder="e.g. hr-payroll@embassy.gov")
    app_password = st.text_input("Google App Password (16 digits)", type="password", placeholder="•••• •••• •••• ••••")
     
    st.markdown("---")
    st.markdown("### Quick Guide")
    st.info("""
    1. Fill in your Gmail and App Password.
    2. Upload the Master Payroll PDF.
    3. Upload the Employee Mapping Sheet (Excel/CSV).
    4. Click Start Dispatch.
    """)

# 5. Main Content Area (Enlarged Navy Titles)
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="navy-title">1. Master Payroll PDF</div>', unsafe_allow_html=True)
    uploaded_pdf = st.file_uploader("Upload multi-page Payroll PDF", type=["pdf"])

with col2:
    st.markdown('<div class="navy-title">2. Employee Mapping Sheet</div>', unsafe_allow_html=True)
    uploaded_mapping = st.file_uploader("Upload Excel or CSV mapping file", type=["xlsx", "csv"])

st.markdown("---")

# 6. Dispatch Processing Logic
if st.button("Start Payroll Dispatch Process", type="primary"):
    if not sender_email or not app_password:
        st.error("Please provide both Sender Email and Google App Password in the sidebar.")
    elif not uploaded_pdf or not uploaded_mapping:
        st.error("Please upload BOTH the Master Payroll PDF and the Employee Mapping Sheet.")
    else:
        server = None
        try:
            st.info("Reading Mapping Sheet and Connecting to Gmail SMTP Server...")
             
            if uploaded_mapping.name.endswith('.csv'):
                mapping_df = pd.read_csv(uploaded_mapping)
            else:
                mapping_df = pd.read_excel(uploaded_mapping)
             
            mapping_df.columns = [str(c).strip() for c in mapping_df.columns]
             
            ref_col = [c for c in mapping_df.columns if any(k in c.lower() for k in ['ref', 'id', 'number', 'رقم', 'مرجعي'])]
            email_col = [c for c in mapping_df.columns if any(k in c.lower() for k in ['email', 'mail', 'إيميل', 'بريد'])]
            name_col = [c for c in mapping_df.columns if any(k in c.lower() for k in ['name', 'اسم', 'employee'])]
             
            if not ref_col or not email_col:
                st.error("Could not auto-detect Reference Number and Email columns. Please check your Excel/CSV headers.")
                st.stop()
                 
            ref_key = ref_col[0]
            email_key = email_col[0]
            name_key = name_col[0] if name_col else None
             
            mapping_dict = {}
            for _, row in mapping_df.iterrows():
                val = row[ref_key]
                if pd.notna(val):
                    ref_val = str(int(val)).strip() if isinstance(val, float) and val.is_integer() else str(val).strip()
                    email_val = str(row[email_key]).strip() if pd.notna(row[email_key]) else ""
                    emp_name = str(row[name_key]).strip() if name_key and pd.notna(row[name_key]) else "Employee"
                    if ref_val:
                        mapping_dict[ref_val] = {"email": email_val, "name": emp_name}
             
            pdf_bytes = uploaded_pdf.read()
            reader = PdfReader(io.BytesIO(pdf_bytes))
             
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, app_password)
             
            progress_bar = st.progress(0)
            status_text = st.empty()
             
            sent_count = 0
            failed_count = 0
             
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                total_pages = len(pdf.pages)
                 
                for index, page in enumerate(pdf.pages):
                    extracted_text = page.extract_text() or ""
                     
                    matched_ref = None
                    matched_data = None
                     
                    for ref_num, data in mapping_dict.items():
                        if ref_num in extracted_text:
                            matched_ref = ref_num
                            matched_data = data
                            break
                     
                    if not matched_ref or not matched_data or not matched_data["email"]:
                        st.warning(f"Page {index + 1}: No matching Reference Number found or missing email.")
                        failed_count += 1
                        continue
                     
                    recipient_email = matched_data["email"]
                    emp_name = matched_data["name"]
                     
                    writer = PdfWriter()
                    writer.add_page(reader.pages[index])
                     
                    out_pdf_bytes = io.BytesIO()
                    writer.write(out_pdf_bytes)
                    out_pdf_bytes.seek(0)
                     
                    msg = MIMEMultipart()
                    msg['From'] = f"U.S. Embassy Cairo HR <{sender_email}>"
                    msg['To'] = recipient_email
                    msg['Subject'] = f"Official Payroll Statement - Ref: {matched_ref}"
                     
                    body = f"Dear {emp_name},\n\nPlease find attached your official U.S. Embassy Cairo Payroll Statement for Reference Number: {matched_ref}.\n\nBest regards,\nHuman Resources Department\nU.S. Embassy Cairo"
                    msg.attach(MIMEText(body, 'plain'))
                     
                    attachment = MIMEApplication(out_pdf_bytes.read(), Name=f"Payroll_Statement_{matched_ref}.pdf")
                    attachment['Content-Disposition'] = f'attachment; filename="Payroll_Statement_{matched_ref}.pdf"'
                    msg.attach(attachment)
                     
                    server.send_message(msg)
                    sent_count += 1
                     
                    status_text.markdown(f"Page {index + 1}: Dispatched to {emp_name} ({recipient_email}) [Ref: {matched_ref}]")
                    progress_bar.progress((index + 1) / total_pages)
             
            st.markdown("---")
            st.success("Dispatch Completed Successfully.")
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Pages Processed", total_pages)
            m2.metric("Successfully Sent", sent_count)
            m3.metric("Unmatched Pages", failed_count)
             
        except Exception as e:
            st.error(f"Operation Failed: {str(e)}")
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass

# 7. Copyright Footer Bar
st.markdown("""
    <div class="custom-footer">
         © 2026 American Embassy Payroll Statements. All Rights Reserved.
         Confidential & Internal Use Only.

    </div>
""", unsafe_allow_html=True)