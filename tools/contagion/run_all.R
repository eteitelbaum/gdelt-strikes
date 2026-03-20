# tools/contagion/run_all.R
#
# Full contagion data build pipeline — runs all phases in order.
#
# Prerequisites (run once before this script):
#   Rscript tools/adm1_crosswalk/build_gadm_crosswalk.R
#
# Usage (from project root):
#   Rscript tools/contagion/run_all.R
#   Rscript tools/contagion/run_all.R --rebuild   # force adjacency recomputation

library(here)

ROOT <- here::here()

run_phase <- function(script, label) {
  cat("\n", strrep("─", 60), "\n", sep = "")
  cat(label, "\n")
  cat(strrep("─", 60), "\n\n", sep = "")
  source(file.path(ROOT, script))
}

run_phase("tools/contagion/build_panel.R",    "PHASE 1-3: Panel construction")
run_phase("tools/contagion/build_adjacency.R","PHASE 4:   Spatial adjacency")
run_phase("tools/contagion/merge_vdem.R",     "PHASE 5:   V-Dem merge")

cat("\n", strrep("═", 60), "\n", sep = "")
cat("Pipeline complete.\n")
cat("Output: data/analysis/contagion_panel.parquet\n")
cat(strrep("═", 60), "\n", sep = "")
