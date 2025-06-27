# agent/langgraph_agent.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import datetime
import streamlit as st
from agent.langgraph_agent import get_langgraph_agent
from PIL import Image
import pytz
st.markdown(
    """
    <style>
        .stChatMessage {
            background-color: black;
            padding: 8px;
            border-radius: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True
)
if "pending_booking" not in st.session_state:
    st.session_state.pending_booking = None

# Set page config with logo icon
st.set_page_config(
    page_title="TailorTalk",
    page_icon="🧵",
    layout="centered"
)
# Load logo image
logo_path = os.path.join("frontend", "assets", "logo.jpeg")
if os.path.exists(logo_path):
    col1, col2 = st.columns([1, 9])  # Logo : Title ratio

    with col1:
        st.image(logo_path, width=50)

    with col2:
        st.markdown("""
            <div style='display: flex; align-items: center; height: 100%;'>
                <h1 style='margin-bottom: 0; font-size: 36px;'>TailorTalk</h1>
            </div>
        """, unsafe_allow_html=True)
    st.caption("Book your meetings using natural language!")
else:
    st.warning("Logo image not found.")


# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
agent = get_langgraph_agent()

# Display previous chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
if user_input := st.chat_input("What would you like to do?"):
    # st.session_state.messages.append({"role": "user", "content": user_input})
        # Show user's message in chat
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # ✅ Check if user is responding to a booking suggestion
    if st.session_state.get("pending_booking"):
        user_response = user_input.lower()

        if user_response in ["yes", "ya", "sure", "ok", "okay"]:
            booking = st.session_state.pending_booking
            from backend.calendar_utils import is_time_slot_available, book_meeting

            if is_time_slot_available(booking["start"], booking["end"]):
                link = book_meeting(booking["summary"], booking["start"], booking["end"])
                
                # Format datetime nicely
                start_dt = datetime.datetime.fromisoformat(booking["start"])
                ist = pytz.timezone("Asia/Kolkata")
                start_ist = start_dt.astimezone(ist)
                readable = start_ist.strftime("%A, %d %B %Y at %I:%M %p")

                response = f"✅ Booking confirmed for **{readable}**! [View on Calendar]({link})"
            else:
                response = "❌ That time slot just got booked. Try another one?"

            st.session_state.pending_booking = None
            st.chat_message("assistant").markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
            st.stop()


        elif user_response in ["no", "nope", "nah"]:
            response = "👍 Okay, I won't book that."
            st.session_state.pending_booking = None
            st.chat_message("assistant").markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
            st.stop()

    # 🟨 If it's not yes/no, continue to LangGraph agent

    # Agent processing
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = agent.invoke({
                "user_input": user_input,
                "intent": None,
                "datetime": None,
                "confirmed": False,
                "booking_link": None,
                "error": None
            })
            
            if result["intent"] == "check_availability":
                dt = result.get("datetime")
                if dt:
                    start_date = datetime.datetime.fromisoformat(dt["start"])
                    readable_date = start_date.strftime("%A, %d %B %Y")  # e.g. Sunday, 30 June 2025
                else:
                    readable_date = "that day"

                if result.get("availability"):
                    slots = result["availability"]
                    if len(slots) > 0:
                        first_slot = slots[0]
                        slot_lines = "\n".join([
                            f"{s.strftime('%I:%M %p')} - {e.strftime('%I:%M %p')}" for s, e in slots
                        ])

                        response = f"✅ You're free on **{readable_date}** at:\n\n{slot_lines}"
                        display_start = first_slot[0].strftime("%I:%M %p")  # e.g. 09:00 AM
                        display_end = first_slot[1].strftime("%I:%M %p")    # e.g. 10:00 AM
                        response += f"\n\n💡 Would you like me to book a meeting from {display_start} to {display_end}?"

                        # 🧠 Save suggestion for confirmation flow
                        slot_date = start_date.strftime("%Y-%m-%d")
                        start_time = first_slot[0].strftime("%H:%M:%S")
                        end_time = first_slot[1].strftime("%H:%M:%S")
                        # Combine date + time as full datetime strings
                        start_dt_str = f"{slot_date}T{start_time}"
                        end_dt_str = f"{slot_date}T{end_time}"

                        st.session_state.pending_booking = {
                            "start": start_dt_str,
                            "end": end_dt_str,
                            "summary": "TailorTalk Meeting"
                        }
                    else:
                        response = f"❌ You're fully booked on **{readable_date}**."
                else:
                    response = f"❌ I couldn't find availability for **{readable_date}**."

            elif result["intent"] == "book_meeting":
                if result["confirmed"]:
                    dt = result.get("datetime")
                    if dt:
                        start_date = datetime.datetime.fromisoformat(dt["start"])
                        ist = pytz.timezone("Asia/Kolkata")
                        start_ist = start_date.astimezone(ist)
                        readable_date = start_ist.strftime("%A, %B %d, %Y at %I:%M %p")
                    else:
                        readable_date = "the scheduled time"

                    response = f"✅ Booking confirmed for **{readable_date}**! [View on Calendar]({result['booking_link']})"
                
                elif result.get("error") == "Time slot unavailable.":
                    response = "⚠️ That time slot is already booked. Try a different time."

                elif result.get("error") == "No time detected.":
                    response = "🤖 I couldn't find a date/time in your message. Could you rephrase?"

                elif result.get("error") == "Calendar API failed.":
                    response = "❌ Something went wrong while accessing the calendar. Please try again."

                else:
                    response = "❌ Something went wrong while booking."

            else:
                response = "🤔 I'm not sure what you're asking. Try rephrasing your request."

            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
            # Display previous chat messages
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
