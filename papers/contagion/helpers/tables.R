## tables.R
## Regression table objects for contagion-paper.qmd
## Sourced from the paper's setup chunk; creates tbl_* objects in the environment.

library(fixest)
library(modelsummary)
library(knitr)
library(arrow)
library(tidyverse)
library(here)

# ── Load model objects ────────────────────────────────────────────────────────

out_dir <- here("outputs/models/contagion")

m_baseline    <- readRDS(file.path(out_dir, "m_baseline.rds"))
m_country     <- readRDS(file.path(out_dir, "m_country.rds"))
m_neighbor_aw <- readRDS(file.path(out_dir, "m_neighbor_aw.rds"))
m_decomp      <- readRDS(file.path(out_dir, "m_decomp.rds"))
m_freexp      <- readRDS(file.path(out_dir, "m_freexp.rds"))
m_frassoc     <- readRDS(file.path(out_dir, "m_frassoc.rds"))
m_repression  <- readRDS(file.path(out_dir, "m_repression.rds"))
m_joint_mod      <- readRDS(file.path(out_dir, "m_joint_mod.rds"))
m_freexp_ext     <- readRDS(file.path(out_dir, "m_freexp_ext.rds"))
m_frassoc_ext    <- readRDS(file.path(out_dir, "m_frassoc_ext.rds"))
m_repression_ext <- readRDS(file.path(out_dir, "m_repression_ext.rds"))
m_joint_mod_ext  <- readRDS(file.path(out_dir, "m_joint_mod_ext.rds"))
m_lag1        <- readRDS(file.path(out_dir, "m_lag1.rds"))
m_lag2        <- readRDS(file.path(out_dir, "m_lag2.rds"))
m_logit       <- readRDS(file.path(out_dir, "m_logit.rds"))
m_twoway      <- readRDS(file.path(out_dir, "m_twoway.rds"))
m_val_baseline <- readRDS(file.path(out_dir, "m_val_baseline.rds"))
m_val_decomp   <- readRDS(file.path(out_dir, "m_val_decomp.rds"))
m_cross_cw     <- readRDS(file.path(out_dir, "m_cross_cw.rds"))
m_cross_aw     <- readRDS(file.path(out_dir, "m_cross_aw.rds"))
m_joint_cw     <- readRDS(file.path(out_dir, "m_joint_cw.rds"))
m_joint_aw     <- readRDS(file.path(out_dir, "m_joint_aw.rds"))

# ── Shared coefficient dictionary ─────────────────────────────────────────────

coef_dict <- c(
  "gid_1"                                      = "ADM1",
  "week_start"                                 = "Week",
  "country_week"                               = "Country $\\times$ Week",
  "neighbor_strike_within_t1_t2"               = "Neighbor strike (t$-$1, t$-$2)",
  "neighbor_strike_cross_t1_t2"                = "Cross-border neighbor strike (t$-$1, t$-$2)",
  "neighbor_strike_within_t1_t1"               = "Neighbor strike (t$-$1 only)",
  "neighbor_strike_within_t2_t2"               = "Neighbor strike (t$-$2 only)",
  "country_share_t1_t2"                        = "Country share (t$-$1, t$-$2)",
  "freexp_z"                                   = "Freedom of expression (z)",
  "frassoc_z"                                  = "Freedom of association (z)",
  "repression_z"                               = "State repression (z)",
  "neighbor_strike_within_t1_t2:freexp_z"      = "Neighbor strike $\\times$ Expression",
  "neighbor_strike_within_t1_t2:frassoc_z"     = "Neighbor strike $\\times$ Association",
  "neighbor_strike_within_t1_t2:repression_z"  = "Neighbor strike $\\times$ Repression",
  "country_share_t1_t2:freexp_z"               = "Country share $\\times$ Expression",
  "country_share_t1_t2:frassoc_z"              = "Country share $\\times$ Association",
  "country_share_t1_t2:repression_z"           = "Country share $\\times$ Repression",
  "freexp_z:country_share_t1_t2"               = "Country share $\\times$ Expression",
  "frassoc_z:country_share_t1_t2"              = "Country share $\\times$ Association",
  "repression_z:country_share_t1_t2"           = "Country share $\\times$ Repression"
)

# ── Shared etable style ───────────────────────────────────────────────────────

etable_style <- style.tex(
  main        = "base",
  depvar.title = "",
  model.format = "(i)",
  line.top    = "\\hline",
  line.bottom = "\\hline"
)

# ── Table 1: Baseline (pooled + separate lags) ────────────────────────────────

tbl_baseline <- list(
  "(1) Pooled"  = m_baseline,
  "(2) t$-$1"   = m_lag1,
  "(3) t$-$2"   = m_lag2
)

# ── Table 2: National vs. neighborhood decomposition ─────────────────────────

tbl_decomposition <- list(
  "(1) Country"  = m_country,
  "(2) Neighbor" = m_neighbor_aw,
  "(3) Both"     = m_decomp
)

# ── Table 3: Institutional moderation (geographic channel only) ──────────────

tbl_moderation <- list(
  "(1) Expression"  = m_freexp,
  "(2) Association" = m_frassoc,
  "(3) Repression"  = m_repression,
  "(4) Joint"       = m_joint_mod
)

# ── Table 4: Institutional moderation (both channels) ────────────────────────

tbl_moderation_ext <- list(
  "(1) Expression"  = m_freexp_ext,
  "(2) Association" = m_frassoc_ext,
  "(3) Repression"  = m_repression_ext,
  "(4) Joint"       = m_joint_mod_ext
)

# ── Table A1: Robustness — alternative SEs ───────────────────────────────────

tbl_robust_se <- list(
  "(1) ADM1 cluster"    = m_baseline,
  "(2) Two-way cluster" = m_twoway,
  "(3) Logit"           = m_logit
)

# ── Table A2: Validated locations — baseline ─────────────────────────────────

tbl_val_baseline <- list(
  "(1) Full sample"    = m_baseline,
  "(2) Validated only" = m_val_baseline
)

# ── Table A3: Validated locations — decomposition ────────────────────────────

tbl_val_decomp <- list(
  "(1) Full sample"    = m_decomp,
  "(2) Validated only" = m_val_decomp
)

# ── Table A4: Cross-border diffusion ─────────────────────────────────────────

tbl_cross_border <- list(
  "(1) Cross, cw FE"   = m_cross_cw,
  "(2) Cross, week FE" = m_cross_aw,
  "(3) Joint, cw FE"   = m_joint_cw,
  "(4) Joint, week FE" = m_joint_aw
)

# ── Summary statistics ────────────────────────────────────────────────────────

panel <- read_parquet(here("data/analysis/contagion_panel.parquet"))

sumstats_data <- panel |>
  filter(!is.na(neighbor_strike_within_t1_t2), !is.na(strike_onset)) |>
  select(
    `Strike onset`               = strike_onset,
    `Neighbor strike (t-1, t-2)` = neighbor_strike_within_t1_t2,
    `Freedom of expression (z)`  = freexp_z,
    `Freedom of association (z)` = frassoc_z,
    `State repression (z)`       = repression_z
  )

tbl_sumstats <- datasummary(
  All(sumstats_data) ~ N + Mean + SD + Min + Max,
  data   = sumstats_data,
  fmt    = 3,
  output = "data.frame"
)
