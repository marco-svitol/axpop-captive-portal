#!/usr/bin/env python3
"""
DuneBugger Captive Portal
A Flask-based WiFi captive portal for Raspberry Pi
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_socketio import SocketIO, emit
import json
import logging
import os
import signal
import sys
from wifi_manager import WiFiManager
from access_point_manager import AccessPointManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dunebugger-captive-portal-secret-key'
socketio = SocketIO(app)

# Initialize WiFi manager and Access Point manager
wifi_manager = WiFiManager()
ap_manager = AccessPointManager()

@app.route('/')
def index():
    """Main captive portal page"""
    return render_template('index.html')

@app.route('/api/scan')
def scan_networks():
    """API endpoint to scan for available WiFi networks"""
    try:
        networks = wifi_manager.scan_networks()
        return jsonify({
            'success': True,
            'networks': networks
        })
    except Exception as e:
        logger.error(f"Failed to scan networks: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/connect', methods=['POST'])
def connect_to_network():
    """API endpoint to connect to a WiFi network"""
    try:
        data = request.get_json()
        ssid = data.get('ssid')
        password = data.get('password', '')
        
        if not ssid:
            return jsonify({
                'success': False,
                'error': 'SSID is required'
            }), 400
        
        # Attempt to connect to the network
        success, message = wifi_manager.connect_to_network(ssid, password)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully connected to {ssid}'
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to connect to network: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status')
def connection_status():
    """API endpoint to get current connection status"""
    try:
        status = wifi_manager.get_connection_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/disconnect')
def disconnect():
    """API endpoint to disconnect from current network"""
    try:
        success, message = wifi_manager.disconnect()
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        logger.error(f"Failed to disconnect: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ap/status')
def ap_status():
    """API endpoint to get access point status"""
    try:
        status = ap_manager.get_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logger.error(f"Failed to get AP status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ap/start', methods=['POST'])
def start_ap():
    """API endpoint to manually start access point"""
    try:
        success, message = ap_manager.setup_access_point()
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        logger.error(f"Failed to start AP: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ap/stop', methods=['POST'])
def stop_ap():
    """API endpoint to manually stop access point"""
    try:
        success, message = ap_manager.teardown_access_point()
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        logger.error(f"Failed to stop AP: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ap/config', methods=['GET'])
def get_ap_config():
    """API endpoint to get access point configuration"""
    try:
        config = ap_manager.config.copy()
        # Don't expose password in GET request
        if 'ap_password' in config:
            config['ap_password'] = '***' if config['ap_password'] else ''
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        logger.error(f"Failed to get AP config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ap/config', methods=['POST'])
def update_ap_config():
    """API endpoint to update access point configuration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No configuration data provided'
            }), 400
        
        success, message = ap_manager.update_config(data)
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        logger.error(f"Failed to update AP config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ap/monitoring/start', methods=['POST'])
def start_monitoring():
    """API endpoint to start connectivity monitoring"""
    try:
        ap_manager.start_monitoring()
        return jsonify({
            'success': True,
            'message': 'Monitoring started'
        })
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ap/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """API endpoint to stop connectivity monitoring"""
    try:
        ap_manager.stop_monitoring()
        return jsonify({
            'success': True,
            'message': 'Monitoring stopped'
        })
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info('Client connected')
    emit('status', {'message': 'Connected to DuneBugger Captive Portal'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info('Client disconnected')

@socketio.on('scan_request')
def handle_scan_request():
    """Handle WebSocket scan request"""
    try:
        networks = wifi_manager.scan_networks()
        emit('scan_result', {
            'success': True,
            'networks': networks
        })
    except Exception as e:
        logger.error(f"WebSocket scan failed: {e}")
        emit('scan_result', {
            'success': False,
            'error': str(e)
        })

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    # Stop AP monitoring and clean up
    try:
        ap_manager.stop_monitoring()
    except Exception as e:
        logger.error(f"Error during AP cleanup: {e}")
    sys.exit(0)

if __name__ == '__main__':
    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create templates and static directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    
    try:
        # Start AP monitoring
        logger.info("Starting access point monitoring...")
        ap_manager.start_monitoring()
        
        # Run the application
        logger.info(f"Starting server on port {port}...")
        socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, shutting down...")
    except Exception as e:
        logger.error(f"Application error: {e}")
    finally:
        # Clean up AP monitoring
        try:
            ap_manager.stop_monitoring()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        logger.info("Application shutdown complete.")