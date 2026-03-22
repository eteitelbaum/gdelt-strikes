# Methods Note: Fixed Effects Identification Strategy

This note identifies the key citations needed to validate the empirical strategy in
the contagion paper and flags any gaps in the current methods section. The paper uses
a two-way fixed effects linear probability model estimated with `feols` from the
`fixest` package.

---

## The Specification

**Baseline**:
$$Y_{it} = \beta \cdot \text{NeighborStrike}_{i,t-1:t-2} + \alpha_i + \gamma_{c \times t} + \varepsilon_{it}$$

- $\alpha_i$: ADM1 fixed effects (time-invariant unit heterogeneity)
- $\gamma_{c \times t}$: country-by-week fixed effects (national common shocks)
- Standard errors clustered at ADM1 level
- Estimated as LPM via OLS

Five methodological choices need citation and justification:
1. Linear probability model over logit/probit
2. Two-way fixed effects identification
3. Country-by-week FE as common shock absorber
4. Clustering standard errors at ADM1
5. `fixest` package for computation

---

## 1. Linear Probability Model (LPM)

### The choice and its justification

The paper uses LPM rather than logit/probit. Two reasons: (a) the incidental parameters
problem makes logit with many fixed effects inconsistent; (b) LPM coefficients are
directly interpretable as marginal effects.

### Key citations

**Wooldridge, Jeffrey M. 2010. *Econometric Analysis of Cross Section and Panel Data*.
2nd ed. Cambridge: MIT Press.**
Already cited in the paper (`@wooldridge2010`). The canonical textbook defense of LPM
in panel settings. Chapter 15 covers binary response models with panel data and
discusses why logit with fixed effects is problematic. Wooldridge explicitly recommends
LPM when there are many fixed effects and the goal is the average partial effect (APE).

**Angrist, Joshua D. and Jörn-Steffen Pischke. 2009. *Mostly Harmless Econometrics:
An Empiricist's Companion*. Princeton: Princeton University Press.**
Chapter 3 defends LPM as a workhorse estimator for causal inference with binary
outcomes, arguing the nonlinearity of logit/probit adds little in most applied settings
and complicates interpretation. The standard reference for applied economists using LPM.
DOI: not applicable (book). ISBN: 978-0691120355.

**Neyman, Jerzy and Elizabeth L. Scott. 1948. "Consistent Estimates Based on Partially
Consistent Observations." *Econometrica* 16(1): 1–32. DOI: 10.2307/1914288**
The original paper establishing the incidental parameters problem — as the number of
fixed effects grows, MLE estimates of the structural parameters in nonlinear models
become inconsistent. Foundational reference for why logit with many FEs is unreliable.

**Lancaster, Tony. 2000. "The Incidental Parameter Problem Since 1948." *Journal of
Econometrics* 95(2): 391–413. DOI: 10.1016/S0304-4076(99)00044-5**
The most accessible review of the incidental parameters literature. Shows that in
logit with fixed effects, the bias in the slope coefficients can be substantial even
in large samples when T is small. The standard citation for this problem in applied
work.

**Fernandez-Val, Ivan and Martin Weidner. 2016. "Individual and Time Effects in
Nonlinear Panel Models with Large N, T." *Journal of Econometrics* 192(1): 291–312.
DOI: 10.1016/j.jeconom.2015.12.007**
Extends the incidental parameters analysis to two-way FE nonlinear models (individual
AND time effects). Shows bias remains even with large T in nonlinear models — but
crucially, also **proposes analytical and jackknife bias corrections** that make
bias-corrected logit feasible. Implemented in R via the `alpaca` package. This paper
therefore does double duty: it establishes the problem AND offers the solution.

### State of the literature

The literature has moved beyond simply saying "use LPM because logit is biased."
Bias-corrected logit estimators (Fernandez-Val & Weidner 2016) are now available and
implemented. However, LPM remains the standard and defensible choice for several
reasons:

