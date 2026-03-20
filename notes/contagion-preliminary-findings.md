# Contagion Analysis: Preliminary Findings

**Date**: 2026-03-19
**Notebook**: `notebooks/03-modeling/explanatory/contagion-models.qmd`
**Data**: `data/analysis/contagion_panel.parquet`
**Sample**: 745 ADM1 units × 557 weeks = 414,965 rows; 1.4% strike onset rate; 136 countries; 2015–2025

---

## Setup

Panel constructed from 11,503 validated GDELT strike events (2015–2025),
aggregated to ADM1×week. Treatment variable (`neighbor_strike_within_t1_t2`) is
a binary indicator for whether any within-country geographic neighbor had a
strike onset in weeks t-1 or t-2. Adjacency computed from GADM polygons using
`poly2nb()`. V-Dem institutional moderators merged at country-year level and
z-scored.

---

## Fixed effects specification: a central tension

All models use LPM estimated via OLS (`feols`, fixest) with SEs clustered at
ADM1. The choice of fixed effects structure is consequential and drives most of
the key results:

**`ADM1 + country×week` FEs (preregistered, strict identification)**
- ADM1 FEs absorb all time-invariant regional characteristics
- Country×week FEs absorb every common shock within a country in a given week —
  national strike waves, political events, economic shocks
