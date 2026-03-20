"""System prompt, few-shot examples, and message builder for geo validation."""

SYSTEM_PROMPT = """\
You are a geolocation validator for GDELT strike event data. For each
event you receive: a GDELT geocode (the location GDELT assigned to the
event), the source URL, and any available article text. Your task is to
determine whether the GDELT geocode correctly identifies where the strike
occurred.

Output a JSON object with exactly these four fields:
  "extracted_location" : where the strike actually occurred per the
                         article (city and/or region and country).
                         Use "unknown" if you cannot determine this.
  "match"              : "yes", "no", or "uncertain"
  "corrected_location" : when match is "no", the correct location in the
                         format "City, Region, Country" or "Region, Country".
                         Use null when match is "yes" or "uncertain".
  "reasoning"          : one sentence explaining your judgment.

--- RULES ---

yes — The article confirms the strike occurred in the geocoded location
or immediately adjacent area.

no — The article clearly states the strike occurred in a different
location than the GDELT geocode.

uncertain — Use when:
  • The article is inaccessible (broken link, paywall) AND the URL slug
    does not unambiguously name a specific location
  • The strike is described as nationwide or multi-city and no single
    ADM1 region can be confirmed
  • The article is accessible but does not mention a specific enough
    location to confirm or contradict the geocode

Important:
  • You can read and extract locations from articles in any language.
    Non-English text is not a reason to return "uncertain".
  • Do not use the news outlet's home country or city as a location
    signal — a Reunion-based outlet reporting on a Marseille strike
    should be geocoded to Marseille, not Reunion.
  • Do use the article dateline (the location line that appears after
    the byline and before the article text, e.g. "MARSEILLE, France —")
    as a reliable location signal.
  • GDELT frequently assigns events to capital cities when the actual
    location is elsewhere. Be alert to this pattern.
  • For nationwide or general strikes, return "uncertain" rather than
    "no", even if GDELT assigned the capital.
  • If only a title is available, use both the URL slug and title together.
  • If the article is inaccessible but the URL slug or title unambiguously
    names a specific city or region, use that to determine the match —
    do not default to "uncertain" just because the article body is missing.
    - If the slug/title names the same location as the geocode → "yes"
    - If the slug/title names a clearly different location → "no" with
      corrected_location set accordingly
    Examples: "sudbury-miners-go-on-strike" confirms Sudbury;
    "flights-cancelled-at-geneva-airport" contradicts a Copenhagen geocode;
    "greve-des-eboueurs-a-marseille" contradicts a Reunion geocode.
    Return "uncertain" only when the slug names just a country or is
    otherwise too vague to confirm or contradict a specific location.\
"""

# ---------------------------------------------------------------------------
# Few-shot examples
# ---------------------------------------------------------------------------

