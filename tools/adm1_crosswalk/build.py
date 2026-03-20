"""
Build a crosswalk from GDELT ADM1 codes (FIPS 10-4) to GeoNames IDs and
ISO 3166-2 subdivision codes.

Sources:
  docs/geonames/countryInfo.txt      -- FIPS ↔ ISO2 country code mapping
  docs/geonames/admin1CodesASCII.txt -- GeoNames ADM1 names + IDs (ISO2-keyed)
  data/enhanced/gdelt_strikes.parquet -- unique GDELT ADM1 codes to crosswalk

Output:
  data/reference/adm1_crosswalk.csv

Usage:
  python -m tools.adm1_crosswalk.build
"""

import re
import unicodedata
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
from rapidfuzz import process, fuzz

ROOT = Path(__file__).resolve().parents[2]

COUNTRY_INFO   = ROOT / "docs/geonames/countryInfo.txt"
ADMIN1_CODES   = ROOT / "docs/geonames/admin1CodesASCII.txt"
GDELT_PARQUET  = ROOT / "data/enhanced/gdelt_strikes.parquet"
OUT_DIR        = ROOT / "data/reference"
OUT_CSV        = OUT_DIR / "adm1_crosswalk.csv"

FUZZY_THRESHOLD = 70   # scores below this are flagged as low-confidence

# Common administrative suffixes to strip before fuzzy matching.
# Helps with cases like "Nasarawa State" vs "Nassarawa", "Kaduna State" vs "Kaduna".
_ADMIN_SUFFIXES = re.compile(
    r'\s+(State|Province|Region|District|Governorate|Oblast|Kray|Republic'
    r'|Department|County|Division|Territory)$',
    re.IGNORECASE
)

def _strip_diacritics(s: str) -> str:
    """Decompose Unicode and remove combining characters (diacritics)."""
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")

def _normalize(name: str) -> str:
    """Strip diacritics, trailing admin suffixes, and lowercase for matching."""
    if not name:
        return ""
    name = _strip_diacritics(name.strip())
    return _ADMIN_SUFFIXES.sub("", name).lower()


# ---------------------------------------------------------------------------
# UK: aggregate LADs → 4 nations
# GDELT codes UK at Local Authority District level, which is finer than ADM1.
# For a cross-national panel we aggregate up to England/Scotland/Wales/NI.
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

def assign_uk_nation(lad_name: str) -> dict:
    """Map a UK LAD name to one of the 4 nations; defaults to England."""
    if not lad_name or lad_name.startswith("("):
        return {**_UK_NATIONS["England"], "match_method": "uk_default_england",
                "match_score": None}
    best_score, best_nation = 0, "England"
    for nation, lads in [("Scotland", _SCOTLAND_LADS),
                          ("Wales",   _WALES_LADS),
                          ("Northern Ireland", _NI_LADS)]:
        result = process.extractOne(lad_name, lads, scorer=fuzz.token_sort_ratio)
        if result and result[1] > best_score:
            best_score, best_nation = result[1], nation
    if best_score >= 70:
        return {**_UK_NATIONS[best_nation],
                "match_method": "uk_nation_fuzzy", "match_score": best_score}
    return {**_UK_NATIONS["England"],
            "match_method": "uk_default_england", "match_score": best_score}


# ---------------------------------------------------------------------------
# Ireland: aggregate counties → 4 provinces
# GDELT codes Ireland at county level; GeoNames ADM1 = 4 provinces.
# ---------------------------------------------------------------------------

_IE_COUNTY_TO_PROVINCE = {
    # Connacht
    "Galway": "Connacht", "County Galway": "Connacht", "Galway City": "Connacht",
    "Mayo": "Connacht", "Sligo": "Connacht", "Leitrim": "Connacht",
    "Roscommon": "Connacht",
    # Leinster
    "Dublin": "Leinster", "Dublin City": "Leinster", "County Dublin": "Leinster",
    "County Fingal": "Leinster", "Fingal": "Leinster",
    "Dún Laoghaire-Rathdown": "Leinster", "South Dublin": "Leinster",
    "Kildare": "Leinster", "Wicklow": "Leinster", "Wexford": "Leinster",
    "Carlow": "Leinster", "Kilkenny": "Leinster", "Laois": "Leinster",
    "Offaly": "Leinster", "Westmeath": "Leinster", "Longford": "Leinster",
    "Meath": "Leinster", "Louth": "Leinster",
    # Munster
    "Cork": "Munster", "Cork City": "Munster", "County Cork": "Munster",
    "Kerry": "Munster", "Limerick": "Munster", "Limerick City": "Munster",
    "Tipperary": "Munster", "Waterford": "Munster", "Waterford City": "Munster",
    "Clare": "Munster",
    # Ulster (Republic counties only — NI handled by UK codes)
    "Cavan": "Ulster", "Monaghan": "Ulster", "Donegal": "Ulster",
}

