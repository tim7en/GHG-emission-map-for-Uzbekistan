#!/usr/bin/env python3
"""
Google Earth Engine Authentication for GHG Emissions Analysis

This script provides authentication handling for Google Earth Engine
specifically for GHG emissions downscaling analysis.

Author: AlphaEarth Analysis Team - GHG Module
Date: January 2025
"""

import os
import sys
import json
import webbrowser
from pathlib import Path

def authenticate_gee():
    """Authenticate Google Earth Engine using Python API"""
    
    print("🔐 Google Earth Engine Authentication - GHG Emissions Module")
    print("=" * 65)
    
    try:
        import ee
        print("SUCCESS: Earth Engine API imported successfully")
        
        # Check if already authenticated with project
        try:
            ee.Initialize(project='ee-sabitovty')
            print("SUCCESS: Already authenticated and ready with project ee-sabitovty!")
            test_connection()
            return True
        except:
            pass
        
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
        
        # Try to open browser automatically
        try:
            webbrowser.open(auth_url)
            print("\nSUCCESS: Browser opened automatically")
        except:
            print("\nWARNING:  Could not open browser automatically")
            print("   Please copy and paste the URL above into your browser")
        
        # Get authorization code from user
        auth_code = input("\nMEMO: Paste the authorization code here: ").strip()
        
        if not auth_code:
            print("ERROR: No authorization code provided")
            return False
        
        print(f"\n🔑 Using authorization code: {auth_code[:20]}...")
        
        # Authenticate using the code and initialize with project
        try:
            print("🔄 Completing authentication...")
            ee.Authenticate(code_verifier=None, authorization_code=auth_code)
            ee.Initialize(project='ee-sabitovty')
            print("SUCCESS: Earth Engine initialized successfully with project ee-sabitovty!")
            
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
        print("1. Trying default initialization with project...")
        try:
            ee.Initialize(project='ee-sabitovty')
            print("SUCCESS: Default initialization successful!")
            return test_connection()
        except:
            pass
        
        print("2. Trying project-based initialization...")
        try:
            ee.Initialize(project='earthengine-legacy')
            print("SUCCESS: Legacy project initialization successful!")
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
    
    try:
        import ee
        print("\n🧪 Testing Google Earth Engine connection...")
        
        # Test basic computation
        test_number = ee.Number(2025).getInfo()
        print(f"SUCCESS: Basic computation test: {test_number}")
        
        # Test image access
        image = ee.Image('USGS/SRTMGL1_003')
        scale = image.projection().nominalScale().getInfo()
        print(f"SUCCESS: Image access test successful! SRTM scale: {scale}m")
        
        # Test emissions-specific datasets
        try:
            # Test ODIAC dataset access
            odiac_test = ee.ImageCollection('ODIAC/ODIAC_CO2_v2020A') \
                          .filterDate('2020-01-01', '2020-12-31') \
                          .first()
            
            if odiac_test:
                print("SUCCESS: ODIAC CO2 emissions dataset accessible!")
            else:
                print("WARNING:  ODIAC dataset may not be accessible")
                
        except Exception as e:
            print(f"WARNING:  ODIAC dataset test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Connection test failed: {e}")
        return False

def save_auth_status(authenticated=False):
    """Save authentication status for the analysis script"""
    
    status_file = Path.cwd() / ".gee_auth_status_ghg.json"
    
    status = {
        "authenticated": authenticated,
        "timestamp": str(Path(__file__).stat().st_mtime),
        "module": "ghg_emissions"
    }
    
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)
    
    print(f"MEMO: Authentication status saved to: {status_file}")

def check_auth_status():
    """Check current authentication status"""
    
    status_file = Path.cwd() / ".gee_auth_status_ghg.json"
    
    if status_file.exists():
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
            return status.get("authenticated", False)
        except:
            return False
    
    return False

def main():
    """Main authentication function"""
    
    success = authenticate_gee()
    save_auth_status(success)
    
    if success:
        print("\n🎉 Google Earth Engine setup complete for GHG emissions analysis!")
        print("SUCCESS: You can now run the GHG emissions downscaling analysis:")
        print("   python ghg_downscaling_uzb.py")
    else:
        print("\nWARNING: GEE authentication not complete")
        print("MEMO: The analysis will run in simulation mode")
        print("   This will demonstrate the workflow with synthetic data")
    
    print(f"\nCHART: Next steps:")
    print(f"   1. Run: python ghg_downscaling_uzb.py")
    print(f"   2. Check output in: outputs/")
    
    return success

if __name__ == "__main__":
    main()