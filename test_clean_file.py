#!/usr/bin/env python3
"""
Simple validation test for the clean QGIS file.
"""

import json
import os

def test_clean_file():
    file_path = "fixed_complete_uzbekistan_cadastral_data/VILOYAT_BORDER_2023_zoom_1/VILOYAT_BORDER_2023_zoom_1_qgis_fixed_clean.geojson"
    
    print(f"Testing: {os.path.basename(file_path)}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    file_size = os.path.getsize(file_path)
    print(f"📁 File size: {file_size / (1024*1024):.2f} MB")
    
    try:
        # Load and validate the entire JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Valid JSON structure")
        print(f"✓ Type: {data.get('type')}")
        print(f"✓ CRS: {data.get('crs', {}).get('properties', {}).get('name')}")
        print(f"✓ Features count: {len(data.get('features', []))}")
        
        if data.get('features'):
            feature = data['features'][0]
            print(f"✓ First feature geometry: {feature.get('geometry', {}).get('type')}")
            print(f"✓ First feature region: {feature.get('properties', {}).get('region')}")
        
        print(f"\n🎉 SUCCESS! File is ready for QGIS testing")
        print(f"\n📋 QGIS TESTING INSTRUCTIONS:")
        print(f"1. Open QGIS")
        print(f"2. Layer → Add Layer → Add Vector Layer")
        print(f"3. Browse to: {os.path.abspath(file_path)}")
        print(f"4. Click 'Add'")
        print(f"\nExpected: {len(data.get('features', []))} polygon features should load")
        print(f"Coordinate system: WGS84 (EPSG:4326)")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_clean_file()
