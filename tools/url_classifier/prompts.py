"""Prompts, few-shot examples, and message builders for URL classification."""

FEW_SHOT_EXAMPLES = [
    # --- relevant ---
    {
        "url": "https://www.chicagotribune.com/2019/10/17/chicago-teachers-strike-enters-third-day/",
        "classification": "relevant",
        "reasoning": "URL slug explicitly mentions 'teachers-strike'.",
    },
    {
        "url": "https://www.birgun.net/haber/emek-mucadelesi-yine-tehdit-unsuru-sayildi-akpden-23uncu-kez-grev-yasagi-653470",
        "classification": "relevant",
        "reasoning": "Turkish URL contains 'grev-yasagi' (strike ban) and 'emek-mucadelesi' (labor struggle).",
    },
    {
        "url": "https://www.lemonde.fr/societe/article/2023/03/07/greve-du-7-mars-sncf-ratp-enseignants_6164850_3224.html",
        "classification": "relevant",
        "reasoning": "French URL contains 'greve' (strike) and references transport/education workers.",
    },
    {
        "url": "https://www.reviewjournal.com/opinion/editorials/editorial-why-public-employee-strikes-should-be-illegal-3441538/",
        "classification": "relevant",
        "reasoning": "Opinion piece about public employee strikes — article is substantively about strikes.",
    },
    {
        "url": "https://www.thehindu.com/news/national/bank-employees-go-on-two-day-strike-over-wage-revision/article65432100.ece",
        "classification": "relevant",
        "reasoning": "URL slug says 'bank-employees-go-on-two-day-strike'.",
    },
    # --- not_relevant ---
    {
        "url": "https://www.ghanaweb.com/GhanaHomePage/business/Dangote-s-refinery-to-begin-direct-petrol-supply-in-Nigeria-2000578",
        "classification": "not_relevant",
        "reasoning": "Article about oil refinery supply logistics — no strike content indicated.",
    },
    {
        "url": "https://palsolidarity.org/2025/09/the-war-on-the-west-bank-the-open-ambition-to-erase-palestine/",
        "classification": "not_relevant",
        "reasoning": "Article about the Israeli-Palestinian conflict, unrelated to labor strikes.",
    },
    {
        "url": "https://www.bbc.com/sport/football/67890123",
        "classification": "not_relevant",
        "reasoning": "BBC Sport football article — clearly unrelated to labor action.",
    },
    {
        "url": "https://www.reuters.com/world/us/us-inflation-hits-40-year-high-2022-06-10/",
        "classification": "not_relevant",
        "reasoning": "Economic news about inflation — no strike indicated.",
    },
    # --- relevant: strike ended/resolved but still occurred ---
    {
        "url": "https://www.boston.com/news/business/2024/10/30/hundreds-more-striking-boston-hotel-workers-reach-tentative-contract-agreement/",
        "classification": "relevant",
        "reasoning": "Workers were striking and reached an agreement — the strike occurred.",
    },
    {
        "url": "http://bsccomment.com/2016/01/14/why-are-junior-doctors-striking.html",
        "classification": "relevant",
        "reasoning": "URL asks why junior doctors are striking — they are actively striking.",
    },
    # --- not_relevant: strike called off BEFORE it started ---
    {
        "url": "https://www.oann.com/newsroom/ila-strike-suspended-dockworkers-agree-to-delay-walkout/",
        "classification": "not_relevant",
        "reasoning": "Walkout was agreed to be delayed before it began — no strike occurred.",
    },
    {
        "url": "http://www.business-standard.com/article/pti-stories/will-never-abstain-from-work-maha-lawyers-tell-hc-115100900894_1.html",
        "classification": "not_relevant",
        "reasoning": "URL states workers 'will never abstain from work' — explicitly no strike.",
    },
    # --- not_relevant: historical/academic analysis of distant-past strike ---
    {
        "url": "https://dissidentvoice.org/2025/03/civil-workers-uncivil-problem-the-1934-civil-works-administration-strike-in-utica-new-york/",
        "classification": "not_relevant",
        "reasoning": "Article published in 2025 is a historical analysis of a 1934 strike — not a contemporaneous strike event.",
    },
    # --- uncertain: planned/threatened/balloted strike, occurrence unconfirmed ---
    {
        "url": "http://www.independent.ie/irish-news/education/asti-to-ballot-for-strike-action-if-extra-working-hour-leads-to-pay-cut-for-teachers-34733591.html",
        "classification": "uncertain",
        "reasoning": "URL indicates a ballot for strike action — the strike is planned, not confirmed to have occurred.",
    },
    {
        "url": "https://dailypost.ng/2024/10/30/withheld-salaries-nigerian-academic-technologists-to-embark-on-strike-nov-14/",
        "classification": "uncertain",
        "reasoning": "URL indicates a strike planned for a future date (Nov 14) — occurrence not confirmed.",
    },
    # --- uncertain: labor/union mention without a specific strike event ---
    {
        "url": "https://finance.yahoo.com/news/union-workers-hawaiis-largest-hotel-233201022.html",
        "classification": "uncertain",
        "reasoning": "URL mentions union workers at a hotel but does not indicate a strike occurred.",
    },
    {
        "url": "http://www.independent.ie/breaking-news/irish-news/remain-in-eu-to-reduce-air-traffic-control-strikes-urges-ryanair-chief-oleary-34620544.html",
        "classification": "not_relevant",
        "reasoning": "URL is about policy advocacy to reduce strikes, not a report of a specific strike event.",
    },
    # --- uncertain: opaque URLs ---
    {
        "url": "https://www.shorouknews.com/news/view.aspx?cdate=14092025&id=e5d555bc-c2eb-4412-bc26-4c5630345307",
        "classification": "uncertain",
        "reasoning": "URL contains only a date and opaque UUID — no descriptive slug.",
    },
    {
        "url": "https://news.bbc.co.uk/2/hi/business/7654321.stm",
        "classification": "uncertain",
        "reasoning": "BBC News URL with only a numeric ID — content unknowable from URL alone.",
    },
    {
        "url": "https://www.aljazeera.com/economy/2023/5/14/article",
        "classification": "uncertain",
        "reasoning": "Generic Al Jazeera economy URL — no slug describing the article content.",
    },
]

