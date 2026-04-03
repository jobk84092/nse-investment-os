#!/usr/bin/env python3
"""
Convert Telegram Desktop JSON export → data/raw/telegram_for_commentary.csv

  Telegram Desktop → open the Abojani chat → ⋮ → Export chat history → JSON only
  → unzip / find result.json → pass path below.

No my.telegram.org / api_id required.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.ingest.telegram_export_parse import parse_telegram_export_json  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Telegram Desktop export → commentary CSV")
    ap.add_argument(
        "result_json",
        type=Path,
        help="Path to result.json from Telegram Desktop export",
    )
    ap.add_argument(
        "--max-messages",
        type=int,
        default=500,
        help="Max rows to write (newest messages with URLs first)",
    )
    args = ap.parse_args()
    n = parse_telegram_export_json(args.result_json, max_messages=args.max_messages)
    if n == 0:
        print("No rows written (missing file, wrong format, or no messages with http(s) links).")
        return 1
    print(f"Wrote {n} rows to data/raw/telegram_for_commentary.csv")
    print("Run: .venv/bin/python scripts/run_all.py  (with telegram.process_desktop_export_before_run in settings)")
    print("Or merge manually into data/manual/market_commentary.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
