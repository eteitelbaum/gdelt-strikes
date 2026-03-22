# Revisiting Hibbs and the Political Economy of Strikes with Contemporary Data

## Motivation

The canonical cross-national literature on strike activity — Hibbs (1976), Rees (1952),
Shorter & Tilly (1974), Franzosi (1995) — was built on data from advanced industrial
democracies in the mid-20th century, a period characterized by high union density,
centralized collective bargaining, and manufacturing-dominated economies. The GDELT
panel (2015–2025, 181 countries, ADM1-week resolution) offers an opportunity to
revisit these classic arguments with contemporary global data at unprecedented scale
and granularity. Do the old regularities still hold?

---

## The Classic Arguments to Test

### 1. Pro-cyclicality (Hibbs 1976; Rees 1952)
**Classic claim**: Strike frequency rises in economic booms (workers have leverage,
outside options improve) and falls in recessions (job insecurity suppresses militancy).

**Contemporary puzzle**: The post-COVID period offers a hard test. The 2020–2022
recovery produced the tightest labor markets in decades, yet GDELT shows *fewer*
strike-active regions, not more. Does the pro-cyclical relationship still hold, or
has the form of labor conflict shifted (quits, organizing campaigns, regulatory
battles) in ways GDELT doesn't capture?

**How to test**: Merge GDELT onset rates with quarterly GDP growth and unemployment
by country. Run country-FE panel regression of onset rate on lagged GDP growth and
unemployment. Compare coefficients across pre-2020 and post-2020 subsamples.

### 2. Left government suppression (Hibbs 1976)
**Classic claim**: Left-party governments suppress strikes via political exchange —
unions restrain militancy when political allies hold power.

**Contemporary complications**:
- Union density has collapsed in many countries since the 1970s, weakening the
  political exchange mechanism
- The left-labor alliance has frayed in many democracies (centrist "third way" parties)
- In some countries the relationship may have reversed (populist left governments
  may *encourage* labor militancy)

**How to test**: Merge with V-Party or ParlGov data on government ideology. Test
whether left executive is associated with lower onset rates in the GDELT panel.
Allow for heterogeneity by union density (ILO data) — does suppression only occur
where union-party ties remain strong?

### 3. Corporatism suppresses strikes (Hibbs 1976; Cameron 1984)
**Classic claim**: Centralized union confederations and coordinated wage bargaining
institutions (corporatism) suppress strikes by internalizing conflict.

**Contemporary relevance**: Corporatist arrangements have eroded in many countries
(UK, US, parts of Southern Europe) but remain strong in Scandinavia and parts of
Central Europe. Does the cross-national variation in corporatism still predict
strike rates in the contemporary period?

**How to test**: Merge with ICTWSS database (union density, bargaining coordination,
collective bargaining coverage) or Varieties of Capitalism indicators. Country-level
regression of mean onset rate on corporatism measures.

### 4. Business cycle effects (Card 1990; Cramton & Tracy 1992; Kennan 1985)
**Classic claim**: Strike incidence responds to unexpected changes in firm
profitability and real wages — when firms are doing better than expected, workers
demand a share; when real wages erode, workers strike to recover losses.

**Contemporary test**: The 2021–2023 inflation shock produced real wage declines
across most countries simultaneously — a natural experiment in the wage-erosion
mechanism. Did countries with larger real wage declines see larger increases in
strike activity?

**How to test**: Merge with country-level CPI and nominal wage data. Construct
real wage change variable. Test whether real wage declines predict subsequent
strike onset rates, controlling for country and week fixed effects.

---

## What Would Be New

Relative to the classic studies, a GDELT-based revisitation would offer:

1. **Global coverage**: Hibbs and others focused on 15–18 OECD countries. GDELT covers
   181 countries including the Global South, where union structures, political
   institutions, and economic conditions differ dramatically. Do the classic
   relationships hold outside the advanced industrial world?

2. **Subnational resolution**: Classic studies used country-year data. GDELT allows
   ADM1-week analysis — much finer temporal and spatial grain. Do business cycle
   effects operate at the subnational level, or only nationally?

3. **Contemporary institutional context**: Union density has collapsed, gig work has
   expanded, and the sectoral composition of economies has shifted dramatically since
   the 1970s. Are the classic relationships attenuated, reversed, or concentrated in
   specific sectors/regions?

4. **The COVID natural experiment**: An unprecedented simultaneous global shock to
   labor markets, followed by a highly uneven recovery. A rare opportunity to test
   the pro-cyclical hypothesis under extreme conditions.

---

## Potential Paper Structure

**Title**: "The Political Economy of Strikes Revisited: A Global Subnational Analysis"

**Argument**: The classic Hibbs-era regularities — pro-cyclicality, left-government
suppression, corporatism — were established in a specific institutional context that
no longer characterizes most of the world economy. Using GDELT data from 181 countries
at ADM1-week resolution, we test whether these relationships survive into the
contemporary period and generalize beyond the advanced industrial world.

**Sections**:
1. Introduction — the puzzle: classic theory meets contemporary trends
2. Theory — reviewing the Hibbs-era arguments and their institutional preconditions
3. Data — GDELT + macroeconomic + institutional covariates
4. Analysis:
   - Pro-cyclicality test (GDP, unemployment, real wages)
   - Political government test (left/right executive)
   - Corporatism test (ICTWSS)
   - COVID as natural experiment
5. Heterogeneity — Global South vs. OECD; high vs. low union density
6. Conclusion — what survives, what doesn't, what's new

**Key data sources to merge**:
- World Bank WDI: GDP growth, unemployment, inflation by country-year
- ILO: union density, collective bargaining coverage (ILOSTAT)
- ICTWSS database: corporatism indicators
- ParlGov or V-Party: government ideology (left/right executive)
- Oxford COVID Stringency Index: for the COVID natural experiment
- V-Dem: political institutions (already in the contagion paper)

---

## Relationship to Existing Work

This is a **third paper** in a potential sequence:
1. **Contagion paper** (current): geographic vs. national diffusion mechanisms
2. **COVID/sectoral paper**: recomposition of strike activity post-COVID, sector coding
3. **Hibbs revisited**: political economy of long-run strike trends, global scope

The GDELT infrastructure, ADM1 panel, and V-Dem covariates from the contagion paper
are directly reusable. The main additional investment is merging macroeconomic and
institutional covariates — largely available from existing public databases.
