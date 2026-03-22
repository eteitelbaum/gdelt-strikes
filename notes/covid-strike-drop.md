# COVID-Era Strike Drop: Analysis Plan

The weekly strike prevalence plot shows a clear drop in strike activity starting around
2020 and a persistently lower level through the post-COVID period (~2021–2025 compared
to 2015–2019). This note outlines approaches for analyzing the drop formally.

---

## Two Competing Interpretations

Before analyzing, the key question is whether this is **real** or **artifact**:

1. **Real**: COVID lockdowns suppressed strike activity — workers couldn't assemble,
   plants shut down, job insecurity made workers risk-averse about collective action.
   Post-COVID, some suppression may have persisted due to changed work arrangements,
   weakened unions, or labor market restructuring.

2. **Artifact**: GDELT coverage dropped because news media pivoted to pandemic coverage,
   systematically undercounting strikes that did occur. GDELT's media-derived counts
   are sensitive to editorial attention, and COVID dominated global news cycles from
   March 2020 onward.

The two interpretations have different implications for the contagion paper:
- If real: COVID is a substantively interesting moderator; the post-COVID period may
  have structurally different contagion dynamics
- If artifact: the post-COVID data are less reliable and may need to be flagged as a
  scope condition or handled with a robustness check (e.g., sample restricted to
  pre-2020)

---

## Approach 1: Interrupted Time Series (ITS)

**What it does**: Formally estimates the magnitude of the level shift at COVID and
whether the trend changed.

**Model**:
```r
library(tidyverse)

panel_weekly <- panel |>
  group_by(week_start) |>
  summarise(n_onset = sum(strike_onset), .groups = "drop") |>
  mutate(
    time       = as.numeric(week_start - min(week_start)) / 7,  # weeks since start
    post_covid = as.integer(week_start >= as.Date("2020-03-01")),
    time_post  = time * post_covid  # interaction: slope change after COVID
  )

m_its <- lm(n_onset ~ time + post_covid + time_post, data = panel_weekly)
summary(m_its)
```

**Interpretation**:
- `post_covid` coefficient: immediate level shift at March 2020
- `time_post` coefficient: change in slope after COVID (trend flattening or steepening)
- `time` coefficient: pre-COVID trend

**Visualization**:
```r
panel_weekly |>
  mutate(fitted = fitted(m_its)) |>
  ggplot(aes(week_start)) +
  geom_line(aes(y = n_onset), alpha = 0.4) +
  geom_line(aes(y = fitted), color = "red", linewidth = 1) +
  geom_vline(xintercept = as.Date("2020-03-01"), linetype = "dashed") +
  labs(title = "Interrupted Time Series: Strike Onset", x = NULL, y = "Weekly onsets")
```

---

## Approach 2: Bai-Perron Structural Break Test

**What it does**: Lets the data identify when break(s) occurred, rather than imposing
March 2020. Could reveal whether the break aligns with COVID, an earlier GDELT
methodology change, or another event.

```r
library(strucchange)

# Fit breakpoint model
bp <- breakpoints(n_onset ~ time, data = panel_weekly, h = 0.1)
summary(bp)
plot(bp)

# Confidence intervals for break dates
confint(bp)

# Compare: is the break at COVID or elsewhere?
```

