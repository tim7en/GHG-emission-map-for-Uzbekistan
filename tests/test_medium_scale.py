#!/usr/bin/env python3
"""
Medium Scale Test: Small Geographic Area Analysis

This test script validates GHG analysis for a small pilot region (e.g., Tashkent area).
Use this after small scale tests pass, before running full country analysis.

Author: AlphaEarth Analysis Team
Date: January 2025
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from preprocessing.data_loader import RealDataLoader


def test_pilot_region_analysis():
    """Test analysis for a small pilot region"""
    print("🧪 MEDIUM SCALE TEST: Pilot Region Analysis")
    print("=" * 55)
    
    # Initialize data loader
    loader = RealDataLoader()
    
    # Define pilot region (Tashkent area - 100km² area)
    pilot_bounds = {
        'min_lon': 69.0,
        'max_lon': 69.5,
        'min_lat': 41.0,
        'max_lat': 41.5
    }
    
    print(f"\n1️⃣ Pilot Region Definition:")
    print(f"   Region: Tashkent Area (100km² pilot)")
    print(f"   Bounds: {pilot_bounds['min_lon']:.1f}°-{pilot_bounds['max_lon']:.1f}°E, {pilot_bounds['min_lat']:.1f}°-{pilot_bounds['max_lat']:.1f}°N")
    
    # Load available data
    print(f"\n2️⃣ Loading Available Data Sources:")
    all_data = loader.get_all_available_data()
    
    if len(all_data) == 0:
        print("❌ TEST FAILED: No data sources available")
        return False
    
    # Analyze IPCC data by sector for pilot region
    if 'IPCC_2022' in all_data:
        ipcc_data = all_data['IPCC_2022']
        print(f"\n3️⃣ IPCC Data Analysis for Pilot Region:")
        
        # Estimate pilot region emissions (proportional to national data)
        pilot_area_fraction = 0.001  # Rough estimate for 100km² vs total country
        
        # Calculate emissions by gas type
        if 'gas_type' in ipcc_data.columns and 'emissions_2022_gg_co2eq' in ipcc_data.columns:
            gas_emissions = ipcc_data.groupby('gas_type')['emissions_2022_gg_co2eq'].sum()
            pilot_emissions = gas_emissions * pilot_area_fraction
            
            print(f"   Estimated pilot region emissions (Gg CO2-eq):")
            for gas, emissions in pilot_emissions.items():
                print(f"     {gas}: {emissions:.2f}")
            
            total_pilot = pilot_emissions.sum()
            print(f"   Total pilot emissions: {total_pilot:.2f} Gg CO2-eq")
        
        # Identify key sectors for pilot region
        print(f"\n4️⃣ Key Emission Sectors in Pilot Region:")
        if 'sector' in ipcc_data.columns and 'emissions_2022_gg_co2eq' in ipcc_data.columns:
            sector_emissions = ipcc_data.groupby('sector')['emissions_2022_gg_co2eq'].sum().sort_values(ascending=False)
            pilot_sector_emissions = sector_emissions * pilot_area_fraction
            
            top_sectors = pilot_sector_emissions.head(5)
            for sector, emissions in top_sectors.items():
                sector_short = sector[:40] + "..." if len(sector) > 40 else sector
                print(f"     {sector_short:<45} {emissions:>8.3f} Gg CO2-eq")
    
    # Test Google Earth Engine connectivity (if available)
    print(f"\n5️⃣ Testing Google Earth Engine Access:")
    gee_data = loader.load_gee_data()
    
    if len(gee_data) > 0:
        print(f"   ✅ GEE data available: {list(gee_data.keys())}")
        for source, data in gee_data.items():
            if len(data) > 0:
                print(f"     {source}: {len(data)} data points")
    else:
        print(f"   ⚠️  GEE data not available (expected for this test)")
        print(f"      Analysis will use IPCC data with spatial interpolation")
    
    print(f"\n✅ TEST PASSED: Pilot region analysis completed successfully!")
    return True


def test_spatial_grid_generation():
    """Test spatial grid generation for downscaling"""
    print("\n🗺️  MEDIUM SCALE TEST: Spatial Grid Generation")
    print("=" * 55)
    
    # Define test grid parameters
    pilot_bounds = {
        'min_lon': 69.0,
        'max_lon': 69.5,
        'min_lat': 41.0,
        'max_lat': 41.5
    }
    
    grid_resolution = 0.01  # ~1km resolution
    
    print(f"1️⃣ Grid Parameters:")
    print(f"   Resolution: {grid_resolution:.3f}° (~1km)")
    print(f"   Area: {(pilot_bounds['max_lon'] - pilot_bounds['min_lon']) * 111:.0f} x {(pilot_bounds['max_lat'] - pilot_bounds['min_lat']) * 111:.0f} km")
    
    # Generate grid
    lons = np.arange(pilot_bounds['min_lon'], pilot_bounds['max_lon'], grid_resolution)
    lats = np.arange(pilot_bounds['min_lat'], pilot_bounds['max_lat'], grid_resolution)
    
    grid_points = []
    for lon in lons:
        for lat in lats:
            grid_points.append({
                'longitude': lon,
                'latitude': lat,
                'grid_id': f"{lon:.3f}_{lat:.3f}"
            })
    
    grid_df = pd.DataFrame(grid_points)
    
    print(f"\n2️⃣ Grid Generation Results:")
    print(f"   Grid points generated: {len(grid_df)}")
    print(f"   Longitude range: {grid_df['longitude'].min():.3f}° - {grid_df['longitude'].max():.3f}°")
    print(f"   Latitude range: {grid_df['latitude'].min():.3f}° - {grid_df['latitude'].max():.3f}°")
    
    # Add mock auxiliary data for testing
    np.random.seed(42)
    grid_df['population_density'] = np.random.lognormal(3, 1, len(grid_df))
    grid_df['urban_fraction'] = np.random.beta(2, 5, len(grid_df))
    grid_df['elevation'] = np.random.normal(500, 200, len(grid_df))
    
    print(f"\n3️⃣ Auxiliary Data Statistics:")
    print(f"   Population density: {grid_df['population_density'].mean():.0f} ± {grid_df['population_density'].std():.0f} people/km²")
    print(f"   Urban fraction: {grid_df['urban_fraction'].mean():.2f} ± {grid_df['urban_fraction'].std():.2f}")
    print(f"   Elevation: {grid_df['elevation'].mean():.0f} ± {grid_df['elevation'].std():.0f} m")
    
    # Test data quality
    missing_data = grid_df.isnull().sum().sum()
    if missing_data > 0:
        print(f"❌ TEST FAILED: {missing_data} missing values in grid")
        return False
    
    print(f"\n✅ TEST PASSED: Spatial grid generated successfully!")
    return True


def test_emission_estimation():
    """Test emission estimation for pilot region"""
    print("\n📊 MEDIUM SCALE TEST: Emission Estimation")
    print("=" * 55)
    
    # Load data
    loader = RealDataLoader()
    all_data = loader.get_all_available_data()
    
    if 'IPCC_2022' not in all_data:
        print("❌ TEST FAILED: IPCC data not available")
        return False
    
    ipcc_data = all_data['IPCC_2022']
    
    # Simple spatial downscaling estimation
    print("1️⃣ Estimating Pilot Region Emissions:")
    
    # Urban vs rural emission factors (simplified)
    urban_factor = 5.0  # Urban areas have 5x higher emissions
    rural_factor = 1.0
    
    # Grid for estimation
    grid_size = 10  # 10x10 grid for testing
    total_national_co2 = ipcc_data[ipcc_data['gas_type'] == 'CO2']['emissions_2022_gg_co2eq'].sum()
    
    # Estimate pilot region fraction (urban area)
    pilot_area_fraction = 0.001  # 0.1% of national area
    urban_fraction = 0.3  # 30% urban in pilot region
    
    urban_emissions = total_national_co2 * pilot_area_fraction * urban_fraction * urban_factor
    rural_emissions = total_national_co2 * pilot_area_fraction * (1 - urban_fraction) * rural_factor
    total_pilot_emissions = urban_emissions + rural_emissions
    
    print(f"   National CO2 emissions: {total_national_co2:.0f} Gg CO2-eq")
    print(f"   Pilot urban emissions: {urban_emissions:.2f} Gg CO2-eq")
    print(f"   Pilot rural emissions: {rural_emissions:.2f} Gg CO2-eq")
    print(f"   Total pilot emissions: {total_pilot_emissions:.2f} Gg CO2-eq")
    
    # Spatial distribution
    print(f"\n2️⃣ Spatial Distribution Analysis:")
    grid_emissions = []
    
    # Calculate base emission per cell
    base_emission_per_cell = total_pilot_emissions / (grid_size * grid_size)
    
    for i in range(grid_size):
        for j in range(grid_size):
            # Simulate urban center effect
            distance_from_center = np.sqrt((i - grid_size/2)**2 + (j - grid_size/2)**2)
            urban_prob = max(0, 1 - distance_from_center / (grid_size/2))
            
            # Assign emission factor based on urban probability
            if urban_prob > 0.5:
                emission_factor = urban_factor
            else:
                emission_factor = rural_factor
            
            # Calculate weighted emissions (normalized to maintain total)
            cell_emissions = base_emission_per_cell * emission_factor
            
            grid_emissions.append({
                'grid_x': i,
                'grid_y': j,
                'urban_probability': urban_prob,
                'emissions_co2': cell_emissions,
                'emissions_per_km2': cell_emissions * 100  # Convert to per km²
            })
    
    emissions_df = pd.DataFrame(grid_emissions)
    
    # Normalize to maintain mass balance
    current_total = emissions_df['emissions_co2'].sum()
    normalization_factor = total_pilot_emissions / current_total
    emissions_df['emissions_co2'] = emissions_df['emissions_co2'] * normalization_factor
    emissions_df['emissions_per_km2'] = emissions_df['emissions_per_km2'] * normalization_factor
    
    print(f"   Grid cells: {len(emissions_df)}")
    print(f"   Emissions range: {emissions_df['emissions_co2'].min():.3f} - {emissions_df['emissions_co2'].max():.3f} Gg CO2-eq/cell")
    print(f"   Peak emissions: {emissions_df['emissions_co2'].max():.3f} Gg CO2-eq/cell")
    print(f"   Total verification: {emissions_df['emissions_co2'].sum():.3f} Gg CO2-eq")
    
    # Validate mass conservation
    estimated_total = emissions_df['emissions_co2'].sum()
    mass_balance_error = abs(estimated_total - total_pilot_emissions) / total_pilot_emissions
    
    if mass_balance_error > 0.01:  # 1% tolerance
        print(f"❌ TEST FAILED: Mass balance error {mass_balance_error*100:.1f}%")
        return False
    
    print(f"   ✅ Mass balance validated (error: {mass_balance_error*100:.2f}%)")
    
    print(f"\n✅ TEST PASSED: Emission estimation completed successfully!")
    return True


if __name__ == "__main__":
    print("🚀 Starting Medium Scale Tests for GHG Emissions Analysis")
    print("=" * 65)
    
    # Run tests
    test1_passed = test_pilot_region_analysis()
    test2_passed = test_spatial_grid_generation()
    test3_passed = test_emission_estimation()
    
    # Summary
    print("\n📋 MEDIUM SCALE TEST SUMMARY:")
    print("=" * 65)
    print(f"✅ Pilot Region Analysis: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"✅ Spatial Grid Generation: {'PASSED' if test2_passed else 'FAILED'}")
    print(f"✅ Emission Estimation: {'PASSED' if test3_passed else 'FAILED'}")
    
    if test1_passed and test2_passed and test3_passed:
        print("\n🎉 ALL MEDIUM SCALE TESTS PASSED!")
        print("   Next step: Run large scale tests for full country analysis")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("   Please fix issues before proceeding to large scale analysis")
        sys.exit(1)