_IE_PROVINCE_INFO = {
    "Connacht": {"adm1_name": "Connacht", "geonames_adm1_id": "2965694", "iso_3166_2": "IE-C"},
    "Leinster": {"adm1_name": "Leinster", "geonames_adm1_id": "2963597", "iso_3166_2": "IE-L"},
    "Munster":  {"adm1_name": "Munster",  "geonames_adm1_id": "2962944", "iso_3166_2": "IE-M"},
    "Ulster":   {"adm1_name": "Ulster",   "geonames_adm1_id": "2960313", "iso_3166_2": "IE-U"},
}

def assign_ireland_province(county_name: str) -> dict:
    """Map an Irish county name to one of the 4 provinces."""
    if not county_name or county_name.startswith("("):
        return {"adm1_name": None, "geonames_adm1_id": None,
                "iso_3166_2": None, "match_method": "ie_no_match", "match_score": None}
    # Exact lookup first
    province = _IE_COUNTY_TO_PROVINCE.get(county_name)
    if province:
        return {**_IE_PROVINCE_INFO[province],
                "match_method": "ie_exact", "match_score": 100}
    # Fuzzy fallback against county keys
    result = process.extractOne(county_name, list(_IE_COUNTY_TO_PROVINCE.keys()),
                                scorer=fuzz.token_sort_ratio)
    if result and result[1] >= 70:
        province = _IE_COUNTY_TO_PROVINCE[result[0]]
        return {**_IE_PROVINCE_INFO[province],
                "match_method": "ie_fuzzy", "match_score": result[1]}
    return {"adm1_name": None, "geonames_adm1_id": None,
            "iso_3166_2": None, "match_method": "ie_no_match", "match_score": result[1] if result else None}


# ---------------------------------------------------------------------------
# France: map pre-2016 region names to post-2016 GeoNames names
# The 2016 territorial reform merged 22 regions into 13. GeoNames has a mix
# of old and new names; this mapping targets the cases that cause mismatches.
# ---------------------------------------------------------------------------

_FR_OLD_TO_NEW = {
    # Merged into Nouvelle-Aquitaine
    "Aquitaine":        "Nouvelle-Aquitaine",
    "Limousin":         "Nouvelle-Aquitaine",
    "Poitou-Charentes": "Nouvelle-Aquitaine",
    # Merged into Hauts-de-France
    "Nord-Pas-de-Calais": "Hauts-de-France",
    "Picardie":           "Hauts-de-France",
    # Merged into Normandy
    "Haute-Normandie": "Normandy",
    "Basse-Normandie": "Normandy",
    # Merged into Grand Est
    "Alsace":             "Grand Est",
    "Champagne-Ardenne":  "Grand Est",
    "Lorraine":           "Grand Est",
    # Merged into Occitanie
    "Languedoc-Roussillon": "Occitanie",
    "Midi-Pyrénées":        "Occitanie",
    "Midi-Pyrenees":        "Occitanie",
    # Centre renamed
    "Centre": "Centre-Val de Loire",
    # Language differences (not reform-related)
    "Bretagne": "Brittany",
    "Corse":    "Corsica",
}


# ---------------------------------------------------------------------------
# Philippines: aggregate provinces → 17 regions
# GDELT codes Philippines at province/city level (ADM2); GeoNames and GADM
# use regions as ADM1. For cross-national panel compatibility, aggregate up.
# ---------------------------------------------------------------------------

