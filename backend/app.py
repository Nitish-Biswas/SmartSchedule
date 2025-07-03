import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from calendar_service import CalendarService
from agent import AppointmentBookingAgent
from datetime import datetime, timedelta
from fastapi.responses import FileResponse, Response

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
@app.middleware("http")
async def log_requests(request: Request, call_next):
    ip = request.client.host
    method = request.method
    path = request.url.path
    print(f"👀 {ip} - {method} {path}")
    response = await call_next(request)
    return response

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
    
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")

@app.head("/")
async def root_head(request: Request):
    return Response(status_code=200)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)