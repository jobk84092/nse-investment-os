import pandas as pd
from src.utils.paths import settings

def portfolio_snapshot(holdings: pd.DataFrame) -> pd.DataFrame:
    df = holdings.copy()
    df["market_value"] = df["quantity"] * df["current_price"]
    df["cost_value"] = df["quantity"] * df["avg_cost"]
    df["unrealized_pl"] = df["market_value"] - df["cost_value"]
    total = df["market_value"].sum() if len(df) else 0
    df["weight_pct"] = (df["market_value"] / total * 100).round(2) if total else 0
    return df.sort_values("market_value", ascending=False)

def sector_snapshot(holdings: pd.DataFrame) -> pd.DataFrame:
    df = portfolio_snapshot(holdings)
    sector = df.groupby("sector", as_index=False)["market_value"].sum()
    total = sector["market_value"].sum() if len(sector) else 0
    sector["sector_weight_pct"] = (sector["market_value"] / total * 100).round(2) if total else 0
    return sector.sort_values("market_value", ascending=False)

def concentration_alerts(holdings: pd.DataFrame) -> list[str]:
    cfg = settings()["position_limits"]
    alerts = []
    snap = portfolio_snapshot(holdings)
    for _, row in snap.iterrows():
        if row["weight_pct"] > cfg["max_single_stock_pct"]:
            alerts.append(f"{row['ticker']} exceeds single-stock limit at {row['weight_pct']}%.")
    sector = sector_snapshot(holdings)
    for _, row in sector.iterrows():
        if row["sector_weight_pct"] > cfg["max_single_sector_pct"]:
            alerts.append(f"{row['sector']} exceeds sector limit at {row['sector_weight_pct']}%.")
    return alerts
