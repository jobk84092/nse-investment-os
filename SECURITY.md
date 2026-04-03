# Security

## Never commit (private / high sensitivity)

- **Your email in config:** Before a **public** push, set `alerts.recipient_email`, `email_digest.to`, and `email_digest.from_address` in `config/settings.json` to placeholders or remove personal addresses (or keep a private fork with real values).
- **Portfolio & money:** `data/manual/holdings.csv`, `data/manual/monthly_budget.csv`
- **Your notes & links:** `data/manual/market_commentary.csv`, `data/manual/ndindi_tracker.csv`, `data/manual/simplywallst_watchlist.csv` (if they contain personal strategy)
- **Secrets:** `.email_env`, `.telegram_env`, `.env`, `credentials.json`, `gmail_send_token.json`, `telegram_session.session` (+ `-journal`)
- **Broker PDFs / exports:** anything under `downloads/` or paths you configure for AIB PDF sync

This repository’s `.gitignore` excludes most of the above; **verify with `git status`** before every push.

## Email & Telegram

- Use **Gmail API** token or **app passwords** only in local env files (gitignored).
- Telegram access uses a **session file** tied to your account—keep it local.

## Reporting

If you find a security issue in this template project, open a private discussion with the maintainer (do not file a public issue with exploit details first).

## Disclaimer

This software is for **personal research and organization**. It is not financial advice. You are responsible for your data and compliance with NSE, Telegram, and Gmail terms of use.
