# NSE Investment OS

A VS Code / Cursor-ready Python project for a **balanced but aggressive-leaning** Nairobi Securities Exchange (NSE) investing workflow: scored watchlist, portfolio checks, monthly memo, optional Telegram + email digests.

**Not financial advice.** For organizing your own research and discipline.

This system is designed around your style:

- Buffett / Graham principles
- monthly stock budget averaging about **KES 20,000**, but variable
- quality + value first
- current affairs and corporate announcements tracking
- disciplined portfolio sizing
- investment memo generation
- alerts through:
  - desktop alerts
  - email summaries
  - Gmail/Calendar-friendly `.ics` reminder generation

## What this project does

1. Tracks your current portfolio and monthly buys
2. Scores watchlist names using:
   - quality
   - value
   - dividend support
   - balance-sheet strength
   - governance/news penalty
3. Pulls NSE news / announcements pages
4. Produces:
   - ranked watchlist
   - top ideas
   - monthly investment memo
   - portfolio concentration checks
   - action reminders
5. Creates alert files and summaries you can extend

## Important note

This starter is intentionally **safe and editable**:

- it does not auto-trade
- it does not scrape private paid dashboards
- it uses manual CSV imports for Simply Wall St and Ndindi tracker data
- it is designed to be iterated inside Cursor / VS Code

## Market pulse in the memo

Each run adds **corporate actions / NSE context**, **RSS headlines** (with optional homepage fallback), **your curated commentary CSV** (Abojani, Ndindi, etc.), and **Ndindi-style tracker** notes. Configure `memo_enrichment` in `config/settings.json` and see `docs/MEMO_ENRICHMENT.md`.

## Strategy and comfort

Outputs are **checklists**, not trade instructions. Read `docs/STRATEGY_AND_COMFORT.md` and the opening sections of `output/monthly_investment_memo.md` after each run. Optional: set `guidance.personal_comfort_note` in `config/settings.json` to pin a one-line rule you want at the top of every memo.

## Quick start

```bash
cd nse_investment_os
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**First clone:** copy example CSVs into `data/manual/` (your real `holdings.csv` etc. are gitignored so you don’t leak a portfolio):

```bash
cp data/manual/examples/holdings.csv.example data/manual/holdings.csv
cp data/manual/examples/monthly_budget.csv.example data/manual/monthly_budget.csv
cp data/manual/examples/market_commentary.csv.example data/manual/market_commentary.csv
cp data/manual/examples/ndindi_tracker.csv.example data/manual/ndindi_tracker.csv
cp data/manual/examples/simplywallst_watchlist.csv.example data/manual/simplywallst_watchlist.csv
```

If you already maintain real files locally, keep using them—Git will not track those paths once ignored.

Edit `data/manual/approved_universe.csv` and the files above for your tickers. Then:

```bash
python scripts/run_all.py
```

Outputs go to `output/` (also gitignored by default).

### Documentation map

| Topic | Doc |
|--------|-----|
| Email (Gmail API / SMTP) + fortnightly launchd | `docs/EMAIL_DIGEST.md` |
| Memo: NSE, RSS, Telegram, commentary | `docs/MEMO_ENRICHMENT.md` |
| Telegram (Telethon + Desktop export) | `docs/TELEGRAM_SOURCES.md` |
| Strategy framing | `docs/STRATEGY_AND_COMFORT.md` |
| Secrets & what not to push | `SECURITY.md` |

## Alert recipient setup

Set your recipient in `config/settings.json`:

```json
"alerts": {
  "generate_email_summary": true,
  "generate_desktop_alert": true,
  "generate_calendar_ics": true,
  "recipient_email": "your@email.com"
}
```

This email is added to:

- `output/alerts/email_summary.md` as `To: ...`
- `output/alerts/monthly_stock_review.ics` description metadata

## Fortnightly email (memo + CSV + Telegram digest)

`scripts/send_memo_email.py` emails the address in `config/settings.json` (`email_digest.to` / `alerts.recipient_email`) with the memo, key `output/` files, and `data/raw/telegram_for_commentary.csv` when present. Use Gmail API token or `.email_env` for SMTP. On macOS, schedule **`scripts/run_and_email_fortnightly.sh`** with **`scripts/com.jobkimani.nse.fortnightly_email.plist`** (1st & 15th each month at 08:00 local). Full steps: `docs/EMAIL_DIGEST.md`.

## Main design

- **Core bucket**: strong quality compounders
- **Value bucket**: discounted but still understandable businesses
- **Speculative bucket**: tightly capped
- **Risk controls**:
  - max 15% per stock
  - max 35% per sector
  - max 15% special situations combined

## Manual data files you should update

- `data/manual/holdings.csv`
- `data/manual/monthly_budget.csv`
- `data/manual/simplywallst_watchlist.csv`
- `data/manual/ndindi_tracker.csv`
- `data/manual/approved_universe.csv`

## Alerts included

- markdown email summary output
- desktop alert text output
- calendar `.ics` reminder for monthly stock review

You can later wire these into:

- local notifications
- Gmail draft creation
- Google Calendar import
- cron / launchd / Task Scheduler
- GitHub Actions

## Publish to GitHub (public repo checklist)

1. Read **`SECURITY.md`** — confirm no secrets or real portfolio files are staged (`git status`, `git diff --cached`).
2. Replace personal emails in **`config/settings.json`** with placeholders or your public contact if you want (or keep private via a local-only override pattern).
3. **`plist` paths** in `scripts/com.jobkimani.nse.fortnightly_email.plist` point at this machine’s absolute path — contributors should copy the plist and edit `ProgramArguments` / `WorkingDirectory` for their Mac.
4. Initialize and push:

   ```bash
   cd nse_investment_os
   git init
   git add -A
   git status   # verify: no credentials.json, no .email_env, no holdings with real sizes, etc.
   git commit -m "Initial commit: NSE Investment OS"
   gh repo create nse-investment-os --public --source=. --remote=origin --push
   ```

   Or create an empty repo on GitHub and: `git remote add origin …` then `git push -u origin main`.

5. Optional: add a **license** (e.g. MIT) and a one-line **disclaimer** in the repo About: “Educational / personal tooling—not investment advice.”