1. **APE equivalence**: For causal inference we care about the average partial effect
   (APE) — the change in probability for a one-unit change in treatment. Wooldridge
   and Angrist & Pischke argue LPM estimates the APE directly without needing to
   integrate over the distribution of fixed effects. Bias-corrected logit estimates
   the same quantity with more complexity.

2. **Practical equivalence in large panels with rare outcomes**: At a 1.4% onset rate,
   predicted probabilities are far from 0 or 1 for most observations, which is
   precisely where LPM and logit agree most. The nonlinearity of logit only materially
   affects estimates when predicted probabilities are near the boundary.

3. **Computational scale**: With 181 countries × hundreds of ADM1 units × 500+ weeks
   and country×week FEs, even `alpaca` may struggle with the dimensionality.

4. **Disciplinary convention**: Political science panels routinely use LPM with
   clustered standard errors. Econometrics journals would push harder for the
   correction.

### Recommended approach

Use LPM as the main specification. Add a robustness check with bias-corrected logit
using the `alpaca` package and report that results are substantively identical. Cite
both Fernandez-Val & Weidner (2016) and Wooldridge (2010). This preempts the reviewer
concern entirely without complicating the main presentation.

```r
# Bias-corrected logit robustness check
library(alpaca)
m_logit_corrected <- feglm(
  strike_onset ~ neighbor_strike_within_t1_t2 | gid_1 + country_week,
  data   = analysis,
  family = binomial()
)
# alpaca applies the Fernandez-Val & Weidner bias correction automatically
```

**Hahn, Jinyong and Whitney Newey. 2004. "Jackknife and Analytical Bias Reduction for
Nonlinear Panel Models." *Econometrica* 72(4): 1295–1319. DOI: 10.1111/j.1468-0262.2004.00532.x**
Companion paper developing the jackknife approach to bias correction for nonlinear
panel models. Cited alongside Fernandez-Val & Weidner for completeness.

### What the paper currently says

The paper cites only Wooldridge (2010). Should also cite Angrist & Pischke (2009) for
the applied defense of LPM, Lancaster (2000) for the incidental parameters problem,
and Fernandez-Val & Weidner (2016) both to acknowledge the problem in two-way FE
settings and to motivate the bias-corrected logit robustness check.

---

## 2. Two-Way Fixed Effects Identification

### The logic

ADM1 FEs absorb time-invariant unit characteristics (baseline strike propensity,
industrial composition, geography). Country-by-week FEs absorb all within-country
common weekly shocks. Identification comes from within-unit, within-country-week
variation in neighbor exposure.

### Key citations

**Mundlak, Yair. 1978. "On the Pooling of Time Series and Cross Section Data."
*Econometrica* 46(1): 69–85. DOI: 10.2307/1913646**
Foundational paper establishing the fixed effects estimator as the appropriate
approach when unit-level heterogeneity is correlated with the regressors. The
standard textbook citation for why FE is preferred over random effects in this setting.

**Chamberlain, Gary. 1984. "Panel Data." In *Handbook of Econometrics*, vol. 2, eds.
Z. Griliches and M. Intriligator, pp. 1247–1318. Amsterdam: North-Holland.**
The most thorough treatment of FE identification in panel data. Establishes the
within-estimator and its properties. Standard citation alongside Mundlak for the FE
approach.

**Hsiao, Cheng. 2003. *Analysis of Panel Data*. 2nd ed. Cambridge: Cambridge University
Press. DOI: 10.1017/CBO9780511754203**
The most comprehensive textbook reference for panel data methods. Covers two-way FE,
identification assumptions, and properties of the within estimator. Good for citing
the two-way FE approach specifically.

---

## 3. Country-by-Week Fixed Effects as Common Shock Absorber

### The logic

The country-by-week FE is the key identifying restriction. It absorbs any factor that
varies at the country-week level: general strikes, political events, macroeconomic
shocks, legal changes, national media cycles. This is a saturated approach — rather
than parametrically controlling for national conditions, we include a dummy for every
country-week cell. The approach is common in the international trade literature.

### Key citations

