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

def is_time_slot_available(start: str, end: str) -> bool:
    service = get_calendar_service()

    # Convert to datetime objects
    start_dt = datetime.datetime.fromisoformat(start)
    end_dt = datetime.datetime.fromisoformat(end)

    # ✅ Ensure timezone-aware in UTC
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=pytz.UTC)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=pytz.UTC)

    start_time_iso = start_dt.isoformat()
    end_time_iso = end_dt.isoformat()

    print("Checking slot:", start_time_iso, "→", end_time_iso)

    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_time_iso,
        timeMax=end_time_iso,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    return len(events) == 0


def book_meeting(summary, start_time_iso, end_time_iso):
    service = get_calendar_service()
    event = {
        'summary': summary,
        'start': {
            'dateTime': start_time_iso,
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': end_time_iso,
            'timeZone': 'Asia/Kolkata',
        },
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    return event.get('htmlLink')
