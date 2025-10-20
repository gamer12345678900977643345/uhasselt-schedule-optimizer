#!/usr/bin/env python3
"""
Setup script for UHasselt Schedule Optimizer
Handles initial configuration and Google Calendar setup.
"""

import json
import os
import sys
from pathlib import Path


def create_directories():
    """Create necessary directories."""
    directories = ["logs", "output", "config"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")


def setup_configuration():
    """Setup initial configuration."""
    print("\n=== Configuration Setup ===")
    
    # Check if config already exists
    if Path("config.json").exists():
        response = input("config.json already exists. Overwrite? (y/n): ").lower()
        if response != 'y':
            print("Keeping existing configuration.")
            return
    
    # Get ICS URL
    print("\n1. MyTimetable ICS URL")
    print("   Go to https://mytimetable.uhasselt.be/")
    print("   Log in and go to 'Export' -> 'iCal'")
    print("   Copy the ICS URL")
    ics_url = input("   Enter your MyTimetable ICS URL: ").strip()
    
    if not ics_url:
        print("❌ ICS URL is required!")
        return False
    
    # Get preferred group
    print("\n2. Preferred Group")
    print("   Available groups: A, B, C, D, E")
    preferred_group = input("   Enter your preferred group (default: A): ").strip().upper()
    if not preferred_group:
        preferred_group = "A"
    
    # Get optimization mode
    print("\n3. Optimization Mode")
    print("   1. earliest_lesson - Choose earliest lesson time")
    print("   2. latest_lesson - Choose latest lesson time")
    opt_mode = input("   Choose optimization mode (1 or 2, default: 1): ").strip()
    optimization_mode = "latest_lesson" if opt_mode == "2" else "earliest_lesson"
    
    # Get weekend preference
    skip_weekends = input("\n4. Skip weekend lessons? (y/n, default: y): ").strip().lower()
    skip_weekends = skip_weekends != "n"
    
    # Get Google Calendar preference
    print("\n5. Google Calendar Integration")
    google_enabled = input("   Enable Google Calendar sync? (y/n, default: n): ").strip().lower()
    google_enabled = google_enabled == "y"
    
    calendar_name = "UHasselt Optimized Schedule"
    if google_enabled:
        calendar_name = input("   Enter calendar name (default: UHasselt Optimized Schedule): ").strip()
        if not calendar_name:
            calendar_name = "UHasselt Optimized Schedule"
    
    # Create configuration
    config = {
        "ics_url": ics_url,
        "preferred_group": preferred_group,
        "fallback_group_behavior": "use_all_if_missing",
        "optimization_mode": optimization_mode,
        "minimum_break_minutes": 1,
        "skip_weekends": skip_weekends,
        "timezone": "Europe/Brussels",
        "google_calendar": {
            "enabled": google_enabled,
            "calendar_name": calendar_name,
            "credentials_file": "credentials.json"
        },
        "api": {
            "enabled": True,
            "port": 5000,
            "host": "0.0.0.0"
        },
        "logging": {
            "level": "INFO",
            "file": "logs/optimizer.log"
        }
    }
    
    # Save configuration
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuration saved to config.json")
    return True


def setup_google_calendar():
    """Setup Google Calendar credentials."""
    print("\n=== Google Calendar Setup ===")
    
    if not Path("config.json").exists():
        print("❌ Please run configuration setup first!")
        return False
    
    # Load config
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    if not config.get("google_calendar", {}).get("enabled", False):
        print("Google Calendar integration is disabled in config.")
        return True
    
    print("To enable Google Calendar integration:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a new project or select existing one")
    print("3. Enable Google Calendar API")
    print("4. Create credentials (OAuth 2.0 Client ID)")
    print("5. Download the credentials JSON file")
    print("6. Rename it to 'credentials.json' and place it in this directory")
    
    if Path("credentials.json").exists():
        print("✅ credentials.json found!")
        return True
    else:
        print("❌ credentials.json not found. Please follow the steps above.")
        return False


def test_installation():
    """Test the installation."""
    print("\n=== Testing Installation ===")
    
    try:
        # Test imports
        print("Testing imports...")
        from main import UHasseltScheduleOptimizer
        from google_calendar_integration import GoogleCalendarIntegration
        print("✅ All imports successful")
        
        # Test optimizer initialization
        print("Testing optimizer...")
        optimizer = UHasseltScheduleOptimizer()
        print("✅ Optimizer initialized successfully")
        
        # Test configuration
        if Path("config.json").exists():
            print("✅ Configuration file found")
        else:
            print("❌ Configuration file missing")
            return False
        
        print("\n🎉 Installation test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False


def main():
    """Main setup function."""
    print("=== UHasselt Schedule Optimizer Setup ===")
    print("This script will help you configure the optimizer.\n")
    
    # Create directories
    create_directories()
    
    # Setup configuration
    if not setup_configuration():
        print("❌ Configuration setup failed!")
        sys.exit(1)
    
    # Setup Google Calendar
    setup_google_calendar()
    
    # Test installation
    if test_installation():
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run: python main.py --config config.json")
        print("2. Or run the API: python webhook_api.py")
        print("3. Check the README.md for more information")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
