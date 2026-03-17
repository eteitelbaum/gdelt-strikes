#!/usr/bin/env python3
"""
Classify GDELT strike event URLs as relevant/not_relevant/uncertain
using OpenAI's gpt-4o-mini with few-shot prompting and the Batch API.

Workflow:
  1. python -m url_classifier --prepare [N]   # build batch JSONL from parquet
  2. python -m url_classifier --submit         # upload + submit batch to OpenAI
  3. python -m url_classifier --status         # check batch status
  4. python -m url_classifier --collect        # download results → CSV
  5. python -m url_classifier --test N         # direct API call on N random URLs (no batch)
  6. python -m url_classifier --pass2-prepare  # fetch titles + build pass2 JSONL
  7. python -m url_classifier --pass2-submit   # submit pass2 batch
  8. python -m url_classifier --pass2-status   # check pass2 status
  9. python -m url_classifier --pass2-collect  # collect pass2 results, update CSV
 10. python -m url_classifier --pass2-test N   # test pass2 on N uncertain URLs

Output: data/enhanced/url_classifications.csv
  GLOBALEVENTID, source_url, classification, reasoning
"""

import argparse
import json
import sys
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

from .batch import (
    MODEL, PASS2_MODEL,
    check_pass2_status, check_status,
    collect_pass2, collect_results,
    prepare_batch, prepare_pass2,
    submit_batch, submit_pass2,
)
from .data import OUTPUT_CSV, ROOT, load_events
from .fetch import fetch_title
from .prompts import (
    PASS2_SYSTEM_PROMPT, SYSTEM_PROMPT,
    build_pass2_user_message, build_user_message,
)

load_dotenv(ROOT / ".env")

# Pricing for gpt-4o-mini (per 1M tokens)
_PRICE_INPUT  = 0.15
_PRICE_OUTPUT = 0.60


def run_test(n: int):
    client = OpenAI()
    df = load_events().sample(min(n, len(load_events())), random_state=99)

    print(f"Testing {len(df)} URLs with direct API calls (model: {MODEL})...\n")

    total_input = 0
    total_output = 0
    counts = {"relevant": 0, "not_relevant": 0, "uncertain": 0, "parse_error": 0}
    rows = []

    for _, row in df.iterrows():
        url = row["SOURCEURL"]
        resp = client.chat.completions.create(
            model=MODEL,
            temperature=0,
            max_tokens=80,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_message(url)},
            ],
        )
        total_input  += resp.usage.prompt_tokens
        total_output += resp.usage.completion_tokens

        try:
            result = json.loads(resp.choices[0].message.content)
        except Exception:
            result = {"classification": "parse_error", "reasoning": resp.choices[0].message.content}

        label = result.get("classification", "parse_error")
        reason = result.get("reasoning", "")
        counts[label] = counts.get(label, 0) + 1
        rows.append({"GLOBALEVENTID": row["GLOBALEVENTID"], "source_url": url,
                     "classification": label, "reasoning": reason})
        print(f"[{label:14s}] {url[:90]}")
        print(f"               → {reason}\n")

    # Save test results (timestamped to avoid overwriting annotated files)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_csv = ROOT / f"data/test/url_classifications_pass1_test_{stamp}.csv"
    pd.DataFrame(rows).to_csv(test_csv, index=False)
    print(f"Test results saved to {test_csv}\n")

    # Cost summary
    sample_cost = (total_input / 1_000_000 * _PRICE_INPUT) + (total_output / 1_000_000 * _PRICE_OUTPUT)
    total_events = len(load_events())
    scale_factor = total_events / n
    projected_input  = total_input  * scale_factor
    projected_output = total_output * scale_factor
    projected_full_cost = (projected_input / 1_000_000 * _PRICE_INPUT) + (projected_output / 1_000_000 * _PRICE_OUTPUT)

    print("─" * 60)
    print(f"RESULTS ({n} URLs sampled)")
    for label, count in counts.items():
        if count:
            print(f"  {label:14s}: {count:4d}  ({count/n*100:.1f}%)")
    print(f"\nTOKEN USAGE (this sample)")
    print(f"  Input tokens : {total_input:,}  (avg {total_input//n}/url)")
    print(f"  Output tokens: {total_output:,}  (avg {total_output//n}/url)")
    print(f"  Sample cost  : ${sample_cost:.4f}")
    print(f"\nPROJECTED (all {total_events:,} events, direct API, no batch discount)")
    print(f"  Estimated cost : ${projected_full_cost:.2f}")
    print(f"  With 50% batch discount: ${projected_full_cost/2:.2f}")


