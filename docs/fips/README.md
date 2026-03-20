# docs/fips/

## Files

### `fips10-4-subdivisions.csv`

**Source**: http://efele.net/maps/fips-10/data/fips-all.txt
**Downloaded**: 2026-03-18
**License**: CC0 (public domain dedication)
**Script**: `tools/adm1_crosswalk/fetch_fips_table.py`

The efele.net FIPS 10-4 archive is maintained by Éric Ferret and tracks
the complete publication history of FIPS 10-4 across all change notices
(CN399–CN414). It is derived from the Statoids database (statoids.com,
Gwillim Law) and from the original NIST/NGA publications.

**About FIPS 10-4**: FIPS Publication 10-4, *Countries, Dependencies, Areas
of Special Sovereignty, and Their Principal Administrative Divisions*, was
published by the US National Institute of Standards and Technology (NIST).
It was the dominant US government standard for country and subdivision codes
from the 1970s until its retirement in 2008 (replaced by GENC, the US
government profile of ISO 3166). GDELT continues to use FIPS 10-4 for
backward compatibility across its 1979–present archive.

**Contents of the CSV** (4,674 rows):

| Column | Description |
|---|---|
| `fips_country` | 2-char FIPS 10-4 country code (e.g. `TU` = Turkey) |
| `fips_adm1` | 4-char FIPS 10-4 ADM1 code (e.g. `TU90` = Kilis) |
| `fips_adm1_name` | Official name (UTF-8, with diacritics) |
| `fips_adm1_name_ascii` | ASCII approximation (diacritics stripped) |
| `adm1_type` | Administrative type in FIPS (province, state, parish, etc.) |
| `start_cn` | Change notice when this code was introduced |
| `end_cn` | Change notice when this code was last valid |
| `current` | `True` if end_cn = 414 (still valid in final published CN) |

3,219 entries are current (end_cn = 414); 1,455 are historical codes retired
across earlier change notices. Historical codes are retained because GDELT
data from earlier years may reference them.

**Note on US state codes**: FIPS 10-4 encodes US states as `US01`–`US56`
(numeric suffixes). GDELT uses postal abbreviations instead (`USTX`, `USCA`,
etc.), which are not standard FIPS 10-4. This divergence is handled in the
ADM1 crosswalk build script.
