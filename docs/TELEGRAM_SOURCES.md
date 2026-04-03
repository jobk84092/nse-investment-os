# Telegram → memo (automated)

## A) Live fetch every `run_all.py` (default)

**No my.telegram.org required.** The Telethon script uses the same **test `api_id` / `api_hash`** Telegram publishes in **Telegram Desktop** source (`telegramdesktop/tdesktop`, `Telegram/SourceFiles/config.h`). Many personal clients use these; Telegram may rate-limit shared ids—if login ever fails, add your own credentials to `.telegram_env` (optional).

1. **One-time SMS login** (creates `telegram_session.session` in the project root, gitignored):

   ```bash
   cd nse_investment_os
   .venv/bin/python scripts/telegram_to_commentary.py --from-settings
   ```

   Enter phone + code when prompted.

   If a name is not found, list sidebar titles:  
   `.venv/bin/python scripts/telegram_to_commentary.py --list-chats`

2. **Automation:** `config/settings.json` has **`telegram.fetch_before_run`: `true`**. Each **`python scripts/run_all.py`** will:

   - Pull the last N messages **per chat** from every title substring in **`telegram.chat_filters`** (list),
   - Prefer a **`t.me`** link per message; if missing, use the **first `http(s)` URL in the text** (so article links still merge),
   - Write `data/raw/telegram_for_commentary.csv` and **merge new URLs** into `data/manual/market_commentary.csv`.

3. **Optional overrides** in **`.telegram_env`** (see **`.telegram_env.example`**): `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_CHAT_FILTER`, `TELEGRAM_MESSAGE_LIMIT`.

4. **Scheduled runs** (`run_and_email_fortnightly.sh`): still sources `.telegram_env` if present; **not required** for defaults.

**Turn off** live fetch: set **`fetch_before_run`** to **`false`**.

---

## B) Telegram Desktop JSON export (backup, no login session)

If you prefer not to use Telethon, set **`process_desktop_export_before_run`: `true`** and place **`result.json`** under `data/raw/telegram_export/`. See older instructions in git history or ask in Cursor; **B is off by default** when **A** is on.

---

## Rules

- Respect **group rules** (Abojani / paid communities).
- **Copyright:** personal memo only; don’t republish bulk content.
- **Telegram ToS:** reasonable personal use; no spam.
