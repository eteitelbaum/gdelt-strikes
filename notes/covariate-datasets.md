# Covariate Datasets: National and Subnational

This note catalogs datasets for potential merging into the strike
diffusion/contagion analysis, organized by geographic level and thematic
domain. Items marked **[confirm]** were mentioned in prior discussion but
need confirmation of exact source/version.

---

## National-Level Datasets

### Political Institutions and Democracy

**V-Dem (Varieties of Democracy)**
- Source: v-dem.net
- Coverage: ~180 countries, 1789–present
- Key variables: electoral democracy index, liberal democracy index,
  civil society participation, labor rights components
- Unit: country-year
- Notes: multiple indices available at different levels of aggregation;
  the polyarchy and civil liberties indices are most relevant for
  strike propensity modeling

**DPI (Database of Political Institutions)**
- Source: World Bank
- Coverage: ~180 countries, 1975–present
- Key variables: government type, electoral rules, party system,
  checks and balances
- Unit: country-year

### Economic Conditions

**World Bank World Development Indicators (WDI)**
- Source: data.worldbank.org
- Coverage: ~217 countries, 1960–present
- Key variables: GDP per capita, GDP growth, inflation, unemployment,
  trade openness, FDI, manufacturing share of GDP, labor force
  participation
- Unit: country-year

**IMF World Economic Outlook (WEO)**
- Source: imf.org/external/datamapper
- Coverage: ~190 countries, 1980–present
- Key variables: GDP, inflation, current account, fiscal balance
- Unit: country-year; includes projections (useful for expectation-based
  mechanisms)

**UNCTAD Trade and Development Data**
- Source: unctadstat.unctad.org
- Coverage: ~200 countries
- Key variables: trade flows, FDI inflows/outflows, commodity prices,
  value chains, manufacturing exports
- Unit: country-year
- Notes: particularly useful for trade exposure and commodity dependence
  mechanisms

### Labor and Industrial Relations

**ILO ILOSTAT**
- Source: ilostat.ilo.org
- Coverage: varies by indicator, ~180 countries
- Key variables: strike frequency and workers involved (where reported),
  union density, collective bargaining coverage, labor force by sector
- Unit: country-year
- Notes: strike data patchy for developing countries; useful as a
  validation check against GDELT counts

**OECD Labour Statistics**
- Source: stats.oecd.org
- Coverage: OECD members + some partner countries
- Key variables: strike days lost, union density, minimum wage, wages
  by sector
- Unit: country-year
- Notes: more reliable and complete than ILO for OECD countries

### Conflict

**UCDP (Uppsala Conflict Data Program)**
- Source: ucdp.uu.se
- Coverage: global, 1946–present
- Preferred over ACLED due to stable data generating process
- Key datasets:
  - UCDP/PRIO Armed Conflict Dataset: country-year conflict incidence
  - UCDP GED (Georeferenced Event Dataset): event-level with coordinates
    → can be aggregated to ADM1-year
- Unit: conflict-year (UCDP/PRIO) or event (GED)

**ACLED (Armed Conflict Location & Event Data)**
- Source: acleddata.com
- Coverage: global (Africa from 1997, others more recent)
- Has ADM1-level event data with GADM admin names
- Event-level only; includes `admin1` field (GADM name) for ADM1
  aggregation — no pre-aggregated ADM1 product
- **Caveat**: data generating process has changed substantially over time;
  coverage expansion conflated with trends; use with caution for
  longitudinal analysis. UCDP preferred.

---

## Subnational Datasets (ADM1 Level)

### Human Development

**Subnational Human Development Index (SHDI)**
- Source: Global Data Lab (globaldatalab.org)
- Coverage: ~160 countries, 1990–present, ADM1 level
- Key variables: subnational HDI, education index, health index,
  income index, GNI per capita (subnational)
- Unit: ADM1-year
- Notes: most widely used subnational cross-national dataset in
  comparative politics; ADM1 units match GADM GID_1; directly relevant
  as a control for regional development levels
- **[confirm]** — this is almost certainly the "ADM1 dataset for 160
  countries" referenced in earlier discussion

### Economic Activity (Proxy)

**Nighttime Lights (VIIRS/NPP)**
- Source: NOAA/NASA; accessible via Google Earth Engine
- Coverage: global, 2012–present (VIIRS); 1992–2013 (DMSP-OLS)
- Key variables: radiance/luminosity at grid level → aggregated to ADM1
- Unit: ADM1-year (after aggregation)
- Notes: standard proxy for local economic activity where GDP data is
  unavailable; complements SHDI income index; requires spatial
  aggregation step using ADM1 shapefiles (GADM)

