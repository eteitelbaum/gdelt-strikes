# Methods Notes

**Date**: 2026-03-19

---

## 1. ADM1 unit selection

### What we do

The analysis panel includes only ADM1 units that appear in the validated GDELT
strike events data — i.e., regions where at least one strike was recorded over
the 2015–2025 period. This yields 745 ADM1 units across 136 countries (568 in
the analysis sample after dropping isolates with no within-country neighbors).

### Rationale

GDELT is a media-derived dataset: events are extracted from news articles, so
a zero in the data is ambiguous — it could mean no strike occurred, or it could
mean a strike occurred but went unreported. Including all global ADM1 units and
treating unobserved regions as true zeros would conflate "no strike" with "no
media coverage," which is a serious threat to validity given GDELT's known
geographic biases:

- Over-representation of English-language and urban media markets
- Under-coverage of rural regions, especially in the Global South
- Systematic gaps in regions with limited press freedom

Restricting to observed regions avoids falsely coding unobserved strikes as
zeros. The implicit assumption is that regions appearing in our sample have
sufficient media coverage that zeros within the panel period are genuinely
informative (i.e., absence of coverage reflects absence of activity rather than
a coverage gap).

### Limitation

This means findings generalize only to regions with sufficient media presence to
generate GDELT coverage — likely urban, economically active, or politically
prominent subnational units. The sample is not representative of all ADM1 units
globally, and results may not extend to poorly-covered regions. This should be
stated as a scope condition in the paper.

### Comparison to alternative approaches

The alternative — a full administrative panel including all ADM1 units in
covered countries — is more common in conflict studies using ACLED, where
coverage is considered more comprehensive and zeros are more reliably true zeros.
For GDELT, the events-based approach is more defensible and is consistent with
prior GDELT-based subnational analyses (e.g., Müller and Rauh 2018; Blair and
Sambanis 2020).

---

## 2. LPM (OLS) vs. logit for binary outcomes

### What we do

The main models use a linear probability model (LPM) estimated via OLS with
high-dimensional fixed effects (`feols` in the `fixest` package). A logit
robustness check is included (`feglm` with `family = binomial`).

### Why LPM rather than logit

The conventional teaching in applied statistics is to use logit or probit for
binary outcomes. In practice, political science and economics research with panel
data and fixed effects has largely shifted to LPM for the following reasons:

**1. The incidental parameters problem.**
Logit with fixed effects suffers from Neyman-Scott incidental parameters bias:
because each fixed effect is estimated from a finite number of observations,
the FE estimates are inconsistent. The bias does not diminish as the number of
units grows — it worsens as more groups are added. With 568 ADM1 FEs and 41,000+
country×week FEs, this is a serious concern. LPM (OLS) does not have this
problem — FE estimates are unbiased regardless of the number of groups.

`feglm` implements a bias-corrected logit estimator (Fernández-Val 2009) that
partially addresses this, and we include it as a robustness check. But the
correction is approximate and computationally demanding with high-dimensional FEs.

**2. Direct interpretability of coefficients.**
LPM coefficients are average marginal effects by construction — a one-unit
change in X shifts P(Y=1) by β percentage points. Logit coefficients are log
odds ratios, requiring post-estimation computation of average marginal effects
(AMEs) for substantive interpretation. With interaction terms (our moderation
models), this matters considerably: LPM interaction coefficients directly measure
the difference in marginal effects, while logit interaction coefficients do not
(Ai and Norton 2003).

**3. Computational feasibility.**
Absorbing high-dimensional FEs is substantially faster and more numerically
stable in OLS than in nonlinear models. This is practically important with
41,000+ country×week cells.

**4. Results are typically similar.**
When the outcome is not extremely rare and predictions are not near the [0,1]
boundaries, LPM and logit marginal effects are close in practice. The primary
concern with LPM — predicting outside [0,1] — matters more for prediction than
for causal inference focused on coefficient estimates.

### Potential concern: rare outcome

Our outcome has a 1.4% baseline rate (0.87% in the validated-only sample), which
is near the lower boundary where LPM performs worst — predicted probabilities
can go negative for some covariate values, and the linear approximation to the
logistic curve is less accurate in the tails. This is the main reason to include
the logit robustness check. In our case the logit results are qualitatively
consistent with LPM, supporting the main specification.

### References

- Ai, C., and Norton, E. C. (2003). Interaction terms in logit and probit models.
  *Economics Letters*, 80(1), 123–129.
- Fernández-Val, I. (2009). Fixed effects estimation of structural parameters and
  marginal effects in panel probit models. *Journal of Econometrics*, 150(1), 71–85.
- Wooldridge, J. M. (2010). *Econometric Analysis of Cross Section and Panel
  Data* (2nd ed.). MIT Press. (Chapter 15 on LPM vs. probit/logit.)
- Angrist, J. D., and Pischke, J.-S. (2009). *Mostly Harmless Econometrics*.
  Princeton University Press. (Chapter 3.4 on LPM.)
