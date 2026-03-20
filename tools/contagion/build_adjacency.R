# tools/contagion/build_adjacency.R
#
# Phase 4: Build topological adjacency lists from GADM polygons and compute
# binary neighbor strike exposure indicators.
#
# Adjacency is cached to data/spatial/gadm_adjacency.rds — recomputed only
# if the cache is absent or --rebuild flag is passed.
#
# Inputs:
#   data/analysis/contagion_panel_base.parquet  (from build_panel.R)
#   gadm-boundaries/gadm_410-levels.gpkg
#
# Output:
#   data/analysis/contagion_panel_adj.parquet
#   New columns (preregistered):
#     neighbor_strike_within_t1_t2  — binary, pooled t-1 + t-2, within country
#   New columns (exploratory):
#     neighbor_strike_cross_t1_t2   — cross-border neighbors
#     neighbor_strike_within_t1_t1  — within-country, t-1 only
#     neighbor_strike_within_t2_t2  — within-country, t-2 only

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(sf)
  library(spdep)
  library(here)
})

source(here::here("helpers/spatial_helpers.R"))

ROOT       <- here::here()
IN_PATH    <- file.path(ROOT, "data/analysis/contagion_panel_base.parquet")
GADM_PATH  <- file.path(ROOT, "gadm-boundaries/gadm_410-levels.gpkg")
CACHE_PATH <- file.path(ROOT, "data/spatial/gadm_adjacency.rds")
OUT_PATH   <- file.path(ROOT, "data/analysis/contagion_panel_adj.parquet")

# Allow --rebuild flag to force recomputation of adjacency cache
rebuild <- "--rebuild" %in% commandArgs(trailingOnly = TRUE)
if (rebuild && file.exists(CACHE_PATH)) {
  file.remove(CACHE_PATH)
  cat("Removed adjacency cache — will recompute.\n")
}

cat("=== Phase 4: Spatial adjacency and neighbor exposure ===\n\n")

# ── Load panel ────────────────────────────────────────────────────────────────

cat("Loading base panel...\n")
panel <- read_parquet(IN_PATH)
cat("  Rows:", nrow(panel), "| ADM1 units:", n_distinct(panel$gid_1), "\n\n")

# ── Load GADM ADM1 boundaries ─────────────────────────────────────────────────

cat("Loading GADM ADM1 layer (simplified)...\n")
sf_use_s2(FALSE)
adm1_sf <- load_gadm_adm1(GADM_PATH, simplify = TRUE, dtol = 0.01)

# Restrict to countries in panel
panel_countries <- unique(panel$gid_0)
adm1_sf <- adm1_sf |> filter(GID_0 %in% panel_countries)
cat("  ADM1 regions (panel countries only):", nrow(adm1_sf), "\n\n")

# ── Build adjacency ───────────────────────────────────────────────────────────

adj <- build_gadm_adjacency(adm1_sf, cache_path = CACHE_PATH, snap = 0.01)

# Save simplified boundaries for use in diagnostic notebook
adm1_path <- file.path(ROOT, "data/spatial/gadm_adm1_simplified.gpkg")
if (!file.exists(adm1_path)) {
  st_write(adm1_sf, adm1_path, quiet = TRUE)
  cat("Simplified boundaries saved →", adm1_path, "\n")
}

cat("Adjacency summary:\n")
adj$summary |>
  summarize(
    regions_with_within_neighbor = sum(n_neighbors_within > 0),
    regions_no_within_neighbor   = sum(n_neighbors_within == 0),
    median_within_neighbors      = median(n_neighbors_within),
    max_within_neighbors         = max(n_neighbors_within)
  ) |>
  print()
cat("\n")

# Isolates (no within-country neighbors) — documented for methods section
isolates <- adj$summary |>
  filter(n_neighbors_within == 0) |>
  left_join(
    adm1_sf |> sf::st_drop_geometry() |> select(GID_1, NAME_1),
    by = c("gid_1" = "GID_1")
  ) |>
  arrange(gid_0)

cat("Regions with no within-country neighbors (islands/enclaves):",
    nrow(isolates), "\n")
if (nrow(isolates) > 0) {
  print(isolates |> select(gid_0, gid_1, NAME_1), n = 30)
}
cat("\n")

# ── Compute exposure indicators ───────────────────────────────────────────────

cat("Computing neighbor strike exposure indicators...\n")

# Preregistered: within-country, pooled t-1 + t-2
panel <- compute_neighbor_exposure(panel, adj, lag_weeks = 1:2, type = "within")
cat("  neighbor_strike_within_t1_t2: done\n")

# Exploratory: cross-border, pooled t-1 + t-2
panel <- compute_neighbor_exposure(panel, adj, lag_weeks = 1:2, type = "cross")
cat("  neighbor_strike_cross_t1_t2: done\n")

# Exploratory: separate lags for robustness checks
panel <- compute_neighbor_exposure(panel, adj, lag_weeks = 1, type = "within")
cat("  neighbor_strike_within_t1_t1: done\n")

panel <- compute_neighbor_exposure(panel, adj, lag_weeks = 2, type = "within")
cat("  neighbor_strike_within_t2_t2: done\n")

cat("\nExposure distribution (preregistered):\n")
panel |>
  count(neighbor_strike_within_t1_t2) |>
  mutate(pct = round(n / sum(n) * 100, 1)) |>
  print()
cat("\n")

# ── Save ─────────────────────────────────────────────────────────────────────

write_parquet(panel, OUT_PATH)
cat("Saved →", OUT_PATH, "\n")
