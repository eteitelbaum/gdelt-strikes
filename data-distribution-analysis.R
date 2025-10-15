#!/usr/bin/env Rscript

# Data Distribution Analysis for Strike Prediction
# Checking country-year distributions and temporal patterns

library(dplyr)
library(lubridate)
library(arrow)
library(ggplot2)
library(stringr)

# Load the raw data
cat("Loading GDELT strikes data...\n")
all_strikes_data <- read_parquet("data/raw/gdelt_strikes.parquet")

cat("Raw data dimensions:", nrow(all_strikes_data), "x", ncol(all_strikes_data), "\n")

# Apply same filters as main analysis
filtered_data <- all_strikes_data |>
  filter(
    !is.na(ActionGeo_ADM1Code), 
    !is.na(ActionGeo_CountryCode),
    ActionGeo_ADM1Code != ActionGeo_CountryCode
  ) |>
  mutate(
    date = as.Date(SQLDATE, format = "%Y%m%d"),
    year = year(date),
    month = month(date),
    year_month = floor_date(date, "month")
  )

cat("Filtered data dimensions:", nrow(filtered_data), "x", ncol(filtered_data), "\n")

# === TEMPORAL DISTRIBUTION ANALYSIS ===
cat("\n=== TEMPORAL DISTRIBUTION ===\n")

# Events by year
yearly_counts <- filtered_data |>
  count(year, name = "events") |>
  arrange(year)

print("Events by year:")
print(yearly_counts)

# Date range
cat("Date range:", min(filtered_data$date), "to", max(filtered_data$date), "\n")

# === COUNTRY DISTRIBUTION ANALYSIS ===
cat("\n=== COUNTRY DISTRIBUTION ===\n")

# Events by country
country_counts <- filtered_data |>
  count(ActionGeo_CountryCode, name = "total_events") |>
  arrange(desc(total_events))

cat("Total unique countries:", nrow(country_counts), "\n")
cat("Top 15 countries by event count:\n")
print(head(country_counts, 15))

# Countries with very few events
sparse_countries <- country_counts |>
  filter(total_events < 100)

cat("Countries with < 100 events:", nrow(sparse_countries), "\n")
cat("This represents", round(100 * nrow(sparse_countries) / nrow(country_counts), 1), "% of all countries\n")

# === COUNTRY-YEAR DISTRIBUTION ===
cat("\n=== COUNTRY-YEAR DISTRIBUTION ===\n")

country_year_counts <- filtered_data |>
  count(ActionGeo_CountryCode, year, name = "events") |>
  arrange(ActionGeo_CountryCode, year)

# Summary statistics
country_year_summary <- country_year_counts |>
  summarise(
    total_country_years = n(),
    mean_events = mean(events),
    median_events = median(events),
    min_events = min(events),
    max_events = max(events),
    q25 = quantile(events, 0.25),
    q75 = quantile(events, 0.75)
  )

cat("Country-year combinations:", country_year_summary$total_country_years, "\n")
cat("Events per country-year - Mean:", round(country_year_summary$mean_events, 1), 
    "Median:", country_year_summary$median_events, "\n")
cat("Events per country-year - Min:", country_year_summary$min_events, 
    "Max:", country_year_summary$max_events, "\n")

# Very sparse country-years
sparse_country_years <- country_year_counts |>
  filter(events < 10)

cat("Country-years with < 10 events:", nrow(sparse_country_years), 
    "(", round(100 * nrow(sparse_country_years) / nrow(country_year_counts), 1), "%)\n")

# Countries with consistent activity across years
countries_by_year_coverage <- country_year_counts |>
  group_by(ActionGeo_CountryCode) |>
  summarise(
    years_active = n(),
    total_events = sum(events),
    avg_events_per_year = mean(events),
    .groups = "drop"
  ) |>
  arrange(desc(years_active), desc(total_events))

cat("\nCountries with most consistent year coverage:\n")
print(head(countries_by_year_coverage, 10))

# === WEEKLY AGGREGATION IMPACT ===
cat("\n=== WEEKLY AGGREGATION ANALYSIS ===\n")

