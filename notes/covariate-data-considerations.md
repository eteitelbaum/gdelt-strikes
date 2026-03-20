# Covariate Data: What to Merge and When

This note records the strategic reasoning about which covariate datasets to
incorporate into each paper, and what the right approach is for different
journal targets.

---

## The Core Tension

The paper roadmap offers two possible strategies:

1. **Lean identification**: clean design + fixed effects absorb confounders;
   minimal controls; emphasis on robustness checks. Favored by the
   credibility-revolution literature in economics and increasingly in top
   political science journals.

2. **Full battery of controls**: comprehensive theoretical framing with
   competing explanations controlled for; development indicators, conflict
   data, labor market covariates. Traditional comparative politics and
   sociology approach.

The answer depends on which paper and which journal.

---

## Paper 4 (Diffusion/Contagion) — the Flagship

### Design
Neighbor-strike exposure → strike onset; ADM1 FE + country×week FE.

### Why the lean strategy is stronger here

The two sets of fixed effects do most of the work:
- **ADM1 FE**: absorbs all time-invariant regional characteristics — income
  levels, urbanization, industry mix, union density, geography
- **Country×week FE**: absorbs all national-level time-varying confounders —
  macro shocks, political crises, national policies, global trends

What remains after both is: "conditional on everything stable about your
region and everything happening nationally that week, does a neighboring
region having a strike increase your probability of striking?" That is a
clean identification strategy. Adding SHDI or development controls largely
re-controls for things the FEs already handle and risks introducing bad
controls.

**Nighttime lights** should not be added as a control here — it is the
outcome variable in Paper 6. Adding it as a control in Paper 4 would
introduce post-treatment bias.

### The one covariate to add: UCDP conflict

Add lagged ADM1-level conflict (from UCDP GED) as a control. This addresses
the main identification objection: that what looks like strike diffusion is
actually correlated repression or conflict spreading across a region. It is
theoretically motivated, not defensive kitchen-sinking.

### Core data for Paper 4
- GDELT strikes (ADM1-week) — outcome and treatment
- V-Dem national indices — institutional moderators (main theoretical payload)
- UCDP conflict (ADM1-year, aggregated from GED) — control for conflict confound

**Do not add**: SHDI, nighttime lights, OECD/Eurostat labor covariates.
These are not needed for identification and introduce complexity without
improving the design.

---

## Journal-Specific Strategy

### APSR / AJPS (top general political science) — primary target for Paper 4

This design is well-matched. These audiences have absorbed the credibility
revolution. Priorities:
- Emphasize clean within-country identification
- Rigorous robustness checks: alternative spatial exposure measures,
  different FE structures, falsification/placebo tests, GDELT measurement
  quality checks
- V-Dem interaction framed as the theoretical contribution (institutions
  as filters on diffusion, not just as controls)
- GDELT measurement quality will be a bigger reviewer concern than omitted
  variables — the geo-validation pipeline and `geo_quality` flag address this

### Top economics (JPE, QJE, AER)

Same lean logic, even more strictly applied. Additional requirements:
- Cleaner exclusion restriction story for why neighbor exposure is exogenous
- The V-Dem interaction needs careful framing to avoid a "moderated IV"
  critique
- Higher bar but higher payoff; consider after an APSR/AJPS submission

### CPS / World Politics / BJPS (comparative politics)

These journals are increasingly credibility-influenced but genre-expect more
engagement with comparative institutions literature. Adjustments:
- Add SHDI as a single summary development control to speak to the
  structural/power-resources tradition
- Engage more directly with the corporatism and industrial relations
  systems literature
- Design stays the same; one robustness column with development controls

### AJS / ASR (sociology)

More tradition of comprehensive controls; expects engagement with the labor
sociology literature (strike waves, Shorter & Tilly, power resources).
A fuller covariate battery makes genre sense here. However, the paper
probably contributes more to political science than sociology, and the
strike-waves literature in sociology is less active. Lower priority target.

---

## Which Papers Need Subnational Covariates

The ADM1 crosswalk and subnational data pipeline being built now is primarily
infrastructure for other papers in the roadmap — not Paper 4.

| Paper | Key data needed | Subnational covariates? |
|---|---|---|
| Paper 1 (local economic triggers) | Weather, price shocks, nighttime lights | Yes — NTL is the treatment |
| Paper 2 (institutions as filters) | V-Dem × shock interactions | No |
| Paper 3 (geography of origins) | Spatial features, urbanization, capital regions | Yes — spatial features |
| **Paper 4 (diffusion)** | **GDELT + V-Dem + UCDP** | **No (UCDP only)** |
| Paper 5 (repression) | ACLED/UCDP event data | Yes — conflict at ADM1 |
| Paper 6 (economic effects) | Nighttime lights (ADM1-week) | Yes — NTL is the outcome |

### Implication

Paper 4 can be submitted before the full crosswalk and covariate pipeline is
complete. The subnational data work is not on the critical path for the
flagship paper. Write Paper 4 now in parallel with the pipeline work.

---

## Country-Level Covariates (All Papers)

For national-level covariates, no pipeline work is needed. The R
`countrycode` package handles FIPS → ISO2/ISO3/COW at analysis time.
Key national datasets (V-Dem, WDI, UCDP/PRIO armed conflict) merge on
country-year without any crosswalk beyond what `countrycode` provides.
