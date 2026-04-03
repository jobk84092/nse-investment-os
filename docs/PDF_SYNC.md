# Sync holdings from AIB portfolio valuation PDF

The script finds the newest matching PDF under your OneDrive `stocks` folder (or a path you set), parses the **Portfolio Details** table, and overwrites `data/manual/holdings.csv`. A timestamped `.bak` file is written first.

## Requirements

- **macOS:** `pdftotext` from Poppler (`brew install poppler`) is used when available.
- **Fallback:** `pypdf` (in `requirements.txt`) if `pdftotext` is missing.

## Configuration

In `config/settings.json`, optional block:

```json
"aib_pdf_sync": {
  "search_dir": "",
  "filename_globs": [
    "*PortfolioValuation*.pdf",
    "*portfolio-valuation*.pdf",
    "*PORTFOLIO*.pdf"
  ],
  "holdings_csv": "data/manual/holdings.csv"
}
```

- Leave `search_dir` empty to use the parent `stocks` folder (the directory that contains `20260402 stocks automation`).
- Set `search_dir` to an absolute path if your PDFs live elsewhere.

## Commands

Dry run (no write):

```bash
.venv/bin/python scripts/sync_holdings_from_aib_pdf.py --dry-run
```

Use a specific file:

```bash
.venv/bin/python scripts/sync_holdings_from_aib_pdf.py --pdf "/path/to/PortfolioValuation....pdf"
```

Then regenerate outputs:

```bash
.venv/bin/python scripts/run_all.py
```

## Preserving your notes

Existing `thesis_bucket`, `notes`, and `sector` are reused **per ticker** when present. New rows get default sector from a built-in map and default thesis (`core`, except a few tickers like `UCHM`).

## Fortnightly automation (macOS)

Copy `scripts/com.jobkimani.nse.pdf_sync.plist` to `~/Library/LaunchAgents/`, then:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.jobkimani.nse.pdf_sync.plist
```

Edit the plist if your repo path differs. The job runs the sync script only; run `run_all.py` separately or add a wrapper shell script if you want memo + alerts every time.
