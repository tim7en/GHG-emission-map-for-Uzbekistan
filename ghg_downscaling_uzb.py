#!/usr/bin/env python3
"""
Standalone GHG Emissions Downscaling Script for Uzbekistan

This script provides a complete, standalone greenhouse gas emissions
downscaling analysis system for Uzbekistan using Google Earth Engine
and machine learning techniques.

Features:
- Multi-source emissions data integration (ODIAC, EDGAR)
- High-resolution spatial downscaling (1km to 200m)
- Comprehensive visualization and reporting
- Uncertainty quantification
- Sector-specific analysis

Usage:
    python ghg_downscaling_uzb.py

Requirements:
    - Python 3.8+
    - Google Earth Engine account (optional - will run in simulation mode)
    - Dependencies listed in requirements.txt

Author: AlphaEarth Analysis Team - GHG Module
Date: January 2025
"""

import sys
import os
from pathlib import Path

# Add source directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Change to project directory for relative paths
os.chdir(current_dir)

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking Dependencies")
    print("-" * 30)
    
    required_packages = [
        'numpy', 'pandas', 'matplotlib', 'seaborn', 'sklearn', 
        'scipy', 'pathlib'
    ]
    
    optional_packages = ['ee', 'geemap']
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"SUCCESS: {package}")
        except ImportError:
            missing_required.append(package)
            print(f"ERROR: {package}")
    
    for package in optional_packages:
        try:
            __import__(package)
            print(f"SUCCESS: {package} (optional)")
        except ImportError:
            missing_optional.append(package)
            print(f"WARNING:  {package} (optional - simulation mode will be used)")
    
    if missing_required:
        print(f"\nERROR: Missing required packages: {', '.join(missing_required)}")
        print("Please install with: pip install " + " ".join(missing_required))
        return False
    
    if missing_optional:
        print(f"\nWARNING:  Missing optional packages: {', '.join(missing_optional)}")
        print("For full GEE functionality, install with: pip install earthengine-api geemap")
        print("Analysis will continue in simulation mode.")
    
    print("\nSUCCESS: Dependency check complete")
    return True

def check_gee_authentication():
    """Check Google Earth Engine authentication status"""
    print("\n🔐 Checking Google Earth Engine Authentication")
    print("-" * 50)
    
    try:
        import ee
        
        # Check authentication status file
        auth_status_file = Path(".gee_auth_status_ghg.json")
        if auth_status_file.exists():
            import json
            try:
                with open(auth_status_file, 'r') as f:
                    status = json.load(f)
                if status.get("authenticated", False):
                    print("SUCCESS: Previous authentication detected")
            except:
                pass
        
        # Try to initialize
        try:
            ee.Initialize(project='ee-sabitovty')
            print("SUCCESS: Google Earth Engine authentication successful with project ee-sabitovty")
            
            # Test basic functionality
            test_result = ee.Number(2025).getInfo()
            print(f"SUCCESS: GEE connection test successful: {test_result}")
            
            return True
            
        except Exception as e:
            print(f"ERROR: GEE authentication failed: {e}")
            print("SETTINGS: To authenticate, run: python gee_auth.py")
            print("   Or the analysis will run in simulation mode")
            return False
            
    except ImportError:
        print("WARNING:  Google Earth Engine API not available")
        print("   Analysis will run in simulation mode")
        return False

def show_startup_banner():
    """Display startup banner with project information"""
    print("🏭" + "=" * 70 + "EARTH:")
    print("    GHG EMISSIONS DOWNSCALING ANALYSIS FOR UZBEKISTAN")
    print("    High-Resolution Greenhouse Gas Mapping Using Machine Learning")
    print("=" * 72)
    print()
    print("TARGET: OBJECTIVES:")
    print("   * Spatial downscaling of GHG emissions (1km -> 200m resolution)")
    print("   * Multi-source data integration (ODIAC, EDGAR, auxiliary data)")
    print("   * Sector-specific emissions analysis")
    print("   * Uncertainty quantification and validation")
    print("   * Comprehensive mapping and reporting")
    print()
    print("CHART: OUTPUTS:")
    print("   * High-resolution emissions maps")
    print("   * Regional emissions summaries")
    print("   * Model performance metrics")
    print("   * Technical analysis report")
    print()
    print("MICROSCOPE: METHODS:")
    print("   * Machine learning-based spatial downscaling")
    print("   * Multi-variate regression with auxiliary predictors")
    print("   * Cross-validation and uncertainty assessment")
    print("   * Google Earth Engine integration")
    print()
    print("=" * 72)

def create_project_structure():
    """Create necessary project directories"""
    print("📁 Setting Up Project Structure")
    print("-" * 35)
    
    directories = [
        "src",
        "data", 
        "outputs",
        "figs",
        "reports"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"SUCCESS: {directory}/")
    
    print("SUCCESS: Project structure ready")

