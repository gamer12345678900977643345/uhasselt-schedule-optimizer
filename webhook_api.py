#!/usr/bin/env python3
"""
Webhook API for UHasselt Schedule Optimizer
Provides REST API endpoints for schedule optimization and Google Calendar integration.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from main import UHasseltScheduleOptimizer
from google_calendar_integration import GoogleCalendarIntegration


# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global optimizer instance
optimizer = None


def initialize_optimizer():
    """Initialize the optimizer with default config."""
    global optimizer
    try:
        optimizer = UHasseltScheduleOptimizer()
        logger.info("Optimizer initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize optimizer: {e}")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })


@app.route('/optimize', methods=['POST'])
def optimize_schedule():
    """Optimize schedule from ICS URL."""
    try:
        data = request.get_json()
        
        if not data or 'ics_url' not in data:
            return jsonify({"error": "ics_url is required"}), 400
        
        # Get parameters
        ics_url = data['ics_url']
        preferred_group = data.get('preferred_group', 'A')
        optimization_mode = data.get('optimization_mode', 'earliest_lesson')
        sync_to_google = data.get('sync_to_google', False)
        calendar_name = data.get('calendar_name', 'UHasselt Optimized Schedule')
        
        # Create temporary config
        config = {
            "preferred_group": preferred_group,
            "fallback_group_behavior": "use_all_if_missing",
            "optimization_mode": optimization_mode,
            "minimum_break_minutes": 1,
            "skip_weekends": True,
            "timezone": "Europe/Brussels"
        }
        
        # Initialize optimizer with config
        temp_optimizer = UHasseltScheduleOptimizer()
        temp_optimizer.config = config
        
        # Run optimization
        result = temp_optimizer.run_optimization(
            ics_url=ics_url,
            output_path="optimized_schedule.ics",
            sync_to_google=sync_to_google,
            calendar_name=calendar_name
        )
        
        return jsonify({
            "success": True,
            "output_file": result['output_file'],
            "google_calendar_url": result.get('google_calendar_url'),
            "message": "Schedule optimized successfully"
        })
        
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download optimized schedule file."""
    try:
        file_path = Path("output") / filename
        
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/google-calendar/sync', methods=['POST'])
def sync_to_google_calendar():
    """Sync optimized schedule to Google Calendar."""
    try:
        data = request.get_json()
        
        if not data or 'ics_url' not in data:
            return jsonify({"error": "ics_url is required"}), 400
        
        # Get parameters
        ics_url = data['ics_url']
        calendar_name = data.get('calendar_name', 'UHasselt Optimized Schedule')
        preferred_group = data.get('preferred_group', 'A')
        optimization_mode = data.get('optimization_mode', 'earliest_lesson')
        
        # Create temporary config
        config = {
            "preferred_group": preferred_group,
            "fallback_group_behavior": "use_all_if_missing",
            "optimization_mode": optimization_mode,
            "minimum_break_minutes": 1,
            "skip_weekends": True,
            "timezone": "Europe/Brussels"
        }
        
        # Initialize optimizer
        temp_optimizer = UHasseltScheduleOptimizer()
        temp_optimizer.config = config
        
        # Download and parse ICS
        ics_content = temp_optimizer.download_ics(ics_url)
        calendar = temp_optimizer.parse_ics(ics_content)
        
        # Optimize schedule
        optimized_calendar = temp_optimizer.optimize_schedule(calendar)
        
        # Sync to Google Calendar
        integration = GoogleCalendarIntegration()
        google_url = integration.sync_schedule(optimized_calendar, calendar_name)
        
        if google_url:
            return jsonify({
                "success": True,
                "google_calendar_url": google_url,
                "message": "Schedule synced to Google Calendar successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to sync to Google Calendar"
            }), 500
            
    except Exception as e:
        logger.error(f"Google Calendar sync failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration."""
    try:
        if optimizer:
            return jsonify(optimizer.config)
        else:
            return jsonify({"error": "Optimizer not initialized"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/config', methods=['POST'])
def update_config():
    """Update configuration."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Configuration data is required"}), 400
        
        # Update global optimizer config
        if optimizer:
            optimizer.config.update(data)
            
            # Save to config file
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(optimizer.config, f, indent=2)
            
            return jsonify({
                "success": True,
                "message": "Configuration updated successfully",
                "config": optimizer.config
            })
        else:
            return jsonify({"error": "Optimizer not initialized"}), 500
            
    except Exception as e:
        logger.error(f"Config update failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/status', methods=['GET'])
def get_status():
    """Get system status and recent activity."""
    try:
        # Check if output directory exists and has files
        output_dir = Path("output")
        recent_files = []
        
        if output_dir.exists():
            recent_files = [
                {
                    "filename": f.name,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    "size": f.stat().st_size
                }
                for f in output_dir.glob("*.ics")
            ]
            # Sort by modification time, newest first
            recent_files.sort(key=lambda x: x["modified"], reverse=True)
        
        return jsonify({
            "status": "running",
            "timestamp": datetime.utcnow().isoformat(),
            "recent_files": recent_files[:5],  # Last 5 files
            "optimizer_initialized": optimizer is not None
        })
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500


def main():
    """Run the webhook API server."""
    # Create necessary directories
    Path("logs").mkdir(exist_ok=True)
    Path("output").mkdir(exist_ok=True)
    
    # Initialize optimizer
    initialize_optimizer()
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"Starting UHasselt Schedule Optimizer API on port {port}")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == "__main__":
    main()
