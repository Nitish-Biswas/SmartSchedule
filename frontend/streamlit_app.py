import streamlit as st
import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL")

# ---------- Page config ----------
st.set_page_config(page_title="AI Appointment Booking",
                   page_icon="📅", layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
.main-header {
    text-align: center;
    padding: 2rem 0;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    color: white;
    margin-bottom: 2rem;
    border-radius: 10px;
}

.chat-container {
    max-height: 500px;
    overflow-y: auto;
    padding: 1rem;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    background-color: #f8f9fa;
}

.user-message {
    background-color: #007bff;
    color: white;
    padding: 10px 15px;
    border-radius: 18px;
    margin: 5px 0;
    margin-left: 20%;
    text-align: right;
}

.bot-message {
    background-color: #e9ecef;
    color: #333;
    padding: 10px 15px;
    border-radius: 18px;
    margin: 5px 0;
    margin-right: 20%;
}

.stButton > button {
    width: 100%;
    background-color: #007bff;
    color: white;
    border: none;
    padding: 10px;
    border-radius: 5px;
    font-weight: bold;
}

.stButton > button:hover {
    background-color: #0056b3;
}
</style>

""", unsafe_allow_html=True)

# ---------- Session state ----------
st.session_state.setdefault("messages", [])

# ---------- Helper -----------
def send_message(user_text: str) -> None:
    """Append user message, hit backend, append bot reply."""
    st.session_state.messages.append({"role": "user", "content": user_text})

    try:
        resp = requests.post(f"{BACKEND_URL}/chat",
                             json={"message": user_text},
                             timeout=30)
        if resp.status_code == 200:
            bot_text = resp.json().get("response", "")
        else:
            bot_text = f"Error: {resp.status_code} - {resp.text}"
    except requests.exceptions.RequestException as e:
        bot_text = f"Connection error: {e}"
    except Exception as e:
        bot_text = f"Unexpected error: {e}"

    st.session_state.messages.append({"role": "bot", "content": bot_text})

# ---------- Header ----------
st.markdown("""
<div class="main-header">
  <h1>🤖 AI Appointment Booking Assistant</h1>
  <p>Chat with me to book appointments on your Google Calendar!</p>
</div>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### 📋 How to Use")
    st.markdown("""
    1. **Start a conversation** by typing your message
    2. **Ask about availability** for specific dates
    3. **Request to book** an appointment
    4. **Confirm details** when prompted
    
    ### 💡 Example Queries:
    - "Check availability for today"
    - "Book a meeting tomorrow at 2 PM"
    - "What slots are available on 12-07-2025?"
    - "Schedule a doctor appointment next Monday"
    - "I am planning to meet my friends today"
    """)

    st.markdown("### 🔧 System Status")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            st.success("✅ Backend Connected")
        else:
            st.error("❌ Backend Error")
    except:
        st.error("❌ Backend Offline")

# ---------- Chat history ----------
chat_container = st.container()
for m in st.session_state.messages:
    if m["role"] == "user":
        chat_container.markdown(f'<div class="user-message">{m["content"]}</div>',
                                unsafe_allow_html=True)
    else:
        chat_container.markdown(f'<div class="bot-message">{m["content"]}</div>',
                                unsafe_allow_html=True)

# ---------- Input area ----------
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input(
        "Type your message here...",
        key="user_input",
        placeholder="e.g., 'Check availability for tomorrow' or 'Book a meeting at 2 PM'"
    )
    submitted = st.form_submit_button("Send 📤")

if submitted and user_input:
    with st.spinner("🤔 AI is thinking..."):
        send_message(user_input)
    st.rerun()   # show the reply immediately

# ---------- Quick actions ----------
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📅 Check Today's Availability"):
        send_message("Check availability for today")
        st.rerun()

with col2:
    if st.button("🔄 Check Tomorrow's Availability"):
        send_message("Check availability for tomorrow")
        st.rerun()

with col3:
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages.clear()
        st.rerun()


CALENDAR_URL = "https://calendar.google.com/calendar/u/0?cid=YzI5MzFiM2U1M2Y4YTFiMDI1ZWI5MjM5MmM0N2UzZjI1MTI5ZWZhNjdkN2FjNmNhZjU0OGMwYmIyYzdkYTk0NUBncm91cC5jYWxlbmRhci5nb29nbGUuY29t"

# 📆 Open Calendar button (full width)
st.markdown("<br>", unsafe_allow_html=True)

st.markdown(f"""
<a href="{CALENDAR_URL}" target="_blank">
    <button style='width: 100%;
                   padding: 12px 0;
                   font-size: 16px;
                   border: none;
                   border-radius: 5px;
                   background-color: #007bff;
                   color: white;
                   font-weight: bold;
                   cursor: pointer;'>
        📆 Open Calendar
    </button>
</a>
""", unsafe_allow_html=True)

# ---------- Footer ----------
st.markdown("""
---
<div style="text-align: center; color: #666; padding: 1rem; font-size: 15px;">

  <p style="font-size: 16px;">
    <strong>Built by</strong> 
    <img src="https://avatars.githubusercontent.com/u/87754699?v=4" 
         style="height: 1.5em; vertical-align: middle; border-radius: 50%; margin: 0 5px;">
    <strong>Nitish Biswas</strong>
  </p>

  <p>
    <img src="https://img.icons8.com/ios-filled/20/phone.png" style="vertical-align: middle;"/> +91-8979053318 &nbsp;|&nbsp;
    <img src="https://img.icons8.com/ios-filled/20/email.png" style="vertical-align: middle;"/> <a href="mailto:nitishbiswas066@gmail.com">nitishbiswas066@gmail.com</a> &nbsp;|&nbsp;
    <img src="https://img.icons8.com/ios-filled/20/linkedin.png" style="vertical-align: middle;"/> <a href="https://www.linkedin.com/in/nitish-biswas1/" target="_blank">LinkedIn</a> &nbsp;|&nbsp;
    <img src="https://img.icons8.com/ios-filled/20/github.png" style="vertical-align: middle;"/> <a href="https://github.com/Nitish-Biswas" target="_blank">GitHub</a> &nbsp;|&nbsp;
  </p>

</div>
""", unsafe_allow_html=True)


