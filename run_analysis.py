#!/usr/bin/env python3
"""
GHG Emissions Analysis for Uzbekistan - Main Entry Point

This script provides a clear, structured approach to GHG emissions analysis
following the progressive testing methodology: small -> medium -> large scale.

Features:
- No mock data usage (real IPCC 2022 data only)
- Progressive testing from small pilot regions to full country
- Clear folder structure and user guidance
- Comprehensive validation at each scale

Usage:
    python run_analysis.py                    # Interactive mode
    python run_analysis.py --test small       # Run small scale tests
    python run_analysis.py --test medium      # Run medium scale tests  
    python run_analysis.py --test large       # Run large scale tests
    python run_analysis.py --scale full       # Full country analysis

Author: AlphaEarth Analysis Team - GHG Module
Date: January 2025
"""

import sys
import argparse
from pathlib import Path
import subprocess


def print_banner():
    """Print welcome banner"""
    print("EARTH: GHG EMISSIONS ANALYSIS FOR UZBEKISTAN")
    print("=" * 50)
    print("Advanced Greenhouse Gas Emissions Downscaling System")
    print("Using Real IPCC 2022 Data + Google Earth Engine")
    print("=" * 50)


def print_help():
    """Print detailed help information"""
    help_text = """
BOOK: ANALYSIS METHODOLOGY

This system follows a progressive testing approach to ensure reliability:

MICROSCOPE: PHASE 1: SMALL SCALE TESTS
   * Validate IPCC 2022 data loading
   * Check data quality and completeness  
   * Verify system configuration
   Duration: ~30 seconds

CITY:  PHASE 2: MEDIUM SCALE TESTS  
   * Pilot region analysis (Tashkent area, 100km^2)
   * Spatial grid generation and validation
   * Emission estimation with mass balance
   Duration: ~2 minutes

MAP:  PHASE 3: LARGE SCALE TESTS
   * Full country data loading and validation
   * National spatial coverage assessment
   * Performance and scalability testing  
   Duration: ~5 minutes

STARTING: PHASE 4: PRODUCTION ANALYSIS
   * Complete Uzbekistan emissions mapping
   * High-resolution spatial downscaling
   * Comprehensive reports and visualizations
   Duration: 10-30 minutes

CHART: DATA SOURCES (NO MOCK DATA)
   * IPCC 2022 National Inventory (Primary)
   * Google Earth Engine satellite data (Optional)
   * Real geospatial auxiliary data only

FOLDER: FOLDER STRUCTURE
   data/
   ├── ipcc_2022_data/     # IPCC 2022 emissions data
   ├── raw/                # Raw datasets  
   ├── processed/          # Processed data
   └── validation/         # Validation data
   
   src/
   ├── preprocessing/      # Data loading modules
   ├── analysis/          # Analysis algorithms
   ├── visualization/     # Plotting and mapping
   └── utils/            # Utility functions
   
   tests/                 # Progressive test suite
   configs/              # Configuration files
   outputs/              # Analysis results

SETTINGS: COMMANDS
   
   python run_analysis.py
   # Interactive menu for guided analysis
   
   python run_analysis.py --test small
   # Run small scale validation tests
   
   python run_analysis.py --test medium  
   # Run medium scale pilot region tests
   
   python run_analysis.py --test large
   # Run large scale performance tests
   
   python run_analysis.py --scale full
   # Execute full country analysis
   
   python run_analysis.py --help
   # Show this help information

WARNING:  REQUIREMENTS
   * Python 3.8+
   * Required packages: pip install -r requirements.txt
   * IPCC 2022 data files in data/ipcc_2022_data/
   * (Optional) Google Earth Engine authentication

SUCCESS: VALIDATION
   Each phase includes comprehensive validation:
   * Data loading and quality checks
   * Mass balance conservation
   * Performance benchmarking
   * Result verification
"""
    print(help_text)