**Baier, Scott L. and Jeffrey H. Bergstrand. 2007. "Do Free Trade Agreements Actually
Increase Members' International Trade?" *Journal of International Economics* 71(1):
72–95. DOI: 10.1016/j.jinteco.2006.02.005**
Popularized the use of country-pair and time fixed effects (and ultimately
country×year FEs) in the gravity model of trade to absorb multilateral resistance
terms. The trade literature is where country×time FEs became standard practice. A
useful methodological precedent.

**Head, Keith and Thierry Mayer. 2014. "Gravity Equations: Workhorse, Toolkit, and
Cookbook." In *Handbook of International Economics*, vol. 4, eds. G. Gopinath,
E. Helpman, and K. Rogoff. Amsterdam: Elsevier. DOI: 10.1016/B978-0-444-54314-1.00003-3**
The definitive review of gravity models and their identification strategies, including
the use of country×time FEs to absorb unobservable common shocks. The standard
methodological reference for this approach.

**What the conflict contagion papers do**: Neither Buhaug & Gleditsch (2008) nor
Gleditsch & Rivera (2017) uses country×time fixed effects. Both use logit with
parametric controls (democracy, GDP per capita, population size, time dependence
variables). Buhaug & Gleditsch (2008, p. 227) discusses country FEs explicitly as
a robustness check, noting they are "generally skeptical of the merits of fixed
effects analysis for binary dependent variables" because it excludes all countries
without within-unit variation. They do run the country FE check and find their main
result holds. Gleditsch & Rivera (2017) does not include unit FEs at all.

**Implication**: The conflict literature does not provide a precedent for country×time
FEs. Our approach is actually *more demanding* than the conflict literature standard —
we absorb all country-week-level variation with a saturated dummy rather than relying
on parametric controls. The closest precedent remains the gravity/trade literature.
Stick with Baier & Bergstrand and Head & Mayer as citations, and note in the text
that saturated time×unit interaction FEs are the standard approach in that literature
for absorbing unobservable common shocks.

---

## 4. Clustering Standard Errors

### The logic

Standard errors are clustered at the ADM1 level to account for serial correlation in
the error term within units over time. ADM1 is the unit of observation, so clustering
at this level is the natural choice.

### Key citations

**Bertrand, Marianne, Esther Duflo, and Sendhil Mullainathan. 2004. "How Much Should
We Trust Differences-in-Differences Estimates?" *Quarterly Journal of Economics*
119(1): 249–275. DOI: 10.1162/003355304772839588**
The paper that established clustering as standard practice in panel difference-in-
differences settings. Shows that ignoring within-unit serial correlation severely
understates standard errors. Even though the paper focuses on DiD, it is the standard
citation for why we cluster in panel regression.

**Cameron, A. Colin and Douglas L. Miller. 2015. "A Practitioner's Guide to Cluster-
Robust Inference." *Journal of Human Resources* 50(2): 317–372.
DOI: 10.3368/jhr.50.2.317**
The most comprehensive practical guide to cluster-robust inference. Covers when to
cluster, at what level, and what to do when there are few clusters. Addresses the
ADM1 clustering choice directly (cluster at the level of treatment assignment). Should
be cited alongside Bertrand et al.

### Potential issue: number of clusters

With 181 countries × many ADM1 units, we have a large number of clusters — not a
problem. But within any single country, if there are few ADM1 units, cluster-robust
inference may be unreliable for those country-specific tests. Cameron & Miller (2015)
discuss the "few clusters" problem. Worth noting if the number of clusters per country
varies substantially.

---

## 5. The `fixest` Package

**Berge, Laurent. 2018. "Efficient Estimation of Maximum Likelihood Models with
Multiple Fixed-Effects: The R Package FENmlm." CREA Discussion Papers.**

**Berge, Laurent. 2021. "Efficient Estimation of Maximum Likelihood Models with
Multiple Fixed-Effects: The R Package fixest." CRAN package vignette.**

The `fixest` package documentation should be cited when using `feols()`. The package
implements the Mundlak within-estimator with multiple high-dimensional fixed effects
using the alternating projections algorithm, enabling estimation with country×week
FEs (which can be very large dimensional). Check the current CRAN citation:

