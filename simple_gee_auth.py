#!/usr/bin/env python3
"""
Simple Google Earth Engine Authentication for AlphaEarth Analysis

This script handles GEE authentication using Python directly, avoiding 
CLI permission issues.

Usage:
    python simple_gee_auth.py

Author: AlphaEarth Analysis Team
Date: August 11, 2025
"""

import os
import sys
import json
from pathlib import Path

def authenticate_gee():
    """Authenticate Google Earth Engine using Python API"""
    
    print("🔐 Google Earth Engine Authentication")
    print("=" * 45)
    
    try:
        import ee
        print("SUCCESS: Earth Engine API imported successfully")
        
        # Create local credentials directory
        local_creds_dir = Path.cwd() / ".earthengine"
        local_creds_dir.mkdir(exist_ok=True)
        print(f"📁 Using local credentials directory: {local_creds_dir}")
        
        # Set environment variable
        os.environ['EARTHENGINE_CREDENTIALS_DIR'] = str(local_creds_dir)
        
        print("\nGLOBE: Please follow these steps:")
        print("1. Open the URL below in your web browser")
        print("2. Sign in with your Google account")
        print("3. Copy the authorization code")
        print("4. Paste it back here")
        
        # Generate authentication URL
        auth_url = ("https://accounts.google.com/o/oauth2/auth?"
                   "client_id=517222506229-vsmmajv00ul0bs7p89v5m89qs8eb9359.apps.googleusercontent.com&"
                   "scope=https://www.googleapis.com/auth/earthengine%20"
                   "https://www.googleapis.com/auth/cloud-platform&"
                   "redirect_uri=urn:ietf:wg:oauth:2.0:oob&"
                   "response_type=code")
        
        print(f"\n🔗 Authentication URL:")
        print(f"{auth_url}")
        print("\n" + "="*80)
        
        # Get authorization code from user
        auth_code = input("\nMEMO: Enter the authorization code from the browser: ").strip()
        
        if not auth_code:
            print("ERROR: No authorization code provided")
            return False
        
        try:
            # Try to authenticate with the code
            ee.Authenticate(authorization_code=auth_code)
            print("SUCCESS: Authentication successful!")
            
            # Test initialization
            ee.Initialize()
            print("SUCCESS: Earth Engine initialized successfully!")
            
            # Test with a simple query
            test_connection()
            
            return True
            
        except Exception as e:
            print(f"ERROR: Authentication failed: {e}")
            print("Trying alternative authentication method...")
            return try_alternative_auth()
            
    except ImportError:
        print("ERROR: Earth Engine API not available")
        print("Please install with: pip install earthengine-api")
        return False
    except Exception as e:
        print(f"ERROR: Authentication error: {e}")
        return try_alternative_auth()

def try_alternative_auth():
    """Try alternative authentication methods"""
    
    print("\n🔄 Trying alternative authentication...")
    
    try:
        import ee
        
        # Alternative initialization methods
        print("1. Trying default initialization...")
        try:
            ee.Initialize()
            print("SUCCESS: Default initialization successful!")
            return test_connection()
        except:
            pass
        
        print("2. Trying project-based initialization...")
        try:
            ee.Initialize(project='earthengine-legacy')
            print("SUCCESS: Project-based initialization successful!")
            return test_connection()
        except:
            pass
        
        print("3. Trying cloud platform initialization...")
        try:
            ee.Initialize(opt_url='https://earthengine.googleapis.com')
            print("SUCCESS: Cloud platform initialization successful!")
            return test_connection()
        except:
            pass
        
        print("WARNING: All authentication methods failed")
        print("Running in simulation mode...")
        return False
        
    except Exception as e:
        print(f"ERROR: Alternative authentication failed: {e}")
        return False

def test_connection():
    """Test Earth Engine connection with a simple query"""
    
    print("\n🧪 Testing Earth Engine connection...")
    
    try:
        import ee
        
        # Test with Uzbekistan bounds
        uzbekistan = ee.Geometry.Rectangle([55.9, 37.2, 73.2, 45.6])
        
        # Simple test: count MODIS images
        modis_collection = ee.ImageCollection('MODIS/061/MOD11A1') \
            .filterDate('2023-01-01', '2023-01-31') \
            .filterBounds(uzbekistan)
        
        count = modis_collection.size().getInfo()
        print(f"SUCCESS: Connection test successful!")
        print(f"   Found {count} MODIS LST images for January 2023")
        
        # Test image access
        first_image = modis_collection.first()
        image_id = first_image.get('system:id').getInfo()
        print(f"   Sample image ID: {image_id}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Connection test failed: {e}")
        return False

def save_auth_status(authenticated=False):
    """Save authentication status for the analysis script"""
    
    status_file = Path.cwd() / ".gee_auth_status.json"
    
    status = {
        "authenticated": authenticated,
        "timestamp": str(Path(__file__).stat().st_mtime),
        "method": "python_api" if authenticated else "simulation"
    }
    
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)
    
    print(f"STORAGE: Authentication status saved to {status_file}")

def main():
    """Main authentication function"""
    
    success = authenticate_gee()
    save_auth_status(success)
    
    if success:
        print("\n🎉 Google Earth Engine setup complete!")
        print("SUCCESS: You can now run the urban heat analysis:")
        print("   python urban_heat_gee_standalone.py")
    else:
        print("\nWARNING: GEE authentication not complete")
        print("MEMO: The analysis will run in simulation mode")
        print("   This will demonstrate the workflow with synthetic data")
    
    print(f"\nCHART: Next steps:")
    print(f"   1. Run: python urban_heat_gee_standalone.py")
    print(f"   2. Check output in: gee_urban_heat_analysis/")
    
    return success

if __name__ == "__main__":
    main()
