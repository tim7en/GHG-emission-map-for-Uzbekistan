# Jizzakh air-quality satellite analysis, 2016–2025

Generated: 2026-08-07T16:48:52+05:00

## Executive summary

A strict ten-complete-calendar-year window (2016–2025) was requested. The selected Sentinel-5P/TROPOMI products begin in 2018, so 2016–2017 are explicitly recorded as unavailable. The report therefore provides an eight-year satellite record where observations exist; it does not fill or simulate missing years.

These products measure atmospheric columns (or an aerosol index), not ground-level regulatory concentrations. They cannot be compared directly with WHO ambient-air limits or interpreted as AQI without surface monitors and atmospheric modelling.

## Study areas

- Jizzakh Region: FAO GAUL 2015 level-1 feature `Jizzakh`.
- Jizzakh city: a 10 km radius geodesic buffer around 40.1158 N, 67.8422 E. This is an analysis zone, not a legal city boundary.

## Pollutants and indicators

| Code | Measurement | Unit | Earth Engine collection | Observed coverage |
|---|---|---:|---|---|
| NO2 | Tropospheric nitrogen dioxide | mol/m^2 | `COPERNICUS/S5P/OFFL/L3_NO2` | 2018-06-28 to 2026-07-28 |
| CO | Carbon monoxide total column | mol/m^2 | `COPERNICUS/S5P/OFFL/L3_CO` | 2018-07-04 to 2026-08-04 |
| SO2 | Sulfur dioxide column | mol/m^2 | `COPERNICUS/S5P/OFFL/L3_SO2` | 2018-11-28 to 2026-08-04 |
| O3 | Ozone total column | mol/m^2 | `COPERNICUS/S5P/OFFL/L3_O3` | 2018-09-08 to 2026-08-04 |
| HCHO | Tropospheric formaldehyde | mol/m^2 | `COPERNICUS/S5P/OFFL/L3_HCHO` | 2018-11-28 to 2026-08-04 |
| CH4 | Methane dry-air mixing ratio | ppb | `COPERNICUS/S5P/OFFL/L3_CH4` | 2018-11-28 to 2026-08-04 |
| AER_AI | UV absorbing aerosol index | dimensionless | `COPERNICUS/S5P/OFFL/L3_AER_AI` | 2018-06-28 to 2026-08-04 |

## Period statistics

| Area | Pollutant | Years | First–last | Period mean | Annual-mean range | Unit |
|---|---|---:|---|---:|---:|---|
| Jizzakh City (10 km radius) | AER_AI | 8 | 2018–2025 | -0.187923 | -0.965808–0.306627 | dimensionless |
| Jizzakh City (10 km radius) | CH4 | 8 | 2018–2025 | 1906.13 | 1884.96–1926.29 | ppb |
| Jizzakh City (10 km radius) | CO | 8 | 2018–2025 | 0.0321053 | 0.0300967–0.0334564 | mol/m^2 |
| Jizzakh City (10 km radius) | HCHO | 8 | 2018–2025 | 0.00010528 | 6.63737e-05–0.000119217 | mol/m^2 |
| Jizzakh City (10 km radius) | NO2 | 8 | 2018–2025 | 5.18276e-05 | 4.32297e-05–6.24635e-05 | mol/m^2 |
| Jizzakh City (10 km radius) | O3 | 8 | 2018–2025 | 0.141128 | 0.134573–0.150339 | mol/m^2 |
| Jizzakh City (10 km radius) | SO2 | 7 | 2019–2025 | 0.000179696 | 0.000136186–0.000258483 | mol/m^2 |
| Jizzakh Region | AER_AI | 8 | 2018–2025 | -0.359194 | -1.12893–0.121265 | dimensionless |
| Jizzakh Region | CH4 | 8 | 2018–2025 | 1902.16 | 1877.74–1925.77 | ppb |
| Jizzakh Region | CO | 8 | 2018–2025 | 0.0307509 | 0.028775–0.0321572 | mol/m^2 |
| Jizzakh Region | HCHO | 8 | 2018–2025 | 9.78888e-05 | 6.14474e-05–0.000109395 | mol/m^2 |
| Jizzakh Region | NO2 | 8 | 2018–2025 | 3.031e-05 | 2.61327e-05–3.41288e-05 | mol/m^2 |
| Jizzakh Region | O3 | 8 | 2018–2025 | 0.141083 | 0.134542–0.150377 | mol/m^2 |
| Jizzakh Region | SO2 | 7 | 2019–2025 | 0.000173055 | 0.000143906–0.000230171 | mol/m^2 |

## Methods

For each product and calendar year, all OFFL Level-3 images intersecting Jizzakh were averaged in Earth Engine. The spatial mean and spatial standard deviation of that annual composite were then computed at 5 km analysis scale for each study area. Spatial maps show the 2025 annual mean. Map colour limits use the regional 2nd and 98th percentiles.

No quality-assurance band was applied because the Earth Engine Level-3 ingestion already masks source pixels below each product's documented QA threshold. Negative SO2/HCHO retrievals can remain and are valid retrieval noise; they were not clipped.

## Interpretation and limitations

- Satellite column values respond to emissions, transport, chemistry, clouds, terrain and sampling. A trend is not automatically an emissions trend.
- The city circle is close to the native gridded footprint and should be treated as a local-area indicator, not street-scale exposure.
- Sentinel-5P has no direct PM2.5 or PM10 concentration product. AER_AI indicates absorbing aerosols but is neither particulate mass nor AQI.
- O3 is a total column product, not surface ozone. CH4 is a greenhouse gas indicator rather than a conventional local AQ pollutant.
- Ground-monitor validation, meteorological normalization, seasonal analysis and uncertainty-aware trend tests are recommended before policy use.

## Output inventory

- `annual_city_region_statistics.csv`: annual values, image counts, and explicit no-data rows.
- `annual_trends_table.csv`: one row per pollutant and year with paired city/region values, uncertainty fields, image counts, and quality status.
- `period_summary.csv`: compact city/region summary.
- `satellite_metadata.json`: collection, band, instrument, units, projection and processing metadata.
- `maps/`: long-period spatial maps and annual city-versus-region trend figures.
- `map_metadata.json`: colour limits and units for reproducible map interpretation.

## Reproduction

Run `python jizzakh_air_quality_analysis.py` from the repository root with an authenticated Earth Engine account for project `ee-sabitovty`.
