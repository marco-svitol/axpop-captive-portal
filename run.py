#!/usr/bin/env python3
"""
DuneBugger Captive Portal Runner
Production runner for the captive portal application
"""

import os
import sys
import logging
import signal
import time
import threading
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

from app import app, socketio

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/dunebugger-portal.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class CaptivePortalRunner:
    def __init__(self):
        self.running = True
        self.server_thread = None
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        # Stop the socketio server
        if hasattr(socketio, 'stop'):
            socketio.stop()
        # Exit the process
        sys.exit(0)
    
    def check_privileges(self):
        """Check if running with sufficient privileges"""
        if os.geteuid() != 0:
            logger.warning("Not running as root. Some network operations may fail.")
            return False
        return True
    
    def setup_environment(self):
        """Setup the runtime environment"""
        # Create log directory if it doesn't exist
        log_dir = Path('/var/log')
        log_dir.mkdir(exist_ok=True)
        
        # Ensure static directories exist
        static_dirs = ['static/css', 'static/js', 'templates']
        for dir_path in static_dirs:
            (current_dir / dir_path).mkdir(parents=True, exist_ok=True)
    
    def run(self):
        """Run the captive portal application"""
        logger.info("Starting DuneBugger Captive Portal...")
        
        self.check_privileges()
        self.setup_environment()
        
        try:
            # Run the Flask-SocketIO application
            logger.info("Server starting on port 80...")
            socketio.run(
                app,
                host='0.0.0.0',
                port=80,
                debug=False,
                use_reloader=False,
                log_output=True,
                allow_unsafe_werkzeug=True  # Allow for production use
            )
        except KeyboardInterrupt:
            logger.info("Received KeyboardInterrupt, shutting down...")
            self.running = False
        except PermissionError:
            logger.error("Permission denied to bind to port 80. Run as root or use a different port.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            sys.exit(1)
        finally:
            logger.info("Application shutdown complete.")

if __name__ == '__main__':
    runner = CaptivePortalRunner()
    try:
        runner.run()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application crashed: {e}")
        sys.exit(1)