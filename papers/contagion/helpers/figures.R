## figures.R
## Plot objects for contagion-paper.qmd
## Sourced from the paper's setup chunk; creates fig_* objects in the environment.

library(tidyverse)
library(arrow)
library(sf)
library(scales)
library(patchwork)
library(rnaturalearth)
library(here)

conflicted::conflicts_prefer(dplyr::filter)
conflicted::conflicts_prefer(dplyr::lag)
conflicted::conflicts_prefer(lubridate::date)

theme_set(theme_minimal(base_size = 11))

# ── Data ──────────────────────────────────────────────────────────────────────

panel <- read_parquet(here("data/analysis/contagion_panel.parquet"))

adm1_sf <- st_read(
  here("data/spatial/gadm_adm1_simplified.gpkg"),
  quiet = TRUE
)

# ── Figure 1: Weekly strike prevalence ───────────────────────────────────────

fig_strikes_over_time <- panel |>
  group_by(week_start) |>
  summarize(n_striking = sum(strike_onset), .groups = "drop") |>
  ggplot(aes(week_start, n_striking)) +
  geom_line(linewidth = 0.4, color = "steelblue") +
  geom_smooth(
    method = "loess", span = 0.15, se = FALSE,
    color = "firebrick", linewidth = 0.8
  ) +
  labs(
    title = "(a) Weekly ADM1 strike activity",
    x     = NULL,
    y     = "ADM1 regions"
  ) +
  theme(plot.title = element_text(size = 10, face = "plain"))

# ── Figure 2: Coverage map ────────────────────────────────────────────────────

strike_counts <- panel |>
  group_by(gid_1) |>
  summarize(n_onset = sum(strike_onset), .groups = "drop")

map_data <- adm1_sf |>
  left_join(strike_counts, by = c("GID_1" = "gid_1")) |>
  mutate(n_onset_log = log1p(n_onset))

world <- ne_countries(scale = "medium", returnclass = "sf")

fig_coverage_map <- ggplot() +
  geom_sf(data = world, fill = "#d9d9d9", color = "#b0b0b0", linewidth = 0.1) +
  geom_sf(data = map_data, aes(fill = n_onset_log), linewidth = 0.05, color = "white") +
  scale_fill_gradient(
    low      = "#c6dbef",
    high     = "#08306b",
    na.value = "#d9d9d9",
    name     = "Weeks",
    labels   = \(x) round(expm1(x)),
    breaks   = log1p(c(2, 6, 19, 54, 147))
  ) +
  coord_sf(expand = FALSE) +
  theme_minimal() +
  theme(
    legend.position  = "right",
    axis.text        = element_blank(),
    panel.grid.major = element_line(color = "grey90", linewidth = 0.2),
    plot.title       = element_text(size = 10, face = "plain")
  ) +
  labs(x = NULL, y = NULL)

# ── Figure 3: Neighbor exposure panel ────────────────────────────────────────

p_exposure <- panel |>
  filter(!is.na(neighbor_strike_within_t1_t2)) |>
  count(neighbor_strike_within_t1_t2) |>
  mutate(
    pct   = n / sum(n),
    label = c("No neighbor strike", "Neighbor strike")
  ) |>
  ggplot(aes(label, pct)) +
  geom_col(fill = "#08306b") +
  geom_text(aes(label = percent(pct, accuracy = 0.1)), vjust = -0.4, size = 3.5) +
  scale_y_continuous(labels = percent, expand = expansion(mult = c(0, 0.15))) +
  labs(title = "(b) Neighbor exposure", x = NULL, y = "Share of ADM1-weeks") +
  theme(
    plot.title  = element_text(size = 10, face = "plain"),
    axis.text.x = element_text(size = 8)
  )

p_onset <- panel |>
  filter(!is.na(neighbor_strike_within_t1_t2)) |>
  group_by(neighbor_strike_within_t1_t2) |>
  summarize(strike_rate = mean(strike_onset), .groups = "drop") |>
  mutate(
    label = c("No neighbor strike", "Neighbor strike"),
    pct   = percent(strike_rate, accuracy = 0.1)
  ) |>
  ggplot(aes(label, strike_rate)) +
  geom_col(fill = "#08306b") +
  geom_text(aes(label = pct), vjust = -0.4, size = 3.5) +
  scale_y_continuous(labels = percent, expand = expansion(mult = c(0, 0.15))) +
  labs(title = "(b) Strike onset rate", x = NULL, y = "Strike onset rate") +
  theme(
    plot.title   = element_text(size = 10, face = "plain"),
    axis.text.x  = element_text(size = 8)
  )

fig_neighbor_exposure <- p_exposure + p_onset +
  plot_annotation(
    caption = expression(italic("Note: ") * "Strike events derived from GDELT. Neighbor defined as any within-country ADM1 region sharing a border.")
  )

# ── Figure 1: Puzzle (theory section) — trend + onset rates ──────────────────

fig_1 <- (fig_strikes_over_time | p_onset) +
  plot_layout(widths = c(2, 1)) +
  plot_annotation(
    caption = expression(italic("Note: ") * "Strike events derived from GDELT. Neighbor defined as any within-country ADM1 region sharing a border.")
  )

# ── Figure 2: Data section — map + exposure distribution ─────────────────────

fig_2 <- fig_coverage_map +
  labs(caption = expression(italic("Note: ") * "Strike events derived from GDELT. Administrative boundaries from GADM v4.1."))
