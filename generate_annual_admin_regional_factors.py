#!/usr/bin/env python3
"""Generate annual 14-unit administrative proxy factors for Uzbekistan.

This script bridges two existing products in the repository:
1. Static 2022 administrative factors derived from 2 km emission rasters.
2. Annual 7-zone observation-based proxy factors derived from Sentinel-5P.

The annual observation signal is applied at the macro-zone level, then split to
the 14 administrative units using each unit's 2022 static share within the
assigned macro-zone.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parent
STATIC_FACTORS_CSV = REPO_ROOT / "outputs" / "regional_emission_factors" / "regional_emission_factors.csv"
ANNUAL_MACRO_CSV = REPO_ROOT / "outputs" / "annual_proxy_regional_factors" / "annual_proxy_regional_factors_2018_2026.csv"
OUTPUT_DIR = REPO_ROOT / "outputs" / "annual_admin_regional_factors"


ADMIN_TO_MACRO_ZONE = {
    "Andijon viloyati": "Fergana Valley",
    "Buxoro viloyati": "Central",
    "Farg‘ona viloyati": "Fergana Valley",
    "Jizzax viloyati": "Samarkand",
    "Namangan viloyati": "Fergana Valley",
    "Navoiy viloyati": "Central",
    "Qashqadaryo viloyati": "Kashkadarya",
    "Qoraqalpog‘iston respublikasi": "Karakalpakstan",
    "Samarqand viloyati": "Samarkand",
    "Sirdaryo viloyati": "Tashkent",
    "Surxondaryo viloyati": "Kashkadarya",
    "Toshkent shahri": "Tashkent",
    "Toshkent viloyati": "Tashkent",
    "Xorazm viloyati": "Khorezm",
}

ADMIN_TO_MAPPING_BASIS = {
    "Andijon viloyati": "direct Fergana Valley observation province",
    "Buxoro viloyati": "direct Central observation province",
    "Farg‘ona viloyati": "direct Fergana Valley observation province",
    "Jizzax viloyati": "nearest eastern-central observation anchor is Samarkand",
    "Namangan viloyati": "direct Fergana Valley observation province",
    "Navoiy viloyati": "nearest western-central observation anchor is Bukhara/Central",
    "Qashqadaryo viloyati": "direct Kashkadarya observation province",
    "Qoraqalpog‘iston respublikasi": "direct Karakalpakstan observation province",
    "Samarqand viloyati": "direct Samarkand observation province",
    "Sirdaryo viloyati": "nearest corridor observation anchor is Tashkent",
    "Surxondaryo viloyati": "southern corridor anchored by Qarshi/Kashkadarya",
    "Toshkent shahri": "direct Tashkent observation province",
    "Toshkent viloyati": "direct Tashkent observation province",
    "Xorazm viloyati": "direct Khorezm observation province",
}


def load_static_factors() -> pd.DataFrame:
    df = pd.read_csv(STATIC_FACTORS_CSV)
    missing = sorted(set(ADMIN_TO_MACRO_ZONE).difference(df["region"].unique()))
    if missing:
        raise ValueError(f"Static factor file is missing admin units: {missing}")

    df = df[df["region"].isin(ADMIN_TO_MACRO_ZONE)].copy()
    df["macro_zone"] = df["region"].map(ADMIN_TO_MACRO_ZONE)
    df["mapping_basis"] = df["region"].map(ADMIN_TO_MAPPING_BASIS)
    df["within_macro_static_share"] = (
        df["factor_total"]
        / df.groupby("macro_zone")["factor_total"].transform("sum")
    )
    return df


def load_annual_macro_factors() -> pd.DataFrame:
    df = pd.read_csv(ANNUAL_MACRO_CSV)
    required_columns = {
        "year",
        "region",
        "factor_total_proxy",
        "factor_combustion_proxy",
        "factor_no2_proxy",
        "factor_co_proxy",
        "factor_ch4_proxy",
        "year_quality_note",
    }
    missing = sorted(required_columns.difference(df.columns))
    if missing:
        raise ValueError(f"Annual macro factor file is missing columns: {missing}")
    return df.rename(columns={"region": "macro_zone"})


def combine_admin_and_macro(static_df: pd.DataFrame, macro_df: pd.DataFrame) -> pd.DataFrame:
    combined = macro_df.merge(static_df, on="macro_zone", how="left", validate="many_to_many")
    if combined["region"].isna().any():
        missing_zones = sorted(combined.loc[combined["region"].isna(), "macro_zone"].unique())
        raise ValueError(f"Unmapped macro-zones in annual series: {missing_zones}")

    for source_col, output_col in [
        ("factor_total_proxy", "factor_total_admin_proxy"),
        ("factor_combustion_proxy", "factor_combustion_admin_proxy"),
        ("factor_no2_proxy", "factor_no2_admin_proxy"),
        ("factor_co_proxy", "factor_co_admin_proxy"),
        ("factor_ch4_proxy", "factor_ch4_admin_proxy"),
    ]:
        combined[output_col] = combined[source_col] * combined["within_macro_static_share"]

    combined["admin_rank_in_year"] = (
        combined.groupby("year")["factor_total_admin_proxy"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    sum_checks = combined.groupby("year").agg(
        factor_total_sum=("factor_total_admin_proxy", "sum"),
        factor_combustion_sum=("factor_combustion_admin_proxy", "sum"),
        factor_no2_sum=("factor_no2_admin_proxy", "sum"),
        factor_co_sum=("factor_co_admin_proxy", "sum"),
        factor_ch4_sum=("factor_ch4_admin_proxy", "sum"),
        admin_unit_count=("region", "nunique"),
    )
    for column in [
        "factor_total_sum",
        "factor_combustion_sum",
        "factor_no2_sum",
        "factor_co_sum",
        "factor_ch4_sum",
    ]:
        if not sum_checks[column].round(10).eq(1.0).all():
            raise ValueError(f"Normalization check failed for {column}:\n{sum_checks}")
    if not sum_checks["admin_unit_count"].eq(14).all():
        raise ValueError(f"Expected 14 admin units per year, got:\n{sum_checks}")

    return combined.sort_values(["year", "factor_total_admin_proxy"], ascending=[True, False])


def write_outputs(combined: pd.DataFrame, static_df: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = OUTPUT_DIR / "annual_admin_regional_factors_2018_2026.csv"
    combined.to_csv(csv_path, index=False)

    summary_rows: List[dict] = []
    for year, group in combined.groupby("year"):
        for rank, (_, row) in enumerate(group.nlargest(5, "factor_total_admin_proxy").iterrows(), start=1):
            summary_rows.append(
                {
                    "year": int(year),
                    "rank": rank,
                    "region": row["region"],
                    "macro_zone": row["macro_zone"],
                    "factor_total_admin_proxy": row["factor_total_admin_proxy"],
                    "year_quality_note": row["year_quality_note"],
                }
            )

    summary_csv_path = OUTPUT_DIR / "annual_admin_regional_factors_summary.csv"
    with summary_csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "year",
                "rank",
                "region",
                "macro_zone",
                "factor_total_admin_proxy",
                "year_quality_note",
            ],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    zone_members = {
        macro_zone: group[["region", "within_macro_static_share", "mapping_basis"]].to_dict("records")
        for macro_zone, group in static_df.groupby("macro_zone")
    }
    year_summaries = {}
    for year, group in combined.groupby("year"):
        top_regions = group.nlargest(5, "factor_total_admin_proxy")
        year_summaries[str(int(year))] = {
            "top_regions": [
                {
                    "region": row["region"],
                    "macro_zone": row["macro_zone"],
                    "factor_total_admin_proxy": float(row["factor_total_admin_proxy"]),
                }
                for _, row in top_regions.iterrows()
            ],
            "factor_sum_check": float(group["factor_total_admin_proxy"].sum()),
            "admin_unit_count": int(group["region"].nunique()),
            "year_quality_note": group["year_quality_note"].iloc[0],
        }

    summary_json = {
        "method": {
            "type": "14-unit administrative annual proxy factors",
            "bridge_rule": "Each annual macro-zone factor is distributed across member administrative units using the unit's 2022 static factor share within that macro-zone.",
            "important_note": "These are annual administrative proxy weights, not direct observed emissions by province.",
        },
        "macro_zone_membership": zone_members,
        "year_summaries": year_summaries,
    }

    json_path = OUTPUT_DIR / "annual_admin_regional_factors_2018_2026.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(summary_json, handle, indent=2, ensure_ascii=False)

    print(f"Wrote {csv_path}")
    print(f"Wrote {summary_csv_path}")
    print(f"Wrote {json_path}")
    for year, group in combined.groupby("year"):
        top = group.nlargest(1, "factor_total_admin_proxy").iloc[0]
        print(
            f"{int(year)}: top admin unit = {top['region']} "
            f"({top['factor_total_admin_proxy']:.4f}) via {top['macro_zone']}"
        )


def main() -> None:
    static_df = load_static_factors()
    macro_df = load_annual_macro_factors()
    combined = combine_admin_and_macro(static_df, macro_df)
    write_outputs(combined, static_df)


if __name__ == "__main__":
    main()