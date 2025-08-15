#!/usr/bin/env python3
"""
Test Server-Side Atmospheric Analysis for Uzbekistan

Simplified version for testing with reduced computation.

Author: AlphaEarth Analysis Team
Date: August 15, 2025
"""

import ee
import pandas as pd
import json
from pathlib import Path
import time
from datetime import datetime

def test_server_side_analysis():
    """Lightweight test of server-side atmospheric analysis"""
    
    print("🧪 TEST SERVER-SIDE ATMOSPHERIC ANALYSIS")
    print("=" * 50)
    print("MICROSCOPE: Reduced scope for testing:")
    print("   * 3 cities only")
    print("   * 2 gases only") 
    print("   * 30-day period only")
    print("   * Lower resolution")
    print("=" * 50)
    
    try:
        # Initialize GEE
        ee.Initialize(project='ee-sabitovty')
        print("SUCCESS: Google Earth Engine initialized")
        
        # Define test area (smaller bounding box)
        test_bounds = ee.Geometry.Rectangle([64.0, 39.0, 72.0, 42.0])  # Central Uzbekistan only
        
        # Test with only 3 major cities
        test_cities = {
            'Tashkent': [69.2401, 41.2995],
            'Samarkand': [66.9597, 39.6270],
            'Bukhara': [64.4207, 39.7747]
        }
        
        print(f"\n📍 Testing with {len(test_cities)} cities")
        
        # Create city points
        city_features = []
        for city_name, coords in test_cities.items():
            feature = ee.Feature(
                ee.Geometry.Point(coords),
                {'city': city_name, 'lon': coords[0], 'lat': coords[1]}
            )
            city_features.append(feature)
        
        city_collection = ee.FeatureCollection(city_features)
        
        # Test with only 2 gases for speed
        test_datasets = {
            'NO2': {
                'collection': 'COPERNICUS/S5P/OFFL/L3_NO2',
                'band': 'tropospheric_NO2_column_number_density'
            },
            'CO': {
                'collection': 'COPERNICUS/S5P/OFFL/L3_CO',
                'band': 'CO_column_number_density'
            }
        }
        
        # Use shorter time period for faster processing
        start_date = '2024-07-01'
        end_date = '2024-07-31'  # Just July 2024
        
        print(f"\n📅 Analysis period: {start_date} to {end_date}")
        
        results = {}
        
        for gas, config in test_datasets.items():
            print(f"\n📡 Processing {gas}...")
            
            try:
                # Load collection with limited timeframe
                collection = ee.ImageCollection(config['collection']) \
                    .filterDate(start_date, end_date) \
                    .filterBounds(test_bounds) \
                    .select(config['band']) \
                    .limit(5)  # Limit to 5 images max for speed
                
                # Check data availability
                size = collection.size().getInfo()
                print(f"   CHART: Found {size} images")
                
                if size > 0:
                    # Compute mean on server
                    print("   🔄 Computing mean on server...")
                    mean_image = collection.mean()
                    
                    # Sample at city points (server-side)
                    print("   📍 Sampling at city locations...")
                    sampled = mean_image.sampleRegions(
                        collection=city_collection,
                        scale=10000,  # 10km resolution for speed
                        projection='EPSG:4326'
                    )
                    
                    # Get results from server
                    features = sampled.getInfo()['features']
                    
                    city_data = {}
                    for feature in features:
                        props = feature['properties']
                        city = props['city']
                        concentration = props.get(config['band'])
                        
                        if concentration is not None:
                            city_data[city] = {
                                'concentration': concentration,
                                'longitude': props['lon'],
                                'latitude': props['lat']
                            }
                    
                    results[gas] = city_data
                    print(f"   SUCCESS: Extracted data for {len(city_data)} cities")
                    
                    # Quick server-side statistics
                    print("   TRENDING: Computing regional stats on server...")
                    stats = mean_image.reduceRegion(
                        reducer=ee.Reducer.mean().combine(
                            reducer2=ee.Reducer.minMax(),
                            sharedInputs=True
                        ),
                        geometry=test_bounds,
                        scale=10000,
                        maxPixels=1e6  # Reduced pixel limit
                    )
                    
                    region_stats = stats.getInfo()
                    print(f"   CHART: Regional statistics computed")
                    
                else:
                    print(f"   WARNING:  No {gas} data available")
                    
            except Exception as e:
                print(f"   ERROR: Error processing {gas}: {str(e)[:80]}...")
        
        # Display results
        if results:
            print(f"\nCHART: TEST RESULTS:")
            print("=" * 30)
            
            for city in test_cities.keys():
                print(f"\n🏙️  {city}:")
                for gas, gas_data in results.items():
                    if city in gas_data:
                        conc = gas_data[city]['concentration']
                        if gas == 'NO2':
                            print(f"   {gas}: {conc:.2e} mol/m^2")
                        elif gas == 'CO':
                            print(f"   {gas}: {conc:.2e} mol/m^2")
                    else:
                        print(f"   {gas}: No data")
            
            # Save test results
            output_dir = Path('outputs')
            output_dir.mkdir(exist_ok=True)
            
            # Create simple CSV
            test_rows = []
            for city in test_cities.keys():
                row = {'city': city}
                for gas in results.keys():
                    if city in results[gas]:
                        row[f'{gas}_concentration'] = results[gas][city]['concentration']
                        row['longitude'] = results[gas][city]['longitude']
                        row['latitude'] = results[gas][city]['latitude']
                    else:
                        row[f'{gas}_concentration'] = None
                test_rows.append(row)
            
            test_df = pd.DataFrame(test_rows)
            test_file = output_dir / 'test_atmospheric_data.csv'
            test_df.to_csv(test_file, index=False)
            
            # Save test metadata
            test_metadata = {
                'test_date': datetime.now().isoformat(),
                'cities_tested': len(test_cities),
                'gases_tested': list(results.keys()),
                'time_period': f"{start_date} to {end_date}",
                'processing_mode': 'server_side_test',
                'spatial_resolution': '10km',
                'success': True
            }
            
            metadata_file = output_dir / 'test_metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(test_metadata, f, indent=2)
            
            print(f"\nSTORAGE: Test results saved:")
            print(f"   Data: {test_file}")
            print(f"   Metadata: {metadata_file}")
            
            print(f"\n🎉 TEST SUCCESSFUL!")
            print(f"SUCCESS: Server-side processing confirmed working")
            print(f"CHART: {len(test_cities)} cities analyzed")
            print(f"EMISSION: {len(results)} gases detected")
            
            return True
            
        else:
            print("\nERROR: No data extracted in test")
            return False
            
    except Exception as e:
        print(f"\nERROR: Test failed: {e}")
        return False

if __name__ == "__main__":
    print("STARTING: Starting lightweight test...")
    start_time = time.time()
    
    success = test_server_side_analysis()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nSTOPWATCH:️  Test completed in {duration:.1f} seconds")
    
    if success:
        print("SUCCESS: Ready for full-scale analysis!")
        print("\n💡 If test worked well, we can:")
        print("   * Increase number of cities")
        print("   * Add more gases")
        print("   * Extend time period")
        print("   * Increase spatial resolution")
    else:
        print("ERROR: Test failed - need to debug first")
