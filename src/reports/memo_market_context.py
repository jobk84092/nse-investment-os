"""
Memo sections: NSE pages, RSS headlines, manual commentary, Ndindi-style tracker.
"""
from __future__ import annotations

from typing import Any

import pandas as pd


def _md_bullet_link(title: str, url: str) -> str:
    t = (title or "").strip()
    u = (url or "").strip()
    if not t or not u:
        return ""
    t = t.replace("<", "(").replace(">", ")")
    safe = t.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
    return f"- [{safe}]({u})"


def _take_nse_subset(news: pd.DataFrame, source_key: str, max_items: int) -> pd.DataFrame:
    if news.empty or "source" not in news.columns:
        return pd.DataFrame()
    sub = news[news["source"] == source_key].copy()
    sub = sub[~sub["title"].astype(str).str.startswith("ERROR", na=False)]
    sub = sub.drop_duplicates(subset=["title", "url"]).head(max_items)
    return sub


def lines_ndindi_tracker(ndindi: pd.DataFrame) -> list[str]:
    lines: list[str] = []
    if ndindi.empty or "ticker" not in ndindi.columns:
        return lines
    note_col = "tracking_note" if "tracking_note" in ndindi.columns else None
    if not note_col:
        return lines
    lines.append("### Ndindi-style tracker (your notes)")
    lines.append("")
    lines.append(
        "Short notes you maintain in `data/manual/ndindi_tracker.csv` (not live quotes from any public figure)."
    )
    lines.append("")
    for _, r in ndindi.iterrows():
        t = str(r.get("ticker", "")).strip().upper()
        n = str(r.get(note_col, "")).strip()
        if not t:
            continue
        hint = str(r.get("conviction_hint", "")).strip()
        tail = f" — *{hint}*" if hint else ""
        lines.append(f"- **{t}**: {n}{tail}" if n else f"- **{t}**{tail}")
    return lines


def lines_manual_commentary(commentary: pd.DataFrame) -> list[str]:
    lines: list[str] = [
        "### Expert & NSE voices you curate (your “what are they saying?” queue)",
        "",
        "This is where **your** trusted analysts and commentators live. Paste fresh links into `data/manual/market_commentary.csv` "
        "(columns: `voice`, `published` optional, `headline`, `url`) after each podcast, thread, or note you want to act on later. "
        "Respect copyright and site terms.",
        "",
    ]
    if commentary.empty:
        lines.append("- *(No rows yet.)* Add at least one headline + URL you want to remember this month.")
        lines.append("")
        return lines
    colmap = {str(c).strip().lower(): c for c in commentary.columns}
    if "headline" not in colmap or "url" not in colmap:
        lines.append("- *(Fix CSV headers.)* Required columns: `voice`, `headline`, `url`.")
        lines.append("")
        return lines
    vcol = colmap.get("voice") or colmap.get("source")
    hcol = colmap["headline"]
    ucol = colmap["url"]
    dcol = colmap.get("published") or colmap.get("date")
    added = 0
    for _, r in commentary.iterrows():
        voice = str(r[vcol]).strip() if vcol else "Commentary"
        raw_h = r[hcol]
        raw_u = r[ucol]
        if pd.isna(raw_h) or pd.isna(raw_u):
            continue
        head = str(raw_h).strip()
        url = str(raw_u).strip()
        if not head or not url:
            continue
        when = ""
        if dcol:
            d = str(r[dcol]).strip()
            if d:
                when = f" ({d})"
        bl = _md_bullet_link(f"{voice}{when}: {head}", url)
        if bl:
            lines.append(bl)
            added += 1
    if added == 0:
        lines.append("- *(No valid rows.)* Fill in `headline` and `url` for each voice you track.")
    lines.append("")
    return lines


def lines_rss_headlines(rss: pd.DataFrame) -> list[str]:
    lines: list[str] = []
    if rss.empty:
        return lines
    lines.append("### Investment headlines (RSS)")
    lines.append("")
    lines.append(
        "Headlines from feeds in `config/settings.json` → `memo_enrichment.rss_feeds`. "
        "Verify URLs periodically; publishers change feed paths."
    )
    lines.append("")
    cur_label: str | None = None
    for _, r in rss.iterrows():
        label = str(r.get("feed_label", "Feed")).strip()
        title = str(r.get("title", "")).strip()
        link = str(r.get("link", "")).strip()
        if label != cur_label:
            if cur_label is not None:
                lines.append("")
            lines.append(f"#### {label}")
            lines.append("")
            cur_label = label
        pub = str(r.get("published", "")).strip()
        suffix = f" — _{pub}_" if pub else ""
        bl = _md_bullet_link(f"{title}{suffix}", link)
        if bl:
            lines.append(bl)
    lines.append("")
    return lines


def lines_nse_sections(news: pd.DataFrame, max_per: int) -> list[str]:
    lines: list[str] = []
    if news.empty:
        lines.append("### NSE corporate actions")
        lines.append("")
        lines.append(
            "- No rows after filtering (or scrape failed). Announcement tables are often loaded in the browser; "
            "check `nse_sources` in the browser or paste links into `data/manual/market_commentary.csv`."
        )
        lines.append("")
        lines.append("### Listed company announcements (NSE)")
        lines.append("")
        lines.append(
            "- Same as above: use the live NSE site, or add items to `market_commentary.csv`. "
            "Full anchor scrape (noisy) is in `data/raw/nse_news_links_all.csv`; filtered rows in `nse_news_links.csv`."
        )
        lines.append("")
        return lines

    lines.append("### NSE corporate actions")
    lines.append("")
    ca = _take_nse_subset(news, "corporate_actions", max_per)
    if ca.empty:
        lines.append(
            "- No detail links matched the filter (many NSE tables load in the browser). "
            "Open the corporate-actions page manually or paste PDF links into `data/manual/market_commentary.csv`."
        )
    else:
        for _, r in ca.iterrows():
            bl = _md_bullet_link(str(r["title"]), str(r["url"]))
            if bl:
                lines.append(bl)
    lines.append("")

    lines.append("### Listed company announcements (NSE)")
    lines.append("")
    la = _take_nse_subset(news, "listed_announcements", max_per)
    if la.empty:
        lines.append(
            "- No announcement detail links matched the filter. "
            "Use `nse_sources` URLs in the browser, or add links to `market_commentary.csv`."
        )
    else:
        for _, r in la.iterrows():
            bl = _md_bullet_link(str(r["title"]), str(r["url"]))
            if bl:
                lines.append(bl)
    lines.append("")
    return lines


def lines_market_pulse(
    nse_news: pd.DataFrame,
    rss: pd.DataFrame,
    commentary: pd.DataFrame,
    ndindi: pd.DataFrame,
    memo_cfg: dict[str, Any],
) -> list[str]:
    max_nse = int(memo_cfg.get("nse_memo_max_links_per_section", 12))
    lines: list[str] = [
        "## Market pulse — NSE filings, news, and expert homework",
        "",
        "Use this section as your **reading list** before sizing trades. Automated pulls are **headlines + links** only—",
        "open each source, especially voices you trust (Abojani, Ndindi, brokers, Kenyan Wall Street, etc.).",
        "",
        "**What to look for:** dividends / rights issues, CEO changes, big contract wins, regulatory hits, and **macro** pieces that affect banks, telco, or your largest sector.",
        "",
    ]
    lines.extend(lines_nse_sections(nse_news, max_nse))
    lines.extend(lines_rss_headlines(rss))
    lines.extend(lines_manual_commentary(commentary))
    lines.extend(lines_ndindi_tracker(ndindi))
    return lines
