import io  
import smtplib  
import re
from email.mime.application import MIMEApplication  
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText

import pandas as pd  
import pdfplumber  
from pypdf import PdfReader, PdfWriter  
import streamlit as st

# 1. Page Configuration
st.set_page_config(  
    page_title="U.S. Embassy Cairo - Payroll Dispatcher",  
    layout="wide",  
    initial_sidebar_state="expanded",  
)

# 2. Complete CSS matching U.S. Embassy Presentation & Mockup exactly
st.markdown(  
    """  
    <style>  
    :root {  
        --embassy-navy: #0B2238;  
        --embassy-red: #A61C1E;  
        --embassy-gold: #C5A059;  
        --embassy-bg: #F8F9FA;  
    }  
     
    .stApp {  
        background-color: #F8F9FA;  
    }  
     
    /* Sidebar Dark Navy Styling */
    [data-testid="stSidebar"] {  
        background-color: #0B2238 !important;  
        padding-top: 2rem;
    }  

    [data-testid="stSidebar"] * {
        color: #FFFFFF;
    }

    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* Keep input fields readable with white background and dark text */
    [data-testid="stSidebar"] input {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        border-radius: 6px !important;
        border: 1px solid #CBD5E1 !important;
    }

    [data-testid="stSidebar"] input::placeholder {
        color: #94A3B8 !important;
    }

    /* Force Sidebar collapse/expand button to be visible */
    [data-testid="collapsedControl"] {
        display: block !important;
        color: #0B2238 !important;
    }

    /* Quick Guide Box Styling */
    .guide-box {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 8px;
        padding: 16px;
        font-size: 13.5px;
        line-height: 1.6;
        color: #E2E8F0;
    }

    /* Top Navy Banner */
    .header-box {  
        background-color: #0B2238;  
        color: white;  
        padding: 24px 15px;  
        border-radius: 8px;  
        text-align: center;  
        border-bottom: 3.5px solid #A61C1E;  
        box-shadow: 0px 4px 14px rgba(11, 34, 56, 0.08);  
        margin-bottom: 35px;  
    }  
     
    .header-title {  
        font-size: 22px;  
        font-weight: 800;  
        letter-spacing: 1.5px;  
        margin-bottom: 6px;  
        color: #FFFFFF;  
    }  
     
    .header-subtitle {  
        font-size: 13.5px;  
        color: #C5A059;  
        font-weight: 500;  
    }  

    /* Step Section Titles */
    .section-title {
        font-size: 18px;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 8px;
    }

    /* Red Dispatch Button matching design */
    .stButton > button {  
        background-color: #A61C1E !important;  
        color: #FFFFFF !important;  
        font-weight: 600 !important;  
        font-size: 15px !important;
        border-radius: 6px !important;  
        padding: 10px 24px !important;  
        border: none !important;  
        box-shadow: 0 3px 6px rgba(166, 28, 30, 0.25) !important;  
        transition: all 0.2s ease !important;  
        width: auto !important;  
        min-width: 250px;
    }  
     
    .stButton > button:hover {  
        background-color: #881517 !important;  
        transform: translateY(-1px);  
    }  
     
    /* Footer Styling */
    .custom-footer {  
        text-align: center;  
        padding: 25px 10px 10px 10px;  
        color: #475569;  
        font-size: 12px;  
        margin-top: 50px;  
        border-top: 1px solid #E2E8F0;
    }  
    </style>  
    """,  
    unsafe_allow_html=True,  
)

# 3. Sidebar (Authentication & Guide) Exactly as in the design
with st.sidebar:
    st.markdown("## Authentication")
    st.markdown(
        "<p style='font-size: 13px; color: #CBD5E1; margin-bottom: 20px;'>"
        "Enter official credentials to enable SMTP dispatch."
        "</p>", 
        unsafe_allow_html=True
    )

    sender_email = st.text_input(  
        "Sender Gmail Address", 
        placeholder="e.g. hr-payroll@embassy.gov"  
    )  
    app_password = st.text_input(  
        "Google App Password (16 digits)",  
        type="password",  
        placeholder="•••• •••• •••• ••••"  
    )

    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    st.markdown("### Quick Guide")
    
    st.markdown(
        """
        <div class="guide-box">
            1. Fill in your Gmail and App Password.<br>
            2. Upload the Master Payroll PDF.<br>
            3. Upload the Employee Mapping Sheet (Excel/CSV).<br>
            4. Click Start Dispatch.
        </div>
        """,
        unsafe_allow_html=True
    )

# 4. Main Section - Banner
st.markdown(  
    """  
    <div class="header-box">  
        <div class="header-title">U.S. EMBASSY CAIRO</div>  
        <div class="header-subtitle">Automated Individual Payroll Statements Dispatch System</div>  
    </div>  
    """,  
    unsafe_allow_html=True,  
)

# 5. Main Section - Two Columns for Uploads
col1, col2 = st.columns(2)

with col1:  
    st.markdown('<div class="section-title">1. Master Payroll PDF</div>', unsafe_allow_html=True)  
    uploaded_pdf = st.file_uploader(  
        "Upload multi-page Payroll PDF", 
        type=["pdf"],
        help="Upload the comprehensive unseparated PDF payroll document"
    )

with col2:  
    st.markdown('<div class="section-title">2. Employee Mapping Sheet</div>', unsafe_allow_html=True)  
    uploaded_mapping = st.file_uploader(  
        "Upload Excel or CSV mapping file", 
        type=["xlsx", "csv"],
        help="Upload the Excel or CSV containing Reference Numbers and Emails"
    )

