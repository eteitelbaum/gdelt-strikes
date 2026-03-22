# Data Section Outline

## Notes Used

- `notes/gdelt-data-citations.md` — GDELT validation strategy, false positive
  problem, URL classifier approach and citations, external validation alternatives,
  geolocation attenuation argument
- `notes/gdelt-geolocation-reliability.md` — geolocation mechanics, known
  reliability issues (capital city bias, paywalled sources), key literature
- `notes/geo-validation-results.md` — geocode validator results: 34.5% mismatch
  rate, country-level error rates, error typology
- `notes/methods-notes.md` §1 — ADM1 unit selection rationale, panel scope
  condition, comparison to ACLED-based studies
- `papers/contagion/contagion-paper.qmd` — current Data section text (lines 123–176)

---

**Current paper status**: The existing Data section covers the basics (GDELT source,
panel construction, neighbor definition, treatment variable, V-Dem moderators) but is
thin on the validation pipeline and missing the geo-validation results entirely.
The section needs to be substantially expanded before it can stand on its own at
3–4 pages.

---

## 1. Strike Events: GDELT

**What's already in the paper**: GDELT introduced, CAMEO 143 extraction, coordinate
filtering, spatial join to GADM, 93% assignment rate, uneven coverage acknowledged.

**What's missing**:

### 1a. CAMEO definitional scope
- CAMEO code 143 groups labor strikes, boycotts, and work stoppages under a single
  event type. This is the definitional ambiguity that motivates the LLM filter.
- Cite: Schrodt (2012) CAMEO codebook; Halterman & Keith (2025) who note explicitly
  that CAMEO includes labor strikes while the Crowd Counting Consortium excludes them —
  our filter operationalizes the conceptual cut that CAMEO does not make.
- The filtering step is not merely noise reduction; it produces a measure of *labor
  strikes specifically* rather than CAMEO's broader protest category.

### 1b. The false positive problem
- Raw GDELT events have high false positive rates: Wang et al. (2016, *Science*)
  found only 21% of valid GDELT protest URLs actually covered a protest event.
- This is the foundational empirical finding motivating any filtering step.
- Hoffmann et al. (2022) document that even after SVM classification, their
  validated dataset was 3,564 events from 379,747 raw GDELT records in six
  European countries — one order of magnitude reduction.

---

## 2. Validation Pipeline (NEW — not in paper)

This is the section's main gap and biggest opportunity. The two-stage validation
pipeline is a methodological contribution in its own right.

### 2a. URL classifier
- Approach: LLM few-shot classification (GPT-4) on URL + headline text, following
  the codebook LLM framework of Halterman & Keith (2025).
- Scale: 181 countries, 10 years — feasible via OpenAI batch API where Hoffmann
  et al.'s GPU + full-text approach was not.
- Input: URL + headline (sufficient signal for strike events, which almost always
  name location and dispute in the headline).
- Contrast with Hoffmann et al. (2022): their SVM + full-text approach required
  GPU cluster and was limited to 6 countries. Our LLM approach achieves comparable
  conceptual precision at global scale.
- Output: 11,503 validated events retained from ~30,900 raw CAMEO-143 events.
- **Still needed**: Precision/recall figures from the validation sample to parallel
  Hoffmann et al.'s P=0.74, R=0.83. This is needed to respond to reviewer requests.

### 2b. Geocode validator
- After URL classification, a second LLM pass checks whether GDELT's ADM1
  geolocation is correct for each validated event (again using URL + headline).
- Results: Among events with a definitive verdict (yes/no), **34.5% were
  miscoded** (1,806 corrected; 3,430 confirmed; 6,267 uncertain/broken links).
- Dominant error types: outlet-based geocoding (foreign bureaux assigned to outlet
  location), capital city bias, institution name confusion.
- Country-level error rates: China 95%, Russia 77%, Ukraine 74% — driven by
  foreign bureau reporting. High rates also for Israel (64%), Mexico (70%).
- These corrections are applied before constructing the analysis panel.
- **Geo-quality indicator**: events coded as `confirmed`, `corrected`, or
  `unvalidated` (uncertain). Used in robustness checks.

