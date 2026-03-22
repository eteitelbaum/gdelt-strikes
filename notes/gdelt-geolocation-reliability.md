# GDELT Geolocation: Reliability Notes

## How GDELT Geolocates Events

GDELT runs web crawlers that scrape text from the sources it monitors. For
open-access sources (wire services, many local and regional papers, open news
sites) it obtains substantial article text. For paywalled sources it can only
access whatever is publicly visible — typically the headline, lede paragraph,
and Open Graph/meta tags. The depth of text available therefore varies by
source.

For geolocation specifically this distinction matters less than it might seem:
strike coverage almost always names the location in the headline or opening
sentence, so the NER step is working with sufficient text in most cases even
when full-text access is unavailable.

The geolocation pipeline matches place names found in the article text against
the **GeoNames** database and assigns coordinates and administrative codes.
The exact NER system GDELT uses has not been fully documented publicly.
Earlier versions of the pipeline (circa 2013–2015) likely relied on
rule-based or dictionary-based entity recognition consistent with the
TABARI/PETRARCH event coding infrastructure of that era. Leetaru has not
published a detailed technical spec for the geolocation component specifically.
**Treat any claim about the specific NER model with skepticism unless sourced
directly from GDELT documentation.**

GDELT produces three sets of geographic fields per event:

- `Actor1Geo` / `Actor2Geo` — location of the actors
- `ActionGeo` — location where the action took place

For strike analysis `ActionGeo_ADM1Code` is the relevant field.

---

## Known Reliability Issues

**Capital city / dateline bias.** The single most documented problem. When a
national wire story or foreign correspondent covers a strike, the dateline city
(often the capital or a major media hub) can be picked up as the action
location rather than the city where the strike actually occurred. Events from
smaller cities or regions that are covered primarily through national wires are
most affected.

**National/general strikes.** A country-wide general strike may be assigned to
whichever city is most prominently mentioned in coverage — often the capital —
rather than being flagged as multi-locational.

**ADM1 accuracy degrades sub-nationally.** Country-level coding is generally
considered reliable. ADM1-level coding introduces substantially more noise,
particularly for non-English sources where NER performance drops.

**Paywalled sources.** Where GDELT cannot access article body text, geolocation
falls back to whatever place names appear in the headline and metadata. This is
often sufficient for strikes (which name the location prominently) but
introduces more uncertainty for ambiguously worded headlines.

**Multiple location mentions.** Articles about regional strikes may name
several cities; which one GDELT picks up as `ActionGeo` is not always the
most relevant one.

---

## Key Literature to Consult

Citations verified and updated based on search confirmation.

### Foundational / Methodological

- **Leetaru, Kalev and Philip A. Schrodt. 2013.** "GDELT: Global Data on
  Events, Location, and Tone, 1979–2012." Presented at the ISA Annual
  Convention. The original methodological description; addresses geolocation
  approach at a high level. **In bib file.**

- **Schrodt, P.A.** Various papers on TABARI and PETRARCH event coding.
  Background on the automated coding infrastructure underlying GDELT.

### Validation / Critique

- **Hammond, Jesse and Nils B. Weidmann. 2014.** "Using Machine-Coded Event
  Data for the Micro-Level Study of Political Violence." *Research & Politics*
  1(2). DOI: 10.1177/2053168014539924.
  The key subnational geolocation validation paper. Benchmarks GDELT against
  ACLED and UCDP GED for African violence at cell-month level. Documents the
  capital city bias directly and concludes GDELT "should be used with caution
  for geo-spatial analyses at the subnational level." **In bib file.**
  Note: earlier drafts of this note incorrectly listed the journal as
  *Journal of Peace Research* — it is *Research & Politics*.

- **Raleigh, Clionadh, Andrew Linke, Håvard Hegre, and Joakim Karlsen. 2010.**
  "Introducing ACLED: An Armed Conflict Location and Event Dataset."
  *Journal of Peace Research* 47(5): 651–660. DOI: 10.1177/0022343310378914.
  Introduces ACLED — cite when describing what ACLED is as a benchmark
  dataset. There is no separate "Raleigh et al." GDELT comparison paper;
  the GDELT/ACLED comparison is Hammond & Weidmann (2014), which uses
  ACLED as the gold standard.

