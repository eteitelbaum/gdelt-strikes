# Data Section — Draft

> **Status**: First full draft. Intended to replace the current Data section in `contagion-paper.qmd` (lines 123–177). Review for fit and then integrate.
>
> **Bibliography notes**:
> - `@wang2016` is in the bib ("Growing Pains for Global Monitoring," *Science* 2016).
> - `@halterman2025a` is the correct bib key for Halterman and Keith (2025).
> - `@hoffmann2022` is NOT in the bib. Needs to be added before integration.
> - `@schrodt2012a` is NOT in the bib. Needs to be added before integration.
> - `@muller2018` and `@blair2020` are NOT in the bib. Either add them or drop the inline citation in the Panel Construction paragraph.
> - `@hammond2014`, `@ward2013`, `@leetaru2013a` are all confirmed in the bib.
> - `@robertson2011` is confirmed in the bib.
> - `@raleigh2010` is NOT in the bib. Needs to be added before integration. Full citation: Raleigh, Clionadh, Andrew Linke, Håvard Hegre, and Joakim Karlsen. 2010. "Introducing ACLED." *Journal of Peace Research* 47(5): 651–660.

---

# Data

Testing the theoretical expectations requires systematic data on strike activity at subnational resolution across a large and diverse set of countries over an extended period. No existing source has met these requirements. The International Labour Organization publishes annual strike statistics compiled from national labor ministry reports, but these aggregate to the country-year level and contain no event-level or subnational geographic information. The High Profile Strikes Dataset [@robertson2011] provides cross-national event records of major industrial actions and represents the most comprehensive global strike compilation assembled to date, but it is restricted to high-salience cases and is no longer in production. Broader conflict and protest databases offer event-level geocoded records but do not systematically cover labor strikes as a distinct event type. ACLED explicitly excludes strikes from its protest category unless they are accompanied by a public demonstration [@raleigh2010], rendering coordinated work stoppages invisible in the data.

This analysis draws on the Global Database of Events, Language and Tone (GDELT), which offers event-level records with subnational geocoding across a large number of countries and includes a dedicated identifier for strike events [@leetaru2013a]. GDELT identifies events through automated processing of news text, a design that maximizes global coverage but generates substantial false positives and introduces location errors at the subnational level. The remainder of this section describes the steps taken to extract and filter the data, the validation pipeline used to address these problems, the construction of the analysis panel, and the key variables used in the analysis.

## Strike Events and False Positives

GDELT codes events using the Conflict and Mediation Event Observations (CAMEO) scheme, which assigns each reported event to one of several hundred action categories [@leetaru2013a; @schrodt2012a]. The relevant category here is CAMEO code 143, labeled "strikes and boycotts," which covers labor strikes, work stoppages, and political boycotts. I queried the GDELT database via Google BigQuery for all code-143 events from January 2015 to September 2025, retaining only records with valid geographic coordinates, which yielded 492,500 records. Three further filters were then applied to improve data quality before any content-based validation. First, I kept only events assigned to a specific subnational administrative region rather than to a country as a whole, reducing the dataset to 328,982 records. Then I filtered for events with at least one high-confidence news mention, where confidence reflects how closely the source article matches the coded event according to GDELT's internal scoring, leaving 134,141 records. Then I filtered for events where the associated news articles were tagged with the keyword "STRIKE" in GDELT's article-level topic metadata, reducing the dataset to 30,899 records.

```{r}
#| label: tbl-pipeline
#| tbl-cap: "Data extraction and filtering pipeline."
#| echo: false

library(tinytable)

pipeline <- data.frame(
  Step = c(
    "BigQuery download",
    "Geographic filter",
    "High-confidence filter",
    "Keyword theme filter",
    "LLM content classifier"
  ),
  Description = c(
    "CAMEO code 143, valid coordinates",
    "Valid subnational region code assigned",
    "At least one high-confidence news mention",
    "Article tagged \"STRIKE\" in topic metadata",
    "Article describes a labor strike"
  ),
  Records = c("492,500", "328,982", "134,141", "30,899", "11,503")
)

tt(pipeline, width = 1,
   notes = "Each row shows the number of records retained after applying the listed filter.") |>
  style_tt(j = 3, align = "r")
```

