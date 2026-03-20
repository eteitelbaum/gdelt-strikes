"""
apply_corrections.py — Standardize corrected_location strings via OpenAI Batch API

For each geo_validation.csv row where match='no', the LLM provided a
corrected_location string (e.g. "Nagpur, Maharashtra, India"). This script
converts those strings to standardized ADM1 identifiers using the OpenAI
Batch API (fast, cheap, handles the clean structured strings well).

Workflow (mirrors tools/geo_validator/batch.py):
    --prepare   Build batch JSONL from geo_validation.csv no-match rows
    --submit    Upload and submit to OpenAI Batch API
    --status    Check batch progress
    --collect   Download results → data/reference/corrected_location_crosswalk.csv

Usage:
    python -m tools.adm1_crosswalk.apply_corrections --prepare
    python -m tools.adm1_crosswalk.apply_corrections --submit
    python -m tools.adm1_crosswalk.apply_corrections --status
    python -m tools.adm1_crosswalk.apply_corrections --collect
"""

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd
from openai import OpenAI

ROOT           = Path(__file__).resolve().parents[2]
GEO_VALIDATION = ROOT / "data/enhanced/geo_validation.csv"
BATCH_DIR      = ROOT / "tools/adm1_crosswalk"
BATCH_JSONL    = BATCH_DIR / "corrections_batch_requests.jsonl"
BATCH_META     = BATCH_DIR / "corrections_batch_meta.json"
BATCH_RESULTS  = BATCH_DIR / "corrections_batch_results.jsonl"
CROSSWALK_OUT  = ROOT / "data/reference/corrected_location_crosswalk.csv"

MODEL      = "gpt-4o-mini"
MAX_TOKENS = 150

SYSTEM_PROMPT = """\
You are a geographic coding assistant. Given a location string (city, region,
and/or country), return the standardized ADM1 (first-level administrative
division) name and ISO 3166-2 subdivision code for that location.

Output a JSON object with exactly these fields:
  "adm1_name"   : standardized English name of the ADM1 region
                  (e.g. "Maharashtra", "Île-de-France", "Bavaria")
  "iso_3166_2"  : ISO 3166-2 code (e.g. "IN-MH", "FR-IDF", "DE-BY")
                  Use null if you are not confident in the code.
  "country_iso2": ISO 3166-1 alpha-2 country code (e.g. "IN", "FR", "DE")
  "match_method": one of:
      "resolved"      - successfully identified ADM1 and country
      "country_level" - location is country-wide or no specific ADM1
                        (e.g. "Belgium", "Nationwide, Spain")
      "unresolvable"  - cannot determine a valid ADM1

Rules:
  - If the location string is just a country name, use "country_level".
  - If the string contains "nationwide" or "multiple cities", use "country_level".
  - If you genuinely cannot determine the ADM1, use "unresolvable".
  - For the adm1_name, use the standard English name as it appears in
    official sources (GADM, Wikipedia). Do not abbreviate.
  - Return only the JSON object, no other text.
"""