### 2c. Geolocation measurement error
- Even after correction, geolocation introduces noise. Classical measurement error
  in the treatment variable (neighbor's ADM1 assignment) attenuates spatial
  diffusion coefficients toward zero — a conservative bias.
- "To the extent that GDELT mislabels some strike events to the wrong ADM1 region,
  our estimates of geographic neighbor effects are attenuated and should be
  interpreted as lower bounds on the true geographic diffusion effect."
- Country×week FEs absorb capital city bias: capital bias systematically assigns
  events to the capital's ADM1 unit, but our FE design identifies from variation
  *across* ADM1 units within the same country-week.
- Cite: Hammond & Weidmann (2014, *Research & Politics*) — documents dateline bias
  and ADM1-level degradation in machine-coded event data.

### 2d. External validation
- No gold-standard global strike database exists against which to validate our
  measure at scale. Main alternatives: ILO (country-level annual, spotty coverage),
  ETUI (European only), national administrative records (country-specific).
- The absence of a global database is part of the substantive motivation for this
  paper. Acknowledge directly.
- Ward et al. (2013) show GDELT and ICEWS share ~71% of variance for major protest
  events after filtering — filtered GDELT signal is real, though both share
  coverage biases.

---

## 3. Panel Construction

**What's already in the paper**: ADM1-week aggregation, binary onset indicator,
panel dimensions as placeholders ([N], [C], [W], [R]), exclusion of island ADM1s,
coverage map (Figure 2).

**What's missing or underspecified**:

### 3a. Unit selection rationale
- **Key methodological decision not in paper**: The panel includes only ADM1 units
  that appear in the validated GDELT data (at least one strike over 2015–2025):
  745 ADM1 units across 136 countries, reduced to 568 after excluding isolates.
- Rationale: GDELT is media-derived. A zero in the data is ambiguous — it could
  mean no strike occurred, or a strike occurred but went unreported. Including all
  global ADM1 units as true zeros would conflate "no strike" with "no media
  coverage."
- This is consistent with prior GDELT-based subnational analyses (Müller & Rauh
  2018; Blair & Sambanis 2020) and distinct from ACLED-based studies where zeros
  are more reliably true zeros.
- Scope condition: findings generalize to regions with sufficient media presence to
  generate GDELT coverage — likely urban, economically active, or politically
  prominent subnational units.

### 3b. Onset definition
- Onset = 1 if at least one validated strike event recorded in the ADM1-week.
  Follows the epidemiological convention in the conflict literature.
- Baseline onset rate: 1.4% (0.87% in the confirmed-geocode subset).

### 3c. Full panel statistics
- Fill in: [N] ADM1 units, [C] countries, [W] weeks, [R] unit-week observations.

---

## 4. Neighbor Relationships

**What's already in the paper**: Within-country contiguity via spdep::poly2nb,
Table A1 note. Cross-border adjacency noted as exploratory extension.

**Possibly add**: Brief note on distribution of neighbor counts and how it relates
to the treatment sparsity (7.9% exposure rate).

---

## 5. Key Variables

**What's already in the paper**: Treatment variable (neighbor_strike_t1_t2, 7.9%
exposure, 3.5-fold raw association), national contagion variable (country_share,
normalized), V-Dem moderators (standardized, z-scored).

**Minor addition**: The choice to average lags t−1 and t−2 (rather than using
each separately) should be briefly justified — reduces noise, consistent with the
temporal structure of strike propagation.

---

## 6. Summary Statistics Table

**What's already in the paper**: None explicitly for this section (there is likely
a summary statistics table elsewhere or planned).

**Addition**: A summary statistics table for the analysis panel would anchor the
data section and is expected by reviewers. Could be a kable table (following the
existing pattern for avoiding double-float with etable).

---

## Gap Assessment: Does the Data Section Have Enough for 3–4 Pages?

**Yes**, comfortably, once the validation pipeline is written up properly:

| Subsection | Estimated length |
|---|---|
| GDELT source + CAMEO definitional scope | ~0.5 pp |
| False positive problem + motivation | ~0.5 pp |
| URL classifier (approach, scale, contrast w/ Hoffmann) | ~0.75 pp |
| Geocode validator (results, error types, corrections) | ~0.75 pp |
| Measurement error + attenuation argument | ~0.25 pp |
| External validation / absence of gold standard | ~0.25 pp |
| Panel construction + unit selection | ~0.5 pp |
| Neighbor relationships + variables | ~0.25 pp |
| **Total** | ~3.75 pp |

The geo-validation results alone (34.5% mismatch rate, country-level error table)
are substantive enough to deserve a paragraph with the data. These results are
currently not in the paper at all.

---

## Priority Notes to Draw From

1. `notes/gdelt-data-citations.md` — comprehensive; maps each citation to its
   role in the data section
2. `notes/geo-validation-results.md` — the validation numbers not yet in paper
3. `notes/gdelt-geolocation-reliability.md` — geolocation mechanics and bias
4. `notes/methods-notes.md` §1 — ADM1 unit selection rationale
