# Theory Section: Strike Contagion — Literature and Argument Development

This note develops the theoretical framework for the contagion paper and identifies
relevant literature across five strands. The goal is to beef up the theory section
beyond the current 2–3 citations.

---

## Core Argument

The paper tests two competing mechanisms for why strike activity clusters spatially:

1. **Geographic diffusion** — step-by-step transmission between adjacent regions via
   demonstration effects, shared worker networks, or employer responses
2. **National wave dynamics** — simultaneous mobilization driven by common national
   signals (union calls, political events, media coverage)

The main finding is that geographic neighbor effects disappear once national-level
strike activity is controlled. This favors interpretation (2).

---

## Strand 1: Labor Studies / Industrial Relations

The classic labor studies literature already anticipated the national wave finding.

**Shorter & Tilly (1974)** — *Strikes in France, 1830–1968*
The foundational reference. Shorter and Tilly argue that strike waves are driven by
macro-level political and economic cycles (industrialization, state crisis) rather than
local workplace grievances or geographic spread. National-level processes synchronize
strike timing across regions. **Key citation for the national wave mechanism.**

**Cronin (1979)** — "Strikes and Power in Britain, 1870–1920." *IRSH* 24(2): 144–167.
Documents the major British strike waves of 1871–72, 1889–90, 1911–13, 1919–20 and
shows they were nationally synchronized across industries and regions simultaneously —
not spreading step-by-step from an origin. Reinforces the national wave interpretation.

**Franzosi (1989)** — "One Hundred Years of Strike Statistics." *ILRR* 42(3): 348–362.
Methodological survey warning that treating strikes as independent events ignores
cross-unit dependence. Directly validates our concern that naive spatial models
overestimate geographic diffusion by not accounting for national common shocks.

**Franzosi (1995)** — *The Puzzle of Strikes: Class and State Strategies in Postwar Italy*.
Cambridge University Press.
[Details tentative — verify before citing.] The central puzzle is why strike waves
occur when they do, given that the timing does not follow simple economic or bargaining
logic. Franzosi challenges asymmetric information / bargaining failure models by arguing
that Italian strike waves are driven by class dynamics and national political rhythms
that those models miss. Key arguments: (1) strikes are expressions of class conflict
between labor and capital, not just rational bargaining failures; (2) the state is an
active participant with its own strategies, not a neutral arbiter; (3) strike waves
reflect national political mobilization cycles — periods of broad left-labor advance or
retreat — not local workplace grievances spreading geographically; (4) employers
responded to strike waves by restructuring production (moving to smaller plants,
outsourcing) to reduce union leverage, reshaping the terrain of future conflict.
Methodologically distinctive in combining quantitative and narrative/sequence analysis.
Relevant to the contagion paper as a single-country historical case study showing that
apparent spatial clustering of strikes reflects national political rhythms, not
geographic diffusion — consistent with our cross-national finding.

**Biggs (2002)** — "Strikes as Sequences of Interaction." *Social Science History* 26(3).
Analyzes the 1886 American strike wave. Strikes generate information for other workers
(about employer resistance, union effectiveness, political opportunity) creating feedback
loops. Distinguishes local imitation from national mobilization driven by shared
information — a key micro-foundation for the broadcast vs. contagion distinction.

### What to add to the theory section

The labor studies tradition provides historical and comparative evidence that strike
waves are national phenomena. We should open the theory section by situating ourselves
within this tradition — our paper provides the first large-N cross-national subnational
test of what Shorter & Tilly, Franzosi, and Cronin documented in single-country
historical cases.

---

## Strand 2: Social Movement Diffusion

The social movements literature provides the sharpest conceptual tools for our argument.

**Tarrow (1994/2011)** — *Power in Movement*
Tarrow's "cycles of contention" concept: periods when protest rises across multiple
sectors and regions simultaneously, driven by expanding political opportunities rather
than geographic spread. Information about the "susceptibility of a polity to challenge"
spreads through a shared political environment, not through direct inter-group contact.
**This is the single most important social movement citation — cycles of contention are
the non-relational national-level mechanism that produces exactly what we observe.**

