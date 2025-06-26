from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import streamlit as st
# Load credentials from a service account JSON file
SERVICE_ACCOUNT_FILE = os.path.join("backend", "credentials.json")  # 🔐 put your actual JSON here

def get_calendar_service():
    credentials = service_account.Credentials.from_service_account_info({
        "type": "service_account",
        "client_email": st.secrets["GOOGLE_CALENDAR_CLIENT_EMAIL"],
        "private_key": st.secrets["GOOGLE_CALENDAR_PRIVATE_KEY"],
        "token_uri": "https://oauth2.googleapis.com/token"
    }, scopes=["https://www.googleapis.com/auth/calendar"])

    return build("calendar", "v3", credentials=credentials)