FEW_SHOT = [
    {
        "role": "user",
        "content": "Nagpur, Maharashtra, India"
    },
    {
        "role": "assistant",
        "content": '{"adm1_name": "Maharashtra", "iso_3166_2": "IN-MH", "country_iso2": "IN", "match_method": "resolved"}'
    },
    {
        "role": "user",
        "content": "Paris, Île-de-France, France"
    },
    {
        "role": "assistant",
        "content": '{"adm1_name": "Île-de-France", "iso_3166_2": "FR-IDF", "country_iso2": "FR", "match_method": "resolved"}'
    },
    {
        "role": "user",
        "content": "Belgium"
    },
    {
        "role": "assistant",
        "content": '{"adm1_name": null, "iso_3166_2": null, "country_iso2": "BE", "match_method": "country_level"}'
    },
    {
        "role": "user",
        "content": "Nationwide, United Kingdom"
    },
    {
        "role": "assistant",
        "content": '{"adm1_name": null, "iso_3166_2": null, "country_iso2": "GB", "match_method": "country_level"}'
    },
    {
        "role": "user",
        "content": "West Bank, Palestinian Territories"
    },
    {
        "role": "assistant",
        "content": '{"adm1_name": "West Bank", "iso_3166_2": null, "country_iso2": "PS", "match_method": "resolved"}'
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_location(raw: str) -> str:
    """Take first location if semicolon-separated; strip parentheticals."""
    if not raw or pd.isna(raw):
        return ""
    loc = raw.split(";")[0].strip()
    loc = re.sub(r'\s*\(.*?\)\s*$', '', loc).strip()
    return loc


def build_messages(location: str) -> list:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        *FEW_SHOT,
        {"role": "user", "content": location},
    ]


def load_no_match_rows() -> pd.DataFrame:
    df = pd.read_csv(GEO_VALIDATION, dtype=str)
    return df[df["match"] == "no"][["GLOBALEVENTID", "corrected_location"]].copy()


def parse_result_line(line: str) -> dict | None:
    try:
        obj      = json.loads(line)
        event_id = obj["custom_id"]
        body     = obj["response"]["body"]
        content  = body["choices"][0]["message"]["content"]
        parsed   = json.loads(content)
        return {
            "GLOBALEVENTID": event_id,
            "adm1_name":     parsed.get("adm1_name"),
            "iso_3166_2":    parsed.get("iso_3166_2"),
            "country_iso2":  parsed.get("country_iso2"),
            "match_method":  parsed.get("match_method", "unresolvable"),
        }
    except Exception as e:
        print(f"  parse error: {e} — line: {line[:120]}")
        return None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def prepare():
    rows = load_no_match_rows()
    print(f"Building batch from {len(rows):,} no-match rows...")

    with open(BATCH_JSONL, "w") as f:
        for _, row in rows.iterrows():
            loc = parse_location(row["corrected_location"])
            if not loc:
                loc = row["corrected_location"] or "unknown"
            request = {
                "custom_id": str(row["GLOBALEVENTID"]),
                "method":    "POST",
                "url":       "/v1/chat/completions",
                "body": {
                    "model":      MODEL,
                    "messages":   build_messages(loc),
                    "max_tokens": MAX_TOKENS,
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                },
            }
            f.write(json.dumps(request) + "\n")

    size_mb = BATCH_JSONL.stat().st_size / 1_048_576
    print(f"Written: {BATCH_JSONL.name}  ({size_mb:.1f} MB, {len(rows):,} requests)")
    print("Run --submit to upload and submit.")


def submit():
    if not BATCH_JSONL.exists():
        print("No batch file found. Run --prepare first.")
        sys.exit(1)

    client = OpenAI()
    print(f"Uploading {BATCH_JSONL.name} ...")
    with open(BATCH_JSONL, "rb") as f:
        uploaded = client.files.create(file=f, purpose="batch")

    batch = client.batches.create(
        input_file_id=uploaded.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    print(f"Submitted: {batch.id}  status: {batch.status}")
    meta = {"batch_id": batch.id, "file_id": uploaded.id}
    BATCH_META.write_text(json.dumps(meta, indent=2))
    print(f"Metadata saved → {BATCH_META.name}")
    print("Check progress: python -m tools.adm1_crosswalk.apply_corrections --status")


def status():
    if not BATCH_META.exists():
        print("No batch metadata found. Run --submit first.")
        sys.exit(1)
    client = OpenAI()
    meta   = json.loads(BATCH_META.read_text())
    batch  = client.batches.retrieve(meta["batch_id"])
    c      = batch.request_counts
    print(f"Batch {batch.id}: {batch.status}")
    print(f"  total={c.total}  completed={c.completed}  failed={c.failed}")
    if batch.status == "completed":
        print("Ready — run --collect to download results.")
    return batch.status == "completed"


def collect():
    if not BATCH_META.exists():
        print("No batch metadata found.")
        sys.exit(1)

    client = OpenAI()
    meta   = json.loads(BATCH_META.read_text())
    batch  = client.batches.retrieve(meta["batch_id"])

    if batch.status != "completed":
        print(f"Batch not ready (status: {batch.status}).")
        sys.exit(1)

    print(f"Downloading results (file: {batch.output_file_id}) ...")
    content = client.files.content(batch.output_file_id).text
    BATCH_RESULTS.write_text(content)

    # Parse results
    rows     = load_no_match_rows()
    loc_map  = dict(zip(rows["GLOBALEVENTID"].astype(str),
                        rows["corrected_location"]))

    results = []
    for line in content.strip().split("\n"):
        if not line:
            continue
        result = parse_result_line(line)
        if result:
            result["corrected_location"] = loc_map.get(result["GLOBALEVENTID"], "")
            results.append(result)

    out = pd.DataFrame(results)[[
        "GLOBALEVENTID", "corrected_location",
        "adm1_name", "iso_3166_2", "country_iso2", "match_method"
    ]]
    out.to_csv(CROSSWALK_OUT, index=False)

    print(f"\nSaved {len(out):,} rows → {CROSSWALK_OUT}")
    print(out["match_method"].value_counts().to_string())
    missing = len(rows) - len(out)
    if missing:
        print(f"Warning: {missing} rows missing from results (parse errors)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group  = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--submit",  action="store_true")
    group.add_argument("--status",  action="store_true")
    group.add_argument("--collect", action="store_true")
    args = parser.parse_args()

    if args.prepare:
        prepare()
    elif args.submit:
        submit()
    elif args.status:
        status()
    elif args.collect:
        collect()
