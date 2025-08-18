#!/usr/bin/env python3
"""
Final validation and QGIS compatibility check for combined GeoJSON files.
"""

import json
import os
from pathlib import Path

def comprehensive_qgis_validation(file_path):
    """Comprehensive validation for QGIS compatibility"""
    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE QGIS VALIDATION")
    print(f"File: {os.path.basename(file_path)}")
    print(f"{'='*60}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    file_size = os.path.getsize(file_path)
    print(f"📁 File size: {file_size / (1024*1024):.2f} MB")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read the beginning to check structure
            start_content = f.read(5000)
            
        # Parse the beginning as JSON to validate structure
        try:
            # Find the end of the first feature to parse a valid JSON chunk
            brace_count = 0
            json_chunk = ""
            for char in start_content:
                json_chunk += char
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and '"features": [' in json_chunk:
                        json_chunk += ']}'  # Close the features array and root object
                        break
            
            # Parse the chunk
            partial_data = json.loads(json_chunk)
            
            print(f"\n📋 STRUCTURE VALIDATION:")
            print(f"✓ Root type: {partial_data.get('type')}")
            print(f"✓ CRS: {partial_data.get('crs', {}).get('properties', {}).get('name')}")
            print(f"✓ Features array present: {'features' in partial_data}")
            
            if 'features' in partial_data and partial_data['features']:
                feature = partial_data['features'][0]
                print(f"✓ First feature type: {feature.get('type')}")
                print(f"✓ Geometry type: {feature.get('geometry', {}).get('type')}")
                print(f"✓ Properties present: {'properties' in feature}")
                
                # Check properties
                if 'properties' in feature:
                    props = feature['properties']
                    print(f"✓ Property keys: {list(props.keys())}")
                    
                    # Check for essential properties
                    if 'fid' in props:
                        print(f"✓ Feature ID: {props['fid']}")
                    if 'region' in props:
                        print(f"✓ Region: {props['region']}")
                    if '_metadata' in props:
                        print(f"✓ Metadata present")
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            return False
        
        # QGIS-specific checks
        print(f"\n🗺️ QGIS COMPATIBILITY CHECKS:")
        
        qgis_issues = []
        qgis_warnings = []
        
        # Check file size
        if file_size > 100 * 1024 * 1024:  # 100MB
            qgis_warnings.append("File is very large (>100MB) - may load slowly in QGIS")
        elif file_size > 50 * 1024 * 1024:  # 50MB
            qgis_warnings.append("File is large (>50MB) - may take time to load in QGIS")
        
        # Check coordinate system
        if '"EPSG:4326"' in start_content:
            print("✓ Uses WGS84 (EPSG:4326) - compatible with most QGIS projects")
        else:
            qgis_warnings.append("CRS may not be explicitly WGS84")
        
        # Check for proper FeatureCollection structure
        if '"type": "FeatureCollection"' in start_content:
            print("✓ Proper FeatureCollection format")
        else:
            qgis_issues.append("Not a valid FeatureCollection")
        
        # Check for features array
        if '"features": [' in start_content:
            print("✓ Features array present")
        else:
            qgis_issues.append("No features array found")
        
        # Report issues and warnings
        if qgis_issues:
            print(f"\n❌ CRITICAL ISSUES (will prevent QGIS loading):")
            for issue in qgis_issues:
                print(f"   - {issue}")
        
        if qgis_warnings:
            print(f"\n⚠️ WARNINGS (may affect performance):")
            for warning in qgis_warnings:
                print(f"   - {warning}")
        
        if not qgis_issues and not qgis_warnings:
            print(f"\n✅ EXCELLENT - No issues or warnings detected!")
        elif not qgis_issues:
            print(f"\n✅ GOOD - File should load in QGIS (minor warnings only)")
        
        return len(qgis_issues) == 0
        
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        return False

def print_qgis_instructions(file_path):
    """Print instructions for testing in QGIS"""
    print(f"\n{'='*60}")
    print(f"QGIS TESTING INSTRUCTIONS")
    print(f"{'='*60}")
    
    print(f"""
1. Open QGIS Desktop
2. Go to 'Layer' → 'Add Layer' → 'Add Vector Layer'
3. Click 'Browse' and select this file:
   {file_path}
4. Click 'Add'

EXPECTED RESULTS:
✓ Layer should appear in the Layers panel
✓ Features should be visible on the map
✓ Attribute table should contain:
  - fid (Feature ID)
  - region (Region name)
  - _metadata (Download metadata)
✓ Coordinate system should be EPSG:4326 (WGS 84)

TROUBLESHOOTING:
- If layer doesn't load: Check QGIS logs (View → Panels → Log Messages)
- If features are missing: Check feature count in layer properties
- If coordinates seem wrong: Verify CRS is set to EPSG:4326
- If file is too slow: Consider using a smaller subset or different zoom level

FILE INFO:
- Layer type: {os.path.basename(file_path).split('_')[0]} boundaries
- Zoom level: {os.path.basename(file_path).split('_')[-1].split('.')[0].replace('zoom_', '')}
- Coverage: Uzbekistan administrative boundaries
""")

def main():
    base_dir = "fixed_complete_uzbekistan_cadastral_data"
    
    if not os.path.exists(base_dir):
        print(f"Directory not found: {base_dir}")
        return
    
    # Find all QGIS-ready files
    qgis_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if "qgis_fixed" in file and file.endswith(".geojson"):
                qgis_files.append(os.path.join(root, file))
    
    if not qgis_files:
        print("No QGIS-ready files found. Run create_qgis_fixed.py first.")
        return
    
    print(f"Found {len(qgis_files)} QGIS-ready files for validation")
    
    # Validate each file
    for file_path in qgis_files:
        is_valid = comprehensive_qgis_validation(file_path)
        
        if is_valid:
            print_qgis_instructions(file_path)
        else:
            print(f"\n❌ File needs fixing before QGIS testing: {file_path}")

if __name__ == "__main__":
    main()
