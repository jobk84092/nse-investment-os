"""Append new Telegram-derived rows into data/manual/market_commentary.csv (dedupe by URL)."""
from __future__ import annotations

import pandas as pd

from src.utils.paths import DATA_MANUAL, DATA_RAW
from src.utils.io import read_csv, write_csv

_COLS = ["voice", "published", "headline", "url"]


def _norm_url(u: str) -> str:
    return (u or "").strip().lower().rstrip("/")


def merge_telegram_into_manual_commentary() -> int:
    raw_path = DATA_RAW / "telegram_for_commentary.csv"
    manual_path = DATA_MANUAL / "market_commentary.csv"
    if not raw_path.is_file():
        return 0

    tele = pd.read_csv(raw_path, dtype=str)
    if tele.empty:
        return 0
    for c in _COLS:
        if c not in tele.columns:
            return 0

    tele = tele.fillna("")
    tele = tele[tele["url"].astype(str).str.strip() != ""]
    if tele.empty:
        return 0

    manual = read_csv(manual_path)
    if manual.empty:
        base = pd.DataFrame(columns=_COLS)
    else:
        for c in _COLS:
            if c not in manual.columns:
                manual[c] = ""
        base = manual[_COLS].copy()

    seen = {_norm_url(str(u)) for u in base["url"].tolist() if str(u).strip()}
    new_rows: list[dict] = []
    for _, r in tele.iterrows():
        u = _norm_url(str(r["url"]))
        if not u or u in seen:
            continue
        seen.add(u)
        new_rows.append({c: str(r.get(c, "") or "") for c in _COLS})

    if not new_rows:
        return 0

    out = pd.concat([base, pd.DataFrame(new_rows)], ignore_index=True)
    write_csv(out, manual_path)
    return len(new_rows)