_PH_PROVINCE_TO_REGION = {
    # NCR — National Capital Region
    "Manila": "National Capital Region", "Caloocan": "National Capital Region",
    "Las Piñas": "National Capital Region", "Las Pinas": "National Capital Region",
    "Makati": "National Capital Region", "Malabon": "National Capital Region",
    "Mandaluyong": "National Capital Region", "Marikina": "National Capital Region",
    "Muntinlupa": "National Capital Region", "Navotas": "National Capital Region",
    "Parañaque": "National Capital Region", "Paranaque": "National Capital Region",
    "Pasay": "National Capital Region", "Pasig": "National Capital Region",
    "Quezon City": "National Capital Region", "San Juan": "National Capital Region",
    "Taguig": "National Capital Region", "Valenzuela": "National Capital Region",
    "Metro Manila": "National Capital Region",
    # CAR — Cordillera Administrative Region
    "Abra": "Cordillera", "Apayao": "Cordillera", "Benguet": "Cordillera",
    "Ifugao": "Cordillera", "Kalinga": "Cordillera", "Mountain Province": "Cordillera",
    "Baguio": "Cordillera", "Baguio City": "Cordillera",
    # Region I — Ilocos
    "Ilocos Norte": "Ilocos", "Ilocos Sur": "Ilocos",
    "La Union": "Ilocos", "Pangasinan": "Ilocos",
    "Dagupan": "Ilocos", "Laoag": "Ilocos", "San Fernando": "Ilocos",
    "Vigan": "Ilocos",
    # Region II — Cagayan Valley
    "Batanes": "Cagayan Valley", "Cagayan": "Cagayan Valley",
    "Isabela": "Cagayan Valley", "Nueva Vizcaya": "Cagayan Valley",
    "Quirino": "Cagayan Valley", "Santiago": "Cagayan Valley",
    "Tuguegarao": "Cagayan Valley",
    # Region III — Central Luzon
    "Aurora": "Central Luzon", "Bataan": "Central Luzon", "Bulacan": "Central Luzon",
    "Nueva Ecija": "Central Luzon", "Pampanga": "Central Luzon",
    "Tarlac": "Central Luzon", "Zambales": "Central Luzon",
    "Angeles": "Central Luzon", "Angeles City": "Central Luzon",
    "Olongapo": "Central Luzon", "San Fernando City": "Central Luzon",
    # Region IV-A — CALABARZON
    "Batangas": "Calabarzon", "Cavite": "Calabarzon", "Laguna": "Calabarzon",
    "Quezon": "Calabarzon", "Rizal": "Calabarzon",
    "Antipolo": "Calabarzon", "Calamba": "Calabarzon", "Calamba City": "Calabarzon",
    "Lucena": "Calabarzon", "Lipa": "Calabarzon", "Cavite City": "Calabarzon",
    # Region IV-B — MIMAROPA
    "Marinduque": "Mimaropa", "Occidental Mindoro": "Mimaropa",
    "Oriental Mindoro": "Mimaropa", "Palawan": "Mimaropa", "Romblon": "Mimaropa",
    "Puerto Princesa": "Mimaropa", "Calapan": "Mimaropa",
    # Region V — Bicol
    "Albay": "Bicol Region", "Camarines Norte": "Bicol Region",
    "Camarines Sur": "Bicol Region", "Catanduanes": "Bicol Region",
    "Masbate": "Bicol Region", "Sorsogon": "Bicol Region",
    "Naga": "Bicol Region", "Legazpi": "Bicol Region",
    # Region VI — Western Visayas
    "Aklan": "Western Visayas", "Antique": "Western Visayas",
    "Capiz": "Western Visayas", "Guimaras": "Western Visayas",
    "Iloilo": "Western Visayas", "Negros Occidental": "Western Visayas",
    "Bacolod": "Western Visayas", "Iloilo City": "Western Visayas",
    "Roxas": "Western Visayas",
    # Region VII — Central Visayas
    "Bohol": "Central Visayas", "Cebu": "Central Visayas",
    "Negros Oriental": "Central Visayas", "Siquijor": "Central Visayas",
    "Cebu City": "Central Visayas", "Lapu-Lapu": "Central Visayas",
    "Mandaue": "Central Visayas", "Tagbilaran": "Central Visayas",
    # Region VIII — Eastern Visayas
    "Biliran": "Eastern Visayas", "Eastern Samar": "Eastern Visayas",
    "Leyte": "Eastern Visayas", "Northern Samar": "Eastern Visayas",
    "Samar": "Eastern Visayas", "Southern Leyte": "Eastern Visayas",
    "Tacloban": "Eastern Visayas", "Ormoc": "Eastern Visayas",
    # Region IX — Zamboanga Peninsula
    "Zamboanga del Norte": "Zamboanga Peninsula",
    "Zamboanga del Sur": "Zamboanga Peninsula",
    "Zamboanga Sibugay": "Zamboanga Peninsula",
    "Zamboanga": "Zamboanga Peninsula", "Zamboanga City": "Zamboanga Peninsula",
    "Pagadian": "Zamboanga Peninsula",
    # Region X — Northern Mindanao
    "Bukidnon": "Northern Mindanao", "Camiguin": "Northern Mindanao",
    "Lanao del Norte": "Northern Mindanao", "Misamis Occidental": "Northern Mindanao",
    "Misamis Oriental": "Northern Mindanao",
    "Cagayan de Oro": "Northern Mindanao", "Iligan": "Northern Mindanao",
    "Malaybalay": "Northern Mindanao",
    # Region XI — Davao
    "Compostela Valley": "Davao Region", "Davao de Oro": "Davao Region",
    "Davao del Norte": "Davao Region", "Davao del Sur": "Davao Region",
    "Davao Occidental": "Davao Region", "Davao Oriental": "Davao Region",
    "Davao": "Davao Region", "Davao City": "Davao Region",
    "Tagum": "Davao Region", "Panabo": "Davao Region",
    # Region XII — SOCCSKSARGEN
    "Cotabato": "Soccsksargen", "North Cotabato": "Soccsksargen",
    "Sarangani": "Soccsksargen", "South Cotabato": "Soccsksargen",
    "Sultan Kudarat": "Soccsksargen",
    "General Santos": "Soccsksargen", "Kidapawan": "Soccsksargen",
    "Koronadal": "Soccsksargen",
    # Region XIII — Caraga
    "Agusan del Norte": "Caraga", "Agusan del Sur": "Caraga",
    "Dinagat Islands": "Caraga", "Surigao del Norte": "Caraga",
    "Surigao del Sur": "Caraga", "Butuan": "Caraga", "Surigao": "Caraga",
    # BARMM — Bangsamoro
    "Basilan": "Autonomous Region in Muslim Mindanao",
    "Lanao del Sur": "Autonomous Region in Muslim Mindanao",
    "Maguindanao": "Autonomous Region in Muslim Mindanao",
    "Sulu": "Autonomous Region in Muslim Mindanao",
    "Tawi-Tawi": "Autonomous Region in Muslim Mindanao",
    "Marawi": "Autonomous Region in Muslim Mindanao",
}

