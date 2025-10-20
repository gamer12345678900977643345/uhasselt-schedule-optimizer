#!/usr/bin/env python3
"""
UHasselt Schedule Optimizer
Back-end tool die de UHasselt MyTimetable ICS-link automatisch analyseert,
groepen detecteert (A/B/all/{N/A}), en een geoptimaliseerde Google Calendar ICS genereert.

Author: Michel Carmans
Version: 1.0
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import pytz
import requests
from ics import Calendar, Event
from ics.icalendar import Calendar as ICalendar

from google_calendar_integration import GoogleCalendarIntegration


class UHasseltScheduleOptimizer:
    """Main class for optimizing UHasselt schedules."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the optimizer with configuration."""
        self.config = self._load_config(config_path)
        self.setup_logging()
        self.group_detection_rules = self._load_group_rules()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default configuration
            return {
                "preferred_group": "A",
                "fallback_group_behavior": "use_all_if_missing",
                "optimization_mode": "earliest_lesson",
                "minimum_break_minutes": 1,
                "skip_weekends": True,
                "timezone": "Europe/Brussels"
            }
    
    def _load_group_rules(self) -> List[Dict[str, str]]:
        """Load group detection rules."""
        return [
            {"regex": r"(groep|Group)\s*A", "assign": "A"},
            {"regex": r"(groep|Group)\s*B", "assign": "B"},
            {"regex": r"(groep|Group)\s*C", "assign": "C"},
            {"regex": r"(groep|Group)\s*D", "assign": "D"},
            {"regex": r"(groep|Group)\s*E", "assign": "E"},
            {"regex": r"all|alle", "assign": "ALL"},
            {"regex": r"\{N/A\}", "assign": "NA"}
        ]
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/optimizer.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Create logs directory if it doesn't exist
        Path("logs").mkdir(exist_ok=True)
    
    def download_ics(self, url: str) -> str:
        """Download ICS file from URL."""
        try:
            self.logger.info(f"Downloading ICS from: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self.logger.error(f"Failed to download ICS: {e}")
            raise
    
    def parse_ics(self, ics_content: str) -> Calendar:
        """Parse ICS content into Calendar object."""
        try:
            calendar = Calendar(ics_content)
            self.logger.info(f"Parsed {len(calendar.events)} events from ICS")
            return calendar
        except Exception as e:
            self.logger.error(f"Failed to parse ICS: {e}")
            raise
    
    def detect_group(self, event: Event) -> str:
        """Detect group from event summary and description."""
        text_to_analyze = f"{event.name} {event.description or ''}"
        
        for rule in self.group_detection_rules:
            if re.search(rule["regex"], text_to_analyze, re.IGNORECASE):
                return rule["assign"]
        
        return "UNKNOWN"
    
    def group_events_by_course(self, events: List[Event]) -> Dict[str, List[Event]]:
        """Group events by course code."""
        course_groups = {}
        
        for event in events:
            # Extract course code from summary (assuming format: "XXXX - Course Name")
            course_match = re.match(r'^(\d+)\s*-\s*', event.name)
            if course_match:
                course_code = course_match.group(1)
            else:
                course_code = "UNKNOWN"
            
            if course_code not in course_groups:
                course_groups[course_code] = []
            
            course_groups[course_code].append(event)
        
        return course_groups
    
    def select_optimal_event(self, events: List[Event], course_code: str) -> Optional[Event]:
        """Select the optimal event from a list of events for the same course."""
        if not events:
            return None
        
        # Detect groups for all events
        events_with_groups = []
        for event in events:
            group = self.detect_group(event)
            events_with_groups.append((event, group))
        
        # Filter by preferred group
        preferred_group = self.config.get("preferred_group", "A")
        preferred_events = [e for e, g in events_with_groups if g == preferred_group]
        
        if preferred_events:
            events_to_choose_from = preferred_events
        elif self.config.get("fallback_group_behavior") == "use_all_if_missing":
            events_to_choose_from = [e for e, g in events_with_groups if g == "ALL"]
            if not events_to_choose_from:
                events_to_choose_from = [e for e, g in events_with_groups]
        else:
            events_to_choose_from = [e for e, g in events_with_groups]
        
        if not events_to_choose_from:
            return events[0]  # Fallback to first event
        
        # Apply optimization mode
        optimization_mode = self.config.get("optimization_mode", "earliest_lesson")
        
        if optimization_mode == "earliest_lesson":
            return min(events_to_choose_from, key=lambda e: e.begin)
        elif optimization_mode == "latest_lesson":
            return max(events_to_choose_from, key=lambda e: e.begin)
        else:
            return events_to_choose_from[0]
    
    def should_skip_weekend(self, event: Event) -> bool:
        """Check if event should be skipped based on weekend setting."""
        if not self.config.get("skip_weekends", True):
            return False
        
        # Check if event is on weekend (Saturday=5, Sunday=6)
        return event.begin.weekday() >= 5
    
    def optimize_schedule(self, calendar: Calendar) -> Calendar:
        """Optimize the schedule by selecting best events for each course."""
        self.logger.info("Starting schedule optimization...")
        
        # Filter out weekend events if configured
        events = [e for e in calendar.events if not self.should_skip_weekend(e)]
        
        # Group events by course
        course_groups = self.group_events_by_course(events)
        
        # Select optimal events
        optimized_events = []
        for course_code, course_events in course_groups.items():
            optimal_event = self.select_optimal_event(course_events, course_code)
            if optimal_event:
                optimized_events.append(optimal_event)
                self.logger.info(f"Selected event for course {course_code}: {optimal_event.name}")
        
        # Create new calendar
        optimized_calendar = Calendar()
        for event in optimized_events:
            optimized_calendar.events.add(event)
        
        self.logger.info(f"Optimized schedule contains {len(optimized_events)} events")
        return optimized_calendar
    
    def generate_optimized_ics(self, calendar: Calendar, output_path: str = "optimized_schedule.ics"):
        """Generate optimized ICS file."""
        try:
            # Create output directory
            Path("output").mkdir(exist_ok=True)
            
            output_file = Path("output") / output_path
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(str(calendar))
            
            self.logger.info(f"Optimized schedule saved to: {output_file}")
            return str(output_file)
        except Exception as e:
            self.logger.error(f"Failed to generate ICS: {e}")
            raise
    
    def run_optimization(self, ics_url: str, output_path: str = "optimized_schedule.ics", 
                        sync_to_google: bool = False, calendar_name: str = "UHasselt Optimized Schedule"):
        """Run the complete optimization process."""
        try:
            # Download and parse ICS
            ics_content = self.download_ics(ics_url)
            calendar = self.parse_ics(ics_content)
            
            # Optimize schedule
            optimized_calendar = self.optimize_schedule(calendar)
            
            # Generate output
            output_file = self.generate_optimized_ics(optimized_calendar, output_path)
            
            # Sync to Google Calendar if requested
            google_url = None
            if sync_to_google:
                try:
                    integration = GoogleCalendarIntegration()
                    # Get user email from environment
                    user_email = os.environ.get('USER_EMAIL')
                    google_url = integration.sync_schedule(optimized_calendar, calendar_name, user_email)
                    if google_url:
                        self.logger.info(f"Calendar synced to Google: {google_url}")
                    else:
                        self.logger.warning("Failed to sync to Google Calendar")
                except Exception as e:
                    self.logger.error(f"Google Calendar sync failed: {e}")
            
            self.logger.info("Schedule optimization completed successfully!")
            return {
                "output_file": output_file,
                "google_calendar_url": google_url
            }
            
        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="UHasselt Schedule Optimizer")
    parser.add_argument("--config", default="config.json", help="Configuration file path")
    parser.add_argument("--url", help="ICS URL to optimize")
    parser.add_argument("--output", default="optimized_schedule.ics", help="Output file name")
    parser.add_argument("--sync-google", action="store_true", help="Sync to Google Calendar")
    parser.add_argument("--calendar-name", default="UHasselt Optimized Schedule", help="Google Calendar name")
    
    args = parser.parse_args()
    
    # Load ICS URL from config if not provided
    if not args.url:
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                config = json.load(f)
                args.url = config.get("ics_url")
        except (FileNotFoundError, KeyError):
            print("Error: ICS URL not provided and not found in config file")
            sys.exit(1)
    
    if not args.url:
        print("Error: ICS URL is required")
        sys.exit(1)
    
    # Run optimization
    optimizer = UHasseltScheduleOptimizer(args.config)
    try:
        result = optimizer.run_optimization(
            args.url, 
            args.output, 
            sync_to_google=args.sync_google,
            calendar_name=args.calendar_name
        )
        
        print(f"Optimization completed! Output saved to: {result['output_file']}")
        if result['google_calendar_url']:
            print(f"Google Calendar URL: {result['google_calendar_url']}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
