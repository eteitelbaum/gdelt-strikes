# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a research project analyzing global labor strikes using GDELT (Global Database of Events, Language and Tone) event data. The project has two active papers:

**Paper 1 — Predictive Forecasting** (`papers/nyu-sds-conf/`): Machine learning pipeline forecasting strike occurrence and intensity at ADM1-week resolution. Presented at the NYU Data Science Frontiers Workshop.

**Paper 2 — Contagion Analysis** (`papers/contagion/`): Two-way fixed effects panel study of geographic vs. national diffusion of strike activity. Tests whether strikes spread across ADM1 borders (geographic contagion) or propagate through national-level common shocks. The main active paper.

**Tech Stack**: R + Quarto + fixest + tidymodels + Apache Arrow (R); Python + OpenAI API (validation tools)

---

## Paper 2: Contagion Analysis (Main Active Paper)

### The Research Question

Do strikes spread geographically to neighboring ADM1 regions, or does the apparent clustering of strikes reflect national common shocks (e.g., general strikes, austerity policies, national labor law changes)?

### The Empirical Specification

Two-way fixed effects linear probability model estimated with `feols` from the `fixest` package:

```
Y_{it} = β · NeighborStrike_{i,t-1:t-2} + α_i + γ_{c×t} + ε_{it}
```

- `Y_{it}`: strike onset indicator for ADM1 region i in week t
- `NeighborStrike_{i,t-1:t-2}`: any ADM1 neighbor had a strike onset in t-1 or t-2
- `α_i`: ADM1 fixed effects (time-invariant unit heterogeneity)
- `γ_{c×t}`: country-by-week fixed effects (absorbs all national common shocks)
- Standard errors clustered at ADM1 level
- Estimated as LPM via OLS

### Contagion Paper Pipeline

```bash
# 1. Build adjacency matrix (shared-border ADM1 pairs)
Rscript tools/contagion/build_adjacency.R

# 2. Build the ADM1-week analysis panel
Rscript tools/contagion/build_panel.R

# 3. Merge V-Dem covariates
Rscript tools/contagion/merge_vdem.R

# Or run all steps in sequence:
Rscript tools/contagion/run_all.R

# 4. Run diagnostics notebook
quarto render notebooks/02-data-preparation/explanatory/contagion-diagnostics.qmd

# 5. Run models notebook
quarto render notebooks/03-modeling/explanatory/contagion-models.qmd

# 6. Render the paper
quarto render papers/contagion/contagion-paper.qmd
```

### Contagion Data Files (`data/contagion/` — git-ignored)

- `analysis_panel.parquet`: Main ADM1-week panel with neighbor exposure variables
- `adjacency_matrix.parquet`: ADM1 shared-border pairs
- Saved model objects: `outputs/contagion/` (rds files for each model specification)

### Contagion Paper Files (`papers/contagion/`)

- `contagion-paper.qmd`: Main paper (Quarto, renders to PDF via working-paper extension)
- `tables.R`: Generates all regression tables using `etable()` from fixest
- `figures.R`: Generates all figures
- `presentation.qmd`: Slide deck version
- `analysis-plan.md`: Pre-analysis plan
- `clpw-abstract.md`: Abstract for CLPW conference submission
- `_extensions/eteitelbaum/working-paper/`: Custom Quarto extension for PDF formatting

### Table Rendering Notes (important)

The paper uses `etable()` from fixest with `style.tex(main="base")` and `tex=TRUE`, which outputs raw LaTeX tabular content only (no `\begin{table}` wrapper). Key patterns:

```r
#| tbl-cap: "Caption text"
#| echo: false
#| output: asis
etable(model_object, dict=coef_dict, signif.code=c(...),
       fitstat=~n+r2, style.tex=etable_style, tex=TRUE)
```

- Do NOT add `#| label: tbl-*` to etable chunks — causes double-float rendering
- `\floatplacement{table}{H}` is set globally in `_extensions/.../header.tex`
- Summary statistics table uses `datasummary(output="data.frame")` + `kable()` to avoid double-float

---

## Paper 1: Predictive Forecasting

