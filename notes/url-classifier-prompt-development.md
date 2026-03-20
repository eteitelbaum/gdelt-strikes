# URL Classifier: Prompt Development and Calibration

## Overview

GDELT event coding uses EventCode 143 (strikes/boycotts) to identify strike
events, but the code is noisy: many captured events are not actually about
labor strikes. To filter the raw dataset of ~30,899 events, we built a
two-pass LLM classification pipeline using OpenAI's gpt-4o-mini via the
Batch API. This note documents the prompt development process, the edge cases
identified through manual review, and the final prompts used in production.

---

## Pipeline Architecture

### Pass 1: URL-only classification

Each event has a `SOURCEURL` field. Pass 1 classifies that URL string alone
into one of three categories:

- **relevant** — the URL indicates the article covers a labor strike or work
  stoppage (ongoing, recently resolved, or recent retrospective)
- **not_relevant** — the URL clearly indicates an unrelated topic, or the
  strike was explicitly averted before it started
- **uncertain** — the URL is too opaque to determine relevance, or the strike
  is described as planned/threatened but unconfirmed

The `uncertain` category feeds into Pass 2 rather than being discarded.

### Pass 2: Title-fetch + reclassification

For events classified as `uncertain` in Pass 1, the pipeline attempts to
fetch the article's HTML `<title>` tag via direct HTTP request, with a
Wayback Machine fallback for dead links. The title and URL are then submitted
together to a second prompt. Events that remain `uncertain` after Pass 2
(typically those with completely opaque URLs and unretrievable pages) are
flagged for separate treatment in the analysis.

**Model:** gpt-4o-mini for both passes
**API method:** OpenAI Batch API (24h completion window, 50% cost discount)
**Estimated cost:** ~$4–5 for Pass 1 on the full 30,899-event dataset;
~$0.70 additional for Pass 2 on the uncertain subset

---

## Calibration Process

Prompt development followed an iterative review cycle:

1. Draft prompt + few-shot examples
2. Run `--test 100` on a fixed random sample (`random_state=99`) for
   apples-to-apples comparison across iterations
3. Manually review all 100 classifications, annotating errors
4. Identify categories of systematic misclassification
5. Add or revise rules and few-shot examples to address them
6. Repeat

The fixed seed ensured each iteration was evaluated on the same 100 URLs.
Test results were saved to `data/test/` with timestamps to preserve the
review history.

### Iteration 1: Baseline

Initial prompt defined only `relevant` and `not_relevant`. Opaque URLs with
numeric IDs (e.g., `shorouknews.com/view.aspx?id=...`, `bbc.co.uk/2/hi/...`)
were being forced into one of two categories — often landing as `not_relevant`
by default when the model had insufficient signal. This was the primary
motivation for introducing the three-way split.

### Iteration 2: Three-way split introduced

Added `uncertain` as a catch-all for opaque URLs and genuinely ambiguous
cases. Initial distribution on 100-URL test: approximately 44% relevant /
26% not_relevant / 30% uncertain.

Key problem identified: the prompt used the phrase "confirmed to have
occurred," which led the model to over-apply `not_relevant`. Articles about
strikes that had been resolved, settled, or ended (all of which confirm the
strike happened) were being misclassified as not_relevant because the strike
was "no longer ongoing."

Fix: rewrote the preamble to explicitly state that resolved, settled, and
aftermath articles are all relevant. Separated the pre-start cancellation
case clearly.

### Iteration 3: Opaque URL rule

Observed that numeric-ID URLs were still occasionally landing in
`not_relevant`. Added an explicit rule: opaque URLs (numeric IDs, query
strings with no descriptive slug) must always be `uncertain`, never
`not_relevant`. `not_relevant` should only be used when the topic can be
positively identified as unrelated.

### Iteration 4: Planned/threatened strikes

Manual review identified articles about strikes that were planned or balloted
but had not yet occurred being classified as `relevant`. Examples:

- `asti-to-ballot-for-strike-action-if-extra-working-hour...` → should be
  `uncertain` (ballot announced, strike not confirmed)
- `nigerian-academic-technologists-to-embark-on-strike-nov-14` → should be
  `uncertain` (future date, occurrence unconfirmed)

Added rule: Strike PLANNED, THREATENED, or BALLOTED but not confirmed to have
started → `uncertain`. Added both URLs as few-shot examples.

Separately identified the inverse error: strikes suspended or averted
*after* they started were being treated as `not_relevant`. Added rule: a
strike being SUSPENDED mid-course (after starting) is still relevant.
Added `oann.com/ila-strike-suspended-dockworkers-agree-to-delay-walkout/` as
a `not_relevant` few-shot example (walkout was delayed *before* it began).

### Iteration 5: Pass 2 prompt parity

