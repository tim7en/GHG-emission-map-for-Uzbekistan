#!/usr/bin/env python3
"""Google Earth Engine air-pollutant analysis for Jizzakh, Uzbekistan.

Creates a self-contained output folder containing annual statistics, satellite
metadata, trend figures, pollutant maps, and a Markdown report. Satellite
columns are not converted to surface concentrations or AQI.
"""

from __future__ import annotations

import json
import argparse
import time
from datetime import date, datetime
from pathlib import Path

import ee
import matplotlib.pyplot as plt
import pandas as pd
import requests


PROJECT = "ee-sabitovty"
START_YEAR = 2016
END_YEAR = 2025  # ten complete calendar years
CITY_LON_LAT = (67.8422, 40.1158)
CITY_RADIUS_M = 10_000
OUT = Path("outputs/jizzakh_air_quality_2016_2025")
MAPS = OUT / "maps"

POLLUTANTS = {
    "NO2": {
        "collection": "COPERNICUS/S5P/OFFL/L3_NO2",
        "band": "tropospheric_NO2_column_number_density",
        "name": "Tropospheric nitrogen dioxide",
        "unit": "mol/m^2",
        "palette": ["081d58", "225ea8", "41b6c4", "c7e9b4", "ffffd9", "fd8d3c", "bd0026"],
    },
    "CO": {
        "collection": "COPERNICUS/S5P/OFFL/L3_CO",
        "band": "CO_column_number_density",
        "name": "Carbon monoxide total column",
        "unit": "mol/m^2",
        "palette": ["0d0887", "7e03a8", "cc4778", "f89540", "f0f921"],
    },
    "SO2": {
        "collection": "COPERNICUS/S5P/OFFL/L3_SO2",
        "band": "SO2_column_number_density",
        "name": "Sulfur dioxide column",
        "unit": "mol/m^2",
        "palette": ["313695", "74add1", "e0f3f8", "ffffbf", "f46d43", "a50026"],
    },
    "O3": {
        "collection": "COPERNICUS/S5P/OFFL/L3_O3",
        "band": "O3_column_number_density",
        "name": "Ozone total column",
        "unit": "mol/m^2",
        "palette": ["440154", "31688e", "35b779", "fde725"],
    },
    "HCHO": {
        "collection": "COPERNICUS/S5P/OFFL/L3_HCHO",
        "band": "tropospheric_HCHO_column_number_density",
        "name": "Tropospheric formaldehyde",
        "unit": "mol/m^2",
        "palette": ["2c7bb6", "abd9e9", "ffffbf", "fdae61", "d7191c"],
    },
    "CH4": {
        "collection": "COPERNICUS/S5P/OFFL/L3_CH4",
        "band": "CH4_column_volume_mixing_ratio_dry_air",
        "name": "Methane dry-air mixing ratio",
        "unit": "ppb",
        "palette": ["ffffcc", "a1dab4", "41b6c4", "2c7fb8", "253494"],
    },
    "AER_AI": {
        "collection": "COPERNICUS/S5P/OFFL/L3_AER_AI",
        "band": "absorbing_aerosol_index",
        "name": "UV absorbing aerosol index",
        "unit": "dimensionless",
        "palette": ["313695", "74add1", "ffffbf", "f46d43", "a50026"],
    },
}


def get_study_areas():
    adm1 = ee.FeatureCollection("FAO/GAUL/2015/level1")
    uzb = adm1.filter(ee.Filter.eq("ADM0_NAME", "Uzbekistan"))
    names = uzb.aggregate_array("ADM1_NAME").getInfo()
    matches = [n for n in names if "jizz" in n.lower() or "djizz" in n.lower()]
    if not matches:
        raise RuntimeError(f"Jizzakh boundary not found in GAUL. Available names: {names}")
    region_feature = uzb.filter(ee.Filter.eq("ADM1_NAME", matches[0])).first()
    region = ee.Feature(region_feature).geometry()
    city = ee.Geometry.Point(CITY_LON_LAT).buffer(CITY_RADIUS_M)
    return matches[0], {"Jizzakh Region": region, "Jizzakh City (10 km radius)": city}


