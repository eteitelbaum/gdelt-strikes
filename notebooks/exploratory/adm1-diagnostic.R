# Diagnostic: Check ADM1 code quality
# Country codes are typically 2-3 characters, ADM1 codes should be longer

adm1_diagnostic <- all_strikes_data |>
  filter(!is.na(ActionGeo_ADM1Code), !is.na(ActionGeo_CountryCode)) |>
  mutate(
    # Check if ADM1 code is just the country code repeated
    is_genuine_adm1 = ActionGeo_ADM1Code != ActionGeo_CountryCode,
    # Check if ADM1 is longer than country code (another indicator)
    adm1_longer = nchar(ActionGeo_ADM1Code) > nchar(ActionGeo_CountryCode),
    # Combined check - genuine if either condition is true
    has_regional_info = is_genuine_adm1 | adm1_longer
  )

# Summary statistics
cat("=== ADM1 CODE QUALITY DIAGNOSTIC ===\n\n")

total_strikes <- nrow(adm1_diagnostic)
genuine_adm1 <- sum(adm1_diagnostic$has_regional_info)
country_only <- sum(!adm1_diagnostic$has_regional_info)

cat("Total strikes with location data:", total_strikes, "\n")
cat("Strikes with genuine ADM1 codes:", genuine_adm1, "(", round(100*genuine_adm1/total_strikes, 1), "%)\n")
cat("Strikes with country-only codes:", country_only, "(", round(100*country_only/total_strikes, 1), "%)\n\n")

# Show examples of each type
cat("=== EXAMPLES ===\n")
cat("Genuine ADM1 codes (regional data):\n")
adm1_diagnostic |>
  filter(has_regional_info) |>
  select(ActionGeo_CountryCode, ActionGeo_ADM1Code, ActionGeo_FullName) |>
  distinct() |>
  slice_head(n = 10) |>
  print()

cat("\nCountry-only codes (no regional detail):\n")
adm1_diagnostic |>
  filter(!has_regional_info) |>
  select(ActionGeo_CountryCode, ActionGeo_ADM1Code, ActionGeo_FullName) |>
  distinct() |>
  slice_head(n = 10) |>
  print()