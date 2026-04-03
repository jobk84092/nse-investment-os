from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

import feedparser
import pandas as pd
import requests
from bs4 import BeautifulSoup


def _entry_published(entry: Any) -> str:
    for attr in ("published", "updated", "created"):
        v = getattr(entry, attr, None)
        if v:
            return str(v)[:80]
    return ""


def _http_headers() -> dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (compatible; NSE-Investment-OS/1.0; +local research)",
        "Accept": "application/rss+xml, application/xml, text/xml, text/html, */*",
    }


def _site_host(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def fetch_homepage_article_links(homepage_url: str, label: str, max_items: int) -> pd.DataFrame:
    """When RSS is broken, grab likely story links from the site homepage."""
    rows: list[dict[str, str]] = []
    try:
        resp = requests.get(homepage_url, timeout=25, headers=_http_headers())
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        want_host = _site_host(homepage_url)
        seen: set[str] = set()
        for a in soup.find_all("a", href=True):
            text = " ".join(a.get_text(" ", strip=True).split())
            if len(text) < 28:
                continue
            href = (a.get("href") or "").strip()
            if not href or href.startswith("#"):
                continue
            abs_u = urljoin(homepage_url, href)
            if _site_host(abs_u) != want_host:
                continue
            if abs_u in seen:
                continue
            path = urlparse(abs_u).path.lower()
            if any(x in path for x in ("/wp-admin", "/login", "/feed", "/category/", "/author/", "/tag/", "/page/")):
                continue
            if path in ("/", ""):
                continue
            seen.add(abs_u)
            rows.append(
                {
                    "feed_label": label,
                    "title": text[:300],
                    "link": abs_u,
                    "published": "",
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            if len(rows) >= max_items:
                break
    except Exception as ex:
        rows.append(
            {
                "feed_label": label,
                "title": f"Homepage fallback ERROR: {ex}",
                "link": homepage_url,
                "published": "",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    return pd.DataFrame(rows)


def fetch_rss_feed(
    feed_url: str,
    label: str,
    max_items: int,
    homepage_fallback: str | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    if not (feed_url or "").strip():
        return pd.DataFrame(rows)
    try:
        resp = requests.get(feed_url, timeout=25, headers=_http_headers())
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
        if getattr(parsed, "bozo", False) and not parsed.entries:
            fb = (homepage_fallback or "").strip()
            if fb:
                return fetch_homepage_article_links(fb, label, max_items)
            rows.append(
                {
                    "feed_label": label,
                    "title": f"RSS parse issue: {getattr(parsed, 'bozo_exception', 'unknown')}",
                    "link": feed_url,
                    "published": "",
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            return pd.DataFrame(rows)
        for e in parsed.entries[: max(0, int(max_items))]:
            title = " ".join((e.get("title") or "").split()).strip()
            link = (e.get("link") or "").strip()
            if not title or not link:
                continue
            rows.append(
                {
                    "feed_label": label,
                    "title": title[:300],
                    "link": link,
                    "published": _entry_published(e),
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
            )
    except Exception as ex:
        rows.append(
            {
                "feed_label": label,
                "title": f"ERROR: {ex}",
                "link": feed_url,
                "published": "",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    return pd.DataFrame(rows)


def fetch_all_rss_feeds(feeds_cfg: list[dict[str, Any]], max_per_feed: int) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for item in feeds_cfg:
        url = (item.get("url") or "").strip()
        label = (item.get("label") or "RSS").strip()
        if not url:
            continue
        fb = (item.get("homepage_fallback") or "").strip()
        parts.append(fetch_rss_feed(url, label, max_per_feed, homepage_fallback=fb or None))
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)