FEW_SHOT_EXAMPLES = [
    # 1. match — English, body text confirms location
    {
        "user": """\
GDELT geocode: Sydney, New South Wales, Australia
URL: https://cpa.org.au/guardian/issue-2152/strike-at-sydneys-westmead-hospital/
Article text:
Workers at Westmead Hospital in western Sydney walked off the job Monday \
in a dispute over staffing levels and pay. The strike, organised by the \
Health Services Union, left the hospital operating on minimum staffing. \
Nurses and orderlies gathered outside the Westmead campus throughout the day.\
""",
        "assistant": """\
{"extracted_location": "Sydney, New South Wales, Australia", "match": "yes", \
"corrected_location": null, \
"reasoning": "Article confirms the strike took place at Westmead Hospital in \
Sydney, consistent with the GDELT geocode."}\
""",
    },

    # 2. match — English, URL slug sufficient (article inaccessible)
    {
        "user": """\
GDELT geocode: Sudbury, Ontario, Canada
URL: https://www.timescolonist.com/sudbury-miners-go-on-strike-after-rejecting-deal-from-vale-canada-1.24325523
Article text:
Not available.\
""",
        "assistant": """\
{"extracted_location": "Sudbury, Ontario, Canada", "match": "yes", \
"corrected_location": null, \
"reasoning": "Article is inaccessible but the URL slug \
('sudbury-miners-go-on-strike') unambiguously names Sudbury as the \
location of the strike."}\
""",
    },

    # 3. match — dateline as location signal
    {
        "user": """\
GDELT geocode: Colombo, Western, Sri Lanka
URL: http://www.adaderana.lk/news.php?nid=48132
Article text:
COLOMBO, Sri Lanka — Postal workers staged a protest Monday blocking \
the road near the Central Mail Exchange in Fort, Colombo. The workers \
are demanding salary increases and better working conditions. Union \
leaders said the action would continue until the government responds \
to their demands.\
""",
        "assistant": """\
{"extracted_location": "Colombo, Western Province, Sri Lanka", "match": "yes", \
"corrected_location": null, \
"reasoning": "Article dateline and body both confirm the protest took place \
at the Central Mail Exchange in Colombo, consistent with the GDELT geocode."}\
""",
    },

    # 4. match — French
    {
        "user": """\
GDELT geocode: Paris, Île-de-France, France
URL: http://www.lefigaro.fr/flash-eco/2018/03/22/cheminots-greve-sncf-paris
Article text:
Les cheminots de la SNCF ont lancé ce jeudi une grève de deux jours \
contre la réforme ferroviaire du gouvernement. Des milliers de travailleurs \
ont cessé le travail en région parisienne, perturbant fortement le trafic \
dans la capitale. Le syndicat CGT-Cheminots a annoncé que le mouvement est \
particulièrement suivi à Paris et en banlieue.\
""",
        "assistant": """\
{"extracted_location": "Paris, Île-de-France, France", "match": "yes", \
"corrected_location": null, \
"reasoning": "Article describes SNCF railway workers striking in the Paris \
region (région parisienne), consistent with the GDELT geocode."}\
""",
    },

    # 5. match — Spanish
    {
        "user": """\
GDELT geocode: Buenos Aires, Distrito Federal, Argentina
URL: https://www.infobae.com/sociedad/2019/04/30/paro-docente-ciudad-buenos-aires
Article text:
Los docentes de la Ciudad de Buenos Aires realizaron este martes un paro \
de 24 horas en reclamo de una recomposición salarial urgente. La medida fue \
acatada por el 85% del personal en las escuelas públicas porteñas. Los \
manifestantes se concentraron frente al Ministerio de Educación en el \
centro de la ciudad.\
""",
        "assistant": """\
{"extracted_location": "Buenos Aires, Argentina", "match": "yes", \
"corrected_location": null, \
"reasoning": "Article describes teachers striking in the City of Buenos Aires \
(Ciudad de Buenos Aires), confirming the GDELT geocode."}\
""",
    },

    # 6. match — Arabic
    {
        "user": """\
GDELT geocode: Amman, Jordan
URL: https://www.alghad.com/articles/2018/06/06/jordan-teachers-strike
Article text:
أعلن آلاف المعلمين الأردنيين الإضراب عن العمل في عمان احتجاجاً على \
تأخر صرف الرواتب. وتجمع المضربون أمام مقر نقابة المعلمين في وسط \
العاصمة الأردنية، حيث رفعوا لافتات تطالب الحكومة بالاستجابة لمطالبهم.\
""",
        "assistant": """\
{"extracted_location": "Amman, Jordan", "match": "yes", \
"corrected_location": null, \
"reasoning": "Article (Arabic) describes Jordanian teachers striking in \
Amman (عمان), the capital, consistent with the GDELT geocode."}\
""",
    },

    # 7. match — Portuguese
    {
        "user": """\
GDELT geocode: São Paulo, São Paulo, Brazil
URL: https://www.folha.uol.com.br/mercado/2021/05/metalurgicos-sao-paulo-greve.shtml
Article text:
Metalúrgicos do ABC Paulista e da Grande São Paulo cruzaram os braços \
nesta segunda-feira em protesto contra demissões em massa na indústria \
automobilística. A paralisação afetou fábricas na região metropolitana \
de São Paulo, com cerca de 30 mil trabalhadores aderindo ao movimento, \
segundo os sindicatos da categoria.\
""",
        "assistant": """\
{"extracted_location": "São Paulo, Brazil", "match": "yes", \
"corrected_location": null, \
"reasoning": "Article (Portuguese) describes metalworkers striking across \
the São Paulo metropolitan region, consistent with the GDELT geocode."}\
""",
    },

    # 8. mismatch — capital city bias (from user annotations)
    {
        "user": """\
GDELT geocode: Kabul, Kabol, Afghanistan
URL: http://www.outlookafghanistan.net/national_detail.php?post_id=25391
Article text:
Title: Samangan Doctors on Strike, Demand Pending Salaries - The Daily Outlook Afghanistan\
""",
        "assistant": """\
{"extracted_location": "Samangan, Afghanistan", "match": "no", \
"corrected_location": "Samangan, Afghanistan", \
"reasoning": "Article title names Samangan province as the location of the \
doctors' strike; GDELT incorrectly assigned the event to Kabul — a common \
capital-city geocoding bias."}\
""",
    },

    # 9. mismatch — institution confused with similarly-named one (from user annotations)
    {
        "user": """\
GDELT geocode: University of Botswana, South East, Botswana
URL: https://www.sundaystandard.info/mosotho-student-injured-during-biust-strike/
Article text:
A student was injured during a strike at the Botswana International \
University of Science and Technology (BIUST) in Palapye. Students at \
the institution in the Central District had been striking for three days \
over unpaid stipends before the incident occurred.\
""",
        "assistant": """\
{"extracted_location": "Palapye, Central District, Botswana", "match": "no", \
"corrected_location": "Palapye, Central District, Botswana", \
"reasoning": "Article places the strike at BIUST in Palapye, Central District; \
GDELT misassigned it to the South East district, likely confusing BIUST with \
the University of Botswana in Gaborone."}\
""",
    },

    # 10. mismatch — outlet's home country incorrectly used as geocode
    {
        "user": """\
GDELT geocode: Saint-Denis, Reunion, Reunion
URL: http://www.journaldunet.com/economie/actualite/depeche/afp/24/1757284/greve-des-eboueurs-a-marseille-la-metropole-fait-evacuer-quelques-bennes.shtml
Article text:
La grève des éboueurs à Marseille entre dans sa deuxième semaine. La \
Métropole Aix-Marseille-Provence a commencé à évacuer quelques bennes \
débordantes, mais des tonnes de déchets s'accumulent toujours dans les \
rues de la ville phocéenne.\
""",
        "assistant": """\
{"extracted_location": "Marseille, France", "match": "no", \
"corrected_location": "Marseille, Provence-Alpes-Côte d'Azur, France", \
"reasoning": "Article describes a garbage collectors' strike in Marseille, \
France; GDELT incorrectly geocoded the event to Reunion, likely because the \
outlet has a Reunion connection — the outlet's location is irrelevant."}\
""",
    },

    # 11. uncertain — broken link, URL uninformative about location
    {
        "user": """\
GDELT geocode: Luanda, Luanda, Angola
URL: http://www.nasdaq.com/article/angolan-teachers-begin-threeday-strike-over-wages-20170405-01186
Article text:
Not available.\
""",
        "assistant": """\
{"extracted_location": "unknown", "match": "uncertain", \
"corrected_location": null, \
"reasoning": "Article is inaccessible and the URL slug identifies only the \
country (Angola), not a specific city or region that would confirm or \
contradict the Luanda geocode."}\
""",
    },

    # 12. uncertain — nationwide strike, capital assigned
    {
        "user": """\
GDELT geocode: Naypyidaw, Mandalay, Myanmar
URL: https://www.sott.net/article/449800-2-protesters-killed-in-myanmar-as-workers-stage-general-strike
Article text:
Workers across Myanmar staged a nationwide general strike Tuesday, with \
protests and work stoppages reported in Yangon, Mandalay, and dozens of \
smaller cities. At least two protesters were killed as security forces \
moved to disperse crowds. Trade unions said participation was near-total \
across all sectors and regions.\
""",
        "assistant": """\
{"extracted_location": "nationwide, Myanmar", "match": "uncertain", \
"corrected_location": null, \
"reasoning": "Article describes a nationwide general strike spanning multiple \
cities; assigning this event to a single ADM1 such as Naypyidaw is not \
meaningful."}\
""",
    },

    # 13. uncertain — paywall, organisation operates across multiple locations
    {
        "user": """\
GDELT geocode: Karingal, Victoria, Australia
URL: https://www.theadvocate.com.au/story/8850485/aged-care-staff-strike-over-pay-dispute-at-baptcare/
Article text:
[Paywalled — snippet only]: "Aged care staff at Baptcare have begun strike \
action over a pay dispute..."\
""",
        "assistant": """\
{"extracted_location": "unknown", "match": "uncertain", \
"corrected_location": null, \
"reasoning": "Article is paywalled and only a brief snippet is available; \
Baptcare operates aged care facilities across multiple states, so the snippet \
alone cannot confirm whether the strike occurred specifically at the \
Karingal location."}\
""",
    },
]