```r
citation("fixest")
```

---

## 6. Potential Gaps and Additions

### Spatial econometrics as alternative

The paper uses a reduced-form FE approach rather than an explicit spatial lag model
(SAR/SLM). Reviewers may ask why. Key references if this needs to be addressed:

**Anselin, Luc. 1988. *Spatial Econometrics: Methods and Models*. Dordrecht: Kluwer.**
The foundational spatial econometrics reference. The spatial autoregressive (SAR)
model is the standard approach in that literature. Worth citing to explain why we
prefer the FE approach (no need to specify the weight matrix functional form; FEs
absorb both spatial and temporal dependence at the national level).

**LeSage, James P. and R. Kelley Pace. 2009. *Introduction to Spatial Econometrics*.
Boca Raton: CRC Press.**
More recent reference. Arezki et al. (2024) use this framework — could compare and
contrast our approach with theirs.

### Why not a spatial lag model? (Anticipated reviewer question)

Reviewers familiar with spatial econometrics may ask why we use a reduced-form FE
approach rather than an explicit spatial lag (SAR) model. Here is the response.

A spatial lag model (SAR — spatial autoregressive model) specifies the outcome as a
function of the weighted average of *contemporaneous* outcomes in neighboring units:

$$Y_{it} = \rho \cdot WY_{it} + X_{it}\beta + \varepsilon_{it}$$

where $W$ is a spatial weights matrix and $\rho$ is the spatial autocorrelation
parameter estimated as part of the system. Our approach instead uses a constructed
lagged regressor (neighbor strike onset in $t-1$ and $t-2$) in a standard FE
regression. The differences are consequential:

**1. Simultaneity**: The SAR model requires the researcher to solve the simultaneity
problem — my outcome and my neighbor's outcome are determined at the same time,
making $WY$ endogenous. This requires instrumental variables or structural assumptions.
Our lagged treatment ($t-1$, $t-2$) avoids simultaneity entirely: the neighbor's
past behavior is predetermined with respect to this period's outcome.

**2. Weight matrix specification**: SAR requires the researcher to specify the
functional form of $W$ — binary contiguity, inverse distance, trade flows, etc. The
results are sensitive to this choice (Anselin 1988; LeSage & Pace 2009). We sidestep
this by using a simple binary contiguity indicator (shared border) as the treatment
variable, which requires no assumptions about the functional form of spatial decay.

**3. National confounders**: In the SAR framework, national common shocks must be
modeled parametrically. Our country×week FEs provide a saturated, assumption-free
absorber of all country-week-level confounders — a much weaker identification
requirement.

**4. Interpretability**: The SAR $\rho$ is a structural contagion parameter that
includes both direct and indirect (multiplier) effects. Our $\beta$ is a reduced-form
predictive effect: does past neighbor activity predict my onset, conditional on shared
national shocks? This is a more conservative and more interpretable quantity for our
research question.

The trade-off: the SAR model, when correctly specified, is more efficient and
provides a structural interpretation. Our approach is more robust to misspecification
of the spatial process and to national confounding. Given the scale of our panel
(181 countries, hundreds of ADM1 units each, weekly frequency) and the severity of
national common shock confounding documented in the results, the FE approach is the
appropriate choice.

**Key references for this comparison**:
- Anselin, Luc. 1988. *Spatial Econometrics: Methods and Models*. Dordrecht: Kluwer.
- LeSage, James P. and R. Kelley Pace. 2009. *Introduction to Spatial Econometrics*.
  Boca Raton: CRC Press.

**Arezki, Rabah, Alou Adesse Dama, Simeon Djankov, and Ha Nguyen. 2024.
"Contagious Protests." *Empirical Economics* 66(6): 2397–2434.**
The closest existing analog to this paper at the cross-national level. Uses ACLED
protest data + Dow Jones news media coverage across 200 countries, 2000–2020, at
monthly frequency. Estimates an autoregressive spatial (SAR) model with
geographic distance weights between countries. Finds strong cross-border protest
contagion, with social media penetration as the key amplifier. Key differences
from our design: (1) spatial unit is the country, not ADM1; (2) the SAR framework
cannot cleanly separate national common shocks from geographic diffusion — our
TWFE absorbs all country-week variation with a saturated fixed effect rather than
relying on a parametric spatial model; (3) their lagged DV/spatial lag approach
requires structural assumptions about simultaneity that our predetermined neighbor
treatment avoids. **Use in methods section to contrast SAR and TWFE approaches,
motivating our choice on identification grounds.**