st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

# 6. Dispatch Button & Zero Storage In-Memory Processing
if st.button("Start Payroll Dispatch Process"):  
    if not sender_email or not app_password:  
        st.error("Authentication required: Please enter both Sender Email and App Password in the sidebar.")  
    elif not uploaded_pdf or not uploaded_mapping:  
        st.error("Missing files: Please upload both the Master Payroll PDF and Employee Mapping Sheet.")  
    else:  
        try:  
            status_box = st.status("Processing in-memory dispatch...", expanded=True)
            status_box.write("Parsing employee mapping sheet...")

            if uploaded_mapping.name.endswith(".csv"):  
                mapping_df = pd.read_csv(uploaded_mapping)  
            else:  
                mapping_df = pd.read_excel(uploaded_mapping)

            mapping_df.columns = [str(c).strip() for c in mapping_df.columns]

            # Dynamic column identification
            ref_col = [c for c in mapping_df.columns if any(k in c.lower() for k in ["ref", "id", "number", "رقم", "مرجعي"])]  
            email_col = [c for c in mapping_df.columns if any(k in c.lower() for k in ["email", "mail", "إيميل", "بريد"])]  
            name_col = [c for c in mapping_df.columns if any(k in c.lower() for k in ["name", "اسم", "employee"])]

            if not ref_col or not email_col:  
                st.error("Could not auto-detect Reference Number and Email columns. Please review the sheet headers.")  
                st.stop()

            ref_key = ref_col[0]  
            email_key = email_col[0]  
            name_key = name_col[0] if name_col else None

            mapping_dict = {}  
            for _, row in mapping_df.iterrows():  
                ref_val = str(row[ref_key]).strip()  
                email_val = str(row[email_key]).strip()  
                emp_name = str(row[name_key]).strip() if name_key and pd.notna(row[name_key]) else "Colleague"  
                if ref_val and ref_val.lower() != 'nan':  
                    mapping_dict[ref_val] = {"email": email_val, "name": emp_name}

            status_box.write("Connecting securely via Google SMTP TLS...")
            server = smtplib.SMTP("smtp.gmail.com", 587)  
            server.starttls()  
            server.login(sender_email.strip(), app_password.strip().replace(" ", ""))

            pdf_bytes = uploaded_pdf.read()  
            reader = PdfReader(io.BytesIO(pdf_bytes))

            progress_bar = st.progress(0)  
            sent_count = 0  
            unmatched_pages = []

            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:  
                total_pages = len(pdf.pages)

                for index, page in enumerate(pdf.pages):  
                    extracted_text = page.extract_text() or ""

                    matched_ref = None  
                    matched_data = None

                    # In-memory exact and word-boundary reference matching
                    for ref_num, data in mapping_dict.items():  
                        if re.search(r'\b' + re.escape(ref_num) + r'\b', extracted_text) or (ref_num in extracted_text):  
                            matched_ref = ref_num  
                            matched_data = data  
                            break

                    if not matched_ref or not matched_data["email"]:  
                        unmatched_pages.append(index + 1)
                        continue

                    recipient_email = matched_data["email"]  
                    emp_name = matched_data["name"]

                    # Extract single page cleanly in memory (Zero Storage)
                    writer = PdfWriter()  
                    writer.add_page(reader.pages[index])

                    out_pdf_bytes = io.BytesIO()  
                    writer.write(out_pdf_bytes)  
                    out_pdf_bytes.seek(0)

                    msg = MIMEMultipart()  
                    msg["From"] = f"U.S. Embassy Cairo HR <{sender_email}>"  
                    msg["To"] = recipient_email  
                    msg["Subject"] = f"Official Payroll Statement - Ref: {matched_ref}"

                    body = (  
                        f"Dear {emp_name},\n\n"
                        f"Please find attached your official U.S. Embassy Cairo Payroll Statement for Reference Number: {matched_ref}.\n\n"
                        f"Best regards,\n"
                        f"Human Resources Department\n"
                        f"U.S. Embassy Cairo"  
                    )  
                    msg.attach(MIMEText(body, "plain"))

                    attachment = MIMEApplication(  
                        out_pdf_bytes.read(),  
                        Name=f"Payroll_Statement_{matched_ref}.pdf",  
                    )  
                    attachment["Content-Disposition"] = f'attachment; filename="Payroll_Statement_{matched_ref}.pdf"'  
                    msg.attach(attachment)

                    server.send_message(msg)  
                    sent_count += 1
                    progress_bar.progress((index + 1) / total_pages)

            server.quit()
            status_box.update(label="Dispatch process finished!", state="complete", expanded=False)

            st.success("Payroll statements dispatched successfully.")  
            m1, m2, m3 = st.columns(3)  
            m1.metric("Total Pages Processed", total_pages)  
            m2.metric("Successfully Sent", sent_count)  
            m3.metric("Unmatched Pages", len(unmatched_pages))

            if unmatched_pages:
                st.warning(f"Unmatched page numbers: {unmatched_pages}")

        except Exception as e:  
            st.error(f"Process failed: {str(e)}")

# 7. Footer exactly as in the design
st.markdown(  
    """  
    <div class="custom-footer">  
        © 2026 American Embassy Payroll Statements. All Rights Reserved.<br>
        Confidential & Internal Use Only.
    </div>  
    """,  
    unsafe_allow_html=True,  
)