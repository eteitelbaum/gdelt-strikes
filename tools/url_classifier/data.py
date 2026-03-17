"""Path constants and data I/O for the URL classifier."""

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]

INPUT_PARQUET  = ROOT / "data/enhanced/gdelt_strikes.parquet"
OUTPUT_CSV     = ROOT / "data/enhanced/url_classifications.csv"
BATCH_DIR      = ROOT / "tools/url_classifier"

BATCH_JSONL    = BATCH_DIR / "batch_requests.jsonl"
BATCH_META     = BATCH_DIR / "batch_meta.json"
BATCH_RESULTS  = BATCH_DIR / "batch_results.jsonl"

PASS2_BATCH_JSONL   = BATCH_DIR / "pass2_batch_requests.jsonl"
PASS2_BATCH_META    = BATCH_DIR / "pass2_batch_meta.json"
PASS2_BATCH_RESULTS = BATCH_DIR / "pass2_batch_results.jsonl"
TITLES_CACHE        = BATCH_DIR / "uncertain_titles.csv"


def load_events() -> pd.DataFrame:
    table = pq.read_table(INPUT_PARQUET, columns=["GLOBALEVENTID", "SOURCEURL"])
    df = table.to_pandas()
    df = df.dropna(subset=["SOURCEURL"])
    df = df.drop_duplicates(subset=["GLOBALEVENTID"])
    return df


def already_classified() -> set:
    """Return set of GLOBALEVENTID values already in the output CSV."""
    if OUTPUT_CSV.exists():
        done = pd.read_csv(OUTPUT_CSV, usecols=["GLOBALEVENTID"])
        return set(done["GLOBALEVENTID"].tolist())
    return set()
