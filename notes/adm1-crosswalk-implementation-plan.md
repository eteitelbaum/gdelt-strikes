# ADM1 Crosswalk: Implementation Plan

This note is the single authoritative reference for building a crosswalk from
GDELT's FIPS 10-4 ADM1 codes to modern standardized identifiers, and applying
it to the geo-validated strike event data. Written to survive context resets.

---

## Background and Motivation

GDELT encodes event locations using **FIPS 10-4**, a US federal government
standard (published by NIST, retired 2008 but still used by GDELT for archive
consistency). Format:
- `ActionGeo_CountryCode`: 2-char FIPS country code (e.g. `TU` = Turkey)
- `ActionGeo_ADM1Code`: 4-char code = FIPS country + FIPS ADM1 (e.g. `TU90` = Kilis)

To merge GDELT events with modern political science datasets we need a
crosswalk from FIPS ADM1 codes to identifiers used by those datasets.

---

## What the Target Datasets Actually Use

Investigated thoroughly (2026-03-18). The identifier landscape is fragmented:

| Dataset | ADM1 join method | Identifier |
|---|---|---|
| ACLED | Text match on GADM admin1 name | `NAME_1` from GADM shapefile |
| SHDI (Global Data Lab) | Spatial join against GDL polygons | GDL-Code (e.g. `AFGr101`) |
| UCDP GED | Spatial join (event coords → GADM polygons) | `GID_1` / `NAME_1` from GADM |
| Nighttime lights | Raster aggregation against GADM ADM1 polygons | `GID_1` / `NAME_1` from GADM |
| Gridded GDP | Same as nighttime lights | Same |
| OECD Regional | Code join | ISO 3166-2 |
| Eurostat | Code join | NUTS2 (= ISO 3166-2 for most EU) |

**Key findings:**

- **GADM 4.1** ships `GID_1` (idiosyncratic GADM code), `HASC_1` (Statoids
  codes), and `NAME_1`. It does **not** include GeoNames IDs or ISO 3166-2
  natively. No pre-built FIPS → GADM crosswalk exists because GADM GID_1 is
  GADM's own invention, independent of all other standards.

- **SHDI** uses GDL-Code, not GADM GID_1. GDL regions are often **aggregations
  of multiple GADM ADM1 units** (e.g. `AFGr101` = "Central: Kabul, Wardak,
  Kapisa, Logar..."). GDL publishes their own shapefiles (V6.6 downloaded to
  `docs/gdl/`). The GDL Codes V6.6 file has only 5 columns: `iso_code`,
  `country`, `continent`, `gdlcode`, `region` — no ISO 3166-2, no GADM GID_1.
  **Merging with SHDI requires a spatial join** (GADM ADM1 polygons against GDL
  polygons to assign each GADM ADM1 to a GDL region), not a code lookup.

- **ACLED** ships only `admin1` text names (GADM-derived) — no code field.
  Name-based matching is unavoidable.

- **Spatial datasets** (nighttime lights, UCDP GED, gridded GDP): aggregate
  to GADM ADM1 polygons during data construction; results carry `NAME_1`. Link
  back to FIPS via the crosswalk `adm1_name` field.

- **Text joins to SHDI/ACLED are unavoidable** regardless of the hub
  identifier. The best we can do is provide a standardized `adm1_name` that
  minimizes mismatch rate against GADM `NAME_1`.

**Therefore, the crosswalk targets two output identifiers:**
1. `adm1_name` — standardized name (GeoNames-derived, close to GADM `NAME_1`);
   primary join anchor for ACLED and spatial dataset results
2. `iso_3166_2` — clean code join for OECD/Eurostat

The GeoNames ID is retained as an intermediate key and stable internal
reference, but it is not the final merge key for any target dataset.

---

## Scope: Full FIPS 10-4 Table

The crosswalk covers **all codes in the full FIPS 10-4 subdivision table**
(~3,000–4,000 entries), not just the ~1,549 codes appearing in our GDELT data.
Reasons:
- Same effort as a partial crosswalk; permanent reusable asset
- Edge cases (dissolved states, disputed territories, admin reforms) resolved
  once
