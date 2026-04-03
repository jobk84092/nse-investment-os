# Memo enrichment: corporate actions, RSS, voices

After **Market pulse**, the memo adds **This month’s playbook**: ranked **new money** vs **add-ons**, budget line, sector headroom callouts, and a short homework checklist tied to your curated links. Tune `memo_playbook.max_new_money_slots` in `config/settings.json`.

The monthly memo includes a **Market pulse** section built from:

1. **NSE** — HTML scrape of your `nse_sources` URLs, then a **strict URL filter** so only paths that look like announcement or corporate-action **details** appear (not the global site menu). Many NSE tables load in the browser, so this list may be empty; use the official site when needed.

2. **RSS** — Feeds listed under `memo_enrichment.rss_feeds` in `config/settings.json`. If a feed’s XML is invalid, you can set **`homepage_fallback`** to the site root; the job will collect likely article links from that page instead.

3. **Curated voices** — `data/manual/market_commentary.csv` with columns `voice`, `published` (optional), `headline`, `url`. Use this for **Ali Abojani**, **Ndindi Nyoro**, newsletters, YouTube episodes, or X threads you want in the memo (respect copyright and terms of use).

4. **Telegram (optional)** — **Default:** **`telegram.fetch_before_run`** runs **Telethon** on each `run_all.py` (built-in API id/hash; one-time SMS login). Merges new links into `market_commentary.csv`. **Backup:** Desktop **JSON export** if you set **`process_desktop_export_before_run`**. **`docs/TELEGRAM_SOURCES.md`**.

5. **Ndindi-style tracker** — `data/manual/ndindi_tracker.csv`: your per-ticker notes and conviction hints (already merged into scoring).

Raw pulls are saved under `data/raw/` as `nse_news_links_all.csv` (full scrape), `nse_news_links.csv` (announcement-style paths only), `rss_headlines.csv`, and optionally `telegram_for_commentary.csv`.
