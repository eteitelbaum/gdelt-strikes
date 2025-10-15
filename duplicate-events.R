# Check for duplicate GLOBALEVENTID values
cat("=== DUPLICATE GLOBALEVENTID CHECK ===\n\n")

# Count total events and unique event IDs
total_events <- nrow(all_strikes_data)
unique_events <- n_distinct(all_strikes_data$GLOBALEVENTID)

cat("Total strike events:", total_events, "\n")
cat("Unique GLOBALEVENTID values:", unique_events, "\n")
cat("Duplicate events:", total_events - unique_events, "\n")

if (total_events != unique_events) {
  cat("\n⚠️  WARNING: Found duplicate GLOBALEVENTID values!\n\n")
  
  # Find and show duplicate events
  duplicates <- all_strikes_data |>
    group_by(GLOBALEVENTID) |>
    filter(n() > 1) |>
    arrange(GLOBALEVENTID) |>
    select(GLOBALEVENTID, SQLDATE, ActionGeo_CountryCode, ActionGeo_ADM1Code, 
           ActionGeo_FullName, EventCode, Actor1Name, Actor2Name)
  
  cat("Number of GLOBALEVENTID values with duplicates:", n_distinct(duplicates$GLOBALEVENTID), "\n")
  cat("Total duplicate records:", nrow(duplicates), "\n\n")
  
  cat("Sample of duplicate events:\n")
  duplicates |>
    slice_head(n = 10) |>
    print()
  
} else {
  cat("\n✅ All GLOBALEVENTID values are unique - no duplicates found!\n")
}

# No duplicates found! 