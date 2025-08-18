#!/usr/bin/env python3
"""
Create a properly formatted combined GeoJSON file for QGIS compatibility - Fixed version.
"""

import json
import os
from pathlib import Path

def create_proper_combined_geojson(input_dir, output_file):
    """Create a properly formatted combined GeoJSON from individual files"""
    print(f"\n=== Creating combined file: {output_file} ===")
    
    # Initialize the FeatureCollection structure
    combined_data = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {
                "name": "EPSG:4326"
            }
        },
        "features": []
    }
    
    # Process all individual feature files
    individual_files = list(Path(input_dir).glob("feature_*.geojson"))
    print(f"Found {len(individual_files)} individual files")
    
    total_features = 0
    
    for file_path in sorted(individual_files):
        print(f"Processing: {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Extract features from this file
                if 'features' in data and isinstance(data['features'], list):
                    features = data['features']
                    print(f"  Added {len(features)} features")
                    
                    # Add all features to combined collection
                    combined_data['features'].extend(features)
                    total_features += len(features)
                else:
                    print(f"  Warning: No features found in {file_path.name}")
                    
        except Exception as e:
            print(f"  Error processing {file_path.name}: {e}")
    
    print(f"\nTotal features combined: {total_features}")
    
    # Write the combined file with proper formatting
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write with indentation for readability and QGIS compatibility
            json.dump(combined_data, f, ensure_ascii=False, indent=2)
        
        file_size = os.path.getsize(output_file)
        print(f"✅ Combined file created: {file_size / (1024*1024):.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating combined file: {e}")
        return False

def test_individual_file_structure(input_dir):
    """Test the structure of individual files to understand the data"""
    print(f"\n=== Testing individual file structure ===")
    
    individual_files = list(Path(input_dir).glob("feature_*.geojson"))
    
    if not individual_files:
        print("No individual files found")
        return
    
    # Test the first file
    test_file = individual_files[0]
    print(f"Testing: {test_file.name}")
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"File structure:")
        print(f"  Type: {data.get('type', 'MISSING')}")
        print(f"  CRS: {data.get('crs', 'MISSING')}")
        print(f"  Features count: {len(data.get('features', []))}")
        
        if 'features' in data and data['features']:
            feature = data['features'][0]
            print(f"  First feature type: {feature.get('type', 'MISSING')}")
            print(f"  First feature properties keys: {list(feature.get('properties', {}).keys())}")
            print(f"  First feature geometry type: {feature.get('geometry', {}).get('type', 'MISSING')}")
            
    except Exception as e:
        print(f"Error reading test file: {e}")

def validate_qgis_file(file_path):
    """Quick validation for QGIS compatibility"""
    print(f"\n=== Validating: {os.path.basename(file_path)} ===")
    
    try:
        # Read first 2000 characters to check structure
        with open(file_path, 'r', encoding='utf-8') as f:
            start = f.read(2000)
            
        print(f"File start (first 500 chars):")
        print(start[:500])
        print("...")
        
        # Check structure
        checks = [
            (start.strip().startswith('{'), "Starts with JSON object"),
            ('"type": "FeatureCollection"' in start, "Has FeatureCollection type"),
            ('"features": [' in start, "Has features array"),
            ('"crs":' in start, "Has CRS definition"),
            ('"EPSG:4326"' in start, "Uses WGS84 coordinate system")
        ]
        
        all_good = True
        for check, description in checks:
            if check:
                print(f"✓ {description}")
            else:
                print(f"❌ Missing: {description}")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error validating file: {e}")
        return False

def main():
    base_dir = "fixed_complete_uzbekistan_cadastral_data"
    
    if not os.path.exists(base_dir):
        print(f"Directory not found: {base_dir}")
        return
    
    # Process each layer directory
    for layer_dir in Path(base_dir).iterdir():
        if layer_dir.is_dir():
            print(f"\n{'='*60}")
            print(f"Processing layer: {layer_dir.name}")
            print(f"{'='*60}")
            
            # First, test individual file structure
            test_individual_file_structure(str(layer_dir))
            
            # Create new combined file
            new_combined_file = layer_dir / f"{layer_dir.name}_qgis_fixed.geojson"
            
            success = create_proper_combined_geojson(str(layer_dir), str(new_combined_file))
            
            if success:
                # Validate the new file
                validate_qgis_file(str(new_combined_file))

if __name__ == "__main__":
    main()
