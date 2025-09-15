import streamlit as st
import os
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from PyPDF2 import PdfReader
from docx import Document
import base64

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

st.set_page_config(page_title="Gmail Contract Generator", layout="wide")
st.title("📧 Gmail → Contract Generator")

# --- STEP 1: Upload Google OAuth credentials.json ---
st.sidebar.header("Setup")
uploaded = st.sidebar.file_uploader("Upload your Google OAuth credentials.json", type="json")
if uploaded:
    with open("credentials.json", "wb") as f:
        f.write(uploaded.read())
    st.sidebar.success("✅ credentials.json uploaded!")

# --- STEP 2: Authenticate Gmail ---
if os.path.exists("credentials.json"):
    if "creds" not in st.session_state:
        flow = Flow.from_client_secrets_file(
    "credentials.json",
    scopes=SCOPES,
    redirect_uri="https://gmail-contract-generator-dnsfvhdx9ver7ent5csome.streamlit.app/"
)

        auth_url, _ = flow.authorization_url(prompt="consent")
        st.sidebar.markdown(f"[🔑 Click here to login to Gmail]({auth_url})")
        code = st.sidebar.text_input("Paste Google authorization code here:")
        if code:
            flow.fetch_token(code=code)
            st.session_state.creds = flow.credentials
            st.sidebar.success("✅ Authentication successful!")

# --- STEP 3: Fetch Emails ---
if "creds" in st.session_state:
    service = build("gmail", "v1", credentials=st.session_state.creds)
    results = service.users().messages().list(
        userId="me", labelIds=["INBOX"], q="is:unread", maxResults=10
    ).execute()
    messages = results.get("messages", [])

    if messages:
        # Dropdown to select email
        email_map = {}
        for msg in messages:
            m = service.users().messages().get(userId="me", id=msg["id"]).execute()
            snippet = m.get("snippet", "No preview")
            email_map[snippet[:80]] = m
        selected = st.selectbox("📩 Select an email", list(email_map.keys()))

        chosen_email = email_map[selected]
        st.subheader("Email Content")
        st.write(chosen_email["snippet"])

        # --- STEP 4: Fetch attachments ---
        parts = chosen_email.get("payload", {}).get("parts", [])
        attachments_text = ""
        for part in parts:
            if part.get("filename"):
                att_id = part["body"].get("attachmentId")
                if att_id:
                    att = service.users().messages().attachments().get(
                        userId="me", messageId=chosen_email["id"], id=att_id
                    ).execute()
                    file_data = base64.urlsafe_b64decode(att["data"])
                    fname = part["filename"]

                    # Save and extract text if PDF/DOCX
                    with open(fname, "wb") as f:
                        f.write(file_data)
                    if fname.endswith(".pdf"):
                        reader = PdfReader(fname)
                        for page in reader.pages:
                            attachments_text += page.extract_text() + "\n"
                    elif fname.endswith(".docx"):
                        doc = Document(fname)
                        for para in doc.paragraphs:
                            attachments_text += para.text + "\n"

        # --- STEP 5: Generate contract ---
        if st.button("Generate Contract"):
            contract = Document()
            contract.add_heading("Generated Contract", 0)
            contract.add_paragraph("Email summary: " + chosen_email["snippet"])
            if attachments_text:
                contract.add_heading("Extracted from Attachments", level=1)
                contract.add_paragraph(attachments_text)
            output_file = "contract.docx"
            contract.save(output_file)

            with open(output_file, "rb") as f:
                st.download_button("⬇️ Download Contract", f, file_name="contract.docx")
