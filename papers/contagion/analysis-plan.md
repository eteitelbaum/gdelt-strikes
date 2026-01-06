# Analysis Plan: Spatial Diffusion of Labor Strikes

**Status**: Preregistration draft
**Last Updated**: 2026-01-05

## 1. Research Question

Do strikes in nearby subnational units increase the probability of subsequent strike onset, and is this diffusion conditioned by national political and labor institutions?

In our analysis, institutions are conceptualized as *opportunity filters* that condition whether strike activity elsewhere alters local mobilization incentives.

## 2. Theory & Hypotheses

### H1 (Demonstration effect)

Exposure to strikes in geographically proximate subnational units increases the probability of strike onset in a focal unit.

### H2 (Information & coordination)

The diffusion effect is stronger in countries with higher freedom of expression.

### H3 (Organizational opportunity)

The diffusion effect is stronger in countries with greater freedom of association.

### H4 (Repression)

The diffusion effect is weaker in countries with higher levels of state repression.

### Theoretical Grounding

This analysis builds on three literatures:

#### A. Conflict Contagion (Spatial Spillovers with Strong Identification)

- **Buhaug & Gleditsch (2008)**: Foundational work on spatial clustering of conflict and distinguishing contagion from shared risk factors
- **Braithwaite (2010)**: Demonstrates that state capacity conditions conflict contagion, establishing the "institutions as filters" framework we adapt here
- **Cederman, Gleditsch & Buhaug (2013)**: Subnational conflict diffusion with emphasis on local spillovers
- **Rüegger (2019)**: Local exposure to violence using ADM-level panels with strong fixed effects structure

#### B. Protest Diffusion (Quantitative, Weaker Identification)

- **Beissinger (2002)** *Nationalist Mobilization and the Collapse of the Soviet State*: Qualitative-quantitative hybrid establishing demonstration effects and protest diffusion across space; classic reference reviewers expect; provides theoretical backbone
- **Kern & Hainmueller (2009)** "Opium for the Masses": Shows information exposure → protest behavior using early credible causal design; useful for signaling rigor (though not about diffusion per se)
- **Barberá et al. (2015)** "The Critical Periphery in the Growth of Social Protests": Spatial diffusion of protests with event-based exposure logic; widely cited despite weak fixed effects; good for positioning relative to protest studies
- **Davenport (2007)** "State Repression and Political Order": Canonical review showing institutions shape responses to contention; repression as deterrent vs. escalation; justifies why institutions condition diffusion
- **Carey (2010)** "The Dynamic Relationship Between Protest and Repression": Subnational protest dynamics with event → response → future mobilization; clean conceptual parallel to our framework

#### C. Strike Waves and Labor Mobilization (Historical and Conceptual Foundations)

- **Shorter & Tilly (1974)** *Strikes in France, 1830–1968*: Classic work on strike waves and historical diffusion intuition; no causal design but canonical reference
- **Franzosi (1995)** *The Puzzle of Strikes*: Micro-macro strike dynamics and organizational logic; still cited in IR/labor sociology

Our approach adapts insights from conflict contagion (A) to labor mobilization, incorporating lessons from protest diffusion research (B) while grounding the analysis in the strike literature (C). We theorize that national political and labor institutions condition whether strike activity in nearby regions alters local mobilization incentives.

---

## 3. Units of Analysis

Subnational administrative unit (ADM1) × week.

---

## 4. Data Sources

* **Strike events**: GDELT (event codes corresponding to labor strikes)
* **Institutional variables**: V-Dem national-level indicators
* **Geography**: GADM ADM1 boundaries (available in `/gadm-boundaries`)

---

## 5. Outcome Variable

**Primary outcome**:

* Binary indicator of strike onset in ADM1 $i$ during week $t$

**Notes**:

* Alternative outcomes such as strike counts will be analyzed as robustness checks and are not part of the preregistered estimand

---

## 6. Treatment / Exposure Variable

We define exposure based on geographic adjacency between subnational units. Our primary analyses focus on within-country diffusion, where institutional context is held constant. We then examine cross-border adjacency as a secondary test of whether strike signals propagate across institutional boundaries. As a robustness check, we also estimate distance-weighted exposure measures that allow strike influence to decay with geographic distance.

**Primary exposure (preregistered)**:

* Binary indicator for whether at least one strike occurred in a within-country geographically adjacent ADM1 within the prior $k$ weeks

**Operationalization**:

* Proximity definition: ADM1s sharing a border within the same country
* Lag window: 1–2 weeks prior to $t$
* Neighbor restriction: Same-country neighbors only

This exposure captures potential demonstration effects from nearby strike activity while holding national institutional context constant.

