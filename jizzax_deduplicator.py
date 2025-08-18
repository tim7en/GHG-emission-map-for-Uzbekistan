#!/usr/bin/env python3
"""
Comprehensive Deduplicator for Jizzax Cadastral Data

This script analyzes all unique properties across different layer types and removes duplicates
based on comprehensive property analysis, not just file content.

Key features:
- Analyzes unique properties across all layer types
- Detects duplicates based on multiple property combinations
- Preserves metadata and georeferencing information
- Provides detailed reporting on unique properties found
- Safe deduplication with backup functionality
"""

import json
import os
import hashlib
import shutil
import time
from pathlib import Path
from collections import defaultdict, Counter
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveDeduplicator:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.backup_dir = self.data_dir / "jizzax_duplicates_backup"
        self.property_analysis = {
            'unique_properties': set(),
            'property_combinations': defaultdict(list),
            'layer_properties': defaultdict(set),
            'property_stats': Counter()
        }
        self.duplicates = []
        self.files_processed = 0
        self.start_time = time.time()
        
    def analyze_file_properties(self, file_path):
        """Extract and analyze all properties from a GeoJSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract feature properties
            properties = {}
            if 'features' in data and len(data['features']) > 0:
                feature_props = data['features'][0].get('properties', {})
                
                # Extract main properties (excluding _metadata)
                for key, value in feature_props.items():
                    if key != '_metadata':
                        properties[key] = value
                        self.property_analysis['unique_properties'].add(key)
                        self.property_analysis['property_stats'][key] += 1
                
                # Extract layer info from metadata
                metadata = feature_props.get('_metadata', {})
                layer_name = metadata.get('layer_name', 'unknown')
                zoom_level = metadata.get('zoom_level', 'unknown')
                
                # Store layer-specific properties
                self.property_analysis['layer_properties'][layer_name].update(properties.keys())
                
                return {
                    'file_path': str(file_path),
                    'layer_name': layer_name,
                    'zoom_level': zoom_level,
                    'properties': properties,
                    'property_keys': sorted(properties.keys()),
                    'metadata': metadata,
                    'file_size': file_path.stat().st_size
                }
                
        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
            return None
    
    def generate_property_hash(self, file_info):
        """Generate hash based on key properties for duplicate detection"""
        if not file_info:
            return None
            
        # Create hash based on critical identifying properties
        hash_data = {
            'layer_name': file_info.get('layer_name'),
            'zoom_level': file_info.get('zoom_level'),
        }
        
        # Add key identifying properties based on layer type
        properties = file_info.get('properties', {})
        
        # Common identifying properties across layers
        identifying_props = [
            'fid', 'objectid', 'id', 'uid',  # IDs
            'cadastral_number', 'kadastr',   # Cadastral identifiers
            'mahalla_code', 'district',      # Geographic identifiers
            'soato_region', 'soato_district' # Administrative codes
        ]
        
        for prop in identifying_props:
            if prop in properties and properties[prop] is not None:
                hash_data[prop] = properties[prop]
        
        # Generate hash
        hash_string = json.dumps(hash_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(hash_string.encode('utf-8')).hexdigest()
    
    def find_duplicates(self):
        """Find duplicate files based on property analysis"""
        logger.info("Starting comprehensive duplicate detection...")
        
        file_hashes = defaultdict(list)
        all_files = []
        
        # Scan all GeoJSON files
        for layer_dir in self.data_dir.iterdir():
            if layer_dir.is_dir() and not layer_dir.name.startswith('.'):
                logger.info(f"Processing layer: {layer_dir.name}")
                
                for geojson_file in layer_dir.glob("*.geojson"):
                    file_info = self.analyze_file_properties(geojson_file)
                    if file_info:
                        all_files.append(file_info)
                        
                        # Generate hash for duplicate detection
                        prop_hash = self.generate_property_hash(file_info)
                        if prop_hash:
                            file_hashes[prop_hash].append(file_info)
                        
                        self.files_processed += 1
                        
                        if self.files_processed % 1000 == 0:
                            logger.info(f"Processed {self.files_processed} files...")
        
        # Identify duplicates
        for prop_hash, file_list in file_hashes.items():
            if len(file_list) > 1:
                # Sort by file size to keep the largest (most complete) version
                file_list.sort(key=lambda x: x['file_size'], reverse=True)
                
                # First file is kept, rest are duplicates
                primary_file = file_list[0]
                duplicate_files = file_list[1:]
                
                self.duplicates.extend(duplicate_files)
                
                logger.info(f"Found {len(duplicate_files)} duplicates for hash {prop_hash[:8]}...")
        
        return all_files
    
    def backup_duplicates(self):
        """Backup duplicate files before removal"""
        if not self.duplicates:
            return
            
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        
        logger.info(f"Backing up {len(self.duplicates)} duplicate files...")
        
        for duplicate in self.duplicates:
            src_path = Path(duplicate['file_path'])
            backup_path = self.backup_dir / src_path.name
            
            # Handle name conflicts in backup
            counter = 1
            while backup_path.exists():
                backup_path = self.backup_dir / f"{src_path.stem}_{counter}{src_path.suffix}"
                counter += 1
            
            shutil.copy2(src_path, backup_path)
    
    def remove_duplicates(self):
        """Remove duplicate files after backing up"""
        if not self.duplicates:
            logger.info("No duplicates found to remove.")
            return 0
        
        self.backup_duplicates()
        
        space_saved = 0
        removed_count = 0
        
        for duplicate in self.duplicates:
            try:
                file_path = Path(duplicate['file_path'])
                file_size = file_path.stat().st_size
                file_path.unlink()
                space_saved += file_size
                removed_count += 1
                
            except Exception as e:
                logger.error(f"Error removing {duplicate['file_path']}: {e}")
        
        logger.info(f"Successfully removed {removed_count} duplicate files")
        logger.info(f"Space saved: {space_saved / (1024*1024):.2f} MB")
        
        return space_saved
    
    def analyze_unique_properties(self):
        """Analyze and report on unique properties found"""
        logger.info("\n" + "="*60)
        logger.info("UNIQUE PROPERTIES ANALYSIS")
        logger.info("="*60)
        
        # Report all unique properties found
        logger.info(f"\nTotal unique properties found: {len(self.property_analysis['unique_properties'])}")
        logger.info("\nAll unique properties:")
        for prop in sorted(self.property_analysis['unique_properties']):
            count = self.property_analysis['property_stats'][prop]
            logger.info(f"  - {prop}: appears in {count} files")
        
        # Report properties by layer
        logger.info(f"\nProperties by layer type:")
        for layer, properties in self.property_analysis['layer_properties'].items():
            logger.info(f"\n{layer}:")
            for prop in sorted(properties):
                logger.info(f"  - {prop}")
        
        # Identify common properties across layers
        all_layers = list(self.property_analysis['layer_properties'].keys())
        if len(all_layers) > 1:
            common_props = set.intersection(*[
                self.property_analysis['layer_properties'][layer] 
                for layer in all_layers
            ])
            logger.info(f"\nCommon properties across all layers ({len(common_props)}):")
            for prop in sorted(common_props):
                logger.info(f"  - {prop}")
        
        return {
            'total_unique_properties': len(self.property_analysis['unique_properties']),
            'all_properties': sorted(self.property_analysis['unique_properties']),
            'layer_properties': {k: sorted(v) for k, v in self.property_analysis['layer_properties'].items()},
            'property_frequency': dict(self.property_analysis['property_stats'])
        }
    
    def generate_report(self, all_files, space_saved):
        """Generate comprehensive deduplication report"""
        processing_time = time.time() - self.start_time
        
        # Analyze unique properties
        property_analysis = self.analyze_unique_properties()
        
        # Layer statistics
        layer_stats = defaultdict(int)
        for file_info in all_files:
            layer_stats[file_info['layer_name']] += 1
        
        report = {
            'deduplication_summary': {
                'total_files_scanned': self.files_processed,
                'duplicates_found': len(self.duplicates),
                'duplicates_removed': len(self.duplicates),
                'unique_files_kept': self.files_processed - len(self.duplicates),
                'layers_processed': len(layer_stats),
                'space_saved_mb': space_saved / (1024*1024),
                'processing_time_minutes': processing_time / 60
            },
            'property_analysis': property_analysis,
            'layer_statistics': dict(layer_stats),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'backup_location': str(self.backup_dir) if self.duplicates else None
        }
        
        # Save detailed report
        report_path = self.data_dir / "comprehensive_deduplication_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Save simple summary for compatibility
        summary_path = self.data_dir / "deduplication_report.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(report['deduplication_summary'], f, indent=2)
        
        logger.info(f"\nDetailed report saved to: {report_path}")
        logger.info(f"Summary report saved to: {summary_path}")
        
        return report

def main():
    """Main execution function"""
    script_dir = Path(__file__).parent
    data_dir = script_dir / "jizzax_cadastral_data"
    
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return
    
    logger.info("Starting Comprehensive Cadastral Data Deduplication")
    logger.info(f"Data directory: {data_dir}")
    logger.info("="*60)
    
    # Initialize deduplicator
    deduplicator = ComprehensiveDeduplicator(data_dir)
    
    # Find duplicates and analyze properties
    all_files = deduplicator.find_duplicates()
    
    # Remove duplicates
    space_saved = deduplicator.remove_duplicates()
    
    # Generate comprehensive report
    report = deduplicator.generate_report(all_files, space_saved)
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("DEDUPLICATION COMPLETE")
    logger.info("="*60)
    summary = report['deduplication_summary']
    logger.info(f"Files processed: {summary['total_files_scanned']}")
    logger.info(f"Duplicates found: {summary['duplicates_found']}")
    logger.info(f"Duplicates removed: {summary['duplicates_removed']}")
    logger.info(f"Unique files kept: {summary['unique_files_kept']}")
    logger.info(f"Layers processed: {summary['layers_processed']}")
    logger.info(f"Space saved: {summary['space_saved_mb']:.2f} MB")
    logger.info(f"Processing time: {summary['processing_time_minutes']:.2f} minutes")
    
    property_analysis = report['property_analysis']
    logger.info(f"Unique properties found: {property_analysis['total_unique_properties']}")
    
    if summary['duplicates_removed'] > 0:
        logger.info(f"Backup location: {report['backup_location']}")

if __name__ == "__main__":
    main()