# Simulate the weekly aggregation from main analysis
weekly_data <- filtered_data |>
  mutate(year_week = floor_date(date, "week")) |>
  group_by(ActionGeo_CountryCode, ActionGeo_ADM1Code, year_week) |>
  summarise(
    strike_count = n(),
    year = year(first(year_week)),
    .groups = "drop"
  )

cat("Weekly observations:", nrow(weekly_data), "\n")

# Country-year distribution at weekly level
weekly_country_year <- weekly_data |>
  group_by(ActionGeo_CountryCode, year) |>
  summarise(
    weeks_with_activity = n(),
    total_strikes = sum(strike_count),
    avg_strikes_per_week = mean(strike_count),
    .groups = "drop"
  )

weekly_summary <- weekly_country_year |>
  summarise(
    mean_weeks_active = mean(weeks_with_activity),
    median_weeks_active = median(weeks_with_activity),
    mean_strikes_per_week = mean(avg_strikes_per_week),
    .groups = "drop"
  )

cat("Average weeks with activity per country-year:", round(weekly_summary$mean_weeks_active, 1), "\n")
cat("Median weeks with activity per country-year:", weekly_summary$median_weeks_active, "\n")

# === STRATIFICATION FEASIBILITY ===
cat("\n=== STRATIFICATION FEASIBILITY ===\n")

# For stratification to work well, we need sufficient samples in each stratum
# Check country representation across time

# Temporal split point analysis (e.g., 80% for training)
total_weeks <- weekly_data |>
  summarise(
    min_week = min(year_week),
    max_week = max(year_week),
    total_weeks = as.numeric(difftime(max(year_week), min(year_week), units = "weeks"))
  )

# 80% split point
split_week <- total_weeks$min_week + weeks(round(0.8 * total_weeks$total_weeks))
cat("Suggested 80% temporal split at week:", as.character(split_week), "\n")

# Check country representation before/after split
country_temporal_split <- weekly_data |>
  mutate(split_group = ifelse(year_week <= split_week, "train", "test")) |>
  group_by(ActionGeo_CountryCode, split_group) |>
  summarise(observations = n(), .groups = "drop") |>
  tidyr::pivot_wider(names_from = split_group, values_from = observations, values_fill = 0) |>
  mutate(
    total = train + test,
    train_prop = train / total,
    in_both_splits = train > 0 & test > 0
  )

countries_in_both <- sum(country_temporal_split$in_both_splits)
total_countries <- nrow(country_temporal_split)

cat("Countries represented in both train and test splits:", countries_in_both, "/", total_countries, 
    "(", round(100 * countries_in_both / total_countries, 1), "%)\n")

# Countries only in training data
train_only <- country_temporal_split |>
  filter(train > 0 & test == 0)

cat("Countries only in training data:", nrow(train_only), "\n")

# Countries only in test data  
test_only <- country_temporal_split |>
  filter(train == 0 & test > 0)

cat("Countries only in test data:", nrow(test_only), "\n")

# === RECOMMENDATIONS ===
cat("\n=== RECOMMENDATIONS ===\n")

if (countries_in_both / total_countries < 0.7) {
  cat("⚠️  WARNING: Less than 70% of countries appear in both train/test splits\n")
  cat("   Temporal split may create geographic bias\n")
  cat("   Consider: \n")
  cat("   - Longer time series requirement\n") 
  cat("   - Country filtering (keep only countries with sufficient temporal coverage)\n")
  cat("   - Grouped time series cross-validation instead\n")
} else {
  cat("✅ Temporal split appears feasible - good country representation\n")
}

if (weekly_summary$median_weeks_active < 10) {
  cat("⚠️  WARNING: Many country-years have very sparse weekly activity\n")
  cat("   Consider monthly aggregation instead of weekly\n")
} else {
  cat("✅ Weekly aggregation appears reasonable\n")
}

cat("\n=== SUMMARY STATISTICS FOR REFERENCE ===\n")
cat("Countries:", total_countries, "\n")
cat("Country-years:", nrow(country_year_counts), "\n") 
cat("Weekly observations:", nrow(weekly_data), "\n")
cat("Date range:", as.character(total_weeks$min_week), "to", as.character(total_weeks$max_week), "\n")
cat("Suggested train-test split week:", as.character(split_week), "\n") 