SYSTEM_PROMPT = """\
You are classifying news article URLs to determine whether the article is about \
a labor strike, work stoppage, general strike, or boycott.

Relevant articles include: strikes that are ongoing, strikes that have ended or \
been resolved, strike aftermath, court orders or legal responses during a strike, \
and recent retrospectives on strikes from the past few years. All of these confirm \
a strike occurred in the contemporary period.

Classify each URL as exactly one of:
  relevant      — the URL indicates the article covers a labor strike or work \
stoppage (ongoing, recently resolved, or recent retrospective)
  not_relevant  — the URL clearly indicates an unrelated topic, OR the strike was \
explicitly called off BEFORE it started, OR workers explicitly stated they would \
NOT strike
  uncertain     — the URL is too opaque to determine relevance, OR the strike is \
described as planned/threatened/balloted but it is unclear whether it actually happened

Rules:
- Base your judgment ONLY on the URL string — do not attempt to visit it.
- Recognize strike-related terms in any language \
(e.g., huelga, grève, greve, Streik, grev, sciopero, إضراب, 罢工).
- Military, missile, or lightning strikes → not_relevant.
- A strike that ENDED, was SETTLED, or led to a CONTRACT AGREEMENT still occurred \
→ relevant. Only classify as not_relevant if the strike was called off or averted \
BEFORE it began.
- A strike being SUSPENDED mid-course (after starting) → still relevant.
- Court orders, injunctions, or bans issued DURING a strike → relevant (the strike \
exists).
- Articles explaining WHY workers are striking → relevant (they are striking).
- Academic or purely historical analyses of strikes from the distant past \
(e.g., a 2025 article about a 1934 strike) → not_relevant. The article must \
relate to a contemporaneous or recent strike event.
- Strike PLANNED, THREATENED, or BALLOTED but not confirmed to have started → \
uncertain.
- Hunger strikes, sit-ins, work-to-rule actions, and protest marches are relevant \
ONLY if the participants include workers or unions — including general strikes and \
political strikes called by or involving organized labor. The same action taken solely \
by non-worker actors (e.g., climate activists, political prisoners, students) without \
the participation of workers or unions → not_relevant.
- Union/labor mentions with no specific strike event \
(e.g., "union workers at hotel", "right to strike", "labor strife") → uncertain.
- Policy advocacy about strikes in general → not_relevant.
- Service disruptions without explicit strike mention → uncertain.
- Opaque URLs (numeric IDs, query strings with no descriptive slug) → always \
uncertain, never not_relevant. Use not_relevant only when you can positively \
identify the topic as unrelated.
- When genuinely in doubt, use uncertain.
- Respond with valid JSON only: \
{"classification": "relevant"|"not_relevant"|"uncertain", "reasoning": "<one sentence>"}
"""