Even after applying these filters, the dataset retains a substantial number of false positives. GDELT's design prioritizes capturing as many events as possible rather than ensuring each record reflects a real event, and raw records include misclassified articles, retrospective coverage of past events treated as current, and articles that mention strikes only in passing. The CAMEO coding scheme also groups labor strikes together with political boycotts under a single event type. Applying CAMEO code 143 directly as a measure of labor strikes would therefore mix genuine industrial actions with other forms of collective action for which the contagion mechanisms described in Section 2 need not apply.   

## Validation Pipeline

Due to the false positive issue identified above, previous studies using GDELT have heavily filtered the data. Wang et al. [-@wang2016] analyzed the URLs underlying raw GDELT protest event records and found that only 21% of valid URLs actually described a protest event. Hoffmann et al. [-@hoffmann2022] applied a machine learning classifier to GDELT protest events in six European countries, retaining 3,564 validated records from 379,747 raw events, with precision of 0.74 and recall of 0.83. For GDELT to serve as a credible source for subnational strike analysis, a comparable filtering step is required. I apply a two-stage validation pipeline that addresses these problems in sequence. The first stage uses a large language model to assess whether each remaining record actually describes a labor strike. The second checks whether the location GDELT has assigned to each validated event is correct.

### Stage 1: URL Classifier

The first stage uses GPT-4o mini to assess whether each of the 30,899 remaining records actually describes a labor strike, following the approach described by Halterman and Keith [-@halterman2025a]. The model is prompted using few-shot prompting whereby the prompt includes a set of labeled examples that demonstrate the desired classification before the model is asked to classify a new case. Each prompt pairs the source URL and headline with a system instruction defining what counts as a labor strike and a series of worked examples covering relevant, irrelevant, and ambiguous cases across multiple languages. The model is then asked whether the underlying article covers a labor strike rather than a related but distinct event such as a political boycott. Full article text retrieval proved unneccessary, since news coverage of industrial disputes almost invariably names the location and nature of the dispute in the headline or web address. Uncertain cases from the first pass are resubmitted in a second pass with the article headline added when it can be retrieved. Unlike Hoffmann et al.'s [-@hoffmann2022] classifier, which involved full article retrieval and was limited to six countries, this approach scales to the full global dataset without additional infrastructure. The classifier retained 11,503 events from the 30,899 records submitted. The full system prompt and few-shot examples for both passes are reproduced in the appendix.

### Stage 2: Geocode Validator

The second stage checks whether GDELT's subnational location assignment is correct for each validated event. GDELT determines location by scanning article text for place names, a process that introduces systematic errors at the subnational level [@leetaru2013a]. The most consequential, documented by Hammond and Weidmann [-@hammond2014], is dateline bias: when a wire service or foreign correspondent covers a strike in a secondary city, the dispatch location rather than the strike location can be recorded as the event's geographic origin.

I address these errors with a second model pass using GPT-5 mini. As in Stage 1, the model is prompted with few-shot examples illustrating each type of location error before being asked to assess each case. It receives the source URL and headline and is asked whether GDELT's recorded location is consistent with the geographic content of the article. The full system prompt and examples are reproduced in the appendix. Among the 11,503 validated events, the model returned a definitive verdict for 5,236 events. The remaining 6,267 received an uncertain verdict, predominantly because the source URL returned a broken link or paywalled content that provided too little information to judge. Among events with a definitive verdict, 34.5% were miscoded (1,806 corrected; 3,430 confirmed). Where the model identified a more accurate location, that corrected assignment replaces GDELT's original.

Country-level error rates range from under 10% to over 90%, revealing the systematic nature of the problem.[^geobias] Each validated event is assigned a quality indicator reflecting whether its location was confirmed, corrected, or left unvalidated, and this indicator is used in robustness checks that restrict the sample to location-verified observations.

[^geobias]: Error rates are highest for China (95%), Russia (77%), Ukraine (74%), Mexico (70%), and Israel (64%), almost certainly reflecting outlet-based location assignment: English-language coverage of strikes in these countries is disproportionately written by foreign correspondents, and GDELT records the correspondent's location rather than the strike site. Canada (49%) and the United Kingdom (39%) also show elevated rates, likely reflecting subnational misassignment within English-speaking countries.

### Residual Measurement Error

Even after correction, location uncertainty remains for the 54% of events that returned an uncertain verdict. When the recorded location of a strike event is wrong, the neighbor exposure variable is measured with error, and this will tend to produce estimates of the geographic diffusion effect that are smaller in magnitude than the true effect. Estimates of the geographic neighbor effect should therefore be read as lower bounds on true geographic transmission, to the extent any exists. The country-by-week fixed effects absorb the largest systematic source of remaining error. Dateline bias systematically assigns events to the capital's administrative region, but the capital is one specific region per country, and the identification strategy recovers variation across regions within the same country-week rather than relying on any region's absolute level of recorded activity. Systematic bias toward the capital therefore does not contaminate the neighbor exposure variable for regions elsewhere in the country.