Discovered that the Pass 2 system prompt was substantially shorter than
Pass 1 and was missing several rules, causing inconsistent behavior between
passes. Specifically: planned strikes that were correctly held as `uncertain`
in Pass 1 were flipping to `relevant` in Pass 2 because Pass 2 had no
instruction to keep them uncertain.

Fix: rewrote Pass 2 prompt to carry the full rule set from Pass 1, with two
Pass-2-specific additions: (a) prioritize the article title over the URL slug
when both are present, and (b) only flip a planned strike to `relevant` if
the title explicitly confirms the strike began.

### Iteration 6: Worker vs. non-worker protests

Observed that the prompt was producing correct results for labor hunger
strikes and sit-ins but was incorrectly classifying hunger strikes by
non-labor actors (e.g., climate activists) as `relevant`. The initial fix
used the phrase "labor dispute," which was too narrow — it would exclude
general strikes and political strikes called by unions, which are clearly
in scope.

Final rule: hunger strikes, sit-ins, work-to-rule actions, and protest
marches are relevant ONLY if the participants include workers or unions
(including general strikes and political strikes called by or involving
organized labor). The same action by non-worker actors (climate activists,
political prisoners, students) → `not_relevant`.

### Iteration 7: Historical strikes

Observed that a 2025 article providing an academic analysis of a 1934 strike
(`dissidentvoice.org/2025/03/civil-workers-uncivil-problem-the-1934-civil-works-administration-strike-in-utica-new-york/`)
was classified as `relevant`. The original prompt explicitly listed
"historical accounts of past strikes" as relevant — this was intended for
recent retrospectives (e.g., "the 2023 teachers strike, which ended last
month"), not academic analyses of events from decades ago.

Fix: changed "historical accounts of past strikes" to "recent retrospectives
on strikes from the past few years." Added explicit rule: academic or purely
historical analyses of strikes from the distant past → `not_relevant`. Added
the 1934 dissidentvoice URL as a `not_relevant` few-shot example.

---

## Final Classification Distribution (100-URL test, `random_state=99`)

After full calibration:

| Category      | Count | Share |
|---------------|-------|-------|
| relevant      | 43    | 43%   |
| not_relevant  | 28    | 28%   |
| uncertain     | 29    | 29%   |

Pass 2 on the 29 uncertain events (with title fetching):

| Reclassified to | Count |
|-----------------|-------|
| relevant        | ~8    |
| not_relevant    | ~3    |
| remains uncertain | ~18 |

The residual uncertain events after Pass 2 are predominantly opaque URLs
(numeric IDs, query strings) where the article is no longer accessible and
the Wayback Machine either has no snapshot or returns a paywalled/blocked
page.

---

## Known Residual Edge Cases

**Stub/comment pages that resemble opaque URLs.** URLs like
`progressive.org/comment/5109` have a path structure that the model reads as
a potential stub, leading it toward `not_relevant` rather than `uncertain`.
The opaque-URL rule should catch these but does not always override the
model's domain-based inference. No fix was found that did not create new
false positives.

**Wayback Machine title inconsistency.** Titles retrieved from archived
snapshots occasionally reflect the state of the page at archival time, which
may differ from publication time (e.g., homepage titles, redirect pages). The
`title_source` column in the Pass 2 output distinguishes `direct`, `wayback`,
and `none` for downstream review.

**Remaining uncertain events.** Events that are still `uncertain` after
Pass 2 should be treated as missing data rather than irrelevant. They
disproportionately represent paywalled, non-English, and older sources where
the URL slug is uninformative and the page is no longer accessible. Their
distribution across countries and time periods should be checked to ensure
they do not systematically bias the final dataset.

---

## Final Prompts

### Pass 1 System Prompt

```
You are classifying news article URLs to determine whether the article is about
a labor strike, work stoppage, general strike, or boycott.

Relevant articles include: strikes that are ongoing, strikes that have ended or
been resolved, strike aftermath, court orders or legal responses during a strike,
and recent retrospectives on strikes from the past few years. All of these confirm
a strike occurred in the contemporary period.

Classify each URL as exactly one of:
  relevant      — the URL indicates the article covers a labor strike or work
stoppage (ongoing, recently resolved, or recent retrospective)
  not_relevant  — the URL clearly indicates an unrelated topic, OR the strike was
explicitly called off BEFORE it started, OR workers explicitly stated they would
NOT strike
  uncertain     — the URL is too opaque to determine relevance, OR the strike is
described as planned/threatened/balloted but it is unclear whether it actually happened

Rules:
- Base your judgment ONLY on the URL string — do not attempt to visit it.
- Recognize strike-related terms in any language
  (e.g., huelga, grève, greve, Streik, grev, sciopero, إضراب, 罢工).
- Military, missile, or lightning strikes → not_relevant.
- A strike that ENDED, was SETTLED, or led to a CONTRACT AGREEMENT still occurred
  → relevant. Only classify as not_relevant if the strike was called off or averted
  BEFORE it began.
- A strike being SUSPENDED mid-course (after starting) → still relevant.
- Court orders, injunctions, or bans issued DURING a strike → relevant (the strike
  exists).
- Articles explaining WHY workers are striking → relevant (they are striking).
- Academic or purely historical analyses of strikes from the distant past
  (e.g., a 2025 article about a 1934 strike) → not_relevant. The article must
  relate to a contemporaneous or recent strike event.
- Strike PLANNED, THREATENED, or BALLOTED but not confirmed to have started →
  uncertain.
- Hunger strikes, sit-ins, work-to-rule actions, and protest marches are relevant
  ONLY if the participants include workers or unions — including general strikes and
  political strikes called by or involving organized labor. The same action taken
  solely by non-worker actors (e.g., climate activists, political prisoners,
  students) without the participation of workers or unions → not_relevant.
- Union/labor mentions with no specific strike event
  (e.g., "union workers at hotel", "right to strike", "labor strife") → uncertain.
- Policy advocacy about strikes in general → not_relevant.
- Service disruptions without explicit strike mention → uncertain.
- Opaque URLs (numeric IDs, query strings with no descriptive slug) → always
  uncertain, never not_relevant. Use not_relevant only when you can positively
  identify the topic as unrelated.
- When genuinely in doubt, use uncertain.
- Respond with valid JSON only:
  {"classification": "relevant"|"not_relevant"|"uncertain", "reasoning": "<one sentence>"}
```

### Pass 1 Few-Shot Examples

| URL | Classification | Reasoning |
|-----|---------------|-----------|
| chicagotribune.com/.../chicago-teachers-strike-enters-third-day/ | relevant | URL slug explicitly mentions 'teachers-strike'. |
| birgun.net/.../grev-yasagi-... | relevant | Turkish URL contains 'grev-yasagi' (strike ban). |
| lemonde.fr/.../greve-du-7-mars-... | relevant | French URL contains 'greve' (strike). |
| reviewjournal.com/.../why-public-employee-strikes-should-be-illegal/ | relevant | Opinion piece substantively about strikes. |
| thehindu.com/.../bank-employees-go-on-two-day-strike/ | relevant | URL slug says 'bank-employees-go-on-two-day-strike'. |
| boston.com/.../striking-boston-hotel-workers-reach-tentative-contract-agreement/ | relevant | Workers were striking and reached agreement — strike occurred. |
| bsccomment.com/.../why-are-junior-doctors-striking.html | relevant | URL asks why doctors are striking — they are actively striking. |
| ghanaweb.com/.../Dangote-s-refinery-to-begin-direct-petrol-supply/ | not_relevant | Oil refinery supply logistics — no strike content. |
| palsolidarity.org/.../the-war-on-the-west-bank/ | not_relevant | Israeli-Palestinian conflict, unrelated to labor strikes. |
| bbc.com/sport/football/67890123 | not_relevant | BBC Sport football — clearly unrelated. |
| reuters.com/.../us-inflation-hits-40-year-high/ | not_relevant | Economic news about inflation — no strike indicated. |
| oann.com/.../ila-strike-suspended-dockworkers-agree-to-delay-walkout/ | not_relevant | Walkout delayed before it began — no strike occurred. |
| business-standard.com/.../will-never-abstain-from-work/ | not_relevant | Workers explicitly stated they would not strike. |
| dissidentvoice.org/2025/03/.../1934-civil-works-administration-strike/ | not_relevant | 2025 article about a 1934 strike — not a contemporaneous event. |
| independent.ie/.../asti-to-ballot-for-strike-action/ | uncertain | Ballot announced — strike planned, not confirmed. |
| dailypost.ng/.../to-embark-on-strike-nov-14/ | uncertain | Future date — strike not yet confirmed to have occurred. |
| finance.yahoo.com/.../union-workers-hawaiis-largest-hotel/ | uncertain | Union workers mentioned but no strike indicated. |
| independent.ie/.../remain-in-eu-to-reduce-air-traffic-control-strikes/ | not_relevant | Policy advocacy to reduce strikes, not a strike report. |
| shorouknews.com/view.aspx?cdate=...&id=uuid | uncertain | Only a date and opaque UUID — no descriptive slug. |
| news.bbc.co.uk/2/hi/business/7654321.stm | uncertain | Numeric ID only — content unknowable from URL alone. |
| aljazeera.com/economy/2023/5/14/article | uncertain | Generic economy URL — no descriptive slug. |

### Pass 2 System Prompt

```
You are classifying news articles to determine whether they cover a labor strike,
work stoppage, general strike, or boycott.

You will receive a URL and, when available, the article's page title.
Prioritize the title when present — it is more reliable than the URL slug.

Relevant articles include: strikes that are ongoing, strikes that have ended or
been resolved, strike aftermath, court orders or legal responses during a strike,
and recent retrospectives on strikes from the past few years. All of these confirm
a strike occurred in the contemporary period.

Classify as exactly one of:
  relevant      — the URL and/or title indicate the article covers a labor strike or
work stoppage (ongoing, recently resolved, or recent retrospective)
  not_relevant  — the URL and/or title clearly indicate an unrelated topic, OR the
strike was explicitly called off BEFORE it started, OR workers explicitly stated
they would NOT strike
  uncertain     — both the URL and title are insufficient to determine relevance, OR
the strike is described as planned/threatened/balloted but it is unclear whether it
actually happened

Rules:
- Recognize strike-related terms in any language
  (e.g., huelga, grève, greve, Streik, grev, sciopero, إضراب, 罢工, zabastovka).
- Military, missile, or lightning strikes → not_relevant.
- A strike that ENDED, was SETTLED, or led to a CONTRACT AGREEMENT still occurred
  → relevant. Only classify as not_relevant if the strike was called off or averted
  BEFORE it began.
- A strike being SUSPENDED mid-course (after starting) → still relevant.
- Court orders, injunctions, or bans issued DURING a strike → relevant (the strike
  exists).
- Articles explaining WHY workers are striking → relevant (they are striking).
- Academic or purely historical analyses of strikes from the distant past
  (e.g., a 2025 article about a 1934 strike) → not_relevant. The article must
  relate to a contemporaneous or recent strike event.
- Strike PLANNED, THREATENED, or BALLOTED but not confirmed to have started →
  uncertain. Only flip to relevant if the title explicitly confirms the strike began.
- Hunger strikes, sit-ins, work-to-rule actions, and protest marches are relevant
  ONLY if the participants include workers or unions — including general strikes and
  political strikes called by or involving organized labor. The same action taken
  solely by non-worker actors (e.g., climate activists, political prisoners,
  students) without the participation of workers or unions → not_relevant.
- Union/labor mentions with no specific strike event → uncertain.
- Policy advocacy about strikes in general → not_relevant.
- Service disruptions without explicit strike mention → uncertain.
- When genuinely in doubt, use uncertain.
- Respond with valid JSON only:
  {"classification": "relevant"|"not_relevant"|"uncertain", "reasoning": "<one sentence>"}
```

### Pass 2 Few-Shot Examples

| URL | Title | Classification | Reasoning |
|-----|-------|---------------|-----------|
| shorouknews.com/...opaque... | عمال المصنع يضربون عن العمل... | relevant | Arabic title states factory workers are striking. |
| news.bbc.co.uk/.../7654321.stm | UK bank workers to strike over pay | relevant | Title explicitly states workers will strike. |
| allafrica.com/stories/202106160173.html | Kenya: Government Announces New Infrastructure Budget | not_relevant | Government budget — no labor strike content. |
| bellevuereporter.com/.../boeing-renton-plant-to-halt-737-max-production/ | Boeing Renton plant to halt 737 Max production | not_relevant | Production halt due to manufacturing issues, not a strike. |
| couriermail.com.au/.../tram-services-wind-down-across-melbourne/ | Melbourne tram services grind to halt as workers strike | relevant | Title confirms tram disruption caused by workers' strike. |
| standaard.be/.../dmf20210925_95688975 | Het Laatste Nieuws \| De Standaard | uncertain | Title is the newspaper homepage name — no article content. |
| vg-news.ru/n/141450 | (not available) | uncertain | Opaque URL and no title retrieved. |

---

## Implementation Notes

The pipeline is implemented as a Python package at `tools/url_classifier/`
with the following modules:

- `prompts.py` — system prompts, few-shot examples, message builders
- `batch.py` — OpenAI Batch API plumbing (prepare/submit/status/collect)
- `fetch.py` — concurrent title fetching with Wayback Machine fallback
- `data.py` — path constants and parquet/CSV I/O
- `classify.py` — CLI entry point

Run from the repo root with the virtual environment activated:

```bash
source .venv/bin/activate
python -m tools.url_classifier --prepare    # build batch JSONL
python -m tools.url_classifier --submit     # upload and submit
python -m tools.url_classifier --status     # poll status
python -m tools.url_classifier --collect    # download results → CSV
python -m tools.url_classifier --pass2-prepare  # fetch titles + build pass2
python -m tools.url_classifier --pass2-submit
python -m tools.url_classifier --pass2-collect
```

Output: `data/enhanced/url_classifications.csv` with columns
`GLOBALEVENTID`, `source_url`, `classification`, `reasoning`.
