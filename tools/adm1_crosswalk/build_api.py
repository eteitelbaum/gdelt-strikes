"""
build_api.py — Build full FIPS 10-4 → GeoNames ADM1 crosswalk via API

Input:  docs/fips/fips10-4-subdivisions.csv   (full FIPS table, ~4,674 codes)
        docs/geonames/countryInfo.txt          (FIPS ↔ ISO2 country mapping)
Output: data/reference/adm1_crosswalk.csv      (complete crosswalk)

Each FIPS ADM1 code is resolved to:
  - adm1_name     : GeoNames standardized ADM1 name (join anchor for ACLED etc.)
  - iso_3166_2    : ISO 3166-2 subdivision code (for OECD/Eurostat)
  - geonames_adm1_id : GeoNames ID (stable internal reference)

Country-specific handlers (no API calls needed):
  UK  → 4 nations (England/Scotland/Wales/Northern Ireland)
  IE  → 4 provinces
  PH  → 17 regions
  FR  → post-2016 merged region names

All other codes: query GeoNames searchJSON API using official FIPS name.

Rate limit: 4 seconds between API calls → ~900/hour (limit is 1,000/hour).
Estimated runtime for ~4,000 API calls: ~4.5 hours. Run overnight.
Checkpointing: results written incrementally to avoid losing progress.

Usage:
    # Set GeoNames username (or relies on default)
    export GEONAMES_USERNAME=eteitelbaum

    # Full run (resumes from checkpoint if interrupted)
    python -m tools.adm1_crosswalk.build_api

    # Show progress without running
    python -m tools.adm1_crosswalk.build_api --status

    # Add GDELT-style US postal codes (USTX, USCA...) after main run
    python -m tools.adm1_crosswalk.build_api --add-us-postal
"""

import argparse
import os
import time
from pathlib import Path

import pandas as pd
import requests
from rapidfuzz import fuzz, process

ROOT = Path(__file__).resolve().parents[2]

FIPS_TABLE    = ROOT / "docs/fips/fips10-4-subdivisions.csv"
COUNTRY_INFO  = ROOT / "docs/geonames/countryInfo.txt"
CHECKPOINT    = ROOT / "data/reference/adm1_crosswalk_checkpoint.csv"
OUTPUT        = ROOT / "data/reference/adm1_crosswalk.csv"

GEONAMES_USERNAME = os.environ.get("GEONAMES_USERNAME", "eteitelbaum")
API_SLEEP = 4.0   # seconds between API calls; keeps us under 1,000/hour limit


# ---------------------------------------------------------------------------
# GeoNames API
# ---------------------------------------------------------------------------

def geonames_search(name: str, iso2: str, username: str,
                    feature_code: str = "ADM1") -> dict | None:
    """
    Query GeoNames searchJSON for a place by name + country.
    Returns the top result dict or None if nothing found.
    """
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
        print(f"    API error for {name!r}/{iso2}: {e}")
        return None


def resolve_via_api(fips_name: str, iso2: str, username: str) -> dict:
    """
    Try to resolve a FIPS ADM1 name to a GeoNames ADM1 entry.
    Falls back: ADM1 → ADM2 → no featureCode filter.
    """
    for feature_code in ("ADM1", "ADM2", None):
        kwargs = {"feature_code": feature_code} if feature_code else {}
        result = geonames_search(fips_name, iso2, username, **kwargs)
        if result:
            geonames_id = str(result.get("geonameId", ""))
            adm1_name   = result.get("adminName1") or result.get("name", "")
            # adminCodes1.ISO3166_2 is where GeoNames puts the ISO 3166-2 code
            admin_codes = result.get("adminCodes1", {})
            iso3166_2 = admin_codes.get("ISO3166_2", "")
            if iso3166_2:
                iso3166_2 = f"{iso2}-{iso3166_2}"
            return {
                "adm1_name":        adm1_name,
                "geonames_adm1_id": geonames_id,
                "iso_3166_2":       iso3166_2 or None,
                "match_method":     "api",
                "notes":            feature_code or "no_filter",
            }
    return {
        "adm1_name":        None,
        "geonames_adm1_id": None,
        "iso_3166_2":       None,
        "match_method":     "no_match",
        "notes":            None,
    }


