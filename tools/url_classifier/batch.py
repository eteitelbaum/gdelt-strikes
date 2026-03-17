"""OpenAI Batch API plumbing for pass1 and pass2 classification."""

import json
import sys

import pandas as pd
from openai import OpenAI

from .data import (
    BATCH_JSONL, BATCH_META, BATCH_RESULTS, OUTPUT_CSV,
    PASS2_BATCH_JSONL, PASS2_BATCH_META, PASS2_BATCH_RESULTS, TITLES_CACHE,
    already_classified, load_events,
)
from .fetch import FETCH_WORKERS, fetch_all_titles
from .prompts import (
    SYSTEM_PROMPT, PASS2_SYSTEM_PROMPT,
    build_user_message, build_pass2_user_message,
)

MODEL       = "gpt-4o-mini"
PASS2_MODEL = "gpt-4o-mini"

# Max requests per batch chunk — keeps files well under OpenAI's 200 MB limit
CHUNK_SIZE  = 10_000   # ~17.8M tokens/chunk, under OpenAI's 20M enqueued-token limit


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def parse_result_line(line: str) -> dict | None:
    """Parse one JSONL result line into a flat dict, or None on failure."""
    try:
        obj = json.loads(line)
        event_id = int(obj["custom_id"])
        body = obj["response"]["body"]
        content = body["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return {
            "GLOBALEVENTID": event_id,
            "classification": parsed.get("classification", "uncertain"),
            "reasoning": parsed.get("reasoning", ""),
        }
    except Exception as e:
        print(f"  parse error: {e} — line: {line[:120]}")
        return None


# ---------------------------------------------------------------------------
# Pass 1
# ---------------------------------------------------------------------------

def _chunk_path(i: int) -> "Path":
    from .data import BATCH_DIR
    return BATCH_DIR / f"batch_requests_{i:03d}.jsonl"


def prepare_batch(sample: int | None = None):
    from .data import BATCH_DIR
    df = load_events()
    done = already_classified()
    pending = df[~df["GLOBALEVENTID"].isin(done)]

    if sample:
        pending = pending.sample(min(sample, len(pending)), random_state=42)

    n_chunks = max(1, (len(pending) + CHUNK_SIZE - 1) // CHUNK_SIZE)
    print(f"Preparing {len(pending):,} requests in {n_chunks} chunk(s) "
          f"(skipping {len(done):,} already classified).")

    chunk_files = []
    for i, start in enumerate(range(0, len(pending), CHUNK_SIZE), start=1):
        chunk = pending.iloc[start : start + CHUNK_SIZE]
        path = _chunk_path(i)
        with open(path, "w") as f:
            for _, row in chunk.iterrows():
                request = {
                    "custom_id": str(row["GLOBALEVENTID"]),
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": MODEL,
                        "temperature": 0,
                        "max_tokens": 80,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": build_user_message(row["SOURCEURL"])},
                        ],
                    },
                }
                f.write(json.dumps(request) + "\n")
        size_mb = path.stat().st_size / 1_048_576
        print(f"  Chunk {i}/{n_chunks}: {len(chunk):,} requests  ({size_mb:.0f} MB)  → {path.name}")
        chunk_files.append(str(path))

    # Write a plan file listing all chunk paths for submit to pick up
    plan = {"chunk_files": chunk_files}
    (BATCH_DIR / "batch_plan.json").write_text(json.dumps(plan, indent=2))
    print("Done. Run --submit to upload and submit all chunks.")


def submit_batch():
    """Submit the next unsubmitted chunk. Run repeatedly after each chunk completes."""
    from .data import BATCH_DIR
    plan_path = BATCH_DIR / "batch_plan.json"
    if not plan_path.exists():
        print("No batch plan found. Run --prepare first.")
        sys.exit(1)

    client = OpenAI()
    chunk_files = json.loads(plan_path.read_text())["chunk_files"]
    n_total = len(chunk_files)

    # Load already-submitted batches
    batches = []
    if BATCH_META.exists():
        batches = json.loads(BATCH_META.read_text()).get("batches", [])

    submitted_chunks = {b["chunk"] for b in batches}
    next_chunks = [i for i in range(1, n_total + 1) if i not in submitted_chunks]

    if not next_chunks:
        print("All chunks already submitted. Run --status to check progress.")
        return

    i = next_chunks[0]
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
        print(f"\n{remaining} chunk(s) remaining. After this one completes, run --submit again.")
    else:
        print("\nFinal chunk submitted.")
    print("Check with: python -m tools.url_classifier --status")


def check_status():
    client = OpenAI()
    meta = json.loads(BATCH_META.read_text())
    batches = meta.get("batches") or [{"batch_id": meta["batch_id"], "chunk": 1}]

    all_done = True
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
        print("All chunks complete — run: python -m tools.url_classifier --collect")
    return all_done