**Gridded GDP**
- Source: multiple (Kummu et al. 2018 via Dryad; others)
- Coverage: global grids, can be aggregated to ADM1
- Unit: grid-year → ADM1-year after aggregation
- Notes: **[confirm]** — was this one of the datasets mentioned?

### Conflict (Subnational)

**UCDP GED aggregated to ADM1**
- Derived from UCDP GED event data (lat/lon coordinates)
- Aggregate conflict events to ADM1-year using spatial join with
  GADM shapefiles
- Key variables: conflict incidence, fatalities, conflict type
  (state-based, non-state, one-sided)

### Labor Market (Subnational)

**OECD Regional Statistics**
- Source: stats.oecd.org/Index.aspx?DataSetCode=REG_LABOUR
- Coverage: ~37 OECD member countries at TL2 (roughly ADM1) level
- Key variables: employment rate, unemployment rate, labor force
  participation, GDP per capita by region
- Unit: ADM1-year
- Notes: clean and well-documented but limited to wealthy countries;
  useful for robustness checks within OECD subsample

**Eurostat Regional Statistics**
- Source: ec.europa.eu/eurostat/web/regions
- Coverage: EU member states at NUTS2 level (roughly ADM1/ADM2)
- Key variables: employment, unemployment, wages, sectoral composition
- Unit: NUTS2-year
- Notes: overlaps with OECD but more detailed for EU countries;
  NUTS2 ≈ ADM1 for most EU members

**IPUMS International**
- Source: international.ipums.org
- Coverage: ~100 countries with harmonized census microdata
- Key variables: occupation, industry, employment status, education;
  can construct informality proxies and sectoral composition at ADM1
- Unit: individual → aggregatable to ADM1
- Notes: requires significant processing; coverage uneven (census years
  only, not annual); broadest cross-national option for labor
  characteristics in developing countries

**Key gap**: No comprehensive cross-national subnational dataset exists
for union density, collective bargaining coverage, strike propensity,
or sectoral labor market composition. For non-OECD countries especially,
subnational labor covariates are essentially unavailable in pre-packaged
form. Most cross-national subnational analyses fall back on SHDI +
nighttime lights as proxies. This limitation is shared across the
literature and should be acknowledged explicitly in the paper.

### Population and Demographics

**WorldPop / UN WPP Subnational**
- Source: worldpop.org
- Coverage: global gridded population → aggregatable to ADM1
- Key variables: population by age/sex at ADM1
- Unit: ADM1-year

---

## Geographic Reference

**GADM (Global Administrative Areas)**
- Source: gadm.org
- Coverage: global ADM0–ADM3 shapefiles
- Role: spatial join backbone; used to aggregate gridded data
  (nighttime lights, population) to ADM1 and to link GDELT ADM1
  codes to polygon boundaries
- GID_1 codes are the target identifier for crosswalk

**adm1_crosswalk.csv** (this project)
- Maps GDELT ADM1 codes (FIPS 10-4) → GeoNames IDs → ISO 3166-2
- Bridge to GADM GID_1 and any dataset using standard ADM1 identifiers
- See `notes/adm1-crosswalk-plan.md` for construction details

---

## Notes on Identifier Systems by Dataset

| Dataset | Country ID | ADM1 ID |
|---|---|---|
| GDELT | FIPS 10-4 | FIPS 10-4 (ADM1 suffix) |
| V-Dem | COW / ISO3 | — (national only) |
| WDI | ISO3 / World Bank code | — |
| UNCTAD | ISO3 | — |
| SHDI | ISO3 | GADM GID_1 name |
| UCDP GED | ISO3 / GW code | coordinates → spatial join |
| ACLED | ISO3 | GADM admin1 name |
| Nighttime lights | — | coordinates → spatial join |
| GADM | ISO3 | GID_1 |

The `adm1_crosswalk.csv` + a country code crosswalk (ISO2 ↔ ISO3 ↔ COW ↔
FIPS) will be needed to join across these systems.

---

## Items to Confirm

- [ ] Exact name/version of the "ADM1 dataset for 160 countries" — likely
  SHDI from Global Data Lab
- [ ] Whether gridded GDP was mentioned as a candidate
- [ ] Any sector-specific labor datasets discussed (manufacturing
  concentration, informality rates, etc.)
- [ ] Whether a specific regional inequality dataset was mentioned
- [x] Labor-specific subnational datasets: no comprehensive cross-national
  source exists; OECD Regional + Eurostat for wealthy countries,
  IPUMS International for broader coverage (requires processing);
  SHDI + nighttime lights serve as proxies for the rest