**Secondary analyses (exploratory)**:

1. Cross-border adjacency: Indicator for strikes in ADM1s sharing a border across national boundaries
2. Distance-weighted exposure: Continuous measure allowing strike influence to decay with geographic distance (both within-country and potentially cross-border)

---

## 7. Empirical Specification

**Baseline model**:

$$
Y_{it} = \beta \cdot \text{NeighborStrike}_{i,t-1:t-2} + \alpha_i + \gamma_{c \times t} + \varepsilon_{it}
$$

Where:

* $\alpha_i$ = ADM1 fixed effects
* $\gamma_{c \times t}$ = country × week fixed effects
* $\varepsilon_{it}$ = error term

---

## 8. Institutional Moderation

**Primary institutional moderators** (national-level, time-varying):

1. Freedom of expression
2. Freedom of association
3. State repression

**Moderation model**:

$$
\begin{aligned}
Y_{it} = & \beta_1 \cdot \text{NeighborStrike}_{it} + \beta_2 \cdot \text{Institution}_c + \\
         & \beta_3 \cdot (\text{NeighborStrike}_{it} \times \text{Institution}_c) + \\
         & \alpha_i + \gamma_{c \times t} + \varepsilon_{it}
\end{aligned}
$$

The coefficient $\beta_3$ captures the conditioning role of institutions.

---

## 9. Estimation Strategy

* **Primary estimator**: Linear probability model
* **Standard errors**: Clustered at the ADM1 level

**Notes**:

* Nonlinear models and alternative clustering will be reported as robustness checks

---

## 10. Identification Assumptions

1. **Conditional independence**: Conditional on ADM1 fixed effects and country×week fixed effects, exposure to nearby strikes is as good as random with respect to unobserved confounders affecting strike onset

2. **Institutional exogeneity**: Institutional variables are slow-moving and not affected by short-term local strike activity

---

## 11. Exclusions & Scope Conditions

* The preregistered analysis focuses on within-country diffusion only; cross-border neighbor effects are excluded from the main specification
* The preregistered models treat all strikes equally without distinguishing between types (e.g., political vs. industrial disputes)
* Subnational institutional variation is not modeled in the preregistered specification
* Neighbor adjacency is defined topologically (shared borders) rather than by distance or k-nearest neighbors in the primary specification

---

## 12. Deviations & Exploratory Analyses

The following analyses will be conducted as exploratory extensions and clearly labeled as non-preregistered:

1. Cross-border diffusion: Models including strikes in ADM1s sharing borders across national boundaries
2. Distance-weighted exposure: Continuous measures of neighbor strike exposure allowing for distance decay
3. Strike typology: Breakdown by industrial disputes vs. political strikes (contingent on data availability)
4. Alternative lag structures: Testing different temporal windows beyond 1-2 weeks
5. Nonlinear models: Logistic regression or other non-linear specifications
6. Alternative clustering: Two-way clustering or other variance estimation approaches

Any other analyses not specified in the preregistered plan will also be clearly labeled as exploratory.

---

## 13. Timeline

The preregistration is completed prior to estimation of the main models.

---

## Implementation Notes

### Data Requirements

1. **Existing data**: `data/analysis/adm_week_full.parquet` provides ADM1-week panel structure
2. **Spatial adjacency**: GADM boundaries in `/gadm-boundaries` will be used to construct neighbor relationships based on true border adjacency
3. **V-Dem indicators**: Need to specify exact variable codes for:
   - Freedom of expression (e.g., `v2x_freexp_altinf`)
   - Freedom of association (e.g., `v2x_frassoc_thick`)
   - State repression (e.g., `v2x_clphy`)

### Existing Infrastructure (from Forecasting Models)

The project already includes spatial lag features in `notebooks/02-data-preparation/data-build.qmd`:

- `country_strikes_lag1`: Country-level strike sum at t-1
- `contig_strikes_t1`: Sum of strikes in k-nearest neighbors (k=6) at t-1
- `distw_strikes_t1`: Distance-weighted sum within 500km at t-1

However, these use k-nearest neighbors rather than true border adjacency. For the contagion analysis, we need:

- True topological adjacency (shared borders via GADM polygons)
- Binary treatment indicators (neighbor strike yes/no) rather than continuous sums
- Separate construction for within-country vs. cross-border neighbors
- Distance-weighted versions for robustness checks

### Computational Steps

#### Phase 1: GDELT→GADM Crosswalk (Spatial Join)

