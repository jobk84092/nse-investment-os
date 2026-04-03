# Fortnightly email digest (~every two weeks)

Scheduled on the **1st** and **15th** of each month at **08:00** (local Mac time): pipeline run + email with memo, CSVs, and Telegram digest when present. (Strict “every 14 days” would drift vs wall-clock; 1st/15th is a stable fortnightly rhythm.)

## What gets emailed

- **Body:** Short note listing attachments.
- **Attachments (default):** `monthly_investment_memo.md`, `portfolio_snapshot.csv`, `sector_snapshot.csv`, `top_ideas.csv`, `watchlist_rankings.csv`, **`data/raw/telegram_for_commentary.csv`** (Telegram digest when present), plus `alerts/email_summary.md` when present.

Paths are usually under `output/`; entries starting with `data/` are resolved from the project root (see `email_digest.attachment_files` in `settings.json`).

## Sending method (`email_digest.transport`)

- **`auto` (default):** If `gmail_send_token.json` exists (from OAuth below), send via **Gmail API**. Otherwise use **SMTP** with `.email_env`.
- **`gmail_api`:** Always use Gmail API (needs token file).
- **`smtp`:** Always use app password in `.email_env`.

If SMTP keeps returning **535** even with a new app password, use **Gmail API** — Google still accepts that path reliably.

## Gmail API (use when SMTP / app password fails)

1. Put your **OAuth 2.0 Desktop** client JSON in `nse_investment_os/credentials.json` (same file type as the AIB downloader; gitignored).
2. In [Google Cloud Console](https://console.cloud.google.com/) pick **the same project** as that OAuth client, open **APIs & Services → Library**, search **Gmail API**, open it, and click **Enable**. If you see `403` / “Gmail API has not been used”, this step was skipped.
3. Run once (browser opens; sign in with the Google account you send from):

   ```bash
   cd nse_investment_os
   .venv/bin/python scripts/auth_gmail_send.py
   ```

   This creates **`gmail_send_token.json`** (gitignored) with send-only scope.

4. Send: `.venv/bin/python scripts/send_memo_email.py` (with `transport` **`auto`**, Gmail API is used when the token exists).

## Gmail SMTP (optional)

1. Enable **2-Step Verification** on the Google account you send from.
2. Create an **App password** (Google Account → Security → App passwords).
3. Copy `.email_env.example` to **`.email_env`** and set `NSE_INVEST_SMTP_USER` and `NSE_INVEST_SMTP_PASSWORD`.

The sender also **loads `.email_env` inside Python** (UTF-8 safe), so `launchctl` jobs do not depend on the shell having `source`’d it first — the fortnightly wrapper still sources it for SMTP passwords.

## Commands

```bash
cd nse_investment_os
source .email_env   # or rely on launchd sourcing it from the wrapper script
.venv/bin/python scripts/send_memo_email.py --dry-run
.venv/bin/python scripts/run_all.py && .venv/bin/python scripts/send_memo_email.py
```

Manual full run + send (same as the scheduled job):

```bash
./scripts/run_and_email_fortnightly.sh
```

## Schedule (launchd)

1. If you previously loaded the **bi-monthly** job, unload it:

   ```bash
   launchctl unload ~/Library/LaunchAgents/com.jobkimani.nse.bimonthly_email.plist 2>/dev/null || true
   ```

2. `chmod +x scripts/run_and_email_fortnightly.sh`
3. Copy `scripts/com.jobkimani.nse.fortnightly_email.plist` to `~/Library/LaunchAgents/`
4. Load:

   ```bash
   launchctl load ~/Library/LaunchAgents/com.jobkimani.nse.fortnightly_email.plist
   ```

Logs: `~/Library/Logs/nse_investment_os_fortnightly.log`

## Safety

- Set `email_digest.enabled` to `false` in `settings.json` to skip sends unless you pass `--force` to `send_memo_email.py`.
- Never commit `.email_env` or real passwords.
