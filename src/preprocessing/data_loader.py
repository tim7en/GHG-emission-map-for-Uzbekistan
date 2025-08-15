#!/usr/bin/env python3
"""
Data Loader Module for GHG Emissions Analysis

This module handles loading and preprocessing of real emissions data sources
including IPCC 2022 data, Google Earth Engine datasets, and auxiliary data.

Author: AlphaEarth Analysis Team - GHG Module
Date: January 2025
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import warnings
warnings.filterwarnings('ignore')

# Google Earth Engine Integration
try:
    import ee
    GEE_AVAILABLE = True
except ImportError:
    GEE_AVAILABLE = False


class RealDataLoader:
    """
    Real Data Loader for GHG Emissions Analysis
    
    This class loads only real data sources without any mock/synthetic data generation.
    """
    
    def __init__(self, config_path: str = "configs/config_ghg.json"):
        """Initialize the real data loader"""
        self.config_path = config_path
        self.config = self._load_config()
        self.gee_initialized = False
        
        # Initialize Google Earth Engine if available
        if GEE_AVAILABLE:
            self.gee_initialized = self._initialize_gee()
        
        # Data storage
        self.ipcc_data = None
        self.gee_data = {}
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        import json
        
        # Look for config in multiple locations
        possible_paths = [
            self.config_path,
            "config_ghg.json",
            "../configs/config_ghg.json"
        ]
        
        for path in possible_paths:
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                continue
        
        # Default configuration if no file found
        return {
            "country": "Uzbekistan",
            "analysis_period": {"start_year": 2015, "end_year": 2023},
            "ghg_sources": {"ODIAC": True, "EDGAR": True, "IPCC": True},
            "gases": ["CO2", "CH4", "N2O"],
            "spatial_resolution": 1000,
            "paths": {
                "data": "data",
                "ipcc_2022_data": "data/ipcc_2022_data",
                "raw": "data/raw",
                "processed": "data/processed"
            }
        }
    
    def _initialize_gee(self) -> bool:
        """Initialize Google Earth Engine"""
        try:
            ee.Initialize(project='ee-sabitovty')
            print("SUCCESS: Google Earth Engine initialized successfully")
            return True
        except Exception as e:
            print(f"WARNING: Could not initialize Google Earth Engine: {e}")
            print("   Analysis will use only local IPCC data")
            return False
    
    def load_ipcc_2022_data(self) -> pd.DataFrame:
        """Load IPCC 2022 emissions data for Uzbekistan"""
        print("\nLOADING: IPCC 2022 Emissions Data")
        print("-" * 40)
        
        # Try CSV first, then Excel
        csv_path = Path(self.config['paths']['ipcc_2022_data']) / "ipcc_ghg_emissions_2022_csv.csv"
        xlsx_path = Path(self.config['paths']['ipcc_2022_data']) / "ipcc_ghg_emissions_2022.xlsx"
        
        if csv_path.exists():
            try:
                # Read CSV with proper separator
                self.ipcc_data = pd.read_csv(csv_path, sep=';', encoding='utf-8')
                print(f"SUCCESS: Loaded IPCC CSV data: {len(self.ipcc_data)} emission categories")
            except Exception as e:
                print(f"ERROR: Error loading CSV: {e}")
                return pd.DataFrame()
        elif xlsx_path.exists():
            try:
                self.ipcc_data = pd.read_excel(xlsx_path)
                print(f"SUCCESS: Loaded IPCC Excel data: {len(self.ipcc_data)} emission categories")
            except Exception as e:
                print(f"ERROR: Error loading Excel: {e}")
                return pd.DataFrame()
        else:
            print("ERROR: No IPCC 2022 data found in data/ipcc_2022_data/")
            return pd.DataFrame()
        
        # Clean and process the data
        if self.ipcc_data is not None and len(self.ipcc_data) > 0:
            self.ipcc_data = self._process_ipcc_data(self.ipcc_data)
            self._print_ipcc_summary()
        
        return self.ipcc_data
    
    def _process_ipcc_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process and clean IPCC data"""
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Convert emission values to numeric (handle European decimal format)
        if '2022 Ex,t (Gg CO? Eq)' in df.columns:
            emission_col = '2022 Ex,t (Gg CO? Eq)'
            df['emissions_2022_gg_co2eq'] = df[emission_col].astype(str).str.replace(',', '.').astype(float)
        
        # Extract greenhouse gas type
        if 'Greenhouse gas' in df.columns:
            df['gas_type'] = df['Greenhouse gas'].str.replace('?', '2')  # Fix encoding issues
        
        # Extract sector information
        if 'IPCC Category' in df.columns:
            df['sector'] = df['IPCC Category']
        
        # Add country information
        df['country'] = self.config['country']
        df['year'] = 2022
        
        return df
    
    def _print_ipcc_summary(self):
        """Print summary of IPCC data"""
        if self.ipcc_data is None or len(self.ipcc_data) == 0:
            return
        
        print("\nSUMMARY: IPCC 2022 Data Summary:")
        print(f"   Total emission categories: {len(self.ipcc_data)}")
        
        if 'gas_type' in self.ipcc_data.columns:
            gas_counts = self.ipcc_data['gas_type'].value_counts()
            for gas, count in gas_counts.items():
                print(f"   {gas}: {count} categories")
        
        if 'emissions_2022_gg_co2eq' in self.ipcc_data.columns:
            total_emissions = self.ipcc_data['emissions_2022_gg_co2eq'].sum()
            print(f"   Total emissions: {total_emissions:.1f} Gg CO2-eq")
    
    def load_gee_data(self) -> Dict[str, pd.DataFrame]:
        """Load emissions data from Google Earth Engine"""
        print("\nSATELLITE: Loading Google Earth Engine Data")
        print("-" * 40)
        
        if not self.gee_initialized:
            print("ERROR: Google Earth Engine not available")
            return {}
        
        gee_datasets = {}
        
        try:
            # Get Uzbekistan boundaries
            uzbekistan = self._get_uzbekistan_geometry()
            
            if uzbekistan is None:
                print("ERROR: Could not define Uzbekistan boundaries")
                return {}
            
            # Load available datasets
            if self.config["ghg_sources"].get("ODIAC", False):
                gee_datasets["ODIAC"] = self._load_odiac_gee(uzbekistan)
            
            if self.config["ghg_sources"].get("EDGAR", False):
                gee_datasets["EDGAR"] = self._load_edgar_gee(uzbekistan)
        
        except Exception as e:
            print(f"ERROR: Error loading GEE data: {e}")
            return {}
        
        self.gee_data = gee_datasets
        return gee_datasets
    
    def _get_uzbekistan_geometry(self):
        """Get Uzbekistan geometry for GEE analysis"""
        try:
            # Define Uzbekistan approximate bounds
            uzbekistan_bounds = [
                [55.9, 37.2], [55.9, 45.6], [73.2, 45.6], [73.2, 37.2], [55.9, 37.2]
            ]
            
            return ee.Geometry.Polygon(uzbekistan_bounds)
        except Exception as e:
            print(f"ERROR: Error creating Uzbekistan geometry: {e}")
            return None
    
    def _load_odiac_gee(self, geometry) -> pd.DataFrame:
        """Load ODIAC data from Google Earth Engine"""
        try:
            print("RADAR: Loading ODIAC CO2 emissions...")
            
            # ODIAC fossil fuel CO2 emissions
            odiac = ee.ImageCollection('projects/earthengine-legacy/assets/users/projectgee/ODIAC_2019') \
                      .filterBounds(geometry) \
                      .filterDate('2019-01-01', '2019-12-31')
            
            if odiac.size().getInfo() == 0:
                print("WARNING: No ODIAC data available for Uzbekistan")
                return pd.DataFrame()
            
            # Sample the data
            sample = odiac.first().sample(
                region=geometry,
                scale=10000,  # 10km resolution
                numPixels=500,
                seed=42
            )
            
            # Convert to DataFrame
            sample_data = sample.getInfo()
            if not sample_data['features']:
                return pd.DataFrame()
            
            rows = []
            for feature in sample_data['features']:
                props = feature['properties']
                coords = feature['geometry']['coordinates']
                
                rows.append({
                    'longitude': coords[0],
                    'latitude': coords[1],
                    'CO2_emissions': props.get('co2_emission', 0),
                    'year': 2019,
                    'source': 'ODIAC_GEE'
                })
            
            df = pd.DataFrame(rows)
            print(f"SUCCESS: Loaded {len(df)} ODIAC data points")
            return df
            
        except Exception as e:
            print(f"ERROR: Error loading ODIAC data: {e}")
            return pd.DataFrame()
    
    def _load_edgar_gee(self, geometry) -> pd.DataFrame:
        """Load EDGAR data from Google Earth Engine"""
        try:
            print("RADAR: Loading EDGAR emissions...")
            
            # EDGAR is more complex, may need specific collection access
            print("WARNING: EDGAR GEE access requires specific permissions")
            return pd.DataFrame()
            
        except Exception as e:
            print(f"ERROR: Error loading EDGAR data: {e}")
            return pd.DataFrame()
    
    def get_all_available_data(self) -> Dict[str, pd.DataFrame]:
        """Get all available real data sources"""
        print("\nSEARCH: Loading All Available Real Data Sources")
        print("=" * 50)
        
        all_data = {}
        
        # Load IPCC data (always available locally)
        ipcc_data = self.load_ipcc_2022_data()
        if len(ipcc_data) > 0:
            all_data['IPCC_2022'] = ipcc_data
        
        # Load GEE data if available
        gee_data = self.load_gee_data()
        all_data.update(gee_data)
        
        # Print summary
        print(f"\nCLIPBOARD: Data Loading Summary:")
        print(f"   Available datasets: {len(all_data)}")
        for name, data in all_data.items():
            print(f"   {name}: {len(data)} records")
        
        if len(all_data) == 0:
            print("ERROR: No real data sources available")
            print("   Please check data files and GEE authentication")
        
        return all_data
    
    def validate_data_availability(self) -> Dict[str, bool]:
        """Validate what data sources are available"""
        status = {}
        
        # Check IPCC data
        csv_path = Path(self.config['paths']['ipcc_2022_data']) / "ipcc_ghg_emissions_2022_csv.csv"
        xlsx_path = Path(self.config['paths']['ipcc_2022_data']) / "ipcc_ghg_emissions_2022.xlsx"
        status['IPCC_2022'] = csv_path.exists() or xlsx_path.exists()
        
        # Check GEE availability
        status['Google_Earth_Engine'] = self.gee_initialized
        
        return status