**Why this matters**: If the break date is NOT March 2020 (e.g., it's 2018 or 2022),
the COVID interpretation is weakened and a GDELT methodology change becomes more
plausible. The `strucchange` package also supports multiple break detection.

---

## Approach 3: Country Heterogeneity (Artifact vs. Real Diagnostic)

**Logic**: If the drop is a GDELT coverage artifact, it should be fairly uniform across
countries — all got less coverage. If it's real (COVID suppressed strikes), the drop
should be concentrated in countries with stricter lockdowns.

```r
library(arrow)
library(tidyverse)

# Compute pre/post ratio by country
country_drop <- panel |>
  mutate(post_covid = week_start >= as.Date("2020-03-01")) |>
  group_by(iso3, post_covid) |>
  summarise(onset_rate = mean(strike_onset), .groups = "drop") |>
  pivot_wider(names_from = post_covid, values_from = onset_rate,
              names_prefix = "rate_") |>
  rename(pre = rate_FALSE, post = rate_TRUE) |>
  mutate(ratio = post / pre) |>
  filter(!is.na(pre), !is.na(post), pre > 0)

# Merge with Oxford COVID Stringency Index
# Data: https://github.com/OxCGRT/covid-policy-tracker
# Variable: StringencyIndex_Average (country-level average during 2020-2021)

# Correlate: did stricter lockdowns -> bigger drop in strikes?
# If yes: real suppression effect
# If no correlation: more consistent with coverage artifact
```

**Oxford COVID Stringency Index** is freely available at the OxCGRT GitHub. A positive
correlation between stringency and strike drop magnitude would support the "real"
interpretation.

---

## Approach 4: Simple Pre/Post Comparison

Quickest descriptive check — compute mean weekly onset rate before and after March 2020:

```r
panel |>
  mutate(period = if_else(week_start < as.Date("2020-03-01"), "Pre-COVID", "Post-COVID")) |>
  group_by(period) |>
  summarise(
    onset_rate   = mean(strike_onset),
    n_obs        = n(),
    sd_onset     = sd(strike_onset)
  )
```

Also useful: break the post period into COVID (2020–2021) vs. post-COVID recovery
(2022–2025) to see if levels partially recovered.

```r
panel |>
  mutate(period = case_when(
    week_start < as.Date("2020-03-01") ~ "Pre-COVID (2015-2020)",
    week_start < as.Date("2022-01-01") ~ "COVID (2020-2022)",
    TRUE                               ~ "Post-COVID (2022-2025)"
  )) |>
  group_by(period) |>
  summarise(onset_rate = mean(strike_onset), n = n())
```

---

## Approach 5: Robustness Check for the Contagion Paper

Even if we don't fully analyze the COVID drop, we should check whether the contagion
paper's main results hold in the pre-COVID sample only. If the null geographic neighbor
effect is robust to excluding the COVID and post-COVID period (when onset rates are
lower and data quality may differ), that strengthens confidence in the findings.

```r
# Add to modeling notebook as robustness check
m_pre_covid <- feols(
  strike_onset ~ neighbor_strike_within_t1_t2 | gid_1 + country_week,
  data    = analysis |> filter(week_start < as.Date("2020-03-01")),
  cluster = ~gid_1
)
```

---

## Recommended Sequence

1. **Start with Approach 4** (simple pre/post means) — 10 minutes, tells you the magnitude
2. **Run Approach 2** (Bai-Perron) — identifies break date without imposing assumptions
3. **Run Approach 1** (ITS) — formal model of the level shift
4. **Run Approach 3** (country heterogeneity + Oxford stringency) — artifact vs. real
5. **Run Approach 5** (pre-COVID robustness) — needed for the contagion paper regardless

---

## Potential Outputs

- A figure showing the ITS fit with the counterfactual (what would the trend have been
  without COVID?) — good for a paper or appendix
- A scatter plot of country-level strike drop vs. COVID stringency — diagnostic figure
- A robustness table showing main results hold in pre-COVID sample — appendix item

---

---

## Future Paper: COVID, Sectoral Recomposition, and Strike Geography

This is a separate paper idea, not an addition to the contagion paper. The core
argument: COVID produced a **mixed but structurally important shock** to organized
labor — strengthening some forms of worker power (public sector, logistics, healthcare,
services) while weakening others (traditional manufacturing unions, gig/platform
workers). The interesting question is whether these effects are cyclical or durable,
and how they map onto geography.

### A critical measurement note

The plot showing the post-COVID drop counts **number of ADM1 regions with more than
one strike** — not total strike events. This distinction matters enormously for
interpretation and should be the first thing addressed before drawing any conclusions
about the drop.

Two series could tell very different stories:

- **Total strike events (count)**: Did the absolute number of strikes fall, rise, or
  stay flat post-COVID?
- **Number of active regions (breadth)**: Did strikes become more geographically
  concentrated — fewer regions experiencing strikes, but possibly more strikes within
  those regions?

If total counts held up but active regions declined, the post-COVID picture is one of
**geographic concentration**: strikes becoming more intense in certain hubs (logistics
corridors, major cities, public sector strongholds) while disappearing from the
periphery. This would be consistent with the sectoral recomposition story — logistics
and service-sector strikes are spatially concentrated, while manufacturing strikes were
geographically diffuse.

This could produce a very complex picture:
- Some regions seeing *more* strikes post-COVID, concentrated in specific sectors
- Many regions seeing *fewer or zero* strikes as traditional industries decline
- The aggregate "drop" being an artifact of geographic concentration, not a true
  collapse in labor conflict

**First diagnostic**: Plot both series side by side — total GDELT strike events per
week vs. number of active ADM1 regions per week. If they diverge post-COVID, geographic
concentration is the story. If they move together, the drop is real in both dimensions.

```r
panel |>
  group_by(week_start) |>
  summarise(
    n_regions   = sum(strike_onset > 0),
    n_regions_1plus = sum(strike_onset > 1),  # current plot
    total_events = sum(n_strikes, na.rm = TRUE)  # raw event count (if available)
  ) |>
  pivot_longer(-week_start) |>
  ggplot(aes(week_start, value, color = name)) +
  geom_line(alpha = 0.5) +
  geom_smooth(se = FALSE) +
  facet_wrap(~name, scales = "free_y")
```

---

### The core puzzle

The post-COVID drop in GDELT strike frequency is actually a puzzle from the standpoint
of canonical strike theory. The classic pro-cyclical view — Rees (1952), Hibbs (1976),
and the bargaining power literature more broadly — predicts that tight labor markets
*increase* strike activity: workers have better outside options, lower costs of
withholding labor, and more leverage over employers. The post-2020 recovery produced
exactly these conditions (historically low unemployment, high quit rates, surging
vacancies), yet the GDELT series shows *fewer* strikes, not more.

This creates a genuine empirical puzzle with several candidate explanations:

1. **Measurement artifact**: The drop is not real — COVID disrupted GDELT's media
   coverage pipeline and the post-pandemic recovery in strike activity is being
   undercounted. If true, the pro-cyclical prediction holds but we can't see it.

2. **COVID suppression with slow recovery**: The immediate shock (lockdowns, furloughs,
   job insecurity) suppressed strikes, and the recovery in strike activity is lagged —
   we may only be in the early stages of the pro-cyclical uptick the theory predicts.

3. **Structural transformation of conflict**: Tight labor markets post-COVID manifested
   in *different forms* of worker leverage — mass quits (the "Great Resignation"),
   organizing campaigns, regulatory battles — rather than traditional strike action.
   If the form of collective action shifted, GDELT's strike coding would miss it.

4. **Sectoral recomposition**: The tight labor market was concentrated in sectors
   (logistics, services, gig) that historically have low strike rates and weak union
   infrastructure, while traditional strike-prone sectors (manufacturing) remained
   weak. Aggregate tightness masks sectoral heterogeneity.

The puzzle is worth stating explicitly in any paper that uses this data — it is either
a scope condition (GDELT captures a selected subset of labor conflict) or a substantive
finding about the changing forms of worker power.

### Core mechanisms

1. **Labor market tightening → short-run leverage**: Tight post-2020 labor markets
   increased workers' outside options and willingness to strike (classic bargaining
   power channel — likely cyclical).

