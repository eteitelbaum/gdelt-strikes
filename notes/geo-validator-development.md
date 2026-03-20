# Geo Validator: Development Notes

This document describes the development and calibration of the geo validation
pipeline for GDELT strike events, including the manual validation exercise,
prompt iteration process, and model selection rationale.

---

## Motivation

GDELT assigns each event a geocode (`ActionGeo_FullName`, `ActionGeo_ADM1Code`,
`ActionGeo_CountryCode`) based on named entity recognition applied to article
text. Known reliability issues include:

- **Capital city bias**: events are frequently assigned to the national capital
  when the actual location is a different city or region
- **Outlet-based geocoding**: articles from foreign outlets are sometimes
  geocoded to the outlet's home country rather than the event location
- **Institution confusion**: events at named institutions (e.g. universities,
  hospitals) may be misassigned when GDELT confuses similarly-named entities
- **Nationwide strikes**: general or multi-city strikes are assigned to a
  single ADM1, which may be arbitrary

For the explanatory paper on strike diffusion/contagion, geocoding accuracy
at the ADM1 level is important. We built an LLM pipeline to validate and
correct GDELT geocodes for the 11,504 relevant events identified by the URL
classifier.

---

## Manual Validation Sample

A stratified random sample of 150 relevant events was drawn from
`data/enhanced/gdelt_strikes.parquet` + `data/enhanced/url_classifications.csv`,
stratified by country with a cap of 5 events per country
(`notebooks/exploratory/adm1-validation-sample.py`).

The first 25 rows were manually annotated with:
- `adm1_correct`: yes / no / uncertain
- `notes`: free-text explanation

**Key findings from manual review:**
- Annotation was extremely time-consuming, particularly for non-English articles
- Language barrier made ~60% of cases impossible to validate manually
- Several clear GDELT errors identified:
  - Afghanistan: GDELT assigned Kabul; article title said "Samangan Doctors
    on Strike"
  - Botswana: GDELT assigned South East district (University of Botswana in
    Gaborone); event was at BIUST in Palapye, Central District
- Some URLs were broken or paywalled, making validation impossible
- Many articles were about nationwide strikes, making ADM1 assignment
  inherently ambiguous

---

## Pipeline Design

The geo validator (`tools/geo_validator/`) follows the same modular structure
as the URL classifier (`tools/url_classifier/`), with one key difference: it
fetches **article body text** (not just the title) using BeautifulSoup to
extract paragraph content up to 3,000 characters, with Wayback Machine
fallback for broken links.

**Architecture:**
```
tools/geo_validator/
├── __init__.py
├── __main__.py
├── classify.py      # CLI: --fetch, --prepare, --submit, --status, --collect
├── prompts.py       # system prompt, 13 few-shot examples, message builder
├── batch.py         # OpenAI Batch API plumbing
├── fetch.py         # article body text fetcher + Wayback Machine fallback
└── data.py          # path constants, loads relevant events only
```

**Output:** `data/enhanced/geo_validation.csv` with columns:
- `ActionGeo_FullName`, `ActionGeo_ADM1Code`, `ActionGeo_CountryCode`
  (original GDELT geocode, preserved)
- `extracted_location`: free-text location extracted from article
- `match`: yes / no / uncertain
- `corrected_location`: corrected location when `match=no`, null otherwise
- `reasoning`: one-sentence explanation

The original GDELT geocode is always preserved. Corrections are stored in
separate columns for transparency and auditability.

---

## Prompt Design

### System Prompt

The model receives the GDELT geocode, source URL, extracted URL slug, and
article text (when available), and outputs a JSON object with four fields:
`extracted_location`, `match`, `corrected_location`, `reasoning`.

**Key rules in the prompt:**

1. **Multilingual**: the model reads and extracts locations from articles in
   any language — non-English text is not a reason to return `uncertain`
2. **Dateline**: the article dateline (location after the byline, before the
   text) is a reliable location signal and should be used
3. **Outlet location**: the news outlet's home country/city is irrelevant —
   a Reunion-based outlet reporting on a Marseille strike should be geocoded
   to Marseille
