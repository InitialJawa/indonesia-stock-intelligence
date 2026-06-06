#!/usr/bin/env python3
"""
RESEARCH-004 Phase 1: Market State Engine
Prototype for state classification and backtesting.
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional

BASE_DIR = Path(__file__).parent.parent
INPUT_DIR = BASE_DIR / "database" / "monthly"
BENCHMARK_FILE = BASE_DIR / "benchmarks" / "ihsg.csv"
METADATA_FILE = BASE_DIR / "database" / "historical" / "ticker_metadata.csv"
OUTPUT_DIR = BASE_DIR / "research" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

STATES = ["AVOID", "WEAK", "WATCH", "ACCUMULATE", "BUY"]


def load_ihsg() -> Optional[pd.Series]:
    """Load IHSG benchmark prices."""
    if not BENCHMARK_FILE.exists():
        print(f"Warning: Benchmark file not found at {BENCHMARK_FILE}")
        return None

    try:
        ihsg_df = pd.read_csv(BENCHMARK_FILE)
        date_col = next((c for c in ihsg_df.columns if c.lower() in ["date", "tanggal"]), ihsg_df.columns[0])
        price_col = next((c for c in ihsg_df.columns if c.lower() in ["close", "adj close", "price"]), ihsg_df.columns[1])
        ihsg_df[date_col] = pd.to_datetime(ihsg_df[date_col])
        return ihsg_df.set_index(date_col).sort_index()[price_col].astype(float)
    except Exception as e:
        print(f"Warning: Failed to load IHSG: {e}")
        return None


def load_metadata() -> pd.DataFrame:
    """Load ticker metadata (listing dates)."""
    if METADATA_FILE.exists():
        return pd.read_csv(METADATA_FILE)
    return pd.DataFrame()


def calculate_indicators(
    df: pd.DataFrame,
    ihsg: Optional[pd.Series] = None
) -> pd.DataFrame:
    """
    Calculate all required market state indicators for each time point:
    - 3M return
    - 6M return
    - 12M return
    - Relative strength vs IHSG (RS-6M)
    - Relative strength change (delta RS over past 1M)
    - Drawdown from 12M high
    - Recovery from drawdown
    """
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()

    # Price-based returns
    prices = df["month_end_price"].ffill()

    df["return_3m"] = prices.pct_change(3)
    df["return_6m"] = prices.pct_change(6)
    df["return_12m"] = prices.pct_change(12)

    # Relative strength vs IHSG
    if ihsg is not None:
        df["ihsg_price"] = ihsg.reindex(df.index, method="ffill")
        df["stock_return_6m"] = prices.pct_change(6)
        df["ihsg_return_6m"] = df["ihsg_price"].pct_change(6)
        df["rs_6m"] = df["stock_return_6m"] - df["ihsg_return_6m"]
        df["rs_3m"] = prices.pct_change(3) - df["ihsg_price"].pct_change(3)
    else:
        df["rs_6m"] = df["return_6m"]
        df["rs_3m"] = df["return_3m"]

    df["rs_change"] = df["rs_6m"].diff()

    # Drawdown from 12M high
    df["high_12m"] = prices.rolling(window=12, min_periods=1).max()
    df["drawdown"] = (prices - df["high_12m"]) / df["high_12m"]  # negative values only

    # Recovery from recent lows
    df["low_3m"] = prices.rolling(window=3, min_periods=1).min()
    df["recovery"] = (prices - df["low_3m"]) / df["low_3m"]

    return df.reset_index()


def classify_state(row: pd.Series) -> str:
    """
    Classify market state based on indicators.
    State definitions as per RESEARCH-004.
    """
    # Extract indicators
    rs_6m = row["rs_6m"] if pd.notna(row["rs_6m"]) else -1.0
    return_6m = row["return_6m"] if pd.notna(row["return_6m"]) else -1.0
    return_3m = row["return_3m"] if pd.notna(row["return_3m"]) else -1.0
    rs_change = row["rs_change"] if pd.notna(row["rs_change"]) else -1.0
    drawdown = row["drawdown"] if pd.notna(row["drawdown"]) else -1.0
    recovery = row["recovery"] if pd.notna(row["recovery"]) else 0.0

    # --- BUY State ---
    if (
        rs_6m > 0.05 and
        return_6m > 0.1 and
        return_3m > 0.03 and
        drawdown > -0.1
    ):
        return "BUY"

    # --- ACCUMULATE State ---
    if (
        rs_6m > 0.0 and
        return_6m > 0.03 and
        rs_change > -0.02 and
        recovery > 0.05
    ):
        return "ACCUMULATE"

    # --- WATCH State ---
    if (
        rs_change > 0.0 and
        recovery > 0.02 and
        return_3m > -0.05
    ):
        return "WATCH"

    # --- WEAK State ---
    if (
        drawdown > -0.15 and
        return_3m > -0.08
    ):
        return "WEAK"

    # --- AVOID State (default) ---
    return "AVOID"


def process_ticker(
    file_path: Path,
    ihsg: Optional[pd.Series] = None,
    listing_date: Optional[pd.Timestamp] = None
) -> pd.DataFrame:
    """Process a single ticker's data through the market state engine."""
    try:
        df = pd.read_csv(file_path)
        if len(df) < 13:
            return pd.DataFrame()

        df = calculate_indicators(df, ihsg)

        # Filter by listing date if available
        if listing_date is not None:
            df = df[df["Date"] >= listing_date]

        df["ticker"] = file_path.stem
        df["state"] = df.apply(classify_state, axis=1)

        return df
    except Exception as e:
        print(f"Error processing {file_path.name}: {e}")
        return pd.DataFrame()