def collect_results():
    client = OpenAI()
    meta = json.loads(BATCH_META.read_text())
    batches = meta.get("batches") or [{"batch_id": meta["batch_id"], "chunk": 1}]

    rows = []
    newly_collected = []
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
        newly_collected.append(entry["chunk"])

    # Persist collected flags
    BATCH_META.write_text(json.dumps({"batches": batches}, indent=2))

    if not rows:
        print("No new completed chunks to collect.")
        sys.exit(0)

    results_df = pd.DataFrame(rows)
    results_df["GLOBALEVENTID"] = results_df["GLOBALEVENTID"].astype("int64")
    events_df = load_events()[["GLOBALEVENTID", "SOURCEURL"]].rename(
        columns={"SOURCEURL": "source_url"}
    )
    events_df["GLOBALEVENTID"] = events_df["GLOBALEVENTID"].astype("int64")
    results_df = results_df.merge(events_df, on="GLOBALEVENTID", how="left")
    results_df = results_df[["GLOBALEVENTID", "source_url", "classification", "reasoning"]]

    if OUTPUT_CSV.exists():
        existing = pd.read_csv(OUTPUT_CSV)
        results_df = pd.concat([existing, results_df]).drop_duplicates(
            subset=["GLOBALEVENTID"]
        )

    results_df.to_csv(OUTPUT_CSV, index=False)
    counts = results_df["classification"].value_counts()
    print(f"\nSaved {len(results_df):,} classifications to {OUTPUT_CSV}")
    print(counts.to_string())


# ---------------------------------------------------------------------------
# Pass 2
# ---------------------------------------------------------------------------

def prepare_pass2(try_wayback: bool = True):
    """Fetch titles for uncertain events and build pass2 batch JSONL."""
    if not OUTPUT_CSV.exists():
        print(f"No classifications CSV found at {OUTPUT_CSV}. Run --collect first.")
        sys.exit(1)

    classified = pd.read_csv(OUTPUT_CSV)
    uncertain = classified[classified["classification"] == "uncertain"].copy()
    print(f"Found {len(uncertain):,} uncertain events to reclassify.")

    if TITLES_CACHE.exists():
        print(f"Loading cached titles from {TITLES_CACHE}")
        cached = pd.read_csv(TITLES_CACHE)
        uncertain = uncertain.merge(cached[["GLOBALEVENTID", "title", "title_source"]],
                                    on="GLOBALEVENTID", how="left")
    else:
        print(f"Fetching titles (up to {FETCH_WORKERS} concurrent, wayback={'on' if try_wayback else 'off'})...")
        uncertain = fetch_all_titles(uncertain, try_wayback=try_wayback)
        uncertain[["GLOBALEVENTID", "source_url", "title", "title_source"]].to_csv(
            TITLES_CACHE, index=False
        )
        n_fetched = uncertain["title"].notna().sum()
        print(f"Titles fetched: {n_fetched:,}/{len(uncertain):,} "
              f"({n_fetched/len(uncertain)*100:.1f}%)")

    with open(PASS2_BATCH_JSONL, "w") as f:
        for _, row in uncertain.iterrows():
            request = {
                "custom_id": str(row["GLOBALEVENTID"]),
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": PASS2_MODEL,
                    "temperature": 0,
                    "max_tokens": 80,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": PASS2_SYSTEM_PROMPT},
                        {"role": "user",   "content": build_pass2_user_message(
                            row["source_url"], row.get("title")
                        )},
                    ],
                },
            }
            f.write(json.dumps(request) + "\n")
    print(f"Wrote {PASS2_BATCH_JSONL}")


def submit_pass2():
    client = OpenAI()
    print(f"Uploading {PASS2_BATCH_JSONL} ...")
    with open(PASS2_BATCH_JSONL, "rb") as f:
        uploaded = client.files.create(file=f, purpose="batch")
    batch = client.batches.create(
        input_file_id=uploaded.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    PASS2_BATCH_META.write_text(json.dumps({"batch_id": batch.id, "file_id": uploaded.id}, indent=2))
    print(f"Pass 2 batch submitted: {batch.id}")
    print(f"Check with: python -m url_classifier --pass2-status")


def check_pass2_status():
    client = OpenAI()
    meta = json.loads(PASS2_BATCH_META.read_text())
    batch = client.batches.retrieve(meta["batch_id"])
    counts = batch.request_counts
    print(
        f"Pass 2 batch {batch.id}: {batch.status}\n"
        f"  total={counts.total}  completed={counts.completed}  failed={counts.failed}"
    )
    if batch.status == "completed":
        print("Ready — run: python -m url_classifier --pass2-collect")


def collect_pass2():
    """Download pass2 results and update main classifications CSV."""
    client = OpenAI()
    meta = json.loads(PASS2_BATCH_META.read_text())
    batch = client.batches.retrieve(meta["batch_id"])
    if batch.status != "completed":
        print(f"Pass 2 batch not ready (status: {batch.status}).")
        sys.exit(1)

    content = client.files.content(batch.output_file_id).text
    PASS2_BATCH_RESULTS.write_text(content)

    rows = []
    for line in content.strip().split("\n"):
        if line:
            result = parse_result_line(line)
            if result:
                rows.append(result)

    pass2_df = pd.DataFrame(rows)

    classified = pd.read_csv(OUTPUT_CSV)
    pass2_df = pass2_df.merge(
        classified[["GLOBALEVENTID", "source_url"]], on="GLOBALEVENTID", how="left"
    )

    updated = classified[classified["classification"] != "uncertain"].copy()
    pass2_df = pass2_df[["GLOBALEVENTID", "source_url", "classification", "reasoning"]]
    final = pd.concat([updated, pass2_df]).sort_values("GLOBALEVENTID").reset_index(drop=True)
    final.to_csv(OUTPUT_CSV, index=False)

    counts = pass2_df["classification"].value_counts()
    print(f"\nPass 2 complete — updated {OUTPUT_CSV}")
    print(f"Reclassified {len(pass2_df):,} uncertain events:")
    print(counts.to_string())
