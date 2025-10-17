#!/usr/bin/env python3
"""
Access Point Manager for DuneBugger Captive Portal
Handles automatic AP setup/teardown based on network connectivity
Uses NetworkManager through nmcli commands
"""

import subprocess
import logging
import time
import threading
import json
import os
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class AccessPointManager:
    """Manages access point setup and network connectivity monitoring"""
    
    def __init__(self, config_file: str = 'ap_config.json'):
        self.config_file = config_file
        self.config = self._load_config()
        self.monitoring = False
        self.monitor_thread = None
        self.ap_active = False
        self.ap_connection_name = "DuneBugger-AP"
        self.ap_device = None
        
        # Find available WiFi device for AP
        self._find_ap_device()
        
        logger.info(f"AccessPointManager initialized with device: {self.ap_device}")
    
    def _load_config(self) -> Dict:
        """Load AP configuration from file or create default"""
        default_config = {
            "ap_ssid": "DuneBugger-Setup",
            "ap_password": "dunebugger123",
            "ap_ip": "192.168.4.1",
            "ap_netmask": "255.255.255.0",
            "ap_channel": 7,
            "monitor_interval": 60,  # seconds
            "connection_timeout": 10  # seconds for connectivity check
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load config from {self.config_file}: {e}")
        
        # Save default config
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except IOError as e:
            logger.error(f"Failed to save config: {e}")
    
    def _find_ap_device(self) -> None:
        """Find a suitable WiFi device for access point"""
        try:
            result = subprocess.run(['nmcli', 'device', 'status'], 
                                  capture_output=True, text=True, check=True)
            
            for line in result.stdout.split('\n'):
                if 'wifi' in line:
                    parts = line.split()
                    if parts and len(parts) >= 2:
                        device = parts[0]
                        state = parts[1]
                        # Prefer disconnected devices for AP
                        if state in ['disconnected', 'unavailable']:
                            self.ap_device = device
                            logger.info(f"Selected device {device} for AP (state: {state})")
                            return
                        elif not self.ap_device:  # Fallback to any wifi device
                            self.ap_device = device
            
            if not self.ap_device:
                # Fallback to common device names
                for device in ['wlan1', 'wlan0']:
                    try:
                        subprocess.run(['nmcli', 'device', 'show', device], 
                                     capture_output=True, check=True)
                        self.ap_device = device
                        break
                    except subprocess.CalledProcessError:
                        continue
                        
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to find AP device: {e}")
            self.ap_device = 'wlan0'  # Default fallback
    
    def check_connectivity(self) -> bool:
        """Check if device has internet connectivity via WiFi or Ethernet"""
        try:
            # Check for active connections
            result = subprocess.run(['nmcli', '-t', '-f', 'TYPE,STATE', 'connection', 'show', '--active'], 
                                  capture_output=True, text=True, check=True, 
                                  timeout=self.config['connection_timeout'])
            
            # Look for active ethernet or wifi connections
            for line in result.stdout.strip().split('\n'):
                if line:
                    conn_type, state = line.split(':')
                    if conn_type in ['802-3-ethernet', '802-11-wireless'] and state == 'activated':
                        # Double-check with ping test
                        return self._test_internet_connection()
            
            return False
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.warning(f"Connectivity check failed: {e}")
            return False
    
    def _test_internet_connection(self) -> bool:
        """Test actual internet connectivity with ping"""
        try:
            # Try to ping a reliable DNS server
            result = subprocess.run(['ping', '-c', '1', '-W', '3', '8.8.8.8'], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
    
    def setup_access_point(self) -> Tuple[bool, str]:
        """Set up the access point using NetworkManager"""
        if self.ap_active:
            return True, "Access point is already active"
        
        if not self.ap_device:
            return False, "No suitable WiFi device found for access point"
        
        try:
            # First, try to delete any existing AP connection
            self._cleanup_ap_connection()
            
            # Create hotspot connection
            cmd = [
                'nmcli', 'connection', 'add',
                'type', 'wifi',
                'ifname', self.ap_device,
                'con-name', self.ap_connection_name,
                'autoconnect', 'no',
                'ssid', self.config['ap_ssid']
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False, f"Failed to create connection: {result.stderr}"
            
            # Configure as access point
            cmd = [
                'nmcli', 'connection', 'modify', self.ap_connection_name,
                '802-11-wireless.mode', 'ap',
                '802-11-wireless.band', 'bg',
                '802-11-wireless.channel', str(self.config['ap_channel']),
                'ipv4.method', 'shared',
                'ipv4.addresses', f"{self.config['ap_ip']}/24"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False, f"Failed to configure AP: {result.stderr}"
            
            # Set password if provided
            if self.config['ap_password']:
                cmd = [
                    'nmcli', 'connection', 'modify', self.ap_connection_name,
                    '802-11-wireless-security.key-mgmt', 'wpa-psk',
                    '802-11-wireless-security.psk', self.config['ap_password']
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    logger.warning(f"Failed to set password: {result.stderr}")
            
            # Bring up the access point
            result = subprocess.run(['nmcli', 'connection', 'up', self.ap_connection_name], 
                                  capture_output=True, text=True, timeout=20)
            
            if result.returncode == 0:
                self.ap_active = True
                logger.info(f"Access point '{self.config['ap_ssid']}' is now active on {self.ap_device}")
                return True, f"Access point '{self.config['ap_ssid']}' started successfully"
            else:
                return False, f"Failed to start AP: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Access point setup timed out"
        except Exception as e:
            return False, f"Unexpected error setting up AP: {str(e)}"
    
    def teardown_access_point(self) -> Tuple[bool, str]:
        """Take down the access point"""
        if not self.ap_active:
            return True, "Access point is not active"
        
        try:
            # Bring down the connection
            result = subprocess.run(['nmcli', 'connection', 'down', self.ap_connection_name], 
                                  capture_output=True, text=True, timeout=10)
            
            # Clean up the connection profile
            self._cleanup_ap_connection()
            
            self.ap_active = False
            logger.info("Access point has been taken down")
            return True, "Access point stopped successfully"
            
        except subprocess.TimeoutExpired:
            return False, "Access point teardown timed out"
        except Exception as e:
            return False, f"Error taking down AP: {str(e)}"
    
    def _cleanup_ap_connection(self) -> None:
        """Clean up access point connection profile"""
        try:
            subprocess.run(['nmcli', 'connection', 'delete', self.ap_connection_name], 
                         capture_output=True, timeout=5)
        except:
            pass  # Connection might not exist
    
    def start_monitoring(self) -> None:
        """Start the connectivity monitoring thread"""
        if self.monitoring:
            logger.warning("Monitoring is already running")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Started connectivity monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop the connectivity monitoring"""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("Stopped connectivity monitoring")
        
        # Clean up AP if active
        if self.ap_active:
            self.teardown_access_point()
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        logger.info(f"Monitoring loop started (interval: {self.config['monitor_interval']}s)")
        
        while self.monitoring:
            try:
                has_connectivity = self.check_connectivity()
                
                if has_connectivity and self.ap_active:
                    # We have connectivity and AP is active - tear it down
                    logger.info("Connectivity restored, taking down access point")
                    success, message = self.teardown_access_point()
                    if success:
                        logger.info(message)
                    else:
                        logger.error(f"Failed to teardown AP: {message}")
                
                elif not has_connectivity and not self.ap_active:
                    # No connectivity and AP is not active - set it up
                    logger.info("No connectivity detected, setting up access point")
                    success, message = self.setup_access_point()
                    if success:
                        logger.info(message)
                    else:
                        logger.error(f"Failed to setup AP: {message}")
                
                # Wait for next check
                time.sleep(self.config['monitor_interval'])
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.config['monitor_interval'])
    
    def get_status(self) -> Dict:
        """Get current status of AP and connectivity"""
        return {
            'monitoring': self.monitoring,
            'ap_active': self.ap_active,
            'ap_device': self.ap_device,
            'ap_ssid': self.config['ap_ssid'],
            'connectivity': self.check_connectivity(),
            'config': self.config.copy()
        }
    
    def update_config(self, new_config: Dict) -> Tuple[bool, str]:
        """Update configuration"""
        try:
            # Validate required fields
            required_fields = ['ap_ssid', 'ap_password', 'ap_ip', 'monitor_interval']
            for field in required_fields:
                if field not in new_config:
                    return False, f"Missing required field: {field}"
            
            # Update config
            self.config.update(new_config)
            self._save_config(self.config)
            
            # If AP is active and SSID/password changed, restart it
            if self.ap_active and ('ap_ssid' in new_config or 'ap_password' in new_config):
                logger.info("AP config changed, restarting access point")
                self.teardown_access_point()
                time.sleep(2)
                self.setup_access_point()
            
            return True, "Configuration updated successfully"
            
        except Exception as e:
            return False, f"Failed to update config: {str(e)}"