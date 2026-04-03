from __future__ import annotations
import pandas as pd
from datetime import date
from src.utils.paths import settings
from src.reports.strategy_guidance import (
    lines_before_you_trade,
    lines_discipline_short,
    lines_how_to_read_this_memo,
    lines_if_uneasy,
    lines_limits_vs_portfolio,
    lines_about_top_ideas,
    lines_strategy_snapshot,
)
from src.reports.memo_market_context import lines_market_pulse
from src.reports.memo_playbook import lines_monthly_playbook


def build_monthly_memo(
    holdings: pd.DataFrame,
    sectors: pd.DataFrame,
    scored: pd.DataFrame,
    ideas: pd.DataFrame,
    alerts: list[str],
    nse_news: pd.DataFrame | None = None,
    rss_headlines: pd.DataFrame | None = None,
    market_commentary: pd.DataFrame | None = None,
    ndindi: pd.DataFrame | None = None,
    budget_kes: float | None = None,
    budget_month: str = "",
) -> str:
    cfg = settings()
    today = date.today().isoformat()
    lines = []
    lines.append(f"# Monthly Investment Memo - {today}")
    lines.append("")
    lines.extend(lines_how_to_read_this_memo(cfg))
    lines.extend(lines_strategy_snapshot(cfg))
    lines.append("## Profile")
    lines.append("")
    lines.append(f"- Strategy label: {cfg['investor_profile']['strategy']}")
    lines.append(f"- Average monthly stock budget (settings default): KES {cfg['investor_profile']['average_monthly_stock_budget_kes']:,}")
    lines.append(f"- Use `data/manual/monthly_budget.csv` for the month you are actually funding.")
    lines.append("")
    lines.extend(lines_limits_vs_portfolio(holdings, sectors, cfg["position_limits"]))
    lines.append("## Portfolio snapshot")
    lines.append("")
    total_value = holdings['market_value'].sum() if not holdings.empty else 0
    total_pl = holdings['unrealized_pl'].sum() if not holdings.empty else 0
    lines.append(f"- Portfolio market value: KES {total_value:,.2f}")
    lines.append(f"- Unrealized P/L: KES {total_pl:,.2f}")

    if not holdings.empty:
        top = holdings.sort_values('weight_pct', ascending=False).head(5)[['ticker', 'weight_pct', 'market_value']]
        lines.append("")
        lines.append("### Largest positions")
        lines.append("")
        for _, r in top.iterrows():
            lines.append(f"- {r['ticker']}: {r['weight_pct']:.2f}% | KES {r['market_value']:,.2f}")

    if not sectors.empty:
        lines.append("")
        lines.append("### Sector exposure")
        lines.append("")
        for _, r in sectors.iterrows():
            lines.append(f"- {r['sector']}: {r['sector_weight_pct']:.2f}%")

    memo_cfg = cfg.get("memo_enrichment") or {}
    nse_df = nse_news if nse_news is not None else pd.DataFrame()
    rss_df = rss_headlines if rss_headlines is not None else pd.DataFrame()
    comm_df = market_commentary if market_commentary is not None else pd.DataFrame()
    nd_df = ndindi if ndindi is not None else pd.DataFrame()
    lines.append("")
    lines.extend(lines_market_pulse(nse_df, rss_df, comm_df, nd_df, memo_cfg))

    bk = float(budget_kes) if budget_kes is not None else float(
        cfg["investor_profile"]["average_monthly_stock_budget_kes"]
    )
    lines.append("")
    lines.extend(
        lines_monthly_playbook(cfg, holdings, sectors, ideas, bk, budget_month or "")
    )

    lines.append("")
    lines.extend(lines_about_top_ideas(ideas))
    lines.append("## Top current ideas")
    lines.append("")
    if ideas.empty:
        lines.append("- No strong ideas surfaced this run.")
    else:
        for _, r in ideas.iterrows():
            held = bool(r.get("is_already_held", False))
            tag = " (already held)" if held else ""
            sec = str(r.get("sector", "") or "").strip()
            sec_bit = f" | sector={sec}" if sec else ""
            lines.append(
                f"- {r['ticker']}{tag}{sec_bit} | action={r['action']} | overall={r['overall_score']:.2f} | "
                f"suggested amount ≈ KES {r['suggested_amount_kes']:,.0f} | note: {r.get('watch_notes', '')}"
            )

    lines.append("")
    lines.append("## Risk alerts")
    lines.append("")
    if alerts:
        for a in alerts:
            lines.append(f"- {a}")
    else:
        lines.append("- No portfolio concentration breaches found.")

    lines.append("")
    lines.extend(lines_if_uneasy(cfg, alerts))
    lines.extend(lines_before_you_trade())
    lines.extend(lines_discipline_short())
    return "\n".join(lines)
