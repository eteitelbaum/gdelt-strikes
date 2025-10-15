# Bayesian Models Exploration (brms): Notes and Lessons Learned

**Date**: October 10, 2025  
**Status**: Attempted but abandoned due to computational infeasibility  
**Duration**: One epic debugging session

---

## Executive Summary

We attempted to implement zero-truncated Bayesian count models using the `brms` package for Stage 2 severity modeling on positive-only strike counts. While we successfully resolved numerous technical issues, the models proved computationally infeasible for our dataset size (17k+ observations, 200+ features).

**TL;DR**: Stick with gradient boosting models (gamma/log-transformed) on filtered positive-only data. They achieve the same modeling goal without the computational nightmare.

---

## What We Tried

### Original Goal
Implement proper zero-truncated count models for strike severity:
- **brms_ztp**: Zero-truncated Poisson via brms
- **brms_ztnb**: Zero-truncated Negative Binomial via brms

### Implementation Approach
1. Used `brms::brm()` with truncation specified in formula: `strike_count | trunc(lb = 1) ~ predictors`
2. Trained on positive-only filtered data
3. Used proper Bayesian priors for count distributions

---

## Technical Issues Encountered

### Issue 1: Family Function Confusion

**Problem**: Initial implementation used non-existent family functions:
```r
# ❌ WRONG - these don't exist in brms
brms::zero_truncated_poisson()
brms::zero_truncated_negbinomial()
```

**Solution**: Use standard families with truncation in formula:
```r
# ✅ CORRECT
brm(
  strike_count | trunc(lb = 1) ~ .,
  family = poisson(),        # from stats package
  family = negbinomial()     # from brms
)
```

**Key Learning**: 
- `poisson()` comes from base R's `stats` package, NOT brms
- `negbinomial()` is from brms but accessed without `brms::` prefix
- Truncation is specified in the formula, not the family

### Issue 2: The Great Namespace Conflict Cascade

**Problem**: Loading `brms` (and its dependency `foreach`) created an unprecedented cascade of namespace conflicts with the tidyverse/tidymodels/arrow ecosystem.

**The Epic List** (14 conflicts resolved):

| Line | Conflict | Our Choice | Reason |
|------|----------|------------|--------|
| 28 | `accumulate` | `purrr::` | Tidyverse functional programming |
| 29 | `ar` | `brms::` | Autoregressive terms for brms |
| 30 | `buffer` | `arrow::` | Using Arrow for parquet I/O |
| 31 | `chisq.test` | `stats::` | Standard base R chi-square test |
| 32 | `col_factor` | `readr::` | Column specs, not color scales |
| 33 | `dirichlet` | `brms::` | Was brms vs rstanarm |
| 34 | `discard` | `purrr::` | Functional programming companion to keep() |
| 35 | `duration` | `lubridate::` | Date/time operations throughout |
| 36 | `exponential` | `brms::` | Was brms vs rstanarm |
| 37 | `fisher.test` | `stats::` | Standard statistical test |
| 38 | `get_y` | `brms::` | brms-specific function |
| 39 | `penguins` 🐧 | `modeldata::` | The most absurd conflict of all |
| 40 | `timestamp` | `arrow::` | Arrow data operations |
| 41 | `when` | `purrr::` | Tidyverse functional programming |

**Notable Highlights**:
- **The Penguins Incident**: We're modeling geopolitical labor strikes, and R demanded we choose which version of the Palmer Penguins dataset we prefer. Peak R ecosystem right here. 🐧
- **brms vs rstanarm**: Initially loaded both Bayesian packages, which fought over every distribution function (`dirichlet`, `exponential`, etc.)
- **foreach strikes again**: The `foreach` package (loaded by brms for parallel MCMC) conflicts heavily with `purrr`

**Why This Happened**:
1. R's `library()` dumps ALL exported functions into your search path
2. We're mixing three major ecosystems never designed to work together:
   - Tidyverse/tidymodels (modern functional R)
   - Bayesian Stan ecosystem (brms + dependencies)
   - Apache Arrow (big data C++ library)
3. `foreach` is older and claimed common functional names before tidyverse existed

