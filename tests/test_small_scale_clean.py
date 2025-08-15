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
    print("SMALL SCALE TEST: IPCC Data Loading")
    print("=" * 50)
    
    # Initialize data loader
    loader = RealDataLoader()
    
    # Check data availability
    print("\n1. Checking Data Availability:")
    status = loader.validate_data_availability()
    for source, available in status.items():
        status_icon = "OK" if available else "FAILED"
        print(f"   {status_icon} {source}")
    
    if not status.get('IPCC_2022', False):
        print("\nTEST FAILED: IPCC 2022 data not available")
        print("   Please ensure files exist in data/ipcc_2022_data/")
        return False
    
    # Load IPCC data
    print("\n2. Loading IPCC 2022 Data:")
    ipcc_data = loader.load_ipcc_2022_data()
    
    if ipcc_data is None or len(ipcc_data) == 0:
        print("TEST FAILED: Could not load IPCC data")
        return False
    
    # Validate data structure
    print("\n3. Validating Data Structure:")
    required_cols = ['IPCC Category', 'Greenhouse gas']
    missing_cols = [col for col in required_cols if col not in ipcc_data.columns]
    
    if missing_cols:
        print(f"TEST FAILED: Missing columns: {missing_cols}")
        return False
    
    print("OK - All required columns present")
    
    # Data summary
    print("\n4. Data Summary:")
    print(f"   Total records: {len(ipcc_data)}")
    print(f"   Total columns: {len(ipcc_data.columns)}")
    
    # Check for emissions data
    emission_cols = [col for col in ipcc_data.columns if 'emission' in col.lower() or 'co2' in col.lower()]
    if emission_cols:
        print(f"   Emission columns found: {emission_cols}")
        for col in emission_cols:
            if pd.api.types.is_numeric_dtype(ipcc_data[col]):
                total = ipcc_data[col].sum()
                print(f"   Total {col}: {total:.1f}")
    
    # Gas types
    if 'Greenhouse gas' in ipcc_data.columns:
        gas_types = ipcc_data['Greenhouse gas'].unique()
        print(f"   Gas types: {list(gas_types)}")
    
    print("\nTEST PASSED: IPCC data loaded and validated successfully!")
    return True


def test_data_quality():
    """Test data quality"""
    print("\nSMALL SCALE TEST: Data Quality")
    print("=" * 50)
    
    loader = RealDataLoader()
    ipcc_data = loader.load_ipcc_2022_data()
    
    if ipcc_data is None or len(ipcc_data) == 0:
        print("ERROR: No data to validate")
        return False
    
    # Check for missing values
    print("\n1. Checking for Missing Values:")
    missing_count = ipcc_data.isnull().sum().sum()
    print(f"   Total missing values: {missing_count}")
    
    if missing_count == 0:
        print("OK - No missing values found")
    
    # Data types
    print("\n2. Checking Data Types:")
    print(f"   Data types summary:")
    for dtype in ipcc_data.dtypes.unique():
        count = (ipcc_data.dtypes == dtype).sum()
        print(f"   {dtype}: {count} columns")
    
    # Check for duplicates
    print("\n3. Checking for Duplicates:")
    duplicate_count = ipcc_data.duplicated().sum()
    print(f"   Duplicate rows: {duplicate_count}")
    
    if duplicate_count == 0:
        print("OK - No duplicate rows found")
    
    print("\nOK - Data quality validation completed!")
    return True


if __name__ == "__main__":
    print("STARTING SMALL SCALE TESTS FOR GHG EMISSIONS ANALYSIS")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_ipcc_data_loading()
    test2_passed = test_data_quality()
    
    # Summary
    print("\nTEST SUMMARY:")
    print("=" * 60)
    print(f"IPCC Data Loading: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"Data Quality Check: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\nALL SMALL SCALE TESTS PASSED!")
        print("   Next step: Run medium scale tests with analysis")
    else:
        print("\nSOME TESTS FAILED!")
        print("   Please fix issues before proceeding")
        sys.exit(1)