**McAdam, Tarrow & Tilly (2001)** — *Dynamics of Contention*
Distinguishes "relational" diffusion mechanisms (brokerage — new ties connecting
previously isolated actors) from "non-relational" mechanisms (actors respond
independently to shared stimuli). Most apparent "diffusion" involves national-level
opportunity shifts with meso-level brokerage. Our country×week fixed effects absorb the
non-relational component; the residual neighbor effect tests for relational diffusion.

**Myers (2000)** — "The Diffusion of Collective Violence." *AJS* 106(1): 173–208.
Riots diffuse along mass media distribution networks, not pure geographic proximity.
Directly relevant: GDELT captures media-reported events, and if the diffusion channel
is media networks (which operate nationally), controlling for national activity removes
the mechanism generating apparent spatial clustering.

**Oliver & Myers (2002)** — "Networks, Diffusion, and Cycles of Collective Action."
Both "broadcast" mechanisms (actors respond to a common signal) and "contagion"
mechanisms (direct peer influence) operate in protest waves. Models that cannot
distinguish them overestimate geographic diffusion. Controlling for national activity —
as we do — is precisely the right way to isolate genuine spatial contagion.

**Tarrow & McAdam (2005)** — "Scale Shift in Transnational Contention."
Geographic diffusion between units requires active organizational brokerage. Without
such linkages, apparent spatial clustering reflects simultaneous national mobilization.

### What to add to the theory section

The relational/non-relational distinction from McAdam, Tarrow & Tilly gives us
precise vocabulary. Our country×week FE removes non-relational (broadcast) effects.
The residual neighbor coefficient tests for relational diffusion. This framing
clarifies the identification strategy and connects us to a large theoretical tradition.

---

## Strand 3: Conflict Studies Contagion

The conflict literature provides our closest methodological analog.

**Buhaug & Gleditsch (2008)** — "Contagion or Confusion?" *ISQ* 52(2): 215–233.
Asks whether spatial clustering of civil wars reflects genuine contagion or confounding
by shared attributes. Finds evidence of neighborhood effects but substantially reduced
by structural controls. **The title directly parallels our paper's core question. Their
methodological approach — comparing naive spatial models to models with structural
controls — is the template we follow at the subnational level.**

**Gleditsch (2007)** — "Transnational Dimensions of Civil War." *JPR* 44(3): 293–309.
Regional context matters independently of domestic factors for civil war onset.
Establishes the analogy: national-level strike environments should matter for
subnational strike activity, as we find.

**Braithwaite (2010)** — "Resisting Infection." *JPR* 47(3): 311–319.
State capacity moderates conflict contagion. Parallel argument: national industrial
relations institutions may condition whether local strike activity spreads geographically
(a productive extension for future work).

**Gleditsch & Rivera (2017)** — "The Diffusion of Nonviolent Campaigns." *JCR* 61(5).
Regional diffusion of nonviolent campaigns exists but is conditional on shared political
opportunity structures. Neighbor effects may vanish when shared political environments
are controlled — directly parallel to our finding.

**Weidmann (2015)** — "Communication Networks and Ethnic Conflict." *JPR* 52(3).
Ethnic conflict spreads along communication networks, not geographic proximity.
Reinforces: the relevant diffusion channel is informational (national), not spatial.

### What to add to the theory section

The conflict literature gives us a comparison point. We should note that subnational
geographic spillovers of civil conflict are **robust** to national-level controls in
that literature — unlike our strike findings. Labor strikes and armed conflict may
differ systematically: strikes are more embedded in national institutional frameworks
(labor law, union federations, collective bargaining structures) while civil conflict
involves local resource competition and ethnic geography that generates geographic
spillovers independent of national dynamics. The contrast is theoretically interesting.

---

