#!/usr/bin/env python3
"""
Test script for Access Point Manager
"""

import sys
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

try:
    from access_point_manager import AccessPointManager
    
    print("✅ AccessPointManager imported successfully")
    
    # Create instance
    ap_manager = AccessPointManager()
    print(f"✅ AccessPointManager created with device: {ap_manager.ap_device}")
    
    # Check configuration
    print(f"✅ Configuration loaded: {ap_manager.config}")
    
    # Test connectivity check
    connectivity = ap_manager.check_connectivity()
    print(f"✅ Connectivity check: {connectivity}")
    
    # Test status
    status = ap_manager.get_status()
    print(f"✅ Status: {status}")
    
    print("\n🎉 All basic tests passed!")
    print("\nTo test full functionality:")
    print("1. Run the Flask app: python app.py")
    print("2. Open http://localhost:8080 in a browser")
    print("3. Use the Access Point panel to control the AP")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)