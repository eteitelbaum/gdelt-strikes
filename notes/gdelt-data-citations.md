# Data Note: GDELT Citations and Validation Strategy

This note identifies the key citations needed to defend the use of GDELT as a data
source in the contagion paper, documents the known limitations of raw GDELT event
data, and explains how our validation approach addresses those limitations. It also
flags what cannot be validated and how to acknowledge that honestly.

---

## The Core Problem with Raw GDELT Data

GDELT event data has a well-documented false positive problem. The database is designed
to maximize recall — capturing as many reported events as possible — at the cost of
precision. Raw GDELT records include:

- Events that never occurred (misclassified articles)
- Retrospective coverage (historical strikes reported in current news)
- Geolocation errors (events assigned to the wrong country or region)
- Definitional ambiguity (CAMEO code 143 conflates labor strikes with political
  boycotts under a single "protest" category)

The scale of this problem is documented by **Wang et al. (2016)**, who analyzed the
URLs underlying raw GDELT protest event records and found that only **21% of valid
URLs actually covered a protest event**. This is the foundational empirical finding
on GDELT false positive rates and should be cited when motivating any filtering step.

**Wang et al. (2016).** Published in *Science*. Full citation needs to be verified
and added to the bibliography — not currently in the literature folder. Track down
via Google Scholar. The 21% figure is cited in Hoffmann et al. (2022, p. 288).

---

## 1. Foundational GDELT Description

**Leetaru, Kalev and Philip A. Schrodt. 2013. "GDELT: Global Data on Events,
Location, and Tone, 1979–2012." Presented at the ISA Annual Convention.**
The original methodological description of GDELT. Cite in the data section when
first introducing GDELT. Explains the CAMEO event coding framework, the geolocation
pipeline, and the data architecture. This is the standard reference for "what GDELT
is."

---

## 2. The False Positive Problem and URL-Based Validation

**Hoffmann, Matthias, Felipe G. Santos, Christina Neumayer, and Dan Mercea. 2022.
"Lifting the Veil on the Use of Big Data News Repositories: A Documentation and
Critical Discussion of A Protest Event Analysis." *Communication Methods and
Measures* 16(4): 283–302. DOI: 10.1080/19312458.2022.2128099**

The most important citation for motivating our validation approach. Hoffmann et al.
document their own pipeline for extracting protest events from GDELT in six European
countries (2015–2020), confronting the false positive problem directly. Key findings:

- Raw GDELT protest events: 45% true positive rate on a human-coded sample of 1,000
- After SVM classifier + confidence filters: 58.5% true positive rate
- Final validated dataset: 3,564 events from 379,747 raw GDELT records

**Their method**: Retrieved full article text from all mention URLs using Python
`Newspaper3k`; used Wayback Machine for dead links; applied Opus MT neural
translation for non-English content; built a protest keyword dictionary; trained
an SVM with linear kernel (Precision=0.74, Recall=0.83 on test set). This required
GPU computing infrastructure and was feasible only at 6-country scale.

**What this means for us**: Hoffmann et al. establish that (a) URL-based content
validation is necessary, not optional, and (b) the filtering problem is tractable
with the right approach. Cite to motivate our own classifier and to acknowledge
the false positive baseline.

**Key contrast with our approach**:

| Dimension | Hoffmann et al. (2022) | Our approach |
|---|---|---|
| Method | SVM + keyword dictionary | LLM few-shot (GPT-4) |
| Input | Full article text | URL + headline |
| Languages | Neural MT translation | LLM handles natively |
| Scale | 6 countries, 6 years | 181 countries, 10 years |
| Infrastructure | GPU cluster required | OpenAI batch API |

Our approach avoids the broken-URL and paywall problems that made full-text
retrieval resource-intensive and scale-limiting for Hoffmann et al. For strike
events specifically, the URL and headline contain sufficient signal: strike coverage
almost always names the location and the dispute in the headline or opening sentence.
The LLM few-shot approach implements the same validation logic at global scale.

---

## 3. LLM-Based Event Classification

**Halterman, Andrew and Katherine A. Keith. 2025. "Codebook LLMs: Evaluating LLMs
as Measurement Tools for Political Science Concepts." *Political Analysis*.
DOI: 10.1017/pan.2025.10017**

The methodological grounding for using LLMs to classify political events according
to a codebook. Published in *Political Analysis* (the premier political science
methods journal). Provides a five-stage evaluation framework: codebook preparation,
behavioral testing, zero-shot evaluation, error analysis, and supervised fine-tuning.
Key finding: zero-shot LLM performance is reasonable but fine-tuning substantially
improves accuracy.

**Two reasons to cite**:

1. **Methodological legitimacy**: Halterman & Keith establish LLMs as valid tools
   for political event classification in the political science literature. Our
   few-shot URL classifier is an application of this approach — citing them situates
   our method within a recognized framework.

2. **A directly relevant substantive point** (p. 2): The paper notes that CAMEO's
   definition of "protest" *includes* labor strikes, while the Crowd Counting
   Consortium's definition *excludes* them. This is the definitional ambiguity our
   classifier addresses — GDELT code 143 conflates labor strikes with political
   boycotts, and our LLM classifier makes the conceptual cut that CAMEO does not.
   Our filtering step is therefore not merely noise reduction; it operationalizes
   a more precise definition of labor strike.

**Halterman, Andrew, Philip A. Schrodt, Andreas Beger, Benjamin E. Bagozzi, and
Grace I. Scarborough. 2023. "Creating Custom Event Data Without Dictionaries:
A Bag-of-Tricks." arXiv:2304.01331.**