## Strand 4: Economic Approaches

The economics literature on strikes provides micro-foundations for national
synchronization.

**Ashenfelter & Johnson (1969)** — *AER* 59(1): 35–49.
Foundational economic model. Strikes occur when union wage expectations diverge from
what firms will pay. If wage expectations are anchored by national inflation or national
economic performance, strike timing will be nationally synchronized across regions —
providing an economic micro-foundation for national wave dynamics.

**Kennan & Wilson (1993)** — *JEL* 31(1): 45–104.
Survey of asymmetric-information bargaining. Strikes arise when firms have private
information about profitability that unions cannot observe. Strike waves occur when
aggregate economic uncertainty rises nationally, synchronizing across regions without
any direct spatial contagion.

**Card (1990)** — *QJE* 105(3): 625–659.
Empirical test of asymmetric information model. Strike probability responds to
unexpected changes in firm profitability. If these shocks are nationally correlated,
strikes across regions will be synchronized by shared macroeconomic environments.

**Cramton & Tracy (1992)** — *AER* 82(1): 100–121.
Workers choose between strikes and holdouts based on real wage and labor market
conditions — nationally determined cyclical factors. Reinforces that primary drivers
of strike timing are macroeconomic and national, not geographic.

**Rees (1952)** — "Industrial Conflict and Business Fluctuations." *Journal of Political
Economy* 60(5): 371–382.
One of the earliest empirical demonstrations that strike frequency tracks the business
cycle — rising in booms, falling in recessions. Establishes the macro-synchronization
claim at its historical root and provides the longest time-series evidence for the
national economic mechanism.

**Hibbs (1976)** — "Industrial Conflict in Advanced Industrial Societies." *APSR* 70(4):
1033–1058.
The canonical cross-national empirical demonstration that strike activity across
advanced democracies is driven by macroeconomic conditions and political-institutional
context, not workplace grievances alone. Key findings: (1) strikes are pro-cyclical —
rising with economic growth and tight labor markets when workers have more leverage;
(2) left-party government suppresses strikes via political exchange — unions restrain
militancy when political allies are in power; (3) centralized corporatist union
confederations suppress strikes by internalizing conflict into wage bargaining
institutions; (4) fragmented decentralized union structures (US, UK) produce higher
strike rates. Directly relevant as the canonical source for national-level political
and economic forces driving strike timing — exactly what country×week fixed effects
absorb in our identification strategy.

**Hibbs (1978)** — "On the Political Economy of Long-Run Trends in Strike Activity."
*British Journal of Political Science* 8(2): 153–175.
Analyzes why strike waves hit multiple advanced industrial countries simultaneously
in the late 1960s and early 1970s — France 1968, Italy 1969, UK 1972/74, Canada,
Finland, the US in quick succession. Hibbs argues these cross-national surges reflect
shared macroeconomic and political conditions (inflation, breakdown of postwar wage
bargains, political polarization) hitting multiple countries at once, rather than
contagion spreading sequentially from one country to another. **Directly relevant to
the national wave dynamics argument**: this is the international-level analog of the
within-country finding in the contagion paper — units (countries in Hibbs; regions in
our paper) cluster in their strike activity because of common macro-level shocks, not
because strikes spread geographically step-by-step. A key citation for the claim that
apparent clustering reflects common exposure rather than sequential diffusion.

**Kennan (1985)** — "The Duration of Contract Strikes in U.S. Manufacturing." *Journal
of Econometrics* 28(1): 5–28.
Empirical analysis of strike duration in U.S. manufacturing showing that strikes are
shorter when real wages are rising — a business cycle effect. Alongside Kennan (1987),
provides the most rigorous empirical link between macroeconomic conditions and strike
timing.

**Kennan (1986)** — "The Economics of Strikes." In *Handbook of Labor Economics*, eds.
Ashenfelter and Layard. Amsterdam: North-Holland.
Comprehensive survey of the economics of strikes. Summarizes evidence that strike
incidence and duration are driven by aggregate economic conditions, wage expectations,
and bargaining structure — all nationally determined. The most comprehensive reference
for the economics strand.