- Our GDELT codes are a simple subset lookup into the complete table

---

## Reference Files Already Downloaded

### `docs/geonames/`
- `countryInfo.txt` — 249 countries; FIPS code (col 4), ISO2 (col 1), GeoNames
  country ID (col 17). Source: https://download.geonames.org/export/dump/countryInfo.txt
- `admin1CodesASCII.txt` — 3,862 ADM1 regions; format `ISO2.code → name,
  name_ascii, GeoNames_ID`. Source: https://download.geonames.org/export/dump/admin1CodesASCII.txt

### `docs/gdl/`
- `GDL Codes V6.6.xlsx` — GDL regional codes and names (1,810 rows). Columns:
  `iso_code`, `country`, `continent`, `gdlcode`, `region`. No standard
  geographic identifiers beyond ISO3 country code. Downloaded 2026-03-18.

### `data/reference/adm1_crosswalk.csv` (interim, to be superseded)
Built by `tools/adm1_crosswalk/build.py` using fuzzy name matching against
GDELT's garbled `ActionGeo_FullName` strings. 1,549 rows; 70% high-confidence.
Will be replaced by the GeoNames API build (Step 2).

Country-specific handlers already implemented and kept (logic in `build.py`
will be reused in `build_api.py`):
- **UK**: GDELT at LAD level → aggregate to 4 nations (England/Scotland/
  Wales/Northern Ireland)
- **Ireland**: county level → 4 provinces (Connacht/Leinster/Munster/Ulster)
- **Philippines**: province level → 17 regions (GADM/GeoNames treat regions
  as ADM1 for PH)
- **France**: pre-2016 region names → post-2016 merged names (e.g. Aquitaine →
  Nouvelle-Aquitaine)

### `data/enhanced/geo_validation.csv`
11,503 rows — LLM (gpt-4o-mini) geo-validation results. Key columns:
- `match`: yes (3,430) / no (1,806) / uncertain (6,267)
- `corrected_location`: free-text corrected location for `match=no` events

---

## Why the GeoNames API

No direct code-to-code mapping from FIPS 10-4 ADM1 codes to GeoNames IDs
(or any other modern system) exists as a published table. The FIPS ADM1 suffix
(e.g. `90` in `TU90`) and GeoNames' admin codes (e.g. `80` in `TR.80`) are
independent numeric sequences. Name matching is unavoidable.

The GeoNames API is better than our current fuzzy matching against bulk files
because:
- Uses GeoNames' own search index (handles transliterations, alternate names)
- Can be filtered by country and feature class/code (ADM1, ADM2, etc.)
- Returns ISO 3166-2 code directly alongside the standardized name
- Free (30,000 requests/day with a free account)
- Using official FIPS ADM1 names (from the NGA table) as query strings — not
  GDELT's garbled `ActionGeo_FullName` — gives much cleaner results

**API endpoint** (direct `requests` calls, no extra dependencies):
```
http://api.geonames.org/searchJSON
  ?q={fips_adm1_name}
  &country={ISO2}
  &featureCode=ADM1
  &maxRows=1
  &username={USERNAME}
```
GeoNames account: register at https://www.geonames.org/login, then activate
free web services at https://www.geonames.org/enablefreewebservice (this step
is required but not linked from the account page — easy to miss).

---

## Implementation Plan

### Step 1 — Download Full FIPS 10-4 Subdivision Table
**Why**: gives the official FIPS ADM1 name for every code (e.g. `TU90` →
"Kilis"), which is the clean query string for the GeoNames API. Covers all
~3,000+ codes, not just those in our data.

**Source**: efele.net/maps/fips-10/data/ (archives the full NGA FIPS 10-4
dataset in machine-readable form)
**Output**: `docs/fips/fips10-4-subdivisions.csv`
**Script**: `tools/adm1_crosswalk/fetch_fips_table.py` (written, needs testing)