### Pipeline (Sequential Order)

```bash
# 1. Download raw data from BigQuery
quarto render notebooks/01-data-acquisition/gdelt-download-filter.qmd

# 2. Build analysis datasets
quarto render notebooks/02-data-preparation/predictive/data-build.qmd

# 3. Single-stage models
quarto render notebooks/03-modeling/predictive/single-stage-models.qmd

# 4. Two-stage models (PREFERRED)
quarto render notebooks/03-modeling/predictive/two-stage-models.qmd

# 5. Analysis and visualizations
quarto render notebooks/04-analysis/predictive/modeling-analysis.qmd
quarto render notebooks/04-analysis/predictive/visualizations.qmd

# Render conference paper
quarto render papers/nyu-sds-conf/nyu-abstract.qmd
```

### Two-Stage Architecture (Preferred for Paper 1)

**Stage 1 — Occurrence** (Binary Classification): Logistic regression, random forest, LightGBM, XGBoost. Metrics: ROC-AUC, PR-AUC, Brier score.

**Stage 2 — Severity** (Count Regression on positive-only data): Gamma GLM, log-linear with Duan's smearing, gradient boosting with gamma objective. Metrics: MAE, RMSE, R².

---

## Project Structure

```
gdelt-strikes/
├── notebooks/
│   ├── 01-data-acquisition/
│   │   └── gdelt-download-filter.qmd       # BigQuery data download
│   ├── 02-data-preparation/
│   │   ├── explanatory/
│   │   │   └── contagion-diagnostics.qmd   # Contagion panel diagnostics
│   │   └── predictive/
│   │       └── data-build.qmd              # Feature engineering (Paper 1)
│   ├── 03-modeling/
│   │   ├── explanatory/
│   │   │   └── contagion-models.qmd        # TWFE contagion models
│   │   └── predictive/
│   │       ├── single-stage-models.qmd
│   │       └── two-stage-models.qmd        # PREFERRED for Paper 1
│   ├── 04-analysis/
│   │   └── predictive/
│   │       ├── modeling-analysis.qmd
│   │       └── visualizations.qmd
│   └── exploratory/                        # Data quality, ADM1 diagnostics
│       ├── adm1-diagnostic.R
│       ├── adm1-validation-sample.py
│       ├── gdelt-data-exploration.qmd
│       └── filter-themes-urls.qmd
├── papers/
│   ├── contagion/                          # Paper 2 (main active paper)
│   │   ├── contagion-paper.qmd
│   │   ├── tables.R
│   │   ├── figures.R
│   │   └── _extensions/eteitelbaum/working-paper/
│   └── nyu-sds-conf/                       # Paper 1 (conference)
│       ├── nyu-abstract.qmd
│       └── nyu-presi.qmd
├── tools/
│   ├── contagion/                          # Contagion panel build pipeline
│   │   ├── build_adjacency.R
│   │   ├── build_panel.R
│   │   ├── merge_vdem.R
│   │   └── run_all.R
│   ├── url_classifier/                     # Python: LLM-based URL validation
│   │   ├── classify.py
│   │   ├── batch.py
│   │   ├── prompts.py
│   │   └── README.md
│   ├── geo_validator/                      # Python: LLM-based geo validation
│   │   ├── classify.py
│   │   └── batch.py
│   └── adm1_crosswalk/
│       └── build_gadm_crosswalk.R          # GADM-to-GDELT ADM1 name matching
├── helpers/
│   ├── helpers.R                           # Model evaluation utilities (Paper 1)
│   └── spatial_helpers.R
├── notes/                                  # Literature review and methods notes
│   ├── theory-contagion.md                 # Strike contagion literature (6 strands)
│   ├── methods-fe-identification.md        # Citations for TWFE, LPM, clustering
│   ├── gdelt-data-citations.md             # GDELT validation literature
│   ├── gdelt-geolocation-reliability.md    # Geolocation reliability discussion
│   ├── contagion-preliminary-findings.md   # Early results summary
│   ├── identification-strategy.md          # Identification narrative
│   ├── results-presentation.md             # Results write-up notes
│   ├── covid-strike-drop.md                # COVID-era drop analysis plan
│   ├── hibbs-revisited.md                  # Future paper: Hibbs redux
│   ├── covariate-datasets.md               # External covariate sources
│   └── bayes-notes.md                      # Why Bayesian models were abandoned
├── data/                                   # Data files (NOT in git)
├── archive/                                # Deprecated notebooks
└── CLAUDE.md                               # This file
```

