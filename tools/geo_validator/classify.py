"""CLI entry point and test runner for geo_validator."""

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

from .data import (
    ARTICLE_CACHE, OUTPUT_CSV, ROOT, load_relevant_events,
)
from .fetch import fetch_all_articles
from .prompts import build_messages

TEST_DIR = ROOT / "data/test"
TEST_SAMPLE_SEED = 99


def run_test(n: int = 50, try_wayback: bool = True):
    """
    Quick direct-API test on a sample of relevant events.
    Fetches article text, classifies, and saves timestamped output to data/test/.
    """
    client = OpenAI()
    events = load_relevant_events()
    sample = events.sample(min(n, len(events)), random_state=TEST_SAMPLE_SEED)

    print(f"Fetching article text for {len(sample)} test events...")
    sample = fetch_all_articles(sample, try_wayback=try_wayback)
    fetched = sample["article_text"].notna().sum()
    print(f"Text retrieved for {fetched}/{len(sample)} events.")

    rows = []
    for i, (_, row) in enumerate(sample.iterrows(), 1):
        messages = build_messages(row.to_dict())
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=120,
            response_format={"type": "json_object"},
            messages=messages,
        )
        content = resp.choices[0].message.content
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = {"extracted_location": "unknown", "match": "uncertain",
                      "reasoning": "parse error"}

        rows.append({
            "GLOBALEVENTID":      row["GLOBALEVENTID"],
            "ActionGeo_FullName": row["ActionGeo_FullName"],
            "ActionGeo_ADM1Code": row["ActionGeo_ADM1Code"],
            "SOURCEURL":          row["SOURCEURL"],
            "article_source":     row.get("article_source", "none"),
            "article_text":       str(row.get("article_text") or "")[:500],
            "extracted_location": parsed.get("extracted_location", "unknown"),
            "match":              parsed.get("match", "uncertain"),
            "corrected_location": parsed.get("corrected_location"),
            "reasoning":          parsed.get("reasoning", ""),
        })

        if i % 10 == 0 or i == len(sample):
            counts = pd.Series([r["match"] for r in rows]).value_counts()
            print(f"  {i}/{len(sample)} classified — {dict(counts)}")

    TEST_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = TEST_DIR / f"geo_validation_test_{stamp}.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"\nSaved {len(rows)} test results → {out_path}")


