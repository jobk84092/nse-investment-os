import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
from src.utils.paths import settings

# Drop obvious nav / chrome from NSE listing pages
_TITLE_DENY = frozenset({
    "home", "menu", "search", "login", "register", "twitter", "facebook", "linkedin",
    "youtube", "instagram", "subscribe", "newsletter", "contact", "privacy", "terms",
    "read more", "more", "next", "previous", "back", "skip to content", "cookie",
})


def _clean_title(text: str) -> str:
    t = " ".join(text.split()).strip()
    if len(t) < 8:
        return ""
    low = t.lower()
    if low in _TITLE_DENY or low.startswith("http"):
        return ""
    return t[:220]


def _scrape_links(url: str, source_name: str) -> pd.DataFrame:
    rows = []
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        for a in soup.find_all("a", href=True):
            text = _clean_title(a.get_text(" ", strip=True))
            href = (a.get("href") or "").strip()
            if not text or not href or href.startswith("#") or href.lower().startswith("javascript:"):
                continue
            abs_url = urljoin(resp.url, href)
            rows.append({
                "source": source_name,
                "title": text,
                "url": abs_url,
                "fetched_at": datetime.utcnow().isoformat()
            })
    except Exception as e:
        rows.append({
            "source": source_name,
            "title": f"ERROR: {e}",
            "url": url,
            "fetched_at": datetime.utcnow().isoformat()
        })
    return pd.DataFrame(rows)

def _filter_nse_detail_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop global nav; keep likely announcement / corporate-action detail URLs only."""
    if df.empty:
        return df

    def keep(row) -> bool:
        src = str(row.get("source", ""))
        u = str(row.get("url", "")).lower()
        if str(row.get("title", "")).startswith("ERROR"):
            return True
        if src == "listed_announcements":
            if "/listed-company-announcements/" not in u:
                return False
            tail = u.split("/listed-company-announcements/", 1)[-1].split("?", 1)[0].strip("/")
            return bool(tail)
        if src == "corporate_actions":
            if "/corporate-actions/" not in u:
                return False
            tail = u.split("/corporate-actions/", 1)[-1].split("?", 1)[0].strip("/")
            return bool(tail)
        return True

    return df[df.apply(keep, axis=1)].reset_index(drop=True)


def scrape_nse_link_surface() -> pd.DataFrame:
    """All anchor tags from the two NSE pages (includes site navigation)."""
    cfg = settings()["nse_sources"]
    parts = [
        _scrape_links(cfg["listed_announcements_url"], "listed_announcements"),
        _scrape_links(cfg["corporate_actions_url"], "corporate_actions"),
    ]
    df = pd.concat(parts, ignore_index=True)
    if df.empty:
        return df
    return df.drop_duplicates(subset=["title", "url"]).reset_index(drop=True)


def nse_news_filtered_and_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = scrape_nse_link_surface()
    return _filter_nse_detail_rows(raw.copy()), raw


def fetch_nse_news() -> pd.DataFrame:
    filtered, _ = nse_news_filtered_and_raw()
    return filtered
