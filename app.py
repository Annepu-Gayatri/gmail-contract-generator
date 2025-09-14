import streamlit as st
import os
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from PyPDF2 import PdfReader
from docx import Document

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

st.title("📧 Gmail Email & Attachment Summarizer + Contract Generator")

# Step 1: Upload Google OAuth credentials
st.sidebar.header("Setup")
uploaded = st.sidebar.file_uploader("Upload your Google OAuth credentials.json", type="json")
if uploaded:
    with open("credentials.json", "wb") as f:
        f.write(uploaded.read())
    st.success("✅ credentials.json uploaded!")

# Step 2: Authenticate Gmail
if os.path.exists("credentials.json"):
    st.info("Click below to authenticate your Gmail account")
    if st.button("Authenticate"):
        flow = Flow.from_client_secrets_file(
            "credentials.json",
            scopes=SCOPES,
            redirect_uri="https://gmail-contract-generator.streamlit.app"  # <- update with your Streamlit URL later
        )
        auth_url, _ = flow.authorization_url(prompt="consent")
        st.write("Click this link to log in:", auth_url)
        code = st.text_input("Paste the authorization code here:")
        if code:
            flow.fetch_token(code=code)
            creds = flow.credentials
            st.session_state.creds = creds
            st.success("✅ Authentication successful!")

# Step 3: Fetch unread emails
if "creds" in st.session_state:
    service = build("gmail", "v1", credentials=st.session_state.creds)
    results = service.users().messages().list(
        userId="me", labelIds=["INBOX"], q="is:unread", maxResults=5
    ).execute()
    messages = results.get("messages", [])
    if messages:
        st.write(f"📩 Found {len(messages)} unread emails")
        for msg in messages:
            m = service.users().messages().get(userId="me", id=msg["id"]).execute()
            st.write("•", m.get("snippet"))

# Step 4: Placeholder for attachments, summarization, contract
st.write("Attachment download, summarization, and contract generation will go here")
