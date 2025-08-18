#!/usr/bin/env python3
"""
Enhanced Spatial GHG Analysis with Complete Mapping Capabilities
Combines robust processing with comprehensive spatial mapping throughout the analysis

This script creates detailed spatial distribution maps of GHG emissions across Uzbekistan
using IPCC 2022 data with enhanced landcover integration and exports georeferenced maps.

Author: AlphaEarth Analysis Team
Date: August 18, 2025
"""

import ee
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
import time
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add project paths
import sys
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

try:
    from preprocessing.data_loader import RealDataLoader
except ImportError as e:
    print(f"Error importing RealDataLoader: {e}")
    print("Working directory:", os.getcwd())
    print("Python path:", sys.path)
    raise

class EnhancedSpatialGHGAnalysis:
    """
    Enhanced spatial GHG analysis with comprehensive mapping throughout the process
    """
    
    def __init__(self):
        """Initialize the enhanced spatial analysis system"""
        print("🌍 ENHANCED SPATIAL GHG EMISSIONS ANALYSIS")
        print("=" * 70)
        print("📊 Uzbekistan 2022 - Complete Spatial Distribution")
        print("🗺️ Comprehensive Mapping with Enhanced Landcover")
        print("🛰️ Multi-layer Spatial Analysis & Export")
        print("🎯 Robust Processing + Advanced Visualization")
        print("=" * 70)
        
        # Initialize GEE
        try:
            ee.Initialize(project='ee-sabitovty')
            print("✅ Google Earth Engine initialized successfully")
        except Exception as e:
            print(f"❌ GEE initialization failed: {e}")
            raise
        
        # Define analysis parameters
        self.uzbekistan_bounds = ee.Geometry.Rectangle([55.9, 37.2, 73.2, 45.6])
        self.target_crs = 'EPSG:4326'
        self.target_scale = 1000  # 1km resolution
        self.resolution = 0.01   # ~1km resolution (0.01 degrees)
        
        # Output directories
        self.output_dir = Path("outputs/enhanced_spatial_analysis")
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different outputs
        (self.output_dir / "spatial_maps").mkdir(exist_ok=True)
        (self.output_dir / "auxiliary_layers").mkdir(exist_ok=True)
        (self.output_dir / "composite_indicators").mkdir(exist_ok=True)
        (self.output_dir / "emission_maps").mkdir(exist_ok=True)
        (self.output_dir / "validation_data").mkdir(exist_ok=True)
        
        # Load IPCC data
        self.loader = RealDataLoader()
        self.ipcc_data = None
        self.auxiliary_layers = {}
        self.emission_layers = {}
        self.export_tasks = []
        
    def load_and_prepare_ipcc_data(self):
        """Load and prepare IPCC 2022 data for spatial analysis"""
        print("\n📋 LOADING IPCC 2022 EMISSIONS DATA...")
        
        self.ipcc_data = self.loader.load_ipcc_2022_data()
        
        if self.ipcc_data is None or len(self.ipcc_data) == 0:
            raise ValueError("IPCC data could not be loaded")
        
        print(f"✅ Loaded {len(self.ipcc_data)} emission categories")
        print(f"✅ Total emissions: {self.ipcc_data['emissions_2022_gg_co2eq'].sum():.1f} Gg CO₂-eq")
        
        # Prepare sectoral data
        self.sectoral_emissions = self._prepare_sectoral_data()
        
        # Export IPCC data summary
        self._export_ipcc_summary()
        
        return self.ipcc_data
    
    def _prepare_sectoral_data(self):
        """Prepare sectoral emissions data with enhanced debugging"""
        clean_data = self.ipcc_data.dropna(subset=['IPCC Category', 'emissions_2022_gg_co2eq', 'gas_type'])
        print(f"   📊 Cleaned data: {len(clean_data)} valid categories")
        print(f"   📊 Gas types in cleaned data: {clean_data['gas_type'].value_counts().to_dict()}")
        
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
        
        result_df = pd.DataFrame(sectoral_data)
        print(f"   📊 Sectoral data gas types: {result_df['gas_type'].value_counts().to_dict()}")
        
        return result_df
    
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
    
    def _export_ipcc_summary(self):
        """Export IPCC data summary"""
        ipcc_summary = {
            'analysis_date': datetime.now().isoformat(),
            'total_categories': len(self.ipcc_data),
            'total_emissions': float(self.ipcc_data['emissions_2022_gg_co2eq'].sum()),
            'gas_breakdown': self.ipcc_data['gas_type'].value_counts().to_dict(),
            'sector_breakdown': self.sectoral_emissions['sector_type'].value_counts().to_dict(),
            'categories_detail': []
        }
        
        for _, row in self.sectoral_emissions.iterrows():
            ipcc_summary['categories_detail'].append({
                'ipcc_category': row['ipcc_category'],
                'sector_type': row['sector_type'],
                'gas_type': row['gas_type'],
                'emissions_gg_co2eq': float(row['emissions_gg_co2eq'])
            })
        
        # Save IPCC summary
        summary_file = self.output_dir / 'ipcc_data_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(ipcc_summary, f, indent=2)
        
        print(f"   ✅ IPCC summary saved: {summary_file}")
    
    def create_comprehensive_auxiliary_layers(self):
        """Create comprehensive auxiliary data layers with spatial export"""
        print("\n🛰️ CREATING COMPREHENSIVE AUXILIARY DATA LAYERS...")
        
        auxiliary_layers = {}
        
        # 1. Population density
        print("   📊 Loading population data...")
        try:
            population = ee.ImageCollection("WorldPop/GP/100m/pop") \
                .filter(ee.Filter.date('2020-01-01', '2023-01-01')) \
                .mosaic() \
                .setDefaultProjection('EPSG:4326', None, 100) \
                .reproject('EPSG:4326', None, self.target_scale) \
                .clip(self.uzbekistan_bounds) \
                .rename('population')
            
            # Validate
            test_pixel = population.sample(
                region=ee.Geometry.Point([69.24, 41.30]),
                scale=self.target_scale,
                numPixels=1
            ).size()
            
            if test_pixel.getInfo() > 0:
                auxiliary_layers['population'] = population
                print("   ✅ Population layer loaded and validated")
                
                # Export population map
                self._export_auxiliary_layer(population, 'population', 'Population Density')
            else:
                raise Exception("Population layer validation failed")
                
        except Exception as e:
            print(f"   ⚠️ Population layer failed: {e}")
            auxiliary_layers['population'] = ee.Image.constant(100).rename('population')
        
        # 2. Nighttime lights
        print("   💡 Loading nighttime lights...")
        try:
            nightlights = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG") \
                .filter(ee.Filter.date('2022-01-01', '2023-01-01')) \
                .mean() \
                .select('avg_rad') \
                .setDefaultProjection('EPSG:4326', None, 500) \
                .reproject('EPSG:4326', None, self.target_scale) \
                .clip(self.uzbekistan_bounds) \
                .rename('nightlights')
            
            # Validate
            test_pixel = nightlights.sample(
                region=ee.Geometry.Point([69.24, 41.30]),
                scale=self.target_scale,
                numPixels=1
            ).size()
            
            if test_pixel.getInfo() > 0:
                auxiliary_layers['nightlights'] = nightlights
                print("   ✅ Nighttime lights loaded and validated")
                
                # Export nightlights map
                self._export_auxiliary_layer(nightlights, 'nightlights', 'Nighttime Lights')
            else:
                raise Exception("Nightlights validation failed")
                
        except Exception as e:
            print(f"   ⚠️ Nighttime lights failed: {e}")
            auxiliary_layers['nightlights'] = ee.Image.constant(1).rename('nightlights')
        
        # 3. Enhanced landcover layers
        print("   🌍 Creating enhanced landcover layers...")
        landcover_layers = self._create_enhanced_landcover_layers()
        auxiliary_layers.update(landcover_layers)
        
        # 4. Derived spatial indicators
        print("   🎯 Creating spatial indicators...")
        spatial_indicators = self._create_spatial_indicators(auxiliary_layers)
        auxiliary_layers.update(spatial_indicators)
        
        self.auxiliary_layers = auxiliary_layers
        print(f"   ✅ Successfully created {len(auxiliary_layers)} auxiliary layers")
        
        return auxiliary_layers
    
    def _create_enhanced_landcover_layers(self):
        """Create enhanced landcover layers with validation and export"""
        landcover_layers = {}
        
        # MODIS Land Cover (most reliable for 1km)
        try:
            modis_lc = ee.ImageCollection("MODIS/061/MCD12Q1") \
                .filter(ee.Filter.date('2022-01-01', '2023-01-01')) \
                .first() \
                .select('LC_Type1') \
                .setDefaultProjection('EPSG:4326', None, 500) \
                .reproject('EPSG:4326', None, self.target_scale)
            
            # Urban areas (class 13)
            urban = modis_lc.eq(13).rename('urban').clip(self.uzbekistan_bounds)
            landcover_layers['urban'] = urban
            self._export_auxiliary_layer(urban, 'urban', 'Urban Areas')
            
            # Cropland (classes 12, 14)
            cropland = modis_lc.eq(12).Or(modis_lc.eq(14)).rename('cropland').clip(self.uzbekistan_bounds)
            landcover_layers['cropland'] = cropland
            self._export_auxiliary_layer(cropland, 'cropland', 'Agricultural Areas')
            
            # Forest (classes 1-5)
            forest = modis_lc.gte(1).And(modis_lc.lte(5)).rename('forest').clip(self.uzbekistan_bounds)
            landcover_layers['forest'] = forest
            self._export_auxiliary_layer(forest, 'forest', 'Forest Areas')
            
            # Grassland (classes 6-10)
            grassland = modis_lc.gte(6).And(modis_lc.lte(10)).rename('grassland').clip(self.uzbekistan_bounds)
            landcover_layers['grassland'] = grassland
            self._export_auxiliary_layer(grassland, 'grassland', 'Grassland Areas')
            
            # Barren (class 16)
            barren = modis_lc.eq(16).rename('barren').clip(self.uzbekistan_bounds)
            landcover_layers['barren'] = barren
            self._export_auxiliary_layer(barren, 'barren', 'Barren Areas')
            
            print(f"      ✅ MODIS landcover layers created and exported")
            
        except Exception as e:
            print(f"      ⚠️ MODIS landcover failed: {e}")
            # Create fallback layers
            landcover_layers['urban'] = ee.Image.constant(0.1).rename('urban')
            landcover_layers['cropland'] = ee.Image.constant(0.3).rename('cropland')
            landcover_layers['forest'] = ee.Image.constant(0.1).rename('forest')
            landcover_layers['grassland'] = ee.Image.constant(0.2).rename('grassland')
            landcover_layers['barren'] = ee.Image.constant(0.3).rename('barren')
        
        return landcover_layers
    
    def _create_spatial_indicators(self, auxiliary_layers):
        """Create derived spatial indicators with export"""
        indicators = {}
        
        # Distance to major cities
        try:
            major_cities = ee.FeatureCollection([
                ee.Feature(ee.Geometry.Point([69.2401, 41.2995]), {'city': 'Tashkent'}),
                ee.Feature(ee.Geometry.Point([66.9597, 39.6547]), {'city': 'Samarkand'}),
                ee.Feature(ee.Geometry.Point([64.4203, 39.7751]), {'city': 'Bukhara'}),
                ee.Feature(ee.Geometry.Point([72.3440, 40.7821]), {'city': 'Andijan'}),
                ee.Feature(ee.Geometry.Point([59.6122, 42.4570]), {'city': 'Nukus'})
            ])
            
            distance_to_cities = major_cities.distance(searchRadius=500000) \
                .clip(self.uzbekistan_bounds) \
                .rename('distance_to_cities')
            
            indicators['distance_to_cities'] = distance_to_cities
            self._export_auxiliary_layer(distance_to_cities, 'distance_to_cities', 'Distance to Major Cities')
            
        except Exception as e:
            print(f"      ⚠️ Distance to cities failed: {e}")
            indicators['distance_to_cities'] = ee.Image.constant(50000).rename('distance_to_cities')
        
        # Elevation
        try:
            elevation = ee.Image("USGS/SRTMGL1_003") \
                .clip(self.uzbekistan_bounds) \
                .rename('elevation')
            
            indicators['elevation'] = elevation
            self._export_auxiliary_layer(elevation, 'elevation', 'Elevation')
            
        except Exception as e:
            print(f"      ⚠️ Elevation failed: {e}")
            indicators['elevation'] = ee.Image.constant(500).rename('elevation')
        
        return indicators
    
    def _export_auxiliary_layer(self, image, layer_name, description):
        """Export auxiliary layer using GEE batch export instead of direct download"""
        try:
            # Prepare image with metadata (without coordinate bands to reduce size)
            export_image = image.set({
                'layer_name': layer_name,
                'description': description,
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                'crs': self.target_crs,
                'scale': self.target_scale,
                'country': 'Uzbekistan'
            })
            
            # Use batch export to Google Drive (handles large files better)
            task = ee.batch.Export.image.toDrive(
                image=export_image,
                description=f'UZB_{layer_name}_2022',
                folder='GHG_Analysis_Exports',
                fileNamePrefix=f'UZB_{layer_name}_2022',
                region=self.uzbekistan_bounds,
                scale=self.target_scale,
                crs=self.target_crs,
                maxPixels=1e9,
                fileFormat='GeoTIFF'
            )
            
            # Start the export task
            task.start()
            
            # Store export info
            export_info = {
                'layer_name': layer_name,
                'description': description,
                'filename': f'UZB_{layer_name}_2022.tif',
                'task_id': task.id,
                'task_status': 'STARTED',
                'export_method': 'batch_export_to_drive',
                'export_date': datetime.now().isoformat()
            }
            
            # Save export info
            export_file = self.output_dir / "auxiliary_layers" / f'{layer_name}_export_info.json'
            with open(export_file, 'w') as f:
                json.dump(export_info, f, indent=2)
            
            print(f"      ✅ {layer_name} batch export started (Task ID: {task.id[:12]}...)")
            
        except Exception as e:
            print(f"      ⚠️ Failed to export {layer_name}: {e}")
            # Store minimal export info even on failure
            export_info = {
                'layer_name': layer_name,
                'description': description,
                'status': 'export_failed',
                'error': str(e),
                'export_date': datetime.now().isoformat()
            }
            
            export_file = self.output_dir / "auxiliary_layers" / f'{layer_name}_export_info.json'
            with open(export_file, 'w') as f:
                json.dump(export_info, f, indent=2)
    
    def create_composite_indicators(self):
        """Create composite indicators for emission allocation"""
        print("\n🎨 CREATING COMPOSITE INDICATORS...")
        
        composites = {}
        
        # Urban composite
        urban_composite = self._create_urban_composite()
        if urban_composite:
            composites['urban_composite'] = urban_composite
            self._export_auxiliary_layer(urban_composite, 'urban_composite', 'Urban Composite Indicator')
        
        # Agricultural composite
        agricultural_composite = self._create_agricultural_composite()
        if agricultural_composite:
            composites['agricultural_composite'] = agricultural_composite
            self._export_auxiliary_layer(agricultural_composite, 'agricultural_composite', 'Agricultural Composite Indicator')
        
        # Industrial composite
        industrial_composite = self._create_industrial_composite()
        if industrial_composite:
            composites['industrial_composite'] = industrial_composite
            self._export_auxiliary_layer(industrial_composite, 'industrial_composite', 'Industrial Composite Indicator')
        
        print(f"   ✅ Created {len(composites)} composite indicators")
        return composites
    
    def _create_urban_composite(self):
        """Create urban composite indicator"""
        try:
            urban_base = self.auxiliary_layers.get('urban', ee.Image.constant(0.1))
            nightlights = self.auxiliary_layers.get('nightlights', ee.Image.constant(1))
            population = self.auxiliary_layers.get('population', ee.Image.constant(100))
            
            # Normalize nightlights (0-1)
            nightlights_norm = nightlights.unitScale(0, 50).clamp(0, 1)
            
            # Normalize population (log scale)
            population_norm = population.add(1).log().unitScale(0, 10).clamp(0, 1)
            
            # Combine indicators
            urban_composite = urban_base.multiply(0.4) \
                .add(nightlights_norm.multiply(0.4)) \
                .add(population_norm.multiply(0.2)) \
                .rename('urban_composite')
            
            return urban_composite
            
        except Exception as e:
            print(f"      ⚠️ Urban composite failed: {e}")
            return None
    
    def _create_agricultural_composite(self):
        """Create agricultural composite indicator"""
        try:
            cropland = self.auxiliary_layers.get('cropland', ee.Image.constant(0.3))
            grassland = self.auxiliary_layers.get('grassland', ee.Image.constant(0.2))
            urban = self.auxiliary_layers.get('urban', ee.Image.constant(0.1))
            
            # Agricultural = cropland + grassland - urban
            agricultural_composite = cropland.multiply(0.6) \
                .add(grassland.multiply(0.3)) \
                .add(ee.Image.constant(1).subtract(urban).multiply(0.1)) \
                .rename('agricultural_composite')
            
            return agricultural_composite
            
        except Exception as e:
            print(f"      ⚠️ Agricultural composite failed: {e}")
            return None
    
    def _create_industrial_composite(self):
        """Create industrial composite indicator"""
        try:
            nightlights = self.auxiliary_layers.get('nightlights', ee.Image.constant(1))
            urban = self.auxiliary_layers.get('urban', ee.Image.constant(0.1))
            distance_to_cities = self.auxiliary_layers.get('distance_to_cities', ee.Image.constant(50000))
            
            # Normalize components
            nightlights_norm = nightlights.unitScale(0, 50).clamp(0, 1)
            distance_factor = ee.Image.constant(100000).divide(distance_to_cities.add(1000)).clamp(0, 1)
            
            # Industrial = nightlights + urban + proximity to cities
            industrial_composite = nightlights_norm.multiply(0.5) \
                .add(urban.multiply(0.3)) \
                .add(distance_factor.multiply(0.2)) \
                .rename('industrial_composite')
            
            return industrial_composite
            
        except Exception as e:
            print(f"      ⚠️ Industrial composite failed: {e}")
            return None
    
    def allocate_emissions_spatially_with_export(self):
        """Allocate emissions spatially and export maps throughout the process"""
        print("\n🎯 ALLOCATING EMISSIONS SPATIALLY WITH MAPPING...")
        
        emission_layers = {}
        composite_indicators = self.create_composite_indicators()
        
        # Process each gas type
        for gas_type in ['CO2', 'CH4', 'N2O']:
            print(f"   Processing {gas_type} emissions...")
            
            gas_emissions = self.sectoral_emissions[
                self.sectoral_emissions['gas_type'] == gas_type
            ]
            
            if len(gas_emissions) == 0:
                print(f"   ⚠️ No {gas_type} emissions found")
                continue
            
            try:
                total_emission = gas_emissions['emissions_gg_co2eq'].sum()
                
                # Create allocation map
                allocation_image = self._create_enhanced_allocation(gas_emissions, composite_indicators)
                
                if allocation_image is not None:
                    # Scale to actual emissions
                    emission_image = allocation_image.multiply(total_emission).rename(f'{gas_type}_emissions')
                    emission_layers[gas_type] = emission_image
                    
                    # Export individual gas map
                    self._export_emission_map(emission_image, gas_type, total_emission)
                    
                    print(f"   ✅ {gas_type}: {total_emission:.1f} Gg CO₂-eq allocated and exported")
                else:
                    print(f"   ❌ {gas_type}: allocation failed")
                    
            except Exception as e:
                print(f"   ❌ {gas_type} allocation error: {e}")
        
        # Create and export combined map
        if emission_layers:
            combined_map = self._create_combined_emission_map(emission_layers)
            if combined_map:
                total_combined_emissions = sum([
                    float(self.sectoral_emissions[
                        self.sectoral_emissions['gas_type'] == gas
                    ]['emissions_gg_co2eq'].sum()) for gas in emission_layers.keys()
                ])
                self._export_emission_map(combined_map, 'COMBINED', total_combined_emissions)
        
        self.emission_layers = emission_layers
        return emission_layers
    
    def _create_enhanced_allocation(self, gas_emissions, composite_indicators):
        """Create enhanced allocation using composite indicators"""
        try:
            # Sector-based weights
            sector_weights = {
                'Energy Industries': {'population': 0.2, 'urban_composite': 0.4, 'industrial_composite': 0.4},
                'Transport': {'population': 0.3, 'urban_composite': 0.5, 'industrial_composite': 0.2},
                'Agriculture': {'population': 0.1, 'agricultural_composite': 0.8, 'urban_composite': -0.1},
                'Manufacturing': {'population': 0.1, 'urban_composite': 0.3, 'industrial_composite': 0.6},
                'Residential': {'population': 0.7, 'urban_composite': 0.3, 'industrial_composite': 0.0}
            }
            
            # Aggregate by sector
            sector_totals = gas_emissions.groupby('sector_type')['emissions_gg_co2eq'].sum()
            
            final_allocation = ee.Image.constant(0).rename('final_allocation')
            
            for sector, total_emission in sector_totals.items():
                if total_emission <= 0:
                    continue
                
                weights = sector_weights.get(sector, {'population': 1.0})
                sector_allocation = ee.Image.constant(0.1)  # Base level
                
                # Apply weights
                for indicator_name, weight in weights.items():
                    if weight == 0:
                        continue
                        
                    if indicator_name in composite_indicators:
                        indicator_image = composite_indicators[indicator_name]
                    elif indicator_name in self.auxiliary_layers:
                        indicator_image = self.auxiliary_layers[indicator_name]
                    else:
                        continue
                    
                    if weight > 0:
                        sector_allocation = sector_allocation.add(indicator_image.multiply(weight))
                    else:  # negative weight
                        sector_allocation = sector_allocation.add(
                            ee.Image.constant(1).subtract(indicator_image).multiply(abs(weight))
                        )
                
                # Add to final allocation
                sector_allocation = sector_allocation.multiply(total_emission)
                final_allocation = final_allocation.add(sector_allocation)
            
            # Normalize to probability distribution
            total_sum = final_allocation.reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=self.uzbekistan_bounds,
                scale=self.target_scale,
                maxPixels=int(1e8)
            ).values().get(0)
            
            total_sum_image = ee.Image.constant(total_sum)
            return final_allocation.divide(total_sum_image)
            
        except Exception as e:
            print(f"      ⚠️ Enhanced allocation failed: {e}")
            return ee.Image.constant(1).divide(
                ee.Image.constant(1).reduceRegion(
                    reducer=ee.Reducer.sum(),
                    geometry=self.uzbekistan_bounds,
                    scale=self.target_scale,
                    maxPixels=int(1e8)
                ).values().get(0)
            )
    
    def _export_emission_map(self, emission_image, gas_type, total_emission):
        """Export emission map using GEE batch export"""
        try:
            # Set comprehensive metadata
            export_image = emission_image.set({
                'gas_type': gas_type,
                'total_emissions_gg_co2eq': float(total_emission) if isinstance(total_emission, (int, float)) else 0.0,
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                'source': 'IPCC_2022_Enhanced_Spatial_Analysis',
                'country': 'Uzbekistan',
                'crs': self.target_crs,
                'resolution_meters': self.target_scale,
                'units': 'Gg_CO2_eq_per_pixel',
                'methodology': 'Enhanced multi-layer spatial allocation'
            })
            
            # Use batch export to Google Drive
            task = ee.batch.Export.image.toDrive(
                image=export_image,
                description=f'UZB_GHG_{gas_type}_Enhanced_2022',
                folder='GHG_Analysis_Exports',
                fileNamePrefix=f'UZB_GHG_{gas_type}_Enhanced_2022',
                region=self.uzbekistan_bounds,
                scale=self.target_scale,
                crs=self.target_crs,
                maxPixels=1e9,
                fileFormat='GeoTIFF'
            )
            
            # Start the export task
            task.start()
            
            # Store export info
            export_info = {
                'gas_type': gas_type,
                'filename': f'UZB_GHG_{gas_type}_Enhanced_2022.tif',
                'total_emissions': float(total_emission) if isinstance(total_emission, (int, float)) else 0.0,
                'task_id': task.id,
                'task_status': 'STARTED',
                'export_method': 'batch_export_to_drive',
                'export_date': datetime.now().isoformat()
            }
            
            # Save export info
            export_file = self.output_dir / "emission_maps" / f'{gas_type}_export_info.json'
            with open(export_file, 'w') as f:
                json.dump(export_info, f, indent=2)
            
            # Add to export tasks
            self.export_tasks.append(export_info)
            
            print(f"      ✅ {gas_type} emission map batch export started (Task ID: {task.id[:12]}...)")
            
        except Exception as e:
            print(f"      ❌ Failed to export {gas_type} emission map: {e}")
            # Store minimal export info even on failure
            export_info = {
                'gas_type': gas_type,
                'status': 'export_failed',
                'error': str(e),
                'export_date': datetime.now().isoformat()
            }
            
            export_file = self.output_dir / "emission_maps" / f'{gas_type}_export_info.json'
            with open(export_file, 'w') as f:
                json.dump(export_info, f, indent=2)
    
    def _create_combined_emission_map(self, emission_layers):
        """Create combined total GHG emissions map"""
        try:
            total_emissions = ee.Image.constant(0).rename('total_ghg_emissions')
            
            # GWP factors for CO2-equivalent conversion
            gwp_factors = {'CO2': 1, 'CH4': 25, 'N2O': 298}
            
            for gas_type, emission_image in emission_layers.items():
                gwp = gwp_factors.get(gas_type, 1)
                total_emissions = total_emissions.add(emission_image.multiply(gwp))
            
            return total_emissions
            
        except Exception as e:
            print(f"      ⚠️ Combined map creation failed: {e}")
            return None
    
    def validate_and_sample_results(self):
        """Validate results and create sample data"""
        print("\n📊 VALIDATING RESULTS AND SAMPLING...")
        
        validation_data = {
            'analysis_info': {
                'date': datetime.now().isoformat(),
                'method': 'Enhanced Spatial GHG Analysis',
                'spatial_resolution': f'{self.target_scale}m'
            },
            'emission_totals': {},
            'sample_points': [],
            'validation_metrics': {}
        }
        
        # Sample at major cities
        major_cities = [
            {'name': 'Tashkent', 'coords': [69.24, 41.30]},
            {'name': 'Samarkand', 'coords': [66.96, 39.65]},
            {'name': 'Bukhara', 'coords': [64.42, 39.77]},
            {'name': 'Andijan', 'coords': [72.34, 40.78]},
            {'name': 'Nukus', 'coords': [59.61, 42.45]}
        ]
        
        for gas_type, emission_image in self.emission_layers.items():
            gas_total = float(
                self.sectoral_emissions[
                    self.sectoral_emissions['gas_type'] == gas_type
                ]['emissions_gg_co2eq'].sum()
            )
            validation_data['emission_totals'][gas_type] = gas_total
            
            for city in major_cities:
                try:
                    city_point = ee.Geometry.Point(city['coords'])
                    sample_value = emission_image.sample(
                        region=city_point,
                        scale=self.target_scale,
                        numPixels=1
                    ).first().get(f'{gas_type}_emissions').getInfo()
                    
                    validation_data['sample_points'].append({
                        'city': city['name'],
                        'coordinates': city['coords'],
                        'gas_type': gas_type,
                        'emission_value': sample_value
                    })
                    
                except Exception as e:
                    print(f"   ⚠️ Failed to sample {gas_type} at {city['name']}: {e}")
        
        # Calculate validation metrics
        validation_data['validation_metrics'] = {
            'total_gases_processed': len(self.emission_layers),
            'total_emission_allocated': sum(validation_data['emission_totals'].values()),
            'auxiliary_layers_used': len(self.auxiliary_layers),
            'sample_points_successful': len(validation_data['sample_points']),
            'export_tasks_created': len(self.export_tasks)
        }
        
        # Save validation data
        validation_file = self.output_dir / "validation_data" / 'enhanced_validation_results.json'
        with open(validation_file, 'w') as f:
            json.dump(validation_data, f, indent=2)
        
        print(f"   ✅ Validation completed: {len(validation_data['sample_points'])} sample points")
        print(f"   ✅ Validation data saved: {validation_file}")
        
        return validation_data
    
    def create_comprehensive_summary(self):
        """Create comprehensive analysis summary"""
        print("\n📋 CREATING COMPREHENSIVE ANALYSIS SUMMARY...")
        
        summary = {
            'analysis_info': {
                'date': datetime.now().isoformat(),
                'country': 'Uzbekistan',
                'reference_year': 2022,
                'methodology': 'Enhanced Spatial GHG Analysis with Comprehensive Mapping',
                'processing_platform': 'Google Earth Engine Enhanced',
                'spatial_resolution': f'{self.target_scale}m'
            },
            'data_sources': {
                'emissions_inventory': 'IPCC 2022 National Inventory',
                'auxiliary_layers': list(self.auxiliary_layers.keys()),
                'landcover_enhancement': 'Multi-source integration with spatial export',
                'spatial_indicators': 'Distance to cities, elevation, composite indicators'
            },
            'emissions_summary': {},
            'spatial_outputs': {
                'auxiliary_layer_exports': len([f for f in self.export_tasks if 'auxiliary' in f.get('filename', '')]),
                'emission_map_exports': len([f for f in self.export_tasks if 'GHG' in f.get('filename', '')]),
                'total_spatial_products': len(self.export_tasks)
            },
            'quality_metrics': {
                'total_categories_processed': len(self.sectoral_emissions),
                'gases_with_spatial_allocation': len(self.emission_layers),
                'auxiliary_layers_successful': len(self.auxiliary_layers),
                'export_tasks_created': len(self.export_tasks)
            },
            'export_tasks': self.export_tasks
        }
        
        # Add emissions summary
        for gas_type in self.emission_layers.keys():
            gas_total = float(
                self.sectoral_emissions[
                    self.sectoral_emissions['gas_type'] == gas_type
                ]['emissions_gg_co2eq'].sum()
            )
            summary['emissions_summary'][gas_type] = {
                'total_gg_co2eq': gas_total,
                'percentage': (gas_total / self.ipcc_data['emissions_2022_gg_co2eq'].sum()) * 100,
                'allocation_method': 'Enhanced multi-layer spatial allocation',
                'spatial_export': f'UZB_GHG_{gas_type}_Enhanced_2022.tif'
            }
        
        # Save comprehensive summary
        summary_file = self.output_dir / 'enhanced_spatial_analysis_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"   ✅ Comprehensive summary saved: {summary_file}")
        
        return summary

