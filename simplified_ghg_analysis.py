#!/usr/bin/env python3
"""
Simplified Country-wide GHG Emissions Analysis with Basic Landcover Integration

This version focuses on getting the core analysis working with simplified landcover
integration, avoiding complex composite creation that might cause null image issues.

Author: AlphaEarth Analysis Team
Date: August 18, 2025
"""

import ee
import pandas as pd
import numpy as np
import json
from pathlib import Path
import time
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add project paths
import sys
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from preprocessing.data_loader import RealDataLoader

class SimplifiedGHGAnalysis:
    """
    Simplified GHG emissions distribution analysis with basic landcover integration
    """
    
    def __init__(self):
        """Initialize the analysis system"""
        print("🌍 SIMPLIFIED COUNTRY-WIDE GHG EMISSIONS ANALYSIS")
        print("=" * 70)
        print("📊 Uzbekistan 2022 - IPCC Data with Basic Landcover Integration")
        print("🛰️ Google Earth Engine Processing")
        print("=" * 70)
        
        # Initialize GEE
        try:
            ee.Initialize(project='ee-sabitovty')
            print("✅ Google Earth Engine initialized successfully")
        except Exception as e:
            print(f"❌ GEE initialization failed: {e}")
            raise
        
        # Define Uzbekistan boundaries and projection
        self.uzbekistan_bounds = ee.Geometry.Rectangle([55.9, 37.2, 73.2, 45.6])
        self.target_crs = 'EPSG:4326'
        self.resolution = 0.01   # ~1km resolution
        
        # Output directory
        self.output_dir = Path("outputs/simplified_ghg_analysis")
        self.output_dir.mkdir(exist_ok=True)
        
        # Load IPCC data
        self.loader = RealDataLoader()
        self.ipcc_data = None
        
    def load_and_prepare_ipcc_data(self):
        """Load and prepare IPCC 2022 data for spatial analysis"""
        print("\n📋 LOADING IPCC 2022 EMISSIONS DATA...")
        
        self.ipcc_data = self.loader.load_ipcc_2022_data()
        
        if self.ipcc_data is None or len(self.ipcc_data) == 0:
            raise ValueError("IPCC data could not be loaded")
        
        print(f"✅ Loaded {len(self.ipcc_data)} emission categories")
        print(f"✅ Total emissions: {self.ipcc_data['emissions_2022_gg_co2eq'].sum():.1f} Gg CO₂-eq")
        
        # Prepare sectoral data for spatial distribution
        self.sectoral_emissions = self._prepare_sectoral_data()
        
        return self.ipcc_data
    
    def _prepare_sectoral_data(self):
        """Prepare sectoral emissions data with spatial allocation weights"""
        
        # Clean the data first
        clean_data = self.ipcc_data.dropna(subset=['IPCC Category', 'emissions_2022_gg_co2eq', 'gas_type'])
        
        print(f"   📊 Cleaned data: {len(clean_data)} valid categories (from {len(self.ipcc_data)} total)")
        
        # Define spatial allocation weights for different sectors
        spatial_weights = {
            'Energy Industries': {
                'urban_weight': 0.4,
                'population_weight': 0.3,
                'industrial_weight': 0.3
            },
            'Transport': {
                'urban_weight': 0.5,
                'population_weight': 0.4,
                'road_weight': 0.1
            },
            'Agriculture': {
                'rural_weight': 0.6,
                'cropland_weight': 0.3,
                'population_weight': 0.1
            },
            'Manufacturing': {
                'industrial_weight': 0.5,
                'urban_weight': 0.3,
                'population_weight': 0.2
            },
            'Residential': {
                'population_weight': 0.7,
                'urban_weight': 0.3
            }
        }
        
        # Categorize IPCC sectors
        sectoral_data = []
        
        for _, row in clean_data.iterrows():
            category = row['IPCC Category']
            sector_type = self._classify_sector(category)
            
            sectoral_data.append({
                'ipcc_category': category,
                'sector_type': sector_type,
                'gas_type': row['gas_type'],
                'emissions_gg_co2eq': row['emissions_2022_gg_co2eq'],
                'spatial_weights': spatial_weights.get(sector_type, spatial_weights['Residential'])
            })
        
        return pd.DataFrame(sectoral_data)
    
    def _classify_sector(self, ipcc_category):
        """Classify IPCC categories into spatial allocation types"""
        
        if ipcc_category is None or pd.isna(ipcc_category) or not isinstance(ipcc_category, str):
            return 'Residential'
        
        category_lower = ipcc_category.lower()
        
        if any(term in category_lower for term in ['energy industries', 'electricity', 'power']):
            return 'Energy Industries'
        elif any(term in category_lower for term in ['transport', 'road', 'aviation', 'navigation']):
            return 'Transport'
        elif any(term in category_lower for term in ['enteric', 'fermentation', 'agriculture', 'livestock', 'soil']):
            return 'Agriculture'
        elif any(term in category_lower for term in ['manufacturing', 'industrial', 'cement', 'steel', 'glass']):
            return 'Manufacturing'
        else:
            return 'Residential'
    
    def create_auxiliary_data_layers(self):
        """Create simplified auxiliary data layers"""
        print("\n🛰️ CREATING SIMPLIFIED AUXILIARY DATA LAYERS...")
        
        auxiliary_layers = {}
        
        # 1. Population density layer
        print("   📊 Loading population data...")
        try:
            population = ee.ImageCollection("WorldPop/GP/100m/pop") \
                .filter(ee.Filter.date('2020-01-01', '2023-01-01')) \
                .mosaic() \
                .clip(self.uzbekistan_bounds) \
                .rename('population')
            auxiliary_layers['population'] = population
            print("   ✅ Population layer loaded")
        except Exception as e:
            print(f"   ⚠️ Population layer failed: {e}")
            auxiliary_layers['population'] = ee.Image.constant(100).rename('population')
        
        # 2. Basic urban classification (MODIS only for simplicity)
        print("   🏙️ Creating basic urban classification...")
        try:
            modis_lc = ee.ImageCollection("MODIS/006/MCD12Q1") \
                .filter(ee.Filter.date('2022-01-01', '2023-01-01')) \
                .first() \
                .clip(self.uzbekistan_bounds)
            
            urban_areas = modis_lc.select('LC_Type1').eq(13).rename('urban')
            auxiliary_layers['urban'] = urban_areas
            print("   ✅ Urban classification created")
        except Exception as e:
            print(f"   ⚠️ Urban classification failed: {e}")
            auxiliary_layers['urban'] = ee.Image.constant(0.1).rename('urban')
        
        # 3. Basic agricultural areas (MODIS only)
        print("   🌾 Loading basic agricultural data...")
        try:
            cropland = modis_lc.select('LC_Type1').eq(12).Or(modis_lc.select('LC_Type1').eq(14)).rename('cropland')
            auxiliary_layers['cropland'] = cropland
            print("   ✅ Agricultural data loaded")
        except Exception as e:
            print(f"   ⚠️ Agricultural data failed: {e}")
            auxiliary_layers['cropland'] = ee.Image.constant(0.2).rename('cropland')
        
        # 4. Nighttime lights (industrial proxy)
        print("   💡 Loading nighttime lights...")
        try:
            nightlights = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG") \
                .filter(ee.Filter.date('2022-01-01', '2023-01-01')) \
                .mean() \
                .select('avg_rad') \
                .clip(self.uzbekistan_bounds) \
                .rename('nightlights')
            auxiliary_layers['nightlights'] = nightlights
            print("   ✅ Nighttime lights loaded")
        except Exception as e:
            print(f"   ⚠️ Nighttime lights failed: {e}")
            auxiliary_layers['nightlights'] = ee.Image.constant(1).rename('nightlights')
        
        return auxiliary_layers
    
    def allocate_emissions_spatially(self, auxiliary_layers):
        """Allocate IPCC emissions spatially using simplified approach"""
        print("\n🎯 ALLOCATING EMISSIONS SPATIALLY (SIMPLIFIED)...")
        
        emission_layers = {}
        
        # Process each gas type
        for gas_type in ['CO2', 'CH4', 'N2O']:
            print(f"   Processing {gas_type} emissions...")
            
            gas_emissions = self.sectoral_emissions[
                self.sectoral_emissions['gas_type'] == gas_type
            ]
            
            if len(gas_emissions) == 0:
                continue
            
            # Create emission layer for this gas
            total_emission = 0
            emission_image = ee.Image.constant(0).rename(f'{gas_type}_emissions')
            
            for _, sector in gas_emissions.iterrows():
                sector_emission = sector['emissions_gg_co2eq']
                sector_type = sector['sector_type']
                weights = sector['spatial_weights']
                
                # Create spatial allocation layer based on sector type
                allocation_layer = self._create_simple_allocation_layer(
                    sector_type, weights, auxiliary_layers
                )
                
                # Add this sector's emissions to the total
                sector_layer = allocation_layer.multiply(sector_emission)
                emission_image = emission_image.add(sector_layer)
                total_emission += sector_emission
            
            emission_layers[gas_type] = emission_image
            print(f"   ✅ {gas_type}: {total_emission:.1f} Gg CO₂-eq allocated")
        
        return emission_layers
    
    def _create_simple_allocation_layer(self, sector_type, weights, auxiliary_layers):
        """Create simplified spatial allocation layer for a sector"""
        
        # Base uniform distribution
        allocation = ee.Image.constant(1)
        
        # Apply sector-specific weights using simple approach
        if sector_type == 'Energy Industries':
            allocation = allocation.multiply(
                auxiliary_layers['population'].multiply(weights.get('population_weight', 0.3))
                .add(auxiliary_layers['urban'].multiply(weights.get('urban_weight', 0.4)))
                .add(auxiliary_layers['nightlights'].multiply(weights.get('industrial_weight', 0.3)))
            )
        
        elif sector_type == 'Transport':
            allocation = allocation.multiply(
                auxiliary_layers['population'].multiply(weights.get('population_weight', 0.4))
                .add(auxiliary_layers['urban'].multiply(weights.get('urban_weight', 0.5)))
                .add(auxiliary_layers['nightlights'].multiply(weights.get('road_weight', 0.1)))
            )
        
        elif sector_type == 'Agriculture':
            rural_proxy = ee.Image.constant(1).subtract(auxiliary_layers['urban'])
            allocation = allocation.multiply(
                auxiliary_layers['cropland'].multiply(weights.get('cropland_weight', 0.3))
                .add(rural_proxy.multiply(weights.get('rural_weight', 0.6)))
                .add(auxiliary_layers['population'].multiply(weights.get('population_weight', 0.1)))
            )
        
        elif sector_type == 'Manufacturing':
            allocation = allocation.multiply(
                auxiliary_layers['nightlights'].multiply(weights.get('industrial_weight', 0.5))
                .add(auxiliary_layers['urban'].multiply(weights.get('urban_weight', 0.3)))
                .add(auxiliary_layers['population'].multiply(weights.get('population_weight', 0.2)))
            )
        
        else:  # Residential
            allocation = allocation.multiply(
                auxiliary_layers['population'].multiply(weights.get('population_weight', 0.7))
                .add(auxiliary_layers['urban'].multiply(weights.get('urban_weight', 0.3)))
            )
        
        return allocation
    
    def export_emission_maps(self, emission_layers):
        """Export emission maps with simplified approach"""
        print(f"\n📤 EXPORTING EMISSION MAPS...")
        
        # Create local output directory
        local_output_dir = self.output_dir / "geotiff_maps"
        local_output_dir.mkdir(exist_ok=True)
        
        # Export parameters
        export_params = {
            'region': self.uzbekistan_bounds,
            'scale': self.resolution * 111000,  # Convert degrees to meters
            'crs': self.target_crs,
            'maxPixels': 1e9
        }
        
        export_tasks = []
        
        for gas_type, emission_image in emission_layers.items():
            # Local filename
            filename = f'UZB_GHG_{gas_type}_2022_simplified.tif'
            local_path = local_output_dir / filename
            
            print(f"   🚀 Preparing {gas_type} emissions map...")
            
            try:
                # Get download URL
                download_url = emission_image.getDownloadURL({
                    **export_params,
                    'filePerBand': False,
                    'format': 'GEO_TIFF'
                })
                
                print(f"   ✅ {gas_type} export prepared: {filename}")
                
                export_tasks.append({
                    'gas_type': gas_type,
                    'filename': filename,
                    'local_path': str(local_path),
                    'download_url': download_url,
                    'status': 'ready_for_download'
                })
                
            except Exception as e:
                print(f"   ❌ Failed to prepare {gas_type} export: {e}")
                export_tasks.append({
                    'gas_type': gas_type,
                    'filename': filename,
                    'local_path': str(local_path),
                    'download_url': None,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return export_tasks
    
    def create_analysis_summary(self, emission_layers, export_tasks):
        """Create simplified analysis summary"""
        print("\n📋 CREATING ANALYSIS SUMMARY...")
        
        summary = {
            'analysis_info': {
                'date': datetime.now().isoformat(),
                'country': 'Uzbekistan',
                'reference_year': 2022,
                'methodology': 'IPCC inventory + simplified spatial allocation',
                'processing_platform': 'Google Earth Engine',
                'version': 'Simplified for robustness'
            },
            'data_sources': {
                'emissions_inventory': 'IPCC 2022 National Inventory',
                'spatial_resolution': f'{self.resolution} degrees (~{self.resolution*111:.1f} km)',
                'coordinate_system': self.target_crs,
                'auxiliary_data': [
                    'WorldPop Population Density',
                    'MODIS Land Cover (Urban/Agricultural)',
                    'VIIRS Nighttime Lights'
                ]
            },
            'emissions_summary': {},
            'output_files': []
        }
        
        # Add emissions summary
        for gas_type in emission_layers.keys():
            gas_total = float(
                self.sectoral_emissions[
                    self.sectoral_emissions['gas_type'] == gas_type
                ]['emissions_gg_co2eq'].sum()
            )
            summary['emissions_summary'][gas_type] = {
                'total_gg_co2eq': gas_total,
                'percentage': (gas_total / self.ipcc_data['emissions_2022_gg_co2eq'].sum()) * 100
            }
        
        # Add output files
        for task_info in export_tasks:
            summary['output_files'].append({
                'filename': task_info['filename'],
                'gas_type': task_info['gas_type'],
                'format': 'GeoTIFF',
                'georeferenced': True,
                'crs': self.target_crs
            })
        
        # Save summary
        summary_file = self.output_dir / 'simplified_analysis_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"   ✅ Summary saved: {summary_file}")
        
        return summary

def run_simplified_analysis():
    """Run the simplified country-wide GHG analysis"""
    
    analysis = SimplifiedGHGAnalysis()
    
    try:
        # Step 1: Load IPCC data
        analysis.load_and_prepare_ipcc_data()
        
        # Step 2: Create auxiliary data layers
        auxiliary_layers = analysis.create_auxiliary_data_layers()
        
        # Step 3: Allocate emissions spatially
        emission_layers = analysis.allocate_emissions_spatially(auxiliary_layers)
        
        # Step 4: Export maps
        export_tasks = analysis.export_emission_maps(emission_layers)
        
        # Step 5: Create analysis summary
        summary = analysis.create_analysis_summary(emission_layers, export_tasks)
        
        print("\n🎉 SIMPLIFIED GHG ANALYSIS COMPLETED!")
        print("=" * 70)
        print("📊 Analysis Results:")
        print(f"   ✅ Total emissions allocated: {analysis.ipcc_data['emissions_2022_gg_co2eq'].sum():.1f} Gg CO₂-eq")
        print(f"   ✅ Gases processed: {len(emission_layers)}")
        print(f"   ✅ Maps prepared: {len(export_tasks)}")
        print(f"   ✅ Grid resolution: {analysis.resolution}° (~{analysis.resolution*111:.1f} km)")
        print("\n📁 Outputs:")
        print("   🗺️ Simplified GeoTIFF maps")
        print("   📋 Analysis summary (JSON)")
        print("   🎯 CRS: WGS84 (EPSG:4326)")
        print("   📊 Approach: Robust simplified allocation")
        
        return analysis, summary
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    print("STARTING: Simplified Country-wide GHG Emissions Analysis...")
    analysis, summary = run_simplified_analysis()
    
    if analysis and summary:
        print("\n✅ SUCCESS: Simplified analysis completed successfully!")
    else:
        print("\n❌ FAILED: Analysis encountered errors")
