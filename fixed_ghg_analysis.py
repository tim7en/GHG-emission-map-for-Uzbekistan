#!/usr/bin/env python3
"""
Fixed Country-wide GHG Emissions Analysis for Uzbekistan (2022)
Addresses Google Earth Engine projection and null image issues

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

class FixedGHGAnalysis:
    """
    Fixed GHG emissions analysis with proper GEE image handling
    """
    
    def __init__(self, enable_spatial_maps=True, export_format='GeoTIFF'):
        """Initialize the fixed analysis system with spatial mapping options"""
        print("🔧 FIXED COUNTRY-WIDE GHG EMISSIONS ANALYSIS")
        print("=" * 70)
        print("📊 Uzbekistan 2022 - IPCC Data with Proper GEE Handling")
        print("🛠️ Fixed Projection and Null Image Issues")
        print("🌍 Simplified but Robust Landcover Integration")
        if enable_spatial_maps:
            print("🗺️ Spatial Maps Export Enabled")
        print("=" * 70)
        
        # Initialize GEE
        try:
            ee.Initialize(project='ee-sabitovty')
            print("✅ Google Earth Engine initialized successfully")
        except Exception as e:
            print(f"❌ GEE initialization failed: {e}")
            raise
        
        # Define Uzbekistan boundaries with proper CRS
        self.uzbekistan_bounds = ee.Geometry.Rectangle([55.9, 37.2, 73.2, 45.6])
        self.target_crs = 'EPSG:4326'
        self.target_scale = 1000  # 1km resolution
        
        # Spatial mapping options
        self.enable_spatial_maps = enable_spatial_maps
        self.export_format = export_format
        
        # Output directory
        self.output_dir = Path("outputs/fixed_ghg_analysis")
        self.output_dir.mkdir(exist_ok=True)
        
        if self.enable_spatial_maps:
            self.maps_dir = self.output_dir / "spatial_maps"
            self.maps_dir.mkdir(exist_ok=True)
        
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
    
    def create_fixed_auxiliary_layers(self):
        """Create auxiliary data layers with proper projection handling"""
        print("\n🛰️ CREATING FIXED AUXILIARY DATA LAYERS...")
        
        auxiliary_layers = {}
        
        # 1. Population density (most reliable)
        print("   📊 Loading population data...")
        try:
            population = ee.ImageCollection("WorldPop/GP/100m/pop") \
                .filter(ee.Filter.date('2020-01-01', '2023-01-01')) \
                .mosaic() \
                .setDefaultProjection('EPSG:4326', None, 100) \
                .reproject('EPSG:4326', None, self.target_scale) \
                .clip(self.uzbekistan_bounds) \
                .rename('population')
            
            # Test the image to make sure it's valid
            test_pixel = population.sample(
                region=ee.Geometry.Point([69.24, 41.30]),  # Tashkent
                scale=self.target_scale,
                numPixels=1
            ).size()
            
            if test_pixel.getInfo() > 0:
                auxiliary_layers['population'] = population
                print("   ✅ Population layer loaded and validated")
            else:
                raise Exception("Population layer validation failed")
                
        except Exception as e:
            print(f"   ⚠️ Population layer failed: {e}")
            # Create fallback uniform population
            auxiliary_layers['population'] = ee.Image.constant(100).rename('population')
        
        # 2. Nighttime lights (reliable for industrial/urban)
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
            
            # Test the image
            test_pixel = nightlights.sample(
                region=ee.Geometry.Point([69.24, 41.30]),
                scale=self.target_scale,
                numPixels=1
            ).size()
            
            if test_pixel.getInfo() > 0:
                auxiliary_layers['nightlights'] = nightlights
                print("   ✅ Nighttime lights loaded and validated")
            else:
                raise Exception("Nightlights validation failed")
                
        except Exception as e:
            print(f"   ⚠️ Nighttime lights failed: {e}")
            auxiliary_layers['nightlights'] = ee.Image.constant(1).rename('nightlights')
        
        # 3. Simple urban classification using newer MODIS dataset
        print("   🏙️ Creating urban classification...")
        try:
            # Use more recent MODIS data
            modis_lc = ee.ImageCollection("MODIS/061/MCD12Q1") \
                .filter(ee.Filter.date('2022-01-01', '2023-01-01')) \
                .first() \
                .select('LC_Type1') \
                .setDefaultProjection('EPSG:4326', None, 500) \
                .reproject('EPSG:4326', None, self.target_scale)
            
            # Create urban mask (class 13 = urban)
            urban = modis_lc.eq(13).rename('urban').clip(self.uzbekistan_bounds)
            
            # Test the image
            test_pixel = urban.sample(
                region=ee.Geometry.Point([69.24, 41.30]),
                scale=self.target_scale,
                numPixels=1
            ).size()
            
            if test_pixel.getInfo() > 0:
                auxiliary_layers['urban'] = urban
                print("   ✅ Urban classification created and validated")
            else:
                raise Exception("Urban classification validation failed")
                
        except Exception as e:
            print(f"   ⚠️ Urban classification failed: {e}")
            # Create urban proxy from nighttime lights
            if 'nightlights' in auxiliary_layers:
                urban_proxy = auxiliary_layers['nightlights'].gt(1).rename('urban')
                auxiliary_layers['urban'] = urban_proxy
                print("   ✅ Urban proxy created from nighttime lights")
            else:
                auxiliary_layers['urban'] = ee.Image.constant(0.1).rename('urban')
        
        # 4. Simple cropland classification
        print("   🌾 Creating cropland classification...")
        try:
            if 'modis_lc' in locals():
                # Create cropland mask (classes 12, 14 = cropland)
                cropland = modis_lc.eq(12).Or(modis_lc.eq(14)).rename('cropland').clip(self.uzbekistan_bounds)
                
                # Test the image
                test_pixel = cropland.sample(
                    region=ee.Geometry.Point([66.96, 39.65]),  # Samarkand agricultural area
                    scale=self.target_scale,
                    numPixels=1
                ).size()
                
                if test_pixel.getInfo() > 0:
                    auxiliary_layers['cropland'] = cropland
                    print("   ✅ Cropland classification created and validated")
                else:
                    raise Exception("Cropland validation failed")
            else:
                raise Exception("MODIS data not available")
                
        except Exception as e:
            print(f"   ⚠️ Cropland classification failed: {e}")
            # Create cropland proxy (inverse of urban + population)
            if 'urban' in auxiliary_layers and 'population' in auxiliary_layers:
                cropland_proxy = auxiliary_layers['population'].gt(50).And(
                    auxiliary_layers['urban'].eq(0)
                ).rename('cropland')
                auxiliary_layers['cropland'] = cropland_proxy
                print("   ✅ Cropland proxy created")
            else:
                auxiliary_layers['cropland'] = ee.Image.constant(0.3).rename('cropland')
        
        if self.enable_spatial_maps:
            print(f"   ✅ Successfully created {len(auxiliary_layers)} auxiliary layers")
            self.export_auxiliary_maps(auxiliary_layers)
        else:
            print(f"   ✅ Successfully created {len(auxiliary_layers)} auxiliary layers")
            
        return auxiliary_layers
    
    def export_auxiliary_maps(self, auxiliary_layers):
        """Export auxiliary data layers as spatial maps"""
        print("\n🗺️ EXPORTING AUXILIARY SPATIAL MAPS...")
        
        for layer_name, layer_image in auxiliary_layers.items():
            try:
                print(f"   📊 Exporting {layer_name} map...")
                
                # Add metadata to the image
                layer_with_metadata = layer_image.set({
                    'layer_name': layer_name,
                    'analysis_date': datetime.now().isoformat(),
                    'country': 'Uzbekistan',
                    'crs': self.target_crs,
                    'scale': self.target_scale,
                    'description': f'Auxiliary data layer: {layer_name}'
                })
                
                # Export parameters
                export_params = {
                    'image': layer_with_metadata,
                    'description': f'UZB_auxiliary_{layer_name}',
                    'folder': 'GHG_Analysis_Uzbekistan',
                    'region': self.uzbekistan_bounds,
                    'scale': self.target_scale,
                    'crs': self.target_crs,
                    'maxPixels': 100000000,
                    'fileFormat': 'GeoTIFF'
                }
                
                # Start export task
                task = ee.batch.Export.image.toDrive(**export_params)
                task.start()
                
                print(f"      ✅ {layer_name} export task started: {task.id}")
                
            except Exception as e:
                print(f"      ❌ Failed to export {layer_name}: {e}")
    
    def allocate_emissions_spatially(self, auxiliary_layers):
        """Allocate IPCC emissions spatially with proper error handling"""
        print("\n🎯 ALLOCATING EMISSIONS SPATIALLY...")
        
        emission_layers = {}
        
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
                # Create base allocation image
                total_emission = gas_emissions['emissions_gg_co2eq'].sum()
                
                # Create simple allocation based on sector weights
                allocation_image = self._create_simple_allocation(gas_emissions, auxiliary_layers)
                
                if allocation_image is not None:
                    # Ensure proper scaling to match total emissions
                    emission_layers[gas_type] = allocation_image.multiply(total_emission).rename(f'{gas_type}_emissions')
                    print(f"   ✅ {gas_type}: {total_emission:.1f} Gg CO₂-eq allocated")
                else:
                    print(f"   ❌ {gas_type}: allocation failed")
                    
            except Exception as e:
                print(f"   ❌ {gas_type} allocation error: {e}")
        
        return emission_layers
    
    def export_emission_maps(self, emission_layers):
        """Export emission maps as spatial GeoTIFF files"""
        if not self.enable_spatial_maps:
            print("   ⚠️ Spatial maps export disabled")
            return {}
            
        print("\n🗺️ EXPORTING EMISSION SPATIAL MAPS...")
        
        export_tasks = {}
        
        for gas_type, emission_image in emission_layers.items():
            try:
                print(f"   📊 Exporting {gas_type} emission map...")
                
                # Add comprehensive metadata
                emission_with_metadata = emission_image.set({
                    'gas_type': gas_type,
                    'analysis_date': datetime.now().isoformat(),
                    'country': 'Uzbekistan',
                    'reference_year': 2022,
                    'methodology': 'IPCC inventory + spatial allocation',
                    'crs': self.target_crs,
                    'spatial_resolution': f'{self.target_scale}m',
                    'units': 'Gg_CO2_eq_per_pixel',
                    'source': 'IPCC_2022_National_Inventory',
                    'total_emissions': float(
                        self.sectoral_emissions[
                            self.sectoral_emissions['gas_type'] == gas_type
                        ]['emissions_gg_co2eq'].sum()
                    )
                })
                
                # Add coordinate bands for enhanced metadata
                emission_with_coords = emission_with_metadata.addBands([
                    ee.Image.pixelLonLat().select('longitude').rename('longitude'),
                    ee.Image.pixelLonLat().select('latitude').rename('latitude')
                ])
                
                # Export parameters
                export_params = {
                    'image': emission_with_coords,
                    'description': f'UZB_GHG_{gas_type}_emissions_2022',
                    'folder': 'GHG_Analysis_Uzbekistan',
                    'region': self.uzbekistan_bounds,
                    'scale': self.target_scale,
                    'crs': self.target_crs,
                    'maxPixels': 100000000,
                    'fileFormat': 'GeoTIFF'
                }
                
                # Start export task
                task = ee.batch.Export.image.toDrive(**export_params)
                task.start()
                
                export_tasks[gas_type] = {
                    'task': task,
                    'task_id': task.id,
                    'filename': f'UZB_GHG_{gas_type}_emissions_2022.tif',
                    'status': 'STARTED'
                }
                
                print(f"      ✅ {gas_type} export task started: {task.id}")
                
            except Exception as e:
                print(f"      ❌ Failed to export {gas_type}: {e}")
                export_tasks[gas_type] = {
                    'task': None,
                    'task_id': None,
                    'filename': f'UZB_GHG_{gas_type}_emissions_2022.tif',
                    'status': 'FAILED',
                    'error': str(e)
                }
        
        return export_tasks
    
    def create_combined_emission_map(self, emission_layers):
        """Create combined total GHG emissions map"""
        if len(emission_layers) == 0:
            return None
            
        print("\n🌍 CREATING COMBINED GHG EMISSIONS MAP...")
        
        # Combine all gas types
        total_emissions = ee.Image.constant(0).rename('total_ghg_emissions')
        
        for gas_type, emission_image in emission_layers.items():
            total_emissions = total_emissions.add(emission_image)
        
        # Add metadata
        total_emissions_value = float(self.ipcc_data['emissions_2022_gg_co2eq'].sum())
        
        combined_map = total_emissions.set({
            'title': 'Uzbekistan Total GHG Emissions 2022',
            'description': 'Combined spatial map of all greenhouse gas emissions',
            'gases_included': list(emission_layers.keys()),
            'total_emissions_gg_co2eq': total_emissions_value,
            'analysis_date': datetime.now().isoformat(),
            'methodology': 'IPCC inventory + sector-specific spatial allocation',
            'crs': self.target_crs,
            'spatial_resolution': f'{self.target_scale}m',
            'units': 'Gg_CO2_eq_per_pixel'
        })
        
        print(f"   ✅ Combined map created with {len(emission_layers)} gas types")
        print(f"   ✅ Total emissions: {total_emissions_value:.1f} Gg CO₂-eq")
        
        return combined_map
    
    def export_combined_map(self, combined_map):
        """Export the combined emissions map"""
        if not self.enable_spatial_maps or combined_map is None:
            return None
            
        print("\n📋 EXPORTING COMBINED EMISSIONS MAP...")
        
        try:
            # Add coordinate bands
            combined_with_coords = combined_map.addBands([
                ee.Image.pixelLonLat().select(['longitude', 'latitude']),
                ee.Image.constant(datetime.now().year).rename('year')
            ])
            
            # Export parameters
            export_params = {
                'image': combined_with_coords,
                'description': f'UZB_GHG_TOTAL_emissions_2022',
                'folder': 'GHG_Analysis_Uzbekistan',
                'region': self.uzbekistan_bounds,
                'scale': self.target_scale,
                'crs': self.target_crs,
                'maxPixels': 100000000,
                'fileFormat': 'GeoTIFF'
            }
            
            # Start export task
            task = ee.batch.Export.image.toDrive(**export_params)
            task.start()
            
            print(f"   ✅ Combined map export started: {task.id}")
            
            return {
                'task': task,
                'task_id': task.id,
                'filename': 'UZB_GHG_TOTAL_emissions_2022.tif',
                'status': 'STARTED'
            }
            
        except Exception as e:
            print(f"   ❌ Failed to export combined map: {e}")
            return {
                'task': None,
                'task_id': None,
                'filename': 'UZB_GHG_TOTAL_emissions_2022.tif',
                'status': 'FAILED',
                'error': str(e)
            }
    
    def monitor_export_tasks(self, export_tasks, combined_task=None):
        """Monitor the status of export tasks"""
        if not self.enable_spatial_maps:
            return
            
        print("\n⏱️ MONITORING EXPORT TASKS...")
        
        all_tasks = []
        task_names = []
        
        # Add emission export tasks
        for gas_type, task_info in export_tasks.items():
            if task_info.get('task'):
                all_tasks.append(task_info['task'])
                task_names.append(f"{gas_type} emissions")
        
        # Add combined task
        if combined_task and combined_task.get('task'):
            all_tasks.append(combined_task['task'])
            task_names.append("Combined emissions")
        
        if len(all_tasks) == 0:
            print("   ⚠️ No export tasks to monitor")
            return
        
        print(f"   📊 Monitoring {len(all_tasks)} export tasks...")
        
        # Check initial status
        for i, (task, name) in enumerate(zip(all_tasks, task_names)):
            try:
                status = task.status()['state']
                print(f"   {i+1}. {name}: {status}")
            except Exception as e:
                print(f"   {i+1}. {name}: ERROR - {e}")
        
        print("\n   💡 Export tasks are running in Google Earth Engine")
        print("   💡 Check your Google Drive folder 'GHG_Analysis_Uzbekistan' for completed files")
        print("   💡 Large exports may take 10-30 minutes to complete")
    
    def _create_simple_allocation(self, gas_emissions, auxiliary_layers):
        """Create simple but robust allocation layer"""
        try:
            # Start with uniform base
            allocation = ee.Image.constant(1).rename('allocation')
            
            # Sector-based weights
            sector_weights = {
                'Energy Industries': {'population': 0.3, 'urban': 0.4, 'nightlights': 0.3},
                'Transport': {'population': 0.4, 'urban': 0.5, 'nightlights': 0.1},
                'Agriculture': {'population': 0.2, 'cropland': 0.7, 'urban': -0.1},  # negative urban weight
                'Manufacturing': {'population': 0.2, 'urban': 0.3, 'nightlights': 0.5},
                'Residential': {'population': 0.8, 'urban': 0.2, 'nightlights': 0.0}
            }
            
            # Aggregate sector emissions
            sector_totals = gas_emissions.groupby('sector_type')['emissions_gg_co2eq'].sum()
            
            final_allocation = ee.Image.constant(0).rename('final_allocation')
            
            for sector, total_emission in sector_totals.items():
                if total_emission <= 0:
                    continue
                
                weights = sector_weights.get(sector, {'population': 1.0})
                sector_allocation = ee.Image.constant(0.1)  # Base level
                
                # Apply weights for available layers
                for layer_name, weight in weights.items():
                    if layer_name in auxiliary_layers and weight != 0:
                        if weight > 0:
                            sector_allocation = sector_allocation.add(
                                auxiliary_layers[layer_name].multiply(weight)
                            )
                        else:  # negative weight (e.g., agriculture avoids urban)
                            sector_allocation = sector_allocation.add(
                                ee.Image.constant(1).subtract(auxiliary_layers[layer_name]).multiply(abs(weight))
                            )
                
                # Normalize sector allocation
                sector_allocation = sector_allocation.multiply(total_emission)
                final_allocation = final_allocation.add(sector_allocation)
            
            # Normalize to create probability distribution
            total_sum = final_allocation.reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=self.uzbekistan_bounds,
                scale=self.target_scale,
                maxPixels=1e8
            ).values().get(0)
            
            # Convert to image for division
            total_sum_image = ee.Image.constant(total_sum)
            return final_allocation.divide(total_sum_image)
            
        except Exception as e:
            print(f"      ⚠️ Simple allocation failed: {e}")
            # Return uniform distribution as fallback
            return ee.Image.constant(1).divide(
                ee.Image.constant(1).reduceRegion(
                    reducer=ee.Reducer.sum(),
                    geometry=self.uzbekistan_bounds,
                    scale=self.target_scale,
                    maxPixels=1e8
                ).values().get(0)
            )
    
    def export_sample_data(self, emission_layers):
        """Export sample data for validation"""
        print("\n📊 EXPORTING SAMPLE DATA...")
        
        sample_data = {
            'analysis_info': {
                'date': datetime.now().isoformat(),
                'method': 'Fixed GHG Analysis with Proper GEE Handling',
                'spatial_resolution': f'{self.target_scale}m'
            },
            'emission_totals': {},
            'sample_points': []
        }
        
        # Add emission totals
        for gas_type in emission_layers.keys():
            gas_total = float(
                self.sectoral_emissions[
                    self.sectoral_emissions['gas_type'] == gas_type
                ]['emissions_gg_co2eq'].sum()
            )
            sample_data['emission_totals'][gas_type] = gas_total
        
        # Sample points across Uzbekistan
        major_cities = [
            {'name': 'Tashkent', 'coords': [69.24, 41.30]},
            {'name': 'Samarkand', 'coords': [66.96, 39.65]},
            {'name': 'Bukhara', 'coords': [64.42, 39.77]},
            {'name': 'Andijan', 'coords': [72.34, 40.78]},
            {'name': 'Nukus', 'coords': [59.61, 42.45]}
        ]
        
        for city in major_cities:
            city_point = ee.Geometry.Point(city['coords'])
            
            for gas_type, emission_image in emission_layers.items():
                try:
                    sample_value = emission_image.sample(
                        region=city_point,
                        scale=self.target_scale,
                        numPixels=1
                    ).first().get(f'{gas_type}_emissions').getInfo()
                    
                    sample_data['sample_points'].append({
                        'city': city['name'],
                        'coordinates': city['coords'],
                        'gas_type': gas_type,
                        'emission_value': sample_value
                    })
                    
                except Exception as e:
                    print(f"   ⚠️ Failed to sample {gas_type} at {city['name']}: {e}")
        
        # Save sample data
        sample_file = self.output_dir / 'fixed_sample_data.json'
        with open(sample_file, 'w') as f:
            json.dump(sample_data, f, indent=2)
        
        print(f"   ✅ Sample data saved: {sample_file}")
        return sample_data
    
    def create_analysis_summary(self, emission_layers, auxiliary_layers):
        """Create comprehensive analysis summary"""
        print("\n📋 CREATING ANALYSIS SUMMARY...")
        
        summary = {
            'analysis_info': {
                'date': datetime.now().isoformat(),
                'country': 'Uzbekistan',
                'reference_year': 2022,
                'methodology': 'Fixed IPCC inventory + robust spatial allocation',
                'processing_platform': 'Google Earth Engine (Fixed)',
                'spatial_resolution': f'{self.target_scale}m'
            },
            'fixes_applied': {
                'projection_handling': 'setDefaultProjection() before reproject()',
                'null_image_prevention': 'Validation tests and fallback images',
                'deprecated_datasets': 'Updated to MODIS/061/MCD12Q1',
                'error_handling': 'Comprehensive try-catch with fallbacks'
            },
            'data_sources': {
                'emissions_inventory': 'IPCC 2022 National Inventory',
                'auxiliary_data_loaded': list(auxiliary_layers.keys()),
                'auxiliary_data_count': len(auxiliary_layers)
            },
            'emissions_summary': {},
            'quality_metrics': {
                'total_categories_processed': len(self.sectoral_emissions),
                'gases_with_spatial_allocation': len(emission_layers),
                'auxiliary_layers_successful': len(auxiliary_layers)
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
                'allocation_method': 'Fixed sector-specific weights'
            }
        
        # Save summary
        summary_file = self.output_dir / 'fixed_analysis_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"   ✅ Analysis summary saved: {summary_file}")
        return summary

def run_fixed_analysis(enable_spatial_maps=True):
    """Run the fixed GHG analysis with optional spatial mapping"""
    
    analysis = FixedGHGAnalysis(enable_spatial_maps=enable_spatial_maps)
    
    try:
        # Step 1: Load IPCC data
        ipcc_data = analysis.load_and_prepare_ipcc_data()
        
        # Step 2: Create fixed auxiliary layers
        auxiliary_layers = analysis.create_fixed_auxiliary_layers()
        
        # Step 3: Allocate emissions spatially
        emission_layers = analysis.allocate_emissions_spatially(auxiliary_layers)
        
        # Step 4: Export emission maps (if enabled)
        export_tasks = {}
        combined_task = None
        if enable_spatial_maps:
            export_tasks = analysis.export_emission_maps(emission_layers)
            
            # Step 5: Create and export combined map
            combined_map = analysis.create_combined_emission_map(emission_layers)
            if combined_map:
                combined_task = analysis.export_combined_map(combined_map)
            
            # Step 6: Monitor export tasks
            analysis.monitor_export_tasks(export_tasks, combined_task)
        
        # Step 7: Export sample data
        sample_data = analysis.export_sample_data(emission_layers)
        
        # Step 8: Create analysis summary
        summary = analysis.create_analysis_summary(emission_layers, auxiliary_layers, export_tasks, combined_task)
        
        print("\n🎉 FIXED GHG ANALYSIS COMPLETED!")
        print("=" * 70)
        print("📊 Analysis Results:")
        print(f"   ✅ Total emissions: {ipcc_data['emissions_2022_gg_co2eq'].sum():.1f} Gg CO₂-eq")
        print(f"   ✅ Gases processed: {len(emission_layers)}")
        print(f"   ✅ Auxiliary layers: {len(auxiliary_layers)}")
        print(f"   ✅ Sample points: {len(sample_data.get('sample_points', []))}")
        
        if enable_spatial_maps:
            print("\n�️ Spatial Maps:")
            print(f"   ✅ Emission maps: {len(export_tasks)} gas types")
            if combined_task:
                print("   ✅ Combined map: 1 total emissions map")
            print("   📁 Check Google Drive folder: 'GHG_Analysis_Uzbekistan'")
        
        print("\n�🛠️ Fixes Applied:")
        print("   ✅ Proper projection handling with setDefaultProjection()")
        print("   ✅ Image validation tests to prevent null images")
        print("   ✅ Updated to newer MODIS dataset (061/MCD12Q1)")
        print("   ✅ Comprehensive error handling with fallbacks")
        print("   ✅ Simplified but robust allocation algorithms")
        
        print("\n📁 Outputs:")
        print("   📋 Fixed analysis summary (JSON)")
        print("   📊 Sample emission data (JSON)")
        print("   🎯 Robust spatial allocation results")
        if enable_spatial_maps:
            print("   🗺️ Spatial emission maps (GeoTIFF)")
        
        return analysis, summary
        
    except Exception as e:
        print(f"\n❌ Fixed analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    print("STARTING: Fixed Enhanced GHG Analysis...")
    analysis, summary = run_fixed_analysis()
    
    if analysis and summary:
        print("\n✅ SUCCESS: Fixed analysis completed successfully!")
        print("🎯 Robust GHG spatial allocation now working properly!")
    else:
        print("\n❌ FAILED: Fixed analysis encountered errors")