### Step 2 — Build Full Crosswalk via GeoNames API
**Input**: all codes in `docs/fips/fips10-4-subdivisions.csv`

**Process**:
1. For each FIPS ADM1 code:
   a. Get official FIPS ADM1 name from Step 1 table
   b. Map FIPS country code → ISO2 (via `countryInfo.txt`)
   c. Query GeoNames API: `search?q={fips_name}&country={ISO2}&featureCode=ADM1`
   d. Take top result; if no ADM1 result, try `featureCode=ADM2`, then no
      feature filter
   e. Record GeoNames ID, standardized name, ISO 3166-2 code
2. Apply country-specific overrides (UK/IE/PH/FR — already in `build.py`)
3. Flag cases needing manual review:
   - No API result found
   - Known edge cases (dissolved states, disputed territories, etc.)

**Known edge cases**:
- Dissolved states: USSR republics, Yugoslavia, Czechoslovakia, Sudan
  (pre-South Sudan), Netherlands Antilles
- Disputed territories: Palestine/Israel, Western Sahara, Kosovo, Taiwan,
  Crimea/Ukraine
- Administrative reforms: French regions pre/post-2016 (handled), Ethiopian
  regions, Nigerian state creation
- Country-level codes: GDELT `XX00` codes with no real ADM1 → flag as
  `country_level`

**Output**: `data/reference/adm1_crosswalk.csv` (rebuilt, complete)

Columns:
- `fips_country` — FIPS 10-4 country code
- `fips_adm1` — FIPS 10-4 ADM1 code (4-char)
- `fips_adm1_name` — official FIPS name (from NGA/efele table)
- `iso2_country` — ISO 3166-1 alpha-2
- `geonames_adm1_id` — GeoNames ADM1 ID (stable internal reference)
- `adm1_name` — GeoNames standardized ADM1 name (primary join anchor)
- `iso_3166_2` — ISO 3166-2 subdivision code (for OECD/Eurostat)
- `match_method` — api / country_specific / manual / country_level / no_match
- `notes` — edge case documentation

**Script**: `tools/adm1_crosswalk/build_api.py` (to be written)

### Step 3 — Manual Review of Edge Cases
Review flagged rows from Step 2. Expected ~50–100. Update `notes` and
`match_method = "manual"` for resolved rows.

### Step 4 — Standardize Corrected Locations
**Input**: 1,806 rows from `geo_validation.csv` where `match=no`, with
`corrected_location` free-text strings (e.g. "Nagpur, Maharashtra, India")

**Approach**: OpenAI Batch API (gpt-4o-mini), NOT GeoNames.

**Rationale**: The corrected_location strings were already generated by GPT
and are clean, structured "City, Region, Country" strings. GeoNames would
add accuracy for ambiguous raw strings but the 6-hour rate-limited wait
is not justified here. GPT-4o-mini knows ISO 3166-2 codes well for the
countries appearing in a 2015–2025 strike dataset. Batch API finishes in
minutes, costs ~$1–2, and uses the same infrastructure as geo-validation.

**Process**:
1. `--prepare`: build JSONL batch from no-match rows; parse multi-location
   semicolons (take first); strip parentheticals
2. `--submit`: upload to OpenAI Files API; create batch job
3. `--status`: check batch progress
4. `--collect`: download results → `corrected_location_crosswalk.csv`

**Edge cases handled**:
- Multi-location (semicolons): take first location
- Nationwide / country-only strings: `match_method = country_level`
- Unresolvable: `match_method = unresolvable`

**Output**: `data/reference/corrected_location_crosswalk.csv`
Columns: `GLOBALEVENTID`, `corrected_location`, `adm1_name`, `iso_3166_2`,
`country_iso2`, `match_method`

**Script**: `tools/adm1_crosswalk/apply_corrections.py` (written 2026-03-18)
**CLI**:
```
python -m tools.adm1_crosswalk.apply_corrections --prepare
python -m tools.adm1_crosswalk.apply_corrections --submit
python -m tools.adm1_crosswalk.apply_corrections --status
python -m tools.adm1_crosswalk.apply_corrections --collect
```

