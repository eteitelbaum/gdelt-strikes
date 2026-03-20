# GADM Name Matching: Known Gaps and Improvement Options

## Current Status

The `build_gadm_crosswalk.R` script assigns GADM `GID_1` to each validated
strike event using two methods:

1. **Spatial join** (confirmed/unvalidated events): 98% match rate (8,104/8,267)
2. **Exact lowercase name match** (corrected events): 75% match rate (1,393/1,784)

Overall coverage: **94.5%** (9,497/10,050 events with an assignable ADM1).
The 553 unassigned events are a small fraction and unlikely to affect results.

## Why Name Matching Fails (75%)

Failures in the name match for corrected events fall into a few categories:

1. **Diacritics/encoding differences**: GeoNames/GPT returns "Ile-de-France";
   GADM has "Île-de-France". Similarly "Attica" vs "Attiki", "Bavaria" vs
   "Bayern" etc.

2. **Language variants**: GPT returns English names; GADM uses local language
   names for some countries (e.g. "Attiki" not "Attica", "Noord-Holland" not
   "North Holland").

3. **Disputed/special territories**: West Bank, Gaza Strip, Kosovo — not
   represented in GADM or represented differently.

4. **Sub-ADM1 granularity**: Some corrected locations are cities or ADM2
   units with no direct GADM ADM1 match.

## Improvement Options (for R&R or future work)

### Option 1: Fuzzy string matching (recommended first step)
Use `stringdist` package with Jaro-Winkler or optimal string alignment
distance to match `final_adm1_name` against GADM `NAME_1` within the same
country. Would recover most diacritic and minor spelling variant cases.

```r
library(stringdist)
# Match with threshold ~0.1 (Jaro-Winkler, lower = more similar)
stringdistmatrix(query_names, gadm_names, method = "jw")
```

### Option 2: ISO 3166-2 as bridge identifier
The corrected location crosswalk already has `iso_3166_2` codes (from the
GPT batch step). GADM's `HASC_1` field is essentially ISO 3166-2 for most
countries. Joining on `iso_3166_2` ↔ `HASC_1` (after normalizing format
differences like "IN-MH" vs "IN.MH") would be a clean code-based join
avoiding name matching entirely.

This is likely the most reliable option — no fuzzy matching needed, and
codes are unambiguous. Coverage depends on how completely GPT returned
`iso_3166_2` codes (check `corrected_location_crosswalk.csv`).

### Option 3: GeoNames intermediate lookup
GeoNames returns its own standardized name + ISO 3166-2. This is what
`adm1_crosswalk.csv` already has. Could use `adm1_name` from that crosswalk
as the match target instead of GADM `NAME_1` — but this just shifts the
mismatch problem to a different name field.

## Recommended Path

For initial submission: accept 94.5% coverage, note in methods section.

For R&R: implement Option 2 (ISO 3166-2 ↔ HASC_1 join) first — it's clean
and requires no fuzzy logic. Then Option 1 as a fallback for cases where
`iso_3166_2` was missing from the GPT output.