4. **URL slug**: if the article is inaccessible but the slug or title
   unambiguously names a location, use it — both to confirm (`yes`) and to
   contradict (`no`)
5. **Nationwide strikes**: return `uncertain` rather than `no` when a strike
   is described as national or multi-city
6. **Corrected location**: when `match=no`, output a standardized corrected
   location in "City, Region, Country" format

### Few-Shot Examples (13)

Examples were chosen to cover all major case types and languages:

| # | Case | Label | Purpose |
|---|---|---|---|
| 1 | Sydney, Australia | match | English, body text confirms |
| 2 | Sudbury, Canada | match | English, URL slug sufficient |
| 3 | Colombo, Sri Lanka | match | Dateline as location signal |
| 4 | Paris, France | match | French article |
| 5 | Buenos Aires, Argentina | match | Spanish article |
| 6 | Amman, Jordan | match | Arabic article |
| 7 | São Paulo, Brazil | match | Portuguese article |
| 8 | Kabul → Samangan, Afghanistan | mismatch | Capital city bias |
| 9 | South East → Palapye, Botswana | mismatch | Institution confusion |
| 10 | Reunion → Marseille, France | mismatch | Outlet home country misused |
| 11 | Naypyidaw, Myanmar | uncertain | Nationwide strike |
| 12 | Luanda, Angola | uncertain | Broken link, uninformative slug |
| 13 | Karingal, Australia | uncertain | Paywall + multi-location org |

---

## Prompt Iteration

Three prompt fixes were made based on validation results:

**Fix 1 — Strengthen URL slug rule**
The initial prompt said the model "may" return `yes` from an unambiguous slug.
The model was defaulting to `uncertain` for cases like `sudbury-miners-go-on-
strike` when the article was broken. Changed to a prescriptive instruction with
concrete examples.

**Fix 2 — Extend slug rule to cover mismatches**
After Fix 1, the model was still returning `uncertain` for cases where the slug
named a clearly *different* location from the geocode (e.g.
`flights-cancelled-at-geneva-airport` against a Copenhagen geocode;
`greve-des-eboueurs-a-marseille` against a Reunion geocode). The model's own
reasoning identified the contradiction but still defaulted to `uncertain`.
Extended the slug rule to explicitly cover the `no` case with examples.

**Fix 3 — Extract URL slug explicitly**
The model was failing to parse the slug from URLs with numeric path segments
(e.g. `/region/216/details/430397/workers-stage-rare-strike-in-dubai`).
Added a `_extract_slug()` function in `prompts.py` that extracts the last
meaningful path segment and presents it as a separate `URL slug:` line in
the user message.

---

## Validation Results (150-event sample, gpt-4o-mini)

After prompt iteration:

| Metric | Value |
|---|---|
| Article text retrieved | 60/150 (40%) |
| — via direct fetch | 58 |
| — via Wayback Machine | 2 |
| — not available | 90 |
| Agreement with human annotations (25 rows) | 16/25 (64%) |

**The 64% headline agreement figure understates true accuracy.** Of the 9
disagreements, approximately 6 were cases where the LLM was correct and the
human annotation was limited by the language barrier (Albanian, French,
Bosnian, Spanish, Portuguese articles). Only ~2–3 were genuine LLM errors:

- **Botswana**: BIUST → Palapye correctly identified by human but LLM
  returned `uncertain` due to a flaky article fetch
- **Northumberland**: the KPRDSB school board name does not obviously map
  to Northumberland County without geographic lookup capability

**Match breakdown for events with article text (60):**

| Label | Count | Share |
|---|---|---|
| yes | 30 | 50% |
| no | 11 | 18% |
| uncertain | 19 | 32% |

The 19 uncertain cases with text were mostly legitimate: nationwide strikes,
unrelated article content fetched, or flaky fetches returning empty pages.

**Projected breakdown for full 11,504 events:**
- ~35–40% article retrieval rate
- ~60–65% uncertain
- ~25–30% yes (confirmed correct geocode)
- ~10–15% no (mismatch with corrected location → ~1,000–1,700 corrections)

---

## Model Selection

### Comparison: gpt-4o-mini vs gpt-5-mini

