import os
import datetime
import pickle
import pytz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from backend.google_auth import get_calendar_service


# If modifying these scopes, delete the token.pickle file.
SCOPES = ['https://www.googleapis.com/auth/calendar']

# def get_credentials():
#     creds = None
#     token_path = "credentials/token.pickle"
#     creds_path = "credentials/credentials.json"

#     if os.path.exists(token_path):
#         with open(token_path, 'rb') as token:
#             creds = pickle.load(token)

#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
#             creds = flow.run_local_server(port=0)
#         with open(token_path, 'wb') as token:
#             pickle.dump(creds, token)

#     return creds

# def get_calendar_service():
#     creds = get_credentials()
#     return build('calendar', 'v3', credentials=creds)
# backend/calendar_utils.py

def is_time_slot_available(start: str, end: str, creds: Credentials) -> bool:
    service = build("calendar", "v3", credentials=creds)

    start_dt = datetime.datetime.fromisoformat(start)
    end_dt = datetime.datetime.fromisoformat(end)

    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=pytz.UTC)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=pytz.UTC)

    if end_dt <= start_dt:
        print("❌ Invalid time range.")
        return False

    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_dt.isoformat(),
        timeMax=end_dt.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    return len(events) == 0

def book_meeting(summary: str, start: str, end: str, creds: Credentials) -> str:
    service = build("calendar", "v3", credentials=creds)

    event = {
        'summary': summary,
        'start': {
            'dateTime': start,
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': end,
            'timeZone': 'Asia/Kolkata',
        },
    }

    created_event = service.events().insert(calendarId='primary', body=event).execute()
    print("📅 Event Created:", created_event)
    return created_event.get("htmlLink")
