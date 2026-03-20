# tools/contagion/build_panel.R
#
# Phase 1-3: Load validated strike events, assign GADM GID_1, aggregate to
# balanced ADM1×week panel.
#
# Inputs:
#   data/enhanced/geo_validation_final.csv
#   data/enhanced/gdelt_strikes.parquet
#   data/crosswalks/gdelt_gadm_adm1.parquet  (from tools/adm1_crosswalk/build_gadm_crosswalk.R)
#
# Output:
#   data/analysis/contagion_panel_base.parquet
#   Columns: gid_1, gid_0, week_start, strike_count, strike_onset, geo_quality

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(lubridate)
  library(readr)
  library(tidyr)
  library(here)
})

ROOT          <- here::here()
GVF_PATH      <- file.path(ROOT, "data/enhanced/geo_validation_final.csv")
GDELT_PATH    <- file.path(ROOT, "data/enhanced/gdelt_strikes.parquet")
CROSSWALK_PATH <- file.path(ROOT, "data/crosswalks/gdelt_gadm_adm1.parquet")
OUT_PATH      <- file.path(ROOT, "data/analysis/contagion_panel_base.parquet")

cat("=== Phase 1-3: Event loading and panel construction ===\n\n")

# ── Phase 1: Load and prepare events ─────────────────────────────────────────

cat("Loading geo_validation_final.csv...\n")
gvf <- read_csv(GVF_PATH, show_col_types = FALSE) |>
  filter(!is.na(geo_quality))   # drop country-level / no-ADM1 events

cat("  Events with assignable ADM1:", nrow(gvf), "\n")
cat("  geo_quality distribution:\n")
print(table(gvf$geo_quality))
cat("\n")

cat("Joining dates from gdelt_strikes.parquet...\n")
gdelt_dates <- read_parquet(GDELT_PATH) |>
  select(GLOBALEVENTID, SQLDATE) |>
  mutate(GLOBALEVENTID = as.character(GLOBALEVENTID))

events <- gvf |>
  mutate(GLOBALEVENTID = as.character(GLOBALEVENTID)) |>
  left_join(gdelt_dates, by = "GLOBALEVENTID") |>
  mutate(
    date       = ymd(SQLDATE),
    week_start = floor_date(date, "week", week_start = 1)  # Monday weeks
  )

cat("  Date range:", format(min(events$date)), "–", format(max(events$date)), "\n\n")

# ── Phase 2: Assign GADM GID_1 ───────────────────────────────────────────────

cat("Loading GADM crosswalk...\n")
if (!file.exists(CROSSWALK_PATH)) {
  stop(
    "Crosswalk not found: ", CROSSWALK_PATH, "\n",
    "Run: Rscript tools/adm1_crosswalk/build_gadm_crosswalk.R"
  )
}

crosswalk <- read_parquet(CROSSWALK_PATH) |>
  mutate(GLOBALEVENTID = as.character(GLOBALEVENTID))

cat("  Crosswalk rows:", nrow(crosswalk), "\n")
cat("  Assignment method:\n")
print(table(crosswalk$assign_method))
cat("\n")

events <- events |>
  left_join(
    crosswalk |> select(GLOBALEVENTID, gid_1, gid_0, name_1),
    by = "GLOBALEVENTID"
  ) |>
  filter(!is.na(gid_1))

n_assigned <- nrow(events)
cat("Events with GID_1 assigned:", n_assigned, "\n\n")

# ── Phase 3: Aggregate to balanced ADM1×week panel ───────────────────────────

cat("Aggregating to ADM1×week...\n")

weekly <- events |>
  group_by(gid_1, gid_0, week_start) |>
  summarize(
    strike_count = n(),
    # Best geo_quality in this cell (validated > unvalidated)
    geo_quality  = if_else(
      any(geo_quality == "validated"), "validated", "unvalidated"
    ),
    .groups = "drop"
  )

cat("  Observed ADM1-weeks with strikes:", nrow(weekly), "\n")

# Expand to full balanced panel
all_gid1  <- unique(weekly$gid_1)
all_weeks <- seq(min(weekly$week_start), max(weekly$week_start), by = "week")

cat("  ADM1 units:", length(all_gid1), "\n")
cat("  Weeks:     ", length(all_weeks), "\n")

panel <- expand_grid(gid_1 = all_gid1, week_start = all_weeks) |>
  left_join(weekly, by = c("gid_1", "week_start")) |>
  mutate(
    strike_count = replace_na(strike_count, 0L),
    strike_onset = as.integer(strike_count > 0),
    geo_quality  = replace_na(geo_quality, "zero")   # zero-strike weeks
  ) |>
  left_join(
    events |> distinct(gid_1, gid_0),
    by = "gid_1"
  ) |>
  # gid_0 may be NA for zero-strike rows; fill from weekly
  mutate(gid_0 = coalesce(gid_0.x, gid_0.y)) |>
  select(-gid_0.x, -gid_0.y)

cat("\nBalanced panel:\n")
cat("  Rows:", nrow(panel), "\n")
cat("  Strike onset prevalence:", round(mean(panel$strike_onset) * 100, 2), "%\n\n")

# ── Save ─────────────────────────────────────────────────────────────────────

dir.create(dirname(OUT_PATH), showWarnings = FALSE, recursive = TRUE)
write_parquet(panel, OUT_PATH)
cat("Saved →", OUT_PATH, "\n")
