import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz

class CalendarService:
    def __init__(self, credentials_path: str, calendar_id: str):
        self.credentials_path = credentials_path
        self.calendar_id = calendar_id
        self.service = self._authenticate()
        
    def _authenticate(self):
        """Authenticate with Google Calendar API using service account"""
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        return build('calendar', 'v3', credentials=credentials)
    
    def _parse_datetime(self, dt_string: str) -> datetime:
        """Parse datetime string and ensure timezone awareness"""
        try:
            # Try to parse ISO format first
            if 'T' in dt_string:
                dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            else:
                # Parse simple format like '2025-07-04 02:00:00'
                dt = datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
                # Add UTC timezone if none specified
                if dt.tzinfo is None:
                    dt = pytz.timezone('Asia/Kolkata').localize(dt)
            
            return dt
        except Exception as e:
            print(f"Error parsing datetime {dt_string}: {e}")
            raise
    
    def get_availability(self, start_date: str, end_date: str) -> List[Dict]:
        """Get busy times for the specified date range"""
        try:
            # Convert to datetime objects
            start_dt = self._parse_datetime(start_date)
            end_dt = self._parse_datetime(end_date)
            
            # Get busy times
            body = {
                "timeMin": start_dt.isoformat(),
                "timeMax": end_dt.isoformat(),
                "items": [{"id": self.calendar_id}]
            }
            
            response = self.service.freebusy().query(body=body).execute()
            busy_times = response['calendars'][self.calendar_id]['busy']
            
            return busy_times
            
        except HttpError as error:
            print(f"Error checking availability: {error}")
            return []
    
    def suggest_time_slots(self, date: str, duration_minutes: int = 60) -> List[Dict]:
        """Suggest available time slots for a given date"""
        try:
            # Parse the date
            if 'T' in date:
                target_date = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
            else:
                target_date = datetime.strptime(date, '%Y-%m-%d').date()
            
            # Set working hours (9 AM to 5 PM)
            start_time = datetime.combine(target_date, datetime.min.time().replace(hour=9))
            end_time = datetime.combine(target_date, datetime.min.time().replace(hour=17))
            
            # Add timezone
            timezone = pytz.timezone('Asia/Kolkata')
            start_time = timezone.localize(start_time)
            end_time = timezone.localize(end_time)
            
            # Get busy times
            busy_times = self.get_availability(
                start_time.isoformat(),
                end_time.isoformat()
            )
            
            # Generate time slots
            available_slots = []
            current_time = start_time
            
            while current_time + timedelta(minutes=duration_minutes) <= end_time:
                slot_end = current_time + timedelta(minutes=duration_minutes)
                
                # Check if slot conflicts with busy times
                is_available = True
                for busy in busy_times:
                    busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                    busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                    
                    if (current_time < busy_end and slot_end > busy_start):
                        is_available = False
                        break
                
                if is_available:
                    available_slots.append({
                        'start': current_time.isoformat(),
                        'end': slot_end.isoformat(),
                        'display': current_time.strftime('%I:%M %p')
                    })
                
                current_time += timedelta(minutes=30)  # 30-minute intervals
            
            return available_slots[:5]  # Return top 5 slots
            
        except Exception as error:
            print(f"Error suggesting time slots: {error}")
            return []
    
    def create_event(self, title: str, start_time: str, end_time: str, description: str = "") -> Dict:
        """Create a new calendar event"""
        try:
            # Parse and format datetime strings properly
            start_dt = self._parse_datetime(start_time)
            end_dt = self._parse_datetime(end_time)
            
            # Ensure we have timezone-aware datetimes
            if start_dt.tzinfo is None:
                start_dt = pytz.timezone('Asia/Kolkata').localize(start_dt)
            if end_dt.tzinfo is None:
                end_dt = pytz.timezone('Asia/Kolkata').localize(end_dt)
            
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': 'Asia/Kolkata',
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': 'Asia/Kolkata',
                },
            }
            
            print(f"Creating event: {event}")  # Debug logging
            
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            return {
                'success': True,
                'event_id': created_event['id'],
                'event_link': created_event.get('htmlLink', ''),
                'message': 'Event created successfully!'
            }
            
        except HttpError as error:
            print(f"Error creating event: {error}")
            return {
                'success': False,
                'message': f'Error creating event: {str(error)}'
            }
        except Exception as error:
            print(f"Unexpected error creating event: {error}")
            return {
                'success': False,
                'message': f'Unexpected error: {str(error)}'
            }