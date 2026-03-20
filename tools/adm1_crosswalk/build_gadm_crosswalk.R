# build_gadm_crosswalk.R
#
# Creates data/crosswalks/gdelt_gadm_adm1.parquet
#
# Assigns a GADM 4.1 GID_1 identifier to each validated strike event, using
# two methods depending on geo_quality:
#
#   confirmed / unvalidated events:
#     Coordinate-based spatial join — original GDELT lat/lon is trusted;
#     st_within() assigns each point to the GADM polygon containing it.
#
#   corrected events (match == "no"):
#     Name-based join — original coordinates are wrong (that's why they were
#     corrected); use final_adm1_name matched against GADM NAME_1 instead.
#
#   NA geo_quality (country-level codes, no ADM1):
#     Excluded — no GID_1 can be assigned.
#
# Output columns:
#   GLOBALEVENTID  — event identifier
#   gid_1          — GADM 4.1 ADM1 identifier (e.g. "TUR.42_1")
#   gid_0          — ISO 3166-1 alpha-3 country code (e.g. "TUR")
#   name_1         — GADM standardized ADM1 name
#   assign_method  — "spatial" or "name_match"
#
# Usage (from project root):
#   Rscript tools/adm1_crosswalk/build_gadm_crosswalk.R

suppressPackageStartupMessages({
  library(arrow)
  library(sf)
  library(dplyr)
  library(stringr)
  library(readr)
  library(here)
})

ROOT     <- here::here()
GVF_PATH <- file.path(ROOT, "data/enhanced/geo_validation_final.csv")
GDELT_PATH <- file.path(ROOT, "data/enhanced/gdelt_strikes.parquet")
GADM_PATH  <- file.path(ROOT, "gadm-boundaries/gadm_410-levels.gpkg")
OUT_DIR    <- file.path(ROOT, "data/crosswalks")
OUT_PATH   <- file.path(OUT_DIR, "gdelt_gadm_adm1.parquet")

cat("=== GDELT → GADM ADM1 Crosswalk Builder ===\n\n")

# ── 1. Load validated events ──────────────────────────────────────────────────

cat("Loading geo_validation_final.csv...\n")
gvf <- read_csv(GVF_PATH, show_col_types = FALSE) |>
  select(GLOBALEVENTID, match, geo_quality, final_adm1_name, final_country_iso2)

cat("  Total events:", nrow(gvf), "\n")
cat("  geo_quality distribution:\n")
print(table(gvf$geo_quality, useNA = "always"))
cat("\n")

# Join coordinates and dates from gdelt_strikes
cat("Joining coordinates from gdelt_strikes.parquet...\n")
gdelt <- read_parquet(GDELT_PATH) |>
  select(GLOBALEVENTID, SQLDATE, ActionGeo_Lat, ActionGeo_Long) |>
  mutate(GLOBALEVENTID = as.character(GLOBALEVENTID))

events <- gvf |>
  mutate(GLOBALEVENTID = as.character(GLOBALEVENTID)) |>
  left_join(gdelt, by = "GLOBALEVENTID")

# Split into two groups
events_spatial <- events |>
  filter(geo_quality %in% c("validated", "unvalidated"), match != "no") |>
  filter(!is.na(ActionGeo_Lat), !is.na(ActionGeo_Long))

events_corrected <- events |>
  filter(match == "no", !is.na(final_adm1_name), geo_quality == "validated")

events_excluded <- events |>
  filter(is.na(geo_quality))

cat("  Spatial join group (confirmed/unvalidated):", nrow(events_spatial), "\n")
cat("  Name match group (corrected):              ", nrow(events_corrected), "\n")
cat("  Excluded (no ADM1):                        ", nrow(events_excluded), "\n\n")

# ── 2. Load and simplify GADM ADM1 polygons ───────────────────────────────────

cat("Loading GADM ADM1 layer...\n")
sf_use_s2(FALSE)  # use planar geometry to avoid S2 validation errors on GADM
adm1_sf <- st_read(GADM_PATH, layer = "ADM_1", quiet = TRUE) |>
  select(GID_0, GID_1, NAME_1)