- Treatment is identified from within-country-week variation: does the specific
  region with a striking geographic neighbor (while others don't) have elevated
  onset?
- *Problem*: V-Dem moderators are annual and country-level, so they are perfectly
  collinear with country×week FEs. Moderator main effects are unidentifiable;
  only interactions survive (identified from treatment variation scaled by
  between-country-week moderator variation)
- *Problem*: country×week FEs may absorb the very signal of interest if
  contagion operates at the national wave level rather than neighborhood level

**`ADM1 + week` FEs (alternative, used for moderation models)**
- ADM1 FEs absorb time-invariant regional characteristics (which subsumes
  country-level baseline rates, since ADM1 is nested within country)
- Week FEs absorb global time trends
- V-Dem moderators are identified (they vary within country across years, not
  absorbed by ADM1 or week FEs)
- *Problem*: does not control for country-specific weekly shocks — a national
  election or economic crisis affecting all regions simultaneously is not
  conditioned out, opening a confounding pathway

The two specs bracket the truth: country×week is likely over-controlling
(absorbing national-wave contagion along with confounders); ADM1+week is likely
under-controlling (conflating contagion with country-level common shocks). The
decomposition analysis below was designed to make this tension explicit.

---

## H1: Demonstration effect (spatial contagion)

**Preregistered spec** — LPM with ADM1 + country×week FEs, SEs clustered at ADM1:

$$Y_{it} = \beta \cdot \text{NeighborStrike}_{i,t-1:t-2} + \alpha_i + \gamma_{c \times t} + \varepsilon_{it}$$

**Result**: β = −0.003 (SE = 0.002, p = 0.133) — **null**.

The raw association is striking: regions with a neighbor that struck have a 4.9%
onset rate vs. 1.4% without (3.5× difference). But this entirely disappears once
country×week FEs are included. The FEs absorb common within-country-week shocks,
and once conditioned on, geographic neighbor exposure adds nothing.

The t-1 lag separately is negative and marginally significant (β = −0.006,
p = 0.036), suggesting a possible displacement effect — once a neighbor strikes,
focal regions may be *less* likely to follow immediately (employers settle
preemptively, or workers wait for outcomes). The t-2 lag is null.

---

## National vs. neighborhood decomposition

To understand why H1 fails, we decompose the apparent neighborhood effect by
including an explicit country-level strike indicator alongside the geographic
neighbor variable (ADM1 + week FEs):

$$Y_{it} = \beta_1 \cdot \text{NeighborStrike}_{i,t-1:t-2} + \beta_2 \cdot \text{CountryStrike}_{i,t-1:t-2} + \alpha_i + \gamma_t + \varepsilon_{it}$$

where `CountryStrike` = binary, did any other region in the same country strike
in t-1 or t-2.

| Model | Neighbor strike | Country strike | frassoc interaction | Within R² |
|---|---|---|---|---|
| M1: Country only | — | +0.079*** | — | 0.041 |
| M2: Neighbor only | +0.015*** | — | — | 0.001 |
| M3: Both together | +0.002 (null) | +0.078*** | — | 0.041 |
| M4: Both + frassoc | +0.001 (null) | +0.079*** | +0.003 (null) | 0.042 |

*All models: ADM1 + week FEs, SEs clustered at ADM1.*

**Key results**:

- Country-level contagion is large (7.9pp, ~5× baseline rate) and explains ~4%
  of within-unit variance.
- Geographic neighbor exposure explains 47× less variance (within R² = 0.001)
  and drops entirely to null once country-level is controlled (M3: β = +0.002,
  p = 0.21).
- The frassoc moderation of the neighborhood effect (marginal in the joint
  moderation model) also disappears in M4 once country-level contagion is
  controlled (β = +0.003, p = 0.12). This suggests the frassoc interaction was
  capturing variation in the *structure of national waves* rather than true
  neighborhood diffusion.
- The 1.5pp neighborhood effect seen in M2 is entirely attributable to
  country-level waves: when one region strikes, others in the same country tend
  to strike in the same week not because of geographic proximity, but because
  they share a common national shock.

**Conclusion**: Strike contagion in these data operates at the national level,
not through neighborhood-to-neighborhood geographic diffusion. The country-level
wave effect is robust, large, and not explained by geographic neighbor proximity.

---

## H2–H4: Institutional moderation

### Identification problem with preregistered spec

The preregistered moderation spec (`country×week` FEs + interaction) cannot
identify moderator main effects: V-Dem is annual and country-level, so `freexp_z`,
`frassoc_z`, and `repression_z` are perfectly collinear with `country×week` FEs.
`fixest` drops the main effects but retains the interactions (identified from
within-country-week variation in treatment scaled by between-country-week
variation in moderator). All three interactions are null under this spec.

### Joint moderation model (ADM1 + week FEs)

To recover moderator estimates, we switch to ADM1 + week FEs and include all
three moderators simultaneously:

$$Y_{it} = \beta_1 \cdot \text{NS} + \beta_2 \cdot \text{NS} \times \text{freexp}_z + \beta_3 \cdot \text{NS} \times \text{frassoc}_z + \beta_4 \cdot \text{NS} \times \text{repression}_z + \alpha_i + \gamma_t + \varepsilon_{it}$$

| Term | Full sample | Validated only |
|---|---|---|
| Neighbor strike | +0.014*** | +0.006*** |
| Neighbor × freexp | −0.009 (p = 0.073) | −0.007 (p = 0.068) |
| **Neighbor × frassoc** | **+0.010 (p = 0.062)** | **+0.009 (p = 0.035*)** |
| Neighbor × repression | +0.003 (p = 0.163) | +0.002 (p = 0.238) |

*NS = neighbor_strike_within_t1_t2. ADM1 + week FEs, SEs clustered at ADM1.*

**freexp and frassoc pull in opposite directions** when included jointly (they
partially cancelled when modeled separately). Key findings:

- **Freedom of association amplifies contagion** (H3 supported, marginal): union
  networks and civil society infrastructure create locally-embedded organizing
  capacity that facilitates diffusion between adjacent regions. The frassoc result
  crosses p < 0.05 in the validated-only sample.

- **Freedom of expression attenuates contagion** (opposite of H2): where
  information flows freely via media, workers can coordinate nationally rather
  than through geographic proximity. High-freexp environments produce nationally
  homogeneous strike waves rather than geographically structured diffusion.

- **Repression**: null throughout (H4 not supported).

### Interpretation

Given that the decomposition shows neighborhood effects go to zero after
controlling for country-level contagion, the moderation results likely reflect
the *structure* of national waves rather than pure geographic diffusion:

- **High freexp** → rapid national information spread → uniform national waves
  with no geographic gradient
- **High frassoc** → locally-embedded organizing → geographic clustering within
  national waves, producing apparent neighborhood diffusion patterns

A sharper framing: **freexp produces nationally homogeneous strike waves; frassoc
produces geographically structured ones.**

---

## Robustness

- **Validated-only sample** (geo_quality == "validated", ~0.87% onset rate):
  all results qualitatively identical; frassoc interaction strengthens to p = 0.035.
- **Separate lags**: t-1 negative and significant (−0.006, p = 0.036); t-2 null.
- **Logit**: baseline null result holds.
- **Two-way clustering** (ADM1 + country-week): baseline null result holds.
- **Cross-border diffusion**: null under both country×week and ADM1+week FEs.

---

## Open questions / next steps

1. **Reframe paper**: pivot from "spatial contagion" to "national strike waves
   and their institutional correlates." The interesting question becomes: what
   predicts which countries develop national strike waves?
2. **Country-level analysis**: model `country_strike_t1_t2` as outcome to
   understand drivers of national coordination.
3. **frassoc moderation**: worth following up — is this effect driven by specific
   countries or regions? Conditional effects plot across frassoc distribution.
4. **ISO 3166-2 ↔ HASC_1 name matching** (deferred from crosswalk step): would
   recover ~25% of corrected events currently missing GID_1, potentially
   increasing validated sample.
5. **Temporal granularity**: week may be too coarse for neighborhood diffusion
   (which could operate over days). Daily analysis if data permit.
