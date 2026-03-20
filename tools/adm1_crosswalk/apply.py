"""
apply.py — Build geo_validation_final.csv (Step 5)

Combines three inputs into a single analysis-ready event file:
  1. geo_validation.csv        — LLM validation results (11,503 events)
  2. adm1_crosswalk.csv        — FIPS ADM1 code → standardized identifiers
  3. corrected_location_crosswalk.csv — corrected locations → identifiers

Logic:
  match == "no"        → use corrected_location_crosswalk; geo_quality = "validated"
  match == "yes"       → use adm1_crosswalk via ActionGeo_ADM1Code; geo_quality = "validated"
  match == "uncertain" → use adm1_crosswalk via ActionGeo_ADM1Code; geo_quality = "unvalidated"

Output columns added to geo_validation.csv:
  final_adm1_name   — standardized ADM1 name (primary join anchor for ACLED etc.)
  final_iso_3166_2  — ISO 3166-2 subdivision code (for OECD/Eurostat)
  final_country_iso2 — ISO 3166-1 alpha-2 country code
  geo_quality       — "confirmed" / "corrected" / "unvalidated"

Usage:
    python -m tools.adm1_crosswalk.apply
    python -m tools.adm1_crosswalk.apply --report
"""

import argparse
from pathlib import Path

import pandas as pd

ROOT          = Path(__file__).resolve().parents[2]
GEO_VAL       = ROOT / "data/enhanced/geo_validation.csv"
CROSSWALK     = ROOT / "data/reference/adm1_crosswalk.csv"
CORRECTIONS   = ROOT / "data/reference/corrected_location_crosswalk.csv"
OUTPUT        = ROOT / "data/enhanced/geo_validation_final.csv"


