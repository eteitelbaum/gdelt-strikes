"""Concurrent title fetching with Wayback Machine fallback."""

import html as html_lib
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests

FETCH_TIMEOUT   = 5        # seconds for direct fetch
WAYBACK_TIMEOUT = 8        # seconds for Wayback Machine fetch
FETCH_WORKERS   = 25       # concurrent title-fetch threads
FETCH_MAX_BYTES = 32_768   # stop reading after 32 KB (enough to find <title>)

# Browser-like UA to reduce blocks
FETCH_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Titles that indicate a dead/redirect page rather than real content
DEAD_TITLE_FRAGMENTS = {
    "404", "not found", "page not found", "error", "access denied",
    "forbidden", "unavailable", "just a moment", "attention required",
    "site not found", "domain for sale", "parked domain",
}


def _extract_title(content: bytes) -> str | None:
    text = content.decode("utf-8", errors="replace")
    match = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    title = html_lib.unescape(match.group(1).strip())
    title = re.sub(r"\s+", " ", title)[:300]
    if len(title) < 8:
        return None
    if any(frag in title.lower() for frag in DEAD_TITLE_FRAGMENTS):
        return None
    return title


def _fetch_direct(url: str) -> str | None:
    try:
        resp = requests.get(
            url, timeout=FETCH_TIMEOUT,
            headers={"User-Agent": FETCH_UA},
            stream=True, allow_redirects=True,
        )
        resp.raise_for_status()
        content = b""
        for chunk in resp.iter_content(chunk_size=4096):
            content += chunk
            if b"</title>" in content.lower() or len(content) >= FETCH_MAX_BYTES:
                break
        return _extract_title(content)
    except Exception:
        return None


def _fetch_wayback(url: str) -> str | None:
    try:
        avail = requests.get(
            f"https://archive.org/wayback/available?url={url}",
            timeout=WAYBACK_TIMEOUT,
        ).json()
        snapshot = avail.get("archived_snapshots", {}).get("closest", {})
        if snapshot.get("available"):
            return _fetch_direct(snapshot["url"])
    except Exception:
        pass
    return None


def fetch_title(url: str, try_wayback: bool = True) -> tuple[str | None, str]:
    """Returns (title, source) where source is 'direct', 'wayback', or 'none'."""
    if not url or not url.startswith("http"):
        return None, "none"
    title = _fetch_direct(url)
    if title:
        return title, "direct"
    if try_wayback:
        title = _fetch_wayback(url)
        if title:
            return title, "wayback"
    return None, "none"


def fetch_all_titles(df: pd.DataFrame, try_wayback: bool = True) -> pd.DataFrame:
    """Concurrently fetch titles for all URLs in df. Adds 'title' and 'title_source' columns."""
    results = {}

    def _worker(row):
        title, source = fetch_title(row["source_url"], try_wayback=try_wayback)
        return row["GLOBALEVENTID"], title, source

    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
        futures = {pool.submit(_worker, row): row["GLOBALEVENTID"]
                   for _, row in df.iterrows()}
        done = 0
        for future in as_completed(futures):
            event_id, title, source = future.result()
            results[event_id] = (title, source)
            done += 1
            if done % 100 == 0:
                fetched = sum(1 for t, _ in results.values() if t)
                print(f"  {done}/{len(df)} fetched — {fetched} titles retrieved so far")

    df = df.copy()
    df["title"]        = df["GLOBALEVENTID"].map(lambda i: results.get(i, (None, "none"))[0])
    df["title_source"] = df["GLOBALEVENTID"].map(lambda i: results.get(i, (None, "none"))[1])
    return df
