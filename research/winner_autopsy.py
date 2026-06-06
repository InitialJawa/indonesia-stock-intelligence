#!/usr/bin/env python3
"""
RESEARCH-004B Winner Autopsy:
Identify characteristics of stocks BEFORE large advances.
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict

BASE_DIR = Path(__file__).parent.parent
INPUT_DIR = BASE_DIR / "database" / "historical"
MARKET_STATE_DIR = BASE_DIR / "research" / "output"
OUTPUT_DIR = BASE_DIR / "research" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_data() -> pd.DataFrame:
    """Load and merge market state data with factor warehouse scores."""

    # Load market state data
    ms_df = pd.read_csv(MARKET_STATE_DIR / "market_states_all.csv")
    ms_df["Date"] = pd.to_datetime(ms_df["Date"])
    ms_df["month"] = ms_df["Date"].dt.strftime("%Y-%m")

    # Load factor warehouse
    fw_df = pd.read_csv(INPUT_DIR / "factor_warehouse.csv")
    fw_df["month"] = fw_df["date"]  # already in YYYY-MM format
    fw_df = fw_df.drop("date", axis=1)

    # Merge on ticker and month
    merged = pd.merge(
        ms_df,
        fw_df,
        left_on=["ticker", "month"],
        right_on=["ticker", "month"],
        how="left"
    )

    return merged


def calculate_winner_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Define winner events: forward 3M > 20%, forward 6M > 40%."""
    df = df.copy()

    tickers = df["ticker"].unique()
    all_processed = []

    for ticker in tickers:
        t_df = df[df["ticker"] == ticker].copy().sort_values("Date")
        prices = t_df.set_index("Date")["month_end_price"]

        # Calculate forward returns (explicitly)
        t_df = t_df.set_index("Date")
        t_df["fwd_return_3m"] = prices.pct_change(-3) * -1
        t_df["fwd_return_6m"] = prices.pct_change(-6) * -1

        # Calculate volatility (3M rolling std of monthly returns)
        t_df["monthly_return"] = prices.pct_change()
        t_df["volatility_3m"] = t_df["monthly_return"].rolling(window=3, min_periods=2).std()

        t_df = t_df.reset_index()

        all_processed.append(t_df)

    df = pd.concat(all_processed, ignore_index=True)

    # Filter period: 2023-2025
    df = df[(df["Date"] >= "2023-01-01") & (df["Date"] <= "2025-12-31")]

    # Label winners
    df["is_winner_3m"] = df["fwd_return_3m"] > 0.20
    df["is_winner_6m"] = df["fwd_return_6m"] > 0.40

    return df


def analyze_differences(df: pd.DataFrame) -> Dict:
    """Compare winners vs non-winners across all variables."""

    variables = [
        "quality_score", "value_score", "growth_score", "momentum_score",
        "rs_3m", "rs_6m", "rs_change", "drawdown", "recovery", "volatility_3m",
        "final_score"
    ]

    results = []

    for label in ["is_winner_3m", "is_winner_6m"]:
        group_true = df[df[label] == True]
        group_false = df[df[label] == False]

        for var in variables:
            if var not in df.columns:
                continue

            mean_true = group_true[var].mean()
            mean_false = group_false[var].mean()
            median_true = group_true[var].median()
            median_false = group_false[var].median()
            diff_mean = mean_true - mean_false
            diff_median = median_true - median_false

            results.append({
                "winner_type": label,
                "variable": var,
                "winner_mean": mean_true,
                "non_winner_mean": mean_false,
                "winner_median": median_true,
                "non_winner_median": median_false,
                "diff_mean": diff_mean,
                "diff_median": diff_median,
                "winner_count": len(group_true.dropna(subset=[var])),
                "non_winner_count": len(group_false.dropna(subset=[var]))
            })

    return pd.DataFrame(results)


def main():
    print("=== RESEARCH-004B Winner Autopsy ===")

    df = load_data()
    print(f"Loaded merged dataset with {len(df)} observations")

    df = calculate_winner_labels(df)
    df.to_csv(OUTPUT_DIR / "winner_autopsy_data.csv", index=False)
    print(f"Saved labeled data to {OUTPUT_DIR / 'winner_autopsy_data.csv'}")

    analysis = analyze_differences(df)
    analysis.to_csv(OUTPUT_DIR / "winner_analysis.csv", index=False)
    print(f"Saved analysis to {OUTPUT_DIR / 'winner_analysis.csv'}")

    print("\n=== Winner Counts ===")
    print("3M winners (>20%):", df["is_winner_3m"].sum())
    print("6M winners (>40%):", df["is_winner_6m"].sum())

    print("\n=== Top Predictors for 3M Winners (sorted by mean difference) ===")
    top_3m = analysis[analysis["winner_type"] == "is_winner_3m"].sort_values("diff_mean", ascending=False).head(10)
    print(top_3m[["variable", "diff_mean", "winner_mean", "non_winner_mean"]].round(4))

    print("\n=== Top Predictors for 6M Winners (sorted by mean difference) ===")
    top_6m = analysis[analysis["winner_type"] == "is_winner_6m"].sort_values("diff_mean", ascending=False).head(10)
    print(top_6m[["variable", "diff_mean", "winner_mean", "non_winner_mean"]].round(4))


if __name__ == "__main__":
    main()
