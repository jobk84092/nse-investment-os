import pandas as pd
from src.utils.paths import settings

def score_universe(universe: pd.DataFrame, news: pd.DataFrame | None = None) -> pd.DataFrame:
    cfg = settings()["scoring_weights"]
    df = universe.copy()

    for col in [
        "manual_quality", "manual_value", "manual_capital_allocation",
        "manual_balance_sheet", "manual_dividend", "news_penalty"
    ]:
        if col not in df.columns:
            df[col] = 0.0

    df["quality_score"] = df["manual_quality"].astype(float)
    df["value_score"] = df["manual_value"].astype(float)
    df["capital_allocation_score"] = df["manual_capital_allocation"].astype(float)
    df["balance_sheet_score"] = df["manual_balance_sheet"].astype(float)
    df["dividend_score"] = df["manual_dividend"].astype(float)
    df["news_governance_adjustment"] = df["news_penalty"].astype(float)

    df["overall_score"] = (
        cfg["quality"] * df["quality_score"]
        + cfg["value"] * df["value_score"]
        + cfg["dividend"] * df["dividend_score"]
        + cfg["balance_sheet"] * df["balance_sheet_score"]
        + cfg["capital_allocation"] * df["capital_allocation_score"]
        + cfg["news_governance_adjustment"] * (10 - df["news_governance_adjustment"])
    )

    df["action"] = "WATCH"
    df.loc[
        (df["quality_score"] >= 7.0) &
        (df["value_score"] >= 6.7) &
        (df["news_governance_adjustment"] <= 0.4),
        "action"
    ] = "BUY"
    df.loc[df["news_governance_adjustment"] >= 0.8, "action"] = "AVOID"

    return df.sort_values(["overall_score", "quality_score", "value_score"], ascending=False).reset_index(drop=True)