- **Salehyan, Idean, Cullen S. Hendrix, et al. 2012.** "Social Conflict in
  Africa: A New Database." *International Interactions* 38(4): 503–511.
  DOI: 10.1080/03050629.2012.697426.
  Introduces SCAD (Social Conflict in Africa Database) — covers protests,
  riots, strikes, and communal violence across 47 African countries,
  1990–2010, with georeferenced locations. Peripheral for our paper but
  useful for benchmarking subnational accuracy in African cases.

- **Ward, Michael D., Andreas Beger, et al. 2013.** "Comparing GDELT and
  ICEWS Event Data." Working paper, Duke University.
  The canonical GDELT/ICEWS comparison — already in literature folder.
  Note: an earlier draft of this note listed "Boschee et al." as a separate
  ICEWS/GDELT comparison; that is the same paper. Boschee is an ICEWS
  researcher at BBN but is not an author on the comparison paper.

### Optional / Lower Priority

- **Lee, Sophie J., Howard Liu, and Michael D. Ward. 2019.** "Lost in Space:
  Geolocation in Event Data." *Political Science Research and Methods* 7(4):
  871–888. DOI: 10.1017/psrm.2018.9.
  Proposes a two-stage ML algorithm improving geocoding accuracy by up to 25%
  using N-gram patterns and sentence context from full article text. Relevant
  only if writing a footnote noting that better geocoding algorithms exist
  but require full-text access infeasible at our global scale. Not worth
  citing otherwise — we are not re-geocoding.

### Specifically on Capital City / Dateline Bias

- This problem is discussed in several of the validation papers above.
  Leetaru himself has written blog posts on the GDELT project site
  acknowledging dateline issues — worth checking gdeltproject.org directly
  for technical notes.

---

## Implications for Spatial vs. Temporal Modeling

Geolocation reliability effectively constrains which research designs are
feasible:

**Within-country spatial diffusion (ADM1-level)** — the most ambitious
design, but hardest to defend given geolocation noise. Capital city / dateline
bias would systematically distort proximity measures and spatial lags.
Probably not viable without a validation step that is difficult to implement
at scale.

**Cross-country spatial diffusion** — geolocation is reliable at country
level, so this is technically feasible. Countries could be connected via
shared borders, trade linkages, or regional union federation membership.
However, the theoretical mechanism is weak: why would a strike in France
directly trigger one in Germany rather than both being driven by shared
macroeconomic conditions or a common international event (e.g., an EU-wide
austerity push)? Cross-country contagion is possible but hard to distinguish
from correlated shocks. Worth testing as a robustness check but probably not
the main story.

**Temporal waves within countries** — the most defensible design given the
data. Strike waves are a well-established concept in the comparative labor
politics literature (Shorter & Tilly 1974; Franzosi 1989) and country-week
aggregation sidesteps geolocation concerns entirely. The two-stage model
already built in `two-stage-models.qmd` is essentially set up for this.
Temporal autocorrelation and lagged strike counts are the natural predictors.
This is probably the right framing for the CLPW paper.

**Bottom line:** aggregating to country-level forecloses within-country
spatial analysis by definition. What remains are (a) temporal wave dynamics
within countries and (b) cross-country diffusion, the latter being
theoretically questionable as a primary mechanism. The strongest contribution
is likely a rigorous temporal model of strike waves with country fixed effects,
rather than a spatial one.

---

## Practical Implications for This Project

1. **Country-level analysis is more defensible than ADM1-level.** If the
   spatial diffusion model can be specified at country-week rather than
   ADM1-week, geolocation noise is a much smaller concern.

2. **Check the ADM1 distribution.** The existing `adm1-diagnostic.R` script
   is the right starting point. Flag countries where an implausibly high
   share of events are coded to the capital's ADM1 — this is a strong signal
   of dateline bias.

3. **`NumSources` as a quality proxy.** Events covered by more independent
   sources tend to be better geolocated because the NER has more text with
   potentially redundant location signals. The `high_conf_mentions` field in
   the dataset may already be doing some of this filtering.

4. **Acknowledge in the paper.** Measurement error in the location variable
   will attenuate spatial diffusion coefficients. This is worth a sentence in
   the data section and possibly a robustness check aggregating to country
   level.

5. **Re-geocoding from URL/title is probably not worth it.** GDELT's NER
   runs on more text than a URL or headline alone. Manual or LLM-based
   re-geocoding would only be worthwhile for a targeted subset of high-stakes
   events, not as a wholesale alternative.
