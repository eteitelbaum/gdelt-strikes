"""OpenAI Batch API plumbing for geo validation."""

import json
import sys

import pandas as pd
from openai import OpenAI

from .data import (
    ARTICLE_CACHE, BATCH_DIR, BATCH_JSONL, BATCH_META, BATCH_RESULTS,
    OUTPUT_CSV, already_validated, load_relevant_events,
)
from .fetch import FETCH_WORKERS, fetch_all_articles
from .prompts import build_messages

MODEL      = "gpt-5-mini"
# gpt-5-mini uses ~4000 max_completion_tokens (incl. reasoning) per request.
# At ~3000 input tokens each, 3000 requests ≈ 9M input tokens — safely under
# OpenAI's 20M enqueued-token limit. gpt-4o-mini can use 10,000 (120 tokens out).
CHUNK_SIZE = 3_000


def _model_request_body(model: str, messages: list) -> dict:
    """Build the model-specific body dict for a batch request."""
    is_gpt5 = model.startswith("gpt-5")
    body = {
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": messages,
    }
    if is_gpt5:
        body["max_completion_tokens"] = 4_000
    else:
        body["max_tokens"] = 120
        body["temperature"] = 0
    return body


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _chunk_path(i: int):
    return BATCH_DIR / f"batch_requests_{i:03d}.jsonl"


def parse_result_line(line: str) -> dict | None:
    try:
        obj      = json.loads(line)
        event_id = int(obj["custom_id"])
        body     = obj["response"]["body"]
        content  = body["choices"][0]["message"]["content"]
        parsed   = json.loads(content)
        return {
            "GLOBALEVENTID":      event_id,
            "extracted_location": parsed.get("extracted_location", "unknown"),
            "match":              parsed.get("match", "uncertain"),
            "corrected_location": parsed.get("corrected_location"),
            "reasoning":          parsed.get("reasoning", ""),
        }
    except Exception as e:
        print(f"  parse error: {e} — line: {line[:120]}")
        return None


# ---------------------------------------------------------------------------
# Fetch step (runs locally before batch submission)
# ---------------------------------------------------------------------------

def fetch_articles(try_wayback: bool = True):
    """Fetch article text for all relevant events; saves to ARTICLE_CACHE."""
    events = load_relevant_events()
    done   = already_validated()
    pending = events[~events["GLOBALEVENTID"].isin(done)]

    if ARTICLE_CACHE.exists():
        cached = pd.read_csv(ARTICLE_CACHE)
        cached["GLOBALEVENTID"] = cached["GLOBALEVENTID"].astype("int64")
        already_fetched = set(cached["GLOBALEVENTID"].tolist())
        pending = pending[~pending["GLOBALEVENTID"].isin(already_fetched)]
        print(f"Cache has {len(already_fetched):,} events; {len(pending):,} remaining to fetch.")
    else:
        print(f"Fetching article text for {len(pending):,} events "
              f"(wayback={'on' if try_wayback else 'off'}, workers={FETCH_WORKERS})...")

    if pending.empty:
        print("Nothing to fetch.")
        return

    result = fetch_all_articles(pending, try_wayback=try_wayback)
    fetched = result["article_text"].notna().sum()
    print(f"\nFetched text for {fetched:,}/{len(result):,} events "
          f"({fetched/len(result)*100:.1f}%)")

    out = result[["GLOBALEVENTID", "SOURCEURL", "ActionGeo_FullName",
                  "ActionGeo_ADM1Code", "ActionGeo_CountryCode",
                  "article_text", "article_source"]]
    if ARTICLE_CACHE.exists():
        existing = pd.read_csv(ARTICLE_CACHE)
        out = pd.concat([existing, out]).drop_duplicates("GLOBALEVENTID")

    out.to_csv(ARTICLE_CACHE, index=False)
    print(f"Saved → {ARTICLE_CACHE}")


# ---------------------------------------------------------------------------
# Prepare: build batch JSONL chunk(s) from cache
# ---------------------------------------------------------------------------

