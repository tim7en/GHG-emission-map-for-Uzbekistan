# Cadastral Polygon Downloader for Uzbekistan NGIS Data

This tool processes captured API requests from the Uzbekistan National GIS system and downloads polygon data as individual GeoJSON files.

## 📋 Overview

The captured JSON file contains API requests to the Uzbekistan National GIS system (`db.ngis.uz`). This tool:

1. **Extracts unique API URLs** from the captured requests
2. **Downloads polygon data** from those URLs 
3. **Converts to GeoJSON format** (from Esri JSON if needed)
4. **Saves individual polygon files** with their properties
5. **Generates comprehensive reports** on the download process

## 🚀 Quick Start

### Prerequisites
```bash
pip install requests
```

### Basic Usage
```bash
python run_polygon_download.py
```

### Advanced Usage
```python
from cadastral_polygon_downloader import CadastralPolygonDownloader

# Initialize downloader
downloader = CadastralPolygonDownloader(
    input_json_file="path/to/captured_data.json",
    output_dir="output_directory"
)

# Run download process
report = downloader.run_download_process(delay_seconds=2.0)
print(report)
```

## 📁 File Structure

```
cadastral_polygons_output/
├── geojson_files/           # Individual polygon GeoJSON files
│   ├── UZKAD_ALL_SPUNIT_NORES_LAND_12345_001_20250816_143022.geojson
│   ├── UZKAD_ALL_SPUNIT_NORES_LAND_12346_002_20250816_143023.geojson
│   └── ...
├── logs/                    # Download logs and reports
│   ├── download_report_20250816_143045.md
│   └── polygon_download.log
```

## 📊 Output Format

Each GeoJSON file contains:

```json
{
  "type": "FeatureCollection",
  "metadata": {
    "source": "Uzbekistan National GIS",
    "download_timestamp": "2025-08-16T14:30:22.123456",
    "layer_name": "UZKAD_ALL_SPUNIT_NORES_LAND",
    "zoom_level": 14,
    "geometry_bounds": {
      "xmin": 7709744.420951024,
      "ymin": 5063188.753611738,
      "xmax": 7710355.917177305,
      "ymax": 5063800.249838019
    }
  },
  "features": [
    {
      "type": "Feature",
      "properties": {
        "cadastral_number": "12345",
        "objectid": 1,
        "property_kind": "residential"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[lon1, lat1], [lon2, lat2], ...]]
      }
    }
  ]
}
```

## 🛠️ Technical Details

### Data Source Analysis
- **Source**: Uzbekistan National GIS (db.ngis.uz)
- **Layer**: `UZKAD_ALL_SPUNIT_NORES_LAND` (Cadastral land units)
- **Format**: Original requests use PBF format, converted to GeoJSON
- **Properties**: 
  - `cadastral_number`: Property identifier
  - `objectid`: Database object ID
  - `property_kind`: Type of property (residential, commercial, etc.)

### URL Processing
The tool modifies captured URLs by:
1. Changing format from `f=pbf` to `f=geojson`
2. Adding `returnGeometry=true` parameter
3. Preserving authentication tokens and spatial filters

### Coordinate System
- **Source CRS**: Web Mercator (EPSG:3857)
- **Output CRS**: WGS84 Geographic (EPSG:4326) via GeoJSON standard

## ⚙️ Configuration Options

### Download Parameters
```python
CadastralPolygonDownloader(
    input_json_file="captured_data.json",    # Input file path
    output_dir="output_folder",              # Output directory
)

# Process configuration
downloader.run_download_process(
    delay_seconds=2.0                        # Delay between requests
)
```

### Logging Configuration
- **Console output**: Progress and summary information
- **Log file**: Detailed operation logs
- **Error tracking**: Failed requests and reasons

## 📈 Performance Considerations

### Request Rate Limiting
- Default delay: 2 seconds between requests
- Prevents server overload
- Configurable based on server capacity

### File Organization
- Individual files for each polygon feature
- Timestamped filenames prevent overwrites
- Organized directory structure for easy navigation

### Error Handling
- Timeout handling (30 seconds per request)
- Network error recovery
- Invalid response detection
- Comprehensive error logging

## 🔍 Troubleshooting

### Common Issues

1. **"No valid URLs found"**
   - Check if the JSON file contains `f=pbf` requests
   - Verify the file is not corrupted

2. **"Request failed" errors**
   - Check internet connection
   - Verify the NGIS server is accessible
   - Check if authentication tokens are still valid

3. **"JSON decode failed"**
   - Server might be returning non-JSON response
   - Check if the URL format is correct

### Debug Mode
Enable detailed logging:
```python
import logging
logging.getLogger('cadastral_polygon_downloader').setLevel(logging.DEBUG)
```

## 📋 Sample Report

```
# CADASTRAL POLYGON DOWNLOAD REPORT
Generated: 2025-08-16T14:30:45.123456

## DOWNLOAD STATISTICS
- Total API requests processed: 529
- Unique URLs extracted: 47
- Successful downloads: 45
- Failed downloads: 2
- Total polygons downloaded: 1,247

## SUCCESS RATE
- Download success rate: 95.7%

## OUTPUT LOCATION
- GeoJSON files directory: cadastral_polygons_output/geojson_files
- Log files directory: cadastral_polygons_output/logs
```

## 🔒 Ethical Usage

This tool is designed for:
- ✅ Research and academic purposes
- ✅ Open data initiatives
- ✅ Geographic analysis and mapping
- ✅ Educational use

Please ensure compliance with:
- Terms of service of the data provider
- Local data protection regulations
- Intellectual property rights

## 📞 Support

For issues or questions:
1. Check the log files for detailed error information
2. Review the troubleshooting section above
3. Ensure all dependencies are properly installed

---

**Note**: This tool processes publicly accessible API endpoints. Ensure you have appropriate permissions to access and use the data according to the terms of service of the Uzbekistan National GIS system.
