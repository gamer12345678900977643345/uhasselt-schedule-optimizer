#!/usr/bin/env python3
"""
Google Calendar Integration Module
Handles authentication and calendar operations for UHasselt Schedule Optimizer.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ics import Calendar, Event


class GoogleCalendarIntegration:
    """Handles Google Calendar integration for schedule optimization."""
    
    # Scopes required for calendar access
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, credentials_file: str = "credentials.json", 
                 token_file: str = "token.json"):
        """Initialize Google Calendar integration."""
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.logger = logging.getLogger(__name__)
        
    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API."""
        try:
            # Try Service Account authentication first
            if os.path.exists(self.credentials_file):
                try:
                    # Check if it's a service account key
                    with open(self.credentials_file, 'r') as f:
                        import json
                        key_data = json.load(f)
                        if key_data.get('type') == 'service_account':
                            # Service Account authentication
                            creds = service_account.Credentials.from_service_account_file(
                                self.credentials_file, scopes=self.SCOPES)
                            self.service = build('calendar', 'v3', credentials=creds)
                            self.logger.info("Successfully authenticated with Service Account")
                            return True
                except Exception as e:
                    self.logger.warning(f"Service Account authentication failed: {e}")
            
            # Fallback to OAuth2 authentication
            creds = None
            
            # Load existing token if available
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        self.logger.error(f"Credentials file not found: {self.credentials_file}")
                        self.logger.error("Please download credentials.json from Google Cloud Console")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
            
            # Build service
            self.service = build('calendar', 'v3', credentials=creds)
            self.logger.info("Successfully authenticated with Google Calendar API")
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False
    
    def create_calendar(self, calendar_name: str = "UHasselt Optimized Schedule") -> Optional[str]:
        """Create a new calendar for the optimized schedule."""
        try:
            calendar = {
                'summary': calendar_name,
                'description': 'Optimized UHasselt schedule with minimal gaps between classes',
                'timeZone': 'Europe/Brussels'
            }
            
            created_calendar = self.service.calendars().insert(body=calendar).execute()
            calendar_id = created_calendar['id']
            
            self.logger.info(f"Created calendar: {calendar_name} (ID: {calendar_id})")
            return calendar_id
            
        except HttpError as e:
            self.logger.error(f"Failed to create calendar: {e}")
            return None
    
    def get_calendar_id(self, calendar_name: str = "UHasselt Optimized Schedule") -> Optional[str]:
        """Get calendar ID by name, create if doesn't exist."""
        try:
            # List existing calendars
            calendar_list = self.service.calendarList().list().execute()
            
            for calendar_item in calendar_list.get('items', []):
                if calendar_item['summary'] == calendar_name:
                    return calendar_item['id']
            
            # Calendar not found, create it
            return self.create_calendar(calendar_name)
            
        except HttpError as e:
            self.logger.error(f"Failed to get calendar ID: {e}")
            return None
    
    def clear_calendar(self, calendar_id: str) -> bool:
        """Clear all events from the calendar."""
        try:
            # Get all events
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=datetime.utcnow().isoformat() + 'Z'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Delete all events
            for event in events:
                self.service.events().delete(
                    calendarId=calendar_id,
                    eventId=event['id']
                ).execute()
            
            self.logger.info(f"Cleared {len(events)} events from calendar")
            return True
            
        except HttpError as e:
            self.logger.error(f"Failed to clear calendar: {e}")
            return False
    
    def ics_event_to_google_event(self, ics_event: Event) -> Dict:
        """Convert ICS event to Google Calendar event format."""
        # Format datetime for Google Calendar
        start_time = ics_event.begin.isoformat()
        end_time = ics_event.end.isoformat()
        
        # Create event description
        description_parts = []
        if ics_event.description:
            description_parts.append(ics_event.description)
        
        # Add group information if available
        group_info = self._extract_group_from_event(ics_event)
        if group_info:
            description_parts.append(f"Groep: {group_info}")
        
        description = "\n".join(description_parts) if description_parts else ""
        
        # Create Google Calendar event
        google_event = {
            'summary': ics_event.name,
            'description': description,
            'location': ics_event.location or "",
            'start': {
                'dateTime': start_time,
                'timeZone': 'Europe/Brussels',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'Europe/Brussels',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 15},
                    {'method': 'email', 'minutes': 60},
                ],
            },
        }
        
        return google_event
    
    def _extract_group_from_event(self, event: Event) -> Optional[str]:
        """Extract group information from event name or description."""
        text_to_analyze = f"{event.name} {event.description or ''}"
        
        # Look for group patterns
        import re
        group_patterns = [
            r"groep\s*([A-E])",
            r"group\s*([A-E])",
            r"([A-E])\s*groep",
            r"([A-E])\s*group"
        ]
        
        for pattern in group_patterns:
            match = re.search(pattern, text_to_analyze, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def upload_events(self, calendar: Calendar, calendar_id: str, 
                     clear_existing: bool = True) -> bool:
        """Upload events from ICS calendar to Google Calendar."""
        try:
            if not self.service:
                self.logger.error("Not authenticated with Google Calendar API")
                return False
            
            # Clear existing events if requested
            if clear_existing:
                self.clear_calendar(calendar_id)
            
            # Upload events
            uploaded_count = 0
            for ics_event in calendar.events:
                try:
                    google_event = self.ics_event_to_google_event(ics_event)
                    
                    # Insert event
                    self.service.events().insert(
                        calendarId=calendar_id,
                        body=google_event
                    ).execute()
                    
                    uploaded_count += 1
                    self.logger.debug(f"Uploaded event: {ics_event.name}")
                    
                except HttpError as e:
                    self.logger.error(f"Failed to upload event {ics_event.name}: {e}")
                    continue
            
            self.logger.info(f"Successfully uploaded {uploaded_count} events to Google Calendar")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upload events: {e}")
            return False
    
    def get_calendar_public_url(self, calendar_id: str, user_email: str = None) -> Optional[str]:
        """Get public URL for the calendar and share with user."""
        try:
            calendar = self.service.calendars().get(calendarId=calendar_id).execute()
            
            # Make calendar public
            rule = {
                'scope': {
                    'type': 'default'
                },
                'role': 'reader'
            }
            
            self.service.acl().insert(
                calendarId=calendar_id,
                body=rule
            ).execute()
            
            # Share with specific user if email provided
            if user_email:
                user_rule = {
                    'scope': {
                        'type': 'user',
                        'value': user_email
                    },
                    'role': 'owner'
                }
                
                try:
                    self.service.acl().insert(
                        calendarId=calendar_id,
                        body=user_rule
                    ).execute()
                    self.logger.info(f"Calendar shared with {user_email}")
                except HttpError as e:
                    self.logger.warning(f"Could not share calendar with {user_email}: {e}")
            
            # Return public URL
            public_url = f"https://calendar.google.com/calendar/embed?src={calendar_id}"
            return public_url
            
        except HttpError as e:
            self.logger.error(f"Failed to get public URL: {e}")
            return None
    
    def sync_schedule(self, ics_calendar: Calendar, 
                     calendar_name: str = "UHasselt Optimized Schedule", 
                     user_email: str = None) -> Optional[str]:
        """Complete sync process: authenticate, get/create calendar, upload events."""
        try:
            # Authenticate
            if not self.authenticate():
                return None
            
            # Get or create calendar
            calendar_id = self.get_calendar_id(calendar_name)
            if not calendar_id:
                return None
            
            # Upload events
            if not self.upload_events(ics_calendar, calendar_id):
                return None
            
            # Get public URL and share with user
            public_url = self.get_calendar_public_url(calendar_id, user_email)
            
            self.logger.info("Schedule sync completed successfully!")
            return public_url
            
        except Exception as e:
            self.logger.error(f"Schedule sync failed: {e}")
            return None


def main():
    """Test the Google Calendar integration."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test with sample calendar
    from ics import Calendar
    sample_ics = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//UHasselt//MyTimetable//EN
BEGIN:VEVENT
UID:test1@uhasselt.be
DTSTART:20241009T133000
DTEND:20241009T150000
SUMMARY:5417 - Algemene economie - Werkzitting 1HW A
DESCRIPTION:Docent(en): ADRIAENSENS Charlotte, Groep(en): 03-005417 groep A
LOCATION:A101
END:VEVENT
END:VCALENDAR"""
    
    calendar = Calendar(sample_ics)
    
    # Test integration
    integration = GoogleCalendarIntegration()
    public_url = integration.sync_schedule(calendar)
    
    if public_url:
        print(f"✅ Calendar synced successfully!")
        print(f"📅 Public URL: {public_url}")
    else:
        print("❌ Calendar sync failed")


if __name__ == "__main__":
    main()