### External Validation

No global database of labor strikes exists against which the validated GDELT measure can be compared directly. The International Labour Organization publishes country-level annual strike counts from national labor ministry reports, but coverage is incomplete and definitions vary by national legal framework. The European Trade Union Institute maintains European coverage, and national administrative records provide reliable counts for specific countries, but none of these constitutes a usable global benchmark. Ward et al. [-@ward2013] show that filtered GDELT and the ICEWS event database share approximately 71% of variance for major protest events, providing some reassurance that the filtered GDELT signal captures real mobilization. The absence of a comprehensive global strike database is part of the substantive motivation for this paper.

## Panel Construction

I aggregate validated strike events to an administrative region-week panel spanning January 2015 to September 2025. The outcome variable is a binary strike *onset* indicator equal to one if at least one validated event was recorded in the region during week $t$, following the convention used in the conflict contagion literature. The baseline onset rate is 1.4% across all region-weeks (0.87% in the subsample restricted to location-verified events).

The panel includes only administrative regions that appear in the validated data, specifically regions where at least one validated strike event was recorded during the sample period. This restriction reflects the media-derived nature of the data. A zero in the data is ambiguous: it could mean no strike occurred, or it could mean a strike occurred but was not covered by any source that GDELT monitors. Including all global administrative regions as true zeros would conflate absence of strikes with absence of media coverage, which is a serious concern given that GDELT systematically undercovers rural areas, countries with limited press freedom, and sources in many non-English languages. Restricting to observed regions carries the assumption that, for regions that have appeared in the data at least once, subsequent periods of non-activity reflect genuine absence of strike activity rather than a gap in coverage. This approach is consistent with prior subnational analyses using GDELT [@muller2018; @blair2020] and differs from studies using ACLED, where more comprehensive event coverage makes it more defensible to treat unobserved region-periods as true zeros. As a scope condition, the findings generalize to regions with sufficient media presence to generate GDELT coverage, which in practice means urban, economically active, or politically prominent subnational units.

After restricting to observed regions and excluding island administrative units with no contiguous within-country neighbors, the analysis panel includes 568 regions across [C] countries, observed over [W] weeks, yielding [R] region-week observations. Figure 2 maps cumulative strike prevalence across regions, showing concentration in South Asia, sub-Saharan Africa, and parts of Europe, reflecting both genuine geographic variation and GDELT's media coverage patterns.

```{r}
#| label: fig-data
#| fig-cap: "Cumulative strike prevalence across ADM1 regions, 2015--2025."
#| fig-width: 7
#| fig-height: 3.2

fig_2
```

## Neighbor Relationships

I define geographic neighbors as administrative regions sharing a border within the same country, identified using GADM version 4.1 administrative boundary polygons. The main analysis uses within-country neighbors only. Cross-border adjacency is examined as an exploratory extension. Table A1 (appendix) summarizes the distribution of neighbor counts.

## Key Variables

### Geographic Neighbor Exposure

The primary treatment variable, `neighbor_strike_t1_t2`, is a binary indicator equal to one if at least one within-country neighboring region recorded a strike onset in week $t-1$ or $t-2$. Exposure in either of the two prior weeks counts as exposure. The two-week window is designed to capture the period over which a demonstration effect from a neighboring region's strike might plausibly influence workers' decisions in an adjacent region, while keeping the treatment variable predetermined with respect to the current week's outcome. Only 7.9% of region-weeks are exposed, reflecting the sparsity of the validated strike sample.

### National Contagion

For the decomposition specification, `country_share_t1_t2` is the proportion of other regions in the same country with a strike onset in weeks $t-1$ or $t-2$, divided by the number of other regions in the country. This normalization removes any mechanical relationship between the variable's scale and how many regions a country has.

### Institutional Moderators

Three country-year indicators from the Varieties of Democracy (V-Dem) project are used in the moderation models. These are freedom of expression (`v2x_freexp_altinf`), freedom of association (`v2x_frassoc_thick`), and physical violence by state agents (`v2x_clphy`). All three are standardized before entering interaction models so that the main treatment coefficient is interpretable at the average value of each moderator in the sample.
