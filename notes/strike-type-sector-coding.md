# Strike Type and Sector Coding: Plan and Strategic Considerations

This note describes a potential coding extension to classify GDELT strike
events by type (industrial vs. political) and economic sector, drawing on
the coding scheme from the High Profile Strikes Dataset (HPSD, Teitelbaum
2005). Reference documents in `docs/hpsd/`.

---

## Motivation

The GDELT strike events currently have no coding for:
- **Strike type**: industrial dispute (wages, conditions, layoffs) vs.
  political strike (government policy, liberalization, economic reform)
- **Economic sector**: which industry the striking workers belong to

Both matter for the diffusion paper (Paper 4) and potentially for causes
(Paper 1) and geography (Paper 3):

- **Type and diffusion**: Political strikes and industrial strikes likely
  diffuse by different mechanisms. Political strikes spread via shared
  policy grievances — workers in other regions respond to the same national
  signal (a coordination problem). Industrial strikes spread via demonstration
  effects, labor market spillovers, or solidarity within the same sector or
  employer. Testing whether the diffusion coefficient differs by type, or
  whether political strikes diffuse more broadly while industrial strikes
  diffuse more locally, is a genuinely interesting heterogeneity result.
- **Sector and diffusion**: Strike contagion may be stronger within-sector
  than across-sector. Public sector strikes may diffuse nationally; private
  sector strikes may diffuse locally.

---

## Proposed Coding Approach

### Two-step LLM coding (within one prompt or sequentially)

**Step 1 — Job identification**
Ask the LLM to extract the occupation/job of the striking workers directly
from the article text. This is the easy, reliable step: articles almost
always say "teachers", "miners", "transport workers", "civil servants", etc.
The LLM is doing extraction, not inference.

Example output: `"nurses and hospital workers"`

**Step 2 — Sector mapping**
Map the extracted job description to:
1. **Strike type**: industrial dispute / political strike / both / unclear
2. **ISIC sector** (broad categories from HPSD coding scheme):
   - Mining and Quarrying (C)
   - Manufacturing (D)
   - Electricity, Gas, Water (E)
   - Construction (F)
   - Hotels and Restaurants (H)
   - Transport, Storage, Communications (I)
   - Public Administration (L)
   - Education (M)
   - Health or Social Work (N)
   - Other Community/Social Services (O)
   - Other / Not classifiable

Step 2 can be done either as a continuation of the same LLM call (if the
sector mapping is prompted as a structured output), or as a deterministic
lookup (job description → sector via a mapping table, reducing cost).

### Implementation notes

- The article text is already fetched and stored from the geo-validation
  pipeline — no additional fetching required
- The same `tools/geo_validator/` infrastructure (OpenAI Batch API,
  CHUNK_SIZE=3,000) would handle this job at similar scale and cost
- The HPSD coding sheet (`docs/hpsd/CODING SHEET.doc`) and codebook
  (`docs/hpsd/HPSD Codebook.doc`) provide the few-shot examples and
  category definitions for the prompt
- For the industrial/political distinction, the codebook defines:
  - **Industrial dispute**: launched over work-related issues, directed at
    a company or sector
  - **Political strike**: reaction to general or specific economic policy,
    aimed at the government
- ~11,500 events at ~$0.03/1k tokens (gpt-4o-mini) ≈ modest cost

---

## Strategic Recommendation: Defer to R&R

### Don't add this at initial submission

The baseline diffusion result — does neighbor-region strike exposure predict
strike onset? — is a complete, publishable contribution without the
type/sector breakdown. Adding the heterogeneity analysis at submission risks:

1. Reviewers wanting a full theory of differential diffusion (significantly
   expanding the paper's theoretical burden)
2. Reviewers wanting the sector breakdown to be the main contribution
   (reframing the paper)
3. Adding months of analysis at a stage when clean, focused papers do better

### Do add it at R&R if requested

If a reviewer specifically asks about heterogeneity by strike type, the
coding can be generated quickly:
- The pipeline is already built (geo-validator infrastructure)
- The codebook is already documented (`docs/hpsd/`)
- A new batch job would take a few hours of API processing
- The sector mapping step could be largely deterministic once jobs are
  extracted

### Consider as a follow-on paper

The industrial vs. political diffusion distinction has enough theoretical
content to support its own paper:
- A paper on differential diffusion mechanisms (policy signals vs.
  demonstration effects) would have a distinct contribution
- Could be targeted at more theoretically-oriented comparative politics
  or contentious politics venues
- Building on the baseline diffusion result as established prior work

---

## Relationship to HPSD

The HPSD (1980–2005, 84 non-OECD countries, ~1,000 events manually coded
from printed Lexis-Nexis articles) and the current GDELT dataset (2015–2023,
global, ~11,500 events) do **not overlap in time** — HPSD ends 2005, GDELT
data starts 2015. They cannot be directly compared or used for cross-dataset
validation.

The HPSD is useful here in one specific way: as a source of **few-shot
examples** for the LLM coding prompt. The manually coded events provide
clean, verified examples of the industrial/political distinction and sector
assignments that can anchor the prompt, even though the underlying events
are from a different era. The coding categories are the same; the prompt
doesn't require temporal overlap to benefit from them.