# GeoNames entries for PH regions (from admin1CodesASCII.txt inspection)
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

def assign_philippines_region(province_name: str) -> dict:
    """Map a Philippine province/city name to one of the 17 regions."""
    if not province_name or province_name.startswith("("):
        return {"adm1_name": None, "geonames_adm1_id": None,
                "iso_3166_2": None, "match_method": "ph_no_match", "match_score": None}
    # Exact lookup
    region = _PH_PROVINCE_TO_REGION.get(province_name)
    if region:
        info = _PH_REGION_INFO[region]
        return {"adm1_name": region, **info,
                "match_method": "ph_exact", "match_score": 100}
    # Fuzzy fallback
    result = process.extractOne(province_name, list(_PH_PROVINCE_TO_REGION.keys()),
                                scorer=fuzz.token_sort_ratio)
    if result and result[1] >= 70:
        region = _PH_PROVINCE_TO_REGION[result[0]]
        info = _PH_REGION_INFO[region]
        return {"adm1_name": region, **info,
                "match_method": "ph_fuzzy", "match_score": result[1]}
    return {"adm1_name": None, "geonames_adm1_id": None,
            "iso_3166_2": None, "match_method": "ph_no_match",
            "match_score": result[1] if result else None}


# ---------------------------------------------------------------------------
# Load reference data
# ---------------------------------------------------------------------------

def load_fips_to_iso2() -> dict[str, str]:
    """Return dict mapping FIPS 10-4 country code → ISO 3166-1 alpha-2."""
    cols = ['iso2', 'iso3', 'iso_numeric', 'fips', 'country',
            'capital', 'area_km2', 'population', 'continent', 'tld',
            'currency_code', 'currency_name', 'phone', 'postal_format',
            'postal_regex', 'languages', 'geonames_id', 'neighbours',
            'equivalent_fips']
    df = pd.read_csv(COUNTRY_INFO, sep='\t', comment='#',
                     header=None, names=cols, dtype=str)
    df = df[df['fips'].notna() & (df['fips'] != '-')]
    return df.set_index('fips')['iso2'].to_dict()