**Solution**: Removed `rstanarm` (wasn't actually being used) and declared preferences for all 14 conflicts.

### Issue 3: rstanarm Removal

**Why We Removed It**:
- rstanarm was loaded but not actually running any models
- Created numerous conflicts with brms (both export same distribution functions)
- Doesn't support zero-truncation anyway

**What We Commented Out**:
```r
# library(rstanarm)
# occ_stan_spec <- logistic_reg() |> set_engine("stan", ...)
# stan workflow and evaluation code
```

**Result**: Eliminated several brms vs rstanarm conflicts (dirichlet, exponential, etc.)

---

## The Final Showdown: Convergence Failures

### Zero-Truncated Poisson Results

After resolving all technical issues, the model ran but produced:

```
Warning messages:
1: There were 752 transitions after warmup that exceeded the maximum treedepth. 
   Increase max_treedepth above 10.

2: There were 1 chains where the estimated Bayesian Fraction of Missing 
   Information was low.

3: Examine the pairs() plot to diagnose sampling problems

4: The largest R-hat is 3.66, indicating chains have not mixed.
   Running the chains for more iterations may help.

5: Bulk Effective Samples Size (ESS) is too low, indicating posterior means 
   and medians may be unreliable.

6: Tail Effective Samples Size (ESS) is too low, indicating posterior variances 
   and tail quantiles may be unreliable.
```

**Critical Issues**:

| Diagnostic | Value | Interpretation |
|-----------|-------|----------------|
| **R-hat** | 3.66 | 🔴 SEVERE - should be < 1.01. Model completely failed to converge. Results are NOT trustworthy. |
| **Max treedepth** | 752 exceeded | ⚠️ MCMC sampler struggling with geometry |
| **ESS** | Too low | ⚠️ Not enough effective samples for reliable inference |
| **BFMI** | Low | ⚠️ Sampler inefficiency |

### The Final Error

```
Error in `map2()`:
! result would be too long a vector

At: brms:::posterior_epred_trunc_discrete(...)
```

**Root Cause**: When computing `posterior_epred()` for truncated Poisson distributions, brms attempts to create a massive internal vector. With our data size, this vector exceeds R's memory limits.

**This is a fundamental brms limitation** with truncated distributions on large datasets.

---

## Why brms Failed for Our Use Case

### Dataset Characteristics
- **17,000+ observations**
- **200+ features** (after dummy encoding spatial variables)
- **Sparse positive counts** (many weeks with 0 strikes)

### brms Sweet Spot
- **< 5,000 observations**
- **< 50 predictors**
- **Research contexts** where full posterior distributions are scientifically valuable
- **Flexibility** for complex models (multilevel, custom families, etc.)

### Why It Doesn't Work Here

1. **Computational infeasibility**: Truncation calculations don't scale to large datasets
2. **Non-convergence**: 200+ features with weak priors = non-identifiable model
3. **Diminishing returns**: For prediction tasks, gradient boosting provides better performance
4. **Engineering overhead**: 14 namespace conflicts + 2-3 hour runtimes per fold

---

## Lessons Learned

### ✅ What Worked

1. **Systematic conflict resolution**: The `conflicted` package is essential for complex workflows
2. **Understanding family specifications**: Learning the proper brms syntax for truncated models
3. **Recognizing computational limits**: brms is powerful but has a ceiling

### ❌ What Didn't Work

1. **Zero-truncated brms at scale**: Not feasible for 17k+ observations
2. **Loading multiple Bayesian packages**: brms + rstanarm = namespace hell
3. **Weak priors with high-dimensional data**: 200+ features need strong regularization

### 💡 Key Insights

1. **Filtering ≈ Truncation**: Training on `filter(strike_count > 0)` data achieves nearly the same goal as formal zero-truncation
2. **Gamma GLM is your friend**: For positive-only counts, gamma distributions work brilliantly
3. **Gradient boosting scales**: XGBoost/LightGBM handle 17k × 200 with ease
4. **Choose tools wisely**: brms excels at small-data inference, not big-data prediction

---

## Recommended Approach

### For Stage 2 Severity Models, Use:

**✅ Gradient Boosting Models** (already implemented):
```r
# On positive-only filtered data
gamma_lgbm     # LightGBM with gamma objective
gamma_xgb      # XGBoost with gamma objective  
lgbm_log       # LightGBM on log(count+1) with smearing correction
xgb_log        # XGBoost on log(count+1) with smearing correction
```

**Why These Work**:
- ✅ Computationally efficient (seconds vs hours)
- ✅ Handle high-dimensional data naturally
- ✅ Built-in regularization
- ✅ Proven convergence
- ✅ Achieve same modeling goal as zero-truncation

### When to Revisit brms:

Consider brms if you:
1. **Reduce to < 20 key predictors** (via feature selection)
2. **Subsample to < 3k observations** (representative subset)
3. **Need full posterior distributions** (for uncertainty quantification beyond point estimates)
4. **Have 2-3 hours per fold** (for proper MCMC)
5. **Want to publish Bayesian model comparisons** (academic context)

---

## Stan Ecosystem Clarification

### The Stan Family:

- **Stan**: Core probabilistic programming language (C++)
- **brms**: Flexible R interface, generates Stan code on-the-fly
- **rstanarm**: Pre-compiled Stan models for speed, less flexible

### Both brms and rstanarm:
- ✅ Use Stan's MCMC sampler under the hood
- ✅ Are fully Bayesian
- ✅ Provide posterior distributions
- ❌ Don't scale well to 10k+ observations with 100+ features

**Timeline**:
- **brms** (2015): Newer, more flexible, actively developed
- **rstanarm** (2016): Slightly newer, more stable, pre-compiled

---

## Code Artifacts

### Modified Files
1. `helpers/helpers.R`: Updated `run_brms_sev()` to use proper truncation syntax
2. `two-stage-models.qmd`: 
   - Added 14 conflict preferences (lines 28-41)
   - Commented out rstanarm code
   - Created brms_ztp and brms_ztnb model blocks (now commented out)

### What to Remove Before Final Analysis
If completely abandoning brms:
- Lines 28-41: All brms-related conflict preferences
- Line 21: `library(brms)` 
- Lines 213-220: Commented rstanarm spec
- Lines 938-1010: brms_ztp and brms_ztnb model blocks
- `helpers/helpers.R` lines 125-160: `run_brms_sev()` function

---

## Final Recommendation

**Archive this exploration and proceed with gradient boosting models.** The computational overhead, convergence issues, and namespace conflicts are not justified for a prediction-focused task with this data size.

Save brms for:
- Small, focused datasets (< 5k observations)
- Research requiring full Bayesian inference
- Models where interpretability of posteriors is critical

For labor strike forecasting at scale: **gradient boosting dominates.** 🚀

---

## Memorable Quotes from This Session

> "who cares about the penguins dataset?" - When modeldata and datasets both exported `penguins` 🐧

> "I've never seen anything like it" - After the 11th namespace conflict

> "Is this just poor design on their part?" - A valid question about R's `library()` system

> "Finally got the model running and got all of these error messages back" - R-hat = 3.66 💀

---

**End of brms exploration. May it rest in peace.** ⚰️

*Or at least in commented-out code blocks, waiting for a smaller dataset.*

