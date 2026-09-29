import io  
import smtplib  
import time
import re
from datetime import datetime
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

# 2. Embassy Brand CSS Styling (With Enhanced UX Placeholders)
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
     
    /* Sidebar Background */
    [data-testid="stSidebar"] {  
        background-color: #0B2238 !important;  
        padding-top: 1.5rem;
    }  

    /* Sidebar Headings and Labels */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {
        color: #FFFFFF !important;
    }

    /* Input Fields Styling (White Background + Dark Text) */
    [data-testid="stSidebar"] input {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
    }

    /* Fixed Placeholder Color to Light/Medium Gray for High Contrast & Clear UX */
    [data-testid="stSidebar"] input::placeholder {
        color: #64748B !important;
        opacity: 1 !important;
        font-weight: 400 !important;
    }

    /* Webkit & Mozilla vendor prefixes for cross-browser support */
    [data-testid="stSidebar"] input::-webkit-input-placeholder {
        color: #64748B !important;
        opacity: 1 !important;
    }
    [data-testid="stSidebar"] input::-moz-placeholder {
        color: #64748B !important;
        opacity: 1 !important;
    }

    [data-testid="collapsedControl"] {
        display: block !important;
        color: #0B2238 !important;
    }

    .guide-box {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 8px;
        padding: 14px;
        font-size: 13px;
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
        margin-bottom: 25px;  
    }  
     
    .header-title {  
        font-size: 24px;  
        font-weight: 800;  
        letter-spacing: 1.5px;  
        margin-bottom: 6px;  
        color: #FFFFFF;  
    }  
     
    .header-subtitle {  
        font-size: 14px;  
        color: #C5A059;  
        font-weight: 500;  
    }  

    .section-title {
        font-size: 17px;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 8px;
    }

    /* Red Dispatch Button */
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
    }  

    .stButton > button:hover {  
        background-color: #881517 !important;  
        transform: translateY(-1px);  
    }  

    .custom-footer {  
        text-align: center;  
        padding: 20px 10px;  
        color: #475569;  
        font-size: 12px;  
        margin-top: 40px;  
        border-top: 1px solid #E2E8F0;
    }  
    </style>  
    """,  
    unsafe_allow_html=True,  
)

# 3. Sidebar (Authentication & Settings)
with st.sidebar:
    st.markdown("## Authentication")
    st.markdown(
        "<p style='font-size: 12.5px; color: #CBD5E1; margin-bottom: 15px;'>"
        "Enter official credentials to enable SMTP dispatch."
        "</p>", 
        unsafe_allow_html=True
    )

    default_sender = st.secrets.get("GMAIL_USER", "") if hasattr(st, "secrets") else ""
    default_pass = st.secrets.get("GMAIL_PASS", "") if hasattr(st, "secrets") else ""

    sender_email = st.text_input(  
        "Sender Gmail Address", 
        value=default_sender,
        placeholder="e.g. hr-payroll@embassy.gov"  
    )  
    app_password = st.text_input(  
        "Google App Password (16 digits)",  
        value=default_pass,
        type="password",  
        placeholder="•••• •••• •••• ••••"  
    )

    st.markdown("---")
    st.markdown("### Execution Mode")
    dry_run = st.toggle(
        "Dry Run (Simulation Mode)", 
        value=False, 
        help="Simulate PDF splitting and employee matching without sending any actual emails."
    )
    
    st.markdown("---")
    st.markdown("### Quick Guide")
    st.markdown(
        """
        <div class="guide-box">
            1. Fill in Gmail & App Password.<br>
            2. Upload Master PDF & Mapping Sheet.<br>
            3. Run <b>Dry Run</b> first to inspect matches.<br>
            4. Switch off Dry Run & Dispatch.
        </div>
        """,
        unsafe_allow_html=True
    )

# 4. Header Banner
st.markdown(  
    """  
    <div class="header-box">  
        <div class="header-title">U.S. EMBASSY CAIRO</div>  
        <div class="header-subtitle">Automated Individual Payroll Statements Dispatch System</div>  
    </div>  
    """,  
    unsafe_allow_html=True,  
)

# 5. File Upload Area
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
        help="Must contain columns for Reference Number and Email Address"
    )

st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

# 6. Email Subject & Template Settings (Visible on Main View)
st.markdown('<div class="section-title">✉️ Email Subject & Template Settings</div>', unsafe_allow_html=True)
email_col1, email_col2 = st.columns([1, 2])

with email_col1:
    email_subject = st.text_input(
        "Email Subject", 
        value="Official Payroll Statement - Ref: {ref}"
    )

with email_col2:
    email_body_template = st.text_area(
        "Email Body", 
        value="Dear {name},\n\nPlease find attached your official U.S. Embassy Cairo Payroll Statement for Reference Number: {ref}.\n\nBest regards,\nHuman Resources Department\nU.S. Embassy Cairo",
        height=95
    )

st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

# 7. Dispatch Button & Execution Logic
btn_label = "🔍 Run Matching Simulation (Dry Run)" if dry_run else "Start Payroll Dispatch Process"

if st.button(btn_label):  
    if not dry_run and (not sender_email or not app_password):  
        st.error("Authentication required: Please provide both Sender Email and App Password in the sidebar.")  
    elif not uploaded_pdf or not uploaded_mapping:  
        st.error("Missing files: Please upload both Master Payroll PDF and Employee Mapping Sheet.")  
    else:  
        try:
            status_box = st.status("Initializing payroll processing...", expanded=True)
            status_box.write("Reading employee mapping sheet...")

            if uploaded_mapping.name.endswith(".csv"):  
                mapping_df = pd.read_csv(uploaded_mapping)  
            else:  
                mapping_df = pd.read_excel(uploaded_mapping)

            mapping_df.columns = [str(c).strip() for c in mapping_df.columns]

            # Dynamic column detection
            ref_col = [c for c in mapping_df.columns if any(k in c.lower() for k in ["ref", "id", "number", "رقم", "مرجعي"])]  
            email_col = [c for c in mapping_df.columns if any(k in c.lower() for k in ["email", "mail", "إيميل", "بريد"])]  
            name_col = [c for c in mapping_df.columns if any(k in c.lower() for k in ["name", "اسم", "employee"])]

            if not ref_col or not email_col:  
                st.error("Failed to detect Reference ID and Email columns automatically. Please verify column headers.")  
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

            server = None
            if not dry_run:
                status_box.write("Connecting to Google SMTP (TLS)...")
                server = smtplib.SMTP("smtp.gmail.com", 587, timeout=25)  
                server.starttls()  
                server.login(sender_email.strip(), app_password.strip().replace(" ", ""))

            pdf_bytes = uploaded_pdf.read()  
            reader = PdfReader(io.BytesIO(pdf_bytes))
            progress_bar = st.progress(0)  

            audit_log = []
            sent_count = 0  
            unmatched_count = 0

            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:  
                total_pages = len(pdf.pages)

                for index, page in enumerate(pdf.pages):  
                    extracted_text = page.extract_text() or ""
                    matched_ref = None  
                    matched_data = None

                    # Strict boundary matching to eliminate collisions
                    for ref_num, data in mapping_dict.items():  
                        pattern = r'(?<!\d)' + re.escape(ref_num) + r'(?!\d)'
                        if re.search(pattern, extracted_text):  
                            matched_ref = ref_num  
                            matched_data = data  
                            break

                    timestamp_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    if not matched_ref or not matched_data["email"]:  
                        unmatched_count += 1
                        audit_log.append({
                            "Page": index + 1,
                            "Reference Number": "N/A",
                            "Employee Name": "N/A",
                            "Recipient Email": "N/A",
                            "Status": "Unmatched",
                            "Timestamp": timestamp_now,
                            "Notes": "Reference ID not found in page text"
                        })
                        progress_bar.progress((index + 1) / total_pages)
                        continue

                    recipient_email = matched_data["email"]  
                    emp_name = matched_data["name"]

                    if dry_run:
                        audit_log.append({
                            "Page": index + 1,
                            "Reference Number": matched_ref,
                            "Employee Name": emp_name,
                            "Recipient Email": recipient_email,
                            "Status": "Simulated Matched",
                            "Timestamp": timestamp_now,
                            "Notes": "Ready for dispatch"
                        })
                        sent_count += 1
                    else:
                        # Zero-Storage In-Memory extraction & Dispatch
                        writer = PdfWriter()  
                        writer.add_page(reader.pages[index])

                        out_pdf_bytes = io.BytesIO()  
                        writer.write(out_pdf_bytes)  
                        out_pdf_bytes.seek(0)

                        msg = MIMEMultipart()  
                        msg["From"] = f"U.S. Embassy Cairo HR <{sender_email}>"  
                        msg["To"] = recipient_email  
                        msg["Subject"] = email_subject.format(name=emp_name, ref=matched_ref)

                        body_content = email_body_template.format(name=emp_name, ref=matched_ref)
                        msg.attach(MIMEText(body_content, "plain"))

                        attachment = MIMEApplication(  
                            out_pdf_bytes.read(),  
                            Name=f"Payroll_Statement_{matched_ref}.pdf",  
                        )  
                        attachment["Content-Disposition"] = f'attachment; filename="Payroll_Statement_{matched_ref}.pdf"'  
                        msg.attach(attachment)

                        try:
                            server.send_message(msg)  
                            sent_count += 1
                            audit_log.append({
                                "Page": index + 1,
                                "Reference Number": matched_ref,
                                "Employee Name": emp_name,
                                "Recipient Email": recipient_email,
                                "Status": "Success",
                                "Timestamp": timestamp_now,
                                "Notes": "Delivered to SMTP queue"
                            })
                            time.sleep(0.3)
                        except Exception as send_err:
                            audit_log.append({
                                "Page": index + 1,
                                "Reference Number": matched_ref,
                                "Employee Name": emp_name,
                                "Recipient Email": recipient_email,
                                "Status": "Failed",
                                "Timestamp": timestamp_now,
                                "Notes": str(send_err)
                            })

                    progress_bar.progress((index + 1) / total_pages)

            if server:
                server.quit()

            status_box.update(label="Processing Finished!", state="complete", expanded=False)

            if dry_run:
                st.info("Simulation completed. Review matched pages below before live dispatch.")
            else:
                st.success("Payroll statement dispatch completed.")

            m1, m2, m3 = st.columns(3)  
            m1.metric("Total Pages", total_pages)  
            m2.metric("Matched / Sent" if not dry_run else "Matched (Simulated)", sent_count)  
            m3.metric("Unmatched Pages", unmatched_count)

            # Audit Table and Excel Download
            log_df = pd.DataFrame(audit_log)
            st.markdown("### Process Audit Trail")
            st.dataframe(log_df, use_container_width=True)

            log_output = io.BytesIO()
            with pd.ExcelWriter(log_output, engine='openpyxl') as writer:
                log_df.to_excel(writer, index=False, sheet_name="Dispatch_Log")
            log_output.seek(0)

            st.download_button(
                label="📥 Download Official Dispatch Audit Log (Excel)",
                data=log_output,
                file_name=f"Payroll_Dispatch_Audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:  
            st.error(f"Execution Encountered An Error: {str(e)}")

# 8. Footer Section
st.markdown(  
    """  
    <div class="custom-footer">  
        © 2026 American Embassy Payroll Statements. All Rights Reserved.<br>
        Confidential & Internal Use Only.
    </div>  
    """,  
    unsafe_allow_html=True,  
)