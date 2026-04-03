#!/usr/bin/env python3
"""
Fetch recent messages from Telegram chats you are in; write memo-ready CSV rows.

Uses built-in default API id/hash from Telegram Desktop’s published test constants
(telegramdesktop/tdesktop `config.h`) so you can automate without my.telegram.org.
Override with TELEGRAM_API_ID / TELEGRAM_API_HASH if you have your own.

First run: SMS login once → telegram_session.session (gitignored).

Multi-chat: use --from-settings (reads config/settings.json → telegram.chat_filters).

See docs/TELEGRAM_SOURCES.md for ethics, group rules, and workflow.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
from datetime import timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_CONFIG = _ROOT / "config" / "settings.json"
_DEFAULT_OUT = _ROOT / "data" / "raw" / "telegram_for_commentary.csv"
_SESSION = _ROOT / "telegram_session"

# Telegram Desktop source (non-deploy / test defaults in config.h). Shared by many clients.
_DEFAULT_API_ID = 17349
_DEFAULT_API_HASH = "344583e45741c457fe1862106095a5eb"

_URL_IN_TEXT = re.compile(r"https?://[^\s<>\"')\]]+")


def _message_link(chat_id: int, msg_id: int, username: str | None) -> str:
    if username:
        u = username.lstrip("@")
        return f"https://t.me/{u}/{msg_id}"
    s = str(chat_id)
    if s.startswith("-100"):
        inner = s[4:]
        return f"https://t.me/c/{inner}/{msg_id}"
    return ""


def _headline(text: str, max_len: int = 140) -> str:
    t = (text or "").strip().replace("\r\n", "\n").replace("\r", "\n")
    if not t:
        return ""
    first = t.split("\n", 1)[0].strip()
    first = re.sub(r"\s+", " ", first)
    if len(first) > max_len:
        return first[: max_len - 1].rstrip() + "…"
    return first


def _chat_filters_from_settings() -> tuple[list[str], int]:
    cfg = json.loads(_CONFIG.read_text(encoding="utf-8"))
    tg = cfg.get("telegram") or {}
    raw = tg.get("chat_filters")
    if isinstance(raw, list) and raw:
        filters = [str(x).strip() for x in raw if str(x).strip()]
    else:
        one = str(tg.get("chat_filter") or "Abojani").strip()
        filters = [one] if one else ["Abojani"]
    lim = int(tg.get("message_limit") or 25)
    return filters, max(1, lim)


async def _list_chats() -> int:
    raw_id = os.environ.get("TELEGRAM_API_ID", "").strip()
    raw_hash = os.environ.get("TELEGRAM_API_HASH", "").strip()
    api_id = int(raw_id) if raw_id else _DEFAULT_API_ID
    api_hash = raw_hash if raw_hash else _DEFAULT_API_HASH
    from telethon import TelegramClient

    client = TelegramClient(str(_SESSION), api_id, api_hash)
    await client.start()
    try:
        print("Chats (sidebar titles) — use a unique substring in telegram.chat_filters:\n")
        async for d in client.iter_dialogs(limit=200):
            name = (d.name or "").strip() or "(no name)"
            print(f"  {name}")
        return 0
    finally:
        await client.disconnect()


async def _run_multi(
    chat_filters: list[str],
    limit_per_chat: int,
    out_path: Path,
    skip_forwards: bool,
) -> int:
    raw_id = os.environ.get("TELEGRAM_API_ID", "").strip()
    raw_hash = os.environ.get("TELEGRAM_API_HASH", "").strip()
    api_id = int(raw_id) if raw_id else _DEFAULT_API_ID
    api_hash = raw_hash if raw_hash else _DEFAULT_API_HASH

    from telethon import TelegramClient
    from telethon.tl.types import User

    out_path.parent.mkdir(parents=True, exist_ok=True)
    client = TelegramClient(str(_SESSION), api_id, api_hash)

    await client.start()
    try:
        dialogs = []
        async for d in client.iter_dialogs():
            dialogs.append(d)

        seen_ids: set[int] = set()
        all_rows: list[dict[str, str]] = []
        missing: list[str] = []

        for chat_filter in chat_filters:
            cf_lower = chat_filter.strip().lower()
            entity = None
            chosen_name = ""
            for dialog in dialogs:
                name = (dialog.name or "").strip()
                if cf_lower in name.lower():
                    entity = dialog.entity
                    chosen_name = name
                    break

            if entity is None:
                missing.append(chat_filter)
                print(f"[skip] No chat title containing {chat_filter!r}")
                continue

            if isinstance(entity, User):
                print(f"[skip] {chat_filter!r} matched a user DM, not a channel/group.")
                continue

            eid = int(getattr(entity, "id", 0))
            if eid in seen_ids:
                print(f"[skip] Already fetched {chosen_name!r} (duplicate filter).")
                continue
            seen_ids.add(eid)

            cid = getattr(entity, "id", None)
            uname = getattr(entity, "username", None)
            n_chat = 0
            async for msg in client.iter_messages(entity, limit=limit_per_chat):
                if not msg or not getattr(msg, "id", None):
                    continue
                if skip_forwards and getattr(msg, "fwd_from", None):
                    continue
                raw = msg.message or ""
                if not raw.strip():
                    continue
                url = _message_link(int(cid), int(msg.id), uname)
                if not url:
                    ext = _URL_IN_TEXT.findall(raw)
                    if ext:
                        url = ext[0].rstrip(".,;)")
                when = msg.date
                if when and when.tzinfo is None:
                    when = when.replace(tzinfo=timezone.utc)
                pub = when.astimezone(timezone.utc).isoformat() if when else ""
                hl = _headline(raw)
                if not hl or not url:
                    continue
                all_rows.append(
                    {
                        "voice": f"Telegram: {chosen_name}",
                        "published": pub,
                        "headline": hl,
                        "url": url,
                    }
                )
                n_chat += 1
            print(f"[ok] {chosen_name!r}: {n_chat} rows (filter was {chat_filter!r})")

        if missing:
            print("\nMissing filters — run with --list-chats to see exact sidebar titles.")

        if not seen_ids:
            return 3

        with out_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["voice", "published", "headline", "url"])
            w.writeheader()
            w.writerows(all_rows)

        print(f"\nWrote {len(all_rows)} total rows to {out_path}")
        print("If merge_into_market_commentary is on, run_all.py will append new URLs automatically.")
        return 0
    finally:
        await client.disconnect()


def main() -> int:
    ap = argparse.ArgumentParser(description="Telegram → memo commentary CSV (personal use)")
    ap.add_argument(
        "--from-settings",
        action="store_true",
        help="Use telegram.chat_filters + message_limit from config/settings.json",
    )
    ap.add_argument(
        "--list-chats",
        action="store_true",
        help="Print recent chat titles (sidebar names) and exit",
    )
    ap.add_argument(
        "--chat-filter",
        default=os.environ.get("TELEGRAM_CHAT_FILTER", ""),
        help="Single substring (only if not using --from-settings)",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max messages per chat (0 = use settings or env TELEGRAM_MESSAGE_LIMIT or 25)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=_DEFAULT_OUT,
        help="Output CSV path",
    )
    ap.add_argument(
        "--include-forwards",
        action="store_true",
        help="Include forwarded messages (default: skip)",
    )
    args = ap.parse_args()

    if args.list_chats:
        return asyncio.run(_list_chats())

    if args.from_settings:
        filters, lim = _chat_filters_from_settings()
    else:
        cf = (args.chat_filter or "").strip() or os.environ.get("TELEGRAM_CHAT_FILTER", "Abojani")
        filters = [cf.strip()]
        env_lim = os.environ.get("TELEGRAM_MESSAGE_LIMIT", "").strip()
        lim = args.limit if args.limit > 0 else (int(env_lim) if env_lim else 25)
    lim = max(1, lim)

    return asyncio.run(
        _run_multi(
            chat_filters=filters,
            limit_per_chat=lim,
            out_path=args.out,
            skip_forwards=not args.include_forwards,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
