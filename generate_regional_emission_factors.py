#!/usr/bin/env python3
"""Generate province-level emission factors from country-wide raster outputs.

The script aggregates the existing 2 km country-wide emission rasters by
administrative region and writes factors that can be multiplied by a known
country total to estimate approximate regional emissions.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import rasterio
from rasterio.features import geometry_mask


REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_BOUNDARY_PATH = (
    REPO_ROOT.parent
    / "complete_uzbekistan_cadastral_data"
    / "VILOYAT_BORDER_2023_zoom_1"
    / "VILOYAT_BORDER_2023_zoom_1_qgis_combined.geojson"
)
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "regional_emission_factors"
COUNTRY_SUMMARY_PATH = REPO_ROOT / "outputs" / "country_wide_ghg_analysis" / "analysis_summary.json"
RASTER_DIR = REPO_ROOT / "outputs" / "country_wide_ghg_analysis" / "geotiff_maps"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--boundary-path",
        type=Path,
        default=DEFAULT_BOUNDARY_PATH,
        help="Path to the province boundary GeoJSON.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for generated factor tables.",
    )
    parser.add_argument(
        "--country-total",
        type=float,
        default=None,
        help="Optional country total to convert total factors into estimated regional emissions.",
    )
    return parser.parse_args()


def load_region_geometries(boundary_path: Path) -> Tuple[Dict[str, List[dict]], Dict[str, int]]:
    with boundary_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    regions: Dict[str, List[dict]] = defaultdict(list)
    feature_counts: Dict[str, int] = defaultdict(int)
    for feature in data.get("features", []):
        region_name = feature.get("properties", {}).get("region")
        geometry = feature.get("geometry")
        if not region_name or geometry is None:
            continue
        regions[region_name].append(geometry)
        feature_counts[region_name] += 1

    if not regions:
        raise ValueError(f"No region geometries found in {boundary_path}")

    return dict(sorted(regions.items())), dict(feature_counts)


def load_country_totals(summary_path: Path) -> Dict[str, float]:
    with summary_path.open("r", encoding="utf-8") as handle:
        summary = json.load(handle)

    raw_totals = summary.get("emissions_summary", {})
    totals: Dict[str, float] = {}
    key_map = {"CO2": "CO2", "CH4": "CH4", "CH2": "CH4", "N2O": "N2O"}

    for raw_key, mapped_key in key_map.items():
        gas_info = raw_totals.get(raw_key)
        if not gas_info:
            continue
        totals[mapped_key] = float(gas_info["total_gg_co2eq"])

    required = {"CO2", "CH4", "N2O"}
    missing = required.difference(totals)
    if missing:
        raise ValueError(f"Missing gas totals in {summary_path}: {sorted(missing)}")

    return totals


def resolve_raster_paths() -> Dict[str, Path]:
    raster_candidates = {
        "CO2": [RASTER_DIR / "UZB_GHG_CO2_2022_2km_001.tif"],
        "CH4": [
            RASTER_DIR / "UZB_GHG_CH4_2022_2km_001.tif",
            RASTER_DIR / "UZB_GHG_CH2_2022_2km_001.tif",
        ],
        "N2O": [RASTER_DIR / "UZB_GHG_N2O_2022_2km_001.tif"],
    }

    resolved: Dict[str, Path] = {}
    for gas, candidates in raster_candidates.items():
        for candidate in candidates:
            if candidate.exists():
                resolved[gas] = candidate
                break
        if gas not in resolved:
            raise FileNotFoundError(f"No raster found for {gas}: {candidates}")

    return resolved


def aggregate_raster_by_region(
    raster_path: Path,
    regions: Dict[str, List[dict]],
) -> Tuple[Dict[str, float], float, dict]:
    with rasterio.open(raster_path) as src:
        if src.count != 1:
            raise ValueError(f"Expected single-band raster, got {src.count} bands in {raster_path}")

        raster_data = src.read(1, masked=True).filled(0)
        region_sums: Dict[str, float] = {}
        for region_name, geometries in regions.items():
            mask = geometry_mask(
                geometries,
                transform=src.transform,
                invert=True,
                out_shape=src.shape,
            )
            region_sums[region_name] = float(np.where(mask, raster_data, 0).sum())

        raster_sum = float(raster_data.sum())
        region_total = float(sum(region_sums.values()))
        metadata = {
            "crs": str(src.crs),
            "shape": [src.height, src.width],
            "resolution": [src.res[0], src.res[1]],
            "raster_sum": raster_sum,
            "regional_sum": region_total,
            "regional_coverage_ratio": (region_total / raster_sum) if raster_sum else None,
        }

    return region_sums, region_total, metadata


def compute_factors(
    region_sums_by_gas: Dict[str, Dict[str, float]],
    national_totals: Dict[str, float],
) -> List[dict]:
    country_total = float(sum(national_totals.values()))
    regions = sorted(next(iter(region_sums_by_gas.values())).keys())
    rows: List[dict] = []

    for region_name in regions:
        factor_co2 = region_sums_by_gas["CO2"][region_name] / sum(region_sums_by_gas["CO2"].values())
        factor_ch4 = region_sums_by_gas["CH4"][region_name] / sum(region_sums_by_gas["CH4"].values())
        factor_n2o = region_sums_by_gas["N2O"][region_name] / sum(region_sums_by_gas["N2O"].values())

        est_co2 = factor_co2 * national_totals["CO2"]
        est_ch4 = factor_ch4 * national_totals["CH4"]
        est_n2o = factor_n2o * national_totals["N2O"]
        est_total = est_co2 + est_ch4 + est_n2o
        factor_total = est_total / country_total if country_total else 0.0

        rows.append(
            {
                "region": region_name,
                "factor_total": factor_total,
                "factor_co2": factor_co2,
                "factor_ch4": factor_ch4,
                "factor_n2o": factor_n2o,
                "estimated_total_gg_2022": est_total,
                "estimated_co2_gg_2022": est_co2,
                "estimated_ch4_gg_2022": est_ch4,
                "estimated_n2o_gg_2022": est_n2o,
            }
        )

    rows.sort(key=lambda row: row["estimated_total_gg_2022"], reverse=True)
    return rows


def write_csv(rows: List[dict], feature_counts: Dict[str, int], output_path: Path, country_total_input: float | None) -> None:
    fieldnames = [
        "region",
        "boundary_feature_count",
        "factor_total",
        "factor_co2",
        "factor_ch4",
        "factor_n2o",
        "estimated_total_gg_2022",
        "estimated_co2_gg_2022",
        "estimated_ch4_gg_2022",
        "estimated_n2o_gg_2022",
    ]
    if country_total_input is not None:
        fieldnames.append("estimated_from_input_country_total")

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            output_row = dict(row)
            output_row["boundary_feature_count"] = feature_counts[row["region"]]
            if country_total_input is not None:
                output_row["estimated_from_input_country_total"] = row["factor_total"] * country_total_input
            writer.writerow(output_row)


def write_json(
    rows: List[dict],
    feature_counts: Dict[str, int],
    national_totals: Dict[str, float],
    raster_metadata: Dict[str, dict],
    boundary_path: Path,
    raster_paths: Dict[str, Path],
    output_path: Path,
    country_total_input: float | None,
) -> None:
    payload = {
        "method": "Region shares from 2 km gas-specific emission rasters, weighted by national gas totals",
        "boundary_path": str(boundary_path),
        "raster_paths": {gas: str(path) for gas, path in raster_paths.items()},
        "national_totals_gg_2022": national_totals,
        "country_total_gg_2022": float(sum(national_totals.values())),
        "country_total_input": country_total_input,
        "notes": [
            "Use factor_total * country_total to estimate approximate regional total emissions.",
            "Gas-specific shares are derived from country-wide 2 km rasters in outputs/country_wide_ghg_analysis/geotiff_maps.",
            "The CH4 raster is stored as CH2 in the source filenames and analysis summary; this script remaps it to CH4.",
        ],
        "raster_metadata": raster_metadata,
        "regions": [],
    }

    for row in rows:
        region_payload = dict(row)
        region_payload["boundary_feature_count"] = feature_counts[row["region"]]
        if country_total_input is not None:
            region_payload["estimated_from_input_country_total"] = row["factor_total"] * country_total_input
        payload["regions"].append(region_payload)

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    regions, feature_counts = load_region_geometries(args.boundary_path)
    national_totals = load_country_totals(COUNTRY_SUMMARY_PATH)
    raster_paths = resolve_raster_paths()

    region_sums_by_gas: Dict[str, Dict[str, float]] = {}
    raster_metadata: Dict[str, dict] = {}
    for gas, raster_path in raster_paths.items():
        region_sums, _, metadata = aggregate_raster_by_region(raster_path, regions)
        region_sums_by_gas[gas] = region_sums
        raster_metadata[gas] = metadata

    rows = compute_factors(region_sums_by_gas, national_totals)

    csv_path = output_dir / "regional_emission_factors.csv"
    json_path = output_dir / "regional_emission_factors.json"
    write_csv(rows, feature_counts, csv_path, args.country_total)
    write_json(
        rows,
        feature_counts,
        national_totals,
        raster_metadata,
        args.boundary_path,
        raster_paths,
        json_path,
        args.country_total,
    )

    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print("Top 5 regions by estimated 2022 total emissions:")
    for row in rows[:5]:
        print(
            f"  {row['region']}: factor_total={row['factor_total']:.4f}, "
            f"estimated_total_gg_2022={row['estimated_total_gg_2022']:.1f}"
        )


if __name__ == "__main__":
    main()