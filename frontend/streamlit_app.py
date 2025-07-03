import streamlit as st
import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL")

# Page config
st.set_page_config(
    page_title="AI Appointment Booking",
    page_icon="📅",
    layout="wide"
)

# Custom CSS
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

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Header
st.markdown("""
<div class="main-header">
    <h1>🤖 AI Appointment Booking Assistant</h1>
    <p>Chat with me to book appointments on your Google Calendar!</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with instructions
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
    - "What slots are available on 2024-02-15?"
    - "Schedule a doctor appointment next Monday"
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

# Main chat interface
st.markdown("### 💬 Chat with AI Assistant")

# Display chat history
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-message">{message["content"]}</div>', unsafe_allow_html=True)

# Chat input
col1, col2 = st.columns([4, 1])

with col1:
    user_input = st.text_input(
        "Type your message here...",
        key="user_input",
        placeholder="e.g., 'Check availability for tomorrow' or 'Book a meeting at 2 PM'"
    )

with col2:
    send_button = st.button("Send 📤", key="send_button")

# Handle user input
if send_button and user_input:
    
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    
    with st.spinner("🤔 AI is thinking..."):
        try:
            # Call backend API
            response = requests.post(
                f"{BACKEND_URL}/chat",
                json={"message": user_input},
                timeout=30
            )
            
            if response.status_code == 200:
                bot_response = response.json()["response"]
                st.session_state.messages.append({"role": "bot", "content": bot_response})
            else:
                error_msg = f"Error: {response.status_code} - {response.text}"
                st.session_state.messages.append({"role": "bot", "content": error_msg})
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Connection error: {str(e)}"
            st.session_state.messages.append({"role": "bot", "content": error_msg})
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            st.session_state.messages.append({"role": "bot", "content": error_msg})
    

    st.rerun()


st.markdown("### ⚡ Quick Actions")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📅 Check Today's Availability"):
        st.session_state.messages.append({"role": "user", "content": "Check availability for today"})
        st.rerun()

with col2:
    if st.button("🔄 Check Tomorrow's Availability"):
        st.session_state.messages.append({"role": "user", "content": "Check availability for tomorrow"})
        st.rerun()

with col3:
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🚀 Built with FastAPI, LangGraph, and Streamlit | 
    📅 Powered by Google Calendar API | 
    🤖 AI by Google Gemini</p>
</div>
""", unsafe_allow_html=True)