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

The following are suggested starting points. **Verify all citations before
use** — some details below are recalled from memory and should be confirmed.

### Foundational / Methodological

- **Leetaru & Schrodt (2013).** "GDELT: Global Data on Events, Location, and
  Tone, 1979–2012." Presented at the ISA Annual Convention. The original
  methodological description; addresses geolocation approach at a high level.

- **Schrodt, P.A.** Various papers on TABARI and PETRARCH event coding.
  Background on the automated coding infrastructure underlying GDELT.

### Validation / Critique

- **Hammond & Weidmann (2014).** "Using Machine-Coded Event Data for the
  Micro-level Study of Political Violence." *Journal of Peace Research.*
  Evaluates spatial accuracy of machine-coded event data; discusses the
  dateline bias problem directly. *(Verify journal and year.)*

- **Weidmann (2016) / Weidmann & Ward.** Work comparing GDELT geolocation
  against manually coded datasets at the sub-national level. Search for
  Weidmann's publications on event data validation. *(Specific citation
  needs verification.)*

- **Raleigh et al. / ACLED comparisons.** Several papers have compared GDELT
  event locations against ACLED (Armed Conflict Location & Event Data), which
  uses human coders. These comparisons consistently find country-level
  agreement to be high and sub-national agreement to be substantially lower.
  Search: "GDELT ACLED comparison geolocation."

- **Salehyan et al. (2012).** "Social Conflict in Africa: A New Database."
  *International Interactions.* Introduces SCAD; comparisons with GDELT are
  implicit in subsequent validation work on African conflict event data.
  *(Peripheral but useful for benchmarking sub-national accuracy.)*

- **Boschee et al.** ICEWS (Integrated Crisis Early Warning System) vs. GDELT
  comparisons. ICEWS uses a different automated coding pipeline (ACCENT/Jabari)
  and comparisons illuminate systematic differences in geolocation. Search:
  "ICEWS GDELT comparison."

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
