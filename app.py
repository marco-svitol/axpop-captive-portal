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
from wifi_manager import WiFiManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dunebugger-captive-portal-secret-key'
socketio = SocketIO(app)

# Initialize WiFi manager
wifi_manager = WiFiManager()

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

if __name__ == '__main__':
    # Create templates and static directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    
    # Run the application
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)