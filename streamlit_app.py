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
    page_title="U.S. Embassy Cairo - Payroll System",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Strict Custom Styling
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

# 3. Main Header Banner
st.markdown("""
<div class="main-header">
    <span class="main-header-title">U.S. EMBASSY CAIRO</span>
    <span class="main-header-subtitle">Automated Individual Payroll Statements Dispatch System</span>
</div>
""", unsafe_allow_html=True)

# 4. Main Two-Column Layout
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("Authentication")
    
    try:
        default_sender = st.secrets.get("GMAIL_USER", "")
        default_pass = st.secrets.get("GMAIL_PASS", "")
    except Exception:
        default_sender = ""
        default_pass = ""

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

    st.subheader("Execution Mode")
    dry_run = st.checkbox("Dry Run (Simulation Mode)", value=False)

    st.subheader("Quick Guide")
    st.info("""
    1. Fill in Gmail & App Password.
    2. Upload Master PDF & Mapping Sheet.
    3. Run Dry Run first to inspect matches.
    4. Switch off Dry Run & Dispatch.
    """)

with col2:
    st.subheader("1. Upload multi-page Payroll PDF")
    uploaded_pdf = st.file_uploader("Upload PDF file", type=["pdf"])

    st.subheader("2. Employee Mapping")
    uploaded_mapping = st.file_uploader("Upload Excel or CSV mapping file", type=["xlsx", "csv"])

    st.subheader("Email Subject & Template Settings")
    email_subject = st.text_input(
        "Email Subject",
        value="Official Payroll Statement - Ref: {ref}"
    )
    email_body_template = st.text_area(
        "Email Body Template",
        value="Dear {name},\n\nPlease find attached your official U.S. Embassy Cairo Payroll Statement for Reference Number: {ref}.\n\nBest regards,\nHuman Resources Department\nU.S. Embassy Cairo",
        height=150
    )

    btn_label = "🔍 Run Matching Simulation (Dry Run)" if dry_run else "Start Payroll Dispatch Process"
    dispatch_clicked = st.button(btn_label)

# 5. Execution & Dispatch Logic
if dispatch_clicked:
    clean_sender = sender_email.strip()
    clean_password = app_password.strip().replace(" ", "")

    if not dry_run and (not clean_sender or not clean_password):
        st.error("Authentication required: Please provide both Sender Email and App Password.")
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

            ref_col = [c for c in mapping_df.columns if any(k in c.lower() for k in ["ref", "id", "number"])]
            email_col = [c for c in mapping_df.columns if any(k in c.lower() for k in ["email", "mail"])]
            name_col = [c for c in mapping_df.columns if any(k in c.lower() for k in ["name", "employee"])]

            if not ref_col or not email_col:
                st.error("Failed to detect Reference ID and Email columns automatically. Please verify column headers in mapping file.")
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
                status_box.write("Connecting securely to Google SMTP (SSL Port 465)...")
                server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)
                server.login(clean_sender, clean_password)

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
                        writer = PdfWriter()
                        writer.add_page(reader.pages[index])

                        out_pdf_bytes = io.BytesIO()
                        writer.write(out_pdf_bytes)
                        out_pdf_bytes.seek(0)

                        msg = MIMEMultipart()
                        msg["From"] = f"U.S. Embassy Cairo HR <{clean_sender}>"
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
                st.success("Payroll statement dispatch completed successfully!")

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
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        except Exception as e:
            st.error(f"Execution Encountered An Error: {str(e)}")

# 6. Footer Section
st.markdown("""
<div class="custom-footer">
    © 2026 American Embassy Payroll Statements. All Rights Reserved.<br>
    Confidential & Internal Use Only.
</div>
""", unsafe_allow_html=True)