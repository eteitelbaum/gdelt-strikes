# helpers/spatial_helpers.R
# Spatial utility functions for the strike contagion analysis.
#
# Key functions:
#   load_gadm_adm1()             -- load and optionally simplify GADM ADM1 layer
#   build_gadm_adjacency()       -- compute within/cross-border nb lists (with caching)
#   compute_neighbor_exposure()  -- join neighbor strike indicators onto panel

library(sf)
library(spdep)
library(dplyr)
library(purrr)
library(lubridate)
library(glue)


# ── GADM loading ──────────────────────────────────────────────────────────────

#' Load the GADM ADM1 layer, retaining only essential columns.
#'
#' @param gpkg_path  Path to gadm_410-levels.gpkg.
#' @param simplify   If TRUE, simplify geometries before returning (recommended
#'                   before passing to build_gadm_adjacency() to speed up poly2nb).
#' @param dtol       Simplification tolerance in degrees (~0.01 ≈ 1 km).
#' @return sf data frame with columns GID_0, GID_1, NAME_1, geom.
load_gadm_adm1 <- function(gpkg_path, simplify = TRUE, dtol = 0.01) {
  adm1 <- st_read(gpkg_path, layer = "ADM_1", quiet = TRUE) |>
    select(GID_0, GID_1, NAME_1)

  if (simplify) {
    message("Simplifying ADM1 geometries (dTolerance = ", dtol, " degrees)...")
    adm1 <- st_simplify(adm1, preserveTopology = TRUE, dTolerance = dtol)
  }

  adm1
}


# ── Adjacency construction ────────────────────────────────────────────────────

#' Build within-country and cross-border ADM1 adjacency lists from GADM polygons.
#'
#' Uses rook (shared-edge) contiguity via spdep::poly2nb(). Splits the full
#' neighbor list into within-country and cross-border sublists.
#'
#' Results are cached to `cache_path` as an RDS file. On subsequent calls the
#' cache is loaded directly, skipping the (potentially slow) poly2nb step.
#'
#' @param gadm_sf    sf data frame from load_gadm_adm1(); must have GID_0, GID_1.
#' @param cache_path Path to save/load the cached adjacency list (RDS).
#'                   Set to NULL to disable caching.
#' @param snap       Snapping tolerance for poly2nb (degrees). A value of 0.01
#'                   is appropriate after simplification.
#' @return Named list:
#'   $all        spdep nb object -- all contiguous neighbors
#'   $within     spdep nb object -- within-country neighbors only
#'   $cross      spdep nb object -- cross-border neighbors only
#'   $region_ids character vector of GID_1 values (index aligns with nb lists)
#'   $summary    tibble with per-region neighbor counts
build_gadm_adjacency <- function(gadm_sf,
                                 cache_path = "data/spatial/gadm_adjacency.rds",
                                 snap = 0.01) {
  stopifnot(all(c("GID_0", "GID_1") %in% names(gadm_sf)))

  if (!is.null(cache_path) && file.exists(cache_path)) {
    message("Loading cached adjacency list from: ", cache_path)
    return(readRDS(cache_path))
  }

  message("Computing ADM1 topological adjacency (this may take a few minutes)...")
  nb_all     <- poly2nb(gadm_sf, queen = FALSE, snap = snap)
  region_ids <- gadm_sf$GID_1
  country    <- gadm_sf$GID_0

  # Helper: filter an nb list by a predicate on the neighbor's country
  filter_nb <- function(nb, keep_fn) {
    result <- lapply(seq_along(nb), function(i) {
      nbrs <- nb[[i]]
      if (identical(nbrs, 0L)) return(0L)
      kept <- nbrs[keep_fn(i, nbrs)]
      if (length(kept) == 0L) 0L else kept
    })
    class(result)              <- "nb"
    attr(result, "region.id") <- attr(nb, "region.id")
    result
  }

  nb_within <- filter_nb(nb_all, function(i, nbrs) country[nbrs] == country[i])
  nb_cross  <- filter_nb(nb_all, function(i, nbrs) country[nbrs] != country[i])

  summary_tbl <- tibble(
    gid_1              = region_ids,
    gid_0              = country,
    n_neighbors_all    = map_int(nb_all,    \(x) if (identical(x, 0L)) 0L else length(x)),
    n_neighbors_within = map_int(nb_within, \(x) if (identical(x, 0L)) 0L else length(x)),
    n_neighbors_cross  = map_int(nb_cross,  \(x) if (identical(x, 0L)) 0L else length(x))
  )

  adj <- list(
    all        = nb_all,
    within     = nb_within,
    cross      = nb_cross,
    region_ids = region_ids,
    summary    = summary_tbl
  )

  if (!is.null(cache_path)) {
    dir.create(dirname(cache_path), showWarnings = FALSE, recursive = TRUE)
    saveRDS(adj, cache_path)
    message("Adjacency list saved to: ", cache_path)
  }

  adj
}