---

## Data Locations

### Raw Data (`data/raw/`)
- `gdelt_strikes.parquet`: Raw BigQuery output (CAMEO EventCode 143)
- `gdelt_strikes_filtered.parquet`: ADM1-filtered with valid geographic regions

### Analysis Data (`data/analysis/`)
- `adm_week_full.parquet`: Complete ADM1-week panel (Paper 1)
- `adm_week_positive.parquet`: Strike-weeks only (Paper 1, Stage 2 models)

### Contagion Data (`data/contagion/`)
- `analysis_panel.parquet`: ADM1-week panel with neighbor exposure, country×week FEs
- `adjacency_matrix.parquet`: Shared-border ADM1 pairs

### Model Outputs (`outputs/` — git-ignored)
- `outputs/models/`: Paper 1 model objects, metrics, predictions
- `outputs/contagion/`: Paper 2 model rds files (m_base_cw, m_base_aw, m_cross_cw, etc.)
- `outputs/plots/`: Generated figures

---

## Tools

### `tools/url_classifier/` (Python)
LLM-based classifier that validates whether GDELT URLs correspond to actual strike events. Uses OpenAI batch API with few-shot prompting. Runs in two passes (main + uncertain cases). Required for GDELT data quality — raw GDELT has high false positive rates (Wang et al. 2016 found ~21% of raw protest URLs cover actual events).

```bash
cd tools/url_classifier
python -m url_classifier  # runs classification pipeline
```

### `tools/geo_validator/` (Python)
LLM-based validator that checks whether GDELT's ADM1 geolocation is correct for a sample of events. Same batch API architecture as url_classifier.

### `tools/contagion/` (R)
Builds the contagion analysis panel from scratch:
- `build_adjacency.R`: Constructs shared-border ADM1 pairs from GADM shapefiles
- `build_panel.R`: Aggregates validated GDELT strikes to ADM1-week, constructs neighbor exposure variables
- `merge_vdem.R`: Merges V-Dem country-year covariates
- `run_all.R`: Runs the full pipeline in sequence

### `tools/adm1_crosswalk/` (R)
Matches GDELT's ADM1 name strings to GADM administrative unit codes using GeoNames API.

---

## Key Design Decisions

### Why LPM (not logit) for the contagion model?
The incidental parameters problem makes logit with many fixed effects inconsistent. LPM estimates the average partial effect directly. A bias-corrected logit robustness check using `alpaca` package is planned. See `notes/methods-fe-identification.md`.

### Why country×week FEs (not parametric controls)?
Country×week FEs absorb all national common shocks without requiring correct specification of which controls matter. The conflict contagion literature (Buhaug & Gleditsch 2008; Gleditsch & Rivera 2017) uses logit with parametric controls — our approach is more demanding and assumption-free.

### Why gradient boosting (not Bayesian) for Paper 1?
`brms` with zero-truncated distributions was attempted but abandoned: 17k+ observations × 200+ features caused convergence failures (R-hat = 3.66) and 2-3 hour runtimes per fold. See `notes/bayes-notes.md`.

### GDELT data quality
Raw GDELT strike events (CAMEO code 143) have high false positive rates. The `url_classifier` tool filters events using LLM few-shot classification on URL and headline text, following the validation approach recommended by Hoffmann et al. (2022). See `notes/gdelt-data-citations.md`.

---

## Service Account Configuration

**File**: `service-account.json` (git-ignored)

Google Cloud credentials for BigQuery access to GDELT. Required for `notebooks/01-data-acquisition/gdelt-download-filter.qmd`.

```r
library(bigrquery)
bq_auth()  # OAuth fallback if service account missing
```