cat("  Regions:", nrow(adm1_sf), "| Countries:", n_distinct(adm1_sf$GID_0), "\n")
cat("  Simplifying geometries (dTolerance = 0.01 degrees)...\n")
adm1_sf <- st_simplify(adm1_sf, preserveTopology = TRUE, dTolerance = 0.01)
cat("  Size after simplification:",
    format(object.size(adm1_sf), units = "MB"), "\n\n")

# ── 3. Spatial join (confirmed / unvalidated events) ─────────────────────────

cat("Running spatial join for", nrow(events_spatial), "events...\n")

points_sf <- events_spatial |>
  st_as_sf(coords = c("ActionGeo_Long", "ActionGeo_Lat"), crs = 4326)

joined_spatial <- st_join(points_sf, adm1_sf, join = st_within, left = TRUE) |>
  st_drop_geometry() |>
  select(GLOBALEVENTID, gid_1 = GID_1, gid_0 = GID_0, name_1 = NAME_1) |>
  mutate(assign_method = "spatial")

n_matched_spatial <- sum(!is.na(joined_spatial$gid_1))
cat("  Matched:", n_matched_spatial, "/", nrow(joined_spatial),
    sprintf("(%.1f%%)\n\n", 100 * n_matched_spatial / nrow(joined_spatial)))

# ── 4. Name-based join (corrected events) ────────────────────────────────────

cat("Running name match for", nrow(events_corrected), "corrected events...\n")

# Build GADM name lookup: NAME_1 (lower, stripped) → GID_1, GID_0
gadm_names <- adm1_sf |>
  st_drop_geometry() |>
  mutate(name_key = str_to_lower(str_trim(NAME_1))) |>
  select(GID_0, GID_1, NAME_1, name_key)

# For corrected events, filter GADM to matching country first where possible
corrected_keyed <- events_corrected |>
  mutate(name_key = str_to_lower(str_trim(final_adm1_name)))

# Country-constrained match: add country column to lookup for filtering
gadm_lookup <- gadm_names |>
  select(gid_0 = GID_0, gid_1 = GID_1, name_1 = NAME_1, name_key)

# Step 1: try within country
country_match <- corrected_keyed |>
  left_join(
    gadm_lookup,
    by = c("name_key", "final_country_iso2" = "gid_0")
  )

matched   <- country_match |> filter(!is.na(gid_1))
unmatched <- country_match |> filter(is.na(gid_1)) |>
  select(-gid_1, -name_1)

if (nrow(unmatched) > 0) {
  global_match <- unmatched |>
    left_join(gadm_lookup, by = "name_key")
  joined_corrected <- bind_rows(matched, global_match) |>
    select(GLOBALEVENTID, gid_1, gid_0, name_1) |>
    mutate(assign_method = "name_match")
} else {
  joined_corrected <- matched |>
    select(GLOBALEVENTID, gid_1, gid_0, name_1) |>
    mutate(assign_method = "name_match")
}

n_matched_name <- sum(!is.na(joined_corrected$gid_1))
cat("  Matched:", n_matched_name, "/", nrow(joined_corrected),
    sprintf("(%.1f%%)\n\n", 100 * n_matched_name / nrow(joined_corrected)))

# ── 5. Combine and save ───────────────────────────────────────────────────────

crosswalk <- bind_rows(joined_spatial, joined_corrected) |>
  filter(!is.na(gid_1))

cat("Combined crosswalk:\n")
cat("  Total events with GID_1:", nrow(crosswalk), "\n")
cat("  By method:\n")
print(table(crosswalk$assign_method))
cat("\n")

dir.create(OUT_DIR, showWarnings = FALSE, recursive = TRUE)
write_parquet(crosswalk, OUT_PATH)
cat("Saved →", OUT_PATH, "\n")

# ── 6. QA ─────────────────────────────────────────────────────────────────────

cat("\n=== QA Summary ===\n")
cat("Input events:              ", nrow(events), "\n")
cat("Excluded (no ADM1):        ", nrow(events_excluded), "\n")
cat("Assigned GID_1:            ", nrow(crosswalk), "\n")
cat("Unassigned (both methods): ",
    nrow(events) - nrow(events_excluded) - nrow(crosswalk), "\n")
cat("Coverage:                  ",
    sprintf("%.1f%%\n", 100 * nrow(crosswalk) / (nrow(events) - nrow(events_excluded))))