def test_pass2(n: int, try_wayback: bool = True):
    """Quick test of pass2 on n uncertain URLs from the test or full CSV."""
    client = OpenAI()
    test_dir = ROOT / "data/test"
    candidates = sorted(test_dir.glob("url_classifications_pass1_test*.csv"), reverse=True)
    src = candidates[0] if candidates else OUTPUT_CSV
    if not src.exists():
        print("No classifications CSV found. Run --test or --collect first.")
        sys.exit(1)
    print(f"Reading uncertain events from {src.name}")

    classified = pd.read_csv(src)
    uncertain = classified[classified["classification"] == "uncertain"].sample(
        min(n, len(classified[classified["classification"] == "uncertain"])),
        random_state=42
    )
    print(f"Testing pass2 on {len(uncertain)} uncertain URLs (wayback={'on' if try_wayback else 'off'})...\n")

    rows = []
    for _, row in uncertain.iterrows():
        url = row["source_url"]
        title, source = fetch_title(url, try_wayback=try_wayback)
        title_display = f'"{title}"' if title else "(not retrieved)"
        print(f"URL   : {url[:80]}")
        print(f"Title : {title_display}  [{source}]")

        resp = client.chat.completions.create(
            model=PASS2_MODEL,
            temperature=0,
            max_tokens=80,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": PASS2_SYSTEM_PROMPT},
                {"role": "user",   "content": build_pass2_user_message(url, title)},
            ],
        )
        try:
            result = json.loads(resp.choices[0].message.content)
        except Exception:
            result = {"classification": "parse_error", "reasoning": ""}

        label = result.get("classification", "parse_error")
        reason = result.get("reasoning", "")
        rows.append({"GLOBALEVENTID": row["GLOBALEVENTID"], "source_url": url,
                     "title": title, "title_source": source,
                     "classification": label, "reasoning": reason})
        print(f"Result: [{label}] → {reason}\n")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_csv = ROOT / f"data/test/url_classifications_pass2_test_{stamp}.csv"
    pd.DataFrame(rows).to_csv(test_csv, index=False)
    print(f"Pass 2 test results saved to {test_csv}")


def main():
    parser = argparse.ArgumentParser(description="Classify GDELT strike URLs via OpenAI Batch API.")
    group = parser.add_mutually_exclusive_group(required=True)
    # Pass 1
    group.add_argument("--prepare",       nargs="?", const=None, metavar="N",
                       help="Build pass1 batch JSONL (optionally limit to N events).")
    group.add_argument("--submit",        action="store_true", help="Submit pass1 batch.")
    group.add_argument("--status",        action="store_true", help="Check pass1 batch status.")
    group.add_argument("--collect",       action="store_true", help="Collect pass1 results → CSV.")
    group.add_argument("--test",          type=int, metavar="N", help="Direct API test on N random URLs.")
    # Pass 2
    group.add_argument("--pass2-prepare", action="store_true",
                       help="Fetch titles for uncertain events and build pass2 JSONL.")
    group.add_argument("--pass2-submit",  action="store_true", help="Submit pass2 batch.")
    group.add_argument("--pass2-status",  action="store_true", help="Check pass2 batch status.")
    group.add_argument("--pass2-collect", action="store_true", help="Collect pass2 results, update CSV.")
    group.add_argument("--pass2-test",    type=int, metavar="N",
                       help="Test pass2 title-fetch + reclassify on N uncertain URLs.")
    parser.add_argument("--no-wayback", action="store_true",
                        help="Disable Wayback Machine fallback for title fetching.")
    args = parser.parse_args()

    wayback = not args.no_wayback

    if args.prepare is not None:
        prepare_batch(sample=int(args.prepare))
    elif args.prepare is None and "--prepare" in sys.argv:
        prepare_batch()
    elif args.submit:
        submit_batch()
    elif args.status:
        check_status()
    elif args.collect:
        collect_results()
    elif args.test:
        run_test(args.test)
    elif args.pass2_prepare:
        prepare_pass2(try_wayback=wayback)
    elif args.pass2_submit:
        submit_pass2()
    elif args.pass2_status:
        check_pass2_status()
    elif args.pass2_collect:
        collect_pass2()
    elif args.pass2_test:
        test_pass2(args.pass2_test, try_wayback=wayback)


if __name__ == "__main__":
    main()
