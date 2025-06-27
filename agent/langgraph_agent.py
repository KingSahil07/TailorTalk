import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from typing import TypedDict, Optional
from backend.calendar_utils import is_time_slot_available, book_meeting, get_calendar_service
import datetime

# Define conversation state
class AgentState(TypedDict):
    user_input: str
    intent: Optional[str]
    datetime: Optional[dict]
    confirmed: bool
    booking_link: Optional[str]
    error: Optional[str]
    availability: Optional[list]

# Node: Get Intent
def get_intent(state: AgentState) -> AgentState:
    user_input = state["user_input"].lower()

    if any(x in user_input for x in ["free time", "available", "availability", "do you have time", "do we have time", "have time", "is there time", "any time"]):
        intent = "check_availability"
    elif any(x in user_input for x in ["book", "schedule", "meeting", "call"]):
        intent = "book_meeting"
    else:
        intent = "unknown"

    print("Intent Detected:", intent)
    return {**state, "intent": intent}

from backend.calendar_utils import get_calendar_service
def fetch_availability(state: AgentState) -> AgentState:
    dt = state.get("datetime")
    if not dt:
        return {**state, "availability": [], "error": "No datetime provided."}

    # Assume user asked for that day (e.g., "this Friday")
    start_date = datetime.datetime.fromisoformat(dt["start"])
    end_of_day = start_date.replace(hour=23, minute=59)
    start_utc = start_date.astimezone(datetime.timezone.utc)
    end_utc = end_of_day.astimezone(datetime.timezone.utc)

    service = get_calendar_service()
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_utc.isoformat(),
        timeMax=end_utc.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    booked = [(e['start']['dateTime'], e['end']['dateTime']) for e in events if 'dateTime' in e['start']]

    # Example: you work 9 AM–6 PM
    working_start = start_date.replace(hour=9, minute=0)
    working_end = start_date.replace(hour=18, minute=0)

    free_slots = []
    current = working_start

    for s, e in booked:
        booked_start = datetime.datetime.fromisoformat(s)
        if current < booked_start:
            free_slots.append((current.time(), booked_start.time()))
        current = max(current, datetime.datetime.fromisoformat(e))

    if current < working_end:
        free_slots.append((current.time(), working_end.time()))

    print("🟢 Free slots:", free_slots)

    return {**state, "availability": free_slots}

# Note: Extract Date/Time (simplified, refine later)

# import dateparser
import re
from dateparser.search import search_dates
def get_time_for_part_of_day(text: str):
    if "morning" in text:
        return 9
    if "afternoon" in text:
        return 14
    if "evening" in text:
        return 18
    if "night" in text:
        return 20
    return 10  # default fallback

