"""Fetch article body text with Wayback Machine fallback."""

import concurrent.futures
import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

FETCH_TIMEOUT   = 8
WAYBACK_TIMEOUT = 12
FETCH_WORKERS   = 20
FETCH_MAX_BYTES = 131_072   # 128 KB — enough to capture article body
MAX_TEXT_CHARS  = 3_000     # truncate extracted text to this many characters

FETCH_UA = (
    "Mozilla/5.0 (compatible; GDELTStrikeResearch/1.0; "
    "+https://github.com/eteitelbaum/gdelt-strikes)"
)

# Fragments that indicate a page is a redirect or error, not real content
DEAD_PAGE_FRAGMENTS = [
    "page not found", "404", "access denied", "subscription required",
    "please enable javascript", "just a moment", "captcha",
    "this page has moved", "article not found",
]


def _extract_article_text(html: str) -> str:
    """Extract clean article body text from HTML using BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove noise tags
    for tag in soup(["script", "style", "nav", "header", "footer",
                     "aside", "form", "figure", "figcaption"]):
        tag.decompose()

    # Try to find the main article body
    article = (
        soup.find("article")
        or soup.find(attrs={"class": re.compile(r"article|story|content|body|post", re.I)})
        or soup.find("main")
        or soup.body
    )
    if article is None:
        return ""

    # Collect paragraph text
    paragraphs = article.find_all(["p", "h1", "h2", "h3"])
    text = " ".join(p.get_text(" ", strip=True) for p in paragraphs)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:MAX_TEXT_CHARS]


def _fetch_direct(url: str) -> str | None:
    """Fetch article text directly. Returns text or None on failure."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": FETCH_UA},
            timeout=FETCH_TIMEOUT,
            stream=True,
        )
        if resp.status_code != 200:
            return None
        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type:
            return None

        raw = b""
        for chunk in resp.iter_content(chunk_size=4096):
            raw += chunk
            if len(raw) >= FETCH_MAX_BYTES:
                break
        html = raw.decode("utf-8", errors="replace")

        # Check for dead pages
        snippet = html[:2000].lower()
        if any(frag in snippet for frag in DEAD_PAGE_FRAGMENTS):
            return None

        text = _extract_article_text(html)
        return text if len(text) > 80 else None
    except Exception:
        return None


def _fetch_wayback(url: str) -> str | None:
    """Try to fetch article text via the Wayback Machine CDX + content API."""
    try:
        cdx = requests.get(
            "https://web.archive.org/cdx/search/cdx",
            params={
                "url": url, "output": "json", "limit": 1,
                "fl": "timestamp,statuscode", "filter": "statuscode:200",
                "collapse": "digest",
            },
            timeout=WAYBACK_TIMEOUT,
        )
        if cdx.status_code != 200:
            return None
        rows = cdx.json()
        if len(rows) < 2:
            return None
        timestamp = rows[1][0]
        wb_url = f"https://web.archive.org/web/{timestamp}/{url}"
        return _fetch_direct(wb_url)
    except Exception:
        return None


def fetch_article(url: str, try_wayback: bool = True) -> tuple[str | None, str]:
    """
    Fetch article body text for a URL.

    Returns (text, source) where source is 'direct', 'wayback', or 'none'.
    """
    text = _fetch_direct(url)
    if text:
        return text, "direct"
    if try_wayback:
        text = _fetch_wayback(url)
        if text:
            return text, "wayback"
    return None, "none"


def fetch_all_articles(
    df: pd.DataFrame,
    try_wayback: bool = True,
) -> pd.DataFrame:
    """
    Fetch article text for all rows in df (must have GLOBALEVENTID, SOURCEURL).

    Adds columns: article_text, article_source ('direct'|'wayback'|'none').
    """
    urls = df["SOURCEURL"].tolist()
    ids  = df["GLOBALEVENTID"].tolist()
    n    = len(urls)

    results: dict[int, tuple[str | None, str]] = {}

    def _worker(args):
        eid, url = args
        return eid, fetch_article(url, try_wayback=try_wayback)

    with concurrent.futures.ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
        futures = {pool.submit(_worker, (eid, url)): eid
                   for eid, url in zip(ids, urls)}
        done = 0
        for fut in concurrent.futures.as_completed(futures):
            eid, (text, src) = fut.result()
            results[eid] = (text, src)
            done += 1
            if done % 500 == 0 or done == n:
                fetched = sum(1 for t, _ in results.values() if t)
                print(f"  {done:,}/{n:,} fetched — {fetched:,} with text "
                      f"({fetched/done*100:.1f}%)")

    df = df.copy()
    df["article_text"]   = df["GLOBALEVENTID"].map(lambda i: results[i][0])
    df["article_source"] = df["GLOBALEVENTID"].map(lambda i: results[i][1])
    return df
