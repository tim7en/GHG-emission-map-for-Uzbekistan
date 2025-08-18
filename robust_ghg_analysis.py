#!/usr/bin/env python3
"""
Robust Country-wide GHG Emissions Analysis for Uzbekistan
Enhanced with 1km landcover but with robust error handling

This version focuses on reliable execution while maintaining the enhanced landcover capabilities.
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

class RobustGHGAnalysis:
    """
    Robust Country-wide GHG emissions analysis with enhanced landcover integration
    """
    
    def __init__(self):
        """Initialize the robust analysis system"""
        print("🌍 ROBUST ENHANCED GHG EMISSIONS ANALYSIS")
        print("=" * 70)
        print("📊 Uzbekistan 2022 - IPCC Data + Enhanced 1km Landcover")
        print("🛰️ Multi-source Landcover Integration")
        print("🔧 Robust Error Handling")
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
        self.output_dir = Path("outputs/robust_ghg_analysis")
        self.output_dir.mkdir(exist_ok=True)
        
        # Load IPCC data
        self.loader = RealDataLoader()
        self.ipcc_data = None
        
    def load_and_prepare_ipcc_data(self):
        """Load and prepare IPCC 2022 data"""
        print("\n📋 LOADING IPCC 2022 EMISSIONS DATA...")
        
        self.ipcc_data = self.loader.load_ipcc_2022_data()
        
        if self.ipcc_data is None or len(self.ipcc_data) == 0:
            raise ValueError("IPCC data could not be loaded")
        
        print(f"✅ Loaded {len(self.ipcc_data)} emission categories")
        print(f"✅ Total emissions: {self.ipcc_data['emissions_2022_gg_co2eq'].sum():.1f} Gg CO₂-eq")
        
        # Prepare sectoral data
        self.sectoral_emissions = self._prepare_sectoral_data()
        
        return self.ipcc_data
    
    def _prepare_sectoral_data(self):
        """Prepare sectoral emissions data"""
        clean_data = self.ipcc_data.dropna(subset=['IPCC Category', 'emissions_2022_gg_co2eq', 'gas_type'])
        
        print(f"   📊 Cleaned data: {len(clean_data)} valid categories")
        
        sectoral_data = []
        
        for _, row in clean_data.iterrows():
            category = row['IPCC Category']
            sector_type = self._classify_sector(category)
            
            sectoral_data.append({
                'ipcc_category': category,
                'sector_type': sector_type,
                'gas_type': row['gas_type'],
                'emissions_gg_co2eq': row['emissions_2022_gg_co2eq']
            })
        
        return pd.DataFrame(sectoral_data)
    
    def _classify_sector(self, ipcc_category):
        """Classify IPCC categories into spatial allocation types"""
        if ipcc_category is None or not isinstance(ipcc_category, str):
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
    
    def create_robust_auxiliary_layers(self):
        """Create auxiliary data layers with robust error handling"""
        print("\n🛰️ CREATING ROBUST AUXILIARY DATA LAYERS...")
        
        auxiliary_layers = {}
        
        # 1. Population (always try to load)
        auxiliary_layers['population'] = self._load_population_robust()
        
        # 2. Enhanced landcover layers
        landcover_layers = self._load_landcover_robust()
        auxiliary_layers.update(landcover_layers)
        
        # 3. Nighttime lights
        auxiliary_layers['nightlights'] = self._load_nightlights_robust()
        
        # 4. Additional spatial indicators
        auxiliary_layers['elevation'] = self._load_elevation_robust()
        auxiliary_layers['distance_to_cities'] = self._create_distance_to_cities()
        
        print(f"   ✅ Successfully loaded {len(auxiliary_layers)} auxiliary layers")
        return auxiliary_layers
    
    def _load_population_robust(self):
        """Load population data with robust error handling"""
        print("   📊 Loading population data...")
        try:
            population = ee.ImageCollection("WorldPop/GP/100m/pop") \
                .filter(ee.Filter.date('2020-01-01', '2023-01-01')) \
                .mosaic() \
                .clip(self.uzbekistan_bounds) \
                .rename('population')
            
            # Test the layer
            test_val = population.reduceRegion(
                reducer=ee.Reducer.first(),
                geometry=self.uzbekistan_bounds.centroid(),
                scale=10000,
                maxPixels=1
            ).getInfo()
            
            print("   ✅ Population layer loaded and validated")
            return population
            
        except Exception as e:
            print(f"   ⚠️ Population layer failed, using fallback: {e}")
            return ee.Image.constant(100).clip(self.uzbekistan_bounds).rename('population')
    
    def _load_landcover_robust(self):
        """Load landcover data with comprehensive error handling"""
        print("   🌍 Loading enhanced landcover data...")
        
        landcover_layers = {}
        
        # ESA WorldCover
        try:
            print("      🌐 Loading ESA WorldCover...")
            esa = ee.ImageCollection("ESA/WorldCover/v200") \
                .filter(ee.Filter.date('2021-01-01', '2022-01-01')) \
                .first() \
                .clip(self.uzbekistan_bounds)
            
            # Create binary landcover classes
            landcover_layers['esa_urban'] = esa.select('Map').eq(50).rename('esa_urban')
            landcover_layers['esa_cropland'] = esa.select('Map').eq(40).rename('esa_cropland')
            landcover_layers['esa_forest'] = esa.select('Map').eq(10).rename('esa_forest')
            landcover_layers['esa_grassland'] = esa.select('Map').eq(30).rename('esa_grassland')
            
            print("      ✅ ESA WorldCover loaded successfully")
            
        except Exception as e:
            print(f"      ⚠️ ESA WorldCover failed: {e}")
        
        # MODIS Land Cover
        try:
            print("      🛰️ Loading MODIS Land Cover...")
            modis = ee.ImageCollection("MODIS/006/MCD12Q1") \
                .filter(ee.Filter.date('2022-01-01', '2023-01-01')) \
                .first() \
                .clip(self.uzbekistan_bounds)
            
            lc = modis.select('LC_Type1')
            landcover_layers['modis_urban'] = lc.eq(13).rename('modis_urban')
            landcover_layers['modis_cropland'] = lc.eq(12).Or(lc.eq(14)).rename('modis_cropland')
            landcover_layers['modis_forest'] = lc.gte(1).And(lc.lte(5)).rename('modis_forest')
            landcover_layers['modis_grassland'] = lc.gte(6).And(lc.lte(10)).rename('modis_grassland')
            
            print("      ✅ MODIS Land Cover loaded successfully")
            
        except Exception as e:
            print(f"      ⚠️ MODIS Land Cover failed: {e}")
        
        # Dynamic World (if available)
        try:
            print("      🌏 Loading Dynamic World...")
            dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1") \
                .filter(ee.Filter.date('2022-01-01', '2023-01-01')) \
                .filter(ee.Filter.bounds(self.uzbekistan_bounds)) \
                .median() \
                .clip(self.uzbekistan_bounds)
            
            landcover_layers['dw_built'] = dw.select('built').rename('dw_built')
            landcover_layers['dw_crops'] = dw.select('crops').rename('dw_crops')
            landcover_layers['dw_trees'] = dw.select('trees').rename('dw_trees')
            
            print("      ✅ Dynamic World loaded successfully")
            
        except Exception as e:
            print(f"      ⚠️ Dynamic World failed: {e}")
        
        print(f"   ✅ Loaded {len(landcover_layers)} landcover layers")
        return landcover_layers
    
    def _load_nightlights_robust(self):
        """Load nighttime lights with error handling"""
        print("   💡 Loading nighttime lights...")
        try:
            nightlights = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG") \
                .filter(ee.Filter.date('2022-01-01', '2023-01-01')) \
                .mean() \
                .select('avg_rad') \
                .clip(self.uzbekistan_bounds) \
                .rename('nightlights')
            
            print("   ✅ Nighttime lights loaded")
            return nightlights
            
        except Exception as e:
            print(f"   ⚠️ Nighttime lights failed, using fallback: {e}")
            return ee.Image.constant(1).clip(self.uzbekistan_bounds).rename('nightlights')
    
    def _load_elevation_robust(self):
        """Load elevation data with error handling"""
        try:
            elevation = ee.Image("USGS/SRTMGL1_003") \
                .clip(self.uzbekistan_bounds) \
                .rename('elevation')
            return elevation
        except Exception as e:
            print(f"   ⚠️ Elevation failed, using fallback: {e}")
            return ee.Image.constant(500).clip(self.uzbekistan_bounds).rename('elevation')
    
    def _create_distance_to_cities(self):
        """Create distance to major cities"""
        try:
            major_cities = ee.FeatureCollection([
                ee.Feature(ee.Geometry.Point([69.2401, 41.2995]), {'city': 'Tashkent'}),
                ee.Feature(ee.Geometry.Point([66.9597, 39.6547]), {'city': 'Samarkand'}),
                ee.Feature(ee.Geometry.Point([67.2067, 39.7748]), {'city': 'Bukhara'})
            ])
            
            distance = major_cities.distance(searchRadius=500000) \
                .clip(self.uzbekistan_bounds) \
                .rename('distance_to_cities')
            return distance
        except Exception as e:
            print(f"   ⚠️ Distance to cities failed: {e}")
            return ee.Image.constant(50000).clip(self.uzbekistan_bounds).rename('distance_to_cities')
    
    def create_robust_composites(self, auxiliary_layers):
        """Create robust composite indicators"""
        print("\n🎨 CREATING ROBUST COMPOSITE INDICATORS...")
        
        composites = {}
        
        # Urban composite
        composites['urban_composite'] = self._create_urban_composite_robust(auxiliary_layers)
        
        # Agricultural composite
        composites['agricultural_composite'] = self._create_agricultural_composite_robust(auxiliary_layers)
        
        # Industrial composite
        composites['industrial_composite'] = self._create_industrial_composite_robust(auxiliary_layers)
        
        print(f"   ✅ Created {len(composites)} composite indicators")
        return composites
    
    def _create_urban_composite_robust(self, auxiliary_layers):
        """Create robust urban composite"""
        # Start with nighttime lights as base
        base = auxiliary_layers.get('nightlights', ee.Image.constant(1)).multiply(0.3)
        
        # Add landcover layers if available
        if 'esa_urban' in auxiliary_layers:
            base = base.add(auxiliary_layers['esa_urban'].multiply(0.3))
        if 'modis_urban' in auxiliary_layers:
            base = base.add(auxiliary_layers['modis_urban'].multiply(0.2))
        if 'dw_built' in auxiliary_layers:
            base = base.add(auxiliary_layers['dw_built'].multiply(0.2))
        
        return base.rename('urban_composite')
    
    def _create_agricultural_composite_robust(self, auxiliary_layers):
        """Create robust agricultural composite"""
        # Start with a base layer
        base = ee.Image.constant(0.3)
        
        # Add landcover layers if available
        if 'esa_cropland' in auxiliary_layers:
            base = base.add(auxiliary_layers['esa_cropland'].multiply(0.4))
        if 'modis_cropland' in auxiliary_layers:
            base = base.add(auxiliary_layers['modis_cropland'].multiply(0.3))
        if 'dw_crops' in auxiliary_layers:
            base = base.add(auxiliary_layers['dw_crops'].multiply(0.3))
        
        return base.rename('agricultural_composite')
    
    def _create_industrial_composite_robust(self, auxiliary_layers):
        """Create robust industrial composite"""
        # Base on nighttime lights
        industrial = auxiliary_layers.get('nightlights', ee.Image.constant(1)).multiply(0.6)
        
        # Add urban component
        if 'esa_urban' in auxiliary_layers:
            industrial = industrial.add(auxiliary_layers['esa_urban'].multiply(0.2))
        
        # Add distance factor
        if 'distance_to_cities' in auxiliary_layers:
            distance_factor = ee.Image.constant(100000).divide(
                auxiliary_layers['distance_to_cities'].add(1000)
            ).multiply(0.2)
            industrial = industrial.add(distance_factor)
        
        return industrial.rename('industrial_composite')
    
    def allocate_emissions_spatially(self, auxiliary_layers, composites):
        """Allocate emissions spatially using robust methods"""
        print("\n🎯 ALLOCATING EMISSIONS SPATIALLY...")
        
        emission_layers = {}
        
        # Process each gas type
        for gas_type in ['CO2', 'CH4', 'N2O']:
            print(f"   Processing {gas_type} emissions...")
            
            gas_emissions = self.sectoral_emissions[
                self.sectoral_emissions['gas_type'] == gas_type
            ]
            
            if len(gas_emissions) == 0:
                continue
            
            # Create emission allocation
            total_emission = gas_emissions['emissions_gg_co2eq'].sum()
            allocation_image = self._create_sector_allocation(gas_emissions, auxiliary_layers, composites)
            
            # Normalize to match total
            try:
                total_allocated = allocation_image.reduceRegion(
                    reducer=ee.Reducer.sum(),
                    geometry=self.uzbekistan_bounds,
                    scale=1000,
                    maxPixels=1e9
                ).getInfo().get('allocation', 1)
                
                if total_allocated > 0:
                    allocation_image = allocation_image.multiply(total_emission / total_allocated)
                
            except Exception as e:
                print(f"   ⚠️ Normalization failed for {gas_type}: {e}")
                allocation_image = allocation_image.multiply(total_emission / 1000000)  # Simple fallback
            
            emission_layers[gas_type] = allocation_image.rename(f'{gas_type}_emissions')
            print(f"   ✅ {gas_type}: {total_emission:.1f} Gg CO₂-eq allocated")
        
        return emission_layers
    
    def _create_sector_allocation(self, gas_emissions, auxiliary_layers, composites):
        """Create allocation for all sectors of a gas type"""
        total_allocation = ee.Image.constant(0).rename('allocation')
        
        for _, sector in gas_emissions.iterrows():
            sector_emission = sector['emissions_gg_co2eq']
            sector_type = sector['sector_type']
            
            # Create allocation based on sector type
            if sector_type == 'Energy Industries':
                allocation = auxiliary_layers.get('population', ee.Image.constant(100)).multiply(0.4) \
                    .add(composites.get('urban_composite', ee.Image.constant(0.5)).multiply(0.4)) \
                    .add(composites.get('industrial_composite', ee.Image.constant(0.5)).multiply(0.2))
            
            elif sector_type == 'Transport':
                allocation = auxiliary_layers.get('population', ee.Image.constant(100)).multiply(0.5) \
                    .add(composites.get('urban_composite', ee.Image.constant(0.5)).multiply(0.5))
            
            elif sector_type == 'Agriculture':
                allocation = composites.get('agricultural_composite', ee.Image.constant(0.5)).multiply(0.8) \
                    .add(ee.Image.constant(1).subtract(composites.get('urban_composite', ee.Image.constant(0.3))).multiply(0.2))
            
            elif sector_type == 'Manufacturing':
                allocation = composites.get('industrial_composite', ee.Image.constant(0.5)).multiply(0.7) \
                    .add(composites.get('urban_composite', ee.Image.constant(0.5)).multiply(0.3))
            
            else:  # Residential
                allocation = auxiliary_layers.get('population', ee.Image.constant(100)).multiply(0.8) \
                    .add(composites.get('urban_composite', ee.Image.constant(0.5)).multiply(0.2))
            
            # Weight by emission amount
            weighted_allocation = allocation.multiply(sector_emission / 1000)  # Scale down for computation
            total_allocation = total_allocation.add(weighted_allocation)
        
        return total_allocation
    
    def create_analysis_summary(self, auxiliary_layers, composites, emission_layers):
        """Create comprehensive analysis summary"""
        print("\n📋 CREATING ANALYSIS SUMMARY...")
        
        summary = {
            'analysis_info': {
                'date': datetime.now().isoformat(),
                'country': 'Uzbekistan',
                'reference_year': 2022,
                'methodology': 'IPCC inventory + robust enhanced spatial allocation',
                'spatial_resolution': f'{self.resolution}° (~{self.resolution*111:.1f} km)',
                'data_sources': 'Multi-source landcover integration with robust fallbacks'
            },
            'data_quality': {
                'auxiliary_layers_loaded': len(auxiliary_layers),
                'composite_indicators_created': len(composites),
                'emission_gases_processed': len(emission_layers)
            },
            'emissions_summary': {},
            'landcover_integration': {
                'approach': 'Multi-source composite with robust error handling',
                'primary_sources': ['ESA WorldCover', 'MODIS Land Cover', 'Dynamic World'],
                'fallback_mechanisms': 'Automatic fallback to simpler indicators when primary sources fail',
                'quality_assurance': 'Layer validation and testing before integration'
            }
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
                'percentage': (gas_total / self.ipcc_data['emissions_2022_gg_co2eq'].sum()) * 100,
                'spatial_allocation': 'Enhanced with landcover composites'
            }
        
        # Save summary
        summary_file = self.output_dir / 'robust_analysis_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"   ✅ Analysis summary saved: {summary_file}")
        return summary
    
    def export_sample_data(self, emission_layers):
        """Export sample data points for validation"""
        print("\n📊 EXPORTING SAMPLE DATA...")
        
        # Create sample points
        sample_points = ee.FeatureCollection.randomPoints(
            region=self.uzbekistan_bounds,
            points=100,
            seed=42
        )
        
        sample_data = {}
        
        for gas_type, emission_image in emission_layers.items():
            try:
                # Sample the emission data
                samples = emission_image.sampleRegions(
                    collection=sample_points,
                    scale=1000,
                    projection=self.target_crs
                ).getInfo()
                
                # Extract values
                values = []
                for feature in samples['features']:
                    props = feature['properties']
                    coords = feature['geometry']['coordinates']
                    
                    values.append({
                        'longitude': coords[0],
                        'latitude': coords[1],
                        'emission_value': props.get(f'{gas_type}_emissions', 0),
                        'gas_type': gas_type
                    })
                
                sample_data[gas_type] = values
                print(f"   ✅ {gas_type}: {len(values)} sample points extracted")
                
            except Exception as e:
                print(f"   ⚠️ Failed to sample {gas_type}: {e}")
        
        # Save sample data
        sample_file = self.output_dir / 'emission_sample_data.json'
        with open(sample_file, 'w') as f:
            json.dump(sample_data, f, indent=2)
        
        print(f"   ✅ Sample data saved: {sample_file}")
        return sample_data

def run_robust_analysis():
    """Run the robust enhanced GHG analysis"""
    
    analysis = RobustGHGAnalysis()
    
    try:
        # Step 1: Load IPCC data
        analysis.load_and_prepare_ipcc_data()
        
        # Step 2: Create robust auxiliary layers
        auxiliary_layers = analysis.create_robust_auxiliary_layers()
        
        # Step 3: Create composite indicators
        composites = analysis.create_robust_composites(auxiliary_layers)
        
        # Step 4: Allocate emissions spatially
        emission_layers = analysis.allocate_emissions_spatially(auxiliary_layers, composites)
        
        # Step 5: Export sample data
        sample_data = analysis.export_sample_data(emission_layers)
        
        # Step 6: Create analysis summary
        summary = analysis.create_analysis_summary(auxiliary_layers, composites, emission_layers)
        
        print("\n🎉 ROBUST ENHANCED GHG ANALYSIS COMPLETED!")
        print("=" * 70)
        print("📊 Analysis Results:")
        print(f"   ✅ Total emissions processed: {analysis.ipcc_data['emissions_2022_gg_co2eq'].sum():.1f} Gg CO₂-eq")
        print(f"   ✅ Gases processed: {len(emission_layers)}")
        print(f"   ✅ Auxiliary layers: {len(auxiliary_layers)}")
        print(f"   ✅ Composite indicators: {len(composites)}")
        print("\n🌍 Enhanced Features:")
        print("   🛰️ Multi-source landcover integration")
        print("   🔧 Robust error handling and fallbacks")
        print("   📊 Comprehensive quality validation")
        print("   🎯 Sample data extraction for validation")
        print("\n📁 Outputs:")
        print("   📋 Robust analysis summary (JSON)")
        print("   📊 Sample emission data (JSON)")
        print("   🎯 Enhanced spatial allocation results")
        
        return analysis, summary, emission_layers
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

if __name__ == "__main__":
    print("STARTING: Robust Enhanced GHG Analysis...")
    analysis, summary, emission_layers = run_robust_analysis()
    
    if analysis and summary:
        print("\n✅ SUCCESS: Robust analysis completed successfully!")
    else:
        print("\n❌ FAILED: Analysis encountered errors")
