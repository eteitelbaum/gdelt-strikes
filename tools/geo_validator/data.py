"""Path constants and data I/O for the geo validator."""

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]

INPUT_PARQUET      = ROOT / "data/enhanced/gdelt_strikes.parquet"
CLASSIFICATIONS_CSV = ROOT / "data/enhanced/url_classifications.csv"
OUTPUT_CSV         = ROOT / "data/enhanced/geo_validation.csv"
BATCH_DIR          = ROOT / "tools/geo_validator"

ARTICLE_CACHE      = BATCH_DIR / "article_texts_cache.csv"
BATCH_JSONL        = BATCH_DIR / "batch_requests.jsonl"
BATCH_META         = BATCH_DIR / "batch_meta.json"
BATCH_RESULTS      = BATCH_DIR / "batch_results.jsonl"

GEO_COLS = [
    "GLOBALEVENTID",
    "SOURCEURL",
    "ActionGeo_FullName",
    "ActionGeo_ADM1Code",
    "ActionGeo_CountryCode",
]


def load_relevant_events() -> pd.DataFrame:
    """Load the relevant-only subset with geographic columns."""
    events = pq.read_table(INPUT_PARQUET, columns=GEO_COLS).to_pandas()
    events["GLOBALEVENTID"] = events["GLOBALEVENTID"].astype("int64")

    classifications = pd.read_csv(CLASSIFICATIONS_CSV, usecols=["GLOBALEVENTID", "classification"])
    classifications["GLOBALEVENTID"] = classifications["GLOBALEVENTID"].astype("int64")

    relevant_ids = classifications[classifications["classification"] == "relevant"]["GLOBALEVENTID"]
    return events[events["GLOBALEVENTID"].isin(relevant_ids)].drop_duplicates("GLOBALEVENTID").reset_index(drop=True)


def already_validated() -> set:
    """Return set of GLOBALEVENTID values already in the output CSV."""
    if OUTPUT_CSV.exists():
        done = pd.read_csv(OUTPUT_CSV, usecols=["GLOBALEVENTID"])
        return set(done["GLOBALEVENTID"].tolist())
    return set()
