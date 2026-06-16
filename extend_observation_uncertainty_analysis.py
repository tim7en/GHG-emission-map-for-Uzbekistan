#!/usr/bin/env python3
"""Extend atmospheric observations and compute annual uncertainty metrics.

This utility reuses the existing 10-city Sentinel-5P sampling approach,
appends missing monthly observations after the repository snapshot, and writes
year-by-year uncertainty metrics from the first observation through the target
end month.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List

import ee
import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parent
SOURCE_CSV = REPO_ROOT / "outputs" / "comprehensive_analytics" / "time_series_data_2017_2024.csv"
OUTPUT_DIR = REPO_ROOT / "outputs" / "extended_uncertainty_analysis"
REFERENCE_UNCERTAINTY = REPO_ROOT / "outputs" / "minimal_scientific_analysis" / "uncertainty_results.json"


CITIES: Dict[str, dict] = {
    "Tashkent": {"coords": [69.2401, 41.2995], "population": 2500000, "type": "Capital", "region": "Tashkent"},
    "Samarkand": {"coords": [66.9597, 39.6270], "population": 520000, "type": "Historic", "region": "Samarkand"},
    "Namangan": {"coords": [71.6726, 40.9983], "population": 480000, "type": "Industrial", "region": "Fergana Valley"},
    "Andijan": {"coords": [72.3442, 40.7821], "population": 450000, "type": "Industrial", "region": "Fergana Valley"},
    "Bukhara": {"coords": [64.4207, 39.7747], "population": 280000, "type": "Historic", "region": "Central"},
    "Nukus": {"coords": [59.6103, 42.4531], "population": 260000, "type": "Regional", "region": "Karakalpakstan"},
    "Qarshi": {"coords": [65.7887, 38.8569], "population": 240000, "type": "Regional", "region": "Kashkadarya"},
    "Kokand": {"coords": [70.9428, 40.5258], "population": 230000, "type": "Historic", "region": "Fergana Valley"},
    "Urgench": {"coords": [60.6348, 41.5500], "population": 150000, "type": "Regional", "region": "Khorezm"},
    "Margilan": {"coords": [71.7246, 40.4731], "population": 140000, "type": "Industrial", "region": "Fergana Valley"},
}

DATASETS: Dict[str, dict] = {
    "NO2": {
        "collection": "COPERNICUS/S5P/OFFL/L3_NO2",
        "band": "tropospheric_NO2_column_number_density",
        "scale": 5000,
        "unit": "mol/m^2",
    },
    "CO": {
        "collection": "COPERNICUS/S5P/OFFL/L3_CO",
        "band": "CO_column_number_density",
        "scale": 5000,
        "unit": "mol/m^2",
    },
    "CH4": {
        "collection": "COPERNICUS/S5P/OFFL/L3_CH4",
        "band": "CH4_column_volume_mixing_ratio_dry_air",
        "scale": 5000,
        "unit": "ppb",
    },
}


@dataclass(frozen=True)
class MonthWindow:
    start: date
    end: date


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--end-year", type=int, default=2026, help="Final year to analyze.")
    parser.add_argument("--end-month", type=int, default=5, help="Final complete month to analyze.")
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Ignore existing extended CSV and fetch missing months again from the source CSV cutoff.",
    )
    return parser.parse_args()


def iter_month_windows(start_year: int, start_month: int, end_year: int, end_month: int) -> Iterable[MonthWindow]:
    current_year = start_year
    current_month = start_month
    while (current_year, current_month) <= (end_year, end_month):
        start = date(current_year, current_month, 1)
        if current_month == 12:
            next_year = current_year + 1
            next_month = 1
        else:
            next_year = current_year
            next_month = current_month + 1
        yield MonthWindow(start=start, end=date(next_year, next_month, 1))
        current_year = next_year
        current_month = next_month


def month_start_from_timestamp(ts: pd.Timestamp) -> tuple[int, int]:
    return ts.year, ts.month


def next_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


def initialize_gee() -> None:
    ee.Initialize(project="ee-sabitovty")


def build_city_collection() -> ee.FeatureCollection:
    features = []
    for city_name, city_info in CITIES.items():
        lon, lat = city_info["coords"]
        features.append(
            ee.Feature(
                ee.Geometry.Point([lon, lat]),
                {
                    "city": city_name,
                    "lon": lon,
                    "lat": lat,
                    "population": city_info["population"],
                    "type": city_info["type"],
                    "region": city_info["region"],
                },
            )
        )
    return ee.FeatureCollection(features)


def load_existing_data(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path)
    data["date"] = pd.to_datetime(data["date"])
    return data


def collect_monthly_observations(start_year: int, start_month: int, end_year: int, end_month: int) -> pd.DataFrame:
    initialize_gee()
    city_collection = build_city_collection()
    uzbekistan_bounds = ee.Geometry.Rectangle([55.9, 37.2, 73.2, 45.6])

    records: List[dict] = []
    months = list(iter_month_windows(start_year, start_month, end_year, end_month))
    total_steps = len(months) * len(DATASETS)
    step = 0

    for window in months:
        for gas, config in DATASETS.items():
            step += 1
            print(f"Collecting {gas} for {window.start:%Y-%m} ({step}/{total_steps})")
            collection = (
                ee.ImageCollection(config["collection"])
                .filterDate(window.start.isoformat(), window.end.isoformat())
                .filterBounds(uzbekistan_bounds)
                .select(config["band"])
            )

            count = collection.size().getInfo()
            if count <= 0:
                continue

            sampled = collection.mean().sampleRegions(
                collection=city_collection,
                scale=config["scale"],
                projection="EPSG:4326",
            )
            features = sampled.getInfo().get("features", [])
            for feature in features:
                props = feature.get("properties", {})
                concentration = props.get(config["band"])
                if concentration is None:
                    continue
                records.append(
                    {
                        "date": f"{window.start.year}-{window.start.month:02d}-15",
                        "year": window.start.year,
                        "month": window.start.month,
                        "city": props["city"],
                        "gas": gas,
                        "concentration": concentration,
                        "longitude": props["lon"],
                        "latitude": props["lat"],
                        "population": props["population"],
                        "city_type": props["type"],
                        "region": props["region"],
                        "data_points": count,
                    }
                )

    result = pd.DataFrame(records)
    if not result.empty:
        result["date"] = pd.to_datetime(result["date"])
    return result


def expected_months_for_year(year: int, min_date: pd.Timestamp, max_date: pd.Timestamp) -> int:
    start_month = 1
    end_month = 12
    if year == min_date.year:
        start_month = min_date.month
    if year == max_date.year:
        end_month = max_date.month
    return max(0, end_month - start_month + 1)


def compute_annual_uncertainty_metrics(data: pd.DataFrame) -> pd.DataFrame:
    rows: List[dict] = []
    min_date = data["date"].min()
    max_date = data["date"].max()
    total_cities = data["city"].nunique()

    for gas in sorted(data["gas"].unique()):
        gas_data = data[data["gas"] == gas].copy()
        for year in sorted(gas_data["year"].unique()):
            year_data = gas_data[gas_data["year"] == year].copy()
            if year_data.empty:
                continue

            mean_concentration = float(year_data["concentration"].mean())
            std_concentration = float(year_data["concentration"].std(ddof=1)) if len(year_data) > 1 else 0.0
            sem = std_concentration / np.sqrt(len(year_data)) if len(year_data) > 1 else 0.0
            ci95_lower = mean_concentration - 1.96 * sem
            ci95_upper = mean_concentration + 1.96 * sem

            city_std = year_data.groupby("city")["concentration"].std()
            temporal_cv = float(city_std.mean() / mean_concentration * 100) if mean_concentration else np.nan

            city_means = year_data.groupby("city")["concentration"].mean()
            spatial_cv = float(city_means.std(ddof=1) / city_means.mean() * 100) if len(city_means) > 1 and city_means.mean() else np.nan

            monthly_means = year_data.groupby("month")["concentration"].mean()
            monthly_cv = float(monthly_means.std(ddof=1) / monthly_means.mean() * 100) if len(monthly_means) > 1 and monthly_means.mean() else np.nan

            annual_means_to_date = gas_data[gas_data["year"] <= year].groupby("year")["concentration"].mean()
            running_interannual_cv = float(annual_means_to_date.std(ddof=1) / annual_means_to_date.mean() * 100) if len(annual_means_to_date) > 1 and annual_means_to_date.mean() else np.nan

            expected_months = expected_months_for_year(year, min_date, max_date)
            actual_city_months = year_data[["city", "month"]].drop_duplicates().shape[0]
            expected_city_months = expected_months * total_cities if expected_months else 0
            completeness_pct = float(actual_city_months / expected_city_months * 100) if expected_city_months else np.nan

            rows.append(
                {
                    "gas": gas,
                    "year": int(year),
                    "measurement_count": int(len(year_data)),
                    "cities_covered": int(year_data["city"].nunique()),
                    "months_covered": int(year_data["month"].nunique()),
                    "expected_months_in_window": int(expected_months),
                    "completeness_percent": completeness_pct,
                    "mean_concentration": mean_concentration,
                    "std_concentration": std_concentration,
                    "temporal_cv_percent": temporal_cv,
                    "spatial_cv_percent": spatial_cv,
                    "monthly_cv_percent": monthly_cv,
                    "running_interannual_cv_percent": running_interannual_cv,
                    "ci95_lower": ci95_lower,
                    "ci95_upper": ci95_upper,
                }
            )

    return pd.DataFrame(rows)


def compute_summary(annual_metrics: pd.DataFrame, combined_data: pd.DataFrame, reference_uncertainty: dict) -> dict:
    summary = {
        "observation_window": {
            "start": combined_data["date"].min().strftime("%Y-%m-%d"),
            "end": combined_data["date"].max().strftime("%Y-%m-%d"),
            "total_measurements": int(len(combined_data)),
            "cities": int(combined_data["city"].nunique()),
        },
        "gas_summaries": {},
        "reference_inventory_uncertainty_2022": reference_uncertainty.get("inventory", {}),
        "note_on_regional_factors": "Current regional emission factors in this repo are static 2022 factors; they are not year-specific unless annual spatial emission rasters are generated.",
    }

    for gas in sorted(annual_metrics["gas"].unique()):
        gas_metrics = annual_metrics[annual_metrics["gas"] == gas].copy()
        latest = gas_metrics.sort_values("year").iloc[-1].to_dict()
        uncertainty_trend = {}
        if len(gas_metrics) >= 3:
            years = gas_metrics["year"].to_numpy(dtype=float)
            for key in ["temporal_cv_percent", "spatial_cv_percent", "monthly_cv_percent", "running_interannual_cv_percent"]:
                valid = gas_metrics[["year", key]].dropna()
                if len(valid) >= 3:
                    uncertainty_trend[key] = float(np.polyfit(valid["year"], valid[key], 1)[0])
        summary["gas_summaries"][gas] = {
            "latest_year": int(latest["year"]),
            "latest_metrics": latest,
            "mean_temporal_cv_percent": float(gas_metrics["temporal_cv_percent"].mean(skipna=True)),
            "mean_spatial_cv_percent": float(gas_metrics["spatial_cv_percent"].mean(skipna=True)),
            "mean_monthly_cv_percent": float(gas_metrics["monthly_cv_percent"].mean(skipna=True)),
            "uncertainty_trend_per_year": uncertainty_trend,
        }

    return summary


def main() -> None:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    base_data = load_existing_data(SOURCE_CSV)
    output_csv = OUTPUT_DIR / "time_series_data_2018_2026_extended.csv"
    if output_csv.exists() and not args.force_refresh:
        combined_data = pd.read_csv(output_csv)
        combined_data["date"] = pd.to_datetime(combined_data["date"])
    else:
        last_existing_date = base_data["date"].max()
        fetch_start_year, fetch_start_month = next_month(*month_start_from_timestamp(last_existing_date))
        if (fetch_start_year, fetch_start_month) <= (args.end_year, args.end_month):
            new_data = collect_monthly_observations(fetch_start_year, fetch_start_month, args.end_year, args.end_month)
            combined_data = pd.concat([base_data, new_data], ignore_index=True)
        else:
            combined_data = base_data.copy()

        combined_data = combined_data.drop_duplicates(subset=["date", "city", "gas"]).sort_values(["date", "gas", "city"])
        combined_data.to_csv(output_csv, index=False)
        print(f"Wrote {output_csv}")

    annual_metrics = compute_annual_uncertainty_metrics(combined_data)
    annual_csv = OUTPUT_DIR / "annual_uncertainty_metrics_2018_2026.csv"
    annual_metrics.to_csv(annual_csv, index=False)
    print(f"Wrote {annual_csv}")

    reference_uncertainty = {}
    if REFERENCE_UNCERTAINTY.exists():
        with REFERENCE_UNCERTAINTY.open("r", encoding="utf-8") as handle:
            reference_uncertainty = json.load(handle)

    summary = compute_summary(annual_metrics, combined_data, reference_uncertainty)
    summary_json = OUTPUT_DIR / "annual_uncertainty_summary_2018_2026.json"
    with summary_json.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(f"Wrote {summary_json}")

    for gas in sorted(annual_metrics["gas"].unique()):
        gas_metrics = annual_metrics[annual_metrics["gas"] == gas].sort_values("year")
        latest = gas_metrics.iloc[-1]
        print(
            f"{gas} latest year {int(latest['year'])}: temporal_cv={latest['temporal_cv_percent']:.2f}%, "
            f"spatial_cv={latest['spatial_cv_percent']:.2f}%, monthly_cv={latest['monthly_cv_percent']:.2f}%"
        )


if __name__ == "__main__":
    main()