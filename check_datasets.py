#!/usr/bin/env python3
"""
Check Available GEE Emissions Datasets

This script checks what emissions datasets are available in Google Earth Engine
for your project.
"""

import ee

def check_available_datasets():
    """Check available emissions datasets"""
    
    print("🔍 Checking Available Emissions Datasets")
    print("=" * 50)
    
    try:
        ee.Initialize(project='ee-sabitovty')
        print("SUCCESS: Connected to GEE project: ee-sabitovty")
        
        # Test different ODIAC versions
        odiac_versions = [
            'ODIAC/FOSSILFUEL_CO2',
            'ODIAC/ODIAC_CO2_v2016',
            'ODIAC/ODIAC_CO2_v2020A',
            'ODIAC/ODIAC_CO2_v2022A'
        ]
        
        print("\n🏭 Testing ODIAC CO2 Datasets:")
        for version in odiac_versions:
            try:
                collection = ee.ImageCollection(version)
                size = collection.limit(1).size().getInfo()
                if size > 0:
                    # Get date range
                    first_image = collection.first()
                    image_id = first_image.get('system:id').getInfo()
                    print(f"SUCCESS: {version} - Available! Sample ID: {image_id}")
                else:
                    print(f"WARNING:  {version} - Empty collection")
            except Exception as e:
                print(f"ERROR: {version} - Not accessible: {str(e)[:100]}...")
        
        # Test other emissions datasets
        other_datasets = [
            'CEDS/GBD-MAPS/emissions_CO2_residential_solid_fuels',
            'CAMS/CUT07',
            'COPERNICUS/Sentinel-5P/NRTI/L3_CO',
            'COPERNICUS/Sentinel-5P/NRTI/L3_NO2',
            'COPERNICUS/Sentinel-5P/NRTI/L3_CH4'
        ]
        
        print("\nEARTH: Testing Other Emissions Datasets:")
        for dataset in other_datasets:
            try:
                collection = ee.ImageCollection(dataset)
                size = collection.limit(1).size().getInfo()
                if size > 0:
                    first_image = collection.first()
                    image_id = first_image.get('system:id').getInfo()
                    print(f"SUCCESS: {dataset} - Available!")
                else:
                    print(f"WARNING:  {dataset} - Empty collection")
            except Exception as e:
                print(f"ERROR: {dataset} - Not accessible: {str(e)[:80]}...")
        
        # Test land cover and auxiliary datasets
        print("\n🗺️  Testing Auxiliary Datasets:")
        aux_datasets = [
            'MODIS/061/MCD12Q1',  # Land cover
            'USGS/SRTMGL1_003',   # Elevation
            'MODIS/061/MOD11A1',  # Land surface temperature
            'MODIS/061/MOD13A1',  # Vegetation indices
            'JRC/GSW1_4/GlobalSurfaceWater'  # Surface water
        ]
        
        for dataset in aux_datasets:
            try:
                if 'ImageCollection' in str(type(ee.ImageCollection(dataset))):
                    collection = ee.ImageCollection(dataset)
                    size = collection.limit(1).size().getInfo()
                    if size > 0:
                        print(f"SUCCESS: {dataset} - Available!")
                    else:
                        print(f"WARNING:  {dataset} - Empty collection")
                else:
                    # Single image dataset
                    image = ee.Image(dataset)
                    bands = image.bandNames().getInfo()
                    print(f"SUCCESS: {dataset} - Available! Bands: {len(bands)}")
            except Exception as e:
                print(f"ERROR: {dataset} - Not accessible: {str(e)[:80]}...")
        
    except Exception as e:
        print(f"ERROR: Dataset check failed: {e}")

if __name__ == "__main__":
    check_available_datasets()