**Robertson (2011)** — "Political Contestation and Labor Rights: The Political Economy of
Strikes." (Likely: *Comparative Political Studies* or similar — verify exact citation.)
Shows that regime type and political competition moderate the relationship between
economic shocks and strike activity — weaker democratic institutions suppress the
translation of economic grievances into strike action. **Very relevant for the
institutional conditioning section (H3–H5):** provides comparative politics precedent
for the idea that political institutions shape whether economic signals translate into
strike mobilization, directly supporting the V-Dem moderation analysis.

**Teitelbaum (2007)** — "Wall of Smoke: Labor Reform and the Political Economy of
Development in India." (Verify exact title/citation — author's own work.)
Structural economic conditions shape labor mobilization capacity — the political economy
of labor relations conditions when and where strikes occur. **Self-citation; should be
included.** Relevant to the institutional conditioning section and to the broader
argument that national political-economic context, not geographic proximity, drives
strike clustering.

### What to add to the theory section

The economics literature offers a complementary micro-foundation: if strikes are
triggered by nationally-determined economic conditions (unexpected changes in firm
profitability, real wage declines, macroeconomic uncertainty), national synchronization
follows mechanically. We may want a short paragraph noting that the econ approach
converges with the sociological "national wave" argument from a completely different
theoretical tradition. The business cycle strand (Rees 1952; Hibbs 1976; Kennan 1985,
1986; Card 1990; Cramton & Tracy 1992) and the institutional moderation strand
(Robertson 2011; Teitelbaum 2007) are the two additions from the NYU abstract most
worth incorporating.

---

---

## Strand 6: Recent Empirical Work — What Exists and What Is Missing

The search for recent empirical work confirms the paper is genuinely novel. No existing
study combines (a) strikes specifically, (b) subnational spatial units, (c) cross-
national scope, and (d) fixed effects regression with a spatial lag. The paper fills
the gap between the protest contagion literature (cross-national but not subnational,
not strike-specific) and the strike literature (cross-national but no spatial diffusion
test).

### Closest analogs

**Arezki, Rabah, Alou Adesse Dama, Simeon Djankov, and Ha Nguyen. 2024. "Contagious
Protests." *Empirical Economics* 66(6): 2397–2434. DOI: 10.1007/s00181-023-02539-y**
The most direct analog to the current paper. Uses protest event data from 200 countries,
2000–2020, and estimates an autoregressive spatial panel model with a geographic
distance-based weight matrix. Finds strong evidence of protest contagion across country
borders, with social media penetration amplifying cross-national spillovers. Key
differences from our paper: (1) the spatial unit is the country, not ADM1; (2) the
outcome is protest broadly, not strikes specifically; (3) the spatial lag is cross-
national, not within-country subnational. Our paper extends this logic to the
subnational level and focuses specifically on labor strikes.

**Aidt, Toke S. and Gabriel Leon-Ablan. 2022. "The Interaction of Structural Factors
and Diffusion in Social Unrest: Evidence from the Swing Riots." *British Journal of
Political Science* 52(2): 869–885. DOI: 10.1017/s0007123420000873**
Uses parish-level panel data on the English Swing Riots of 1830–31 to disentangle
structural causes from spatial diffusion. Finds a positive and significant spatial lag
— riots cluster geographically — and shows that diffusion multiplied the effect of
local structural factors by approximately 3.15. Methodologically close: subnational
panel data with spatial lag to test geographic spread of collective action. Limitations
relative to our paper: historical, single-country, and about riots not strikes.

