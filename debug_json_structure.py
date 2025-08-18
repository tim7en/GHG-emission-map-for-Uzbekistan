#!/usr/bin/env python3
"""
Debug and fix JSON structure issues in combined GeoJSON files.
"""

import json
import os
from pathlib import Path

def debug_json_structure(file_path, check_lines=20):
    """Debug JSON structure around the error point"""
    print(f"\n=== Debugging JSON structure: {os.path.basename(file_path)} ===")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = []
            for i, line in enumerate(f):
                lines.append(f"Line {i+1:3d}: {line.rstrip()}")
                if i >= check_lines - 1:
                    break
        
        print("First 20 lines:")
        for line in lines:
            print(line)
        
        # Try to parse incrementally to find the exact error
        print(f"\nTrying incremental JSON parsing...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try parsing chunks to find where it breaks
        for chunk_size in [1000, 2000, 3000, 4000, 5000, 6000]:
            try:
                chunk = content[:chunk_size]
                # Try to make it valid JSON by closing what's open
                if chunk.count('{') > chunk.count('}'):
                    # Add closing braces
                    chunk += '}' * (chunk.count('{') - chunk.count('}'))
                
                json.loads(chunk)
                print(f"✓ Valid JSON up to {chunk_size} characters")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON error at {chunk_size} chars: {e}")
                print(f"Error around: {content[max(0, e.pos-100):e.pos+100]}")
                break
        
    except Exception as e:
        print(f"Error debugging file: {e}")

def create_clean_combined_file(input_dir, output_file):
    """Create a clean combined file with careful JSON handling"""
    print(f"\n=== Creating clean combined file: {output_file} ===")
    
    individual_files = sorted(list(Path(input_dir).glob("feature_*.geojson")))
    
    if not individual_files:
        print("No individual files found")
        return False
    
    print(f"Found {len(individual_files)} individual files")
    
    # Start building the combined structure
    all_features = []
    
    for file_path in individual_files:
        print(f"Processing: {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'features' in data and isinstance(data['features'], list):
                all_features.extend(data['features'])
                print(f"  Added {len(data['features'])} features")
            else:
                print(f"  Warning: No features in {file_path.name}")
                
        except Exception as e:
            print(f"  Error processing {file_path.name}: {e}")
            continue
    
    # Create the final structure
    combined_data = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {
                "name": "EPSG:4326"
            }
        },
        "features": all_features
    }
    
    print(f"\nTotal features: {len(all_features)}")
    
    # Write the file carefully
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
        
        file_size = os.path.getsize(output_file)
        print(f"✅ Clean file created: {file_size / (1024*1024):.2f} MB")
        
        # Validate the created file
        with open(output_file, 'r', encoding='utf-8') as f:
            json.load(f)  # This will raise an exception if invalid
        
        print("✅ JSON validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error creating clean file: {e}")
        return False

def main():
    base_dir = "fixed_complete_uzbekistan_cadastral_data"
    
    # Find the problematic file
    problem_file = Path(base_dir) / "VILOYAT_BORDER_2023_zoom_1" / "VILOYAT_BORDER_2023_zoom_1_qgis_fixed.geojson"
    
    if problem_file.exists():
        # Debug the problematic file
        debug_json_structure(str(problem_file))
        
        # Create a clean version
        clean_file = problem_file.parent / f"{problem_file.stem}_clean.geojson"
        success = create_clean_combined_file(str(problem_file.parent), str(clean_file))
        
        if success:
            print(f"\n✅ Clean file created: {clean_file}")
            print(f"Original file: {problem_file.stat().st_size / (1024*1024):.2f} MB")
            print(f"Clean file: {clean_file.stat().st_size / (1024*1024):.2f} MB")
        
    else:
        print(f"Problem file not found: {problem_file}")

if __name__ == "__main__":
    main()