def create_requirements_file():
    """Create requirements.txt file for the project"""
    requirements_content = """# GHG Emissions Downscaling Requirements
# Core scientific computing
numpy>=1.21.0
pandas>=1.3.0
matplotlib>=3.5.0
seaborn>=0.11.0
scikit-learn>=1.0.0
scipy>=1.7.0

# Geospatial libraries
geopandas>=0.10.0
rasterio>=1.2.0
shapely>=1.8.0
pyproj>=3.3.0

# Optional: Google Earth Engine
earthengine-api>=0.1.300
geemap>=0.15.0

# Utilities
pathlib2>=2.3.0
tqdm>=4.62.0
"""
    
    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        with open(requirements_path, 'w') as f:
            f.write(requirements_content)
        print(f"📄 Created: {requirements_path}")

def show_analysis_options():
    """Show available analysis options to user"""
    print("\n🎛️  Analysis Options")
    print("-" * 25)
    print("1. STARTING: Run Complete Analysis (Recommended)")
    print("2. 🔐 Setup/Test GEE Authentication")
    print("3. CHART: Load and Explore Data Only")
    print("4. 🤖 Train Models Only")
    print("5. 🗺️  Create Maps Only")
    print("6. ❓ Show Help")
    print("7. 🚪 Exit")
    
    choice = input("\nSelect option (1-7): ").strip()
    return choice

def run_authentication_setup():
    """Run GEE authentication setup"""
    print("\n🔐 Setting Up Google Earth Engine Authentication")
    print("-" * 55)
    
    try:
        from gee_auth import main as auth_main
        success = auth_main()
        return success
    except Exception as e:
        print(f"ERROR: Authentication setup failed: {e}")
        print("   You can still run the analysis in simulation mode")
        return False

def run_data_exploration():
    """Run data exploration only"""
    print("\nCHART: Data Exploration Mode")
    print("-" * 30)
    
    try:
        from ghg_downscaling import GHGEmissionsDownscaler
        
        downscaler = GHGEmissionsDownscaler()
        downscaler.initialize_gee()
        
        # Load and explore data
        downscaler.load_emissions_data()
        downscaler.load_auxiliary_data()
        
        print("\nSUCCESS: Data exploration complete!")
        print("   Check data/ directory for loaded datasets")
        
    except Exception as e:
        print(f"ERROR: Data exploration failed: {e}")
        import traceback
        traceback.print_exc()

def run_model_training():
    """Run model training only"""
    print("\n🤖 Model Training Mode")
    print("-" * 25)
    
    try:
        from ghg_downscaling import GHGEmissionsDownscaler
        
        downscaler = GHGEmissionsDownscaler()
        downscaler.initialize_gee()
        
        # Load data and train models
        downscaler.load_emissions_data()
        downscaler.load_auxiliary_data()
        integrated_data = downscaler.prepare_downscaling_dataset()
        downscaler.train_downscaling_models(integrated_data)
        
        print("\nSUCCESS: Model training complete!")
        print("   Check outputs/ directory for model performance metrics")
        
    except Exception as e:
        print(f"ERROR: Model training failed: {e}")
        import traceback
        traceback.print_exc()

def run_mapping_only():
    """Run mapping/visualization only"""
    print("\n🗺️  Mapping Mode")
    print("-" * 20)
    
    # Check if downscaled data exists
    output_files = list(Path("outputs").glob("downscaled_*_emissions.csv"))
    
    if not output_files:
        print("ERROR: No downscaled data found. Run complete analysis first.")
        return
    
    try:
        from ghg_downscaling import GHGEmissionsDownscaler
        import pandas as pd
        
        downscaler = GHGEmissionsDownscaler()
        
        # Load existing downscaled data
        for output_file in output_files:
            gas_type = output_file.stem.replace("downscaled_", "").replace("_emissions", "")
            data = pd.read_csv(output_file)
            downscaler.downscaled_data[gas_type.upper() + "_emissions"] = data
        
        # Create maps
        for gas_type in downscaler.downscaled_data.keys():
            downscaler.create_emissions_maps(gas_type)
        
        print("\nSUCCESS: Mapping complete!")
        print("   Check figs/ directory for generated maps")
        
    except Exception as e:
        print(f"ERROR: Mapping failed: {e}")
        import traceback
        traceback.print_exc()

