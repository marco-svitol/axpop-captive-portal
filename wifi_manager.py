#!/usr/bin/env python3
"""
WiFi Manager for DuneBugger Captive Portal
Handles WiFi network scanning and connection using NetworkManager CLI tools
"""

import subprocess
import json
import logging
import re
import time
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

class WiFiManager:
    """WiFi management class using NetworkManager CLI tools"""
    
    def __init__(self):
        self.interface_name = self._get_wireless_interface()
        logger.info(f"Initialized WiFiManager with interface: {self.interface_name}")
    
    def _get_wireless_interface(self) -> Optional[str]:
        """Get the name of the wireless interface"""
        try:
            # Get wireless interfaces using nmcli
            result = subprocess.run(['nmcli', 'device', 'status'], 
                                  capture_output=True, text=True, check=True)
            
            for line in result.stdout.split('\n'):
                if 'wifi' in line:
                    parts = line.split()
                    if parts:
                        return parts[0]
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("nmcli not available")
        
        try:
            # Fallback: try common interface names with iwconfig
            for interface in ['wlan0', 'wlp3s0', 'wlo1']:
                try:
                    subprocess.run(['iwconfig', interface], 
                                 capture_output=True, check=True)
                    return interface
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
        except Exception:
            pass
                    
        logger.warning("No wireless interface found, using mock data")
        return "wlan0"  # Return default for mock testing
    
    def scan_networks(self) -> List[Dict[str, str]]:
        """Scan for available WiFi networks"""
        networks = []
        
        try:
            # First try with nmcli
            networks = self._scan_with_nmcli()
            if networks:
                return networks
        except Exception as e:
            logger.warning(f"nmcli scan failed: {e}")
        
        try:
            # Fallback to iwlist
            networks = self._scan_with_iwlist()
            if networks:
                return networks
        except Exception as e:
            logger.warning(f"iwlist scan failed: {e}")
        
        # If both methods fail, return mock data for testing
        logger.warning("All scan methods failed, returning mock data")
        return self._get_mock_networks()
    
    def _scan_with_nmcli(self) -> List[Dict[str, str]]:
        """Scan networks using nmcli"""
        try:
            # Rescan for fresh results
            subprocess.run(['nmcli', 'device', 'wifi', 'rescan'], 
                         capture_output=True, timeout=10)
            time.sleep(2)  # Wait for scan to complete
            
            # Get scan results
            result = subprocess.run(['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 
                                   'device', 'wifi', 'list'], 
                                  capture_output=True, text=True, check=True, timeout=10)
            
            networks = []
            seen_ssids = set()
            
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(':')
                    if len(parts) >= 3:
                        ssid = parts[0].strip()
                        signal = parts[1].strip()
                        security = parts[2].strip()
                        
                        # Skip empty SSIDs and duplicates
                        if ssid and ssid not in seen_ssids:
                            seen_ssids.add(ssid)
                            networks.append({
                                'ssid': ssid,
                                'signal_strength': signal,
                                'security': 'secured' if security else 'open',
                                'encryption': security if security else 'None'
                            })
            
            return sorted(networks, key=lambda x: int(x['signal_strength'] or 0), reverse=True)
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"nmcli scan failed: {e}")
            raise
        except subprocess.TimeoutExpired:
            logger.error("nmcli scan timed out")
            raise
    
    def _scan_with_iwlist(self) -> List[Dict[str, str]]:
        """Scan networks using iwlist (fallback method)"""
        if not self.interface_name:
            raise Exception("No wireless interface available")
        
        try:
            result = subprocess.run(['sudo', 'iwlist', self.interface_name, 'scan'], 
                                  capture_output=True, text=True, check=True, timeout=15)
            
            networks = []
            current_network = {}
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                
                if 'Cell' in line and 'Address:' in line:
                    if current_network.get('ssid'):
                        networks.append(current_network)
                    current_network = {}
                
                elif 'ESSID:' in line:
                    match = re.search(r'ESSID:"([^"]*)"', line)
                    if match:
                        current_network['ssid'] = match.group(1)
                
                elif 'Quality=' in line:
                    match = re.search(r'Quality=(\d+)/(\d+)', line)
                    if match:
                        quality = int(match.group(1))
                        max_quality = int(match.group(2))
                        signal_percent = int((quality / max_quality) * 100)
                        current_network['signal_strength'] = str(signal_percent)
                
                elif 'Encryption key:' in line:
                    if 'off' in line:
                        current_network['security'] = 'open'
                        current_network['encryption'] = 'None'
                    else:
                        current_network['security'] = 'secured'
                        current_network['encryption'] = 'WPA/WPA2'
            
            # Add the last network
            if current_network.get('ssid'):
                networks.append(current_network)
            
            # Filter out networks without SSID and remove duplicates
            unique_networks = []
            seen_ssids = set()
            
            for network in networks:
                ssid = network.get('ssid', '').strip()
                if ssid and ssid not in seen_ssids:
                    seen_ssids.add(ssid)
                    # Set defaults for missing fields
                    network.setdefault('signal_strength', '50')
                    network.setdefault('security', 'open')
                    network.setdefault('encryption', 'None')
                    unique_networks.append(network)
            
            return sorted(unique_networks, key=lambda x: int(x['signal_strength']), reverse=True)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"iwlist scan failed: {e}")
            raise
        except subprocess.TimeoutExpired:
            logger.error("iwlist scan timed out")
            raise
    
    def _get_mock_networks(self) -> List[Dict[str, str]]:
        """Return mock networks for testing when scanning fails"""
        return [
            {
                'ssid': 'DuneBugger-WiFi',
                'signal_strength': '85',
                'security': 'secured',
                'encryption': 'WPA2'
            },
            {
                'ssid': 'Home-Network',
                'signal_strength': '72',
                'security': 'secured',
                'encryption': 'WPA2'
            },
            {
                'ssid': 'Guest-WiFi',
                'signal_strength': '58',
                'security': 'open',
                'encryption': 'None'
            },
            {
                'ssid': 'Mobile-Hotspot',
                'signal_strength': '45',
                'security': 'secured',
                'encryption': 'WPA2'
            }
        ]
    
    def connect_to_network(self, ssid: str, password: str = '') -> Tuple[bool, str]:
        """Connect to a WiFi network"""
        try:
            # First try with nmcli
            return self._connect_with_nmcli(ssid, password)
        except Exception as e:
            logger.warning(f"nmcli connection failed: {e}")
            try:
                # Fallback to wpa_supplicant method
                return self._connect_with_wpa_supplicant(ssid, password)
            except Exception as e2:
                logger.error(f"All connection methods failed: {e2}")
                return False, f"Failed to connect: {str(e2)}"
    
    def _connect_with_nmcli(self, ssid: str, password: str) -> Tuple[bool, str]:
        """Connect using nmcli"""
        try:
            # Check if connection profile already exists
            try:
                subprocess.run(['nmcli', 'connection', 'show', ssid], 
                             capture_output=True, check=True)
                # Profile exists, try to connect
                result = subprocess.run(['nmcli', 'connection', 'up', ssid], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    return True, f"Connected to {ssid}"
            except subprocess.CalledProcessError:
                pass  # Profile doesn't exist, create new one
            
            # Create new connection
            cmd = ['nmcli', 'device', 'wifi', 'connect', ssid]
            if password:
                cmd.extend(['password', password])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return True, f"Successfully connected to {ssid}"
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                return False, f"Connection failed: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "Connection attempt timed out"
        except subprocess.CalledProcessError as e:
            return False, f"Network connection failed: {str(e)}"
    
    def _connect_with_wpa_supplicant(self, ssid: str, password: str) -> Tuple[bool, str]:
        """Connect using wpa_supplicant (fallback method)"""
        if not self.interface_name:
            return False, "No wireless interface available"
        
        try:
            # Create wpa_supplicant configuration
            if password:
                wpa_config = f'''
network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
'''
            else:
                wpa_config = f'''
network={{
    ssid="{ssid}"
    key_mgmt=NONE
}}
'''
            
            # Write config to temporary file
            config_file = '/tmp/wpa_supplicant_temp.conf'
            with open(config_file, 'w') as f:
                f.write(wpa_config)
            
            # Start wpa_supplicant
            subprocess.run(['sudo', 'wpa_supplicant', '-B', '-i', self.interface_name, 
                          '-c', config_file], check=True, timeout=10)
            
            # Wait a moment for connection
            time.sleep(5)
            
            # Get IP address using dhclient
            subprocess.run(['sudo', 'dhclient', self.interface_name], 
                         timeout=20, check=True)
            
            return True, f"Connected to {ssid} using wpa_supplicant"
            
        except Exception as e:
            return False, f"wpa_supplicant connection failed: {str(e)}"
    
    def get_connection_status(self) -> Dict[str, str]:
        """Get current WiFi connection status"""
        try:
            # Try nmcli first
            result = subprocess.run(['nmcli', '-t', '-f', 'DEVICE,STATE,CONNECTION', 
                                   'device', 'status'], 
                                  capture_output=True, text=True, check=True)
            
            for line in result.stdout.strip().split('\n'):
                parts = line.split(':')
                if len(parts) >= 3 and 'wifi' in line:
                    device = parts[0]
                    state = parts[1]
                    connection = parts[2]
                    
                    return {
                        'device': device,
                        'state': state,
                        'connected_network': connection if connection != '--' else None,
                        'method': 'nmcli'
                    }
                    
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Fallback to iwconfig
        if self.interface_name:
            try:
                result = subprocess.run(['iwconfig', self.interface_name], 
                                      capture_output=True, text=True)
                
                if 'ESSID:' in result.stdout:
                    match = re.search(r'ESSID:"([^"]*)"', result.stdout)
                    if match:
                        essid = match.group(1)
                        return {
                            'device': self.interface_name,
                            'state': 'connected' if essid else 'disconnected',
                            'connected_network': essid if essid else None,
                            'method': 'iwconfig'
                        }
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        
        # Return mock status for development
        return {
            'device': self.interface_name or 'wlan0',
            'state': 'disconnected',
            'connected_network': None,
            'method': 'mock'
        }
    
    def disconnect(self) -> Tuple[bool, str]:
        """Disconnect from current WiFi network"""
        try:
            # Try nmcli first
            result = subprocess.run(['nmcli', 'device', 'disconnect', 'wifi'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return True, "Disconnected from WiFi"
        except subprocess.CalledProcessError:
            pass
        
        # Fallback to taking interface down/up
        if self.interface_name:
            try:
                subprocess.run(['sudo', 'ifconfig', self.interface_name, 'down'], 
                             check=True)
                time.sleep(1)
                subprocess.run(['sudo', 'ifconfig', self.interface_name, 'up'], 
                             check=True)
                return True, "WiFi interface reset"
            except subprocess.CalledProcessError as e:
                return False, f"Failed to reset interface: {str(e)}"
        
        return False, "No method available to disconnect"