# ---------------------------------------------------------------------------
# Country-specific handlers (reused from build.py)
# ---------------------------------------------------------------------------

_UK_NATIONS = {
    "England":          {"adm1_name": "England",          "geonames_adm1_id": "6269131", "iso_3166_2": "GB-ENG"},
    "Scotland":         {"adm1_name": "Scotland",         "geonames_adm1_id": "2638360", "iso_3166_2": "GB-SCT"},
    "Wales":            {"adm1_name": "Wales",            "geonames_adm1_id": "2634895", "iso_3166_2": "GB-WLS"},
    "Northern Ireland": {"adm1_name": "Northern Ireland", "geonames_adm1_id": "2641364", "iso_3166_2": "GB-NIR"},
}
_SCOTLAND_LADS = [
    "Aberdeen City", "Aberdeenshire", "Angus", "Argyll and Bute",
    "City of Edinburgh", "Edinburgh", "Clackmannanshire", "Dumfries and Galloway",
    "Dundee City", "Dundee", "East Ayrshire", "East Dunbartonshire",
    "East Lothian", "East Renfrewshire", "Falkirk", "Fife",
    "Glasgow City", "Glasgow", "Highland", "Inverclyde", "Midlothian",
    "Moray", "Na h-Eileanan Siar", "Western Isles", "North Ayrshire",
    "North Lanarkshire", "Orkney Islands", "Orkney", "Perth and Kinross",
    "Renfrewshire", "Scottish Borders", "Shetland Islands", "Shetland",
    "South Ayrshire", "South Lanarkshire", "Stirling",
    "West Dunbartonshire", "West Lothian",
]
_WALES_LADS = [
    "Blaenau Gwent", "Bridgend", "Caerphilly", "Cardiff", "Carmarthenshire",
    "Ceredigion", "Conwy", "Denbighshire", "Flintshire", "Gwynedd",
    "Isle of Anglesey", "Merthyr Tydfil", "Monmouthshire", "Neath Port Talbot",
    "Newport", "Pembrokeshire", "Powys", "Rhondda Cynon Taff", "Swansea",
    "Torfaen", "Vale of Glamorgan", "Wrexham",
]
_NI_LADS = [
    "Antrim", "Ards", "Armagh", "Ballymena", "Ballymoney", "Banbridge",
    "Belfast", "Carrickfergus", "Castlereagh", "Coleraine", "Cookstown",
    "Craigavon", "Derry", "Londonderry", "Down", "Dungannon", "Fermanagh",
    "Larne", "Limavady", "Lisburn", "Magherafelt", "Moyle", "Newry",
    "Mourne", "Newtownabbey", "North Down", "Omagh", "Strabane",
    "Antrim and Newtownabbey", "Ards and North Down",
    "Armagh City Banbridge and Craigavon", "Causeway Coast and Glens",
    "Derry City and Strabane", "Fermanagh and Omagh",
    "Lisburn and Castlereagh", "Mid and East Antrim",
    "Mid Ulster", "Newry Mourne and Down",
]

def assign_uk_nation(fips_name: str) -> dict:
    best_score, best_nation = 0, "England"
    for nation, lads in [("Scotland", _SCOTLAND_LADS),
                          ("Wales",   _WALES_LADS),
                          ("Northern Ireland", _NI_LADS)]:
        result = process.extractOne(fips_name, lads, scorer=fuzz.token_sort_ratio)
        if result and result[1] > best_score:
            best_score, best_nation = result[1], nation
    if best_score >= 70:
        return {**_UK_NATIONS[best_nation],
                "match_method": "country_specific", "notes": f"uk_{best_nation.lower().replace(' ','_')}"}
    return {**_UK_NATIONS["England"],
            "match_method": "country_specific", "notes": "uk_default_england"}