def load_geonames_adm1() -> pd.DataFrame:
    """Return GeoNames ADM1 table keyed by ISO2 country code."""
    df = pd.read_csv(ADMIN1_CODES, sep='\t', header=None,
                     names=['code', 'adm1_name', 'adm1_name_ascii', 'geonames_adm1_id'],
                     dtype=str)
    df[['iso2_country', 'geonames_adm1_code']] = df['code'].str.split('.', n=1, expand=True)
    df['iso_3166_2'] = df['iso2_country'] + '-' + df['geonames_adm1_code']
    # Add normalized name column for suffix-stripped matching
    df['adm1_name_norm']       = df['adm1_name'].apply(_normalize)
    df['adm1_name_ascii_norm'] = df['adm1_name_ascii'].apply(_normalize)
    return df[['iso2_country', 'geonames_adm1_code', 'iso_3166_2',
               'adm1_name', 'adm1_name_ascii', 'adm1_name_norm',
               'adm1_name_ascii_norm', 'geonames_adm1_id']]


# ---------------------------------------------------------------------------
# Extract ADM1 name from ActionGeo_FullName
# ---------------------------------------------------------------------------

def extract_adm1_name(fullname: str) -> str:
    """
    ActionGeo_FullName format:
      "City, ADM1, Country"  → return second-to-last segment
      "ADM1, Country"        → return first segment
    """
    if not fullname or pd.isna(fullname):
        return ""
    parts = [p.strip() for p in fullname.split(',')]
    if len(parts) >= 3:
        return parts[-2]
    if len(parts) == 2:
        return parts[0]
    return parts[0]


# ---------------------------------------------------------------------------
# Fuzzy matching (general)
# ---------------------------------------------------------------------------

def match_adm1(gdelt_name: str, iso2: str, geonames_adm1: pd.DataFrame) -> dict:
    """Fuzzy-match a GDELT ADM1 name against GeoNames entries for the country."""
    candidates = geonames_adm1[geonames_adm1['iso2_country'] == iso2].copy()
    if candidates.empty:
        return {"adm1_name": None, "geonames_adm1_id": None,
                "iso_3166_2": None, "match_method": "no_candidates",
                "match_score": None}

    gdelt_norm = _normalize(gdelt_name)

    # 1. Exact match (case-insensitive, original name)
    exact = candidates[candidates['adm1_name'].str.lower() == gdelt_name.lower()]
    if not exact.empty:
        row = exact.iloc[0]
        return {"adm1_name": row['adm1_name'], "geonames_adm1_id": row['geonames_adm1_id'],
                "iso_3166_2": row['iso_3166_2'], "match_method": "exact", "match_score": 100}

    # 2. Exact match on ASCII name
    exact_ascii = candidates[candidates['adm1_name_ascii'].str.lower() == gdelt_name.lower()]
    if not exact_ascii.empty:
        row = exact_ascii.iloc[0]
        return {"adm1_name": row['adm1_name'], "geonames_adm1_id": row['geonames_adm1_id'],
                "iso_3166_2": row['iso_3166_2'], "match_method": "exact_ascii", "match_score": 100}

    # 3. Exact match after suffix normalization
    exact_norm = candidates[candidates['adm1_name_norm'] == gdelt_norm]
    if not exact_norm.empty:
        row = exact_norm.iloc[0]
        return {"adm1_name": row['adm1_name'], "geonames_adm1_id": row['geonames_adm1_id'],
                "iso_3166_2": row['iso_3166_2'], "match_method": "exact_norm", "match_score": 100}

    # 4. Fuzzy match on normalized names
    all_norm  = candidates['adm1_name_norm'].tolist()
    all_ascii_norm = candidates['adm1_name_ascii_norm'].tolist()
    combined  = all_norm + all_ascii_norm

    result = process.extractOne(gdelt_norm, combined, scorer=fuzz.token_sort_ratio)
    if result is None:
        return {"adm1_name": None, "geonames_adm1_id": None,
                "iso_3166_2": None, "match_method": "no_match", "match_score": None}

    best_name, score, idx = result
    row = candidates.iloc[idx] if idx < len(all_norm) else candidates.iloc[idx - len(all_norm)]
    method = "fuzzy" if score >= FUZZY_THRESHOLD else "low_confidence"
    return {"adm1_name": row['adm1_name'], "geonames_adm1_id": row['geonames_adm1_id'],
            "iso_3166_2": row['iso_3166_2'], "match_method": method, "match_score": score}


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------

