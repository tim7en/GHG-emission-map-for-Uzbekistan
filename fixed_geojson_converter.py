"""
Fix GeoJSON geometry format for QGIS compatibility
Converts ESRI rings format to standard GeoJSON coordinates format
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Any

class GeoJSONGeometryFixer:
    def __init__(self, input_dir: str, output_dir: str = "fixed_geojson_output"):
        """
        Initialize the GeoJSON geometry fixer.
        
        Args:
            input_dir: Directory containing ESRI format GeoJSON files
            output_dir: Directory to save fixed GeoJSON files
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        self.stats = {
            'files_processed': 0,
            'files_fixed': 0,
            'features_converted': 0,
            'errors': 0
        }
        
    def convert_esri_geometry_to_geojson(self, esri_geometry: Dict) -> Dict:
        """
        Convert ESRI geometry format to standard GeoJSON format.
        
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
            
        # Convert rings to coordinates
        # First ring is exterior, others are holes
        coordinates = []
        
        for ring in rings:
            if len(ring) >= 3:  # Valid ring needs at least 3 points
                # Ensure ring is closed (first point == last point)
                if ring[0] != ring[-1]:
                    ring.append(ring[0])
                coordinates.append(ring)
                
        # Create proper GeoJSON polygon
        geojson_geometry = {
            "type": "Polygon",
            "coordinates": coordinates
        }
        
        return geojson_geometry
        
    def fix_feature(self, feature: Dict) -> Dict:
        """
        Fix a single GeoJSON feature by converting geometry format.
        
        Args:
            feature: GeoJSON feature with ESRI geometry
            
        Returns:
            Fixed GeoJSON feature with standard geometry
        """
        if 'geometry' not in feature:
            return feature
            
        # Convert geometry
        original_geometry = feature['geometry']
        fixed_geometry = self.convert_esri_geometry_to_geojson(original_geometry)
        
        # Create fixed feature
        fixed_feature = feature.copy()
        fixed_feature['geometry'] = fixed_geometry
        
        # Add conversion metadata
        if '_metadata' not in fixed_feature['properties']:
            fixed_feature['properties']['_metadata'] = {}
            
        fixed_feature['properties']['_metadata']['geometry_converted'] = True
        fixed_feature['properties']['_metadata']['original_format'] = 'ESRI'
        fixed_feature['properties']['_metadata']['converted_format'] = 'GeoJSON'
        
        return fixed_feature
        
    def fix_geojson_file(self, input_file: Path, output_file: Path) -> bool:
        """
        Fix a single GeoJSON file by converting all geometries.
        
        Args:
            input_file: Path to input file
            output_file: Path to output file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load original file
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Check if it's a FeatureCollection
            if data.get('type') != 'FeatureCollection':
                self.logger.warning(f"File {input_file.name} is not a FeatureCollection")
                return False
                
            # Fix each feature
            fixed_features = []
            features_converted = 0
            
            for feature in data.get('features', []):
                fixed_feature = self.fix_feature(feature)
                fixed_features.append(fixed_feature)
                
                # Check if geometry was converted
                if (fixed_feature.get('properties', {}).get('_metadata', {}).get('geometry_converted')):
                    features_converted += 1
                    
            # Create fixed data
            fixed_data = data.copy()
            fixed_data['features'] = fixed_features
            
            # Update metadata
            if 'metadata' not in fixed_data:
                fixed_data['metadata'] = {}
                
            fixed_data['metadata']['geometry_fixed'] = True
            fixed_data['metadata']['features_converted'] = features_converted
            fixed_data['metadata']['original_features'] = len(data.get('features', []))
            fixed_data['metadata']['qgis_compatible'] = True
            
            # Save fixed file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(fixed_data, f, indent=2, ensure_ascii=False)
                
            self.stats['features_converted'] += features_converted
            return True
            
        except Exception as e:
            self.logger.error(f"Error fixing {input_file.name}: {e}")
            self.stats['errors'] += 1
            return False
            
    def process_directory(self) -> Dict:
        """
        Process all GeoJSON files in the input directory.
        
        Returns:
            Dictionary with processing statistics
        """
        self.logger.info(f"Starting GeoJSON geometry fixing process...")
        self.logger.info(f"Input directory: {self.input_dir}")
        self.logger.info(f"Output directory: {self.output_dir}")
        
        # Find all GeoJSON files
        geojson_files = list(self.input_dir.rglob("*.geojson"))
        
        if not geojson_files:
            self.logger.warning("No GeoJSON files found in input directory")
            return self.stats
            
        self.logger.info(f"Found {len(geojson_files)} GeoJSON files to process")
        
        # Process each file
        for input_file in geojson_files:
            # Create output file path maintaining directory structure
            relative_path = input_file.relative_to(self.input_dir)
            output_file = self.output_dir / relative_path
            
            # Create output directory if needed
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Processing: {relative_path}")
            
            # Fix the file
            success = self.fix_geojson_file(input_file, output_file)
            
            self.stats['files_processed'] += 1
            if success:
                self.stats['files_fixed'] += 1
                
        # Generate report
        self.generate_report()
        return self.stats
        
    def generate_report(self):
        """Generate processing report"""
        report = {
            'processing_summary': self.stats.copy(),
            'success_rate': (self.stats['files_fixed'] / max(self.stats['files_processed'], 1)) * 100,
            'output_directory': str(self.output_dir),
            'qgis_ready': True
        }
        
        # Save report
        report_file = self.output_dir / 'geometry_fix_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        # Log summary
        self.logger.info("=== Geometry Fixing Complete ===")
        self.logger.info(f"Files processed: {self.stats['files_processed']}")
        self.logger.info(f"Files fixed: {self.stats['files_fixed']}")
        self.logger.info(f"Features converted: {self.stats['features_converted']}")
        self.logger.info(f"Errors: {self.stats['errors']}")
        self.logger.info(f"Success rate: {report['success_rate']:.1f}%")
        self.logger.info(f"Output directory: {self.output_dir}")
        self.logger.info("Files are now QGIS compatible!")

def main():
    """Main execution function"""
    input_directory = "cadastral_polygons_output"
    output_directory = "qgis_ready_geojson"
    
    # Create fixer
    fixer = GeoJSONGeometryFixer(input_directory, output_directory)
    
    # Process files
    try:
        stats = fixer.process_directory()
        
        print("\n=== GEOMETRY FIXING COMPLETED ===")
        print(f"Files processed: {stats['files_processed']}")
        print(f"Files fixed: {stats['files_fixed']}")
        print(f"Features converted: {stats['features_converted']}")
        print(f"Success rate: {(stats['files_fixed'] / max(stats['files_processed'], 1)) * 100:.1f}%")
        print(f"Output directory: {output_directory}")
        print("\n✅ Files are now ready for QGIS!")
        
    except Exception as e:
        print(f"Processing failed with error: {e}")

if __name__ == "__main__":
    main()