_IE_COUNTY_TO_PROVINCE = {
    "Galway": "Connacht", "Mayo": "Connacht", "Sligo": "Connacht",
    "Leitrim": "Connacht", "Roscommon": "Connacht",
    "Dublin": "Leinster", "Kildare": "Leinster", "Wicklow": "Leinster",
    "Wexford": "Leinster", "Carlow": "Leinster", "Kilkenny": "Leinster",
    "Laois": "Leinster", "Offaly": "Leinster", "Westmeath": "Leinster",
    "Longford": "Leinster", "Meath": "Leinster", "Louth": "Leinster",
    "Cork": "Munster", "Kerry": "Munster", "Limerick": "Munster",
    "Tipperary": "Munster", "Waterford": "Munster", "Clare": "Munster",
    "Cavan": "Ulster", "Monaghan": "Ulster", "Donegal": "Ulster",
}
_IE_PROVINCE_INFO = {
    "Connacht": {"adm1_name": "Connacht", "geonames_adm1_id": "2965694", "iso_3166_2": "IE-C"},
    "Leinster": {"adm1_name": "Leinster", "geonames_adm1_id": "2963597", "iso_3166_2": "IE-L"},
    "Munster":  {"adm1_name": "Munster",  "geonames_adm1_id": "2962944", "iso_3166_2": "IE-M"},
    "Ulster":   {"adm1_name": "Ulster",   "geonames_adm1_id": "2960313", "iso_3166_2": "IE-U"},
}

def assign_ireland_province(fips_name: str) -> dict:
    province = _IE_COUNTY_TO_PROVINCE.get(fips_name)
    if not province:
        result = process.extractOne(fips_name, list(_IE_COUNTY_TO_PROVINCE.keys()),
                                    scorer=fuzz.token_sort_ratio)
        if result and result[1] >= 70:
            province = _IE_COUNTY_TO_PROVINCE[result[0]]
    if province:
        return {**_IE_PROVINCE_INFO[province],
                "match_method": "country_specific", "notes": f"ie_{province.lower()}"}
    return {"adm1_name": None, "geonames_adm1_id": None,
            "iso_3166_2": None, "match_method": "no_match", "notes": None}


_FR_OLD_TO_NEW = {
    "Aquitaine": "Nouvelle-Aquitaine", "Limousin": "Nouvelle-Aquitaine",
    "Poitou-Charentes": "Nouvelle-Aquitaine",
    "Nord-Pas-de-Calais": "Hauts-de-France", "Picardie": "Hauts-de-France",
    "Haute-Normandie": "Normandy", "Basse-Normandie": "Normandy",
    "Alsace": "Grand Est", "Champagne-Ardenne": "Grand Est", "Lorraine": "Grand Est",
    "Languedoc-Roussillon": "Occitanie", "Midi-Pyrénées": "Occitanie",
    "Centre": "Centre-Val de Loire",
    "Bretagne": "Brittany", "Corse": "Corsica",
}


