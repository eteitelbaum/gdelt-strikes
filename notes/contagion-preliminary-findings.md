# Contagion Analysis: Preliminary Findings

**Date**: 2026-03-19
**Notebook**: `notebooks/03-modeling/explanatory/contagion-models.qmd`
**Data**: `data/analysis/contagion_panel.parquet`
**Sample**: 745 ADM1 units × 557 weeks = 414,965 rows; 1.4% strike onset rate; 136 countries

---

## Setup

Panel constructed from 11,503 validated GDELT strike events (2017–2022),
aggregated to ADM1×week. Treatment variable (`neighbor_strike_within_t1_t2`) is
a binary indicator for whether any within-country geographic neighbor had a
strike onset in weeks t-1 or t-2. Adjacency computed from GADM polygons using
`poly2nb()`. V-Dem institutional moderators merged at country-year level and
z-scored.

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

| Model | Neighbor strike | Country strike | Within R² |
|---|---|---|---|
| Country only | — | +0.079*** | 0.041 |
| Neighbor only | +0.015*** | — | 0.001 |
| Both together | +0.002 (null) | +0.078*** | 0.041 |

**Interpretation**: Country-level contagion is large (7.9pp, ~5× baseline rate)
and explains ~4% of within-unit variance. Geographic neighbor exposure explains
47× less variance and drops to null once country-level is controlled. The 1.5pp
neighborhood effect seen without country control is entirely attributable to
country-level waves — when one region strikes, other regions in the same country
tend to strike in the same week not because of geographic proximity but because
something drives all of them simultaneously.

**Conclusion**: Strike contagion in these data operates at the national level,
not through neighborhood-to-neighborhood geographic diffusion.

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