### Step 5 — Build Unified Analysis Column
**Input**: `geo_validation.csv` + `adm1_crosswalk.csv` +
`corrected_location_crosswalk.csv`

**Logic**:
```
for each event:
  if match == "no":
    use corrected_location_crosswalk → final identifiers
  else:  # match == "yes" or "uncertain"
    use fips_adm1 → adm1_crosswalk → final identifiers
```

**Output**: `data/enhanced/geo_validation_final.csv`
New columns: `final_geonames_adm1_id`, `final_adm1_name`, `final_iso_3166_2`,
`geo_quality` ("corrected" / "confirmed" / "unvalidated")

**Script**: `tools/adm1_crosswalk/apply.py` (to be written)

---

## Downstream Merge Workflows

Once `geo_validation_final.csv` exists:

| Dataset | Merge approach | Join key |
|---|---|---|
| ACLED | Name match on `final_adm1_name` vs ACLED `admin1` | Text (unavoidable) |
| SHDI | Spatial join: GADM ADM1 polygons → GDL polygons → `gdlcode` | Spatial |
| UCDP GED | Spatial join: event coords → GADM ADM1 polygons → `NAME_1` → `final_adm1_name` | Spatial then name |
| Nighttime lights | Raster aggregation to GADM ADM1 → `NAME_1` → `final_adm1_name` | Spatial then name |
| Gridded GDP | Same as nighttime lights | Spatial then name |
| OECD Regional | `final_iso_3166_2` | Code (clean) |
| Eurostat | `final_iso_3166_2` | Code (clean) |
| V-Dem, WDI, etc. | Country level only — R `countrycode` package at analysis time | Country code |

Note: the GADM ADM1 → GDL region aggregation needed for SHDI is a one-time
spatial operation using GDL V6.6 shapefiles (downloaded). It produces a
`gadm_name → gdlcode` lookup table as a separate artifact.

---

## Files and Scripts Summary

```
tools/adm1_crosswalk/
├── build.py              # superseded fuzzy-match version (kept for reference)
├── fetch_fips_table.py   # Step 1: download NGA FIPS 10-4 subdivision table
├── build_api.py          # Step 2: build full crosswalk via GeoNames API
├── apply_corrections.py  # Step 4: standardize corrected_location strings
└── apply.py              # Step 5: build unified final column

docs/
├── geonames/
│   ├── countryInfo.txt          # FIPS ↔ ISO2 country mapping (downloaded)
│   └── admin1CodesASCII.txt     # GeoNames ADM1 names (downloaded)
├── fips/
│   └── fips10-4-subdivisions.csv  # Step 1 output (full FIPS table)
└── gdl/
    └── GDL Codes V6.6.xlsx      # GDL region codes (downloaded 2026-03-18)

data/reference/
├── adm1_crosswalk.csv               # Step 2 output (full crosswalk)
└── corrected_location_crosswalk.csv # Step 4 output

data/enhanced/
├── geo_validation.csv          # existing (gpt-4o-mini output)
└── geo_validation_final.csv    # Step 5 output (analysis-ready)
```

---

## Open Questions / Decisions Deferred

1. **GADM version**: pin to GADM 4.1 for reproducibility. Document version in
   all spatial join scripts.
2. **Dissolved states**: USSR-era events — recode to successor state by city
   name. Document each decision.
3. **Disputed territories**: Palestine events — code to Palestinian Authority
   ADM1 or flag separately? Has implications for analysis sample.
4. **`geo_quality` in models**: treat `uncertain` events as (a) using original
   GDELT geocode, (b) dropped, or (c) included with quality weight. Deferred
   to modeling stage.
5. **Philippines BARMM**: renamed from ARMM in 2019; handle by event date in
   country-specific override.
6. **SHDI spatial aggregation**: GADM ADM1 → GDL region join needs to happen
   before SHDI merge. Build as a separate one-time script producing a
   `gadm_name → gdlcode` lookup.