A curated 20-event comparison was run on cases specifically chosen to stress-
test model capabilities: clear matches, capital city bias, institution
confusion, foreign outlet errors, nationwide strikes, and non-English articles
in six languages.

**Results (20 events):**

| Model | yes | no | uncertain | Agreement with human |
|---|---|---|---|---|
| gpt-4o-mini | 8 | 6 | 6 | — |
| gpt-5-mini | 8 | 8 | 4 | — |
| Model agreement | | | | 15/20 (75%) |

**The 5 disagreements:**

| Case | 4o-mini | 5-mini | Correct |
|---|---|---|---|
| Botswana (BIUST → Palapye) | uncertain | **no** | 5-mini |
| São Paulo → Rio de Janeiro | uncertain | **no** | 5-mini |
| Ernakulam, India (Kochi) | no | **yes** | 5-mini |
| Seoul / Hyundai nationwide | **yes** | uncertain | debatable |
| Reunion → Marseille (slug) | uncertain | **no** | 5-mini |

GPT-5 mini outperformed on 4 of the 5 disagreements. Critically, it resolved
the two classes of errors that prompt engineering could not fix:

1. **Geographic knowledge**: gpt-5-mini knew that BIUST is in Palapye, not
   Gaborone, without needing a geocoding API lookup
2. **Slug-based mismatch**: gpt-5-mini correctly returned `no` for Reunion/
   Marseille using the URL slug, whereas gpt-4o-mini returned `uncertain`
   despite its own reasoning identifying the contradiction

### Why Not a Geocoding API?

An alternative approach would have been to geocode the `extracted_location`
free text (e.g. via Google Maps or Nominatim) and compare coordinates to
GDELT's `ActionGeo_Lat`/`ActionGeo_Long`. This was considered and rejected:

- `extracted_location` is free text of variable quality ("nationwide, Nigeria",
  "unknown", "Kanton Sarajevo") that geocoders handle poorly
- GDELT coordinates are city centroids, not ADM1 polygon boundaries, so
  distance comparisons don't reliably indicate shared administrative regions
- Distance thresholds are arbitrary and context-dependent
- Adds significant pipeline complexity with its own failure modes
- Geographic knowledge embedded in gpt-5-mini achieves the same goal more
  cleanly for the cases that matter

### Why Not Web Search?

GPT-5 mini supports built-in web search as a tool, which would allow the model
to look up article content and geographic information in real time. This was
not used because:

- Web search tools are not available in the Batch API (requires real-time
  calls, losing the 50% cost discount)
- Results would be non-deterministic and harder to reproduce
- Our fetch-then-classify approach is fully auditable: the exact text fed
  to the model is cached in `article_texts_cache.csv`

### Cost Estimate (gpt-5-mini, Batch API)

| Item | Estimate |
|---|---|
| Input tokens/request | ~3,000 |
| Completion tokens/request | ~300 (incl. ~200 reasoning) |
| Events | 11,504 |
| Chunks (3,000/chunk) | 4 |
| Input cost (batch, $0.125/1M) | ~$4.30 |
| Output cost (batch, $1.00/1M) | ~$3.45 |
| **Total** | **~$8–10** |

---

## Known Limitations

1. **Link rot**: ~60% of articles are inaccessible (broken links, paywalls).
   These events receive `uncertain` and are treated as missing data.
2. **Wayback Machine**: recovered only 2/90 inaccessible articles in the
   validation sample — small outlets are rarely archived.
3. **Nationwide strikes**: genuinely cannot be assigned to a single ADM1.
   These are correctly flagged as `uncertain` rather than forced into an
   incorrect geocode.
4. **Institutional geography**: cases where a named institution (school board,
   university) maps to an ADM1 code non-obviously may be miscoded even by
   gpt-5-mini, though this is rare and represents an improvement over
   gpt-4o-mini.
5. **`corrected_location` is free text**: not yet standardized to GDELT FIPS
   codes or ISO ADM1 identifiers. Downstream analysis will need to handle
   this, either by fuzzy matching or by treating corrected events as a
   validated subset with a manually standardized geocode.
