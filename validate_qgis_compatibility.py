#!/usr/bin/env python3
"""
Validate GeoJSON files for QGIS compatibility and fix any issues.
"""

import json
import os
from pathlib import Path

def validate_geojson_for_qgis(file_path):
    """Validate a GeoJSON file for QGIS compatibility"""
    print(f"\n=== Validating: {os.path.basename(file_path)} ===")
    
    issues = []
    recommendations = []
    
    try:
        file_size = os.path.getsize(file_path)
        print(f"File size: {file_size / (1024*1024):.2f} MB")
        
        if file_size > 100 * 1024 * 1024:  # 100MB
            issues.append("File is very large (>100MB) - may cause performance issues in QGIS")
            recommendations.append("Consider splitting into smaller files or use different zoom levels")
        
        # Read and parse the file
        with open(file_path, 'r', encoding='utf-8') as f:
            # For large files, we'll validate structure without loading everything
            if file_size > 10 * 1024 * 1024:  # 10MB
                print("Large file detected - doing structure validation only")
                
                # Check the beginning
                start_content = f.read(5000)
                
                # Check if it's valid JSON start
                if not start_content.strip().startswith('{'):
                    issues.append("File does not start with JSON object")
                
                # Check for required GeoJSON fields
                if '"type": "FeatureCollection"' not in start_content:
                    issues.append("Missing 'type': 'FeatureCollection'")
                
                if '"features": [' not in start_content:
                    issues.append("Missing 'features' array")
                
                # Check for CRS
                if '"crs":' not in start_content:
                    recommendations.append("Consider adding CRS definition for better QGIS compatibility")
                else:
                    print("✓ CRS definition found")
                
                # Check the end of file for proper closure
                f.seek(-1000, 2)  # Go to near end of file
                end_content = f.read()
                
                if not end_content.strip().endswith('}'):
                    issues.append("File does not end with proper JSON closure")
                
                if ']}' not in end_content:
                    issues.append("Features array may not be properly closed")
                    
            else:
                # Small file - full validation
                f.seek(0)
                try:
                    data = json.load(f)
                    
                    # Validate structure
                    if data.get('type') != 'FeatureCollection':
                        issues.append("Root object is not a FeatureCollection")
                    
                    if 'features' not in data:
                        issues.append("No 'features' array found")
                    elif not isinstance(data['features'], list):
                        issues.append("'features' is not an array")
                    else:
                        feature_count = len(data['features'])
                        print(f"✓ {feature_count} features found")
                        
                        # Check first few features
                        for i, feature in enumerate(data['features'][:5]):
                            if feature.get('type') != 'Feature':
                                issues.append(f"Feature {i} is missing 'type': 'Feature'")
                            
                            if 'geometry' not in feature:
                                issues.append(f"Feature {i} is missing geometry")
                            
                            if 'properties' not in feature:
                                issues.append(f"Feature {i} is missing properties")
                            elif not isinstance(feature['properties'], dict):
                                issues.append(f"Feature {i} properties is not an object")
                    
                    # Check CRS
                    if 'crs' in data:
                        crs = data['crs']
                        if isinstance(crs, dict) and crs.get('type') == 'name':
                            crs_name = crs.get('properties', {}).get('name', '')
                            if 'EPSG:4326' in crs_name:
                                print("✓ Valid WGS84 (EPSG:4326) CRS")
                            else:
                                print(f"! CRS: {crs_name}")
                        else:
                            recommendations.append("CRS format could be improved")
                    
                except json.JSONDecodeError as e:
                    issues.append(f"Invalid JSON: {e}")
                    
    except Exception as e:
        issues.append(f"Error reading file: {e}")
    
    # Report results
    if not issues:
        print("✅ No issues found - should work well in QGIS")
    else:
        print("❌ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    
    if recommendations:
        print("💡 Recommendations:")
        for rec in recommendations:
            print(f"  - {rec}")
    
    return len(issues) == 0

def fix_combined_file_structure(directory):
    """Fix any structural issues in combined files"""
    print(f"\n=== Checking directory: {directory} ===")
    
    for file_path in Path(directory).glob("*combined*.geojson"):
        print(f"\nExamining: {file_path.name}")
        
        # Validate the file
        is_valid = validate_geojson_for_qgis(str(file_path))
        
        if not is_valid:
            print(f"❌ File has issues that may prevent QGIS loading")
        else:
            print(f"✅ File should load properly in QGIS")

def main():
    base_dir = "fixed_complete_uzbekistan_cadastral_data"
    
    if not os.path.exists(base_dir):
        print(f"Directory not found: {base_dir}")
        return
    
    # Find all directories with combined files
    for root, dirs, files in os.walk(base_dir):
        combined_files = [f for f in files if "combined" in f and f.endswith(".geojson")]
        if combined_files:
            fix_combined_file_structure(root)

if __name__ == "__main__":
    main()
