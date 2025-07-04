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

                dt = datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
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
            print(f"Checking availability from {start_date} to {end_date}")
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
        
    def get_free_intervals_for_date(self, target_date: str, skip_before: str) -> List:

        # use full-day range 00:00 to 23:59
        try:
            # Parse the date
            timezone = pytz.timezone('Asia/Kolkata')
        
            if 'T' in target_date:
                target_date = datetime.fromisoformat(target_date.replace('Z', '+00:00')).date()
            else:
                target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            if skip_before:
                if 'T' in skip_before:
                    skip_before = datetime.fromisoformat(skip_before.replace('Z', '+00:00')).date()
                    skip_before = datetime.combine(skip_before, datetime.now().time())
                    skip_before = timezone.localize(skip_before)
                else:
                    skip_before = datetime.strptime(skip_before, '%Y-%m-%d').date()
                    skip_before = datetime.combine(skip_before, datetime.now().time())
                    skip_before = timezone.localize(skip_before)
                
            print("skip",skip_before)

            
            start_time = datetime.combine(target_date, datetime.min.time())
            end_time = datetime.combine(target_date, datetime.min.time().replace(hour=23, minute=59))
            print("check0")
            
            # Add timezone
            timezone = pytz.timezone('Asia/Kolkata')
            print(timezone)
            start_time = timezone.localize(start_time)
            end_time = timezone.localize(end_time)
            
            
            # Get busy times
            busy_times = self.get_availability(
                start_time.isoformat(),
                end_time.isoformat()
            )
            print("check1")
    
            busy_sorted = sorted(busy_times, key=lambda x: x['start'])
            print("check2")
            free = []
            cursor = start_time
            print(cursor, skip_before)

            print(f"strat: {start_time}, end: {end_time}, skip_before: {skip_before}")
            for b in busy_sorted:
                bs = datetime.fromisoformat(b['start'].replace('Z','+00:00')).astimezone(timezone)
                be = datetime.fromisoformat(b['end'].replace('Z','+00:00')).astimezone(timezone)
                if skip_before and cursor < skip_before:
                    cursor = skip_before
                    skip_before = None
                if cursor < bs:
                    free.append({'start': cursor, 'end': bs})
                cursor = max(cursor, be)
            if skip_before and cursor < skip_before:
                cursor = skip_before
            if cursor < end_time:
                free.append({'start': cursor, 'end': end_time})
            return [True,free]
        except Exception as error:
            print(f"Error suggesting time slots: {error}")
            return [False,error]
    




        
