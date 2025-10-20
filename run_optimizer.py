#!/usr/bin/env python3
"""
Simple runner script for UHasselt Schedule Optimizer
This script provides an easy way to run the optimizer with a GUI-like interface.
"""

import json
import os
import sys
from pathlib import Path

def get_user_input():
    """Get user input for ICS URL and preferences."""
    print("=== UHasselt Schedule Optimizer ===")
    print()
    
    # Get ICS URL
    ics_url = input("Enter your MyTimetable ICS URL: ").strip()
    if not ics_url:
        print("Error: ICS URL is required")
        return None
    
    # Get preferred group
    print("\nAvailable groups: A, B, C, D, E, ALL")
    preferred_group = input("Enter your preferred group (default: A): ").strip().upper()
    if not preferred_group:
        preferred_group = "A"
    
    # Get optimization mode
    print("\nOptimization modes:")
    print("1. earliest_lesson - Choose earliest lesson time")
    print("2. latest_lesson - Choose latest lesson time")
    opt_mode = input("Choose optimization mode (1 or 2, default: 1): ").strip()
    if opt_mode == "2":
        optimization_mode = "latest_lesson"
    else:
        optimization_mode = "earliest_lesson"
    
    # Get weekend preference
    skip_weekends = input("Skip weekend lessons? (y/n, default: y): ").strip().lower()
    skip_weekends = skip_weekends != "n"
    
    # Get output filename
    output_file = input("Output filename (default: optimized_schedule.ics): ").strip()
    if not output_file:
        output_file = "optimized_schedule.ics"
    
    return {
        "ics_url": ics_url,
        "preferred_group": preferred_group,
        "optimization_mode": optimization_mode,
        "skip_weekends": skip_weekends,
        "output_file": output_file
    }

def create_config(user_input):
    """Create configuration file from user input."""
    config = {
        "ics_url": user_input["ics_url"],
        "preferred_group": user_input["preferred_group"],
        "fallback_group_behavior": "use_all_if_missing",
        "optimization_mode": user_input["optimization_mode"],
        "minimum_break_minutes": 1,
        "skip_weekends": user_input["skip_weekends"],
        "timezone": "Europe/Brussels"
    }
    
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    return config

def main():
    """Main function."""
    try:
        # Check if main.py exists
        if not Path("main.py").exists():
            print("Error: main.py not found. Please run this script from the project directory.")
            sys.exit(1)
        
        # Get user input
        user_input = get_user_input()
        if not user_input:
            sys.exit(1)
        
        # Create configuration
        config = create_config(user_input)
        print(f"\nConfiguration saved to config.json")
        
        # Import and run optimizer
        from main import UHasseltScheduleOptimizer
        
        print("\nStarting optimization...")
        optimizer = UHasseltScheduleOptimizer("config.json")
        
        output_file = optimizer.run_optimization(
            config["ics_url"], 
            user_input["output_file"]
        )
        
        print(f"\n✅ Optimization completed successfully!")
        print(f"📅 Optimized schedule saved to: {output_file}")
        print(f"📊 You can now import this file into Google Calendar or any other calendar app.")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