Working paper (arXiv). Describes the "bag of tricks" for custom event data
production using LLMs, active learning, and transformer-based models — the
methodological infrastructure underlying the POLECAT dataset. Situates our approach
within the broader movement away from CAMEO dictionaries toward LLM-based event
coding. Citable as a preprint; the field treats arXiv papers as citable given how
widely they circulate.

---

## 4. GDELT vs. ICEWS Comparison

**Ward, Michael D., Andreas Beger, Josh Cutler, Matthew Dickenson, Cassy Dorff,
and Ben Radford. 2013. "Comparing GDELT and ICEWS Event Data." Working paper,
Duke University.**

Compares GDELT and ICEWS for protest events in Egypt and Turkey. Key finding
relevant to us: GDELT and ICEWS share ~71% of variance for major protest events
after filtering, suggesting the filtered GDELT signal is real. Also documents that
GDELT shows wider geographic variance in geolocation than ICEWS — relevant to the
geolocation reliability discussion.

Cite for one sentence acknowledging that GDELT and independent event databases
converge on major events, supporting the validity of the filtered data. Secondary
citation; Hoffmann et al. is the primary reference.

---

## 5. CAMEO Ontology and Definitional Issues

**Schrodt, Philip A. 2012. "CAMEO: Conflict and Mediation Event Observations Event
and Actor Codebook." Pennsylvania State University.**

The CAMEO codebook underlying GDELT's event classification. Cite when introducing
the CAMEO code 143 (strikes and boycotts) to explain what GDELT is actually coding.
Establishes the definitional scope: CAMEO groups strikes, boycotts, and work
stoppages together as a single event type.

---

## 6. Geolocation Reliability

GDELT's ADM1-level geolocation introduces noise through several well-documented
mechanisms: capital city / dateline bias (national wire stories assigned to capital
rather than event location), multiple location mentions in a single article, and
degraded NER performance for non-English sources.

**Hammond, Grant and Nils B. Weidmann. 2014. "Using Machine-Coded Event Data for
the Micro-level Study of Political Violence." *Journal of Peace Research* 51(4):
493–501. DOI: 10.1177/0022343314531297**

The standard citation for subnational geolocation accuracy in machine-coded event
data. Documents the dateline bias problem directly. *Not currently in the literature
folder — needs to be acquired.*

**How to handle geolocation error in the paper**: Measurement error in the location
variable will attenuate spatial diffusion coefficients toward zero (classical
measurement error in the treatment variable). This works against finding our result,
so it is a conservative bias. Note this explicitly: "To the extent that GDELT
mislabels some strike events to the wrong ADM1 region, our estimates of geographic
neighbor effects are attenuated and should be interpreted as lower bounds."

The country×week fixed effects absorb a substantial portion of the geolocation
concern: capital city bias systematically assigns events to the capital's ADM1
region, but the capital's region is one specific ADM1 unit in a country. Our FE
design identifies from variation *across* ADM1 units within the same country-week,
so bias toward the capital doesn't contaminate the neighbor exposure variable unless
neighboring units are also the capital — which they rarely are.

---

## 7. The Absence of a Gold-Standard Global Strike Database

There is no gold-standard global labor strike database against which GDELT can be
externally validated. The main alternatives:

- **ILO strike statistics**: Country-level annual counts from official labor ministry
  reports. Spotty coverage (many countries don't report; definitions vary by national
  labor law). Could be used for country-year correlation as a robustness check.
- **ETUI (European Trade Union Institute)**: Tracks European strikes with reasonable
  coverage. Not global.
- **Crowd Counting Consortium (CCC)**: US only, 2017 onward, manually coded.
  Explicitly excludes labor strikes from its protest definition — the opposite
  definitional choice from CAMEO. Not usable for external validation.
- **National administrative records**: High quality for specific countries (UK,
  France, Australia) but country-specific and not globally comparable.

**Implication for the paper**: The absence of a global strike database is precisely
the gap this paper addresses — and is part of the substantive motivation for using
GDELT in the first place. Acknowledge directly: "No gold-standard global strike
database exists against which to validate our measure at scale. Our validation
is therefore based on our URL classifier performance (precision/recall from the
validation sample) and on the internal consistency of the panel."

---

## Priority Citations Summary

| Citation | Where to cite | Priority |
|---|---|---|
| Wang et al. 2016 (*Science*) | Data section: false positive baseline | High |
| Leetaru & Schrodt 2013 | Data section: GDELT description | Essential |
| Hoffmann et al. 2022 | Data section: validation motivation and approach | High |
| Halterman & Keith 2025 | Data section: LLM classifier justification | High |
| Halterman et al. 2023 (preprint) | Data section: custom event data methods | Medium |
| Ward et al. 2013 | Data section: GDELT/ICEWS convergence | Medium |
| Schrodt 2012 (CAMEO) | Data section: event coding definition | Medium |
| Hammond & Weidmann 2014 | Data section: geolocation reliability | Medium |

---

## Items Still Needed

1. **Wang et al. (2016)** full citation — track down via Google Scholar. Published
   in *Science*; the 21% false positive figure is the key finding. Not yet in
   bib file.
2. **Hammond & Weidmann (2014)** — now in bib file. Journal confirmed as
   *Research & Politics* 1(2), DOI: 10.1177/2053168014539924.
3. **Leetaru & Schrodt (2013)** — now in bib file.
4. **Precision/recall figures from our URL classifier validation sample** — needed
   to parallel Hoffmann et al.'s P=0.74, R=0.83 and respond to reviewer requests
   for validation evidence.
