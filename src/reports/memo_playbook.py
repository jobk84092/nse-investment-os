"""
Synthesized “what to do / what to buy next” section from the user’s own scores, budget, and limits.
Not third-party research; ties expert homework (Market pulse) to ranked ideas.
"""
from __future__ import annotations

from typing import Any

import pandas as pd


def _sector_weight(sectors: pd.DataFrame, sector_name: str) -> float | None:
    if sectors.empty or not sector_name:
        return None
    m = sectors[sectors["sector"].astype(str).str.strip().str.lower() == sector_name.strip().lower()]
    if m.empty:
        return None
    return float(m.iloc[0]["sector_weight_pct"])


def lines_monthly_playbook(
    cfg: dict[str, Any],
    holdings: pd.DataFrame,
    sectors: pd.DataFrame,
    ideas: pd.DataFrame,
    budget_kes: float,
    budget_month: str,
) -> list[str]:
    limits = cfg.get("position_limits") or {}
    max_sec = float(limits.get("max_single_sector_pct", 35))
    pb_cfg = cfg.get("memo_playbook") or {}
    max_new = int(pb_cfg.get("max_new_money_slots", 3))

    lines: list[str] = [
        "## This month’s playbook (your data, your rules)",
        "",
        "This block **compresses** scores + budget + sector limits into a short plan. It is still **your** research and conviction—",
        "not a tip sheet. Use **Market pulse** below for NSE headlines and expert links you curated.",
        "",
    ]

    bm = (budget_month or "").strip()
    if bm:
        lines.append(f"- **Budget row in use:** `{bm}` → **KES {budget_kes:,.0f}** for suggested split amounts.")
    else:
        lines.append(f"- **Budget in use:** **KES {budget_kes:,.0f}** (from `monthly_budget.csv` last row or settings default).")
    if not holdings.empty and "market_value" in holdings.columns:
        tv = float(holdings["market_value"].sum())
        lines.append(f"- **Portfolio value (this run):** KES {tv:,.2f}")
    lines.append("")

    if ideas.empty:
        lines.extend(
            [
                "- No BUY/WATCH names passed filters this run. Reasonable actions: **do nothing**, **refresh one thesis** in your CSV, "
                "or **add** a name to `approved_universe.csv` after reading the Market pulse links.",
                "",
            ]
        )
        return lines

    new_ideas = ideas[~ideas["is_already_held"]].head(max_new)
    held_ideas = ideas[ideas["is_already_held"]]

    lines.append("### 1) New money — suggested order (highest composite score among non-held names)")
    lines.append("")
    if new_ideas.empty:
        lines.append(
            "- Every name in the short list is **already in the book**. See “Top current ideas” for add-on sizing, "
            "or raise scores / add tickers so new names enter BUY/WATCH."
        )
        lines.append("")
    else:
        for i, (_, r) in enumerate(new_ideas.iterrows(), start=1):
            t = str(r["ticker"]).strip().upper()
            sec = str(r.get("sector", "") or "").strip()
            sw = _sector_weight(sectors, str(sec))
            action = str(r.get("action", ""))
            amt = float(r.get("suggested_amount_kes", 0) or 0)
            note = str(r.get("watch_notes", "") or "").strip()
            note_short = (note[:120] + "…") if len(note) > 120 else note
            tail = f" — _{note_short}_" if note_short else ""
            line = (
                f"{i}. **{t}** ({action}) · sector _{sec or 'n/a'}_ · **≈ KES {amt:,.0f}**{tail}"
            )
            lines.append(f"- {line}")
            if sw is not None and sw >= max_sec - 5:
                lines.append(
                    f"  - *Sector check:* **{sec}** is already **{sw:.1f}%** of the portfolio (your ceiling is **{max_sec}%**). "
                    "Adding here needs a **deliberate** reason, not autopilot."
                )
            elif sw is not None and sw >= max_sec * 0.75:
                lines.append(
                    f"  - *Sector check:* **{sec}** is **{sw:.1f}%**—getting full; consider **diversifying** new cash elsewhere."
                )
        lines.append("")

    lines.append("### 2) Already own — only if thesis intact")
    lines.append("")
    if held_ideas.empty:
        lines.append("- None of this run’s top five are names you already hold (or list is all new).")
    else:
        for _, r in held_ideas.iterrows():
            t = str(r["ticker"]).strip().upper()
            action = str(r.get("action", ""))
            amt = float(r.get("suggested_amount_kes", 0) or 0)
            lines.append(
                f"- **{t}** ({action}) · suggested add ≈ **KES {amt:,.0f}** — use only if you still want **more** exposure, not because it is familiar."
            )
    lines.append("")

    lines.extend(
        [
            "### 3) What to do before you click buy",
            "",
            "- Skim **at least one** item under *Voices you curate* or *Investment headlines* that touches **your sector or ticker**.",
            "- If NSE corporate-action links are empty, open the live `nse_sources` pages once—tables often need the browser.",
            "- If nothing passes your smell test: **pause** matches your `guidance.when_uncertain` setting.",
            "",
        ]
    )

    return lines