def extract_datetime(state: AgentState) -> AgentState:
    user_input = state.get("user_input", "")
    user_input_lower = user_input.lower()
    print("🧠 User Input:", user_input)
    hour = get_time_for_part_of_day(user_input_lower)

    # 1. Handle "next Monday" etc.
    match = re.search(r'\b(?:on|this)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', user_input_lower)

    if match:
        weekday_name = match.group(1).capitalize()
        weekday_index = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(weekday_name)

        today = datetime.datetime.now(datetime.timezone.utc)
        days_ahead = (weekday_index - today.weekday() + 7) % 7
        if days_ahead == 0:
            days_ahead = 7  # force next week

        next_weekday = today + datetime.timedelta(days=days_ahead)
        next_weekday = next_weekday.replace(hour=hour, minute=0)
        next_weekday = next_weekday.astimezone(datetime.timezone.utc)
        end_dt = next_weekday + datetime.timedelta(hours=1)

        print("📆 Overridden 'next <weekday>' match:", next_weekday)

        return {
            **state,
            "datetime": {
                "start": next_weekday.isoformat(),
                "end": end_dt.isoformat()
            }
        }
    
    # 2. Handle "next month"
    if "next month" in user_input_lower:
        today = datetime.datetime.now(datetime.timezone.utc)
        # Get first day of next month
        if today.month == 12:
            year = today.year + 1
            month = 1
        else:
            year = today.year
            month = today.month + 1

        first_day_next_month = datetime.datetime(year, month, 1, hour=hour, tzinfo=datetime.timezone.utc)
        end = first_day_next_month + datetime.timedelta(hours=1)

        print("📆 Overridden 'next month' match:", first_day_next_month)

        return {
            **state,
            "datetime": {
                "start": first_day_next_month.isoformat(),
                "end": end.isoformat()
            }
        }

    # 3. Handle just "next week"
    if "next week" in user_input_lower:
        today = datetime.datetime.now(datetime.timezone.utc)
        next_monday = today + datetime.timedelta(days=(7 - today.weekday()))  # Monday next week
        start = next_monday.replace(hour=hour, minute=0)
        start = start.astimezone(datetime.timezone.utc)
        end = start + datetime.timedelta(hours=1)

        print("📆 Defaulted to 'next week':", start)

        return {
            **state,
            "datetime": {
                "start": start.isoformat(),
                "end": end.isoformat()
            }
        }

    # 4. Fallback: use dateparser
    results = search_dates(
        user_input_lower,
        settings={
            'PREFER_DATES_FROM': 'future',
            'TIMEZONE': 'Asia/Kolkata',
            'RETURN_AS_TIMEZONE_AWARE': True,
        }
    )

    if results:
        parsed_dt = results[0][1]
        print("🔍 Parsed datetime:", parsed_dt)

        # Only override time if none was detected (i.e., defaulted to 00:00)
        if parsed_dt.hour == 0 and parsed_dt.minute == 0:
            parsed_dt = parsed_dt.replace(hour=hour, minute=0)


        end_dt = parsed_dt + datetime.timedelta(hours=1)
        start_utc = parsed_dt.astimezone(datetime.timezone.utc)
        end_utc = end_dt.astimezone(datetime.timezone.utc)

        return {
            **state,
            "datetime": {
                "start": start_utc.isoformat(),
                "end": end_utc.isoformat()
            }
        }

    print("❌ No datetime found.")
    return {**state, "datetime": None}


# Note: Confirm Booking
def confirm(state: AgentState) -> AgentState:
    dt = state.get("datetime")
    if not dt:
        print("⚠️ No datetime provided.")
        return {**state, "confirmed": False, "booking_link": None, "error": "No time detected."}

    start_iso = dt["start"]
    end_iso = dt["end"]

    try:
        if is_time_slot_available(start_iso, end_iso):
            link = book_meeting("TailorTalk Meeting", start_iso, end_iso)
            return {**state, "confirmed": True, "booking_link": link}
        else:
            return {**state, "confirmed": False, "booking_link": None, "error": "Time slot unavailable."}
    except Exception as e:
        print("❌ Google Calendar API Error:", str(e))
        return {**state, "confirmed": False, "booking_link": None, "error": "Calendar API failed."}

# Create LangGraph
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda

def get_langgraph_agent():
    workflow = StateGraph(AgentState)
    # Add all nodes
    workflow.add_node("get_intent", RunnableLambda(get_intent))
    workflow.add_node("extract_datetime", RunnableLambda(extract_datetime))
    workflow.add_node("confirm", RunnableLambda(confirm))
    workflow.add_node("fetch_availability", RunnableLambda(fetch_availability))
    # Set entry point
    workflow.set_entry_point("get_intent")
    # Direct intent -> datetime
    workflow.add_edge("get_intent", "extract_datetime")
    # After datetime is extracted:
    # - if it's a booking, go to confirm
    # - if it's a check_availability request, go to fetch_availability
    workflow.add_conditional_edges(
        "extract_datetime",
        lambda state: "fetch_availability" if state["intent"] == "check_availability" else "confirm"
    )
    # Terminal steps
    workflow.add_edge("confirm", END)
    workflow.add_edge("fetch_availability", END)

    return workflow.compile()

if __name__ == "__main__":
    agent = get_langgraph_agent()

    user_input = input("You: ")
    result = agent.invoke({
        "user_input": user_input,
        "intent": None,
        "datetime": None,
        "confirmed": False,
        "booking_link": None
    })
    print("\nFinal Agent State:", result)

    if result['confirmed']:
        print(f"✅ Booking Confirmed: {result['booking_link']}")
    else:
        print("❌ Could not confirm booking.")

def is_time_slot_available(start_time_iso, end_time_iso):
    service = get_calendar_service()
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_time_iso,
        timeMax=end_time_iso,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    if events:
        print("❗ Conflicting Events:")
        for event in events:
            print("📅", event.get("summary"), "→", event["start"].get("dateTime"))

    return len(events) == 0
