# backend/agent.py - Updated with better error handling
import os
import re
import json
import pytz
from datetime import datetime, timedelta, time
from typing import Dict, List, Any
from langchain.agents import Tool
from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage



class AppointmentBookingAgent:
    def __init__(self, calendar_service, gemini_api_key: str):
        self.pending_bookings = []
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
                print(f"Checking availability for: {date_input}")
                now = datetime.now()
                if 'today' in date_input.lower():
                    target_date = datetime.now().date()
                elif 'tomorrow' in date_input.lower():
                    target_date = datetime.now().date() + timedelta(days=1)
                else:
                    try:
                        target_date = datetime.strptime(date_input, '%Y-%m-%d').date()
                    except:
                        return "Please provide a valid date in YYYY-MM-DD format, or use 'today' or 'tomorrow'."
                
                # Get available slots
                print(f" Checking availability for {target_date}")
                output = self.calendar_service.get_free_intervals_for_date(target_date.isoformat() + 'T00:00:00Z', skip_before=now.date().isoformat() + 'T00:00:00Z' if target_date == now.date() else None)
                condition = output[0]
                content = output[1]
                if condition:
                    if not content:
                        return f"No free intervals found on {target_date}."
                    
                    lines = [f"{s['start'].strftime('%I:%M %p')} - {s['end'].strftime('%I:%M %p')}" for s in content]
                    return f"Available slots for {target_date}: " + " | ".join(lines)
                
                else:
                    return f"Sorry, I couldn't check availability. Error: {str(content)}"
                
            except Exception as e:
                print(f" Error in check_availability: {e}")
                return f"Sorry, I couldn't check availability. Error: {str(e)}"
            
        def suggest_suitable_time(input_str) -> str:
            try:
                data = json.loads(input_str)
                date = data['date']
                query = data['query']
                """
                Extracts task and date from the query, asks Gemini for JSON output, 
                and checks against the calendar for a suitable time.
                """
                if 'today' in date.lower():
                    target_date = datetime.now().date()
                elif 'tomorrow' in date.lower():
                    target_date = datetime.now().date() + timedelta(days=1)
                else:
                    try:
                        target_date = datetime.strptime(date, '%Y-%m-%d').date()
                    except:
                        return "Please provide a valid date in YYYY-MM-DD format, or use 'today' or 'tomorrow'."
                date_str = target_date.isoformat() + 'T00:00:00Z'
                if not date_str:
                    return ("I couldn't find a date in your request. "
                            "Please specify it like '2025-07-04'.")
                
                
                start = datetime.combine(target_date, time(0, 0, 0))
                end = datetime.combine(target_date, time(23, 59, 0))

                timezone = pytz.timezone('Asia/Kolkata')
                
                start = timezone.localize(start)
                end = timezone.localize(end)


                
                busy = self.calendar_service.get_availability(
                    start.isoformat(), end.isoformat()
                )

                busy_str = ", ".join(
                f"{datetime.fromisoformat(s['start'].replace('Z', '+00:00')).strftime('%H:%M')}-"
                f"{datetime.fromisoformat(s['end'  ].replace('Z', '+00:00')).strftime('%H:%M')}"
                for s in busy
                )

                

                #Build precise prompt for Gemini
                prompt = (
                    "You're an expert scheduling assistant.\n"
                    f"Task request: '{query}'.\n"
                    f"Date: {date_str}.\n"
                    f"Busy intervals on that date (24‑hour HH:MM): {busy_str}.\n"
                    "Make sure the suggested time does NOT overlap with the busy intervals."
                )

                #call Gemini
                
                llm_resp = self.llm.invoke([HumanMessage(content=prompt)])
                
                return llm_resp.content.strip()

            except Exception as e:
                print(f"error in suggesting_suitable_time: {e}")


        def book_appointment(appointment_details: str) -> str:
            try:
                now = datetime.now()
                try:
                    details = json.loads(appointment_details)
                except json.JSONDecodeError:
                    return "Please provide appointment details in proper JSON format."

                start = datetime.fromisoformat(details['start_time'])
                end = datetime.fromisoformat(details['end_time'])
                

                # Past-time check
                print(f"Booking appointment from {start} to {now}")
                if start < now:
                    return "Cannot book an appointment in the past. Please choose a future date/time."

                # Clash detection
                timezone = pytz.timezone('Asia/Kolkata')
                
                start = timezone.localize(start)
                end = timezone.localize(end)

                busy = self.calendar_service.get_availability(
                    start.isoformat(), end.isoformat()
                )
                # Store pending booking request
                pending = {"details": details, "force": bool(busy)}
                self.pending_bookings.append(pending)

                if busy:
                    # Ask user if they want to force-book despite clash
                    return (
                        f"Requested slot {start.strftime('%Y-%m-%d')} {start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')} "
                        "clashes with existing events. Do you still want to book? (yes/no)"
                    )
                else:
                    # No clash: ask for confirmation
                    return (
                        f"Booking '{details.get('title','Appointment')}' on {start.strftime('%Y-%m-%d')} "
                        f"from {start.strftime('%I:%M %p')} to {end.strftime('%I:%M %p')}. OK? (yes/no)"
                    )
            except Exception as e:
                print(f"❌ Error in book_appointment: {e}")
                return f"Sorry, I couldn't book the appointment. Error: {str(e)}"    
            
        def confirm_booking(answer: str) -> str:
            if not self.pending_bookings:
                return "There is no booking to confirm."
            
            if not answer:
                return "Please provide 'yes' to confirm or 'no' to cancel the booking."

            ans = answer.strip().lower()
            pending = self.pending_bookings.pop()
            details = pending['details']

            if ans not in ['yes', 'y']:
                return "Booking cancelled. Let me know if you'd like another time."

            # Proceed to create the event
            title = details.get('title', 'Appointment')
            start_iso = details['start_time']
            end_iso = details['end_time']
            result = self.calendar_service.create_event(
                title=title,
                start_time=start_iso,
                end_time=end_iso,
                description=details.get('description', '')
            )

            if result.get('success'):
                return f"✅ Appointment '{title}' booked successfully!"
            else:
                return f"❌ Failed to book appointment: {result.get('message')}"

        
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
                description=("Book an appointment in the calendar. Use this tool whenever the user wants to schedule, reserve, or set up a meeting, call, event, reminder or any other thing. and it will give only the pending list not confirm the booking. "
                "Input must be a JSON object with the following keys:\n"
                "- 'title': a short title or purpose for the appointment (string)\n"
                "- 'start_time': the ISO format start datetime (e.g., '2025-07-04T14:00:00')\n"
                "- 'end_time': the ISO format end datetime (e.g., '2025-07-04T15:00:00')\n"
                "- 'description': optional details about the appointment (string)\n\n"
            ),
                func=book_appointment
            ),
            Tool(name="confirm_booking", func=confirm_booking,
                 description="Confirm or cancel a pending booking from the pending list. input: 'yes' to confirm or 'no' to cancel."),
            Tool(name="suggest_suitable_time", func=suggest_suitable_time,
                 description="Suggest best time for a task based on calendar and LLM and also suggest best time for any planing or any work to do if it is realted to time. Input1: date in YYYY-MM-DD format, 'today', or 'tomorrow'. Input2: detailed query"),
            Tool(
                name="get_current_date",
                description="Get the current date and time. Input must be a non-empty string",
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
- if only time or only date is given before trying any tool ask the other thing
"""

        try:
            return initialize_agent(
                tools=self.tools,
                llm=self.llm,
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                memory=self.memory,
                verbose=True,
                max_iterations=3,
                early_stopping_method="generate",
                handle_parsing_errors="I'm sorry, I didn’t understand that. Could you rephrase or give more details?"
            )
        except Exception as e:
            print(f"❌ Error creating agent: {e}")
            raise
    
    def chat(self, message: str) -> str:
        """Process user message and return response"""
        try:
            print(f"💬 Processing message: {message}")
            
            # Simple responses for basic queries
            # if "hello" in message.lower() or "hi" in message.lower():
            #     return "Hello! I'm your AI appointment booking assistant. I can help you check availability and book appointments on your Google Calendar. What would you like to do?"
            
            # if "help" in message.lower():
            #     return "I can help you with:\n• Check availability for specific dates\n• Book appointments\n• Suggest time slots\n\nTry saying 'Check availability for today' or 'Book a meeting tomorrow at 2 PM'"
            
            # Use the agent for complex queries
            response = self.agent.run(message)
            print(f"✅ Agent response: {response}")
            return response
            
        except Exception as e:
            print(f"❌ Error in chat: {e}")
            return f"I apologize, but I encountered an error: {str(e)}. Please try a simpler request like 'Check availability for today'."