# ── Neighbor exposure computation ─────────────────────────────────────────────

#' Add a binary neighbor-strike exposure column to an ADM1-week panel.
#'
#' For each (gid_1, week_start), returns 1 if any neighbor of type `type` had
#' strike_onset == 1 during any of the weeks in {week_start - lag_weeks}.
#'
#' Uses a tidy join approach: build a (focal, neighbor) pairs table, shift
#' neighbor strike dates forward by each lag, then aggregate.
#'
#' @param panel_df  data frame with columns: gid_1 (chr), week_start (Date),
#'                  strike_onset (int, 0/1).
#' @param nb_list   Output of build_gadm_adjacency().
#' @param lag_weeks Integer vector of lag weeks. Default 1:2 gives a pooled
#'                  binary indicator: any strike in either t-1 or t-2.
#' @param type      One of "within", "cross", or "all".
#' @return panel_df with an added column named
#'         neighbor_strike_{type}_t{min}_t{max}.
#'         Regions absent from nb_list$region_ids receive NA.
compute_neighbor_exposure <- function(panel_df,
                                      nb_list,
                                      lag_weeks = 1:2,
                                      type = "within") {
  stopifnot(type %in% c("within", "cross", "all"))
  stopifnot(all(c("gid_1", "week_start", "strike_onset") %in% names(panel_df)))

  nb         <- nb_list[[type]]
  region_ids <- nb_list$region_ids
  col_name   <- glue("neighbor_strike_{type}_t{min(lag_weeks)}_t{max(lag_weeks)}")

  # Tidy neighbor-pair lookup: one row per (focal, neighbor) pair
  neighbor_pairs <- imap_dfr(nb, function(nbrs, i) {
    if (identical(nbrs, 0L)) return(NULL)
    tibble(gid_1 = region_ids[i], gid_neighbor = region_ids[nbrs])
  })

  if (nrow(neighbor_pairs) == 0) {
    message("Warning: no neighbor pairs found for type = '", type, "'")
    return(mutate(panel_df, !!col_name := NA_integer_))
  }

  # For each lag k, create a view of neighbor strikes keyed to the *focal* week:
  #   focal_week = neighbor's week + k  (so that a t-1 neighbor strike aligns with focal week t)
  lagged_neighbor_strikes <- map_dfr(lag_weeks, function(k) {
    panel_df |>
      select(gid_neighbor = gid_1, week_start, strike_onset) |>
      mutate(focal_week = week_start + weeks(k)) |>
      select(gid_neighbor, focal_week, strike_onset)
  })

  exposure <- neighbor_pairs |>
    left_join(lagged_neighbor_strikes, by = "gid_neighbor",
              relationship = "many-to-many") |>
    group_by(gid_1, week_start = focal_week) |>
    summarize(
      !!col_name := as.integer(any(strike_onset == 1L, na.rm = TRUE)),
      .groups = "drop"
    )

  # Right-join preserves all rows in panel_df; unmatched regions get NA
  right_join(exposure, panel_df, by = c("gid_1", "week_start"))
}