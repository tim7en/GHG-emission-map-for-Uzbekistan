#!/usr/bin/env python3
"""
Google Earth Engine Authentication Test Script
Tests authentication and basic functionality for ee-sabitovty project

Author: AlphaEarth Analysis Team
Date: August 15, 2025
"""

import ee
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

def test_gee_authentication():
    """Test Google Earth Engine authentication and functionality"""
    
    print("MICROSCOPE: GOOGLE EARTH ENGINE AUTHENTICATION TEST")
    print("=" * 50)
    print(f"🕐 Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python version: {sys.version.split()[0]}")
    print(f"EARTH: Target project: ee-sabitovty")
    print("=" * 50)
    
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'project_id': 'ee-sabitovty',
        'tests': {}
    }
    
    try:
        # Test 1: Authentication
        print("\n🔑 Test 1: Authentication")
        print("-" * 30)
        
        try:
            # Try different authentication methods
            auth_method = None
            
            # Method 1: Service account (for CI/CD)
            service_account_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            if service_account_path and os.path.exists(service_account_path):
                print(f"   🔐 Using service account: {service_account_path}")
                ee.Initialize(project='ee-sabitovty')
                auth_method = 'service_account'
                
            # Method 2: User authentication (local development)
            else:
                print("   🔐 Using default authentication")
                ee.Initialize(project='ee-sabitovty')
                auth_method = 'user_token'
            
            print(f"   SUCCESS: Authentication successful ({auth_method})")
            test_results['tests']['authentication'] = {
                'status': 'passed',
                'method': auth_method,
                'project': 'ee-sabitovty'
            }
            
        except Exception as e:
            print(f"   ERROR: Authentication failed: {e}")
            test_results['tests']['authentication'] = {
                'status': 'failed',
                'error': str(e)
            }
            return test_results
            
        # Test 2: Basic API functionality
        print("\n📡 Test 2: Basic API Functionality")
        print("-" * 30)
        
        try:
            # Test server communication
            test_string = ee.String('Hello from authentication test!')
            response = test_string.getInfo()
            print(f"   📤 Server communication: {response}")
            
            # Test geometry creation
            tashkent = ee.Geometry.Point([69.2401, 41.2995])
            coords = tashkent.getInfo()
            print(f"   📍 Geometry creation: {coords['type']} at {coords['coordinates']}")
            
            # Test date handling
            current_date = ee.Date(datetime.now())
            date_string = current_date.format('YYYY-MM-dd').getInfo()
            print(f"   📅 Date operations: {date_string}")
            
            test_results['tests']['basic_api'] = {
                'status': 'passed',
                'server_response': response,
                'geometry_test': 'passed',
                'date_test': date_string
            }
            print("   SUCCESS: Basic API functionality working")
            
        except Exception as e:
            print(f"   ERROR: Basic API test failed: {e}")
            test_results['tests']['basic_api'] = {
                'status': 'failed', 
                'error': str(e)
            }
            
        # Test 3: Satellite Data Access
        print("\n🛰️ Test 3: Satellite Data Access")
        print("-" * 30)
        
        data_access_results = {}
        
        # Test key atmospheric datasets
        datasets = {
            'NO2': 'COPERNICUS/S5P/OFFL/L3_NO2',
            'CO': 'COPERNICUS/S5P/OFFL/L3_CO',
            'CH4': 'COPERNICUS/S5P/OFFL/L3_CH4',
            'Landsat': 'LANDSAT/LC08/C02/T1_L2'
        }
        
        uzbekistan = ee.Geometry.Rectangle([55.9, 37.2, 73.2, 45.6])
        
        for dataset_name, collection_id in datasets.items():
            try:
                collection = ee.ImageCollection(collection_id) \
                    .filterDate('2024-06-01', '2024-07-01') \
                    .filterBounds(uzbekistan) \
                    .limit(10)
                
                size = collection.size().getInfo()
                print(f"   CHART: {dataset_name}: {size} images available")
                
                if size > 0:
                    first_image = collection.first()
                    bands = first_image.bandNames().getInfo()
                    print(f"      Available bands: {bands[:5]}...")
                    
                    data_access_results[dataset_name] = {
                        'status': 'available',
                        'image_count': size,
                        'bands': bands[:10]  # First 10 bands
                    }
                else:
                    data_access_results[dataset_name] = {
                        'status': 'no_data',
                        'image_count': 0
                    }
                    
            except Exception as e:
                print(f"   ERROR: {dataset_name} access failed: {e}")
                data_access_results[dataset_name] = {
                    'status': 'error',
                    'error': str(e)[:100]
                }
        
        test_results['tests']['data_access'] = data_access_results
        print("   SUCCESS: Satellite data access test completed")
        
        # Test 4: Computational Test
        print("\n⚡ Test 4: Computational Capabilities")
        print("-" * 30)
        
        try:
            start_time = time.time()
            
            # Simple computation test
            test_point = ee.Geometry.Point([69.2401, 41.2995]).buffer(5000)
            
            # Load and process NO2 data
            no2_collection = ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_NO2') \
                .filterDate('2024-06-01', '2024-06-30') \
                .filterBounds(test_point) \
                .select('tropospheric_NO2_column_number_density')
            
            collection_size = no2_collection.size().getInfo()
            
            if collection_size > 0:
                # Compute monthly mean
                monthly_mean = no2_collection.mean()
                
                # Sample at test point
                sample = monthly_mean.sampleRegions(
                    collection=ee.FeatureCollection([ee.Feature(test_point.centroid())]),
                    scale=5000
                ).getInfo()
                
                computation_time = time.time() - start_time
                
                print(f"   ⚡ Computation time: {computation_time:.2f} seconds")
                print(f"   CHART: Images processed: {collection_size}")
                print(f"   TARGET: Sample features: {len(sample['features'])}")
                
                test_results['tests']['computation'] = {
                    'status': 'passed',
                    'computation_time': computation_time,
                    'images_processed': collection_size,
                    'sample_features': len(sample['features'])
                }
                
                print("   SUCCESS: Computational test passed")
                
            else:
                print("   WARNING:  No data available for computation test")
                test_results['tests']['computation'] = {
                    'status': 'no_data',
                    'message': 'No images available for computation test'
                }
                
        except Exception as e:
            print(f"   ERROR: Computational test failed: {e}")
            test_results['tests']['computation'] = {
                'status': 'failed',
                'error': str(e)
            }
            
        # Test 5: Project-specific Resources
        print("\n📂 Test 5: Project Resources")
        print("-" * 30)
        
        try:
            # Test project quota and limits
            print("   💳 Checking project access...")
            
            # Try to access project-specific assets (may not exist)
            try:
                test_asset = ee.Image('users/sabitovty/test_image')
                asset_info = test_asset.getInfo()
                print("   📁 Custom assets: Accessible")
                asset_access = 'accessible'
            except:
                print("   📁 Custom assets: Not found (expected)")
                asset_access = 'none_found'
            
            # Check computational limits by timing a larger operation
            try:
                large_collection = ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_NO2') \
                    .filterDate('2024-01-01', '2024-01-31') \
                    .filterBounds(uzbekistan)
                
                large_size = large_collection.size().getInfo()
                print(f"   CHART: Large collection access: {large_size} images")
                
                test_results['tests']['project_resources'] = {
                    'status': 'passed',
                    'asset_access': asset_access,
                    'large_collection_size': large_size
                }
                
            except Exception as e:
                print(f"   WARNING:  Large collection test: {e}")
                test_results['tests']['project_resources'] = {
                    'status': 'limited',
                    'asset_access': asset_access,
                    'limitation': str(e)[:100]
                }
            
            print("   SUCCESS: Project resources test completed")
            
        except Exception as e:
            print(f"   ERROR: Project resources test failed: {e}")
            test_results['tests']['project_resources'] = {
                'status': 'failed',
                'error': str(e)
            }
            
        # Overall Assessment
        print("\nTARGET: Overall Assessment")
        print("-" * 30)
        
        passed_tests = sum(1 for test in test_results['tests'].values() 
                          if test.get('status') in ['passed', 'available', 'no_data'])
        total_tests = len(test_results['tests'])
        
        success_rate = passed_tests / total_tests * 100
        
        print(f"   CHART: Tests passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("   🎉 Authentication and functionality: EXCELLENT")
            overall_status = 'excellent'
        elif success_rate >= 60:
            print("   SUCCESS: Authentication and functionality: GOOD")
            overall_status = 'good'
        elif success_rate >= 40:
            print("   WARNING:  Authentication and functionality: LIMITED")
            overall_status = 'limited'
        else:
            print("   ERROR: Authentication and functionality: POOR")
            overall_status = 'poor'
            
        test_results['overall'] = {
            'status': overall_status,
            'success_rate': success_rate,
            'passed_tests': passed_tests,
            'total_tests': total_tests
        }
        
        # Save results
        output_dir = Path('outputs/gee_auth_tests')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = output_dir / f'auth_test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print(f"\nSTORAGE: Results saved to: {results_file}")
        
        return test_results
        
    except Exception as e:
        print(f"\nERROR: Critical error during testing: {e}")
        test_results['critical_error'] = str(e)
        return test_results

def main():
    """Main function to run authentication tests"""
    
    results = test_gee_authentication()
    
    # Exit with appropriate code
    if 'critical_error' in results:
        print("\nERROR: CRITICAL ERROR - Authentication completely failed")
        sys.exit(1)
    elif results.get('overall', {}).get('success_rate', 0) >= 60:
        print("\nSUCCESS: AUTHENTICATION TEST PASSED")
        print("STARTING: Google Earth Engine is ready for atmospheric analysis!")
        sys.exit(0)
    else:
        print("\nWARNING:  AUTHENTICATION TEST PARTIALLY FAILED")
        print("SETTINGS: Please check authentication setup and permissions")
        sys.exit(1)

if __name__ == "__main__":
    main()