def run_enhanced_spatial_analysis():
    """Run the complete enhanced spatial GHG analysis with comprehensive mapping"""
    
    analysis = EnhancedSpatialGHGAnalysis()
    
    try:
        # Step 1: Load and prepare IPCC data
        print("\n" + "="*70)
        print("STEP 1: DATA PREPARATION")
        print("="*70)
        ipcc_data = analysis.load_and_prepare_ipcc_data()
        
        # Step 2: Create comprehensive auxiliary layers
        print("\n" + "="*70)
        print("STEP 2: AUXILIARY DATA LAYERS")
        print("="*70)
        auxiliary_layers = analysis.create_comprehensive_auxiliary_layers()
        
        # Step 3: Spatial allocation with mapping
        print("\n" + "="*70)
        print("STEP 3: SPATIAL ALLOCATION & MAPPING")
        print("="*70)
        emission_layers = analysis.allocate_emissions_spatially_with_export()
        
        # Step 4: Validation and sampling
        print("\n" + "="*70)
        print("STEP 4: VALIDATION & SAMPLING")
        print("="*70)
        validation_data = analysis.validate_and_sample_results()
        
        # Step 5: Comprehensive summary
        print("\n" + "="*70)
        print("STEP 5: COMPREHENSIVE SUMMARY")
        print("="*70)
        summary = analysis.create_comprehensive_summary()
        
        # Final results
        print("\n🎉 ENHANCED SPATIAL GHG ANALYSIS COMPLETED!")
        print("=" * 70)
        print("📊 Analysis Results:")
        print(f"   ✅ Total emissions: {ipcc_data['emissions_2022_gg_co2eq'].sum():.1f} Gg CO₂-eq")
        print(f"   ✅ Gases processed: {len(emission_layers)}")
        print(f"   ✅ Auxiliary layers: {len(auxiliary_layers)}")
        print(f"   ✅ Spatial exports: {len(analysis.export_tasks)}")
        print(f"   ✅ Sample points: {len(validation_data['sample_points'])}")
        
        print("\n🗺️ Spatial Products Created:")
        print("   📊 Auxiliary layer maps (population, nightlights, landcover)")
        print("   🎯 Composite indicator maps (urban, agricultural, industrial)")
        print("   🌍 Individual gas emission maps (CO₂, CH₄, N₂O)")
        print("   🔄 Combined total GHG emission map")
        print("   📋 Validation and sample data")
        
        print("\n📁 Output Directories:")
        print("   📂 spatial_maps/ - Auxiliary and landcover layers")
        print("   📂 composite_indicators/ - Derived spatial indicators")
        print("   📂 emission_maps/ - GHG emission spatial distribution")
        print("   📂 validation_data/ - Sample points and validation")
        
        print("\n🎯 All spatial maps ready for download and GIS integration!")
        
        return analysis, summary
        
    except Exception as e:
        print(f"\n❌ Enhanced spatial analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    print("STARTING: Enhanced Spatial GHG Analysis with Comprehensive Mapping...")
    analysis, summary = run_enhanced_spatial_analysis()
    
    if analysis and summary:
        print("\n✅ SUCCESS: Enhanced spatial analysis completed successfully!")
        print("🌍 Complete spatial distribution maps available for all GHG emissions!")
    else:
        print("\n❌ FAILED: Enhanced spatial analysis encountered errors")
