import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from calendar_service import CalendarService
from agent import AppointmentBookingAgent
from datetime import datetime, timedelta

load_dotenv()

app = FastAPI(title="Appointment Booking AI API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
calendar_service = CalendarService(
    credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    calendar_id=os.getenv("CALENDAR_ID")
)

agent = AppointmentBookingAgent(
    calendar_service=calendar_service,
    gemini_api_key=os.getenv("GEMINI_API_KEY")
)

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.get("/")
async def root():
    return {"message": "Appointment Booking AI API is running!"}

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Handle chat messages"""
    try:
        response = agent.chat(message.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
