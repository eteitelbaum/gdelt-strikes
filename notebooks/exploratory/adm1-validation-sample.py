"""
Build a stratified random sample for manual ADM1 geolocation validation.

Merges:
  - data/enhanced/gdelt_strikes.parquet   (geographic fields)
  - data/enhanced/url_classifications.csv (classification + reasoning)
  - tools/url_classifier/uncertain_titles.csv (fetched article titles)

on GLOBALEVENTID, then draws a stratified sample (stratified by country)
restricted to events where a title was retrieved. Output is a CSV suitable
for manual review.

Usage:
    python notebooks/exploratory/adm1-validation-sample.py
    python notebooks/exploratory/adm1-validation-sample.py --n 200 --seed 7
"""

import argparse
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]

GEO_COLS = [
    "GLOBALEVENTID",
    "ActionGeo_CountryCode",
    "ActionGeo_ADM1Code",
    "ActionGeo_FullName",
    "ActionGeo_Lat",
    "ActionGeo_Long",
    "ActionGeo_Type",
    "SQLDATE",
]

OUTPUT_COLS = [
    "GLOBALEVENTID",
    "SQLDATE",
    "ActionGeo_CountryCode",
    "ActionGeo_ADM1Code",
    "ActionGeo_FullName",
    "ActionGeo_Lat",
    "ActionGeo_Long",
    "ActionGeo_Type",
    "classification",
    "source_url",
    "title",
    "title_source",
    "reasoning",
    # manual review columns (blank for the reviewer to fill in)
    "adm1_correct",   # yes / no / unsure
    "notes",
]


def main(n: int = 150, seed: int = 42, per_country_max: int = 5):
    events = pq.read_table(
        ROOT / "data/enhanced/gdelt_strikes.parquet",
        columns=GEO_COLS,
    ).to_pandas()

    classifications = pd.read_csv(ROOT / "data/enhanced/url_classifications.csv")

    titles = pd.read_csv(ROOT / "tools/url_classifier/uncertain_titles.csv")

    # Align types before merging
    events["GLOBALEVENTID"] = events["GLOBALEVENTID"].astype("int64")
    classifications["GLOBALEVENTID"] = classifications["GLOBALEVENTID"].astype("int64")
    titles["GLOBALEVENTID"] = titles["GLOBALEVENTID"].astype("int64")

    # Merge events + classifications
    df = events.merge(classifications, on="GLOBALEVENTID", how="inner")

    # Left-join titles (only uncertain events had titles fetched, but we
    # also want relevant/not_relevant rows that happen to appear here)
    df = df.merge(
        titles[["GLOBALEVENTID", "title", "title_source"]],
        on="GLOBALEVENTID",
        how="left",
    )

    # Restrict to relevant events only — these are the events that will be in the analysis
    pool = df[df["classification"] == "relevant"].copy()
    print(f"Relevant events:      {len(pool):,}")
    print(f"  with fetched title: {pool['title'].notna().sum():,}")

    # Stratified sample by country, capped per country to avoid over-representation
    country_counts = pool["ActionGeo_CountryCode"].value_counts()
    total = len(pool)
    parts = []
    for country, count in country_counts.items():
        subset = pool[pool["ActionGeo_CountryCode"] == country]
        allocated = max(1, min(per_country_max, round(n * count / total)))
        parts.append(subset.sample(min(allocated, len(subset)), random_state=seed))

    sample = (
        pd.concat(parts)
        .drop_duplicates(subset=["GLOBALEVENTID"])
        .sample(min(n, len(pd.concat(parts))), random_state=seed)
        .sort_values(["ActionGeo_CountryCode", "SQLDATE"])
        .reset_index(drop=True)
    )

    # Add blank reviewer columns
    sample["adm1_correct"] = ""
    sample["notes"] = ""

    # Keep only desired output columns (in order)
    out_cols = [c for c in OUTPUT_COLS if c in sample.columns]
    sample = sample[out_cols]

    out_path = ROOT / "data/test/adm1_validation_sample.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(out_path, index=False)

    print(f"\nSample: {len(sample):,} events across "
          f"{sample['ActionGeo_CountryCode'].nunique()} countries")
    print(f"Saved → {out_path}")

    # Summary
    print("\nClassification breakdown:")
    print(sample["classification"].value_counts().to_string())
    print("\nTop 10 countries:")
    print(sample["ActionGeo_CountryCode"].value_counts().head(10).to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build ADM1 validation sample")
    parser.add_argument("--n",              type=int, default=150,
                        help="Target sample size (default: 150)")
    parser.add_argument("--seed",           type=int, default=42,
                        help="Random seed (default: 42)")
    parser.add_argument("--per-country-max", type=int, default=5,
                        help="Max events per country (default: 5)")
    args = parser.parse_args()
    main(n=args.n, seed=args.seed, per_country_max=args.per_country_max)
