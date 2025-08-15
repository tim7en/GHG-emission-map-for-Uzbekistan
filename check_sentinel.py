#!/usr/bin/env python3
"""
Check Sentinel-5P Atmospheric Data for Emissions Proxy

This script checks Sentinel-5P atmospheric data that can serve as emissions proxies.
"""

import ee

def check_sentinel5p_data():
    """Check Sentinel-5P atmospheric data availability"""
    
    print("🛰️  Checking Sentinel-5P Atmospheric Data")
    print("=" * 50)
    
    try:
        ee.Initialize(project='ee-sabitovty')
        print("SUCCESS: Connected to GEE project: ee-sabitovty")
        
        # Test Sentinel-5P datasets (these are more commonly accessible)
        sentinel_datasets = [
            'COPERNICUS/S5P/NRTI/L3_CO',
            'COPERNICUS/S5P/NRTI/L3_NO2', 
            'COPERNICUS/S5P/NRTI/L3_CH4',
            'COPERNICUS/S5P/NRTI/L3_SO2',
            'COPERNICUS/S5P/OFFL/L3_CO',
            'COPERNICUS/S5P/OFFL/L3_NO2',
            'COPERNICUS/S5P/OFFL/L3_CH4'
        ]
        
        print("\nEARTH: Testing Sentinel-5P Atmospheric Data:")
        uzbekistan = ee.Geometry.Rectangle([55.9, 37.2, 73.2, 45.6])
        
        for dataset in sentinel_datasets:
            try:
                collection = ee.ImageCollection(dataset) \
                    .filterDate('2023-01-01', '2023-12-31') \
                    .filterBounds(uzbekistan)
                
                size = collection.size().getInfo()
                if size > 0:
                    first_image = collection.first()
                    bands = first_image.bandNames().getInfo()
                    print(f"SUCCESS: {dataset}")
                    print(f"   Images in 2023: {size}")
                    print(f"   Bands: {bands}")
                else:
                    print(f"WARNING:  {dataset} - No data for Uzbekistan in 2023")
            except Exception as e:
                print(f"ERROR: {dataset} - Error: {str(e)[:80]}...")
        
        # Test other atmospheric datasets
        print("\n🌬️  Testing Other Atmospheric Datasets:")
        other_datasets = [
            'ECMWF/ERA5_LAND/HOURLY',
            'NASA/GLDAS/V021/NOAH/G025/T3H',
            'MODIS/061/MOD09A1'  # Surface reflectance
        ]
        
        for dataset in other_datasets:
            try:
                collection = ee.ImageCollection(dataset) \
                    .filterDate('2023-01-01', '2023-01-31') \
                    .filterBounds(uzbekistan)
                
                size = collection.size().getInfo()
                if size > 0:
                    print(f"SUCCESS: {dataset} - {size} images in Jan 2023")
                else:
                    print(f"WARNING:  {dataset} - No data")
            except Exception as e:
                print(f"ERROR: {dataset} - Error: {str(e)[:80]}...")
                
    except Exception as e:
        print(f"ERROR: Dataset check failed: {e}")

if __name__ == "__main__":
    check_sentinel5p_data()
