#!/usr/bin/env python3
"""
Find newest AIB portfolio valuation PDF under configured OneDrive folder,
parse holdings, update data/manual/holdings.csv (with timestamped backup).
"""
import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.ingest.aib_valuation_pdf import (  # noqa: E402
    find_newest_pdf,
    sync_from_pdf,
)
from src.utils.paths import CONFIG_FILE, DATA_MANUAL  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync holdings.csv from AIB valuation PDF")
    ap.add_argument(
        "--pdf",
        type=Path,
        help="Use this PDF instead of searching",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and print summary only; do not write holdings.csv",
    )
    ap.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not write a .bak copy before overwriting holdings.csv",
    )
    args = ap.parse_args()

    cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    sync_cfg = cfg.get("aib_pdf_sync") or {}
    # Default: OneDrive "stocks" folder that contains this repo (…/stocks/20260402 stocks automation/…)
    _default_stocks_dir = _ROOT.parent.parent
    _dir_cfg = (sync_cfg.get("search_dir") or "").strip()
    search_dir = Path(_dir_cfg) if _dir_cfg else _default_stocks_dir
    patterns = sync_cfg.get("filename_globs") or [
        "*PortfolioValuation*.pdf",
        "*portfolio-valuation*.pdf",
        "*PORTFOLIO*.pdf",
    ]
    out_name = sync_cfg.get("holdings_csv") or "data/manual/holdings.csv"
    holdings_csv = _ROOT / out_name if not Path(out_name).is_absolute() else Path(out_name)

    pdf = args.pdf
    if pdf is None:
        pdf = find_newest_pdf(search_dir, patterns)
    if pdf is None or not pdf.is_file():
        print(
            f"No PDF found under {search_dir} with patterns {patterns}. "
            "Set aib_pdf_sync.search_dir in config/settings.json or pass --pdf.",
            file=sys.stderr,
        )
        return 2

    try:
        n, summary = sync_from_pdf(
            pdf,
            holdings_csv,
            dry_run=args.dry_run,
            backup=not args.no_backup,
        )
    except Exception as e:
        print(e, file=sys.stderr)
        return 1

    print(f"OK: {summary} (rows={n})")
    if args.dry_run:
        print(f"Would write: {holdings_csv}")
    else:
        print(f"Wrote: {holdings_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