_PH_PROVINCE_TO_REGION = {
    "Manila": "National Capital Region", "Metro Manila": "National Capital Region",
    "Quezon City": "National Capital Region", "Makati": "National Capital Region",
    "Pasig": "National Capital Region", "Taguig": "National Capital Region",
    "Baguio": "Cordillera", "Benguet": "Cordillera", "Ifugao": "Cordillera",
    "Ilocos Norte": "Ilocos", "Ilocos Sur": "Ilocos", "La Union": "Ilocos",
    "Pangasinan": "Ilocos",
    "Cagayan": "Cagayan Valley", "Isabela": "Cagayan Valley",
    "Nueva Vizcaya": "Cagayan Valley",
    "Bulacan": "Central Luzon", "Pampanga": "Central Luzon", "Tarlac": "Central Luzon",
    "Nueva Ecija": "Central Luzon", "Bataan": "Central Luzon",
    "Cavite": "Calabarzon", "Laguna": "Calabarzon", "Batangas": "Calabarzon",
    "Rizal": "Calabarzon",
    "Palawan": "Mimaropa", "Occidental Mindoro": "Mimaropa",
    "Oriental Mindoro": "Mimaropa",
    "Albay": "Bicol Region", "Camarines Sur": "Bicol Region",
    "Camarines Norte": "Bicol Region",
    "Iloilo": "Western Visayas", "Negros Occidental": "Western Visayas",
    "Capiz": "Western Visayas", "Aklan": "Western Visayas",
    "Cebu": "Central Visayas", "Bohol": "Central Visayas",
    "Negros Oriental": "Central Visayas",
    "Leyte": "Eastern Visayas", "Samar": "Eastern Visayas",
    "Zamboanga del Norte": "Zamboanga Peninsula",
    "Zamboanga del Sur": "Zamboanga Peninsula",
    "Bukidnon": "Northern Mindanao", "Misamis Oriental": "Northern Mindanao",
    "Misamis Occidental": "Northern Mindanao",
    "Davao del Norte": "Davao Region", "Davao del Sur": "Davao Region",
    "Davao City": "Davao Region",
    "North Cotabato": "Soccsksargen", "South Cotabato": "Soccsksargen",
    "Sultan Kudarat": "Soccsksargen",
    "Agusan del Norte": "Caraga", "Agusan del Sur": "Caraga",
    "Surigao del Norte": "Caraga", "Surigao del Sur": "Caraga",
    "Lanao del Sur": "Autonomous Region in Muslim Mindanao",
    "Maguindanao": "Autonomous Region in Muslim Mindanao",
    "Sulu": "Autonomous Region in Muslim Mindanao",
    "Tawi-Tawi": "Autonomous Region in Muslim Mindanao",
    "Basilan": "Autonomous Region in Muslim Mindanao",
}
_PH_REGION_INFO = {
    "National Capital Region":              {"geonames_adm1_id": "7521309",  "iso_3166_2": "PH-NCR"},
    "Cordillera":                           {"geonames_adm1_id": "7521310",  "iso_3166_2": "PH-15"},
    "Ilocos":                               {"geonames_adm1_id": "7521312",  "iso_3166_2": "PH-01"},
    "Cagayan Valley":                       {"geonames_adm1_id": "7521311",  "iso_3166_2": "PH-02"},
    "Central Luzon":                        {"geonames_adm1_id": "7521313",  "iso_3166_2": "PH-03"},
    "Calabarzon":                           {"geonames_adm1_id": "7521314",  "iso_3166_2": "PH-40"},
    "Mimaropa":                             {"geonames_adm1_id": "7521315",  "iso_3166_2": "PH-41"},
    "Bicol Region":                         {"geonames_adm1_id": "7521316",  "iso_3166_2": "PH-05"},
    "Western Visayas":                      {"geonames_adm1_id": "7521317",  "iso_3166_2": "PH-06"},
    "Central Visayas":                      {"geonames_adm1_id": "7521318",  "iso_3166_2": "PH-07"},
    "Eastern Visayas":                      {"geonames_adm1_id": "7521319",  "iso_3166_2": "PH-08"},
    "Zamboanga Peninsula":                  {"geonames_adm1_id": "7521320",  "iso_3166_2": "PH-09"},
    "Northern Mindanao":                    {"geonames_adm1_id": "7521321",  "iso_3166_2": "PH-10"},
    "Davao Region":                         {"geonames_adm1_id": "7521322",  "iso_3166_2": "PH-11"},
    "Soccsksargen":                         {"geonames_adm1_id": "7521323",  "iso_3166_2": "PH-12"},
    "Caraga":                               {"geonames_adm1_id": "7521324",  "iso_3166_2": "PH-13"},
    "Autonomous Region in Muslim Mindanao": {"geonames_adm1_id": "7521325",  "iso_3166_2": "PH-14"},
}

def assign_philippines_region(fips_name: str) -> dict:
    region = _PH_PROVINCE_TO_REGION.get(fips_name)
    if not region:
        result = process.extractOne(fips_name, list(_PH_PROVINCE_TO_REGION.keys()),
                                    scorer=fuzz.token_sort_ratio)
        if result and result[1] >= 70:
            region = _PH_PROVINCE_TO_REGION[result[0]]
    if region and region in _PH_REGION_INFO:
        return {"adm1_name": region, **_PH_REGION_INFO[region],
                "match_method": "country_specific", "notes": f"ph_{region.lower()[:20]}"}
    return {"adm1_name": None, "geonames_adm1_id": None,
            "iso_3166_2": None, "match_method": "no_match", "notes": None}