def safe_number(value):
    return None if value is None else float(value)


def analyze(areas):
    rows, metadata, composites = [], {}, {}
    area_fc = ee.FeatureCollection([
        ee.Feature(geom, {"area": area_name}) for area_name, geom in areas.items()
    ])
    for code, cfg in POLLUTANTS.items():
        base = (ee.ImageCollection(cfg["collection"])
                .filterBounds(areas["Jizzakh Region"]).select(cfg["band"]))
        annual_images, annual_collections = [], []
        for year in range(START_YEAR, END_YEAR + 1):
            annual = base.filterDate(f"{year}-01-01", f"{year + 1}-01-01")
            count = annual.size()
            image = annual.mean().rename(code)
            reduced = image.reduceRegions(
                collection=area_fc,
                reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True),
                scale=5000,
            ).map(lambda f, y=year, c=count: ee.Feature(f).set({
                "year": y, "image_count": c, "status": "available"
            }))
            missing = area_fc.map(lambda f, y=year: ee.Feature(f).set({
                "year": y, "image_count": 0, "status": "not_available"
            }))
            annual_collections.append(ee.FeatureCollection(ee.Algorithms.If(count.gt(0), reduced, missing)))
            annual_images.append(ee.Image(ee.Algorithms.If(count.gt(0), image, ee.Image.constant(0).rename(code).updateMask(ee.Image.constant(0)))))

        payload = ee.Dictionary({
            "collection_start": ee.Date(base.aggregate_min("system:time_start")).format("YYYY-MM-dd"),
            "collection_end": ee.Date(base.aggregate_max("system:time_start")).format("YYYY-MM-dd"),
            "features": ee.FeatureCollection(annual_collections).flatten().toList(100).map(lambda f: ee.Feature(f).toDictionary()),
        }).getInfo()
        collection_start = payload["collection_start"]
        collection_end = payload["collection_end"]
        metadata[code] = {
            **{k: v for k, v in cfg.items() if k != "palette"},
            "platform": "Sentinel-5P",
            "instrument": "TROPOMI",
            "product_level": "Earth Engine OFFL Level 3",
            "earth_engine_collection_start": collection_start,
            "earth_engine_collection_end": collection_end,
            "earth_engine_level3_projection": "EPSG:4326, 0.01 degree grid",
            "nominal_pixel_size_m": 1113.2,
            "temporal_aggregation": "mean of all available images in each calendar year",
            "spatial_statistic": "mean of annual composite pixels in study area",
        }
        for result in payload["features"]:
            mean_value = safe_number(result.get(f"{code}_mean"))
            result_status = result["status"] if mean_value is not None else (
                "no_valid_pixels" if int(result["image_count"]) > 0 else "not_available"
            )
            rows.append({
                "year": int(result["year"]), "area": result["area"], "pollutant": code,
                "description": cfg["name"], "unit": cfg["unit"],
                "mean": mean_value,
                "spatial_stddev": safe_number(result.get(f"{code}_stdDev")),
                "image_count": int(result["image_count"]), "status": result_status,
            })
        composites[code] = base.filterDate(f"{END_YEAR}-01-01", f"{END_YEAR + 1}-01-01").mean().rename(code)
        print(f"Processed {code}", flush=True)
    return pd.DataFrame(rows), metadata, composites


