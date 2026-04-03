# Setup

## 1. Create a virtual environment

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Edit the manual CSV files

From a fresh clone, copy **`data/manual/examples/*.example`** into `data/manual/` (drop the `.example` suffix)—see the main **README** quick start.

Start with:

- `data/manual/holdings.csv`
- `data/manual/monthly_budget.csv`
- `data/manual/approved_universe.csv`

Optional:

- `data/manual/simplywallst_watchlist.csv`
- `data/manual/ndindi_tracker.csv`
- `data/manual/market_commentary.csv`

## 3. Run the whole workflow

```bash
python scripts/run_all.py
```

Before first run, set your recipient email in `config/settings.json`:

```json
"alerts": {
  "recipient_email": "your@email.com"
}
```

## 4. Review outputs

Look in:

- `output/portfolio_snapshot.csv`
- `output/watchlist_rankings.csv`
- `output/top_ideas.csv`
- `output/monthly_investment_memo.md`
- `output/alerts/`

## 5. Automate later

After you confirm the outputs look right, wire the script into:

- cron
- launchd
- Windows Task Scheduler
- GitHub Actions

## 6. Sync holdings from AIB PDF (optional)

See [PDF_SYNC.md](PDF_SYNC.md): `scripts/sync_holdings_from_aib_pdf.py` picks the newest portfolio valuation PDF and refreshes `data/manual/holdings.csv`, then run `scripts/run_all.py` as usual.

## 7. Market pulse in the memo (NSE, RSS, voices)

See [MEMO_ENRICHMENT.md](MEMO_ENRICHMENT.md). Edit `memo_enrichment` in `config/settings.json` and `data/manual/market_commentary.csv` for Abojani, Ndindi links, and extra RSS sources.
