# URL Classifier

Two-pass LLM pipeline for filtering GDELT strike events by relevance.
Classifies each event's `SOURCEURL` as `relevant`, `not_relevant`, or
`uncertain` using OpenAI's gpt-4o-mini via the Batch API.

**Pass 1** classifies URLs directly. **Pass 2** fetches article titles for
`uncertain` events (with Wayback Machine fallback) and reclassifies using
both the URL and title together.

See `notes/url-classifier-prompt-development.md` for a full account of the
prompt design and calibration process.

---

## Setup

**1. Create and activate a virtual environment** (from the repo root):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r tools/url_classifier/requirements.txt
```

**2. Add your OpenAI API key** to `.env` in the repo root:

```
OPENAI_API_KEY=sk-...
```

---

## Full Run (Production)

Run these commands from the **repo root** with the virtual environment active.

### Pass 1

```bash
# Build batch JSONL from the input parquet
python -m tools.url_classifier --prepare

# Upload to OpenAI and submit batch job
python -m tools.url_classifier --submit

# Check status (repeat until "completed")
python -m tools.url_classifier --status

# Download results → data/enhanced/url_classifications.csv
python -m tools.url_classifier --collect
```

The batch runs on OpenAI's servers — your machine does not need to stay
awake between `--submit` and `--collect`. Expect 1–4 hours for ~30k events.

### Pass 2

```bash
# Fetch titles for uncertain events and build pass2 JSONL
# (runs locally — keep machine awake, ~20–40 min)
caffeinate -i python -m tools.url_classifier --pass2-prepare

# Submit pass2 batch
python -m tools.url_classifier --pass2-submit

# Check status
python -m tools.url_classifier --pass2-status

# Download results and update url_classifications.csv in place
python -m tools.url_classifier --pass2-collect
```

To skip the Wayback Machine fallback during title fetching (faster, fewer
network calls):

```bash
caffeinate -i python -m tools.url_classifier --pass2-prepare --no-wayback
```

---

## Testing

Run a quick direct-API test on a sample of URLs before committing to the
full batch. Results are saved to `data/test/` with a timestamp.

```bash
# Test Pass 1 on 100 URLs (uses random_state=99 — same sample every time)
python -m tools.url_classifier --test 100

# Test Pass 2 on uncertain events from the most recent Pass 1 test
python -m tools.url_classifier --pass2-test 20
```

To test on a different sample, change `random_state` in `classify.py:run_test`.

---

## Output

**`data/enhanced/url_classifications.csv`**

| Column | Description |
|--------|-------------|
| `GLOBALEVENTID` | GDELT event identifier |
| `source_url` | The classified URL |
| `classification` | `relevant`, `not_relevant`, or `uncertain` |
| `reasoning` | One-sentence explanation from the model |

After Pass 2 completes, `uncertain` rows from Pass 1 are replaced in place
with the Pass 2 classifications. Events that remain `uncertain` after both
passes should be treated as missing data in downstream analysis.

**`data/test/`**

Timestamped test outputs from `--test` and `--pass2-test` runs. Pass 2 test
files also include `title` and `title_source` (`direct`, `wayback`, or
`none`) columns.

---

## Intermediary Files

The following files are created during a run and are gitignored:

| File | Description |
|------|-------------|
| `tools/url_classifier/batch_requests.jsonl` | Pass 1 batch input |
| `tools/url_classifier/batch_meta.json` | Pass 1 batch ID (needed for status/collect) |
| `tools/url_classifier/batch_results.jsonl` | Pass 1 raw results from OpenAI |
| `tools/url_classifier/pass2_batch_requests.jsonl` | Pass 2 batch input |
| `tools/url_classifier/pass2_batch_meta.json` | Pass 2 batch ID |
| `tools/url_classifier/pass2_batch_results.jsonl` | Pass 2 raw results |
| `tools/url_classifier/uncertain_titles.csv` | Cached titles from Pass 2 fetch step |

`batch_meta.json` and `pass2_batch_meta.json` persist the OpenAI batch IDs
between terminal sessions, so `--status` and `--collect` work even if you
close and reopen your terminal after submitting.

---

## Module Structure

```
tools/url_classifier/
├── __init__.py
├── __main__.py       # enables python -m tools.url_classifier
├── classify.py       # CLI entry point, run_test(), test_pass2()
├── prompts.py        # system prompts, few-shot examples, message builders
├── batch.py          # Batch API plumbing for pass1 and pass2
├── fetch.py          # concurrent title fetching, Wayback Machine fallback
├── data.py           # path constants, load_events(), already_classified()
└── requirements.txt
```

---

## Cost Estimates

Based on test runs with gpt-4o-mini pricing ($0.15/1M input, $0.60/1M output):

| Step | Events | Estimated cost |
|------|--------|---------------|
| Pass 1 (batch, 50% discount) | ~30,900 | ~$4–5 |
| Pass 2 (batch, 50% discount) | ~8,000–10,000 uncertain | ~$0.70 |
| **Total** | | **~$5–6** |

Direct API calls (used in `--test`) cost roughly 2× the batch price.