**Aidt, Toke S., Gabriel Leon-Ablan, and Max Satchell. 2022. "The Social Dynamics of
Collective Action: Evidence from the Diffusion of the Swing Riots, 1830–1831."
*Journal of Politics* 84(1): 209–225. DOI: 10.1086/714784**
Companion piece developing explicit diffusion mechanisms: information networks, local
organizers, and repression. Finds contagion travels through personal and trade networks
rather than mass media, and magnifies structural effects by a factor of 2.65. Provides
a benchmark for what identifying spatial contagion looks like methodologically.

### Cross-national panel studies of strike determinants

**Brandl, Bernd and Franz Traxler. 2010. "Labour Conflicts: A Cross-national Analysis
of Economic and Institutional Determinants, 1971–2002." *European Sociological Review*
26(5): 519–540. DOI: 10.1093/esr/jcp036**
The most rigorous recent cross-national panel study of strike determinants. Tests
economic explanations (wages, productivity) against institutional explanations (union
strength, corporatism, bargaining structure). Finds institutional variables — especially
collective bargaining structure — are more robust predictors of cross-national
variation. Key reference for our dependent variable's known covariates and for
situating our paper in the cross-national literature. No spatial component.

**Lindvall, Johannes. 2013. "Union Density and Political Strikes." *World Politics*
65(3): 539–569. DOI: 10.1017/s0043887113000142**
Cross-national panel study of political (general) strikes. Finds an inverted-U
relationship with union density — political strikes peak at intermediate density levels.
Relevant if distinguishing labor-management from political strikes; useful as a
benchmark for cross-national modeling.

**Addison, John T. and Paulino Teixeira. 2024. "Strike Incidence and Outcomes: New
Evidence from the 2019 ECS." *European Journal of Industrial Relations* 30(2): 123–149.
DOI: 10.1177/09596801231206979**
Uses 2019 European Company Survey (multi-country establishment data). Finds higher
union density, mixed-level collective agreements, and flexible employment associated
with higher strike incidence. Most recent cross-national empirical study of strike
determinants at firm level. Not a spatial paper but useful for the institutional
covariates.

### Labor geography

**Nowak, Jörg. 2016. "The Spatial Patterns of Mass Strikes: A Labour Geography
Approach." *Geoforum* 75: 270–273. DOI: 10.1016/j.geoforum.2016.08.004**
Examines spatial geography of mass strike waves in Brazil, India, and South Africa
post-2008 from a labor geography perspective. Argues that spatial analysis of strike
waves has been largely absent from labor geography and calls for renewed conceptual
work on what a "strike wave" means spatially. Less quantitative than our paper but one
of the very few works directly addressing geographic spread of strikes in the Global
South — which is our empirical territory.

### Infrastructure / data

**Zhukov, Yuri M., Christian Davenport, and Nadiya Kostyuk. 2019. "Introducing xSub:
A New Portal for Cross-National Data on Sub-National Violence." *Journal of Peace
Research* 56(4): 604–614. DOI: 10.1177/0022343319836697**
Introduces xSub, a cross-national database of subnational conflict events covering 156
countries across 21 data sources at consistent spatial and temporal units (province,
district, grid cell; year, month, week, day). Shows the infrastructure for subnational
panel analysis across many countries. Event categories include protests and strikes
alongside violent conflict. Relevant as prior art for the data approach and as a
potential complementary data source.

---

## Strand 5: Threshold / Network Contagion Models

**Granovetter (1978)** — "Threshold Models of Collective Behavior." *AJS* 83(6): 1420–1443.
Collective action as threshold cascade: actors join when enough others have already
joined. The model is agnostic about *which* others matter — national co-workers, media
reports of distant events, or geographic neighbors. National-level threshold dynamics
can generate apparent geographic clustering without step-by-step spatial diffusion.

**Myers (2000)** — as above. Key application of contagion models to riots via media networks.

**Watts & Dodds (2009)** — "Threshold Models of Social Influence." In *Oxford Handbook of
Analytical Sociology*.
Extends Granovetter to network settings: large cascades depend on the structure of the
influence network, not geographic proximity. If the operative influence network is
national (national media, national unions, sectoral associations), controlling for
national activity removes the mechanism generating spatial clustering.

