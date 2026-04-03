"""
Comfort-first strategy copy for the monthly memo: how to read outputs, not what to buy.
"""
from __future__ import annotations

from typing import Any

import pandas as pd


def lines_how_to_read_this_memo(cfg: dict[str, Any]) -> list[str]:
    note = (cfg.get("guidance") or {}).get("personal_comfort_note", "").strip()
    lines = [
        "## Read this first",
        "",
        "This file is a **checklist and mirror**: it does not know more than the inputs you gave it. It combines:",
        "",
        "- **Your** manual scores and watchlist CSVs (you can change them anytime).",
        "- **Your** latest holdings (from `holdings.csv` or the PDF sync).",
        "- Simple **position and sector limits** from `config/settings.json`.",
        "- A **playbook** section that ranks **new money** vs **add-ons** using those scores—still **your** call.",
        "",
        "If something here makes you uneasy, that is useful information. The default healthy action is often: **no new trade** until you can explain the thesis in one paragraph.",
        "",
    ]
    if note:
        lines.extend(["**Your note to yourself:**", "", note, ""])
    return lines


def lines_strategy_snapshot(cfg: dict[str, Any]) -> list[str]:
    inv = cfg["investor_profile"]
    alloc = cfg["allocation_policy"]
    lim = cfg["position_limits"]
    lines = [
        "## Strategy snapshot (from your settings)",
        "",
        f"- Stated style: **{inv.get('strategy', '')}**.",
        f"- Target mix (intent, not a command): ~{alloc['core_compounders_pct']}% core compounders, "
        f"~{alloc['value_opportunities_pct']}% value, ~{alloc['special_situations_pct']}% special situations.",
        f"- Position guardrails: max **{lim['max_single_stock_pct']}%** in one stock, "
        f"max **{lim['max_single_sector_pct']}%** in one sector.",
        "",
        "Those percentages are **policy you chose**. Breaking them can be fine if deliberate; "
        "the memo flags when reality and policy disagree so you decide consciously.",
        "",
    ]
    bn = (inv.get("budget_note") or "").strip()
    if bn:
        lines.extend([f"- Budget note: {bn}", ""])
    return lines


def lines_limits_vs_portfolio(
    holdings: pd.DataFrame,
    sectors: pd.DataFrame,
    limits: dict[str, float],
) -> list[str]:
    lines = ["## Your rules vs this portfolio", ""]
    if holdings.empty:
        lines.append("- No holdings loaded; add positions or run PDF sync.")
        lines.append("")
        return lines

    max_stock = float(limits["max_single_stock_pct"])
    max_sec = float(limits["max_single_sector_pct"])
    over_stock = holdings[holdings["weight_pct"] > max_stock].sort_values(
        "weight_pct", ascending=False
    )
    over_sec = (
        sectors[sectors["sector_weight_pct"] > max_sec].sort_values(
            "sector_weight_pct", ascending=False
        )
        if not sectors.empty
        else pd.DataFrame()
    )

    if over_stock.empty and over_sec.empty:
        lines.append(
            f"- No line-item breaches right now: every position is at or under **{max_stock}%**, "
            f"every sector at or under **{max_sec}%** (by this run’s numbers)."
        )
        lines.append("")
        lines.append(
            "- If you still feel heavy in one theme (e.g. gold, banks), trust that feeling: "
            "limits are a crude tool, not a full risk picture."
        )
        lines.append("")
        return lines

    if not over_stock.empty:
        lines.append(
            f"**Single-name weight above {max_stock}%** (policy line). "
            "This is not “sell now”; it means size deserves a conscious decision:"
        )
        lines.append("")
        for _, r in over_stock.iterrows():
            lines.append(
                f"- **{r['ticker']}** at **{r['weight_pct']:.2f}%** of the book. "
                "Options: trim over time, stop adding there, or formally accept a higher ceiling and document why."
            )
        lines.append("")

    if not over_sec.empty:
        lines.append(
            f"**Sector weight above {max_sec}%** (policy line). Same idea: notice, then choose on purpose."
        )
        lines.append("")
        for _, r in over_sec.iterrows():
            lines.append(
                f"- **{r['sector']}** at **{r['sector_weight_pct']:.2f}%**."
            )
        lines.append("")

    return lines


def lines_about_top_ideas(ideas: pd.DataFrame) -> list[str]:
    lines = [
        "## How to read “Top current ideas”",
        "",
        "- The table below is the **same short list** as **This month’s playbook**, with raw scores and notes.",
        "- Order is **non-held names first** (then held), still ranked by **your** composite score—not broker consensus.",
        '- **BUY** / **WATCH** come from **simple score thresholds** in code; override them with judgment.',
        "- Use the playbook’s **sector callouts** when one theme (e.g. banks) is already heavy.",
        "",
    ]
    if ideas.empty:
        lines.append("- This run did not surface a short list; that can be a good month to **do nothing** or **research one name**.")
        lines.append("")
    return lines


def lines_if_uneasy(cfg: dict[str, Any], alerts: list[str]) -> list[str]:
    g = cfg.get("guidance") or {}
    default_act = g.get("when_uncertain", "pause_new_buys")
    lines = [
        "## If you feel uneasy this month",
        "",
        "Pick **one** path (seriously, one):",
        "",
        "1. **Pause** — no new purchases until the next valuation PDF sync + one memo read-through.",
        "2. **Clarify** — pick **one** position that bothers you; write 5 sentences: business model, why you own it, what would make you sell.",
        "3. **Rebalance slowly** — if policy limits matter to you, plan a **trim or redirect new cash** over months, not in one emotional trade.",
        "",
    ]
    if default_act == "pause_new_buys":
        lines.append(
            f"*Your setting `guidance.when_uncertain` is **{default_act}**: default to no new buys until clarity returns.*"
        )
    else:
        lines.append(f"*Your setting `guidance.when_uncertain`: **{default_act}**.*")
    lines.append("")
    if alerts:
        lines.append(
            "Alerts above are **tripwires**, not orders. They exist so concentration does not drift in silence."
        )
        lines.append("")
    return lines


def lines_before_you_trade() -> list[str]:
    return [
        "## Before you buy (or add)",
        "",
        "Answer briefly (on paper or in your journal):",
        "",
        "1. What does the company earn, and why can it still be earning that in five years?",
        "2. What has to go **right** for this to work? What would prove you wrong?",
        "3. After this buy, what is your **approximate** weight in this stock and this sector?",
        "4. Is this **new money**, or are you **avoiding** a harder decision elsewhere?",
        "5. If the market cuts this price 20% next month, do you still want to own it?",
        "",
    ]


def lines_discipline_short() -> list[str]:
    return [
        "## Discipline (short)",
        "",
        "- One or two decisions per month beats ten small ones.",
        "- News and scores **inform**; they do not **compel**.",
        "- Longer notes: `docs/STRATEGY_AND_COMFORT.md` and `docs/WORKFLOW.md`.",
        "",
    ]