def backtest_transitions(all_data: pd.DataFrame) -> Dict:
    """
    Backtest state transitions for 2023-2025.
    Calculate:
    - Next 1M return
    - Next 3M return
    - Next 6M return
    - Hit rate
    - Average drawdown after signal
    """
    results = []

    tickers = all_data["ticker"].unique()

    for ticker in tickers:
        df = all_data[all_data["ticker"] == ticker].copy().sort_values("Date")
        df = df.set_index("Date")

        # Calculate forward returns
        prices = df["month_end_price"]
        df["fwd_return_1m"] = prices.pct_change(-1) * -1  # next month
        df["fwd_return_3m"] = prices.pct_change(-3) * -1
        df["fwd_return_6m"] = prices.pct_change(-6) * -1

        # Forward drawdown (worst drawdown in next 3 months)
        df["fwd_drawdown_3m"] = np.nan
        for i in range(len(df) - 3):
            future_prices = prices.iloc[i : i + 3]
            future_high = future_prices.expanding().max()
            future_drawdown = (future_prices - future_high) / future_high
            df.iloc[i, df.columns.get_loc("fwd_drawdown_3m")] = future_drawdown.min()

        df = df.reset_index()
        df = df[(df["Date"] >= "2023-01-01") & (df["Date"] <= "2025-12-31")]

        if len(df) == 0:
            continue

        # Get transitions
        df["prev_state"] = df["state"].shift(1)
        df["transition"] = df["prev_state"] + " → " + df["state"]

        results.append(df)

    all_results = pd.concat(results, ignore_index=True)

    # Aggregate by state and transition
    state_stats = all_results.groupby("state").agg({
        "fwd_return_1m": ["mean", "median", "count"],
        "fwd_return_3m": ["mean", "median", "count"],
        "fwd_return_6m": ["mean", "median", "count"],
        "fwd_drawdown_3m": ["mean", "median", "min"]
    }).round(4)

    transition_stats = all_results.groupby("transition").agg({
        "fwd_return_1m": ["mean", "median", "count"],
        "fwd_return_3m": ["mean", "median", "count"],
        "fwd_return_6m": ["mean", "median", "count"]
    }).round(4)

    return {
        "all_results": all_results,
        "state_stats": state_stats,
        "transition_stats": transition_stats
    }


def main():
    print("=== RESEARCH-004 Phase 1: Market State Engine ===")

    # Load data
    ihsg = load_ihsg()
    metadata = load_metadata()
    listing_dates = {}
    if not metadata.empty:
        listing_dates = {row["ticker"]: pd.to_datetime(row["listing_date"]) for _, row in metadata.iterrows()}

    # Process all tickers
    all_data = []
    files = sorted(INPUT_DIR.glob("*.csv"))

    print(f"Processing {len(files)} tickers...")
    for file in files:
        ticker = file.stem
        listing_date = listing_dates.get(ticker)
        df = process_ticker(file, ihsg, listing_date)
        if not df.empty:
            all_data.append(df)

    if not all_data:
        print("No data processed.")
        return

    all_data = pd.concat(all_data, ignore_index=True)

    # Save processed data
    all_data.to_csv(OUTPUT_DIR / "market_states_all.csv", index=False)
    print(f"Saved full state data to {OUTPUT_DIR / 'market_states_all.csv'}")

    # Backtest
    print("\nRunning backtest for 2023-2025...")
    backtest_results = backtest_transitions(all_data)

    backtest_results["all_results"].to_csv(OUTPUT_DIR / "backtest_results.csv", index=False)
    backtest_results["state_stats"].to_csv(OUTPUT_DIR / "state_stats.csv")
    backtest_results["transition_stats"].to_csv(OUTPUT_DIR / "transition_stats.csv")
    print(f"Saved backtest results to {OUTPUT_DIR}")

    print("\n=== State Distribution (2023-2025) ===")
    state_counts = backtest_results["all_results"]["state"].value_counts()
    print(state_counts)

    print("\n=== Top 10 Most Frequent Transitions ===")
    transition_counts = backtest_results["all_results"]["transition"].value_counts().head(10)
    print(transition_counts)

    print("\n=== State Performance ===")
    print(backtest_results["state_stats"])


if __name__ == "__main__":
    main()
