#!/usr/bin/env python3
"""Generate annual observation-based regional proxy factors.

These factors are derived from annual Sentinel-5P concentration observations by
macro-region. They are suitable as time-varying proxy weights, not as official
inventory-grade regional emission factors.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parent
INPUT_CSV = REPO_ROOT / "outputs" / "extended_uncertainty_analysis" / "time_series_data_2018_2026_extended.csv"
UNCERTAINTY_CSV = REPO_ROOT / "outputs" / "extended_uncertainty_analysis" / "annual_uncertainty_metrics_2018_2026.csv"
OUTPUT_DIR = REPO_ROOT / "outputs" / "annual_proxy_regional_factors"


# 2022 national shares from the country-wide raster summary already used in this repo.
CO2_SHARE = 120990.86499999999 / 191092.47299999997
CH4_SHARE = 59080.349 / 191092.47299999997
N2O_SHARE = 11021.259 / 191092.47299999997

# Total proxy formula:
# 1. Use CO as the main combustion proxy and NO2 as an urban combustion sensitivity term.
# 2. Use CH4 as the proxy for methane and, lacking direct N2O observations, also for N2O.
CO_PROXY_WEIGHT = 0.8
NO2_PROXY_WEIGHT = 0.2


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    observations = pd.read_csv(INPUT_CSV)
    observations["date"] = pd.to_datetime(observations["date"])

    uncertainty = pd.read_csv(UNCERTAINTY_CSV)
    return observations, uncertainty


def compute_region_city_map(observations: pd.DataFrame) -> Dict[str, List[str]]:
    region_city_map = {}
    region_rows = observations[["region", "city"]].drop_duplicates().sort_values(["region", "city"])
    for region, group in region_rows.groupby("region"):
        region_city_map[region] = group["city"].tolist()
    return region_city_map


def compute_gas_region_factors(observations: pd.DataFrame) -> pd.DataFrame:
    city_year_gas = (
        observations.groupby(["year", "gas", "region", "city"], as_index=False)
        .agg(
            annual_mean_concentration=("concentration", "mean"),
            population=("population", "first"),
            months_covered=("month", "nunique"),
        )
    )
    city_year_gas["proxy_score"] = city_year_gas["annual_mean_concentration"] * city_year_gas["population"]

    region_year_gas = (
        city_year_gas.groupby(["year", "gas", "region"], as_index=False)
        .agg(
            proxy_score=("proxy_score", "sum"),
            cities_covered=("city", "nunique"),
            represented_population=("population", "sum"),
            region_mean_concentration=("annual_mean_concentration", "mean"),
            mean_months_covered=("months_covered", "mean"),
        )
    )

    region_year_gas["factor_gas_proxy"] = (
        region_year_gas["proxy_score"]
        / region_year_gas.groupby(["year", "gas"])["proxy_score"].transform("sum")
    )
    return region_year_gas


def pivot_factors(region_year_gas: pd.DataFrame, uncertainty: pd.DataFrame) -> pd.DataFrame:
    factor_pivot = region_year_gas.pivot(index=["year", "region"], columns="gas", values="factor_gas_proxy")
    score_pivot = region_year_gas.pivot(index=["year", "region"], columns="gas", values="proxy_score")
    concentration_pivot = region_year_gas.pivot(index=["year", "region"], columns="gas", values="region_mean_concentration")
    months_pivot = region_year_gas.pivot(index=["year", "region"], columns="gas", values="mean_months_covered")
    city_pivot = region_year_gas.pivot(index=["year", "region"], columns="gas", values="cities_covered")

    base = region_year_gas.groupby(["year", "region"], as_index=False).agg(
        represented_population=("represented_population", "max")
    )
    result = base.set_index(["year", "region"])

    for gas in ["NO2", "CO", "CH4"]:
        result[f"factor_{gas.lower()}_proxy"] = factor_pivot.get(gas)
        result[f"score_{gas.lower()}_proxy"] = score_pivot.get(gas)
        result[f"mean_{gas.lower()}_concentration"] = concentration_pivot.get(gas)
        result[f"months_{gas.lower()}_covered"] = months_pivot.get(gas)
        result[f"cities_{gas.lower()}_covered"] = city_pivot.get(gas)

    result = result.reset_index()

    result["population_share_proxy"] = (
        result["represented_population"]
        / result.groupby("year")["represented_population"].transform("sum")
    )

    result["no2_proxy_source"] = result["factor_no2_proxy"].notna().map({True: "observed", False: "co_fallback"})
    result["co_proxy_source"] = result["factor_co_proxy"].notna().map({True: "observed", False: "population_fallback"})
    result["ch4_proxy_source"] = result["factor_ch4_proxy"].notna().map({True: "observed", False: "co_fallback"})

    result["factor_co_proxy"] = result["factor_co_proxy"].fillna(result["population_share_proxy"])
    result["factor_no2_proxy"] = result["factor_no2_proxy"].fillna(result["factor_co_proxy"])
    result["factor_ch4_proxy"] = result["factor_ch4_proxy"].fillna(result["factor_co_proxy"])

    result["factor_combustion_proxy"] = (
        result["factor_co_proxy"] * CO_PROXY_WEIGHT
        + result["factor_no2_proxy"] * NO2_PROXY_WEIGHT
    )
    result["factor_total_proxy"] = (
        result["factor_combustion_proxy"] * CO2_SHARE
        + result["factor_ch4_proxy"] * (CH4_SHARE + N2O_SHARE)
    )

    # Normalize defensively within year in case of floating point drift.
    result["factor_combustion_proxy"] = (
        result["factor_combustion_proxy"]
        / result.groupby("year")["factor_combustion_proxy"].transform("sum")
    )
    result["factor_total_proxy"] = (
        result["factor_total_proxy"]
        / result.groupby("year")["factor_total_proxy"].transform("sum")
    )

    uncertainty_lookup = uncertainty.set_index(["year", "gas"])
    result["year_quality_note"] = result["year"].map(build_year_quality_notes(uncertainty_lookup))

    return result.sort_values(["year", "factor_total_proxy"], ascending=[True, False])


def build_year_quality_notes(uncertainty_lookup: pd.DataFrame) -> Dict[int, str]:
    notes: Dict[int, str] = {}
    years = sorted({year for year, _ in uncertainty_lookup.index})
    for year in years:
        row_no2 = uncertainty_lookup.loc[(year, "NO2")] if (year, "NO2") in uncertainty_lookup.index else None
        row_co = uncertainty_lookup.loc[(year, "CO")] if (year, "CO") in uncertainty_lookup.index else None
        row_ch4 = uncertainty_lookup.loc[(year, "CH4")] if (year, "CH4") in uncertainty_lookup.index else None

        fragments: List[str] = []
        if row_no2 is not None and row_no2["temporal_cv_percent"] > 40:
            fragments.append("NO2 high variability")
        if row_co is not None and row_co["temporal_cv_percent"] <= 12:
            fragments.append("CO stable")
        if row_ch4 is not None and row_ch4["temporal_cv_percent"] <= 1.0:
            fragments.append("CH4 very stable")
        if row_ch4 is not None and row_ch4["completeness_percent"] < 80:
            fragments.append("CH4 lower coverage")
        notes[year] = "; ".join(fragments) if fragments else "mixed quality"
    return notes


def write_outputs(result: pd.DataFrame, region_city_map: Dict[str, List[str]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = OUTPUT_DIR / "annual_proxy_regional_factors_2018_2026.csv"
    result.to_csv(csv_path, index=False)

    summary = {
        "method": {
            "type": "observation-based regional proxy factors",
            "region_dimension": "macro-regions from the 10-city Sentinel-5P observation network",
            "gas_factor_formula": "For each year and gas, factor = normalized sum of (annual city mean concentration * city population) within region.",
            "combustion_proxy_formula": f"{CO_PROXY_WEIGHT:.1f} * CO proxy + {NO2_PROXY_WEIGHT:.1f} * NO2 proxy",
            "total_proxy_formula": f"{CO2_SHARE:.6f} * combustion_proxy + {(CH4_SHARE + N2O_SHARE):.6f} * CH4_proxy",
            "important_note": "These are time-varying atmospheric proxy weights, not official regional emission factors.",
            "fallback_rule": "If CH4 is missing for a region-year, the script uses the CO proxy for that region-year. If CO were missing, it would fall back to population share.",
        },
        "regions": region_city_map,
        "year_summaries": {},
    }

    for year, group in result.groupby("year"):
        top = group.nlargest(3, "factor_total_proxy")[["region", "factor_total_proxy"]]
        summary["year_summaries"][str(year)] = {
            "top_regions": [
                {"region": row["region"], "factor_total_proxy": float(row["factor_total_proxy"])}
                for _, row in top.iterrows()
            ],
            "factor_sum_check": float(group["factor_total_proxy"].sum()),
            "quality_note": group["year_quality_note"].iloc[0],
        }

    json_path = OUTPUT_DIR / "annual_proxy_regional_factors_2018_2026.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    top_years_path = OUTPUT_DIR / "annual_proxy_regional_factors_summary.csv"
    with top_years_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["year", "rank", "region", "factor_total_proxy", "quality_note"],
        )
        writer.writeheader()
        for year, group in result.groupby("year"):
            top = group.nlargest(3, "factor_total_proxy")
            for rank, (_, row) in enumerate(top.iterrows(), start=1):
                writer.writerow(
                    {
                        "year": int(year),
                        "rank": rank,
                        "region": row["region"],
                        "factor_total_proxy": row["factor_total_proxy"],
                        "quality_note": row["year_quality_note"],
                    }
                )

    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {top_years_path}")
    for year, group in result.groupby("year"):
        top = group.nlargest(1, "factor_total_proxy").iloc[0]
        print(f"{int(year)}: top region = {top['region']} ({top['factor_total_proxy']:.4f})")


def main() -> None:
    observations, uncertainty = load_data()
    region_city_map = compute_region_city_map(observations)
    region_year_gas = compute_gas_region_factors(observations)
    result = pivot_factors(region_year_gas, uncertainty)
    write_outputs(result, region_city_map)


if __name__ == "__main__":
    main()