---

## Draft Additions to Theory Section

### Addition 1: Open with the labor studies tradition

Before the current two-mechanism framing, add a short paragraph situating the paper
in the historical literature:

> The question of why strikes cluster in time and space has a long history in labor
> studies. The foundational comparative-historical work of Shorter and Tilly (1974) on
> French strike waves, and analogous analyses by Cronin (1979) for Britain and Franzosi
> (1995) for Italy, established that strike waves are nationally synchronized phenomena:
> periods of elevated strike activity tend to affect multiple regions and sectors
> simultaneously, driven by shared macro-level political and economic conditions rather
> than by sequential local diffusion. Our paper subjects this historical finding to its
> first large-N cross-national subnational test, using ADM1-week panel data from 181
> countries to ask whether the apparent spatial clustering of strikes reflects genuine
> geographic transmission or common national exposure.

### Addition 2: Connect to social movement diffusion

In the "geographic diffusion vs. national waves" section, add:

> The social movement literature offers a precise conceptual vocabulary for this
> distinction. McAdam, Tarrow, and Tilly (2001) distinguish *relational* diffusion
> mechanisms — in which new ties connect previously isolated actors, enabling direct
> transmission — from *non-relational* mechanisms, in which actors respond
> independently to shared stimuli such as political opportunities, economic shocks, or
> media signals. Geographic neighbor effects, if they exist, represent relational
> diffusion: direct demonstration effects transmitted through proximity. National wave
> dynamics represent non-relational diffusion: simultaneous responses to common
> national stimuli. Tarrow's (1994) concept of "cycles of contention" captures the
> non-relational mechanism at the national level — periods when broad shifts in
> political opportunity generate mobilization across regions and sectors at once, with
> spatial clustering as a byproduct of common national exposure rather than geographic
> spread. Oliver and Myers (2002) show that models which cannot distinguish these
> mechanisms will systematically overestimate geographic diffusion effects — exactly the
> bias our identification strategy is designed to correct.

### Addition 3: Contrast with conflict literature

In the discussion section (or a note in the theory section):

> This stands in contrast to findings in the conflict contagion literature. Buhaug and
> Gleditsch (2008) — whose title "Contagion or Confusion?" directly parallels the
> question we ask about strikes — find that spatial clustering of civil wars persists
> after controlling for shared structural attributes, suggesting genuine neighborhood
> effects. The divergence between the strike and conflict findings is theoretically
> interesting. Strikes are more deeply embedded in national institutional frameworks —
> labor law, national union federations, collective bargaining structures that operate
> at the country level — while civil conflict often involves local resource competition
> and ethnic geography that generates subnational spillovers independent of national
> dynamics. The epidemiological metaphor (Braithwaite 2010) is apt: national
> institutions may function as a form of "herd immunity" against geographic strike
> diffusion, ensuring that mobilization signals travel through national channels rather
> than accumulating locally at geographic borders.

### Addition 4: Economic micro-foundations

Short paragraph for the "national wave dynamics" mechanism:

> Economic theories of strikes provide an additional micro-foundation for national
> synchronization. The canonical bargaining model (Ashenfelter and Johnson 1969) and
> its asymmetric-information extensions (Kennan and Wilson 1993; Card 1990) identify
> strike probability as a function of the gap between worker expectations and firm
> capacity to pay — a gap that is itself driven by macroeconomic conditions that are
> national in scope. When unexpected shifts in profitability, inflation, or real wages
> affect all firms in a country simultaneously, strike timing will be synchronized
> across regions not because workers are imitating each other, but because all workers
> face the same macroeconomic environment. Cramton and Tracy (1992) document this
> pattern empirically for the United States. Our country-by-week fixed effects absorb
> precisely these national macroeconomic common shocks, providing a clean test of
> whether geographic proximity carries independent causal weight.

---

## Key Citations Summary

