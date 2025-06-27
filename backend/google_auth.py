from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import streamlit as st
# Load credentials from a service account JSON file
# SERVICE_ACCOUNT_FILE = os.path.join("backend", "credentials.json")  # put your actual JSON here

def get_calendar_service():
    credentials = service_account.Credentials.from_service_account_info({
        "type": "service_account",
        # "project_id": "your-project-id",  # optional
        # "private_key_id": "dummy-key-id",  # optional
        "private_key": st.secrets["GOOGLE_CALENDAR_PRIVATE_KEY"].replace("\\n", "\n"),
        "client_email": st.secrets["GOOGLE_CALENDAR_CLIENT_EMAIL"],
        # "client_id": "dummy-client-id",  # optional
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{st.secrets['GOOGLE_CALENDAR_CLIENT_EMAIL'].replace('@', '%40')}"
    }, scopes=["https://www.googleapis.com/auth/calendar"])

    service = build("calendar", "v3", credentials=credentials)
    return service