1. **Create GDELT→GADM mapping using coordinate-based spatial join**:
   - Load GADM ADM1 boundaries from `/gadm-boundaries/gadm_410-levels.gpkg`
   - Load GDELT strike events with coordinates (`ActionGeo_Lat`, `ActionGeo_Long`) from `data/enhanced/gdelt_strikes.parquet`
   - Convert GDELT events to spatial points using `sf::st_as_sf()`
   - Perform spatial join using `sf::st_join()` to assign each event to GADM polygon containing its coordinates
   - Create lookup table mapping GDELT `ActionGeo_ADM1Code` → GADM `GID_1` (take mode for many-to-many cases)
   - **Rationale**: All GDELT events have coordinates (download query filtered for non-null lat/lon); validation shows 93% match rate with GADM regions; coordinate-based join is more accurate than name-based matching
   - Save crosswalk as `data/crosswalks/gdelt_gadm_adm1.parquet`

2. **Update ADM1-week panel with GADM identifiers**:
   - Join crosswalk to `data/analysis/adm_week_full.parquet` to add `gid_1` field
   - Verify coverage: document proportion of GDELT events successfully mapped to GADM

#### Phase 2: Spatial Adjacency Matrix

3. **Create topological adjacency relationships**:
   - Use GADM polygons with `sf::st_touches()` or `spdep::poly2nb()` to identify true border-sharing neighbors
   - Separate adjacency into:
     - Within-country neighbors (main specification): ADM1s sharing borders within same country
     - Cross-border neighbors (exploratory): ADM1s sharing borders across national boundaries
   - Save neighbor lists as `data/spatial/gadm_adjacency_within.rds` and `data/spatial/gadm_adjacency_cross_border.rds`

4. **Compute lagged neighbor strike indicators**:
   - Binary treatment: `neighbor_strike_t1_t2` = 1 if any within-country neighbor had strikes during weeks t-1 to t-2
   - Exploratory: `cross_border_strike_t1_t2` for cross-border neighbors
   - Robustness: Distance-weighted continuous measures allowing spatial decay

#### Phase 3: V-Dem Institutional Data

5. **Download and merge V-Dem country-level indicators**:
   - Download V-Dem dataset (latest version) via `vdemdata` R package or direct download
   - Extract institutional moderators at country-year level:
     - Freedom of expression: `v2x_freexp_altinf` (or similar)
     - Freedom of association: `v2x_frassoc_thick` (or similar)
     - State repression: `v2x_clphy` (or similar)
   - **Merge strategy**:
     - Use `countrycode` package to standardize country identifiers
     - Convert GADM `GID_0` (3-letter country codes) to V-Dem country codes using `countrycode()`
     - Expand country-year V-Dem data to country-week level (repeat values within year)
     - Left join to ADM1-week panel on country code and week
   - Handle temporal matching: V-Dem is annual; assign year's value to all weeks in that year
   - **Timing**: Merge V-Dem data AFTER spatial join and adjacency computation, before regression estimation

#### Phase 4: Regression Estimation

6. **Construct outcome and treatment variables**:
   - Outcome: Binary strike onset indicator for ADM1 $i$ at week $t$
   - Main treatment: `neighbor_strike_t1_t2` (binary, within-country neighbors)
   - Moderators: V-Dem institutional variables (standardized)
   - Interactions: Treatment × Moderators

7. **Estimate baseline and moderation models**:
   - Baseline: $Y_{it} = \beta \cdot \text{NeighborStrike}_{i,t-1:t-2} + \alpha_i + \gamma_{c \times t} + \varepsilon_{it}$
   - Moderation: Add institutional moderators and interactions
   - Fixed effects: ADM1 FE ($\alpha_i$) and country×week FE ($\gamma_{c \times t}$)
   - Estimator: Linear probability model
   - Standard errors: Clustered at ADM1 level

8. **Extract and visualize results**:
   - Coefficient plots with confidence intervals
   - Marginal effects of neighbor strikes conditional on institutions
   - Robustness checks: nonlinear models, alternative clustering

9. **Exploratory analyses**:
   - Cross-border diffusion effects
   - Distance-weighted exposure measures
   - Strike typology (industrial vs. political, if feasible)
   - Alternative lag structures

---

## Questions for Resolution

- [ ] Confirm specific V-Dem variable codes for institutional moderators
- [ ] Decide on exact lag structure (1 week only, 2 weeks only, or pooled 1-2 weeks?)
- [ ] Determine sample period (all available data vs. restricted time window)
- [ ] Specify minimum ADM1-week history requirement for inclusion in analysis
- [ ] Determine how to handle island ADM1s or units with no contiguous neighbors
- [ ] Clarify approach for identifying political vs. industrial strikes (CAMEO codes, actor types, or manual coding)
