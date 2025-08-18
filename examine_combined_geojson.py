#!/usr/bin/env python3
"""
Examine the structure of combined GeoJSON files to debug QGIS compatibility issues.
"""

import json
import os

def examine_geojson_structure(file_path, max_chars=10000):
    """Examine the beginning of a GeoJSON file to understand its structure"""
    print(f"\n=== Examining: {file_path} ===")
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    file_size = os.path.getsize(file_path)
    print(f"File size: {file_size / (1024*1024):.2f} MB")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read first part of file
            content = f.read(max_chars)
            print(f"First {len(content)} characters:")
            print("-" * 50)
            print(content)
            print("-" * 50)
            
            # Try to parse as JSON to see structure
            f.seek(0)
            try:
                # Try to load just the first few lines to see structure
                first_line = f.readline().strip()
                print(f"\nFirst line: {first_line}")
                
                # Reset and try to parse structure
                f.seek(0)
                # Read in chunks to find the structure
                chunk = f.read(5000)
                
                # Check if it starts like a proper FeatureCollection
                if chunk.strip().startswith('{'):
                    print("\n✓ Starts with JSON object")
                    if '"type": "FeatureCollection"' in chunk:
                        print("✓ Contains FeatureCollection type")
                    if '"features": [' in chunk:
                        print("✓ Contains features array")
                    if '"crs":' in chunk:
                        print("✓ Contains CRS definition")
                else:
                    print("✗ Does not start with JSON object")
                    
            except Exception as e:
                print(f"Error parsing JSON structure: {e}")
                
    except Exception as e:
        print(f"Error reading file: {e}")

def main():
    base_dir = "fixed_complete_uzbekistan_cadastral_data"
    
    # Find all combined files
    combined_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if "combined" in file and file.endswith(".geojson"):
                combined_files.append(os.path.join(root, file))
    
    print(f"Found {len(combined_files)} combined GeoJSON files")
    
    # Examine each combined file
    for file_path in combined_files:
        examine_geojson_structure(file_path)
    
    # Also examine an individual file for comparison
    print("\n" + "="*60)
    print("COMPARISON: Individual file structure")
    print("="*60)
    
    # Find an individual file
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.startswith("feature_") and file.endswith(".geojson"):
                individual_file = os.path.join(root, file)
                examine_geojson_structure(individual_file, max_chars=2000)
                break
        break

if __name__ == "__main__":
    main()