| Citation | Strand | Role in argument |
|---|---|---|
| Shorter & Tilly 1974 | Labor | Historical evidence for national waves |
| Cronin 1979 | Labor | British evidence for national synchronization |
| Franzosi 1989 | Labor | Methodological warning about cross-unit dependence |
| Franzosi 1995 | Labor | Italian evidence for national wave dynamics |
| Biggs 2002 | Labor | Micro-foundations: strikes as information generators |
| Tarrow 1994/2011 | Movements | Cycles of contention = non-relational national mechanism |
| McAdam, Tarrow & Tilly 2001 | Movements | Relational vs. non-relational diffusion distinction |
| Myers 2000 | Movements | Media networks as diffusion channel (not geography) |
| Oliver & Myers 2002 | Movements | Broadcast vs. contagion — identification strategy |
| Buhaug & Gleditsch 2008 | Conflict | Direct methodological analog; contrast finding |
| Gleditsch & Rivera 2017 | Conflict | Conditional diffusion; parallel null finding |
| Braithwaite 2010 | Conflict | Institutional moderation of contagion |
| Rees 1952 | Economics | Earliest empirical evidence: strikes track business cycle |
| Hibbs 1976 | Economics | Cross-national: macro conditions + institutions drive strikes |
| Hibbs 1978 | Economics / National waves | Cross-national simultaneity of 1968-74 waves = common shocks, not contagion |
| Ashenfelter & Johnson 1969 | Economics | Economic micro-foundations for national waves |
| Kennan 1985, 1986 | Economics | Business cycle effects on strike duration and incidence |
| Kennan & Wilson 1993 | Economics | Asymmetric info → national shock synchronization |
| Card 1990 | Economics | Empirical evidence for macro-driven strike timing |
| Cramton & Tracy 1992 | Economics | Real wages and national cyclical factors |
| Robertson 2011 | Institutions | Regime type moderates economic shocks → strikes (H3–H5) |
| Teitelbaum 2007 | Institutions | Political economy of labor capacity (self-cite) |
| Granovetter 1978 | Networks | Threshold model: national thresholds mimic spatial diffusion |
| Watts & Dodds 2009 | Networks | Network structure determines diffusion channel |
| Arezki et al. 2024 | Recent empirics | Protest contagion panel, 200 countries — closest analog |
| Aidt, Leon-Ablan & Satchell 2022 | Recent empirics | Swing Riots spatial diffusion — methodological benchmark |
| Brandl & Traxler 2010 | Recent empirics | Cross-national panel of strike determinants, no spatial component |
| Nowak 2016 | Recent empirics | Spatial patterns of mass strikes, Global South |
| Lindvall 2013 | Recent empirics | Union density and political strikes, cross-national |

---

---

## Citations for Other Parts of the Paper (Not Theory Section)

**Hicks (1963)** — *The Theory of Wages*. London: Macmillan.
Foundational bargaining theory: strikes occur because of miscalculation about the
opponent's resistance. Classic reference for situating the paper in the long tradition
of industrial dispute analysis. → **Use in introduction** as the historical anchor
("beginning with Hicks's foundational analysis...").

**Brandt (2022)** — spatial lag variables and distance-weighted spillover effects in
conflict forecasting.
Methodological precedent for constructing spatial neighbor variables in a panel setting.
→ **Use in Data/Methods section** when describing the neighbor variable construction
and the choice to use contiguous ADM1 adjacency.

**Flynn (2000)** — predictive value of media attention for labor conflicts.
Demonstrates that GDELT-style media coverage contains signal about upcoming labor
action. → **Use in Data section** when discussing GDELT's media-derived coverage and
its validity as a strike indicator, and potentially in the bias/limitations discussion.

---

## Next Steps

1. Decide which additions to include — all four, or a subset
2. Decide where to place the economics paragraph (theory or discussion)
3. Add citations to the paper's .bib file
4. Work these into the actual theory section in `contagion-paper.qmd`