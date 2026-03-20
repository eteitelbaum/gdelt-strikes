"""
requery_nomatches.py — Re-query GeoNames for all no_match rows

Addresses two failure modes from the main build_api.py run:
  1. Double-name FIPS entries (e.g. "Anhui__Anhwei", "Kondoz__Kunduz"):
     strip everything after __ or _ and retry with the clean first name
  2. Silent API failures (rate limit errors caught as no_match):
     simply re-query; these should resolve on a fresh attempt

Covers ALL no_match rows in the crosswalk, not just those appearing in
our GDELT data — zero-count regions matter for panel construction.

Updates data/reference/adm1_crosswalk.csv in place.

Usage:
    python -m tools.adm1_crosswalk.requery_nomatches
    python -m tools.adm1_crosswalk.requery_nomatches --dry-run
"""

import argparse
import os
import re
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
CROSSWALK = ROOT / "data/reference/adm1_crosswalk.csv"
GEONAMES_USERNAME = os.environ.get("GEONAMES_USERNAME", "eteitelbaum")
API_SLEEP = 4.0


# ---------------------------------------------------------------------------
# Name cleaning
# ---------------------------------------------------------------------------

def clean_fips_name(name: str) -> list[str]:
    """
    Return candidate query strings from a FIPS name, in order of preference.

    FIPS double-name format: "NewName__OldName" or "NewName_OldName"
    Strategy: try the first part, then the second, then the full string.
    Also handles bilingual names like "Name [English]; Nom [French]".
    """
    if not name or pd.isna(name):
        return []

    candidates = []

    # Bilingual bracket format: "Name [lang]; Nom [lang]"
    bracket = re.split(r'\s*\[.*?\]\s*;?\s*', name)
    bracket = [b.strip() for b in bracket if b.strip()]
    if len(bracket) > 1:
        candidates.extend(bracket)

    # Double-underscore separator: "NewName__OldName"
    if '__' in name:
        parts = [p.strip() for p in name.split('__') if p.strip()]
        candidates.extend(parts)
    # Single underscore separator (some Cameroon/Israel entries): "Name_Translation"
    elif '_' in name and not name.startswith('_'):
        parts = [p.strip() for p in name.split('_') if p.strip()]
        candidates.extend(parts)

    # Always include full original as last resort
    candidates.append(name.strip())

    # Deduplicate while preserving order
    seen = set()
    result = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result


# ---------------------------------------------------------------------------
# GeoNames API
# ---------------------------------------------------------------------------

def geonames_search(name: str, iso2: str, username: str,
                    feature_code: str = "ADM1") -> dict | None:
    params = {
        "q": name,
        "country": iso2,
        "featureCode": feature_code,
        "maxRows": 1,
        "style": "FULL",
        "username": username,
    }
    try:
        r = requests.get("http://api.geonames.org/searchJSON",
                         params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        geonames = data.get("geonames", [])
        return geonames[0] if geonames else None
    except Exception as e:
        print(f"    API error: {e}")
        return None


def resolve(name: str, iso2: str, username: str) -> dict | None:
    """
    Try each candidate name and each feature code until we get a result.
    Returns parsed result dict or None.
    """
    candidates = clean_fips_name(name)

    for candidate in candidates:
        for feature_code in ("ADM1", "ADM2", None):
            kwargs = {"feature_code": feature_code} if feature_code else {}
            result = geonames_search(candidate, iso2, username, **kwargs)
            time.sleep(API_SLEEP)
            if result:
                admin_codes = result.get("adminCodes1", {})
                iso3166_2 = admin_codes.get("ISO3166_2", "")
                if iso3166_2:
                    iso3166_2 = f"{iso2}-{iso3166_2}"
                return {
                    "adm1_name":        result.get("adminName1") or result.get("name", ""),
                    "geonames_adm1_id": str(result.get("geonameId", "")),
                    "iso_3166_2":       iso3166_2 or None,
                    "match_method":     "api_requery",
                    "notes":            f"requeried_as:{candidate}",
                }
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(dry_run: bool = False, username: str = GEONAMES_USERNAME):
    df = pd.read_csv(CROSSWALK, dtype=str)
    print(f"Loaded crosswalk: {len(df)} rows")

    no_match = df[df['match_method'] == 'no_match'].copy()
    print(f"no_match rows to requery: {len(no_match)}")

    if dry_run:
        print("\n--- DRY RUN: candidate names ---")
        for _, row in no_match.iterrows():
            candidates = clean_fips_name(row['fips_adm1_name'])
            print(f"  {row['fips_adm1']:8s}  {row['fips_adm1_name'][:40]:40s}  → {candidates}")
        return

    resolved = 0
    still_missing = 0

    for i, (idx, row) in enumerate(no_match.iterrows(), 1):
        iso2 = row.get('iso2_country', '')
        name = row.get('fips_adm1_name', '')

        if not iso2 or pd.isna(iso2) or iso2 == 'nan':
            print(f"  [{i}/{len(no_match)}] {row['fips_adm1']:8s}  SKIP (no iso2)")
            still_missing += 1
            continue

        print(f"  [{i}/{len(no_match)}] {row['fips_adm1']:8s}  {name[:40]:40s}", end="  ")
        result = resolve(name, iso2, username)

        if result:
            df.loc[idx, 'adm1_name']        = result['adm1_name']
            df.loc[idx, 'geonames_adm1_id'] = result['geonames_adm1_id']
            df.loc[idx, 'iso_3166_2']       = result['iso_3166_2']
            df.loc[idx, 'match_method']     = result['match_method']
            df.loc[idx, 'notes']            = result['notes']
            print(f"→ {result['adm1_name']}")
            resolved += 1
        else:
            print("→ still no_match")
            still_missing += 1

        # Save incrementally every 50 rows
        if i % 50 == 0:
            df.to_csv(CROSSWALK, index=False)
            print(f"    [checkpoint saved at {i}]")

    df.to_csv(CROSSWALK, index=False)

    print(f"\nDone.")
    print(f"  Resolved:      {resolved}")
    print(f"  Still missing: {still_missing}")
    print(f"Crosswalk saved → {CROSSWALK}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Show candidate names without querying API")
    parser.add_argument("--username", default=GEONAMES_USERNAME)
    args = parser.parse_args()
    main(dry_run=args.dry_run, username=args.username)
