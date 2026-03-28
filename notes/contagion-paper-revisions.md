# Contagion Paper Revision Notes

## Institutional Conditioning Section (Equation 3)

The paper currently notes (line 267) that moderation effects are "identified primarily from between-country differences in institutional context" and should be read as "descriptive of cross-national heterogeneity rather than within-country causal moderation." This is the right framing.

**Potential addition**: Consider adding a sentence explaining *why* — V-Dem indicators are slow-moving within countries, so within-country variation over time is limited and the ADM1 fixed effects absorb most of it. Identification therefore comes from cross-national differences. This makes the reasoning transparent rather than leaving readers to infer it.

Draft language:
> "Because V-Dem indicators change slowly within countries over the sample period, within-country variation in institutional context is limited; the ADM1 fixed effects absorb much of it. Identification of the moderation effects therefore relies primarily on cross-national differences in institutional context."

## Verify "nearly doubles" language for CountryShare effect

The paper says "at a one-standard-deviation increase, this represents a near-doubling of occurrence risk." But the actual SD of CountryShare = 0.047, giving a 1 SD effect of 0.047 × 0.662 = 0.031 pp, against a baseline of 1.43%. That implies a ~3× increase, not a ~2× increase — so "nearly doubles" may actually understate the effect.

**Action**: Verify the SD used when the paper was written (possibly based on a slightly different sample or construction) and update the language accordingly. The 63× within-R² comparison is unaffected. The presentation has been updated to say "more than doubles" pending final paper revision.

Also: add CountryShare to Table A1 (summary statistics) so readers can verify this calculation directly.

## Reframe Spec 2 as National Channel Characterization (not horse race)

The paper currently frames Spec 2 as a "decomposition" that pits geographic and national contagion against each other simultaneously. Revise to make clear that:

1. The horse race was already settled in Spec 1 — geographic contagion doesn't survive national controls
2. Spec 2's purpose is to **characterize the national channel** and estimate its magnitude directly
3. NeighborStrike is retained in Spec 2 as a **control** (to ensure CountryShare isn't absorbing residual geographic association), not as a co-equal channel being tested

The quantity of interest in Spec 2 is β₂ (CountryShare), not a comparison of β₁ vs. β₂. The framing should shift from "we test both channels simultaneously" to "having ruled out geographic contagion, we now ask how large the national channel is."

## CountryShare Endogeneity Defense

Reviewer question: is CountryShare endogenous (a downstream consequence of the same contagion process being estimated)?

**Defense**: The sequencing of the empirical strategy addresses this. Spec 1 (country×week FEs) already rules out geographic contagion. Given that result, CountryShare in Spec 2 cannot be biased by a geographic contagion process that has been shown not to exist. The decomposition is best understood as characterizing the national channel, remaining agnostic about *why* strikes spread nationally. The mechanism behind national co-movement (union coordination, general strike calls, policy shocks, media contagion) is a natural next step for future work.

**Remaining caveat to acknowledge**: CountryShare is a spatial lag of the outcome, which raises the Manski (1993) reflection problem in interpretation. The lagged structure (t-1:t-2) mitigates simultaneity concerns substantially.

## Add Within-R² to Tables

The presentation now reports within-R² alongside overall R² in all tables. The paper tables should do the same — the 63× comparison (within-R² = 0.063 vs. 0.001) is a key result that readers can't currently verify from the tables alone.

## Robustness Checks to Add

### Intensity of neighbor exposure as predictor
Replace the binary NeighborStrike indicator with a share or count of neighbors that struck in t-1:t-2. Tests whether the *dose* of exposure matters, not just presence. If β grows with more neighbors striking, that supports a genuine contagion mechanism over a simple threshold effect. Analogous in construction to CountryShare on the national side.

### Intensity as dependent variable
Replace binary Y_{it} with a count of strike events in region i in week t. Tests whether neighbor exposure predicts the *scale* of strike activity (intensive margin), not just onset (extensive margin). True diffusion might manifest on both margins.

**Caveat**: GDELT strike counts reflect media coverage as much as actual activity, so count-based outcomes are noisier and harder to interpret cleanly. The binary onset indicator is more robust to GDELT's measurement properties. Intensity-as-DV is conceptually interesting but would need prominent caveating. Intensity-as-predictor is the cleaner of the two robustness checks.

Comments from the APSA CPLW. 

John Alqhuist. Try International Crisis Warning? 

**Neil Ketchley comments:**



1. Egypt paper-find both geographic and national contagion; 
2. Institutional conditioning could be a different paper, not sure how it is related;
3. Nontrivial, non-random missingness... From Egypt. 2.5 thousand labor events for a single year; 
4. Is the DGP influencing the findings? There could be strong reactions to stripping out ADM1s with no events due to missingness; 
5. ADM1 is spatially large, especially for some countries (like Egypt);
6. Ronald Francesco (Kansas), criminally negletected strike database for thirty-some European countries; 
7. Modeling, do spatial modeling, even just as robustness; 
8. T1/T2... downstream effects (?)
9. Flipping signs... Need clearer explanation 
10. Michael Biggs -- frequency versus participation


**Elizabeth Parker-Magyar**

1. Is the dataset more likely to pick up on nationally salient events? Newspaper articles are covering national events... Is it because GDELT relying on primarily national as opposed to local sources. 