def download_maps(composites, region, metadata):
    map_records = []
    bounds = region.bounds().getInfo()["coordinates"]
    for code, image in composites.items():
        stats = image.reduceRegion(
            ee.Reducer.percentile([2, 98]), region, 5000,
            bestEffort=True, maxPixels=1_000_000_000
        ).getInfo()
        lo, hi = stats.get(f"{code}_p2"), stats.get(f"{code}_p98")
        if lo is None or hi is None or lo == hi:
            continue
        url = image.clip(region).getThumbURL({
            "region": bounds, "dimensions": 350, "format": "png",
            "min": lo, "max": hi, "palette": POLLUTANTS[code]["palette"],
        })
        path = MAPS / f"{code}_mean_{END_YEAR}_jizzakh_region.png"
        already_exists = path.exists() and path.stat().st_size > 0
        response = None
        last_error = None
        for attempt in range(0 if already_exists else 1):
            try:
                response = requests.get(url, timeout=120)
                response.raise_for_status()
                break
            except requests.RequestException as exc:
                last_error = str(exc)
                if attempt == 0:
                    break
                time.sleep(3 * (attempt + 1))
        if not already_exists and response is None:
            map_records.append({
                "pollutant": code, "file": None, "period": str(END_YEAR),
                "unit": metadata[code]["unit"], "render_error": last_error,
            })
            continue
        if response is not None:
            path.write_bytes(response.content)
        map_records.append({
            "pollutant": code, "file": str(path.relative_to(OUT)),
            "visualization_min_p2": lo, "visualization_max_p98": hi,
            "unit": metadata[code]["unit"], "period": str(END_YEAR),
            "note": "Annual mean; transparent pixels are outside GAUL region boundary."
        })
    return map_records


def make_charts(df):
    for code, group in df[df["status"] == "available"].groupby("pollutant"):
        fig, ax = plt.subplots(figsize=(9, 5))
        for area, values in group.groupby("area"):
            ax.plot(values["year"], values["mean"], marker="o", label=area)
        ax.set(title=f"{code}: annual satellite-column mean", xlabel="Year", ylabel=f"{code} ({group['unit'].iloc[0]})")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(MAPS / f"{code}_annual_trend_city_region.png", dpi=180)
        plt.close(fig)


