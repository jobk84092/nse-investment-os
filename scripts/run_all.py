import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.ingest.manual_inputs import (
    load_holdings,
    load_budget,
    load_universe,
    load_simply,
    load_ndindi,
    load_market_commentary,
)
from src.news.nse_news import nse_news_filtered_and_raw
from src.news.rss_feeds import fetch_all_rss_feeds
from src.core.scoring import score_universe
from src.portfolio.analytics import portfolio_snapshot, sector_snapshot, concentration_alerts
from src.portfolio.ideas import top_ideas
from src.reports.memo import build_monthly_memo
from src.alerts.generators import generate_calendar_ics, generate_desktop_alert, generate_email_summary
from src.utils.paths import OUTPUT_DIR, DATA_RAW, settings as load_settings
from src.utils.io import write_csv, write_text, ensure_dir
from src.utils.dotenv_local import apply_env_file
from src.ingest.telegram_merge import merge_telegram_into_manual_commentary
from src.ingest.telegram_export_parse import parse_telegram_export_json


def _maybe_fetch_telegram() -> None:
    apply_env_file(_ROOT / ".telegram_env")
    tg = load_settings().get("telegram") or {}
    if not tg.get("fetch_before_run", False):
        return
    print("[telegram] Fetching recent group messages (Telethon; default API id if no .telegram_env)…")
    cmd = [
        sys.executable,
        str(_ROOT / "scripts" / "telegram_to_commentary.py"),
        "--from-settings",
    ]
    r = subprocess.run(cmd, cwd=str(_ROOT), env=os.environ.copy())
    if r.returncode != 0:
        print(
            f"[telegram] Fetch exited {r.returncode}. "
            "If this is the first time, run interactively in Terminal: "
            ".venv/bin/python scripts/telegram_to_commentary.py"
        )
        return
    if tg.get("merge_into_market_commentary", True):
        n = merge_telegram_into_manual_commentary()
        if n:
            print(
                f"[telegram] Merged {n} new link(s) into data/manual/market_commentary.csv"
            )


def _maybe_import_telegram_export() -> None:
    """Telegram Desktop JSON export — no api_id (see docs/TELEGRAM_SOURCES.md)."""
    tg = load_settings().get("telegram") or {}
    if not tg.get("process_desktop_export_before_run", False):
        return
    rel = (tg.get("desktop_export_json") or "data/raw/telegram_export/result.json").strip()
    p = Path(rel) if Path(rel).is_absolute() else (_ROOT / rel)
    if not p.is_file():
        return
    print(f"[telegram] Parsing Telegram Desktop export: {p}")
    n = parse_telegram_export_json(
        p,
        max_messages=int(tg.get("desktop_export_max_messages") or 500),
    )
    if n and tg.get("merge_into_market_commentary", True):
        m = merge_telegram_into_manual_commentary()
        if m:
            print(
                f"[telegram] Merged {m} new link(s) into data/manual/market_commentary.csv"
            )


def main():
    print("[1/6] Initializing directories...")
    ensure_dir(OUTPUT_DIR)
    ensure_dir(DATA_RAW)

    print("[2/6] Loading manual input files...")
    holdings = load_holdings()
    budget = load_budget()
    universe = load_universe()
    simply = load_simply()
    ndindi = load_ndindi()
    _maybe_fetch_telegram()
    _maybe_import_telegram_export()
    commentary = load_market_commentary()

    print("[3/6] Fetching NSE pages, RSS feeds, and assembling market context...")
    news, nse_raw = nse_news_filtered_and_raw()
    memo_cfg = load_settings().get("memo_enrichment") or {}
    rss = fetch_all_rss_feeds(
        memo_cfg.get("rss_feeds") or [],
        int(memo_cfg.get("max_items_per_rss_feed") or 6),
    )
    if not simply.empty and "ticker" in simply.columns:
        universe = universe.merge(simply, on="ticker", how="left")
    if not ndindi.empty and "ticker" in ndindi.columns:
        universe = universe.merge(ndindi[["ticker", "tracking_note", "conviction_hint"]], on="ticker", how="left")

    print("[4/6] Scoring universe and generating portfolio analytics...")
    scored = score_universe(universe, news)
    p_snap = portfolio_snapshot(holdings)
    s_snap = sector_snapshot(holdings)
    alerts = concentration_alerts(holdings)
    ideas = top_ideas(scored, holdings, budget, top_n=5)
    if not budget.empty:
        last_b = budget.iloc[-1]
        budget_kes = float(last_b["budget_kes"])
        budget_month = str(last_b.get("month", "") or "")
    else:
        budget_kes = float(load_settings()["investor_profile"]["average_monthly_stock_budget_kes"])
        budget_month = ""
    memo = build_monthly_memo(
        p_snap,
        s_snap,
        scored,
        ideas,
        alerts,
        nse_news=news,
        rss_headlines=rss,
        market_commentary=commentary,
        ndindi=ndindi,
        budget_kes=budget_kes,
        budget_month=budget_month,
    )

    print("[5/6] Writing reports and output files...")
    write_csv(nse_raw, DATA_RAW / "nse_news_links_all.csv")
    write_csv(news, DATA_RAW / "nse_news_links.csv")
    write_csv(rss, DATA_RAW / "rss_headlines.csv")
    write_csv(p_snap, OUTPUT_DIR / "portfolio_snapshot.csv")
    write_csv(s_snap, OUTPUT_DIR / "sector_snapshot.csv")
    write_csv(scored, OUTPUT_DIR / "watchlist_rankings.csv")
    write_csv(ideas, OUTPUT_DIR / "top_ideas.csv")
    write_text(memo, OUTPUT_DIR / "monthly_investment_memo.md")

    print("[6/6] Generating alerts...")
    summary = "NSE Investment OS completed. Read monthly_investment_memo.md and top_ideas.csv."
    generate_desktop_alert(summary)
    generate_email_summary(memo)
    generate_calendar_ics()

    print("Done. Outputs written to output/")

if __name__ == "__main__":
    main()
