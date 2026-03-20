# Geo Validation: Preliminary Results

This note summarizes the results of the LLM-based geocode validation pipeline
applied to all 11,504 relevant GDELT strike events identified by the URL
classifier. See `geo-validator-development.md` for pipeline design and
methodology details.

---

## Overall Results

| Label | Count | Share of all events |
|---|---|---|
| yes (confirmed correct) | 3,430 | 29.8% |
| no (mismatch, corrected) | 1,806 | 15.7% |
| uncertain | 6,267 | 54.5% |

**Among events with a definitive verdict (yes or no): 34.5% were miscoded.**
This is a substantially higher error rate than might be expected and
underscores the importance of geocode validation for ADM1-level spatial
analysis.

The uncertain category is dominated by link rot (~60% of articles
inaccessible) and genuinely nationwide or multi-city strikes. It does not
indicate model failure — these events are treated as missing data in
downstream analysis.

---

## Corrections by Country

### Absolute correction counts (top 15)

| Country | Corrections |
|---|---|
| United States | 507 |
| India | 146 |
| Canada | 129 |
| United Kingdom | 120 |
| Brazil | 76 |
| France | 62 |
| Italy | 54 |
| Mexico | 50 |
| Spain | 43 |
| Serbia/Russia | 40 |
| Israel | 39 |
| Germany | 31 |
| Greece | 30 |
| Côte d'Ivoire | 30 |
| Australia | 29 |

The US dominates in absolute terms because it has the largest number of
relevant events in the dataset.

### Error rate by country (min 20 validated events, top 15)

| Country | Validated | Corrections | Error rate |
|---|---|---|---|
| China | 22 | 21 | 95% |
| Russia | 52 | 40 | 77% |
| Ukraine | 23 | 17 | 74% |
| Côte d'Ivoire | 41 | 30 | 73% |
| Mexico | 71 | 50 | 70% |
| Israel | 61 | 39 | 64% |
| Venezuela | 35 | 20 | 57% |
| Turkey | 20 | 11 | 55% |
| Canada | 264 | 129 | 49% |
| Brazil | 191 | 76 | 40% |
| United Kingdom | 311 | 120 | 39% |
| Poland | 29 | 11 | 38% |
| Peru | 29 | 11 | 38% |
| Australia | 81 | 29 | 36% |
| Germany | 95 | 31 | 33% |

The extreme error rates for China (95%), Russia (77%), and Ukraine (74%)
almost certainly reflect **outlet-based geocoding**: English-language coverage
of strikes in these countries is often written by foreign bureaux or
wire services, and GDELT codes the event to the outlet's location rather than
the strike location. These events are essentially unusable without correction.

The high rate for Israel (64%) likely reflects the Gaza/West Bank
geopolitical coding problem — events in Palestinian territories are
sometimes assigned to Israeli locations.

Canada (49%) and UK (39%) are surprisingly high and suggest systematic
sub-national misassignment within English-speaking countries, where GDELT's
NER may pick up the wrong named entity (e.g., a province-level organization
name coded to the wrong city).

---

## Error Typology

Based on manual review of a random sample of corrections, the errors fall
into several recognizable categories:

### 1. Outlet home country / foreign bureau geocoding
GDELT assigns the event to the outlet's location rather than where the
strike occurred.

- `London, UK` → `Los Angeles, CA` (SAG-AFTRA/WGA Hollywood strike reported
  by UK outlet)
- `Moscow, Russia` → `England, UK` (McDonald's workers strike in Cambridge
  and Crewe reported by Russian outlet)
- `Gaza, Israel` → `Gaza Strip, Palestine` (UNRWA staff strike miscoded to
  Israeli location)

### 2. Capital city bias
GDELT assigns events to the national or state capital rather than the
actual location.

- `Patna, Bihar` → `New Delhi, Delhi` (AIIMS doctors strike; Patna is the
  Bihar capital, not where AIIMS is located)
- `Paris, France` → `Brest, Brittany` (Naval Group security workers strike;
  slug names Brest unambiguously)
- `Lussac, Poitou-Charentes` → `La Vaupalière, Normandy` (wrong region
  entirely)

### 3. Institution confusion
GDELT NER identifies an institution name and maps it to the wrong location
when similarly-named institutions exist elsewhere.

- `Vancouver, BC` → `Ontario` (LCBO strike slug names Ontario)
- `Queens, New Brunswick` → `Los Angeles / Western Canada` (hotel strike
  article covers multiple locations; NER picked wrong entity)
- `Telangana, Andhra Pradesh` → `Hyderabad, Telangana` (URL path `/city/
  hyderabad/` contradicts GDELT's assignment to Andhra Pradesh)

### 4. Wrong country entirely
Most dramatic errors: the event is assigned to a different country.

- `Georgia, United States` → `Barrie, Ontario, Canada` (Georgian College
  in Ontario confused with the US state of Georgia)
- `Broadmoor, California` → `New Orleans, Louisiana` (sanitation workers
  strike; slug names New Orleans)
- `Nevada, United States` → `Santa Monica, California` (hotel workers
  strike; article names Santa Monica)
- `Jerusalem, Israel` → `West Bank, Palestine` (general strike; slug in
  Turkish names Bati Seria = West Bank)
- `Covilhã, Portugal` → `Lisbon` (Lisbon metro strike slugged as
  `nova-greve-do-metro-de-lisboa`)

### 5. Sub-national misassignment within correct country
The country is right but the ADM1 is wrong — often because GDELT picks up
a well-known city or institution elsewhere in the article rather than the
dateline location.

- `Jalisco, Baja California` → `Mexico City` (hunger strike in Reclusorio
  Norte prison; Jalisco is mentioned in passing)
- `Tharaka, Eastern, Kenya` → `Nyeri, Central, Kenya` (doctors' strike
  slug names Nyeri)

---

## Implications for the Explanatory Paper

1. **~1,806 events (~16%) have corrected geocodes** that should be used
   in place of GDELT's original assignment for ADM1-level spatial analysis.

2. **~3,430 events (30%) are confirmed correct** — a validated subset with
   high confidence geocodes.

3. **~6,267 events (54%) are uncertain** — predominantly broken links. These
   retain the original GDELT geocode but should be treated as unvalidated
   in robustness checks.

4. **Country-level bias is severe for China, Russia, and Ukraine** (~70–95%
   error rate). Any ADM1-level analysis involving these countries should
   either exclude unvalidated events or restrict to the confirmed-correct
   subset.

5. **A `geo_quality` indicator variable** (values: `confirmed`, `corrected`,
   `unvalidated`) can be constructed from the `match` column and used as a
   control or for sample restriction in regression models.

---

## Next Steps

- Merge `geo_validation.csv` into the analysis dataset, applying
  `corrected_location` for `match == "no"` events
- Standardize `corrected_location` free text to GDELT FIPS ADM1 codes or
  ISO codes for the ~1,806 corrected events (fuzzy matching or manual
  review for the ambiguous cases)
- Create `geo_quality` indicator for use in regression specifications
- Consider whether to treat the 54% uncertain events as (a) using original
  GDELT geocode, (b) dropped from ADM1-level models, or (c) included with
  a quality weight
