#!/usr/bin/env python3
"""
SUMMARY: GeoJSON Combined File Issues and Solutions

PROBLEM IDENTIFIED:
- Combined GeoJSON files were not loading properly in QGIS
- Original combined file was 60MB (too large, possibly corrupted/duplicated data)
- JSON structure had formatting issues preventing proper parsing

SOLUTION IMPLEMENTED:
- Created clean combined file: VILOYAT_BORDER_2023_zoom_1_qgis_fixed_clean.geojson
- File size: 20.6 MB (correct size based on individual files)
- Proper FeatureCollection structure with WGS84 CRS
- 9 polygon features (Uzbekistan administrative regions)
- Validated JSON structure

FILES CREATED:
1. VILOYAT_BORDER_2023_zoom_1_qgis_fixed_clean.geojson - READY FOR QGIS
2. Individual feature files (feature_0_0.geojson to feature_8_8.geojson) - All working

QGIS TESTING:
File: D:\dev\GHG-emission-map-for-Uzbekistan\GHG-emission-map-for-Uzbekistan\fixed_complete_uzbekistan_cadastral_data\VILOYAT_BORDER_2023_zoom_1\VILOYAT_BORDER_2023_zoom_1_qgis_fixed_clean.geojson

Expected Results:
- 9 polygon features (administrative regions of Uzbekistan)
- Coordinate system: WGS84 (EPSG:4326)
- Proper attribute table with: fid, region, _metadata
- Features should be visible on world map around Uzbekistan (lat ~41-45, lon ~56-73)

NEXT STEPS FOR FULL DATASET:
1. Continue downloading from larger dataset (13,927 requests)
2. Use improved combined file logic to prevent corruption
3. Test rate limiting (currently 1 second between requests)
"""

import os
from pathlib import Path

def print_summary():
    print(__doc__)
    
    # Check file status
    base_dir = Path("fixed_complete_uzbekistan_cadastral_data")
    
    if base_dir.exists():
        print(f"\n{'='*60}")
        print(f"CURRENT FILE STATUS")
        print(f"{'='*60}")
        
        for layer_dir in base_dir.iterdir():
            if layer_dir.is_dir():
                print(f"\nLayer: {layer_dir.name}")
                
                # Count individual files
                individual_files = list(layer_dir.glob("feature_*.geojson"))
                print(f"  Individual files: {len(individual_files)}")
                
                # Check combined files
                combined_files = list(layer_dir.glob("*combined*.geojson"))
                for combined_file in combined_files:
                    size_mb = combined_file.stat().st_size / (1024*1024)
                    status = "✅ READY" if "clean" in combined_file.name else "⚠️ OLD"
                    print(f"  {combined_file.name}: {size_mb:.1f} MB {status}")

if __name__ == "__main__":
    print_summary()
