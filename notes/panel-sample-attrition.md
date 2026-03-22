# Panel Sample Attrition: From Validated Events to Estimation Sample

## The Three Country Counts

The analysis produces three distinct country counts that should not be confused:

- **181 countries** — countries with any raw GDELT CAMEO-143 events (full BigQuery download)
- **136 countries** — countries with at least one validated strike event after the full filtering pipeline (URL classifier + geocode validator)
- **74 countries** — countries contributing at least one region to the estimation sample

## Why 136 → 74?

The drop from 136 to 74 countries is not due to island states or physical geographic isolation. It is driven by the structure of the neighbor exposure variable.

The treatment variable `neighbor_strike_within_t1_t2` is NA for any region whose within-country neighbors do not appear in the validated data panel. A region's neighbors must also have at least one validated strike event to be included in the panel, and only then can the focal region contribute a non-missing neighbor exposure observation.

Consequence: countries that appear in the validated data with only one or two regions, and where those regions happen not to share borders with other validated regions, drop out of the estimation sample entirely.

## Verified Examples

Checked with R: the following countries have 1–3 validated regions in the panel, and zero of those regions have a within-country neighbor also present in the validated data:

| Country | Validated regions | Regions with neighbor data |
|---|---|---|
| Poland | 1 | 0 |
| Ukraine | 1 | 0 |
| Austria | 3 | 0 |
| Switzerland | 3 | 0 |
| Greece | 2 | 0 |
| Japan | 2 | 0 |
| Thailand | 2 | 0 |

These are not island states. They simply have too few validated events, and those events fall in regions whose neighbors never appear in the data.

## Implications

1. The 136 → 74 drop is correct and expected, not a data bug.
2. The paper text should describe the exclusion as "regions with at least one within-country neighbor also present in the validated data" — not "island units" or "isolated regions," which implies physical geography.
3. The estimation sample (74 countries, 568 regions) is biased toward countries with denser GDELT strike coverage. This is a scope condition: findings generalize to countries and regions where labor unrest generates enough media coverage for multiple neighboring regions to appear in the data.
4. The 62 dropped countries are not randomly distributed — they likely include countries with less English-language media coverage of labor events, smaller countries with few ADM1 units, and countries where strike events cluster geographically in ways that leave most regions unneighbored in the data.

## Code Used

```r
library(arrow)
library(dplyr)

panel <- read_parquet('data/analysis/contagion_panel.parquet')

# Full validated sample
panel |> summarise(regions = n_distinct(gid_1), countries = n_distinct(gid_0))
# regions: 745, countries: 136

# Estimation sample (non-missing neighbor exposure)
panel |>
  filter(!is.na(neighbor_strike_within_t1_t2)) |>
  summarise(regions = n_distinct(gid_1), countries = n_distinct(gid_0),
            weeks = n_distinct(week_start), obs = n())
# regions: 568, countries: 74, weeks: 556, obs: 315,808
```