def build():
    print("Loading reference data...")
    fips_to_iso2  = load_fips_to_iso2()
    geonames_adm1 = load_geonames_adm1()
    print(f"  {len(fips_to_iso2)} FIPS→ISO2 mappings")
    print(f"  {len(geonames_adm1)} GeoNames ADM1 entries")

    print("\nLoading GDELT events...")
    events = pq.read_table(
        GDELT_PARQUET,
        columns=['ActionGeo_ADM1Code', 'ActionGeo_FullName', 'ActionGeo_CountryCode']
    ).to_pandas()

    events = events.dropna(subset=['ActionGeo_ADM1Code'])
    most_common_fullname = (events.groupby(['ActionGeo_ADM1Code', 'ActionGeo_FullName'])
                            .size().reset_index(name='n')
                            .sort_values('n', ascending=False)
                            .drop_duplicates('ActionGeo_ADM1Code')
                            [['ActionGeo_ADM1Code', 'ActionGeo_FullName']])
    country_code = (events.groupby('ActionGeo_ADM1Code')['ActionGeo_CountryCode']
                    .first().reset_index())
    unique = most_common_fullname.merge(country_code, on='ActionGeo_ADM1Code')
    unique = unique.rename(columns={
        'ActionGeo_ADM1Code':    'gdelt_adm1_code',
        'ActionGeo_FullName':    'gdelt_fullname',
        'ActionGeo_CountryCode': 'gdelt_country_code',
    })
    print(f"  {len(unique)} unique GDELT ADM1 codes")

    unique['iso2_country']   = unique['gdelt_country_code'].map(fips_to_iso2)
    unique['gdelt_adm1_name'] = unique['gdelt_fullname'].apply(extract_adm1_name)

    no_iso2 = unique['iso2_country'].isna().sum()
    if no_iso2:
        print(f"  Warning: {no_iso2} codes with no FIPS→ISO2 mapping")

    print("\nMatching ADM1 names to GeoNames...")
    results = []
    for i, row in enumerate(unique.itertuples(), 1):
        if i % 100 == 0 or i == len(unique):
            print(f"  {i}/{len(unique)}")

        iso2     = row.iso2_country
        adm1name = row.gdelt_adm1_name

        if pd.isna(iso2):
            match = {"adm1_name": None, "geonames_adm1_id": None,
                     "iso_3166_2": None, "match_method": "no_iso2", "match_score": None}

        elif iso2 == "GB":
            match = assign_uk_nation(adm1name)

        elif iso2 == "IE":
            match = assign_ireland_province(adm1name)

        elif iso2 == "PH":
            match = assign_philippines_region(adm1name)

        elif iso2 == "FR" and adm1name in _FR_OLD_TO_NEW:
            # Remap pre-2016 French region name to post-2016 GeoNames name
            new_name = _FR_OLD_TO_NEW[adm1name]
            match = match_adm1(new_name, "FR", geonames_adm1)
            if match["match_method"] in ("exact", "exact_ascii", "exact_norm", "fuzzy"):
                match["match_method"] = "fr_region_remap"

        else:
            match = match_adm1(adm1name, iso2, geonames_adm1)

        results.append(match)

    match_df = pd.DataFrame(results)
    out = pd.concat([unique.reset_index(drop=True), match_df], axis=1)

    col_order = [
        'gdelt_country_code', 'gdelt_adm1_code', 'gdelt_fullname',
        'gdelt_adm1_name', 'iso2_country',
        'adm1_name', 'geonames_adm1_id', 'iso_3166_2',
        'match_method', 'match_score',
    ]
    out = out[col_order]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    print(f"\nSaved {len(out)} rows → {OUT_CSV}")
    print("\nMatch method breakdown:")
    print(out['match_method'].value_counts().to_string())

    low = out[out['match_method'] == 'low_confidence']
    if not low.empty:
        print(f"\nLow-confidence matches ({len(low)}) — review manually:")
        print(low[['gdelt_adm1_code', 'gdelt_adm1_name', 'iso2_country',
                    'adm1_name', 'match_score']]
              .sort_values('match_score').to_string())


if __name__ == "__main__":
    build()