def show_help():
    """Show detailed help information"""
    help_text = """
🆘 GHG EMISSIONS DOWNSCALING HELP

📖 OVERVIEW:
This tool performs high-resolution spatial downscaling of greenhouse gas 
emissions for Uzbekistan using machine learning and geospatial data.

SETTINGS: SETUP:
1. Install dependencies: pip install -r requirements.txt
2. (Optional) Authenticate with Google Earth Engine: python gee_auth.py
3. Run analysis: python ghg_downscaling_uzb.py

CHART: ANALYSIS MODES:

1. COMPLETE ANALYSIS (Recommended)
   * Runs full end-to-end analysis
   * Loads emissions data, trains models, creates maps
   * Generates comprehensive report
   * Duration: 10-30 minutes

2. AUTHENTICATION SETUP
   * Tests/configures Google Earth Engine access
   * Required for real satellite data
   * Falls back to simulation mode if unavailable

3. DATA EXPLORATION
   * Loads and examines emissions datasets
   * No model training or prediction
   * Quick overview of available data

4. MODEL TRAINING
   * Trains machine learning models only
   * Uses loaded emissions and auxiliary data
   * Generates model performance metrics

5. MAPPING
   * Creates visualizations from existing results
   * Requires previous analysis run
   * Generates high-quality maps and plots

📁 OUTPUT STRUCTURE:
├── data/           # Loaded datasets
├── outputs/        # Analysis results and models
├── figs/           # Maps and visualizations  
├── reports/        # Technical reports
└── src/            # Source code

🔍 TROUBLESHOOTING:
* Missing packages: pip install -r requirements.txt
* GEE errors: Run python gee_auth.py for authentication
* Simulation mode: Analysis works without GEE authentication
* Memory issues: Reduce target resolution in config

📧 SUPPORT:
For technical support or questions about the methodology,
refer to the generated technical report or documentation.
"""
    
    print(help_text)

def run_complete_analysis():
    """Run the complete GHG emissions downscaling analysis"""
    print("\nSTARTING: Starting Complete Analysis")
    print("-" * 35)
    
    try:
        from ghg_downscaling import GHGEmissionsDownscaler
        
        # Initialize and run complete analysis
        downscaler = GHGEmissionsDownscaler()
        downscaler.run_complete_analysis()
        
        # Show completion summary
        print("\n🎉 ANALYSIS COMPLETED SUCCESSFULLY! 🎉")
        print("=" * 45)
        print("CHART: Results Summary:")
        print(f"   * Emissions data processed: {len(downscaler.emissions_data)} sources")
        print(f"   * Models trained: {len(downscaler.models)} gas types")
        print(f"   * Maps created: {len(downscaler.downscaled_data)} gas types")
        print()
        print("📁 Output Locations:")
        print(f"   * Data: {Path('data').absolute()}")
        print(f"   * Results: {Path('outputs').absolute()}")
        print(f"   * Maps: {Path('figs').absolute()}")
        print(f"   * Reports: {Path('reports').absolute()}")
        print()
        print("🔍 Next Steps:")
        print("   * Review the technical report in reports/")
        print("   * Examine emissions maps in figs/")
        print("   * Check model performance in outputs/")
        print("   * Validate results with field data (if available)")
        
    except Exception as e:
        print(f"ERROR: Analysis failed: {e}")
        print("\nSETTINGS: Troubleshooting:")
        print("   * Check dependency installation: pip install -r requirements.txt")
        print("   * Verify project permissions and disk space")
        print("   * Try running in smaller segments using other menu options")
        print("   * Check the detailed error above for specific issues")
        
        import traceback
        traceback.print_exc()

def main():
    """Main function for the standalone GHG emissions downscaling script"""
    
    # Show startup banner
    show_startup_banner()
    
    # Create project structure
    create_project_structure()
    create_requirements_file()
    
    # Check dependencies
    if not check_dependencies():
        print("\nERROR: Cannot proceed without required dependencies")
        print("   Install them with: pip install -r requirements.txt")
        sys.exit(1)
    
    # Check GEE authentication
    gee_available = check_gee_authentication()
    
    if not gee_available:
        print("\nWARNING:  Google Earth Engine not available")
        print("   Analysis will run in simulation mode with synthetic data")
        print("   For real satellite data, run: python gee_auth.py")
    
    # Interactive menu
    while True:
        choice = show_analysis_options()
        
        if choice == "1":
            run_complete_analysis()
            break
        elif choice == "2":
            run_authentication_setup()
        elif choice == "3":
            run_data_exploration()
        elif choice == "4":
            run_model_training()
        elif choice == "5":
            run_mapping_only()
        elif choice == "6":
            show_help()
        elif choice == "7":
            print("\n👋 Goodbye!")
            break
        else:
            print("\nERROR: Invalid choice. Please select 1-7.")
        
        # Ask if user wants to continue
        if choice in ["1"]:
            break
        
        continue_choice = input("\nPress Enter to return to menu, or 'q' to quit: ").strip().lower()
        if continue_choice == 'q':
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()