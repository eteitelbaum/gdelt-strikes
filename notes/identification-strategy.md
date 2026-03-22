# Identification Strategy: Fixed Effects and Confounding

**Date**: 2026-03-19

---

## The core identification problem

We want to know whether a strike in region B *causes* a strike in neighboring
region A. The threat to identification is that neighboring regions may strike
together not because one caused the other, but because they share common
characteristics or face common shocks.

---

## Why ADM1 fixed effects alone aren't enough

ADM1 fixed effects absorb all *time-invariant* characteristics of each region —
its baseline strike propensity, industrial composition, union density, historical
militancy. If region A is always more strike-prone than region C, the ADM1 FE
accounts for that.

What ADM1 FEs cannot absorb is **time-varying common shocks** — events that
affect multiple regions simultaneously in a given period. These are the real
threat to identification.

**A concrete example**: Suppose manufacturing regions cluster geographically —
steel towns in the same corridor, textile mills in the same valley. These regions
share the same industries, the same unions, the same employer associations, and
the same contract expiration cycles. When a national wage negotiation round opens
in week t, all steel towns face the same pressure simultaneously. Region A
strikes, its neighbor B strikes — not because A inspired B, but because both
responded to the same sectoral signal. The ADM1 FE absorbs the fact that A and B
are *always* steel towns, but not the fact that *this particular week* the steel
sector was under national pressure.

---

## What country×week fixed effects add

Country×week FEs assign a separate intercept to every country-week cell,
absorbing whatever drives within-country co-movement in any given week. The
confounders they are specifically designed for are **national-level shocks** that
affect all regions in a country simultaneously:

- **General strikes**: a national union federation calls a general strike —
  every region responds regardless of industry or geography
- **Political events**: a government austerity announcement, an election result,
  a minimum wage change — these shift strike propensity everywhere at once
- **Macroeconomic shocks**: a currency crisis, a recession, a spike in
  inflation — country-wide in their impact
- **Legal changes**: a court ruling on the right to strike, a new labor law —
  applies uniformly across all regions

Each of these would produce the pattern we need to rule out: neighboring regions
striking together in the same week, not because one caused the other, but because
both responded to the same national signal.

---

## The tradeoff: over-controlling

Country×week FEs are well-suited for national shocks but arguably over-broad
for industry-specific shocks. A sectoral wage cycle affects steel towns but not
agricultural regions in the same country-week — the FE treats it as if it
affects everyone equally, which it doesn't.

More importantly, if contagion itself operates at the national level — through
national union networks, national media, national political mobilization — then
the country×week FE absorbs the very signal we're trying to measure. This is
the central tension in the analysis:

- **country×week FE** is the right control for national common shocks, but also
  removes national-wave contagion
- **ADM1 + week FE** leaves national-wave contagion in the treatment estimate,
  but conflates it with national common shocks

---

## Resolution: the decomposition

The national vs. neighborhood decomposition (see `contagion-preliminary-findings.md`)
makes this tension explicit by introducing a direct country-level strike variable
(`country_strike_t1_t2`) alongside the geographic neighbor variable. This lets
us separately estimate:

- How much of the apparent neighborhood effect is actually country-level
  co-movement (the confounder)
- How much is neighborhood-specific diffusion above and beyond that

The result — neighborhood effect drops to null while country-level effect is
large (7.9pp) — suggests that what the country×week FE was absorbing in the
main specification was genuine national-wave contagion, not just statistical
noise. The FE and the finding are telling the same story from different angles:
strikes in these data really do move at the national level.

---

## Analogy to Besley & Burgess (2004)

Besley and Burgess use a similar fixed effects logic in their study of Indian
labor regulation and economic performance. Their state FEs absorb time-invariant
state characteristics; year FEs absorb national time trends; state×industry
trends control for differential pre-existing trajectories across states.

The parallel to our setup:

| Besley-Burgess | This paper |
|---|---|
| State FE | ADM1 FE |
| Year FE | Week FE |
| State × industry trends | Country × week FE |
| Treatment: labor law amendment | Treatment: neighbor strike (t-1, t-2) |
| Outcome: manufacturing output | Outcome: strike onset |

Note that V-Dem institutional indicators in our paper are *moderators* (they
condition the size of the treatment effect), not the treatment itself — unlike
the labor regulation codes in B&B, which are the treatment. A closer B&B
analogy to our moderation question would be: does a strike in a neighboring
state increase the probability of a strike in your state, and does that effect
depend on how pro-worker your labor regulation is?
