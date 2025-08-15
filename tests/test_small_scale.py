#!/usr/bin/env python3
"""
Small Scale Test: IPCC Data Loading and Validation

This test script validates that IPCC 2022 data can be loaded successfully.
Use this as the first test before running larger analyses.

Author: AlphaEarth Analysis Team
Date: January 2025
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from preprocessing.data_loader import RealDataLoader
import pandas as pd


def test_ipcc_data_loading():
    """Test IPCC 2022 data loading"""
    print("🧪 SMALL SCALE TEST: IPCC Data Loading")
    print("=" * 50)
    
    # Initialize data loader
    loader = RealDataLoader()
    
    # Check data availability
    print("\n1️⃣ Checking Data Availability:")
    status = loader.validate_data_availability()
    for source, available in status.items():
        status_icon = "✅" if available else "❌"
        print(f"   {status_icon} {source}")
    
    if not status.get('IPCC_2022', False):
        print("\n❌ TEST FAILED: IPCC 2022 data not available")
        print("   Please ensure files exist in data/ipcc_2022_data/")
        return False
    
    # Load IPCC data
    print("\n2️⃣ Loading IPCC 2022 Data:")
    ipcc_data = loader.load_ipcc_2022_data()
    
    if ipcc_data is None or len(ipcc_data) == 0:
        print("❌ TEST FAILED: Could not load IPCC data")
        return False
    
    # Validate data structure
    print("\n3️⃣ Validating Data Structure:")
    required_cols = ['IPCC Category', 'Greenhouse gas']
    missing_cols = [col for col in required_cols if col not in ipcc_data.columns]
    
    if missing_cols:
        print(f"❌ TEST FAILED: Missing columns: {missing_cols}")
        return False
    
    print("✅ All required columns present")
    
    # Data summary
    print("\n4️⃣ Data Summary:")
    print(f"   📊 Total records: {len(ipcc_data)}")
    print(f"   🏭 Categories: {ipcc_data['IPCC Category'].nunique()}")
    print(f"   💨 Gases: {ipcc_data['Greenhouse gas'].value_counts().to_dict()}")
    
    if 'emissions_2022_gg_co2eq' in ipcc_data.columns:
        total_emissions = ipcc_data['emissions_2022_gg_co2eq'].sum()
        print(f"   🌍 Total emissions: {total_emissions:.1f} Gg CO2-eq")
    
    # Show top emission sources
    print("\n5️⃣ Top 5 Emission Sources:")
    if 'emissions_2022_gg_co2eq' in ipcc_data.columns:
        top_sources = ipcc_data.nlargest(5, 'emissions_2022_gg_co2eq')[
            ['IPCC Category', 'Greenhouse gas', 'emissions_2022_gg_co2eq']
        ]
        for idx, row in top_sources.iterrows():
            print(f"   {row['IPCC Category'][:50]:<50} | {row['Greenhouse gas']:<4} | {row['emissions_2022_gg_co2eq']:>8.1f}")
    
    print("\n✅ TEST PASSED: IPCC data loaded and validated successfully!")
    return True


def test_data_quality():
    """Test data quality checks"""
    print("\n🔍 SMALL SCALE TEST: Data Quality Validation")
    print("=" * 50)
    
    loader = RealDataLoader()
    ipcc_data = loader.load_ipcc_2022_data()
    
    if len(ipcc_data) == 0:
        print("❌ No data to validate")
        return False
    
    # Check for missing values
    print("\n1️⃣ Checking for Missing Values:")
    missing_counts = ipcc_data.isnull().sum()
    if missing_counts.sum() > 0:
        print("⚠️  Found missing values:")
        for col, count in missing_counts[missing_counts > 0].items():
            print(f"   {col}: {count} missing")
    else:
        print("✅ No missing values found")
    
    # Check data types
    print("\n2️⃣ Checking Data Types:")
    for col, dtype in ipcc_data.dtypes.items():
        print(f"   {col}: {dtype}")
    
    # Check for duplicates
    print("\n3️⃣ Checking for Duplicates:")
    duplicates = ipcc_data.duplicated().sum()
    if duplicates > 0:
        print(f"⚠️  Found {duplicates} duplicate rows")
    else:
        print("✅ No duplicate rows found")
    
    print("\n✅ Data quality validation completed!")
    return True


if __name__ == "__main__":
    print("🚀 Starting Small Scale Tests for GHG Emissions Analysis")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_ipcc_data_loading()
    test2_passed = test_data_quality()
    
    # Summary
    print("\n📋 TEST SUMMARY:")
    print("=" * 60)
    print(f"✅ IPCC Data Loading: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"✅ Data Quality Check: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL SMALL SCALE TESTS PASSED!")
        print("   Next step: Run medium scale tests with analysis")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("   Please fix issues before proceeding")
        sys.exit(1)