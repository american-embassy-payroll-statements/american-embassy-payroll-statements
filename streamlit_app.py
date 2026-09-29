import streamlit as st
import pypdf
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import io

st.set_page_config(
    page_title="U.S. Embassy Cairo - Payroll Dispatch System",
    layout="wide",
    initial_sidebar_state="expanded"
)

hide_streamlit_style = """<style>
#MainMenu {visibility: hidden !important;}
header {visibility: hidden !important;}
footer {visibility: hidden !important;}
[data-testid="stToolbar"] {display: none !important;}
.stAppDeployButton {display: none !important;}
[data-testid="stAppDeployButton"] {display: none !important;}
[data-testid="stStatusWidget"] {display: none !important;}
div[class*="viewerBadge"] {display: none !important;}
div[class*="Profile"] {display: none !important;}
div[class*="stActionButton"] {display: none !important;}
div[data-testid="stBottom"] {display: none !important;}
iframe[title="streamlit_app"] {margin-bottom: -50px;}
#root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}
</style>"""

st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.sidebar.title("Authentication Panel")
sender_email = st.sidebar.text_input("Sender Email Address", placeholder="user@gmail.com")
app_password = st.sidebar.text_input("Google App Password", type="password", help="Enter 16 digit Google App Password")

st.sidebar.markdown("---")
st.sidebar.subheader("System Security Status")
st.sidebar.info("Zero Local Storage Active. All operations processed directly in memory.")

st.title("U.S. Embassy Cairo")
st.subtitle("Automated Individual Payroll Statements Dispatch System")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Step 1: Upload Master Payroll PDF")
    pdf_file = st.file_uploader("Select Master PDF File", type=["pdf"])

with col2:
    st.subheader("Step 2: Upload Reference Mapping File")
    mapping_file = st.file_uploader("Select Mapping Sheet (Excel or CSV)", type=["xlsx", "csv"])

st.markdown("---")

if st.button("Start Payroll Dispatch Process", type="primary"):
    if not sender_email or not app_password:
        st.error("Authentication Error: Please provide both Sender Email and App Password in the sidebar.")
    elif not pdf_file or not mapping_file:
        st.error("Input Error: Please upload both Master Payroll PDF and Reference Mapping File.")
    else:
        try:
            if mapping_file.name.endswith(".csv"):
                df_mapping = pd.read_csv(mapping_file)
            else:
                df_mapping = pd.read_excel(mapping_file)
            
            st.success("Files successfully validated. Starting automated dispatch sequence...")
            
            pdf_reader = pypdf.PdfReader(pdf_file)
            total_pages = len(pdf_reader.pages)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            success_count = 0
            failed_count = 0
            
            for index, row in df_mapping.iterrows():
                ref_number = str(row.get("Reference Number", "")).strip()
                target_email = str(row.get("Email Address", "")).strip()
                page_idx = int(row.get("Page Number", index + 1)) - 1
                
                if page_idx < total_pages:
                    pdf_writer = pypdf.PdfWriter()
                    pdf_writer.add_page(pdf_reader.pages[page_idx])
                    
                    pdf_buffer = io.BytesIO()
                    pdf_writer.write(pdf_buffer)
                    pdf_buffer.seek(0)
                    
                    msg = MIMEMultipart()
                    msg['From'] = sender_email
                    msg['To'] = target_email
                    msg['Subject'] = f"Official Payroll Statement - Reference {ref_number}"
                    
                    body_text = f"Dear Colleague,\n\nPlease find attached your official individual payroll statement.\n\nReference: {ref_number}\n\nBest regards,\nU.S. Embassy Cairo Payroll Department"
                    msg.attach(MIMEText(body_text, 'plain'))
                    
                    attachment = MIMEApplication(pdf_buffer.read(), _subtype="pdf")
                    attachment.add_header('Content-Disposition', 'attachment', filename=f"Payroll_Statement_{ref_number}.pdf")
                    msg.attach(attachment)
                    
                    try:
                        server = smtplib.SMTP('smtp.gmail.com', 587)
                        server.starttls()
                        server.login(sender_email, app_password)
                        server.send_message(msg)
                        server.quit()
                        success_count += 1
                    except Exception as email_err:
                        failed_count += 1
                
                current_progress = (index + 1) / len(df_mapping)
                progress_bar.progress(current_progress)
                status_text.text(f"Processing item {index + 1} of {len(df_mapping)}...")
            
            st.success(f"Dispatch Complete. Successfully sent: {success_count} | Failed: {failed_count}")
            
        except Exception as e:
            st.error(f"Processing Error: {str(e)}")