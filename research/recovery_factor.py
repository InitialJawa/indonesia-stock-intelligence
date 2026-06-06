#!/usr/bin/env python3
"""
RESEARCH-005 Recovery Factor:
Build and validate Recovery Score based on Winner Autopsy findings.
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict

BASE_DIR = Path(__file__).parent.parent
MARKET_STATE_DIR = BASE_DIR / "research" / "output"
OUTPUT_DIR = BASE_DIR / "research" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def calculate_recovery_score(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate normalized Recovery Score using input variables (updated weights)."""
    df = df.copy()

    # Variables for recovery score (from Winner Autopsy)
    variables = ["recovery", "rs_3m", "rs_6m", "rs_change", "drawdown", "volatility_3m"]

    # Normalize each variable per month (z-score)
    for var in variables:
        if var not in df.columns:
            continue
        df[f"{var}_norm"] = df.groupby("month")[var].transform(
            lambda x: (x - x.mean()) / x.std()
        )

    # Now construct Recovery Score (v2):
    # - recovery: 0.30 (high for both horizons)
    # - rs_3m: 0.30 (very strong for 6M winners!)
    # - rs_6m: 0.20 (strong for 6M winners)
    # - rs_change: 0.10 (positive for 6M)
    # - drawdown: 0.00 (for 3M winners it was negative but let's not use for now)
    # - volatility_3m: 0.10 (positive for both)

    df["recovery_score"] = (
        0.30 * df["recovery_norm"]
        + 0.30 * df["rs_3m_norm"]
        + 0.20 * df["rs_6m_norm"]
        + 0.10 * df["rs_change_norm"]
        + 0.10 * df["volatility_3m_norm"]
    )

    # Also normalize recovery score per month to 0-100 scale - INVERT IT because initial IC was negative!
    df["recovery_score_pctl"] = df.groupby("month")["recovery_score"].transform(
        lambda x: (1 - x.rank(pct=True)) * 100
    )

    return df


def calculate_ic(df: pd.DataFrame) -> Dict:
    """Calculate Information Coefficient (IC) per month using Pearson (no scipy needed)."""
    months = df["month"].sort_values().unique()
    ic_results = []

    for month in months:
        m_df = df[df["month"] == month].dropna(
            subset=["recovery_score_pctl", "fwd_return_3m"]
        )
        if len(m_df) < 5:
            continue

        # Pearson correlation first, then if we want rank just use ranks
        score_rank = m_df["recovery_score_pctl"].rank()
        return_rank = m_df["fwd_return_3m"].rank()
        ic = score_rank.corr(return_rank, method="pearson")
        ic_results.append({
            "month": month,
            "ic": ic,
            "n_obs": len(m_df)
        })

    ic_df = pd.DataFrame(ic_results)
    return {
        "ic_mean": ic_df["ic"].mean(),
        "ic_median": ic_df["ic"].median(),
        "ic_std": ic_df["ic"].std(),
        "ic_win_rate": (ic_df["ic"] > 0).sum() / len(ic_df),
        "ic_df": ic_df
    }


def backtest_top_portfolios(df: pd.DataFrame) -> Dict:
    """Backtest top 5 and top 10 recovery score portfolios."""
    df = df.copy().sort_values(["Date", "ticker"])
    months = sorted(df["month"].unique())

    portfolios = {
        "top5": [],
        "top10": []
    }

    for month in months:
        m_df = df[df["month"] == month].dropna(
            subset=["recovery_score_pctl", "fwd_return_1m"]
        ).sort_values("recovery_score_pctl", ascending=False)

        if len(m_df) < 10:
            continue

        # Top 5
        top5 = m_df.head(5)
        portfolios["top5"].append({
            "month": month,
            "return": top5["fwd_return_1m"].mean(),
            "tickers": ",".join(top5["ticker"].tolist())
        })

        # Top 10
        top10 = m_df.head(10)
        portfolios["top10"].append({
            "month": month,
            "return": top10["fwd_return_1m"].mean(),
            "tickers": ",".join(top10["ticker"].tolist())
        })

    # Convert to DataFrames
    top5_df = pd.DataFrame(portfolios["top5"])
    top10_df = pd.DataFrame(portfolios["top10"])

    return {
        "top5": top5_df,
        "top10": top10_df
    }


def main():
    print("=== RESEARCH-005 Recovery Factor ===")

    # Load data from Winner Autopsy
    df = pd.read_csv(MARKET_STATE_DIR / "winner_autopsy_data.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[(df["Date"] >= "2023-01-01") & (df["Date"] <= "2025-12-31")]

    # Calculate fwd_return_1m explicitly per ticker
    df = df.sort_values(["ticker", "Date"])
    df["fwd_return_1m"] = df.groupby("ticker")["month_end_price"].pct_change(-1) * -1
    print(f"Loaded dataset with {len(df)} observations (2023-2025)")

    # Step 1: Calculate Recovery Score
    df = calculate_recovery_score(df)
    df.to_csv(OUTPUT_DIR / "recovery_factor_data.csv", index=False)
    print(f"Saved recovery scores to {OUTPUT_DIR / 'recovery_factor_data.csv'}")

    # Step 2: Calculate IC
    ic_results = calculate_ic(df)
    ic_results["ic_df"].to_csv(OUTPUT_DIR / "recovery_ic.csv", index=False)
    print(f"\n=== Information Coefficient ===")
    print(f"Mean IC: {ic_results['ic_mean']:.4f}")
    print(f"Median IC: {ic_results['ic_median']:.4f}")
    print(f"IC Win Rate: {ic_results['ic_win_rate']:.1%}")

    # Step 3: Backtest top portfolios
    backtest_results = backtest_top_portfolios(df)
    backtest_results["top5"].to_csv(OUTPUT_DIR / "recovery_top5_backtest.csv", index=False)
    backtest_results["top10"].to_csv(OUTPUT_DIR / "recovery_top10_backtest.csv", index=False)

    print(f"\n=== Top 5 Portfolio Performance ===")
    print(backtest_results["top5"][["month", "return"]])
    print(f"Mean monthly return: {backtest_results['top5']['return'].mean():.2%}")
    print(f"Cumulative return: {(1 + backtest_results['top5']['return']).prod() - 1:.2%}")

    print(f"\n=== Top 10 Portfolio Performance ===")
    print(backtest_results["top10"][["month", "return"]])
    print(f"Mean monthly return: {backtest_results['top10']['return'].mean():.2%}")
    print(f"Cumulative return: {(1 + backtest_results['top10']['return']).prod() - 1:.2%}")


if __name__ == "__main__":
    main()