# ---------------------------------------------------------------------------
# US postal abbreviation supplement
# GDELT uses postal codes (USTX, USCA) not FIPS numeric (US48, US06).
# After the main run, duplicate US state rows under postal keys.
# ---------------------------------------------------------------------------

_US_FIPS_NUMERIC_TO_POSTAL = {
    "US01": "USAL", "US02": "USAK", "US04": "USAZ", "US05": "USAR",
    "US06": "USCA", "US08": "USCO", "US09": "USCT", "US10": "USDE",
    "US11": "USDC", "US12": "USFL", "US13": "USGA", "US15": "USHI",
    "US16": "USID", "US17": "USIL", "US18": "USIN", "US19": "USIA",
    "US20": "USKS", "US21": "USKY", "US22": "USLA", "US23": "USME",
    "US24": "USMD", "US25": "USMA", "US26": "USMI", "US27": "USMN",
    "US28": "USMS", "US29": "USMO", "US30": "USMT", "US31": "USNE",
    "US32": "USNV", "US33": "USNH", "US34": "USNJ", "US35": "USNM",
    "US36": "USNY", "US37": "USNC", "US38": "USND", "US39": "USOH",
    "US40": "USOK", "US41": "USOR", "US42": "USPA", "US44": "USRI",
    "US45": "USSC", "US46": "USSD", "US47": "USTN", "US48": "USTX",
    "US49": "USUT", "US50": "USVT", "US51": "USVA", "US53": "USWA",
    "US54": "USWV", "US55": "USWI", "US56": "USWY",
}


# ---------------------------------------------------------------------------
# Load reference data
# ---------------------------------------------------------------------------

def load_fips_table() -> pd.DataFrame:
    return pd.read_csv(FIPS_TABLE, dtype=str)


def load_fips_to_iso2() -> dict:
    cols = ['iso2', 'iso3', 'iso_numeric', 'fips', 'country',
            'capital', 'area_km2', 'population', 'continent', 'tld',
            'currency_code', 'currency_name', 'phone', 'postal_format',
            'postal_regex', 'languages', 'geonames_id', 'neighbours',
            'equivalent_fips']
    df = pd.read_csv(COUNTRY_INFO, sep='\t', comment='#',
                     header=None, names=cols, dtype=str)
    df = df[df['fips'].notna() & (df['fips'] != '-')]
    return df.set_index('fips')['iso2'].to_dict()


def load_checkpoint() -> set:
    """Return set of fips_adm1 codes already processed."""
    if not CHECKPOINT.exists():
        return set()
    df = pd.read_csv(CHECKPOINT, dtype=str)
    return set(df['fips_adm1'].tolist())


def append_checkpoint(row: dict) -> None:
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    write_header = not CHECKPOINT.exists()
    with open(CHECKPOINT, "a", encoding="utf-8", newline="") as f:
        import csv
        fieldnames = ["fips_country", "fips_adm1", "fips_adm1_name", "iso2_country",
                      "adm1_name", "geonames_adm1_id", "iso_3166_2",
                      "match_method", "notes"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in fieldnames})


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------