def main(report_only: bool = False):
    # ------------------------------------------------------------------
    # Load inputs
    # ------------------------------------------------------------------
    geo  = pd.read_csv(GEO_VAL,     dtype=str)
    cw   = pd.read_csv(CROSSWALK,   dtype=str)
    corr = pd.read_csv(CORRECTIONS, dtype=str)

    print(f"geo_validation rows:              {len(geo):,}")
    print(f"adm1_crosswalk rows:              {len(cw):,}")
    print(f"corrected_location_crosswalk rows:{len(corr):,}")

    # ------------------------------------------------------------------
    # Build crosswalk lookup: fips_adm1 → (adm1_name, iso_3166_2, iso2)
    # Only use rows that actually matched (not no_match)
    # ------------------------------------------------------------------
    cw_matched = cw[cw["match_method"] != "no_match"].copy()
    cw_lookup  = cw_matched.set_index("fips_adm1")[
        ["adm1_name", "iso_3166_2", "iso2_country"]
    ].rename(columns={"iso2_country": "country_iso2"})

    # ------------------------------------------------------------------
    # Build corrections lookup: GLOBALEVENTID → (adm1_name, iso_3166_2, country_iso2)
    # Only use resolved rows (skip country_level and unresolvable — those
    # fall back to the FIPS crosswalk)
    # ------------------------------------------------------------------
    corr_resolved = corr[corr["match_method"] == "resolved"].copy()
    corr_lookup   = corr_resolved.set_index("GLOBALEVENTID")[
        ["adm1_name", "iso_3166_2", "country_iso2"]
    ]

    # ------------------------------------------------------------------
    # Assign final identifiers row by row (vectorized via merge)
    # ------------------------------------------------------------------
    geo = geo.copy()
    geo["final_adm1_name"]    = pd.NA
    geo["final_iso_3166_2"]   = pd.NA
    geo["final_country_iso2"] = pd.NA
    geo["geo_quality"]        = pd.NA

    # --- match == "no" → corrected_location_crosswalk (resolved only) ---
    mask_no = geo["match"] == "no"
    no_ids  = geo.loc[mask_no, "GLOBALEVENTID"]
    no_from_corr = no_ids[no_ids.isin(corr_lookup.index)]
    no_fips_fallback = no_ids[~no_ids.isin(corr_lookup.index)]

    # Fill from corrections
    if len(no_from_corr):
        geo.loc[geo["GLOBALEVENTID"].isin(no_from_corr), "final_adm1_name"]    = \
            corr_lookup.loc[no_from_corr, "adm1_name"].values
        geo.loc[geo["GLOBALEVENTID"].isin(no_from_corr), "final_iso_3166_2"]   = \
            corr_lookup.loc[no_from_corr, "iso_3166_2"].values
        geo.loc[geo["GLOBALEVENTID"].isin(no_from_corr), "final_country_iso2"] = \
            corr_lookup.loc[no_from_corr, "country_iso2"].values
        geo.loc[geo["GLOBALEVENTID"].isin(no_from_corr), "geo_quality"] = "validated"

    # Fallback to FIPS crosswalk for country_level / unresolvable corrections
    if len(no_fips_fallback):
        fips_codes = geo.loc[geo["GLOBALEVENTID"].isin(no_fips_fallback), "ActionGeo_ADM1Code"]
        matched    = fips_codes[fips_codes.isin(cw_lookup.index)]
        if len(matched):
            idx = geo[geo["GLOBALEVENTID"].isin(no_fips_fallback) &
                      geo["ActionGeo_ADM1Code"].isin(cw_lookup.index)].index
            codes = geo.loc[idx, "ActionGeo_ADM1Code"]
            geo.loc[idx, "final_adm1_name"]    = cw_lookup.loc[codes, "adm1_name"].values
            geo.loc[idx, "final_iso_3166_2"]   = cw_lookup.loc[codes, "iso_3166_2"].values
            geo.loc[idx, "final_country_iso2"] = cw_lookup.loc[codes, "country_iso2"].values
            geo.loc[idx, "geo_quality"]        = "validated"

    # --- match == "yes" or "uncertain" → adm1_crosswalk ---
    for match_val, quality in [("yes", "validated"), ("uncertain", "unvalidated")]:
        mask = geo["match"] == match_val
        idx  = geo[mask & geo["ActionGeo_ADM1Code"].isin(cw_lookup.index)].index
        codes = geo.loc[idx, "ActionGeo_ADM1Code"]
        geo.loc[idx, "final_adm1_name"]    = cw_lookup.loc[codes, "adm1_name"].values
        geo.loc[idx, "final_iso_3166_2"]   = cw_lookup.loc[codes, "iso_3166_2"].values
        geo.loc[idx, "final_country_iso2"] = cw_lookup.loc[codes, "country_iso2"].values
        geo.loc[idx, "geo_quality"]        = quality

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------
    print("\n--- Coverage report ---")
    print(f"geo_quality distribution:")
    print(geo["geo_quality"].value_counts(dropna=False).to_string())
    print()

    total      = len(geo)
    has_adm1   = geo["final_adm1_name"].notna().sum()
    has_iso    = geo["final_iso_3166_2"].notna().sum()
    no_adm1    = total - has_adm1

    print(f"Events with final_adm1_name:   {has_adm1:,} / {total:,} ({100*has_adm1/total:.1f}%)")
    print(f"Events with final_iso_3166_2:  {has_iso:,} / {total:,} ({100*has_iso/total:.1f}%)")
    print(f"Events missing adm1 entirely:  {no_adm1:,} ({100*no_adm1/total:.1f}%)")

    # Diagnose missing
    missing = geo[geo["final_adm1_name"].isna()]
    if len(missing):
        print(f"\nMissing adm1 breakdown by match:")
        print(missing["match"].value_counts().to_string())
        print(f"\nSample missing FIPS codes:")
        print(missing["ActionGeo_ADM1Code"].value_counts().head(15).to_string())

    if report_only:
        return

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    geo.to_csv(OUTPUT, index=False)
    print(f"\nSaved → {OUTPUT}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true",
                        help="Print coverage report without saving output file")
    args = parser.parse_args()
    main(report_only=args.report)
