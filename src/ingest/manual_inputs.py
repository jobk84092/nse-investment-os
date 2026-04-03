import pandas as pd
from src.utils.paths import DATA_MANUAL
from src.utils.io import read_csv

def load_holdings() -> pd.DataFrame:
    return read_csv(DATA_MANUAL / "holdings.csv")

def load_budget() -> pd.DataFrame:
    return read_csv(DATA_MANUAL / "monthly_budget.csv")

def load_universe() -> pd.DataFrame:
    return read_csv(DATA_MANUAL / "approved_universe.csv")

def load_simply() -> pd.DataFrame:
    return read_csv(DATA_MANUAL / "simplywallst_watchlist.csv")

def load_ndindi() -> pd.DataFrame:
    return read_csv(DATA_MANUAL / "ndindi_tracker.csv")


def load_market_commentary() -> pd.DataFrame:
    """Curated links / notes (Abojani, Ndindi posts, newsletters you pasted)."""
    return read_csv(DATA_MANUAL / "market_commentary.csv")
