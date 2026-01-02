# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a research project for forecasting labor strikes using GDELT (Global Database of Events, Language and Tone) event data. The project implements a machine learning pipeline that:

1. Mines geopolitical event data from Google's GDELT database via BigQuery
2. Engineers temporal and spatial features at the administrative region-week level
3. Builds two-stage predictive models to forecast strike occurrence and intensity

**Tech Stack**: R + Quarto + tidymodels ecosystem + Apache Arrow

## Common Commands

### Rendering Quarto Notebooks

```bash
# Render a specific analysis notebook
quarto render notebooks/01-data-acquisition/gdelt-download-filter.qmd
quarto render notebooks/02-data-preparation/data-build.qmd
quarto render notebooks/03-modeling/two-stage-models.qmd

# Render the conference presentation
quarto render papers/nyu-sds-conf/nyu-presi.qmd
```

### Running the Data Pipeline (Sequential Order)

Execute notebooks in this order to rebuild the full pipeline:

```bash
# 1. Download raw data from BigQuery
quarto render notebooks/01-data-acquisition/gdelt-download-filter.qmd

# 2. Explore and validate data quality (if needed)
quarto render notebooks/exploratory/gdelt-data-exploration.qmd

# 3. Build analysis datasets (ADM1-week aggregation + feature engineering)
quarto render notebooks/02-data-preparation/data-build.qmd

# 4. Single-stage models (direct count prediction)
quarto render notebooks/03-modeling/single-stage-models.qmd

# 5. Two-stage models (occurrence + severity - PREFERRED APPROACH)
quarto render notebooks/03-modeling/two-stage-models.qmd

# 6. Generate visualizations and analysis
quarto render notebooks/04-analysis/visualizations.qmd
quarto render notebooks/04-analysis/modeling-analysis.qmd
```

### R Interactive Development

```r
# Load utility functions
source("helpers/helpers.R")

# Load data
library(arrow)
data <- read_parquet("data/analysis/adm_week_positive.parquet")
```

## Code Architecture

### Data Pipeline (Sequential Processing)

```
BigQuery GDELT
    ↓
[notebooks/01-data-acquisition/gdelt-download-filter.qmd]
    ↓
data/raw/gdelt_strikes.parquet
    ↓
[notebooks/exploratory/gdelt-data-exploration.qmd] - Validation & filtering
    ↓
[notebooks/02-data-preparation/data-build.qmd] - ADM1-week aggregation + feature engineering
    ↓
data/analysis/adm_week_full.parquet (all weeks)
data/analysis/adm_week_positive.parquet (strike weeks only)
    ↓
[notebooks/03-modeling/single-stage-models.qmd] - Direct prediction
[notebooks/03-modeling/two-stage-models.qmd] - Occurrence + severity (PREFERRED)
    ↓
outputs/models/ - Saved models, metrics, predictions
outputs/plots/ - Generated visualizations
```

### Two-Stage Modeling Architecture (Preferred Approach)

The project uses a two-stage forecasting pipeline for handling sparse strike data:

**Stage 1 - Occurrence Model** (Binary Classification):
- Predicts whether strikes occur in a given ADM1-week
- Models: Logistic regression, decision trees, random forests, gradient boosting
- Metrics: ROC-AUC, PR-AUC, Brier score
- Engine: tidymodels + bonsai (LightGBM/XGBoost)

**Stage 2 - Severity Model** (Count Regression on Positive Data):
- Predicts strike count given that strikes occur
- Trained on filtered positive-only data (`adm_week_positive.parquet`)
- Models:
  - Gamma GLM (tidymodels)
  - Log-transformed linear models with Duan's smearing correction
  - Gradient boosting with gamma objective (LightGBM, XGBoost)
- Metrics: MAE, RMSE, R², pseudo-R² (for GLMs)

**Why Two-Stage?**
- Handles sparse outcomes (many weeks with zero strikes)
- More refined than single-stage approaches
- Better calibration and threshold optimization

### Feature Engineering

Features are created in `notebooks/02-data-preparation/data-build.qmd` and include:

- **Temporal**: Lagged strike counts (t-1, t-2, ...), rolling averages, trends
- **Spatial**: Geographic proximity to previous events, ADM1 baseline rates
- **Event characteristics**: Actor diversity, media mentions, tone, article counts
- **Interaction terms**: Region × time interactions

