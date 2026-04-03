import pandas as pd


def top_ideas(scored: pd.DataFrame, holdings: pd.DataFrame, monthly_budget: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    held = set(holdings["ticker"].astype(str)) if not holdings.empty else set()
    budget = monthly_budget.iloc[-1]["budget_kes"] if not monthly_budget.empty else 20000

    df = scored.copy()
    df["is_already_held"] = df["ticker"].astype(str).isin(held)
    df = df[df["action"].isin(["BUY", "WATCH"])].copy()
    # Surface **new** names first at the same score tier (better “what to buy” list).
    df = df.sort_values(
        ["is_already_held", "overall_score", "quality_score", "value_score"],
        ascending=[True, False, False, False],
    )
    df["suggested_amount_kes"] = 0

    preferred = [0.70, 0.20, 0.10]
    top_idx = df.head(top_n).index
    for i, idx in enumerate(top_idx):
        allocation = preferred[i] if i < len(preferred) else max(0.0, 0.10 / max(1, top_n - 3))
        df.loc[idx, "suggested_amount_kes"] = round(budget * allocation, 0)

    return df.loc[top_idx].reset_index(drop=True)
