#!/usr/bin/env python3
"""
Test script for UHasselt Schedule Optimizer
This script tests the optimizer with sample data.
"""

import json
import tempfile
from pathlib import Path
from main import UHasseltScheduleOptimizer

def create_sample_ics():
    """Create a sample ICS file for testing."""
    sample_ics = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//UHasselt//MyTimetable//EN
BEGIN:VEVENT
UID:test1@uhasselt.be
DTSTART:20241009T133000
DTEND:20241009T150000
SUMMARY:5417 - Algemene economie - Werkzitting 1HW A
DESCRIPTION:Docent(en): ADRIAENSENS Charlotte, Groep(en): 03-005417 groep A, {N/A}
LOCATION:A101
END:VEVENT
BEGIN:VEVENT
UID:test2@uhasselt.be
DTSTART:20241009T150000
DTEND:20241009T163000
SUMMARY:5417 - Algemene economie - Werkzitting 1HW B
DESCRIPTION:Docent(en): ADRIAENSENS Charlotte, Groep(en): 03-005417 groep B, {N/A}
LOCATION:A102
END:VEVENT
BEGIN:VEVENT
UID:test3@uhasselt.be
DTSTART:20241010T090000
DTEND:20241010T110000
SUMMARY:5418 - Wiskunde - Hoorcollege ALL
DESCRIPTION:Docent(en): SMITH John, Groep(en): 03-005418 all, {N/A}
LOCATION:A201
END:VEVENT
END:VCALENDAR"""
    
    return sample_ics

def test_group_detection():
    """Test group detection functionality."""
    print("Testing group detection...")
    
    optimizer = UHasseltScheduleOptimizer()
    
    # Test with sample events
    from ics import Calendar
    sample_ics = create_sample_ics()
    calendar = Calendar(sample_ics)
    
    for event in calendar.events:
        group = optimizer.detect_group(event)
        print(f"Event: {event.name}")
        print(f"Detected group: {group}")
        print(f"Description: {event.description}")
        print("-" * 50)

def test_optimization():
    """Test the complete optimization process."""
    print("Testing optimization process...")
    
    # Create temporary config
    config = {
        "preferred_group": "A",
        "fallback_group_behavior": "use_all_if_missing",
        "optimization_mode": "earliest_lesson",
        "minimum_break_minutes": 1,
        "skip_weekends": True,
        "timezone": "Europe/Brussels"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        config_path = f.name
    
    try:
        optimizer = UHasseltScheduleOptimizer(config_path)
        
        # Test with sample ICS
        sample_ics = create_sample_ics()
        calendar = optimizer.parse_ics(sample_ics)
        
        print(f"Original events: {len(calendar.events)}")
        
        # Test grouping
        course_groups = optimizer.group_events_by_course(list(calendar.events))
        print(f"Course groups: {list(course_groups.keys())}")
        
        # Test optimization
        optimized_calendar = optimizer.optimize_schedule(calendar)
        print(f"Optimized events: {len(optimized_calendar.events)}")
        
        # Show optimized events
        for event in optimized_calendar.events:
            group = optimizer.detect_group(event)
            print(f"Selected: {event.name} (Group: {group})")
        
        print("✅ Optimization test completed successfully!")
        
    finally:
        # Clean up
        Path(config_path).unlink()

def main():
    """Run all tests."""
    print("=== UHasselt Schedule Optimizer - Test Suite ===")
    print()
    
    try:
        test_group_detection()
        print()
        test_optimization()
        print()
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
