# Revision To-Dos

## Paper (contagion-paper.qmd)

### Add two-way clustering table to appendix
The two-way clustering robustness check (ADM1 + country-week) has been run and the model object is saved at `outputs/models/contagion/m_twoway.rds`. It is currently referenced in the text but has no dedicated appendix table. Add a table comparing ADM1-only vs. two-way clustered SEs on the baseline specification. The `modelsummary` code for this already exists in `notebooks/03-modeling/explanatory/contagion-models.qmd` (chunk `robustness-twoway-cluster`).