def prepare_batch(sample: int | None = None, model: str = MODEL):
    if not ARTICLE_CACHE.exists():
        print(f"No article cache found at {ARTICLE_CACHE}. Run --fetch first.")
        sys.exit(1)

    cache = pd.read_csv(ARTICLE_CACHE)
    cache["GLOBALEVENTID"] = cache["GLOBALEVENTID"].astype("int64")
    done  = already_validated()
    pending = cache[~cache["GLOBALEVENTID"].isin(done)]

    if sample:
        pending = pending.sample(min(sample, len(pending)), random_state=42)

    n_chunks = max(1, (len(pending) + CHUNK_SIZE - 1) // CHUNK_SIZE)
    print(f"Model: {model}")
    print(f"Preparing {len(pending):,} requests in {n_chunks} chunk(s) "
          f"(skipping {len(done):,} already validated).")

    chunk_files = []
    for i, start in enumerate(range(0, len(pending), CHUNK_SIZE), start=1):
        chunk = pending.iloc[start: start + CHUNK_SIZE]
        path  = _chunk_path(i)
        with open(path, "w") as f:
            for _, row in chunk.iterrows():
                request = {
                    "custom_id": str(row["GLOBALEVENTID"]),
                    "method":    "POST",
                    "url":       "/v1/chat/completions",
                    "body":      _model_request_body(model, build_messages(row.to_dict())),
                }
                f.write(json.dumps(request) + "\n")
        size_mb = path.stat().st_size / 1_048_576
        print(f"  Chunk {i}/{n_chunks}: {len(chunk):,} requests  "
              f"({size_mb:.0f} MB)  → {path.name}")
        chunk_files.append(str(path))

    plan = {"chunk_files": chunk_files}
    (BATCH_DIR / "batch_plan.json").write_text(json.dumps(plan, indent=2))
    print("Done. Run --submit to upload and submit the first chunk.")


# ---------------------------------------------------------------------------
# Submit / status / collect  (identical pattern to url_classifier)
# ---------------------------------------------------------------------------

def submit_batch():
    plan_path = BATCH_DIR / "batch_plan.json"
    if not plan_path.exists():
        print("No batch plan found. Run --prepare first.")
        sys.exit(1)

    client      = OpenAI()
    chunk_files = json.loads(plan_path.read_text())["chunk_files"]
    n_total     = len(chunk_files)

    batches = []
    if BATCH_META.exists():
        batches = json.loads(BATCH_META.read_text()).get("batches", [])

    submitted_chunks = {b["chunk"] for b in batches}
    next_chunks = [i for i in range(1, n_total + 1) if i not in submitted_chunks]

    if not next_chunks:
        print("All chunks already submitted. Run --status to check progress.")
        return

    i    = next_chunks[0]
    path = chunk_files[i - 1]
    print(f"Uploading chunk {i}/{n_total}: {path} ...")
    with open(path, "rb") as f:
        uploaded = client.files.create(file=f, purpose="batch")
    batch = client.batches.create(
        input_file_id=uploaded.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    print(f"Submitted: {batch.id}  status: {batch.status}")
    batches.append({"batch_id": batch.id, "file_id": uploaded.id, "chunk": i})
    BATCH_META.write_text(json.dumps({"batches": batches}, indent=2))

    remaining = len(next_chunks) - 1
    if remaining:
        print(f"\n{remaining} chunk(s) remaining. After this one completes, "
              f"run --submit again.")
    else:
        print("\nFinal chunk submitted.")
    print("Check with: python -m tools.geo_validator --status")


def check_status():
    client  = OpenAI()
    meta    = json.loads(BATCH_META.read_text())
    batches = meta.get("batches", [])

    all_done  = True
    total = completed = failed = 0
    for entry in batches:
        batch = client.batches.retrieve(entry["batch_id"])
        c = batch.request_counts
        total     += c.total
        completed += c.completed
        failed    += c.failed
        if batch.status != "completed":
            all_done = False
        label = f"chunk {entry['chunk']}" if len(batches) > 1 else "batch"
        print(f"{label}  {batch.id}: {batch.status}  "
              f"total={c.total}  completed={c.completed}  failed={c.failed}")

    if len(batches) > 1:
        print(f"\nOverall: total={total}  completed={completed}  failed={failed}")

    if all_done:
        print("All chunks complete — run: python -m tools.geo_validator --collect")
    return all_done


def collect_results():
    client  = OpenAI()
    meta    = json.loads(BATCH_META.read_text())
    batches = meta.get("batches", [])

    cache = pd.read_csv(ARTICLE_CACHE) if ARTICLE_CACHE.exists() else pd.DataFrame()
    if not cache.empty:
        cache["GLOBALEVENTID"] = cache["GLOBALEVENTID"].astype("int64")

    rows = []
    for entry in batches:
        if entry.get("collected"):
            print(f"Chunk {entry['chunk']} already collected — skipping.")
            continue
        batch = client.batches.retrieve(entry["batch_id"])
        if batch.status != "completed":
            print(f"Chunk {entry['chunk']} not ready (status: {batch.status}) — skipping.")
            continue
        print(f"Downloading chunk {entry['chunk']} (file: {batch.output_file_id}) ...")
        content = client.files.content(batch.output_file_id).text
        with open(BATCH_RESULTS, "a") as f:
            f.write(content)
        for line in content.strip().split("\n"):
            if line:
                result = parse_result_line(line)
                if result:
                    rows.append(result)
        entry["collected"] = True

    BATCH_META.write_text(json.dumps({"batches": batches}, indent=2))

    if not rows:
        print("No new completed chunks to collect.")
        sys.exit(0)

    results_df = pd.DataFrame(rows)
    results_df["GLOBALEVENTID"] = results_df["GLOBALEVENTID"].astype("int64")

    # Join back source_url and geo fields from cache
    if not cache.empty:
        geo_cols = ["GLOBALEVENTID", "SOURCEURL", "ActionGeo_FullName",
                    "ActionGeo_ADM1Code", "ActionGeo_CountryCode"]
        results_df = results_df.merge(
            cache[geo_cols], on="GLOBALEVENTID", how="left"
        )

    col_order = [
        "GLOBALEVENTID", "SOURCEURL", "ActionGeo_CountryCode",
        "ActionGeo_ADM1Code", "ActionGeo_FullName",
        "extracted_location", "match", "corrected_location", "reasoning",
    ]
    results_df = results_df[[c for c in col_order if c in results_df.columns]]

    if OUTPUT_CSV.exists():
        existing = pd.read_csv(OUTPUT_CSV)
        results_df = pd.concat([existing, results_df]).drop_duplicates("GLOBALEVENTID")

    results_df.to_csv(OUTPUT_CSV, index=False)
    counts = results_df["match"].value_counts()
    print(f"\nSaved {len(results_df):,} validations to {OUTPUT_CSV}")
    print(counts.to_string())