# ---------------------------------------------------------------------------
# Message builder
# ---------------------------------------------------------------------------

def _extract_slug(url: str) -> str | None:
    """Return the last meaningful path segment of a URL as a readable slug."""
    if not url:
        return None
    # Strip query string and fragment
    path = url.split("?")[0].split("#")[0].rstrip("/")
    segment = path.split("/")[-1]
    # Only return if it looks like a human-readable slug (contains hyphens/words)
    if "-" in segment and not segment.isdigit() and len(segment) > 10:
        return segment
    return None


def build_user_message(row: dict) -> str:
    """Build the user message for a single event."""
    geocode      = row.get("ActionGeo_FullName", "unknown")
    url          = row.get("SOURCEURL", "")
    article_text = row.get("article_text") or "Not available."

    slug = _extract_slug(url)
    slug_line = f"URL slug: {slug}\n" if slug else ""

    return (
        f"GDELT geocode: {geocode}\n"
        f"URL: {url}\n"
        f"{slug_line}"
        f"Article text:\n{article_text}"
    )


def build_messages(row: dict) -> list[dict]:
    """Build the full messages list (system + few-shot + user) for a row."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for ex in FEW_SHOT_EXAMPLES:
        messages.append({"role": "user",      "content": ex["user"]})
        messages.append({"role": "assistant", "content": ex["assistant"]})
    messages.append({"role": "user", "content": build_user_message(row)})
    return messages