PASS2_SYSTEM_PROMPT = """\
You are classifying news articles to determine whether they cover a labor strike, \
work stoppage, general strike, or boycott.

You will receive a URL and, when available, the article's page title. \
Prioritize the title when present — it is more reliable than the URL slug.

Relevant articles include: strikes that are ongoing, strikes that have ended or \
been resolved, strike aftermath, court orders or legal responses during a strike, \
and recent retrospectives on strikes from the past few years. All of these confirm \
a strike occurred in the contemporary period.

Classify as exactly one of:
  relevant      — the URL and/or title indicate the article covers a labor strike or \
work stoppage (ongoing, recently resolved, or recent retrospective)
  not_relevant  — the URL and/or title clearly indicate an unrelated topic, OR the \
strike was explicitly called off BEFORE it started, OR workers explicitly stated they \
would NOT strike
  uncertain     — both the URL and title are insufficient to determine relevance, OR \
the strike is described as planned/threatened/balloted but it is unclear whether it \
actually happened

Rules:
- Recognize strike-related terms in any language \
(e.g., huelga, grève, greve, Streik, grev, sciopero, إضراب, 罢工, zabastovka).
- Military, missile, or lightning strikes → not_relevant.
- A strike that ENDED, was SETTLED, or led to a CONTRACT AGREEMENT still occurred \
→ relevant. Only classify as not_relevant if the strike was called off or averted \
BEFORE it began.
- A strike being SUSPENDED mid-course (after starting) → still relevant.
- Court orders, injunctions, or bans issued DURING a strike → relevant (the strike \
exists).
- Articles explaining WHY workers are striking → relevant (they are striking).
- Academic or purely historical analyses of strikes from the distant past \
(e.g., a 2025 article about a 1934 strike) → not_relevant. The article must \
relate to a contemporaneous or recent strike event.
- Strike PLANNED, THREATENED, or BALLOTED but not confirmed to have started → \
uncertain. Only flip to relevant if the title explicitly confirms the strike began.
- Hunger strikes, sit-ins, work-to-rule actions, and protest marches are relevant \
ONLY if the participants include workers or unions — including general strikes and \
political strikes called by or involving organized labor. The same action taken solely \
by non-worker actors (e.g., climate activists, political prisoners, students) without \
the participation of workers or unions → not_relevant.
- Union/labor mentions with no specific strike event \
(e.g., "union workers at hotel", "right to strike", "labor strife") → uncertain.
- Policy advocacy about strikes in general → not_relevant.
- Service disruptions without explicit strike mention → uncertain.
- When genuinely in doubt, use uncertain.
- Respond with valid JSON only: \
{"classification": "relevant"|"not_relevant"|"uncertain", "reasoning": "<one sentence>"}
"""

PASS2_FEW_SHOT = [
    # title available, clearly relevant
    {
        "url": "https://www.shorouknews.com/news/view.aspx?id=e5d555bc-c2eb",
        "title": "عمال المصنع يضربون عن العمل للمطالبة بزيادة الأجور",
        "classification": "relevant",
        "reasoning": "Arabic title states factory workers are striking for higher wages.",
    },
    {
        "url": "https://news.bbc.co.uk/2/hi/business/7654321.stm",
        "title": "UK bank workers to strike over pay",
        "classification": "relevant",
        "reasoning": "Title explicitly states bank workers will strike.",
    },
    # title available, clearly not relevant
    {
        "url": "https://allafrica.com/stories/202106160173.html",
        "title": "Kenya: Government Announces New Infrastructure Budget",
        "classification": "not_relevant",
        "reasoning": "Title is about a government budget — no labor strike content.",
    },
    {
        "url": "https://www.bellevuereporter.com/news/boeing-renton-plant-to-halt-737-max-production/",
        "title": "Boeing Renton plant to halt 737 MAX production",
        "classification": "not_relevant",
        "reasoning": "Title confirms a production halt due to manufacturing issues, not a labor strike.",
    },
    # title confirms service disruption is strike-caused
    {
        "url": "http://www.couriermail.com.au/news/breaking-news/tram-services-wind-down-across-melbourne/",
        "title": "Melbourne tram services grind to halt as workers strike",
        "classification": "relevant",
        "reasoning": "Title confirms tram disruption is caused by a workers' strike.",
    },
    # title fetched but still generic
    {
        "url": "https://www.standaard.be/cnt/dmf20210925_95688975",
        "title": "Het Laatste Nieuws | De Standaard",
        "classification": "uncertain",
        "reasoning": "Title is just the newspaper homepage name — no article content retrievable.",
    },
    # no title available
    {
        "url": "http://vg-news.ru/n/141450",
        "title": None,
        "classification": "uncertain",
        "reasoning": "URL is opaque and no title could be retrieved.",
    },
]


def build_user_message(url: str) -> str:
    """Build the user turn content for a single URL."""
    shots = "\n".join(
        f'URL: {ex["url"]}\n'
        f'{{"classification": "{ex["classification"]}", "reasoning": "{ex["reasoning"]}"}}'
        for ex in FEW_SHOT_EXAMPLES
    )
    return f"{shots}\n\nURL: {url}"


def build_pass2_user_message(url: str, title: str | None) -> str:
    shots = []
    for ex in PASS2_FEW_SHOT:
        t = ex["title"] if ex["title"] else "(not available)"
        shots.append(
            f'URL: {ex["url"]}\nTitle: {t}\n'
            f'{{"classification": "{ex["classification"]}", "reasoning": "{ex["reasoning"]}"}}'
        )
    title_line = title if title else "(not available)"
    return "\n\n".join(shots) + f"\n\nURL: {url}\nTitle: {title_line}"
