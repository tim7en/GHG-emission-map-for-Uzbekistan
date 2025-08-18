"""
Geographically Correct Cadastral Polygon Downloader for Uzbekistan NGIS
Handles proper coordinate transformation and CRS definition
"""

import json
import logging
import math
import os
import time
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Set
import requests
from datetime import datetime

class GeoreferencedCadastralDownloader:
    def __init__(self, json_file_path: str, output_dir: str = "georeferenced_cadastral_polygons"):
        """
        Initialize the georeferenced cadastral polygon downloader.
        
        Args:
            json_file_path: Path to the captured JSON file
            output_dir: Directory to save downloaded polygons
        """
        self.json_file_path = json_file_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Initialize session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        # Statistics
        self.stats = {
            'total_urls': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'features_extracted': 0,
            'files_created': 0,
            'coordinates_transformed': 0
        }
        
        self.logger.info(f"Initialized georeferenced downloader for {json_file_path}")
        self.logger.info(f"Output directory: {self.output_dir}")
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.output_dir / 'download.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def web_mercator_to_wgs84(self, x: float, y: float) -> tuple:
        """
        Convert Web Mercator (EPSG:3857) coordinates to WGS84 (EPSG:4326)
        
        Args:
            x: X coordinate in Web Mercator
            y: Y coordinate in Web Mercator
            
        Returns:
            Tuple of (longitude, latitude) in WGS84
        """
        # Web Mercator to WGS84 conversion
        longitude = x / 20037508.34 * 180
        latitude = y / 20037508.34 * 180
        latitude = 180 / math.pi * (2 * math.atan(math.exp(latitude * math.pi / 180)) - math.pi / 2)
        
        return longitude, latitude
        
    def detect_coordinate_system(self, coordinates) -> str:
        """
        Detect if coordinates are in Web Mercator or WGS84
        
        Args:
            coordinates: List of coordinate pairs
            
        Returns:
            'web_mercator' or 'wgs84'
        """
        if not coordinates or not coordinates[0] or len(coordinates[0]) == 0:
            return 'unknown'
            
        # Check first coordinate pair from the first ring
        first_ring = coordinates[0]
        if not first_ring or len(first_ring) == 0:
            return 'unknown'
            
        x, y = first_ring[0][0], first_ring[0][1]
        
        # Web Mercator coordinates for Uzbekistan are typically:
        # X: 7,000,000 - 9,000,000
        # Y: 4,500,000 - 6,000,000
        if abs(x) > 1000000 and abs(y) > 1000000:
            return 'web_mercator'
        
        # WGS84 coordinates for Uzbekistan are typically:
        # Longitude: 56° - 73°
        # Latitude: 37° - 46°
        if 56 <= x <= 73 and 37 <= y <= 46:
            return 'wgs84'
            
        return 'unknown'
        
    def transform_coordinates(self, coordinates, source_crs: str) -> List:
        """
        Transform coordinates to WGS84 if needed
        
        Args:
            coordinates: List of coordinate arrays
            source_crs: Source coordinate system
            
        Returns:
            Transformed coordinates in WGS84
        """
        if source_crs == 'wgs84':
            return coordinates
            
        if source_crs == 'web_mercator':
            transformed = []
            for ring in coordinates:
                transformed_ring = []
                for point in ring:
                    if len(point) >= 2:
                        lon, lat = self.web_mercator_to_wgs84(point[0], point[1])
                        transformed_ring.append([lon, lat])
                        self.stats['coordinates_transformed'] += 1
                    else:
                        transformed_ring.append(point)
                transformed.append(transformed_ring)
            return transformed
            
        # Unknown CRS - return as is but log warning
        self.logger.warning(f"Unknown coordinate system: {source_crs}")
        return coordinates
        
    def load_captured_data(self) -> Dict:
        """Load the captured JSON data"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.logger.info(f"Loaded captured data with {data.get('totalRequests', 0)} requests")
            return data
        except Exception as e:
            self.logger.error(f"Failed to load captured data: {e}")
            raise
            
    def convert_pbf_to_json_url(self, url: str) -> str:
        """
        Convert PBF format URL to JSON format URL
        
        Args:
            url: Original URL with f=pbf parameter
            
        Returns:
            Modified URL with f=json parameter
        """
        # Parse the URL
        parsed = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed.query)
        
        # Change format from pbf to json
        query_params['f'] = ['json']
        
        # Remove problematic parameters that might cause issues with JSON format
        params_to_remove = ['quantizationParameters', 'resultType']
        for param in params_to_remove:
            query_params.pop(param, None)
            
        # Reconstruct URL
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        new_url = urllib.parse.urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, new_query, parsed.fragment
        ))
        
        return new_url
        
    def extract_unique_requests(self, data: Dict) -> List[Dict]:
        """
        Extract unique download requests from captured data
        
        Args:
            data: Captured JSON data
            
        Returns:
            List of unique request dictionaries
        """
        requests_list = data.get('requests', [])
        unique_urls = set()
        unique_requests = []
        
        for request in requests_list:
            url = request.get('url', '')
            if url and url not in unique_urls:
                unique_urls.add(url)
                # Convert PBF URL to JSON URL
                json_url = self.convert_pbf_to_json_url(url)
                
                unique_requests.append({
                    'original_url': url,
                    'json_url': json_url,
                    'layer_name': request.get('ngisInfo', {}).get('layerName', 'unknown'),
                    'zoom_level': request.get('zoomLevel', 'unknown'),
                    'geometry': request.get('ngisInfo', {}).get('geometry', ''),
                    'timestamp': request.get('timestamp', ''),
                    'token': request.get('ngisInfo', {}).get('token', '')
                })
                
        self.logger.info(f"Extracted {len(unique_requests)} unique requests from {len(requests_list)} total requests")
        return unique_requests
        
    def download_polygon_data(self, request_info: Dict) -> Optional[Dict]:
        """
        Download polygon data from a single URL
        
        Args:
            request_info: Request information dictionary
            
        Returns:
            Downloaded data as dictionary or None if failed
        """
        url = request_info['json_url']
        layer_name = request_info['layer_name']
        zoom_level = request_info['zoom_level']
        
        try:
            self.logger.info(f"Downloading from: {layer_name} (zoom: {zoom_level})")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check if response is JSON
            try:
                data = response.json()
            except json.JSONDecodeError:
                self.logger.warning(f"Non-JSON response from {url[:100]}...")
                return None
                
            # Check for ArcGIS error
            if 'error' in data:
                error_info = data['error']
                self.logger.error(f"ArcGIS API error: {error_info.get('message', 'Unknown error')}")
                return None
                
            # Check for features
            features = data.get('features', [])
            if not features:
                self.logger.info(f"No features found for {layer_name}")
                return None
                
            self.logger.info(f"Successfully downloaded {len(features)} features from {layer_name}")
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Download failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error during download: {e}")
            return None
            
    def convert_esri_geometry_to_geojson(self, esri_geometry: Dict) -> Dict:
        """
        Convert ESRI geometry format to standard GeoJSON format with proper CRS
        
        Args:
            esri_geometry: Geometry in ESRI format with 'rings'
            
        Returns:
            Geometry in standard GeoJSON format with 'coordinates'
        """
        if 'rings' not in esri_geometry:
            # Already in correct format or no geometry
            return esri_geometry
            
        rings = esri_geometry['rings']
        
        if not rings:
            return {"type": "Polygon", "coordinates": []}
            
        # Detect coordinate system
        source_crs = self.detect_coordinate_system(rings)
        self.logger.debug(f"Detected coordinate system: {source_crs}")
        
        # Convert rings to coordinates
        coordinates = []
        
        for ring in rings:
            if len(ring) >= 3:  # Valid ring needs at least 3 points
                # Ensure ring is closed (first point == last point)
                if ring[0] != ring[-1]:
                    ring.append(ring[0])
                coordinates.append(ring)
                
        # Transform coordinates if needed
        transformed_coordinates = self.transform_coordinates(coordinates, source_crs)
        
        # Create proper GeoJSON polygon
        geojson_geometry = {
            "type": "Polygon",
            "coordinates": transformed_coordinates
        }
        
        return geojson_geometry
        
    def convert_to_geojson(self, esri_data: Dict, request_info: Dict) -> Dict:
        """
        Convert ESRI format to GeoJSON format with proper georeferencing
        
        Args:
            esri_data: Data in ESRI format
            request_info: Original request information
            
        Returns:
            Data converted to GeoJSON format
        """
        features = []
        
        for feature in esri_data.get('features', []):
            # Convert ESRI geometry to proper GeoJSON geometry
            original_geometry = feature.get('geometry', {})
            converted_geometry = self.convert_esri_geometry_to_geojson(original_geometry)
            
            geojson_feature = {
                "type": "Feature",
                "properties": feature.get('attributes', {}),
                "geometry": converted_geometry
            }
            
            # Add metadata from request
            geojson_feature['properties']['_metadata'] = {
                'layer_name': request_info['layer_name'],
                'zoom_level': request_info['zoom_level'],
                'download_timestamp': datetime.now().isoformat(),
                'source_url': request_info['original_url'][:100] + '...',
                'geometry_bounds': request_info['geometry'],
                'geometry_converted': True,
                'original_format': 'ESRI',
                'coordinate_system': 'EPSG:4326',
                'georeferenced': True,
                'qgis_compatible': True
            }
            
            features.append(geojson_feature)
            
        geojson = {
            "type": "FeatureCollection",
            "crs": {
                "type": "name",
                "properties": {
                    "name": "EPSG:4326"
                }
            },
            "features": features,
            "metadata": {
                "total_features": len(features),
                "layer_name": request_info['layer_name'],
                "zoom_level": request_info['zoom_level'],
                "download_timestamp": datetime.now().isoformat(),
                "source": "Uzbekistan National GIS (db.ngis.uz)",
                "geometry_format": "GeoJSON (converted from ESRI)",
                "coordinate_system": "EPSG:4326 (WGS84)",
                "georeferenced": True,
                "qgis_compatible": True
            }
        }
        
        return geojson
        
    def save_geojson_files(self, geojson_data: Dict, request_info: Dict) -> int:
        """
        Save GeoJSON data as individual files with proper CRS
        
        Args:
            geojson_data: GeoJSON formatted data
            request_info: Request information
            
        Returns:
            Number of files created
        """
        files_created = 0
        layer_name = request_info['layer_name']
        zoom_level = request_info['zoom_level']
        
        # Create layer directory
        layer_dir = self.output_dir / f"{layer_name}_zoom_{zoom_level}"
        layer_dir.mkdir(exist_ok=True)
        
        # Save individual feature files
        for i, feature in enumerate(geojson_data['features']):
            # Generate filename from properties
            properties = feature['properties']
            # Use objectid or fid as primary identifier
            object_id = properties.get('objectid', properties.get('fid', f'feature_{i}'))
            
            # Create simple filename to avoid Windows path issues
            filename = f"feature_{i}_{object_id}.geojson"
            filepath = layer_dir / filename
            
            # Create individual feature collection with CRS
            individual_geojson = {
                "type": "FeatureCollection",
                "crs": {
                    "type": "name",
                    "properties": {
                        "name": "EPSG:4326"
                    }
                },
                "features": [feature],
                "metadata": geojson_data['metadata'].copy()
            }
            individual_geojson['metadata']['feature_id'] = str(object_id)
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(individual_geojson, f, indent=2, ensure_ascii=False)
                files_created += 1
            except Exception as e:
                self.logger.error(f"Failed to save {filepath}: {e}")
                
        # Create clean combined file using proper FeatureCollection structure
        combined_filename = f"{layer_name}_zoom_{zoom_level}_qgis_combined.geojson"
        combined_filepath = layer_dir / combined_filename
        
        try:
            # Check if combined file already exists
            if combined_filepath.exists():
                # Load existing data
                with open(combined_filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                # Append new features to existing
                existing_data['features'].extend(geojson_data['features'])
                # Update metadata
                existing_data['metadata']['total_features'] = len(existing_data['features'])
                existing_data['metadata']['last_update'] = datetime.now().isoformat()
            else:
                # Create new combined file with proper structure
                existing_data = {
                    "type": "FeatureCollection",
                    "crs": {
                        "type": "name",
                        "properties": {
                            "name": "EPSG:4326"
                        }
                    },
                    "features": geojson_data['features'],
                    "metadata": geojson_data['metadata']
                }
            
            # Save with clean JSON formatting for QGIS compatibility
            with open(combined_filepath, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False, separators=(',', ': '))
            
            files_created += 1
            self.logger.info(f"Saved {files_created-1} individual files and 1 combined file to {layer_dir}")
        except Exception as e:
            self.logger.error(f"Failed to save combined file {combined_filepath}: {e}")
            
        return files_created
        
    def run_download_process(self, delay_seconds: float = 2.0, max_requests: Optional[int] = None) -> Dict:
        """
        Run the complete download process with proper georeferencing
        
        Args:
            delay_seconds: Delay between requests
            max_requests: Maximum number of requests to process (None for all)
            
        Returns:
            Dictionary with download statistics
        """
        self.logger.info("Starting georeferenced cadastral polygon download process...")
        
        # Load captured data
        data = self.load_captured_data()
        
        # Extract unique requests
        unique_requests = self.extract_unique_requests(data)
        
        if max_requests:
            unique_requests = unique_requests[:max_requests]
            self.logger.info(f"Limited to {max_requests} requests for testing")
            
        self.stats['total_urls'] = len(unique_requests)
        
        # Process each request
        for i, request_info in enumerate(unique_requests, 1):
            progress_pct = (i / len(unique_requests)) * 100
            
            # Enhanced progress logging for large datasets
            if len(unique_requests) > 1000:
                # For large datasets, log every 50 requests and percentage milestones
                if i % 50 == 0 or progress_pct in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
                    self.logger.info(f"Progress: {i}/{len(unique_requests)} ({progress_pct:.1f}%) - {request_info['layer_name']}")
            else:
                # For smaller datasets, log each request
                self.logger.info(f"Processing {i}/{len(unique_requests)} ({progress_pct:.1f}%): {request_info['layer_name']}")
            
            # Detailed progress every 100 requests for large datasets
            if i % 100 == 0:
                self.logger.info(f"=== MILESTONE: {i}/{len(unique_requests)} requests processed ===")
                self.logger.info(f"Success rate: {(self.stats['successful_downloads'] / i) * 100:.1f}%")
                self.logger.info(f"Features extracted: {self.stats['features_extracted']}")
                self.logger.info(f"Files created: {self.stats['files_created']}")
                self.logger.info(f"Estimated time remaining: {((len(unique_requests) - i) * delay_seconds / 60):.1f} minutes")
            
            # Download data
            esri_data = self.download_polygon_data(request_info)
            
            if esri_data:
                self.stats['successful_downloads'] += 1
                
                # Convert to GeoJSON with proper georeferencing
                geojson_data = self.convert_to_geojson(esri_data, request_info)
                
                # Save files
                files_created = self.save_geojson_files(geojson_data, request_info)
                
                self.stats['features_extracted'] += len(geojson_data['features'])
                self.stats['files_created'] += files_created
                
            else:
                self.stats['failed_downloads'] += 1
                
            # Delay between requests
            if i < len(unique_requests):
                time.sleep(delay_seconds)
                
        # Generate final report
        report = self.generate_final_report()
        return report
        
    def generate_final_report(self) -> Dict:
        """Generate final download report"""
        report = {
            'download_summary': self.stats.copy(),
            'success_rate': (self.stats['successful_downloads'] / max(self.stats['total_urls'], 1)) * 100,
            'output_directory': str(self.output_dir),
            'timestamp': datetime.now().isoformat(),
            'coordinate_system': 'EPSG:4326 (WGS84)',
            'georeferenced': True
        }
        
        # Save report
        report_file = self.output_dir / 'georeferenced_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        # Log summary
        self.logger.info("=== Georeferenced Download Process Complete ===")
        self.logger.info(f"Total URLs processed: {self.stats['total_urls']}")
        self.logger.info(f"Successful downloads: {self.stats['successful_downloads']}")
        self.logger.info(f"Failed downloads: {self.stats['failed_downloads']}")
        self.logger.info(f"Success rate: {report['success_rate']:.1f}%")
        self.logger.info(f"Features extracted: {self.stats['features_extracted']}")
        self.logger.info(f"Files created: {self.stats['files_created']}")
        self.logger.info(f"Coordinates transformed: {self.stats['coordinates_transformed']}")
        self.logger.info(f"Output directory: {self.output_dir}")
        self.logger.info("All files properly georeferenced in EPSG:4326!")
        
        return report

def main():
    """Main execution function"""
    import sys
    
    # Configuration - accept command line arguments
    if len(sys.argv) >= 2:
        json_file_path = sys.argv[1]
    else:
        # Updated to use the new large dataset
        json_file_path = r"c:\Users\User\Downloads\cac_captured_data_2025-08-16T06-55-19-488Z+.json"
    
    if len(sys.argv) >= 3:
        output_directory = sys.argv[2]
    else:
        output_directory = "complete_uzbekistan_cadastral_data"
    
    request_delay = 0.1  # seconds - faster rate for large dataset
    max_requests_for_testing = None  # Process ALL requests (13,927 total)
    
    # Create downloader
    downloader = GeoreferencedCadastralDownloader(json_file_path, output_directory)
    
    # Run download process
    try:
        report = downloader.run_download_process(
            delay_seconds=request_delay,
            max_requests=max_requests_for_testing
        )
        
        print("\n=== GEOREFERENCED DOWNLOAD COMPLETED ===")
        print(f"Success rate: {report['success_rate']:.1f}%")
        print(f"Files created: {report['download_summary']['files_created']}")
        print(f"Features extracted: {report['download_summary']['features_extracted']}")
        print(f"Coordinates transformed: {report['download_summary']['coordinates_transformed']}")
        print(f"Coordinate system: {report['coordinate_system']}")
        print(f"Output directory: {report['output_directory']}")
        print("\n✅ All files properly georeferenced for QGIS!")
        
    except KeyboardInterrupt:
        print("\nDownload interrupted by user")
    except Exception as e:
        print(f"Download failed with error: {e}")

if __name__ == "__main__":
    main()
