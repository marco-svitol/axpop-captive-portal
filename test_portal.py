#!/usr/bin/env python3
"""
Test script for DuneBugger Captive Portal
"""

import sys
import requests
import time
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

def test_server(host='localhost', port=80):
    """Test if the server is running and responding"""
    base_url = f"http://{host}:{port}"
    
    print(f"Testing DuneBugger Captive Portal at {base_url}")
    print("=" * 50)
    
    # Test main page
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Main page accessible")
        else:
            print(f"❌ Main page returned {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach main page: {e}")
        return False
    
    # Test scan API
    try:
        response = requests.get(f"{base_url}/api/scan", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Network scan successful ({len(data.get('networks', []))} networks found)")
            else:
                print(f"⚠️ Network scan failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Scan API returned {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach scan API: {e}")
    
    # Test status API
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                status = data.get('status', {})
                print(f"✅ Status API working (Device: {status.get('device', 'unknown')})")
            else:
                print(f"⚠️ Status API failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Status API returned {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach status API: {e}")
    
    print("\nTest completed!")
    return True

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test DuneBugger Captive Portal')
    parser.add_argument('--host', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=80, help='Server port (default: 80)')
    
    args = parser.parse_args()
    
    test_server(args.host, args.port)