def validate_sample(try_wayback: bool = True, model: str = "gpt-4o-mini"):
    """
    Run geo validation on the hand-annotated ADM1 validation sample.
    Fetches article text, classifies via direct API, and saves results to
    data/test/adm1_validation_sample_llm.csv — keeping human annotations
    alongside LLM output for comparison.
    """
    client = OpenAI()
    sample_path = TEST_DIR / "adm1_validation_sample.csv"
    if not sample_path.exists():
        print(f"Validation sample not found at {sample_path}.")
        return

    sample = pd.read_csv(sample_path)
    sample["GLOBALEVENTID"] = sample["GLOBALEVENTID"].astype("int64")

    # Rename source columns to match what fetch_all_articles expects
    sample = sample.rename(columns={"source_url": "SOURCEURL"})

    print(f"Model: {model}")
    print(f"Fetching article text for {len(sample)} events "
          f"(wayback={'on' if try_wayback else 'off'})...")
    sample = fetch_all_articles(sample, try_wayback=try_wayback)
    fetched = sample["article_text"].notna().sum()
    print(f"Text retrieved for {fetched}/{len(sample)} events.\n")

    rows = []
    for i, (_, row) in enumerate(sample.iterrows(), 1):
        messages = build_messages(row.to_dict())
        # gpt-5+ uses max_completion_tokens, doesn't support temperature=0,
        # and uses internal reasoning tokens so needs a much higher budget
        is_gpt5 = model.startswith("gpt-5")
        token_kwarg = "max_completion_tokens" if is_gpt5 else "max_tokens"
        max_tok    = 4000 if is_gpt5 else 120
        extra      = {} if is_gpt5 else {"temperature": 0}
        resp = client.chat.completions.create(
            model=model,
            **{token_kwarg: max_tok},
            **extra,
            response_format={"type": "json_object"},
            messages=messages,
        )
        content = resp.choices[0].message.content
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = {"extracted_location": "unknown", "match": "uncertain",
                      "corrected_location": None, "reasoning": "parse error"}

        rows.append({
            "GLOBALEVENTID":       row["GLOBALEVENTID"],
            "SQLDATE":             row.get("SQLDATE"),
            "ActionGeo_CountryCode": row.get("ActionGeo_CountryCode"),
            "ActionGeo_ADM1Code":  row.get("ActionGeo_ADM1Code"),
            "ActionGeo_FullName":  row.get("ActionGeo_FullName"),
            "source_url":          row.get("SOURCEURL"),
            "title":               row.get("title"),
            "article_source":      row.get("article_source", "none"),
            # Human annotations (kept for comparison)
            "human_correct":       row.get("adm1_correct"),
            "human_notes":         row.get("notes"),
            # LLM output
            "llm_match":           parsed.get("match", "uncertain"),
            "llm_extracted":       parsed.get("extracted_location", "unknown"),
            "llm_corrected":       parsed.get("corrected_location"),
            "llm_reasoning":       parsed.get("reasoning", ""),
        })

        if i % 25 == 0 or i == len(sample):
            counts = pd.Series([r["llm_match"] for r in rows]).value_counts()
            print(f"  {i}/{len(sample)} classified — {dict(counts)}")

    out = pd.DataFrame(rows)
    model_tag = model.replace(".", "-")
    out_path = TEST_DIR / f"adm1_validation_sample_{model_tag}.csv"
    out.to_csv(out_path, index=False)

    print(f"\nSaved → {out_path}")
    print("\nLLM classification breakdown:")
    print(out["llm_match"].value_counts().to_string())

    # Agreement with human annotations where available
    annotated = out[out["human_correct"].notna() & (out["human_correct"].str.strip() != "")]
    if not annotated.empty:
        # Map human labels to LLM labels for comparison
        label_map = {"yes": "yes", "no": "no", "uncertain": "uncertain"}
        annotated = annotated.copy()
        annotated["human_norm"] = annotated["human_correct"].str.strip().str.lower().map(
            lambda x: x if x in label_map else "uncertain"
        )
        agree = (annotated["human_norm"] == annotated["llm_match"]).sum()
        print(f"\nHuman vs LLM agreement on {len(annotated)} annotated rows: "
              f"{agree}/{len(annotated)} ({agree/len(annotated)*100:.0f}%)")
        disagree = annotated[annotated["human_norm"] != annotated["llm_match"]]
        if not disagree.empty:
            print("\nDisagreements:")
            for _, r in disagree.iterrows():
                print(f"  {r['ActionGeo_FullName']:<45} "
                      f"human={r['human_norm']}  llm={r['llm_match']}")


def main():
    parser = argparse.ArgumentParser(
        description="Geo validator for GDELT strike events.",
        prog="python -m tools.geo_validator",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--fetch",   action="store_true",
                       help="Fetch article text for all relevant events")
    group.add_argument("--prepare", action="store_true",
                       help="Build batch JSONL from article cache")
    group.add_argument("--submit",  action="store_true",
                       help="Submit next unsubmitted chunk to OpenAI Batch API")
    group.add_argument("--status",  action="store_true",
                       help="Check batch status")
    group.add_argument("--collect", action="store_true",
                       help="Download completed results → geo_validation.csv")
    group.add_argument("--test",             type=int, metavar="N",
                       help="Quick direct-API test on N events")
    group.add_argument("--validate-sample", action="store_true",
                       help="Run on adm1_validation_sample.csv and compare to human annotations")

    parser.add_argument("--no-wayback", action="store_true",
                        help="Skip Wayback Machine fallback during fetch")
    parser.add_argument("--sample", type=int, default=None,
                        help="Limit --prepare to N events (for testing)")
    parser.add_argument("--model", type=str, default="gpt-4o-mini",
                        help="OpenAI model to use (default: gpt-4o-mini)")

    args = parser.parse_args()
    try_wayback = not args.no_wayback

    from .batch import (
        fetch_articles, prepare_batch, submit_batch,
        check_status, collect_results,
    )

    if args.fetch:
        fetch_articles(try_wayback=try_wayback)
    elif args.prepare:
        prepare_batch(sample=args.sample, model=args.model)
    elif args.submit:
        submit_batch()
    elif args.status:
        check_status()
    elif args.collect:
        collect_results()
    elif args.test is not None:
        run_test(n=args.test, try_wayback=try_wayback)
    elif args.validate_sample:
        validate_sample(try_wayback=try_wayback, model=args.model)
