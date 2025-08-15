#!/usr/bin/env python3
"""
Simple test to check IPCC data loading
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from preprocessing.data_loader import RealDataLoader
    
    print("GHG EMISSIONS ANALYSIS - SIMPLE TEST")
    print("=" * 50)
    
    # Initialize data loader
    print("1. Initializing data loader...")
    loader = RealDataLoader()
    print("   Data loader initialized successfully!")
    
    # Check data availability
    print("\n2. Checking data availability...")
    status = loader.validate_data_availability()
    for source, available in status.items():
        status_icon = "OK" if available else "FAILED"
        print(f"   {source}: {status_icon}")
    
    if not status.get('IPCC_2022', False):
        print("\nERROR: IPCC 2022 data not available")
        sys.exit(1)
    
    # Load IPCC data
    print("\n3. Loading IPCC 2022 data...")
    ipcc_data = loader.load_ipcc_2022_data()
    
    if ipcc_data is None or len(ipcc_data) == 0:
        print("ERROR: Could not load IPCC data")
        sys.exit(1)
    
    print(f"   Total records: {len(ipcc_data)}")
    print(f"   Columns: {list(ipcc_data.columns)}")
    
    # Get summary statistics
    if 'CO2_equivalent_Gg' in ipcc_data.columns:
        total_emissions = ipcc_data['CO2_equivalent_Gg'].sum()
        print(f"   Total emissions: {total_emissions:.1f} Gg CO2-eq")
    
    print("\n4. Data quality check...")
    print(f"   Missing values: {ipcc_data.isnull().sum().sum()}")
    print(f"   Duplicate rows: {ipcc_data.duplicated().sum()}")
    
    # Show first few records
    print("\n5. Sample data:")
    print(ipcc_data.head(3).to_string())
    
    print("\nSUCCESS: IPCC data loaded and validated!")
    print("Ready for further analysis.")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
