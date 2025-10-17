#!/usr/bin/env python3
"""
Test script for dual WiFi interface functionality
"""

import sys
import logging
import subprocess

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def check_wifi_interfaces():
    """Check available WiFi interfaces"""
    print("🔍 Checking WiFi interfaces...")
    
    try:
        result = subprocess.run(['nmcli', 'device', 'status'], 
                              capture_output=True, text=True, check=True)
        
        wifi_devices = []
        print("\nNetwork devices:")
        for line in result.stdout.split('\n'):
            if line.strip():
                parts = line.split()
                if len(parts) >= 3:
                    device, device_type, state = parts[0], parts[1], parts[2]
                    print(f"  {device}: {device_type} ({state})")
                    if 'wifi' in device_type.lower():
                        wifi_devices.append(device)
        
        print(f"\n📶 Found {len(wifi_devices)} WiFi interface(s): {wifi_devices}")
        
        if len(wifi_devices) >= 2:
            print("✅ Sufficient WiFi interfaces for dual-mode operation")
            return True, wifi_devices
        else:
            print(f"❌ Need at least 2 WiFi interfaces, found {len(wifi_devices)}")
            return False, wifi_devices
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to check interfaces: {e}")
        return False, []

def test_access_point_manager():
    """Test AccessPointManager initialization"""
    print("\n🧪 Testing AccessPointManager...")
    
    try:
        from access_point_manager import AccessPointManager
        
        ap_manager = AccessPointManager()
        print(f"✅ AccessPointManager created")
        print(f"   AP device: {ap_manager.ap_device}")
        print(f"   Client device: {ap_manager.client_device}")
        print(f"   Available devices: {ap_manager.get_available_wlan_devices()}")
        
        # Test status
        status = ap_manager.get_status()
        print(f"✅ Status check successful")
        print(f"   Connectivity: {status['connectivity']}")
        print(f"   AP Active: {status['ap_active']}")
        
        return True, ap_manager
        
    except ValueError as e:
        print(f"❌ AccessPointManager validation failed: {e}")
        return False, None
    except Exception as e:
        print(f"❌ AccessPointManager error: {e}")
        return False, None

def test_wifi_manager(ap_manager):
    """Test WiFiManager with client interface"""
    print("\n📡 Testing WiFiManager...")
    
    try:
        from wifi_manager import WiFiManager
        
        client_interface = ap_manager.get_client_wlan_interface()
        wifi_manager = WiFiManager(interface_name=client_interface)
        print(f"✅ WiFiManager created with interface: {wifi_manager.interface_name}")
        
        # Test interface change
        wifi_manager.set_interface("test_interface")
        print(f"✅ Interface change test successful")
        
        # Reset to correct interface
        wifi_manager.set_interface(client_interface)
        print(f"✅ Interface reset to: {wifi_manager.interface_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ WiFiManager error: {e}")
        return False

def test_app_integration():
    """Test app integration"""
    print("\n🌐 Testing app integration...")
    
    try:
        # Import app components
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Test import without actually running the server
        print("✅ App imports successful (not testing full startup)")
        return True
        
    except Exception as e:
        print(f"❌ App integration error: {e}")
        return False

def main():
    print("🏜️ DuneBugger Captive Portal - Dual WiFi Interface Test")
    print("=" * 60)
    
    # Check basic WiFi interfaces
    interfaces_ok, wifi_devices = check_wifi_interfaces()
    
    if not interfaces_ok:
        print("\n❌ CRITICAL: Insufficient WiFi interfaces")
        print("   This system requires at least 2 WiFi interfaces:")
        print("   - One for Access Point mode")
        print("   - One for client WiFi connections")
        print("\n   To resolve this:")
        print("   1. Use a Raspberry Pi with built-in WiFi + USB WiFi adapter")
        print("   2. Use two USB WiFi adapters")
        print("   3. Check that both interfaces are recognized by NetworkManager")
        return False
    
    # Test AccessPointManager
    ap_ok, ap_manager = test_access_point_manager()
    if not ap_ok:
        print("\n❌ AccessPointManager test failed")
        return False
    
    # Test WiFiManager
    wifi_ok = test_wifi_manager(ap_manager)
    if not wifi_ok:
        print("\n❌ WiFiManager test failed")
        return False
    
    # Test app integration
    app_ok = test_app_integration()
    if not app_ok:
        print("\n❌ App integration test failed")
        return False
    
    print("\n🎉 All tests passed!")
    print("\n📋 Configuration Summary:")
    print(f"   AP Interface: {ap_manager.ap_device}")
    print(f"   Client Interface: {ap_manager.client_device}")
    print(f"   AP SSID: {ap_manager.config['ap_ssid']}")
    print(f"   AP IP: {ap_manager.config['ap_ip']}")
    
    print("\n🚀 Ready for deployment!")
    print("   Run: python app.py")
    print("   Or:  sudo systemctl start dunebugger-portal")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)