# backend/agent.py - Updated with better error handling
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from langchain.agents import Tool
from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage

class AppointmentBookingAgent:
    def __init__(self, calendar_service, gemini_api_key: str):
        self.calendar_service = calendar_service
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=gemini_api_key,
                temperature=0.7
            )
            print("✅ Gemini LLM initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing Gemini: {e}")
            raise
            
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent"""
        
        def check_availability(date_input: str) -> str:
            """Check availability for a specific date"""
            try:
                print(f"🔍 Checking availability for: {date_input}")
                
                # Simple date parsing
                if 'today' in date_input.lower():
                    date = datetime.now().date()
                elif 'tomorrow' in date_input.lower():
                    date = datetime.now().date() + timedelta(days=1)
                else:
                    try:
                        date = datetime.strptime(date_input, '%Y-%m-%d').date()
                    except:
                        return "Please provide a valid date in YYYY-MM-DD format, or use 'today' or 'tomorrow'."
                
                # Get available slots
                slots = self.calendar_service.suggest_time_slots(
                    date.isoformat() + 'T00:00:00Z'
                )
                
                if slots:
                    slot_text = "\n".join([f"- {slot['display']}" for slot in slots])
                    return f"Available time slots for {date}:\n{slot_text}"
                else:
                    return f"No available slots found for {date}. Please try another date."
                    
            except Exception as e:
                print(f"❌ Error in check_availability: {e}")
                return f"Sorry, I couldn't check availability. Error: {str(e)}"
        
        def book_appointment(appointment_details: str) -> str:
            """Book an appointment with given details"""
            try:
                print(f"📅 Booking appointment: {appointment_details}")
                
                # Simple JSON parsing
                try:
                    details = json.loads(appointment_details)
                except:
                    return "Please provide appointment details in proper format."
                
                result = self.calendar_service.create_event(
                    title=details.get('title', 'Appointment'),
                    start_time=details['start_time'],
                    end_time=details['end_time'],
                    description=details.get('description', '')
                )
                
                if result['success']:
                    return f"✅ Appointment '{details.get('title', 'Appointment')}' booked successfully!"
                else:
                    return f"❌ Failed to book appointment: {result['message']}"
                    
            except Exception as e:
                print(f"❌ Error in book_appointment: {e}")
                return f"Sorry, I couldn't book the appointment. Error: {str(e)}"
        
        def get_current_date(query) -> str:
            """Get current date and time"""
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return [
            Tool(
                name="check_availability",
                description="Check available time slots for a specific date. Input: date in YYYY-MM-DD format, 'today', or 'tomorrow'.",
                func=check_availability
            ),
            Tool(
                name="book_appointment",
                description="Book an appointment. Input: JSON with title, start_time, end_time, description.",
                func=book_appointment
            ),
            Tool(
                name="get_current_date",
                description="Get the current date and time",
                func=get_current_date
            )
        ]
    
    def _create_agent(self):
        """Create the conversational agent"""
        system_message = """You are a helpful AI assistant that helps users book appointments on their Google Calendar.

Your capabilities:
1. Check calendar availability for specific dates
2. Suggest available time slots
3. Book appointments with user confirmation
4. Handle natural language requests conversationally

Guidelines:
- Always be polite and conversational
- Confirm details before booking
- Ask for clarification when needed
- Provide clear available time slots
- Handle date parsing naturally (today, tomorrow, specific dates)
- For booking, always confirm: title, date, time, and duration
- Use the tools available to you: check_availability, book_appointment, get_current_date

When booking appointments:
- Always confirm all details with the user first
- Ask for a title/purpose for the appointment
- Clarify the duration if not specified (default to 1 hour)
- Show available time slots before booking
"""

        try:
            return initialize_agent(
                tools=self.tools,
                llm=self.llm,
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                memory=self.memory,
                verbose=True,
                max_iterations=3,
                early_stopping_method="generate"
            )
        except Exception as e:
            print(f"❌ Error creating agent: {e}")
            raise
    
    def chat(self, message: str) -> str:
        """Process user message and return response"""
        try:
            print(f"💬 Processing message: {message}")
            
            # Simple responses for basic queries
            if "hello" in message.lower() or "hi" in message.lower():
                return "Hello! I'm your AI appointment booking assistant. I can help you check availability and book appointments on your Google Calendar. What would you like to do?"
            
            if "help" in message.lower():
                return "I can help you with:\n• Check availability for specific dates\n• Book appointments\n• Suggest time slots\n\nTry saying 'Check availability for today' or 'Book a meeting tomorrow at 2 PM'"
            
            # Use the agent for complex queries
            response = self.agent.run(message)
            print(f"✅ Agent response: {response}")
            return response
            
        except Exception as e:
            print(f"❌ Error in chat: {e}")
            return f"I apologize, but I encountered an error: {str(e)}. Please try a simpler request like 'Check availability for today'."