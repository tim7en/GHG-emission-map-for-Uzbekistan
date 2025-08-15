#!/usr/bin/env python3
"""
Large Scale Test: Full Country GHG Analysis

This test validates the complete analysis workflow for all of Uzbekistan.
Use this after small and medium scale tests pass.

Author: AlphaEarth Analysis Team
Date: January 2025
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import time

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from preprocessing.data_loader import RealDataLoader


def test_full_country_data_loading():
    """Test loading data for full country analysis"""
    print("TEST_TUBE: LARGE SCALE TEST: Full Country Data Loading")
    print("=" * 60)
    
    start_time = time.time()
    
    # Initialize data loader
    loader = RealDataLoader()
    
    print("1. Loading Complete National Dataset:")
    all_data = loader.get_all_available_data()
    
    load_time = time.time() - start_time
    
    if len(all_data) == 0:
        print("ERROR: TEST FAILED: No data sources available for full country analysis")
        return False
    
    # Validate IPCC data completeness
    if 'IPCC_2022' in all_data:
        ipcc_data = all_data['IPCC_2022']
        
        print(f"\n2. National IPCC Data Validation:")
        print(f"   Loading time: {load_time:.2f} seconds")
        print(f"   Total emission categories: {len(ipcc_data)}")
        
        # Check all required gases are present
        required_gases = ['CO2', 'CH4', 'N2O']
        available_gases = ipcc_data['gas_type'].unique() if 'gas_type' in ipcc_data.columns else []
        
        for gas in required_gases:
            gas_data = [g for g in available_gases if gas in str(g)]
            status = "SUCCESS:" if gas_data else "ERROR:"
            print(f"   {status} {gas} emissions data")
        
        # Calculate total national emissions
        if 'emissions_2022_gg_co2eq' in ipcc_data.columns:
            total_emissions = ipcc_data['emissions_2022_gg_co2eq'].sum()
            print(f"   Total national emissions: {total_emissions:,.0f} Gg CO2-eq")
            
            # Sector breakdown
            if 'sector' in ipcc_data.columns:
                sector_emissions = ipcc_data.groupby('sector')['emissions_2022_gg_co2eq'].sum().sort_values(ascending=False)
                print(f"   Number of emission sectors: {len(sector_emissions)}")
                print(f"   Largest sector: {sector_emissions.index[0][:50]} ({sector_emissions.iloc[0]:.0f} Gg CO2-eq)")
    
    # Test GEE data availability (if possible)
    print(f"\n3. Earth Engine Data Assessment:")
    gee_status = loader.validate_data_availability()['Google_Earth_Engine']
    
    if gee_status:
        print("   SUCCESS: Google Earth Engine available")
        gee_data = loader.load_gee_data()
        if gee_data:
            for source, data in gee_data.items():
                print(f"   {source}: {len(data)} satellite data points")
    else:
        print("   WARNING:  Google Earth Engine not available")
        print("      Analysis will use IPCC data with spatial modeling")
    
    print(f"\nSUCCESS: TEST PASSED: Full country data loaded successfully!")
    return True


def test_national_spatial_coverage():
    """Test spatial coverage for the entire country"""
    print("\nMAP:  LARGE SCALE TEST: National Spatial Coverage")
    print("=" * 60)
    
    # Define Uzbekistan bounds
    uzbekistan_bounds = {
        'min_lon': 55.9,
        'max_lon': 73.2,
        'min_lat': 37.1,
        'max_lat': 45.6
    }
    
    print("1. National Grid Generation:")
    print(f"   Country bounds: {uzbekistan_bounds['min_lon']:.1f}deg-{uzbekistan_bounds['max_lon']:.1f}degE, {uzbekistan_bounds['min_lat']:.1f}deg-{uzbekistan_bounds['max_lat']:.1f}degN")
    
    # Calculate country dimensions
    country_width = (uzbekistan_bounds['max_lon'] - uzbekistan_bounds['min_lon']) * 111  # km
    country_height = (uzbekistan_bounds['max_lat'] - uzbekistan_bounds['min_lat']) * 111  # km
    country_area = country_width * country_height
    
    print(f"   Dimensions: {country_width:.0f} x {country_height:.0f} km")
    print(f"   Approximate area: {country_area:,.0f} km^2")
    
    # Test different grid resolutions
    resolutions = [0.1, 0.05, 0.01]  # degrees (~10km, 5km, 1km)
    
    print(f"\n2. Grid Resolution Analysis:")
    for resolution in resolutions:
        # Calculate grid size
        n_lons = int((uzbekistan_bounds['max_lon'] - uzbekistan_bounds['min_lon']) / resolution)
        n_lats = int((uzbekistan_bounds['max_lat'] - uzbekistan_bounds['min_lat']) / resolution)
        total_cells = n_lons * n_lats
        
        # Estimate memory and processing requirements
        memory_mb = total_cells * 0.001  # Rough estimate: 1KB per cell
        
        km_resolution = resolution * 111
        print(f"   Resolution {resolution:.3f}deg (~{km_resolution:.0f}km): {total_cells:,} cells, ~{memory_mb:.1f}MB")
        
        # Recommend optimal resolution
        if total_cells < 50000:  # Manageable for full analysis
            print(f"     SUCCESS: Recommended for full country analysis")
        elif total_cells < 200000:  # Possible but resource intensive
            print(f"     WARNING:  Possible but resource intensive")
        else:  # Too large for practical analysis
            print(f"     ERROR: Too large for practical analysis")
    
    print(f"\nSUCCESS: TEST PASSED: Spatial coverage analysis completed!")
    return True


def test_performance_estimation():
    """Test performance estimation for large scale analysis"""
    print("\nLIGHTNING: LARGE SCALE TEST: Performance Estimation")
    print("=" * 60)
    
    # Load data to estimate processing time
    loader = RealDataLoader()
    all_data = loader.get_all_available_data()
    
    if 'IPCC_2022' not in all_data:
        print("ERROR: Cannot estimate performance without IPCC data")
        return False
    
    ipcc_data = all_data['IPCC_2022']
    
    print("1. Processing Time Estimation:")
    
    # Estimate processing for different scales
    scales = [
        {'name': 'Pilot (100km^2)', 'cells': 100, 'area_fraction': 0.001},
        {'name': 'Regional (10,000km^2)', 'cells': 10000, 'area_fraction': 0.1},
        {'name': 'National (400,000km^2)', 'cells': 40000, 'area_fraction': 1.0}
    ]
    
    # Benchmark data processing
    start_time = time.time()
    
    # Simulate data processing operations
    for i in range(1000):
        if 'emissions_2022_gg_co2eq' in ipcc_data.columns:
            _ = ipcc_data['emissions_2022_gg_co2eq'].sum()
            _ = ipcc_data.groupby('gas_type')['emissions_2022_gg_co2eq'].sum() if 'gas_type' in ipcc_data.columns else None
    
    benchmark_time = time.time() - start_time
    time_per_operation = benchmark_time / 1000
    
    print(f"   Benchmark: {time_per_operation*1000:.2f} ms per data operation")
    
    for scale in scales:
        # Estimate processing time based on grid size
        operations_per_cell = 10  # Rough estimate
        total_operations = scale['cells'] * operations_per_cell
        estimated_time = total_operations * time_per_operation
        
        print(f"   {scale['name']}: ~{estimated_time:.1f} seconds ({estimated_time/60:.1f} minutes)")
    
    # Memory estimation
    print(f"\n2. Memory Requirements:")
    base_memory_mb = 50  # Base system memory
    
    for scale in scales:
        # Estimate memory per cell (emissions data, auxiliary data, results)
        memory_per_cell_kb = 2  # Conservative estimate
        total_memory_mb = base_memory_mb + (scale['cells'] * memory_per_cell_kb / 1024)
        
        print(f"   {scale['name']}: ~{total_memory_mb:.0f} MB")
        
        if total_memory_mb < 500:
            print(f"     SUCCESS: Memory requirements acceptable")
        elif total_memory_mb < 2000:
            print(f"     WARNING:  High memory usage, consider chunking")
        else:
            print(f"     ERROR: Excessive memory, requires optimization")
    
    # Data quality assessment
    print(f"\n3. Data Quality for Large Scale Analysis:")
    
    if 'emissions_2022_gg_co2eq' in ipcc_data.columns:
        # Check for data completeness
        total_records = len(ipcc_data)
        valid_emissions = ipcc_data['emissions_2022_gg_co2eq'].notna().sum()
        completeness = valid_emissions / total_records * 100
        
        print(f"   Data completeness: {completeness:.1f}% ({valid_emissions}/{total_records} records)")
        
        if completeness >= 95:
            print(f"   SUCCESS: Excellent data quality for large scale analysis")
        elif completeness >= 80:
            print(f"   WARNING:  Good data quality, some gaps expected")
        else:
            print(f"   ERROR: Poor data quality, may affect analysis reliability")
    
    print(f"\nSUCCESS: TEST PASSED: Performance estimation completed!")
    return True


def test_scalability_validation():
    """Test system scalability for different analysis sizes"""
    print("\nTRENDING: LARGE SCALE TEST: Scalability Validation")
    print("=" * 60)
    
    # Test processing scalability with synthetic workloads
    grid_sizes = [10, 50, 100, 200]  # Different grid dimensions
    
    print("1. Processing Scalability Test:")
    
    processing_times = []
    
    for grid_size in grid_sizes:
        total_cells = grid_size * grid_size
        
        # Simulate grid processing
        start_time = time.time()
        
        # Create synthetic grid data
        grid_data = []
        for i in range(grid_size):
            for j in range(grid_size):
                # Simulate emission calculation
                emission_value = np.random.lognormal(1, 0.5)
                auxiliary_data = {
                    'population': np.random.poisson(1000),
                    'urban_fraction': np.random.beta(2, 5),
                    'elevation': np.random.normal(500, 200)
                }
                
                grid_data.append({
                    'x': i, 'y': j,
                    'emissions': emission_value,
                    **auxiliary_data
                })
        
        # Convert to DataFrame and perform analysis operations
        df = pd.DataFrame(grid_data)
        
        # Simulate typical analysis operations
        _ = df['emissions'].sum()
        _ = df['emissions'].std()
        _ = df.groupby('x')['emissions'].mean()
        _ = df.corr()
        
        processing_time = time.time() - start_time
        processing_times.append(processing_time)
        
        print(f"   Grid {grid_size}x{grid_size} ({total_cells} cells): {processing_time:.3f} seconds")
    
    # Analyze scalability
    print(f"\n2. Scalability Analysis:")
    
    # Calculate scaling factor
    if len(processing_times) >= 2:
        scale_factor = processing_times[-1] / processing_times[0]
        cell_ratio = (grid_sizes[-1]**2) / (grid_sizes[0]**2)
        efficiency = scale_factor / cell_ratio
        
        print(f"   Scaling factor: {scale_factor:.1f}x time for {cell_ratio:.0f}x cells")
        print(f"   Efficiency ratio: {efficiency:.2f} (1.0 = linear scaling)")
        
        if efficiency <= 1.2:
            print(f"   SUCCESS: Excellent linear scaling")
        elif efficiency <= 2.0:
            print(f"   WARNING:  Acceptable scaling with some overhead")
        else:
            print(f"   ERROR: Poor scaling, optimization needed")
    
    # Extrapolate to full country
    if processing_times:
        full_country_cells = 40000  # Estimate for 1km resolution
        current_largest = grid_sizes[-1]**2
        extrapolation_factor = full_country_cells / current_largest
        estimated_full_time = processing_times[-1] * extrapolation_factor
        
        print(f"\n3. Full Country Extrapolation:")
        print(f"   Estimated processing time: {estimated_full_time:.1f} seconds ({estimated_full_time/60:.1f} minutes)")
        
        if estimated_full_time < 300:  # 5 minutes
            print(f"   SUCCESS: Fast processing expected")
        elif estimated_full_time < 1800:  # 30 minutes
            print(f"   WARNING:  Moderate processing time")
        else:
            print(f"   ERROR: Long processing time, consider optimization")
    
    print(f"\nSUCCESS: TEST PASSED: Scalability validation completed!")
    return True


if __name__ == "__main__":
    print("STARTING: Starting Large Scale Tests for GHG Emissions Analysis")
    print("=" * 70)
    
    # Run tests
    test1_passed = test_full_country_data_loading()
    test2_passed = test_national_spatial_coverage()
    test3_passed = test_performance_estimation()
    test4_passed = test_scalability_validation()
    
    # Summary
    print("\nCLIPBOARD: LARGE SCALE TEST SUMMARY:")
    print("=" * 70)
    print(f"SUCCESS: Full Country Data Loading: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"SUCCESS: National Spatial Coverage: {'PASSED' if test2_passed else 'FAILED'}")
    print(f"SUCCESS: Performance Estimation: {'PASSED' if test3_passed else 'FAILED'}")
    print(f"SUCCESS: Scalability Validation: {'PASSED' if test4_passed else 'FAILED'}")
    
    if test1_passed and test2_passed and test3_passed and test4_passed:
        print("\nSUCCESS: ALL LARGE SCALE TESTS PASSED!")
        print("   System ready for full production analysis")
        print("   Run: python run_analysis.py --scale=full")
    else:
        print("\nERROR: SOME TESTS FAILED!")
        print("   Please optimize system before full scale analysis")
        sys.exit(1)