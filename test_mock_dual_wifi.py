#!/usr/bin/env python3
"""
Mock test script for dual WiFi interface functionality
Tests the logic without requiring actual WiFi hardware
"""

import sys
import logging
import unittest.mock

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_with_mock_interfaces():
    """Test with mocked WiFi interfaces"""
    print("🏜️ DuneBugger Captive Portal - Mock Dual WiFi Test")
    print("=" * 55)
    
    # Mock nmcli output with 2 WiFi interfaces
    mock_nmcli_output = """DEVICE           TYPE      STATE         CONNECTION     
wlan0            wifi      connected     MyNetwork      
wlan1            wifi      disconnected  --             
eth0             ethernet  connected     Wired connection 1
lo               loopback  unmanaged     --"""
    
    try:
        with unittest.mock.patch('subprocess.run') as mock_run:
            # Mock the nmcli device status call
            mock_run.return_value.stdout = mock_nmcli_output
            mock_run.return_value.returncode = 0
            
            print("📶 Mocking 2 WiFi interfaces: wlan0, wlan1")
            
            # Test AccessPointManager
            from access_point_manager import AccessPointManager
            
            ap_manager = AccessPointManager()
            print(f"✅ AccessPointManager created successfully")
            print(f"   AP device: {ap_manager.ap_device}")
            print(f"   Client device: {ap_manager.client_device}")
            print(f"   Available devices: {ap_manager.get_available_wlan_devices()}")
            
            # Verify different interfaces are used
            if ap_manager.ap_device != ap_manager.client_device:
                print("✅ AP and client use different interfaces")
            else:
                print("❌ AP and client using same interface")
                return False
            
            # Test WiFiManager integration
            from wifi_manager import WiFiManager
            client_interface = ap_manager.get_client_wlan_interface()
            wifi_manager = WiFiManager(interface_name=client_interface)
            
            print(f"✅ WiFiManager using client interface: {wifi_manager.interface_name}")
            
            # Test configuration validation
            config_test = {
                'ap_ssid': 'Test-AP',
                'ap_password': 'testpass123',
                'ap_ip': '192.168.50.5',
                'monitor_interval': 60,
                'ap_wlan_interface': 'wlan1',
                'client_wlan_interface': 'wlan0'
            }
            
            success, message = ap_manager.update_config(config_test)
            if success:
                print(f"✅ Configuration validation: {message}")
            else:
                print(f"❌ Configuration validation failed: {message}")
                return False
            
            # Test invalid configuration (same interfaces)
            invalid_config = config_test.copy()
            invalid_config['ap_wlan_interface'] = 'wlan0'  # Same as client
            
            success, message = ap_manager.update_config(invalid_config)
            if not success and "must be different" in message:
                print("✅ Correctly rejected same interface configuration")
            else:
                print("❌ Failed to reject invalid configuration")
                return False
            
            print("\n🎉 All mock tests passed!")
            print("\n📋 Mock Configuration:")
            print(f"   AP Interface: {ap_manager.ap_device}")
            print(f"   Client Interface: {ap_manager.client_device}")
            print(f"   Interfaces are separate: ✅")
            
            return True
            
    except Exception as e:
        print(f"❌ Mock test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_insufficient_interfaces():
    """Test behavior with insufficient interfaces"""
    print("\n🧪 Testing insufficient interface handling...")
    
    # Mock nmcli output with only 1 WiFi interface
    mock_nmcli_output_single = """DEVICE           TYPE      STATE         CONNECTION     
wlan0            wifi      disconnected  --             
eth0             ethernet  connected     Wired connection 1
lo               loopback  unmanaged     --"""
    
    try:
        with unittest.mock.patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = mock_nmcli_output_single
            mock_run.return_value.returncode = 0
            
            from access_point_manager import AccessPointManager
            
            try:
                ap_manager = AccessPointManager()
                print("❌ Should have failed with insufficient interfaces")
                return False
            except ValueError as e:
                if "Two WiFi interfaces are required" in str(e):
                    print("✅ Correctly detected insufficient interfaces")
                    return True
                else:
                    print(f"❌ Unexpected error: {e}")
                    return False
                    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    print("Testing dual WiFi interface logic...")
    
    # Test with sufficient interfaces
    test1_ok = test_with_mock_interfaces()
    
    # Test with insufficient interfaces
    test2_ok = test_insufficient_interfaces()
    
    if test1_ok and test2_ok:
        print("\n🎉 All logic tests passed!")
        print("\n📝 Ready for hardware deployment:")
        print("   - Ensure Raspberry Pi has 2 WiFi interfaces")
        print("   - Run on actual hardware with: python app.py")
        print("   - Configure interfaces via web UI if needed")
        return True
    else:
        print("\n❌ Some tests failed")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)