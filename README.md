# SmartSchedule


SmartSchedule is an AI-powered appointment booking assistant that integrates with Google Calendar. Users interact with a conversational interface to check availability and book appointments, powered by Gemini LLM and Google Calendar API.

---
## Check out the live project here: https://smartschedule-vyljaqblkun5wacwjhkhs4.streamlit.app/

## Features
- **Conversational AI:** Book and check appointments using natural language.
- **Google Calendar Integration:** Uses a service account for secure access.
- **Smart Suggestions:** Suggests suitable times, detects conflicts, and confirms bookings.
- **Modern UI:** Streamlit-based frontend for a seamless chat experience.

---

## Architecture
- **Backend:** FastAPI, LangChain, Gemini LLM, Google Calendar API
- **Frontend:** Streamlit (Python)
- **Communication:** REST API between frontend and backend

---

## Directory Structure
```
SmartSchedule/
├── backend/         # FastAPI backend, Google Calendar integration, AI agent
│   ├── app.py
│   ├── agent.py
│   ├── calendar_service.py
│   ├── requirements.txt
├── frontend/        # Streamlit frontend
│   ├── streamlit_app.py
│   ├── requirements.txt
├── credentials/     # Place your Google service account JSON here
│   └── service-account.json
```

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/Nitish-Biswas/SmartSchedule.git
cd SmartSchedule
```

### 2. Google Cloud Setup
- Create a Google Cloud project and enable the Google Calendar API.
- Create a **service account** and download the JSON key. Place it in `credentials/service-account.json`.
- Share your target Google Calendar with the service account email (with edit permissions).
- Get your **Calendar ID** from Google Calendar settings.

### 3. Environment Variables
Create a `.env` file in root directorie:

#### `.env`
```
GOOGLE_APPLICATION_CREDENTIALS=../credentials/service-account.json
CALENDAR_ID=your_calendar_id@group.calendar.google.com
GEMINI_API_KEY=your_gemini_api_key
BACKEND_URL="http://localhost:8000"  or "your backend url"
```



- `GEMINI_API_KEY`: Get from Google AI Studio (Gemini API access).

### 4. Install Dependencies

#### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Frontend
```bash
cd ../frontend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Run the Application

#### Start Backend (FastAPI)
```bash
cd backend
uvicorn app:app --reload
```

#### Start Frontend (Streamlit)
```bash
cd frontend
streamlit run streamlit_app.py
```

---

## Usage
- Open the Streamlit app in your browser (usually at `http://localhost:8501`).
- Start chatting! Example queries:
  - "Check availability for today"
  - "Book a meeting tomorrow at 2 PM"
  - "What slots are available on 2025-07-12?"
  - "Schedule a doctor appointment next Monday"
- The assistant will check your Google Calendar and help you book appointments.

---

## Dependencies
- **Backend:** fastapi, uvicorn, google-api-python-client, google-auth, langchain, langchain-google-genai, python-dotenv, pydantic, httpx, python-multipart, pytz
- **Frontend:** streamlit, requests, python-dotenv

---

## License
MIT License

---

## Acknowledgements
- [FastAPI](https://fastapi.tiangolo.com/)
- [Streamlit](https://streamlit.io/)
- [Google Calendar API](https://developers.google.com/calendar)
- [LangChain](https://python.langchain.com/)
- [Gemini LLM](https://ai.google.dev/)



