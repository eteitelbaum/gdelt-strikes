# Appendix: LLM Classifier Prompts

> **Status**: Draft for integration into `contagion-paper.qmd` appendix.
> These are the exact system prompts and few-shot examples used in each
> validation stage. Format as Quarto code blocks (` ```{} `) or as a
> verbatim LaTeX listing depending on how the appendix is structured.

---

## Stage 1: URL Classifier (GPT-4o mini)

The URL classifier runs in two passes. Pass 1 uses the source URL alone. Pass 2
re-submits uncertain cases with the article headline added when available.

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
                  explicitly called off BEFORE it started, OR workers explicitly
                  stated they would NOT strike
  uncertain     — the URL is too opaque to determine relevance, OR the strike is
                  described as planned/threatened/balloted but it is unclear
                  whether it actually happened

Rules:
- Base your judgment ONLY on the URL string — do not attempt to visit it.
- Recognize strike-related terms in any language
  (e.g., huelga, grève, greve, Streik, grev, sciopero, إضراب, 罢工).
- Military, missile, or lightning strikes → not_relevant.
- A strike that ENDED, was SETTLED, or led to a CONTRACT AGREEMENT still
  occurred → relevant. Only classify as not_relevant if the strike was called
  off or averted BEFORE it began.
- A strike being SUSPENDED mid-course (after starting) → still relevant.
- Court orders, injunctions, or bans issued DURING a strike → relevant.
- Articles explaining WHY workers are striking → relevant.
- Academic or purely historical analyses of strikes from the distant past
  (e.g., a 2025 article about a 1934 strike) → not_relevant.
- Strike PLANNED, THREATENED, or BALLOTED but not confirmed to have started
  → uncertain.
- Hunger strikes, sit-ins, work-to-rule actions, and protest marches are
  relevant ONLY if the participants include workers or unions. The same action
  taken solely by non-worker actors (e.g., climate activists, political
  prisoners, students) without the participation of workers or unions
  → not_relevant.
- Union/labor mentions with no specific strike event → uncertain.
- Policy advocacy about strikes in general → not_relevant.
- Service disruptions without explicit strike mention → uncertain.
- Opaque URLs (numeric IDs, query strings with no descriptive slug) → always
  uncertain, never not_relevant.
- When genuinely in doubt, use uncertain.
- Respond with valid JSON only:
  {"classification": "relevant"|"not_relevant"|"uncertain", "reasoning": "<one sentence>"}
```

### Pass 1 Few-Shot Examples

| URL | Classification | Reasoning |
|---|---|---|
| `chicagotribune.com/.../chicago-teachers-strike-enters-third-day/` | relevant | URL slug explicitly mentions 'teachers-strike'. |
| `birgun.net/.../grev-yasagi-...` | relevant | Turkish URL contains 'grev-yasagi' (strike ban) and 'emek-mucadelesi' (labor struggle). |
| `lemonde.fr/.../greve-du-7-mars-sncf-ratp-enseignants_...` | relevant | French URL contains 'greve' (strike) and references transport/education workers. |
| `reviewjournal.com/.../why-public-employee-strikes-should-be-illegal/` | relevant | Opinion piece substantively about strikes. |
| `thehindu.com/.../bank-employees-go-on-two-day-strike-over-wage-revision/` | relevant | URL slug says 'bank-employees-go-on-two-day-strike'. |
| `ghanaweb.com/.../Dangote-s-refinery-to-begin-direct-petrol-supply/` | not_relevant | Article about oil refinery supply logistics — no strike content indicated. |
| `palsolidarity.org/.../the-war-on-the-west-bank.../` | not_relevant | Article about the Israeli-Palestinian conflict, unrelated to labor strikes. |
| `bbc.com/sport/football/67890123` | not_relevant | BBC Sport football article — clearly unrelated to labor action. |
| `reuters.com/.../us-inflation-hits-40-year-high/` | not_relevant | Economic news about inflation — no strike indicated. |
| `boston.com/.../striking-boston-hotel-workers-reach-tentative-contract-agreement/` | relevant | Workers were striking and reached an agreement — the strike occurred. |
| `bsccomment.com/.../why-are-junior-doctors-striking.html` | relevant | URL asks why junior doctors are striking — they are actively striking. |
| `oann.com/.../ila-strike-suspended-dockworkers-agree-to-delay-walkout/` | not_relevant | Walkout was agreed to be delayed before it began — no strike occurred. |
| `business-standard.com/.../will-never-abstain-from-work-maha-lawyers.../` | not_relevant | URL states workers 'will never abstain from work' — explicitly no strike. |
| `dissidentvoice.org/.../the-1934-civil-works-administration-strike-in-utica.../` | not_relevant | 2025 article about a 1934 strike — historical analysis, not a contemporaneous event. |
| `independent.ie/.../asti-to-ballot-for-strike-action.../` | uncertain | A ballot for strike action — the strike is planned, not confirmed. |
| `dailypost.ng/.../nigerian-academic-technologists-to-embark-on-strike-nov-14/` | uncertain | Strike planned for a future date — occurrence not confirmed. |
| `finance.yahoo.com/.../union-workers-hawaiis-largest-hotel.../` | uncertain | Mentions union workers but does not indicate a strike occurred. |
| `shorouknews.com/news/view.aspx?cdate=...&id=...` | uncertain | URL contains only a date and opaque ID — no descriptive slug. |
| `news.bbc.co.uk/2/hi/business/7654321.stm` | uncertain | BBC News URL with only a numeric ID — content unknowable from URL alone. |
| `aljazeera.com/economy/2023/5/14/article` | uncertain | Generic economy URL — no slug describing article content. |

### Pass 2 System Prompt

Pass 2 re-submits uncertain cases with the article headline added when it can be retrieved.

```
You are classifying news articles to determine whether they cover a labor strike,
work stoppage, general strike, or boycott.

You will receive a URL and, when available, the article's page title.
Prioritize the title when present — it is more reliable than the URL slug.

[Classification categories and rules identical to Pass 1, with the following
additions:]

- Strike PLANNED, THREATENED, or BALLOTED but not confirmed to have started
  → uncertain. Only flip to relevant if the title explicitly confirms the
  strike began.
- Respond with valid JSON only:
  {"classification": "relevant"|"not_relevant"|"uncertain", "reasoning": "<one sentence>"}
```

### Pass 2 Few-Shot Examples

| URL | Title | Classification | Reasoning |
|---|---|---|---|
| `shorouknews.com/...` | "عمال المصنع يضربون عن العمل للمطالبة بزيادة الأجور" | relevant | Arabic title states factory workers are striking for higher wages. |
| `news.bbc.co.uk/.../7654321.stm` | "UK bank workers to strike over pay" | relevant | Title explicitly states bank workers will strike. |
| `allafrica.com/stories/...` | "Kenya: Government Announces New Infrastructure Budget" | not_relevant | Title is about a government budget — no labor strike content. |
| `bellevuereporter.com/.../boeing-renton-plant-to-halt-737-max-production/` | "Boeing Renton plant to halt 737 MAX production" | not_relevant | Title confirms a production halt due to manufacturing issues, not a labor strike. |
| `couriermail.com.au/.../tram-services-wind-down-across-melbourne/` | "Melbourne tram services grind to halt as workers strike" | relevant | Title confirms tram disruption is caused by a workers' strike. |
| `standaard.be/cnt/dmf20210925_...` | "Het Laatste Nieuws \| De Standaard" | uncertain | Title is just the newspaper homepage name — no article content. |
| `vg-news.ru/n/141450` | *(not available)* | uncertain | URL is opaque and no title could be retrieved. |

---

## Stage 2: Geocode Validator (GPT-5 mini)

### System Prompt

```
You are a geolocation validator for GDELT strike event data. For each event you
receive: a GDELT geocode (the location GDELT assigned to the event), the source
URL, and any available article text. Your task is to determine whether the GDELT
geocode correctly identifies where the strike occurred.

Output a JSON object with exactly these four fields:
  "extracted_location" : where the strike actually occurred per the article
                         (city and/or region and country). Use "unknown" if
                         you cannot determine this.
  "match"              : "yes", "no", or "uncertain"
  "corrected_location" : when match is "no", the correct location in the
                         format "City, Region, Country" or "Region, Country".
                         Use null when match is "yes" or "uncertain".
  "reasoning"          : one sentence explaining your judgment.

--- RULES ---

yes — The article confirms the strike occurred in the geocoded location or
      immediately adjacent area.

no  — The article clearly states the strike occurred in a different location
      than the GDELT geocode.

uncertain — Use when:
  • The article is inaccessible (broken link, paywall) AND the URL slug does
    not unambiguously name a specific location
  • The strike is described as nationwide or multi-city and no single region
    can be confirmed
  • The article is accessible but does not mention a specific enough location
    to confirm or contradict the geocode

Important:
  • You can read and extract locations from articles in any language.
    Non-English text is not a reason to return "uncertain".
  • Do not use the news outlet's home country or city as a location signal.
  • Do use the article dateline as a reliable location signal.
  • GDELT frequently assigns events to capital cities when the actual location
    is elsewhere. Be alert to this pattern.
  • For nationwide or general strikes, return "uncertain" rather than "no",
    even if GDELT assigned the capital.
  • If the article is inaccessible but the URL slug or title unambiguously
    names a specific city or region, use that to determine the match.
    - Slug/title matches geocode → "yes"
    - Slug/title names a clearly different location → "no" with
      corrected_location set accordingly
    - Return "uncertain" only when the slug names just a country or is
      otherwise too vague.
```

### Few-Shot Examples

| GDELT Geocode | URL / Article | Match | Corrected Location | Reasoning |
|---|---|---|---|---|
| Sydney, NSW, Australia | Strike at Westmead Hospital, Sydney (body text confirms) | yes | — | Article confirms strike at Westmead Hospital in Sydney. |
| Sudbury, Ontario, Canada | `sudbury-miners-go-on-strike-after-rejecting-deal-from-vale-canada` (inaccessible) | yes | — | URL slug unambiguously names Sudbury. |
| Colombo, Western, Sri Lanka | Article dateline "COLOMBO, Sri Lanka — Postal workers staged a protest..." | yes | — | Dateline confirms Colombo. |
| Paris, Île-de-France, France | French article: SNCF workers striking in "région parisienne" | yes | — | Article confirms Paris region. |
| Buenos Aires, Argentina | Spanish article: teachers striking in "Ciudad de Buenos Aires" | yes | — | Article confirms Buenos Aires. |
| Amman, Jordan | Arabic article: teachers striking in "عمان" (Amman) | yes | — | Arabic text confirms Amman. |
| São Paulo, Brazil | Portuguese article: metalworkers striking in São Paulo metropolitan area | yes | — | Article confirms São Paulo region. |
| Kabul, Afghanistan | Title: "Samangan Doctors on Strike, Demand Pending Salaries" | no | Samangan, Afghanistan | Title names Samangan; GDELT assigned Kabul (capital city bias). |
| University of Botswana, South East | Article: strike at BIUST in Palapye, Central District | no | Palapye, Central District, Botswana | GDELT confused BIUST with University of Botswana in Gaborone. |
| Saint-Denis, Reunion | French article: garbage collectors' strike in Marseille | no | Marseille, Provence-Alpes-Côte d'Azur, France | GDELT assigned outlet's home location (Reunion) rather than strike site. |
| Luanda, Angola | `angolan-teachers-begin-threeday-strike-over-wages` (inaccessible) | uncertain | — | URL identifies only the country; cannot confirm or contradict Luanda. |
| Naypyidaw, Myanmar | Article: nationwide general strike across Yangon, Mandalay, and dozens of cities | uncertain | — | Nationwide strike; assigning to a single region is not meaningful. |
| Karingal, Victoria, Australia | Paywalled snippet: aged care staff at Baptcare striking | uncertain | — | Baptcare operates across multiple states; snippet insufficient to confirm location. |
