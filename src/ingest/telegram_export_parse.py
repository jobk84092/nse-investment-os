"""
Parse Telegram Desktop chat export (result.json) → telegram_for_commentary.csv

No Telegram API credentials. User: Telegram Desktop → ⋮ → Export chat history → JSON.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from src.utils.paths import DATA_RAW

_URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")


def flatten_telegram_text(text: object) -> str:
    if text is None:
        return ""
    if isinstance(text, str):
        return text
    if isinstance(text, list):
        parts: list[str] = []
        for el in text:
            if isinstance(el, str):
                parts.append(el)
            elif isinstance(el, dict):
                parts.append(str(el.get("text", "")))
            else:
                parts.append(str(el))
        return "".join(parts)
    return str(text)


def _headline(text: str, max_len: int = 140) -> str:
    t = (text or "").strip().replace("\r\n", "\n").replace("\r", "\n")
    if not t:
        return ""
    first = t.split("\n", 1)[0].strip()
    first = re.sub(r"\s+", " ", first)
    if len(first) > max_len:
        return first[: max_len - 1].rstrip() + "…"
    return first


def parse_telegram_export_json(
    export_path: Path,
    out_path: Path | None = None,
    max_messages: int = 500,
    voice_prefix: str = "Telegram export",
) -> int:
    """
    Read Telegram Desktop `result.json`, write memo-style CSV. Returns row count.
    Only includes messages that contain at least one http(s) URL.
    """
    out_path = out_path or (DATA_RAW / "telegram_for_commentary.csv")
    if not export_path.is_file():
        return 0

    raw = json.loads(export_path.read_text(encoding="utf-8"))
    chat_name = str(raw.get("name") or "chat").strip()
    messages = raw.get("messages") or []
    if not isinstance(messages, list):
        return 0

    voice = f"{voice_prefix}: {chat_name}"
    rows: list[dict[str, str]] = []

    for msg in reversed(messages):  # newest first in output
        if not isinstance(msg, dict):
            continue
        mtype = msg.get("type")
        if mtype == "service":
            continue
        if mtype not in (None, "message"):
            continue
        if "text" not in msg:
            continue
        flat = flatten_telegram_text(msg.get("text"))
        if not flat.strip():
            continue
        urls = _URL_RE.findall(flat)
        if not urls:
            continue
        url = urls[0].rstrip(".,;)")
        when = str(msg.get("date") or msg.get("date_unixtime") or "").strip()
        hl = _headline(flat)
        if not hl:
            continue
        rows.append(
            {
                "voice": voice,
                "published": when,
                "headline": hl,
                "url": url,
            }
        )
        if len(rows) >= max_messages:
            break

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return 0
    pd.DataFrame(rows).to_csv(out_path, index=False)
    return len(rows)