2. **"Essential worker" framing → legitimacy shock**: Logistics, healthcare, food
   supply workers gained moral and political salience; public support for unions hit
   multi-decade highs. Legitimacy is a durable input into organizing success.

3. **Workplace transformation**: Remote work (harder to organize, but new conflict
   margins around return-to-office); platform/gig expansion (pushed labor toward
   regulatory strategies — AB5-style classification battles).

4. **Sectoral divergence** (key empirical claim):
   - *Strengthened*: public sector (teachers, nurses), logistics (Amazon, warehousing),
     service sector (Starbucks, hospitality)
   - *Weakened/stagnant*: traditional manufacturing, small private firms

5. **Organizing model shift**: More worker-led, decentralized campaigns; less reliance
   on union bureaucracies; heavy use of digital tools and public pressure. High
   visibility but fragile — hard to convert into durable contracts.

6. **Inflation shock (2022–23)**: Real wage erosion → more militancy, but harder
   bargaining environments.

### The Polanyian question

Is this a double-movement moment (re-embedding labor protections) or a cyclical spike
in contention without institutionalization? Likely the latter unless policy catches up
(PRO Act failed; NLRB more active but enforcement constrained).

### Why sector coding matters

The sectoral divergence argument is the most directly testable claim — but requires
knowing *which sector* each GDELT strike event belongs to. GDELT does not code this.

**Proposed pipeline**: Use the same few-shot LLM classification approach developed for
geo-validation and URL relevance filtering — classify each GDELT strike event by sector
based on article URL and title content. The existing infrastructure (OpenAI batch API,
few-shot prompts, validation logic) is directly reusable.

Candidate sector taxonomy (to be refined):
- Public sector (government, education, healthcare)
- Logistics and warehousing
- Manufacturing
- Services (retail, hospitality, food)
- Platform/gig
- Mining and energy
- Transport (rail, aviation, ports)
- Other / unclassified

With sector labels, the analysis could cross:
- **Sector × Oxford COVID stringency** → which sectors were more suppressed by lockdowns?
- **Sector × region** → does post-COVID strike geography shift toward logistics/service
  hubs and away from traditional manufacturing regions?
- **Sector × contagion** → do strikes spread differently within sectors vs. across
  sectors? Is national wave dynamics stronger within-sector?

### Data requirements

- Sector classifier: LLM few-shot on GDELT URL + title (same pipeline as url_classifier)
- Regional industrial composition: ILO employment by sector × country (or World Bank)
- Oxford COVID Stringency Index: country-level average during 2020–2021
- Existing contagion panel: already has ADM1-week structure, just needs sector label

### Note on scope

This is a **separate paper** from the contagion analysis. The contagion paper has a
clean identification strategy and argument that would be diluted by adding COVID/sector
complexity. The sectoral recomposition question is big enough to stand alone.

---

## Resources

- Oxford COVID Stringency Index: https://github.com/OxCGRT/covid-policy-tracker
- `strucchange` R package: Zeileis et al. (2002), JSS
- Bai & Perron (1998, 2003) on structural break estimation: *Econometrica* 66(1);
  *Journal of Applied Econometrics* 18(1)