### Helper Functions (`helpers/helpers.R`)

Critical utility functions for model evaluation:

- `collect_fold_metrics()`: Extract out-of-fold predictions with optional smearing correction
- `collect_occurrence_fold_metrics()`: Binary classifier evaluation
- `compute_pseudo_r2()`: Deviance-based pseudo-R² for Poisson/Tweedie/Gamma GLMs
- `compute_smearing_factor()`: Duan's smearing estimate for log-scale back-transformation
- `compute_and_save_importance()`: Permutation feature importance across CV folds

## Project Structure

```
gdelt-strikes/
├── notebooks/
│   ├── 01-data-acquisition/
│   │   └── gdelt-download-filter.qmd          # BigQuery data download
│   ├── 02-data-preparation/
│   │   └── data-build.qmd                     # Feature engineering core
│   ├── 03-modeling/
│   │   ├── single-stage-models.qmd            # Direct count prediction
│   │   └── two-stage-models.qmd               # Two-stage pipeline (PREFERRED)
│   ├── 04-analysis/
│   │   ├── modeling-analysis.qmd              # Results analysis
│   │   └── visualizations.qmd                 # Visualization generation
│   └── exploratory/
│       ├── gdelt-data-exploration.qmd         # Data exploration
│       ├── data-quality-exploration.qmd       # Quality checks
│       ├── country-filter-exploration.qmd     # Country filtering
│       └── filter-themes-urls.qmd             # Theme filtering
├── archive/
│   └── notebooks/                             # Deprecated analysis notebooks
├── outputs/
│   ├── models/                                # Model outputs (NOT in git)
│   └── plots/                                 # Generated visualizations (NOT in git)
├── data/                                      # Data files (NOT in git)
├── helpers/
│   └── helpers.R                              # Model evaluation utilities
├── papers/
│   └── nyu-sds-conf/                         # Conference presentation
├── notes/
│   └── bayes-notes.md                         # Technical exploration notes
└── CLAUDE.md                                  # This file
```

## Data Locations

### Raw Data (`data/raw/`)
- `gdelt_strikes.parquet`: Raw BigQuery output (EventCode starting with '143')
- `gdelt_strikes_filtered.parquet`: ADM1-filtered with valid geographic regions

### Analysis Data (`data/analysis/`)
- `adm_week_full.parquet`: Complete ADM1-week dataset (includes zero-strike weeks)
- `adm_week_positive.parquet`: Positive-only (strike weeks only) - **used for Stage 2 models**

### Model Outputs (`outputs/models/` - git-ignored)

**Single-Stage Models** (`sst_*`):
- Fitted models (.rds)
- Metrics (CSV)
- Predictions (Parquet)
- Feature importance (Parquet)

**Two-Stage Models** (`tsr_*`):
- Pipeline selections (.rds)
- Calibration curves (CSV)
- Optimization results (CSV)
- Naive baselines (CSV)

### Plot Outputs (`outputs/plots/` - git-ignored)
- Publication-ready figures (PDF and PNG formats)
- Diagnostic plots from model analysis
- Time series visualizations

## Key Design Decisions

### Why Gradient Boosting Over Bayesian Models?

The project initially explored Bayesian approaches (`brms` with zero-truncated distributions) but abandoned them due to:

- **Computational infeasibility**: 17k+ observations × 200+ features exceeds brms capacity
- **Convergence failures**: R-hat = 3.66 (should be < 1.01)
- **Namespace conflicts**: 14+ package conflicts when mixing tidymodels + brms + arrow
- **Runtime**: 2-3 hours per fold with non-convergent results

**Solution**: Gradient boosting on filtered positive-only data achieves the same modeling goal with better performance and faster runtime.

See `notes/bayes-notes.md` for detailed exploration and lessons learned.

## Service Account Configuration

**File**: `service-account.json` (git-ignored)

Google Cloud service account credentials for BigQuery access to GDELT data. Required for `notebooks/01-data-acquisition/gdelt-download-filter.qmd`.

If missing, authenticate via:
```r
library(bigrquery)
bq_auth()  # Opens browser for OAuth
```