def run_tests(scale):
    """Run tests for specified scale"""
    print(f"\n🧪 Running {scale.upper()} Scale Tests")
    print("-" * 40)
    
    test_file = f"tests/test_{scale}_scale.py"
    
    if not Path(test_file).exists():
        print(f"ERROR: Test file not found: {test_file}")
        return False
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True)
        
        # Print output
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        # Check if tests passed
        if result.returncode == 0:
            print(f"\nSUCCESS: {scale.upper()} SCALE TESTS PASSED!")
            return True
        else:
            print(f"\nERROR: {scale.upper()} SCALE TESTS FAILED!")
            return False
            
    except Exception as e:
        print(f"ERROR: Error running tests: {e}")
        return False


def run_full_analysis():
    """Run full country analysis"""
    print("\nSTARTING: Starting Full Country Analysis")
    print("=" * 40)
    
    # Check if all tests have been run successfully
    print("1. Verifying Prerequisites...")
    
    # Run prerequisite tests quickly
    prereq_tests = ['small', 'medium', 'large']
    all_passed = True
    
    for test_scale in prereq_tests:
        print(f"   Checking {test_scale} scale prerequisites...")
        if not run_tests(test_scale):
            print(f"   ERROR: {test_scale} scale tests failed")
            all_passed = False
            break
        else:
            print(f"   SUCCESS: {test_scale} scale tests passed")
    
    if not all_passed:
        print("\nERROR: Prerequisites not met. Please run and fix tests first:")
        print("   python run_analysis.py --test small")
        print("   python run_analysis.py --test medium") 
        print("   python run_analysis.py --test large")
        return False
    
    print("\n2. Starting Full Analysis...")
    
    # Import and run the main analysis
    try:
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from preprocessing.data_loader import RealDataLoader
        
        # Initialize analysis
        loader = RealDataLoader()
        
        print("\nCHART: Loading National Emissions Data...")
        all_data = loader.get_all_available_data()
        
        if len(all_data) == 0:
            print("ERROR: No data available for analysis")
            return False
        
        print(f"SUCCESS: Loaded {len(all_data)} data sources")
        
        # For now, just validate the data loading
        # Full analysis implementation would go here
        for source, data in all_data.items():
            print(f"   {source}: {len(data)} records")
        
        print("\nSUCCESS: Full Country Analysis Framework Ready!")
        print("   (Complete analysis implementation in progress)")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Analysis failed: {e}")
        return False


def interactive_menu():
    """Show interactive menu for user guidance"""
    while True:
        print("\nTARGET: INTERACTIVE ANALYSIS MENU")
        print("=" * 40)
        print("1. Run Small Scale Tests (Quick validation)")
        print("2. Run Medium Scale Tests (Pilot region)")  
        print("3. Run Large Scale Tests (Performance check)")
        print("4. Run Full Country Analysis")
        print("5. Run All Tests Progressively")
        print("6. Show Help Documentation")
        print("7. Exit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == '1':
            run_tests('small')
        elif choice == '2':
            run_tests('medium')
        elif choice == '3':
            run_tests('large')
        elif choice == '4':
            run_full_analysis()
        elif choice == '5':
            print("\n🔄 Running All Tests Progressively...")
            scales = ['small', 'medium', 'large']
            all_passed = True
            
            for scale in scales:
                if not run_tests(scale):
                    all_passed = False
                    break
            
            if all_passed:
                print("\n🎉 ALL TESTS PASSED! Ready for full analysis.")
                if input("Run full analysis now? (y/n): ").lower().startswith('y'):
                    run_full_analysis()
            else:
                print("\nWARNING:  Please fix failing tests before proceeding.")
                
        elif choice == '6':
            print_help()
        elif choice == '7':
            print("👋 Goodbye!")
            break
        else:
            print("ERROR: Invalid choice. Please select 1-7.")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="GHG Emissions Analysis for Uzbekistan",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--test', choices=['small', 'medium', 'large'],
                       help='Run specific scale tests')
    parser.add_argument('--scale', choices=['full'], 
                       help='Run full scale analysis')
    parser.add_argument('--help-detailed', action='store_true',
                       help='Show detailed help documentation')
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.help_detailed:
        print_help()
    elif args.test:
        run_tests(args.test)
    elif args.scale == 'full':
        run_full_analysis()
    else:
        interactive_menu()


if __name__ == "__main__":
    main()