def write_report(df, metadata, map_records, gaul_name):
    available = df[(df.status == "available") & df["mean"].notna()]
    summary = available.groupby(["area", "pollutant"], as_index=False).agg(
        first_year=("year", "min"), last_year=("year", "max"),
        years=("year", "nunique"), period_mean=("mean", "mean"),
        min_annual_mean=("mean", "min"), max_annual_mean=("mean", "max"), unit=("unit", "first")
    )
    summary.to_csv(OUT / "period_summary.csv", index=False)
    lines = [
        "# Jizzakh air-quality satellite analysis, 2016–2025", "",
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}", "",
        "## Executive summary", "",
        "A strict ten-complete-calendar-year window (2016–2025) was requested. The selected Sentinel-5P/TROPOMI products begin in 2018, so 2016–2017 are explicitly recorded as unavailable. The report therefore provides an eight-year satellite record where observations exist; it does not fill or simulate missing years.", "",
        "These products measure atmospheric columns (or an aerosol index), not ground-level regulatory concentrations. They cannot be compared directly with WHO ambient-air limits or interpreted as AQI without surface monitors and atmospheric modelling.", "",
        "## Study areas", "",
        f"- Jizzakh Region: FAO GAUL 2015 level-1 feature `{gaul_name}`.",
        f"- Jizzakh city: a {CITY_RADIUS_M/1000:.0f} km radius geodesic buffer around {CITY_LON_LAT[1]:.4f} N, {CITY_LON_LAT[0]:.4f} E. This is an analysis zone, not a legal city boundary.", "",
        "## Pollutants and indicators", "",
        "| Code | Measurement | Unit | Earth Engine collection | Observed coverage |", "|---|---|---:|---|---|",
    ]
    for code, meta in metadata.items():
        lines.append(f"| {code} | {meta['name']} | {meta['unit']} | `{meta['collection']}` | {meta['earth_engine_collection_start']} to {meta['earth_engine_collection_end']} |")
    lines += ["", "## Period statistics", "", "| Area | Pollutant | Years | First–last | Period mean | Annual-mean range | Unit |", "|---|---|---:|---|---:|---:|---|"]
    for _, r in summary.iterrows():
        lines.append(f"| {r.area} | {r.pollutant} | {int(r.years)} | {int(r.first_year)}–{int(r.last_year)} | {r.period_mean:.6g} | {r.min_annual_mean:.6g}–{r.max_annual_mean:.6g} | {r.unit} |")
    lines += [
        "", "## Methods", "",
        f"For each product and calendar year, all OFFL Level-3 images intersecting Jizzakh were averaged in Earth Engine. The spatial mean and spatial standard deviation of that annual composite were then computed at 5 km analysis scale for each study area. Spatial maps show the {END_YEAR} annual mean. Map colour limits use the regional 2nd and 98th percentiles.", "",
        "No quality-assurance band was applied because the Earth Engine Level-3 ingestion already masks source pixels below each product's documented QA threshold. Negative SO2/HCHO retrievals can remain and are valid retrieval noise; they were not clipped.", "",
        "## Interpretation and limitations", "",
        "- Satellite column values respond to emissions, transport, chemistry, clouds, terrain and sampling. A trend is not automatically an emissions trend.",
        "- The city circle is close to the native gridded footprint and should be treated as a local-area indicator, not street-scale exposure.",
        "- Sentinel-5P has no direct PM2.5 or PM10 concentration product. AER_AI indicates absorbing aerosols but is neither particulate mass nor AQI.",
        "- O3 is a total column product, not surface ozone. CH4 is a greenhouse gas indicator rather than a conventional local AQ pollutant.",
        "- Ground-monitor validation, meteorological normalization, seasonal analysis and uncertainty-aware trend tests are recommended before policy use.", "",
        "## Output inventory", "",
        "- `annual_city_region_statistics.csv`: annual values, image counts, and explicit no-data rows.",
        "- `period_summary.csv`: compact city/region summary.",
        "- `satellite_metadata.json`: collection, band, instrument, units, projection and processing metadata.",
        "- `maps/`: long-period spatial maps and annual city-versus-region trend figures.",
        "- `map_metadata.json`: colour limits and units for reproducible map interpretation.", "",
        "## Reproduction", "", "Run `python jizzakh_air_quality_analysis.py` from the repository root with an authenticated Earth Engine account for project `ee-sabitovty`.", "",
    ]
    (OUT / "JIZZAKH_AIR_QUALITY_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--maps-only", action="store_true", help="Reuse completed statistics and regenerate maps/report")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    MAPS.mkdir(parents=True, exist_ok=True)
    ee.Initialize(project=PROJECT)
    gaul_name, areas = get_study_areas()
    if args.maps_only:
        df = pd.read_csv(OUT / "annual_city_region_statistics.csv")
        saved_metadata = json.loads((OUT / "satellite_metadata.json").read_text(encoding="utf-8"))
        metadata = saved_metadata["datasets"]
        composites = {
            code: (ee.ImageCollection(cfg["collection"])
                   .filterDate(f"{END_YEAR}-01-01", f"{END_YEAR + 1}-01-01")
                   .filterBounds(areas["Jizzakh Region"]).select(cfg["band"]).mean().rename(code))
            for code, cfg in POLLUTANTS.items()
        }
    else:
        df, metadata, composites = analyze(areas)
        df.to_csv(OUT / "annual_city_region_statistics.csv", index=False)
        (OUT / "satellite_metadata.json").write_text(json.dumps({
            "generated_utc": datetime.utcnow().isoformat() + "Z",
            "analysis_window": [f"{START_YEAR}-01-01", f"{END_YEAR}-12-31"],
            "study_areas": {"region": f"FAO GAUL 2015 level 1: {gaul_name}", "city": {"centre_lon_lat": CITY_LON_LAT, "radius_m": CITY_RADIUS_M}},
            "datasets": metadata,
        }, indent=2), encoding="utf-8")
    map_records = download_maps(composites, areas["Jizzakh Region"], metadata)
    (OUT / "map_metadata.json").write_text(json.dumps(map_records, indent=2), encoding="utf-8")
    make_charts(df)
    write_report(df, metadata, map_records, gaul_name)
    print(f"Analysis complete: {OUT.resolve()}")


if __name__ == "__main__":
    main()