---

### Subnational spatial panel precedents

**Aidt, Toke S. and Gabriel Leon-Ablan. 2022. "The Interaction of Structural
Factors and Diffusion in Social Unrest: Evidence from the Swing Riots."
*British Journal of Political Science* 52(2): 869–885. DOI: 10.1017/s0007123420000873**
Uses parish-level panel data on the English Swing Riots of 1830–31 to disentangle
structural causes from spatial diffusion. Constructs a spatial lag variable at the
parish level and estimates its effect alongside structural predictors. Finds a
positive and significant spatial lag — riots cluster geographically — and shows
that diffusion multiplied the effect of local structural factors by approximately
3.15. **Methodological precedent for the subnational spatial panel approach: a
subnational unit × time panel with a geographic neighbor treatment variable.
Use in the methods/data section when describing neighbor variable construction.**
Note: their positive geographic finding for historical English riots contrasts
with our null finding for modern strikes — worth flagging in the discussion.

**Aidt, Toke S., Gabriel Leon-Ablan, and Max Satchell. 2022. "The Social Dynamics
of Collective Action: Evidence from the Diffusion of the Swing Riots, 1830–1831."
*Journal of Politics* 84(1): 209–225. DOI: 10.1086/714784**
Companion piece developing explicit diffusion mechanisms for the same Swing Riots
data: information networks, local organizers, and repression. Finds contagion
travels through personal and trade networks rather than mass media, and magnifies
structural effects by a factor of 2.65. **Use alongside the BJPS paper as a
pair of methodological precedents for subnational spatial panel identification of
collective action diffusion.**

### Parallel trends / common trends

The country×week FE approach implicitly assumes that in the absence of neighbor
exposure, all ADM1 units in the same country-week would have the same counterfactual
strike propensity (up to unit fixed effects). This is a strong assumption worth
acknowledging. Relevant literature:

**Callaway, Brantly and Pedro H.C. Sant'Anna. 2021. "Difference-in-Differences with
Multiple Time Periods." *Journal of Econometrics* 225(2): 200–230.
DOI: 10.1016/j.jeconom.2020.12.001**
Recent DiD literature on heterogeneous treatment effects and parallel trends. Less
directly applicable but relevant if reviewers push on identification assumptions.

### Inference with spatial dependence

Even after controlling for country×week FEs, spatial dependence in the error term
across nearby ADM1 units could lead to underestimated standard errors. ADM1 clustering
handles within-unit temporal dependence but not cross-unit spatial dependence.

**Conley, Timothy G. 1999. "GMM Estimation with Cross Sectional Dependence."
*Journal of Econometrics* 92(1): 1–45. DOI: 10.1016/S0304-4076(98)00084-0**
Standard approach for spatial HAC standard errors. Could be implemented as a
robustness check using the `conleySE` package in R. Probably not necessary for the
main text but worth noting as a potential reviewer concern.

---

## Priority Citations to Add to the Paper

| Citation | Why needed | Priority |
|---|---|---|
| Angrist & Pischke 2009 | LPM defense | High |
| Lancaster 2000 | Incidental parameters | High |
| Bertrand, Duflo & Mullainathan 2004 | Clustering | High |
| Cameron & Miller 2015 | Clustering guide | Medium |
| Berge / fixest citation | Package citation | Medium |
| Fernandez-Val & Weidner 2016 | Two-way FE binary outcomes | Medium |
| Anselin 1988 or LeSage & Pace 2009 | Address spatial econometrics alternative | Low |
| Mundlak 1978 | FE identification | Low (standard) |
