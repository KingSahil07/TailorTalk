from backend.calendar_utils import is_time_slot_available, book_meeting
import datetime

now = datetime.datetime.utcnow()
start_time = now + datetime.timedelta(days=1, hours=15)
end_time = start_time + datetime.timedelta(hours=1)
start_iso = start_time.isoformat() + 'Z'
end_iso = end_time.isoformat() + 'Z'

if is_time_slot_available(start_iso, end_iso):
    link = book_meeting("Test Meeting", start_iso, end_iso)
    print("Meeting booked:", link)
else:
    print("Time slot not available")
