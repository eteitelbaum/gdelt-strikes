"""
fetch_fips_table.py — Download FIPS 10-4 subdivision table from efele.net

Downloads the full FIPS 10-4 subdivision history from efele.net/maps/fips-10/
and outputs a CSV of all codes (current and historical). Historical codes are
included because GDELT events may reference retired codes.

Source file: http://efele.net/maps/fips-10/data/fips-all.txt
Format per line: CODE_startCN_endCN_type____NAME__
  - CODE    : 4-char FIPS code (2-char country + 2-char ADM1 suffix)
  - startCN : change notice when code was introduced
  - endCN   : change notice when code was last valid (414 = still current)
  - type    : administrative type (parish, province, emirate, etc.)
  - NAME    : official English name

Output: docs/fips/fips10-4-subdivisions.csv
Columns:
  fips_country   : 2-char FIPS country code
  fips_adm1      : 4-char FIPS ADM1 code
  fips_adm1_name : official name (latest version for this code)
  adm1_type      : administrative type in FIPS
  start_cn       : change notice when introduced
  end_cn         : change notice when last valid
  current        : True if end_cn == 414

Usage:
    python -m tools.adm1_crosswalk.fetch_fips_table
"""

import csv
import sys
import unicodedata
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "docs" / "fips" / "fips10-4-subdivisions.csv"
SOURCE_URL = "http://efele.net/maps/fips-10/data/fips-all.txt"


def fetch_raw() -> str:
    print(f"Fetching {SOURCE_URL} ...")
    resp = requests.get(SOURCE_URL, timeout=30)
    resp.raise_for_status()
    return resp.content.decode("utf-8")


def normalize_name(name: str) -> str:
    """Convert latin-1 diacritic sequences to closest ASCII equivalent."""
    # Normalize unicode to NFD (decomposed), then strip combining characters
    nfd = unicodedata.normalize("NFD", name)
    ascii_approx = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return ascii_approx.strip()


def parse(text: str) -> list[dict]:
    """
    Parse fips-all.txt into records.

    Line format: CODE_startCN_endCN_type[_subtype]___NAME__
    The name is always separated from the header by 3+ consecutive underscores.
    Some entries have a subtype field (e.g. Turkey uses 'province_il').
    Country-level entries (code ending in '00') are skipped.

    For codes that appear multiple times (renamed across change notices),
    we keep all versions.
    """
    import re
    # Match: 4-char code, startCN, endCN, one or more type/subtype fields,
    # then 3+ underscores, then the name, then trailing underscores
    pattern = re.compile(
        r'^([A-Z0-9]{4})_(\d+)_(\d+)_([A-Za-z_ ]+?)_{3,}(.+?)_*$'
    )

    records = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        m = pattern.match(line)
        if not m:
            continue

        code = m.group(1)
        start_cn = m.group(2)
        end_cn = m.group(3)
        type_field = m.group(4).strip("_").strip()
        name = m.group(5).strip()

        if len(code) != 4:
            continue
        # Skip country-level entries (XX00 codes are country summaries)
        if code[2:] == "00":
            continue
        if not name:
            continue

        # adm1_type: first token of the type field
        adm1_type = type_field.split("_")[0].strip()

        fips_country = code[:2]
        fips_adm1 = code

        try:
            start_cn_int = int(start_cn)
            end_cn_int = int(end_cn)
        except ValueError:
            continue

        records.append({
            "fips_country": fips_country,
            "fips_adm1": fips_adm1,
            "fips_adm1_name": name,
            "fips_adm1_name_ascii": normalize_name(name),
            "adm1_type": adm1_type,
            "start_cn": start_cn_int,
            "end_cn": end_cn_int,
            "current": end_cn_int == 414,
        })

    return records


def deduplicate(records: list[dict]) -> list[dict]:
    """
    For each FIPS code, keep the most recent entry (highest end_cn).
    Also retain a flag indicating whether it was ever current (end_cn=414).
    """
    by_code: dict[str, dict] = {}
    for r in records:
        code = r["fips_adm1"]
        if code not in by_code or r["end_cn"] > by_code[code]["end_cn"]:
            by_code[code] = r
    return sorted(by_code.values(), key=lambda r: r["fips_adm1"])


def write_output(records: list[dict]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "fips_country", "fips_adm1", "fips_adm1_name", "fips_adm1_name_ascii",
        "adm1_type", "start_cn", "end_cn", "current",
    ]
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records)} rows to {OUTPUT_PATH}")


def main():
    try:
        text = fetch_raw()
    except Exception as e:
        print(f"Download failed: {e}")
        sys.exit(1)

    all_records = parse(text)
    print(f"Parsed {len(all_records)} total entries (including historical)")

    current = [r for r in all_records if r["current"]]
    print(f"  Current (end_cn=414): {len(current)}")
    print(f"  Historical only:      {len(all_records) - len(current)}")

    deduped = deduplicate(all_records)
    print(f"  Unique codes (latest version): {len(deduped)}")

    print("\nSample (first 10):")
    for r in deduped[:10]:
        status = "current" if r["current"] else f"retired CN{r['end_cn']}"
        print(f"  {r['fips_adm1']:6s}  {r['fips_adm1_name_ascii']:<30s}  [{status}]")

    write_output(deduped)


if __name__ == "__main__":
    main()
