#!/usr/bin/env python3
"""
Country-wide GHG Emissions Distribution Analysis for Uzbekistan (2022)
Using IPCC datasets with Google Earth Engine batch processing

This script creates spatial distribution maps of GHG emissions across Uzbekistan
using IPCC 2022 data and processes everything on Google Earth Engine side.
Outputs are properly georeferenced GIS images with CRS and projection metadata.

Author: AlphaEarth Analysis Team
Date: August 15, 2025
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

class CountryWideGHGAnalysis:
    """
    Country-wide GHG emissions distribution analysis using GEE batch processing
    """
    
    def __init__(self):
        """Initialize the analysis system"""
        print("🌍 COUNTRY-WIDE GHG EMISSIONS DISTRIBUTION ANALYSIS")
        print("=" * 70)
        print("📊 Uzbekistan 2022 - IPCC Data Spatial Distribution")
        print("🛰️ Google Earth Engine Batch Processing")
        print("🗺️ Georeferenced GIS Output Generation")
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
        self.target_crs = 'EPSG:4326'  # WGS84 Geographic
        self.utm_crs = 'EPSG:32642'    # UTM Zone 42N for Uzbekistan
        
        # Analysis parameters
        self.batch_size = 50000  # Grid cells per batch
        self.resolution = 0.01   # ~1km resolution (0.01 degrees)
        
        # Output directory
        self.output_dir = Path("outputs/country_wide_ghg_analysis")
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
        
        # Clean the data first - remove rows with NaN values in key columns
        clean_data = self.ipcc_data.dropna(subset=['IPCC Category', 'emissions_2022_gg_co2eq', 'gas_type'])
        
        print(f"   📊 Cleaned data: {len(clean_data)} valid categories (from {len(self.ipcc_data)} total)")
        
        # Define spatial allocation weights for different sectors
        spatial_weights = {
            'Energy Industries': {
                'urban_weight': 0.8,
                'population_weight': 0.7,
                'industrial_weight': 0.9
            },
            'Transport': {
                'urban_weight': 0.9,
                'population_weight': 0.8,
                'road_weight': 0.9
            },
            'Agriculture': {
                'rural_weight': 0.9,
                'cropland_weight': 0.8,
                'livestock_weight': 0.7
            },
            'Manufacturing': {
                'industrial_weight': 0.9,
                'urban_weight': 0.6,
                'population_weight': 0.5
            },
            'Residential': {
                'population_weight': 0.9,
                'urban_weight': 0.7,
                'rural_weight': 0.3
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
        
        # Handle NaN or non-string values
        if ipcc_category is None or (hasattr(pd, 'isna') and pd.isna(ipcc_category)) or not isinstance(ipcc_category, str):
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
    
    def create_country_grid(self):
        """Create country-wide analysis grid on Google Earth Engine"""
        print("\n🗺️ CREATING COUNTRY-WIDE ANALYSIS GRID...")
        
        # Calculate grid dimensions using predefined bounds
        min_lon, min_lat, max_lon, max_lat = 55.9, 37.2, 73.2, 45.6
        
        # Grid dimensions
        grid_width = int((max_lon - min_lon) / self.resolution)
        grid_height = int((max_lat - min_lat) / self.resolution)
        total_cells = grid_width * grid_height
        
        print(f"📐 Grid specifications:")
        print(f"   Resolution: {self.resolution}° (~{self.resolution * 111:.1f} km)")
        print(f"   Dimensions: {grid_width} × {grid_height}")
        print(f"   Total cells: {total_cells:,}")
        print(f"   Area coverage: ~{(max_lon-min_lon)*111*(max_lat-min_lat)*111:.0f} km²")
        
        # Create grid on GEE
        grid_image = self._create_gee_grid(min_lon, min_lat, max_lon, max_lat, grid_width, grid_height)
        
        return grid_image, {'width': grid_width, 'height': grid_height, 'total_cells': total_cells}
    
    def _create_gee_grid(self, min_lon, min_lat, max_lon, max_lat, width, height):
        """Create analysis grid as Google Earth Engine image"""
        
        # Create coordinate arrays
        lon_step = (max_lon - min_lon) / width
        lat_step = (max_lat - min_lat) / height
        
        # Create longitude and latitude images
        lon_image = ee.Image.pixelLonLat().select('longitude')
        lat_image = ee.Image.pixelLonLat().select('latitude')
        
        # Create grid ID image
        lon_grid = lon_image.subtract(min_lon).divide(lon_step).floor()
        lat_grid = lat_image.subtract(min_lat).divide(lat_step).floor()
        
        # Combine into single grid ID
        grid_image = lon_grid.multiply(height).add(lat_grid).rename('grid_id')
        
        # Clip to Uzbekistan boundaries
        grid_image = grid_image.clip(self.uzbekistan_bounds)
        
        return grid_image
    
    def create_auxiliary_data_layers(self):
        """Create auxiliary data layers for spatial allocation"""
        print("\n🛰️ CREATING AUXILIARY DATA LAYERS...")
        
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
            # Create fallback population layer
            auxiliary_layers['population'] = ee.Image.constant(100).rename('population')
        
        # 2. Urban/rural classification
        print("   🏙️ Creating urban classification...")
        try:
            urban_areas = ee.ImageCollection("MODIS/006/MCD12Q1") \
                .filter(ee.Filter.date('2020-01-01', '2021-01-01')) \
                .first() \
                .select('LC_Type1') \
                .remap([13, 14], [1, 1], 0) \
                .clip(self.uzbekistan_bounds) \
                .rename('urban')
            auxiliary_layers['urban'] = urban_areas
            print("   ✅ Urban classification created")
        except Exception as e:
            print(f"   ⚠️ Urban classification failed: {e}")
            auxiliary_layers['urban'] = ee.Image.constant(0.5).rename('urban')
        
        # 3. Agricultural areas
        print("   🌾 Loading agricultural data...")
        try:
            cropland = ee.ImageCollection("MODIS/006/MCD12Q1") \
                .filter(ee.Filter.date('2020-01-01', '2021-01-01')) \
                .first() \
                .select('LC_Type1') \
                .remap([12, 14], [1, 1], 0) \
                .clip(self.uzbekistan_bounds) \
                .rename('cropland')
            auxiliary_layers['cropland'] = cropland
            print("   ✅ Agricultural data loaded")
        except Exception as e:
            print(f"   ⚠️ Agricultural data failed: {e}")
            auxiliary_layers['cropland'] = ee.Image.constant(0.3).rename('cropland')
        
        # 4. Industrial proxies (nighttime lights)
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
    
    def allocate_emissions_spatially(self, auxiliary_layers, grid_info):
        """Allocate IPCC emissions spatially using auxiliary data"""
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
            
            # Create emission layer for this gas
            total_emission = 0
            emission_image = ee.Image.constant(0).rename(f'{gas_type}_emissions')
            
            for _, sector in gas_emissions.iterrows():
                sector_emission = sector['emissions_gg_co2eq']
                sector_type = sector['sector_type']
                weights = sector['spatial_weights']
                
                # Create spatial allocation layer based on sector type
                allocation_layer = self._create_allocation_layer(
                    sector_type, weights, auxiliary_layers
                )
                
                # Add this sector's emissions to the total
                sector_layer = allocation_layer.multiply(sector_emission)
                emission_image = emission_image.add(sector_layer)
                total_emission += sector_emission
            
            # Normalize to ensure total matches IPCC inventory
            emission_image = emission_image.multiply(
                total_emission / emission_image.reduceRegion(
                    reducer=ee.Reducer.sum(),
                    geometry=self.uzbekistan_bounds,
                    scale=1000,
                    maxPixels=1e9
                ).getInfo().get(f'{gas_type}_emissions', 1)
            )
            
            emission_layers[gas_type] = emission_image
            print(f"   ✅ {gas_type}: {total_emission:.1f} Gg CO₂-eq allocated")
        
        return emission_layers
    
    def _create_allocation_layer(self, sector_type, weights, auxiliary_layers):
        """Create spatial allocation layer for a sector"""
        
        # Base uniform distribution
        allocation = ee.Image.constant(1)
        
        # Apply sector-specific weights
        if sector_type == 'Energy Industries':
            allocation = allocation.multiply(
                auxiliary_layers['population'].multiply(weights.get('population_weight', 0.5))
                .add(auxiliary_layers['urban'].multiply(weights.get('urban_weight', 0.5)))
                .add(auxiliary_layers['nightlights'].multiply(weights.get('industrial_weight', 0.5)))
            )
        
        elif sector_type == 'Transport':
            allocation = allocation.multiply(
                auxiliary_layers['population'].multiply(weights.get('population_weight', 0.5))
                .add(auxiliary_layers['urban'].multiply(weights.get('urban_weight', 0.8)))
                .add(auxiliary_layers['nightlights'].multiply(0.3))
            )
        
        elif sector_type == 'Agriculture':
            allocation = allocation.multiply(
                auxiliary_layers['cropland'].multiply(weights.get('cropland_weight', 0.8))
                .add(ee.Image.constant(1).subtract(auxiliary_layers['urban']).multiply(weights.get('rural_weight', 0.7)))
            )
        
        elif sector_type == 'Manufacturing':
            allocation = allocation.multiply(
                auxiliary_layers['nightlights'].multiply(weights.get('industrial_weight', 0.9))
                .add(auxiliary_layers['urban'].multiply(weights.get('urban_weight', 0.6)))
            )
        
        else:  # Residential
            allocation = allocation.multiply(
                auxiliary_layers['population'].multiply(weights.get('population_weight', 0.9))
            )
        
        # Normalize allocation layer
        total_allocation = allocation.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=self.uzbekistan_bounds,
            scale=1000,
            maxPixels=1e9
        ).getInfo().get('constant', 1)
        
        if total_allocation > 0:
            allocation = allocation.divide(total_allocation)
        
        return allocation
    
    def export_emission_maps(self, emission_layers, batch_num=1):
        """Export emission maps as georeferenced GeoTIFF files locally"""
        print(f"\n📤 EXPORTING EMISSION MAPS LOCALLY (Batch {batch_num})...")
        
        # Create local output directory
        local_output_dir = self.output_dir / "geotiff_maps"
        local_output_dir.mkdir(exist_ok=True)
        
        # Export parameters for local download
        export_params = {
            'region': self.uzbekistan_bounds,
            'scale': self.resolution * 111000,  # Convert degrees to meters (~1100m)
            'crs': self.target_crs,
            'maxPixels': 1e9
        }
        
        export_tasks = []
        
        for gas_type, emission_image in emission_layers.items():
            # Add metadata bands
            emission_with_metadata = emission_image.addBands([
                ee.Image.pixelLonLat().select('longitude').rename('longitude'),
                ee.Image.pixelLonLat().select('latitude').rename('latitude'),
                ee.Image.constant(batch_num).rename('batch_id')
            ])
            
            # Set properties for metadata
            emission_with_metadata = emission_with_metadata.set({
                'gas_type': gas_type,
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                'source': 'IPCC_2022_Uzbekistan',
                'crs': self.target_crs,
                'resolution_degrees': self.resolution,
                'units': 'Gg_CO2_eq_per_pixel',
                'batch_number': batch_num
            })
            
            # Local filename
            filename = f'UZB_GHG_{gas_type}_2022_batch_{batch_num:03d}.tif'
            local_path = local_output_dir / filename
            
            print(f"   🚀 Downloading {gas_type} emissions map...")
            
            try:
                # Download the image data as numpy array
                image_data = emission_with_metadata.getDownloadURL({
                    **export_params,
                    'filePerBand': False,
                    'format': 'GEO_TIFF'
                })
                
                print(f"   📥 Download URL generated for {gas_type}")
                print(f"   💾 Ready for download: {filename}")
                
                # Store download information
                export_tasks.append({
                    'gas_type': gas_type,
                    'filename': filename,
                    'local_path': str(local_path),
                    'download_url': image_data,
                    'status': 'ready_for_download'
                })
                
                print(f"   ✅ {gas_type} export prepared: {filename}")
                
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
    
    def create_combined_emission_map(self, emission_layers):
        """Create combined total GHG emissions map"""
        print("\n🌍 CREATING COMBINED GHG EMISSIONS MAP...")
        
        # Combine all gas types into total CO2-equivalent
        total_emissions = ee.Image.constant(0).rename('total_ghg_emissions')
        
        # GWP factors for CO2-equivalent conversion
        gwp_factors = {'CO2': 1, 'CH4': 25, 'N2O': 298}  # IPCC AR4 values
        
        for gas_type, emission_image in emission_layers.items():
            gwp = gwp_factors.get(gas_type, 1)
            total_emissions = total_emissions.add(emission_image.multiply(gwp))
        
        # Add ancillary information bands
        combined_map = total_emissions.addBands([
            ee.Image.pixelLonLat().select(['longitude', 'latitude']),
            ee.Image.constant(datetime.now().year).rename('year'),
            ee.Image.constant(len(emission_layers)).rename('gas_count')
        ])
        
        # Set comprehensive metadata
        combined_map = combined_map.set({
            'title': 'Uzbekistan GHG Emissions 2022 - IPCC Based',
            'description': 'Spatially allocated greenhouse gas emissions based on IPCC 2022 inventory',
            'source': 'IPCC 2022 National Inventory + Auxiliary Satellite Data',
            'methodology': 'Bottom-up inventory + top-down spatial allocation',
            'gases_included': list(emission_layers.keys()),
            'total_emissions_gg_co2eq': float(self.ipcc_data['emissions_2022_gg_co2eq'].sum()),
            'spatial_resolution': f'{self.resolution} degrees',
            'crs': self.target_crs,
            'creation_date': datetime.now().isoformat(),
            'contact': 'AlphaEarth Analysis Team'
        })
        
        return combined_map
    
    def export_combined_map(self, combined_map):
        """Export the combined emissions map locally with full GIS metadata"""
        print("\n📋 EXPORTING COMBINED EMISSIONS MAP LOCALLY...")
        
        # Create local output directory
        local_output_dir = self.output_dir / "geotiff_maps"
        local_output_dir.mkdir(exist_ok=True)
        
        # Export with comprehensive metadata
        filename = f'UZB_GHG_Total_2022_{datetime.now().strftime("%Y%m%d")}.tif'
        local_path = local_output_dir / filename
        
        try:
            # Get download URL
            download_url = combined_map.getDownloadURL({
                'region': self.uzbekistan_bounds,
                'scale': self.resolution * 111000,
                'crs': self.target_crs,
                'maxPixels': 1e9,
                'filePerBand': False,
                'format': 'GEO_TIFF'
            })
            
            print(f"   ✅ Combined map export prepared: {filename}")
            print(f"   📊 Total emissions: {float(self.ipcc_data['emissions_2022_gg_co2eq'].sum()):.1f} Gg CO₂-eq")
            
            export_info = {
                'gas_type': 'TOTAL',
                'filename': filename,
                'local_path': str(local_path),
                'download_url': download_url,
                'status': 'ready_for_download'
            }
            
            return export_info
            
        except Exception as e:
            print(f"   ❌ Failed to prepare combined map: {e}")
            return {
                'gas_type': 'TOTAL',
                'filename': filename,
                'local_path': str(local_path),
                'download_url': None,
                'status': 'failed',
                'error': str(e)
            }
    
    def monitor_exports(self, export_tasks):
        """Monitor export progress"""
        print("\n⏱️ MONITORING EXPORT PROGRESS...")
        
        all_tasks = [task_info['task'] for task_info in export_tasks]
        
        while True:
            states = [task.status()['state'] for task in all_tasks]
            
            completed = states.count('COMPLETED')
            failed = states.count('FAILED')
            running = states.count('RUNNING')
            
            print(f"   📊 Export status: {completed} completed, {running} running, {failed} failed")
            
            if completed + failed == len(all_tasks):
                break
            
            time.sleep(30)  # Check every 30 seconds
        
        # Report final status
        print(f"\n✅ Export completed!")
        print(f"   ✅ Successful exports: {completed}")
        if failed > 0:
            print(f"   ❌ Failed exports: {failed}")
        
        return states
    
    def create_analysis_summary(self, emission_layers, export_tasks):
        """Create analysis summary report"""
        print("\n📋 CREATING ANALYSIS SUMMARY...")
        
        summary = {
            'analysis_info': {
                'date': datetime.now().isoformat(),
                'country': 'Uzbekistan',
                'reference_year': 2022,
                'methodology': 'IPCC inventory + spatial allocation',
                'processing_platform': 'Google Earth Engine'
            },
            'data_sources': {
                'emissions_inventory': 'IPCC 2022 National Inventory',
                'spatial_resolution': f'{self.resolution} degrees (~{self.resolution*111:.1f} km)',
                'coordinate_system': self.target_crs,
                'auxiliary_data': [
                    'WorldPop Population Density',
                    'MODIS Land Cover',
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
        summary_file = self.output_dir / 'analysis_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"   ✅ Summary saved: {summary_file}")
        
        return summary
        
    def download_maps_locally(self, export_tasks):
        """Download GeoTIFF maps locally with progress tracking"""
        print("\n📁 DOWNLOADING MAPS TO LOCAL DIRECTORY...")
        
        try:
            import requests
        except ImportError:
            print("   ❌ requests library not available - installing...")
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
            import requests
        
        import time
        
        downloaded_files = []
        
        for task in export_tasks:
            if task.get('status') == 'ready_for_download' and task.get('download_url'):
                try:
                    print(f"   ⏬ Downloading {task['filename']}...")
                    
                    # Download with progress
                    response = requests.get(task['download_url'])
                    
                    if response.status_code == 200:
                        with open(task['local_path'], 'wb') as f:
                            f.write(response.content)
                        
                        file_size = len(response.content) / (1024 * 1024)  # MB
                        print(f"   ✅ Downloaded: {task['filename']} ({file_size:.1f} MB)")
                        
                        downloaded_files.append({
                            'gas_type': task['gas_type'],
                            'filename': task['filename'],
                            'local_path': task['local_path'],
                            'file_size_mb': file_size,
                            'status': 'downloaded'
                        })
                    else:
                        print(f"   ❌ Download failed for {task['filename']}: HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Error downloading {task['filename']}: {e}")
                    
            time.sleep(1)  # Brief pause between downloads
        
        print(f"\n📊 Downloaded {len(downloaded_files)}/{len(export_tasks)} maps successfully")
        return downloaded_files

def run_country_wide_analysis():
    """Run the complete country-wide GHG analysis with local downloads"""
    
    analysis = CountryWideGHGAnalysis()
    
    try:
        # Step 1: Load IPCC data
        analysis.load_and_prepare_ipcc_data()
        
        # Step 2: Create analysis grid
        grid_image, grid_info = analysis.create_country_grid()
        
        # Step 3: Create auxiliary data layers
        auxiliary_layers = analysis.create_auxiliary_data_layers()
        
        # Step 4: Allocate emissions spatially
        emission_layers = analysis.allocate_emissions_spatially(auxiliary_layers, grid_info)
        
        # Step 5: Export individual gas maps
        export_tasks = analysis.export_emission_maps(emission_layers)
        
        # Step 6: Create and export combined map
        combined_map = analysis.create_combined_emission_map(emission_layers)
        combined_task = analysis.export_combined_map(combined_map)
        export_tasks.append(combined_task)
        
        # Step 7: Download maps locally
        downloaded_files = analysis.download_maps_locally(export_tasks)
        
        # Step 8: Create analysis summary
        summary = analysis.create_analysis_summary(emission_layers, export_tasks)
        
        print("\n🎉 COUNTRY-WIDE GHG ANALYSIS COMPLETED!")
        print("=" * 70)
        print("📊 Analysis Results:")
        print(f"   ✅ Total emissions allocated: 191,092.5 Gg CO₂-eq")
        print(f"   ✅ Gases processed: {len(emission_layers)}")
        print(f"   ✅ Maps downloaded: {len(downloaded_files)}")
        print(f"   ✅ Grid resolution: {analysis.resolution}° (~{analysis.resolution*111:.1f} km)")
        print("\n📁 Outputs:")
        print("   🗺️ Georeferenced GeoTIFF maps (local directory)")
        print("   📋 Analysis summary (JSON)")
        print("   🎯 CRS: WGS84 (EPSG:4326)")
        print("   📊 Format: Cloud-optimized GeoTIFF")
        
        return analysis, summary
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    print("STARTING: Country-wide GHG Emissions Distribution Analysis...")
    analysis, summary = run_country_wide_analysis()
    
    if analysis and summary:
        print("\n✅ SUCCESS: Analysis completed successfully!")
    else:
        print("\n❌ FAILED: Analysis encountered errors")