def run(username: str = GEONAMES_USERNAME):
    fips_df = load_fips_table()
    fips_to_iso2 = load_fips_to_iso2()
    done = load_checkpoint()

    todo = fips_df[~fips_df['fips_adm1'].isin(done)]
    total = len(fips_df)
    remaining = len(todo)
    print(f"Total FIPS codes: {total}")
    print(f"Already done:     {total - remaining}")
    print(f"Remaining:        {remaining}")
    print(f"GeoNames username: {username}")
    print(f"Estimated time for API calls: see progress below\n")

    api_calls = 0
    for i, row in enumerate(todo.itertuples(), 1):
        fips_adm1 = row.fips_adm1
        fips_name = row.fips_adm1_name_ascii  # clean ASCII name for API query
        fips_country = row.fips_country
        iso2 = fips_to_iso2.get(fips_country)

        result = {
            "fips_country":    fips_country,
            "fips_adm1":       fips_adm1,
            "fips_adm1_name":  row.fips_adm1_name,
            "iso2_country":    iso2 or "",
        }

        if not iso2:
            result.update({"adm1_name": None, "geonames_adm1_id": None,
                           "iso_3166_2": None, "match_method": "no_iso2", "notes": None})

        elif iso2 == "GB":
            result.update(assign_uk_nation(fips_name))

        elif iso2 == "IE":
            result.update(assign_ireland_province(fips_name))

        elif iso2 == "PH":
            result.update(assign_philippines_region(fips_name))

        elif iso2 == "FR" and fips_name in _FR_OLD_TO_NEW:
            query_name = _FR_OLD_TO_NEW[fips_name]
            api_result = resolve_via_api(query_name, "FR", username)
            if api_result["match_method"] == "api":
                api_result["match_method"] = "country_specific"
                api_result["notes"] = f"fr_remap→{query_name}"
            result.update(api_result)
            api_calls += 1
            time.sleep(API_SLEEP)

        else:
            api_result = resolve_via_api(fips_name, iso2, username)
            result.update(api_result)
            api_calls += 1
            time.sleep(API_SLEEP)

        append_checkpoint(result)

        if i % 50 == 0 or i == remaining:
            pct = (total - remaining + i) / total * 100
            print(f"  [{pct:.1f}%] {total - remaining + i}/{total} — "
                  f"API calls this session: {api_calls} — last: {fips_adm1} ({fips_name})")

    print(f"\nDone. {api_calls} API calls made this session.")
    finalize()


def finalize():
    """Merge checkpoint into final output CSV, adding US postal supplement."""
    if not CHECKPOINT.exists():
        print("No checkpoint found — run first.")
        return

    df = pd.read_csv(CHECKPOINT, dtype=str)
    print(f"Checkpoint: {len(df)} rows")

    # Add GDELT-style US postal code rows (USTX, USCA, etc.)
    us_rows = df[df['fips_adm1'].isin(_US_FIPS_NUMERIC_TO_POSTAL.keys())].copy()
    postal_rows = []
    for _, row in us_rows.iterrows():
        postal_code = _US_FIPS_NUMERIC_TO_POSTAL.get(row['fips_adm1'])
        if postal_code:
            new_row = row.copy()
            new_row['fips_adm1'] = postal_code
            new_row['notes'] = f"gdelt_postal_alias_of_{row['fips_adm1']}"
            postal_rows.append(new_row)
    if postal_rows:
        df = pd.concat([df, pd.DataFrame(postal_rows)], ignore_index=True)
        print(f"Added {len(postal_rows)} US postal code alias rows")

    df = df.sort_values(['fips_country', 'fips_adm1']).reset_index(drop=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False)
    print(f"Saved {len(df)} rows → {OUTPUT}")

    # Summary
    print("\nMatch method breakdown:")
    print(df['match_method'].value_counts().to_string())
    no_match = df[df['match_method'].isin(['no_match', 'no_iso2'])]
    if not no_match.empty:
        print(f"\nUnresolved ({len(no_match)} rows) — candidates for manual review:")
        print(no_match[['fips_adm1', 'fips_adm1_name', 'iso2_country', 'match_method']].to_string(index=False))


def status():
    fips_df = load_fips_table()
    done = load_checkpoint()
    total = len(fips_df)
    n_done = len(done)
    print(f"Total FIPS codes: {total}")
    print(f"Processed:        {n_done} ({n_done/total*100:.1f}%)")
    print(f"Remaining:        {total - n_done}")
    if CHECKPOINT.exists():
        df = pd.read_csv(CHECKPOINT, dtype=str)
        print(f"\nMatch method breakdown so far:")
        print(df['match_method'].value_counts().to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true", help="Show progress without running")
    parser.add_argument("--finalize", action="store_true", help="Merge checkpoint to final CSV")
    parser.add_argument("--username", default=GEONAMES_USERNAME)
    args = parser.parse_args()

    if args.status:
        status()
    elif args.finalize:
        finalize()
    else:
        run(username=args.username)
