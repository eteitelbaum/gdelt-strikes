# tools/contagion/merge_vdem.R
#
# Phase 5: Merge V-Dem institutional moderators onto the ADM1×week panel
# and save the final analysis-ready dataset.
#
# V-Dem is annual; values are repeated across all weeks within each year.
# Moderators are standardized (z-scored) for interpretability of interactions.
#
# Inputs:
#   data/analysis/contagion_panel_adj.parquet  (from build_adjacency.R)
#
# Output:
#   data/analysis/contagion_panel.parquet      (final analysis dataset)
#
# V-Dem variables (confirm codes before preregistration):
#   v2x_freexp_altinf  — freedom of expression (H2)
#   v2x_frassoc_thick  — freedom of association (H3)
#   v2x_clphy          — physical violence index / repression (H4)

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(lubridate)
  library(vdemdata)
  library(countrycode)
  library(here)
})

ROOT     <- here::here()
IN_PATH  <- file.path(ROOT, "data/analysis/contagion_panel_adj.parquet")
OUT_PATH <- file.path(ROOT, "data/analysis/contagion_panel.parquet")

VDEM_VARS <- c("v2x_freexp_altinf", "v2x_frassoc_thick", "v2x_clphy")

cat("=== Phase 5: V-Dem merge ===\n\n")

# ── Load panel ────────────────────────────────────────────────────────────────

cat("Loading adjacency panel...\n")
panel <- read_parquet(IN_PATH)
cat("  Rows:", nrow(panel), "| ADM1 units:", n_distinct(panel$gid_1), "\n\n")

# ── Extract V-Dem ─────────────────────────────────────────────────────────────

cat("Extracting V-Dem variables...\n")
vdem_annual <- vdem |>
  as_tibble() |>
  select(iso3 = country_text_id, year, all_of(VDEM_VARS)) |>
  filter(!is.na(iso3)) |>
  rename(
    freexp     = v2x_freexp_altinf,
    frassoc    = v2x_frassoc_thick,
    repression = v2x_clphy
  )

cat("  V-Dem years available:", min(vdem_annual$year), "–",
    max(vdem_annual$year), "\n")
cat("  Countries:", n_distinct(vdem_annual$iso3), "\n\n")

# ── Check ISO3 coverage ───────────────────────────────────────────────────────

panel_country_years <- panel |>
  mutate(year = year(week_start)) |>
  distinct(gid_0, year)

unmatched <- panel_country_years |>
  anti_join(vdem_annual |> distinct(iso3), by = c("gid_0" = "iso3"))

if (nrow(unmatched) > 0) {
  cat("GID_0 codes not matched directly to V-Dem (attempting countrycode bridge):\n")
  print(distinct(unmatched, gid_0))

  # Bridge via countrycode for edge cases (Kosovo, Palestine, Taiwan etc.)
  bridge <- unmatched |>
    distinct(gid_0) |>
    mutate(
      iso3_bridge = countrycode(gid_0, origin = "iso3c", destination = "iso3c",
                                warn = FALSE)
    ) |>
    filter(!is.na(iso3_bridge))

  if (nrow(bridge) > 0) {
    cat("Bridged via countrycode:", nrow(bridge), "countries\n")
    # Add bridged rows to vdem with original gid_0 as key
    vdem_bridged <- vdem_annual |>
      inner_join(bridge, by = c("iso3" = "iso3_bridge")) |>
      mutate(iso3 = gid_0) |>
      select(-gid_0)
    vdem_annual <- bind_rows(vdem_annual, vdem_bridged)
  }
} else {
  cat("All GID_0 codes matched directly to V-Dem ISO3.\n\n")
}

# ── Merge onto panel ──────────────────────────────────────────────────────────

cat("Merging V-Dem onto panel (country × year → country × week)...\n")

panel <- panel |>
  mutate(year = year(week_start)) |>
  left_join(
    vdem_annual |> rename(gid_0 = iso3),
    by = c("gid_0", "year")
  ) |>
  select(-year)

# Coverage check
n_missing <- sum(is.na(panel$freexp))
cat("  Missing V-Dem (freexp):", n_missing, "/", nrow(panel),
    sprintf("(%.1f%%)\n\n", 100 * n_missing / nrow(panel)))

# ── Standardize moderators ───────────────────────────────────────────────────

panel <- panel |>
  mutate(
    freexp_z     = as.numeric(scale(freexp)),
    frassoc_z    = as.numeric(scale(frassoc)),
    repression_z = as.numeric(scale(repression))
  )

# ── Add FE identifiers ────────────────────────────────────────────────────────

# country × week FE string (absorbed by fixest via ^gid_0^week_start or
# as a factor interaction)
panel <- panel |>
  mutate(country_week = paste(gid_0, week_start, sep = "_"))

# ── Summary ──────────────────────────────────────────────────────────────────

cat("Final panel summary:\n")
cat("  Rows:               ", nrow(panel), "\n")
cat("  ADM1 units (gid_1): ", n_distinct(panel$gid_1), "\n")
cat("  Countries (gid_0):  ", n_distinct(panel$gid_0), "\n")
cat("  Weeks:              ", n_distinct(panel$week_start), "\n")
cat("  Strike onset rate:  ",
    round(mean(panel$strike_onset, na.rm = TRUE) * 100, 2), "%\n")

cat("\nV-Dem moderator distributions:\n")
panel |>
  select(freexp, frassoc, repression) |>
  tidyr::pivot_longer(everything(), names_to = "variable") |>
  group_by(variable) |>
  summarize(
    n       = sum(!is.na(value)),
    mean    = round(mean(value, na.rm = TRUE), 3),
    sd      = round(sd(value, na.rm = TRUE), 3),
    missing = sum(is.na(value)),
    .groups = "drop"
  ) |>
  print()

# ── Save ─────────────────────────────────────────────────────────────────────

write_parquet(panel, OUT_PATH)
cat("\nSaved →", OUT_PATH, "\n")
