import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from langchain.agents import Tool
from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage
from calendar_service import CalendarService

class AppointmentBookingAgent:
    def __init__(self, calendar_service: CalendarService, gemini_api_key: str):
        self.calendar_service = calendar_service
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  
            google_api_key=gemini_api_key,
            temperature=0.7
        )
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
                # Parse date input
                if 'today' in date_input.lower():
                    date = datetime.now().date()
                elif 'tomorrow' in date_input.lower():
                    date = datetime.now().date() + timedelta(days=1)
                else:
                    # Try to parse date
                    date = datetime.strptime(date_input, '%Y-%m-%d').date()
                
                # Get available slots
                slots = self.calendar_service.suggest_time_slots(
                    date.isoformat() + 'T00:00:00Z'
                )
                
                if slots:
                    slot_text = "\n".join([f"- {slot['display']}" for slot in slots])
                    return f"Available time slots for {date}:\n{slot_text}"
                else:
                    return f"No available slots found for {date}"
                    
            except Exception as e:
                return f"Error checking availability: {str(e)}"
        
        def book_appointment(appointment_details: str) -> str:
            """Book an appointment with given details"""
            try:
                # Parse JSON string safely
                details = json.loads(appointment_details)
                
                # Validate required fields
                if not all(key in details for key in ['title', 'start_time', 'end_time']):
                    return "❌ Missing required fields: title, start_time, end_time"
                
                # Format datetime strings properly if needed
                start_time = details['start_time']
                end_time = details['end_time']
                
                # If datetime strings don't have timezone info, they should be in ISO format
                # The calendar service will handle the timezone conversion
                
                result = self.calendar_service.create_event(
                    title=details['title'],
                    start_time=start_time,
                    end_time=end_time,
                    description=details.get('description', '')
                )
                
                if result['success']:
                    return f"✅ Appointment booked successfully! Event ID: {result['event_id']}"
                else:
                    return f"❌ Failed to book appointment: {result['message']}"
                    
            except json.JSONDecodeError:
                return "❌ Invalid JSON format for appointment details"
            except Exception as e:
                return f"Error booking appointment: {str(e)}"
        
        def parse_user_time(time_request: str) -> str:
            """Parse user's time request and return formatted datetime info"""
            try:
                current_time = datetime.now()
                
                # Handle "tomorrow" and "today"
                if 'tomorrow' in time_request.lower():
                    target_date = current_time.date() + timedelta(days=1)
                elif 'today' in time_request.lower():
                    target_date = current_time.date()
                else:
                    target_date = datetime.strptime(time_request, '%Y-%m-%d').date()
                
                # Extract time information
                time_info = {
                    'date': target_date.strftime('%Y-%m-%d'),
                    'start_time': None,
                    'end_time': None
                }
                
                # Common time patterns
                import re
                
                # Pattern for "3pm to 5pm" or "3 PM to 5 PM"
                pattern1 = r'(\d{1,2})\s*([ap]m)\s*to\s*(\d{1,2})\s*([ap]m)'
                match1 = re.search(pattern1, time_request.lower())
                
                if match1:
                    start_hour = int(match1.group(1))
                    start_period = match1.group(2)
                    end_hour = int(match1.group(3))
                    end_period = match1.group(4)
                    
                    # Convert to 24-hour format
                    if start_period == 'pm' and start_hour != 12:
                        start_hour += 12
                    elif start_period == 'am' and start_hour == 12:
                        start_hour = 0
                    
                    if end_period == 'pm' and end_hour != 12:
                        end_hour += 12
                    elif end_period == 'am' and end_hour == 12:
                        end_hour = 0
                    
                    time_info['start_time'] = f"{target_date}T{start_hour:02d}:00:00"
                    time_info['end_time'] = f"{target_date}T{end_hour:02d}:00:00"
                    
                    return f"Parsed time: {time_info['date']} from {start_hour:02d}:00 to {end_hour:02d}:00 (24-hour format)"
                
                # Pattern for single time like "3pm"
                pattern2 = r'(\d{1,2})\s*([ap]m)'
                match2 = re.search(pattern2, time_request.lower())
                
                if match2:
                    hour = int(match2.group(1))
                    period = match2.group(2)
                    
                    if period == 'pm' and hour != 12:
                        hour += 12
                    elif period == 'am' and hour == 12:
                        hour = 0
                    
                    time_info['start_time'] = f"{target_date}T{hour:02d}:00:00"
                    time_info['end_time'] = f"{target_date}T{hour+1:02d}:00:00"  # Default 1 hour
                    
                    return f"Parsed time: {time_info['date']} from {hour:02d}:00 to {hour+1:02d}:00 (24-hour format)"
                
                return "Could not parse time from request. Please specify time clearly (e.g., '3pm to 5pm')"
                
            except Exception as e:
                return f"Error parsing time: {str(e)}"
        
        def get_current_date(query: str = "") -> str:
            """Get current date and time"""
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return [
            Tool(
                name="check_availability",
                description="Check available time slots for a specific date. Input should be a date in YYYY-MM-DD format, 'today', or 'tomorrow'.",
                func=check_availability
            ),
            Tool(
                name="parse_user_time",
                description="Parse user's time request to extract date and time information. Use this when user specifies specific times like '3pm to 5pm' or 'tomorrow at 2pm'.",
                func=parse_user_time
            ),
            Tool(
                name="book_appointment",
                description="Book an appointment. Input should be a JSON string with keys: title, start_time, end_time, description.",
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
- Use the tools available to you: check_availability, parse_user_time, book_appointment, get_current_date

CRITICAL TIME PARSING WORKFLOW:
1. When user specifies times (like "3pm to 5pm"), FIRST use parse_user_time tool
2. Use the parsed time information for booking
3. Don't use suggested time slots when user has specified exact times
4. Always confirm the EXACT time with the user before booking

Time conversion reference:
- 12 AM = 00:00, 1 AM = 01:00, 2 AM = 02:00, etc.
- 12 PM = 12:00, 1 PM = 13:00, 2 PM = 14:00, 3 PM = 15:00, 4 PM = 16:00, 5 PM = 17:00, etc.

When booking appointments:
- Always confirm all details with the user first
- Ask for a title/purpose for the appointment
- Use parse_user_time tool for user-specified times
- When calling book_appointment, pass a JSON string with the appointment details
- IMPORTANT: Format datetime strings as ISO format: "YYYY-MM-DDTHH:MM:SS"

Example workflow for "book appointment tomorrow 3pm to 5pm":
1. Use parse_user_time("tomorrow 3pm to 5pm")
2. Confirm: "I'll book for [DATE] from 3:00 PM to 5:00 PM. Is this correct?"
3. Book with: {"title": "...", "start_time": "2025-07-04T15:00:00", "end_time": "2025-07-04T17:00:00"}

Before booking, ALWAYS confirm with the user:
"I'm about to book [TITLE] for [DATE] from [START_TIME] to [END_TIME]. Is this correct?"
"""
        
        return initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True,
            system_message=system_message
        )
    
    def chat(self, message: str) -> str:
        """Process user message and return response"""
        try:
            # Use invoke instead of deprecated run method
            response = self.agent.invoke({"input": message})
            return response["output"]
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}. Please try again."