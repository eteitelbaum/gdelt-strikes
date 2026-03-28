# Speaker Notes — Contagion Presentation

## Figure 1: Strike Waves Are Real

The line chart shows weekly ADM1 strike activity from 2015–2025. The spikiness is the key thing to point out — strike activity doesn't unfold smoothly over time but clusters into discrete bursts, which is the visual signature of wave-like behavior. Multiple regions striking in the same week produces those tall spikes, and the LOESS trend (red line) shows the longer-run undulation of activity rising and falling in cycles. If strikes were purely independent random events, you'd expect a much flatter, more uniform distribution over time.

The bar chart shows strikes also cluster in space — regions with a striking neighbor are 3.5× more likely to strike (4.9% vs. 1.4% onset rate).

Together they set up the central question: we see temporal clustering AND spatial clustering. The natural interpretation is contagion. But is the spatial clustering actually geographic (neighbors spreading to neighbors), or is it just that the temporal waves hit all regions in a country simultaneously because of national-level shocks? That's what the rest of the paper answers.

## Baseline Specification (Equation 1)

Our first specification is a two-way fixed effects model. It models strike occurrence (1/0) as a function of a neighboring strike in the previous two weeks (1/0) controlling for ADM1 fixed effects and country-week fixed effects. The key thing is that the country-week fixed effects absorb all variation at the national level, meaning that we don't have to specify which country-level dynamics matter, and it removes the most obvious source of spurious correlation — the possibility that neighboring regions strike together simply because they share the same national context. This does not rule out regional confounders but it allows us to ask whether any geographic association remains once national dynamics are absorbed.

## Decomposition (Equation 2)

Our second specification decomposes the national and regional contagion effects. We remove the country-week fixed effects while retaining global week and ADM1 effects, and we add a CountryShare variable measuring the share of ADM1s in the same country experiencing a strike in the previous two weeks. By replacing the country-week FEs with an explicit measure of national strike activity, we can now estimate the national channel directly and assess its magnitude. The tradeoff is that the regional contagion effect is not fully identified, but if the first model shows us that regional diffusion is not relevant then we can be fairly confident that CountryShare is not contaminated by regional diffusion, while retaining β₁ as a control for any residual geographic association. If national contagion is driving the apparent geographic clustering, we expect β₂ to be large and positive while β₁ remains near zero.

## Results: No Evidence of Geographic Contagion (Table 2)

In Table 2 we see that the effect of neighbor strikes for the main specification (t-1, t-2) is not statistically significant, suggesting that once we fully control for national shocks, regional dynamics have no explanatory power. We also test separately for t-1 and t-2 periods and find a small negative effect for t-1, suggesting a possible strategic delay dynamic whereby workers in one region are perhaps holding off on striking based on seeing how strikes in neighboring regions play out. Notably, the pooled t-1/t-2 result is essentially zero, which is consistent with this interpretation — a negative effect at t-1 being offset by a positive effect at t-2 as workers act on the information gained from observing neighboring strikes. This pattern is intriguing but would require further investigation to distinguish from sampling noise.

## Results: National Contagion Dominates (Table 3)

Table 3 presents the decomposition results. The key numbers to convey:

**The coefficient (β₂ = 0.662)**: This is a linear probability model coefficient. A 1-unit increase in CountryShare — meaning all other regions in the country strike — raises P(strike) by 66.2 percentage points. But CountryShare never moves by a full unit; its SD is about 0.047 (roughly 5 percentage points). So a typical 1 SD move raises strike probability by 0.047 × 0.662 ≈ 3 percentage points, on a baseline of 1.4% — more than doubling it.

**The within-R² comparison**: The overall R² in the table includes the fixed effects' contribution and is not the relevant comparison. What matters is the within-R² — how much each variable explains of the residual variation after fixed effects are removed. CountryShare alone: within-R² = 0.063 (6.3%). NeighborStrike alone: within-R² = 0.001 (0.1%). Ratio: 63×.

**The narrative**: The raw data shows a 3.5× higher strike rate when a neighbor strikes (4.9% vs. 1.4% in Figure 1). That association fully disappears once national dynamics are controlled (Table 2). Table 3 then shows why — national co-movement explains 63 times more of the within-unit variation than geographic exposure does. The geographic clustering in the raw data was entirely a reflection of national strike waves, not cross-border transmission.

## Results: Institutions Shape the Geography of National Waves (Table 4) — if time

Table 4 interacts both the neighbor strike indicator and CountryShare with three V-Dem institutional indicators. The main CountryShare coefficient stays large and stable across all columns (~0.65), confirming the national channel is robust to institutional controls. The interesting action is in the interactions with the neighbor strike indicator: freedom of association strengthens geographic spillover (Neighbor × Association = +0.005 in col. 2, +0.016 in the joint model), while freedom of expression dampens it in the joint specification (Neighbor × Expression = −0.012). Repression has no significant effect on geographic transmission. The interpretation: where workers are free to organize collectively, geographic proximity matters more for spreading strike activity — unions and labor networks can act as transmission belts across borders. But remember, since we've already shown the geographic channel is near zero on average, these interactions are best read as describing how institutions shape the spatial distribution of nationally-driven waves rather than amplifying true cross-border contagion.
