#!/usr/bin/env python3
"""
RESEARCH-006: Recovery Overlay Validation
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
INPUT_DIR = BASE_DIR / "research" / "output"
OUTPUT_DIR = BASE_DIR / "research" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_and_prepare_data():
    # Load recovery factor data
    recovery_data = pd.read_csv(INPUT_DIR / "recovery_factor_data.csv")
    recovery_data["Date"] = pd.to_datetime(recovery_data["Date"])

    # Since we don't have full historical ISI Config B scores,
    # we'll create a synthetic Config B score using momentum score (as a placeholder)
    # We'll use what's available in the data
    df = recovery_data.copy()

    # Normalize Recovery Score to 0-100 per month (same as ISI)
    df["recovery_0_100"] = df.groupby("month")["recovery_score_pctl"].transform(
        lambda x: (x - x.min()) / (x.max() - x.min()) * 100
    )

    # Create synthetic Config B ISI score for placeholder (since we don't have real historical)
    # We'll use a combination of recovery and randomness just for the structure of the experiments
    np.random.seed(42)
    df["synthetic_isi_score"] = df.groupby("month").cumcount() % 100

    # Create overlay variants (Experiment A)
    df["overlay_v1"] = 0.95 * df["synthetic_isi_score"] + 0.05 * df["recovery_0_100"]
    df["overlay_v2"] = 0.90 * df["synthetic_isi_score"] + 0.10 * df["recovery_0_100"]
    df["overlay_v3"] = 0.85 * df["synthetic_isi_score"] + 0.15 * df["recovery_0_100"]
    df["overlay_v4"] = 0.80 * df["synthetic_isi_score"] + 0.20 * df["recovery_0_100"]

    # Create state engine (Experiment C)
    df["recovery_state"] = pd.cut(
        df["recovery_score_pctl"],
        bins=[-0.01, 40, 60, 80, 100.01],
        labels=["AVOID", "WATCH", "ACCUMULATE", "BUY"]
    )

    return df


def run_experiment_a(df):
    """Run Score Overlay variants and calculate performance metrics"""
    print("=== Experiment A — Score Overlay ===")

    # Calculate ranks per month
    df = df.sort_values(["month", "ticker"])

    for score_col in ["synthetic_isi_score", "overlay_v1", "overlay_v2", "overlay_v3", "overlay_v4"]:
        df[f"{score_col}_rank"] = df.groupby("month")[score_col].rank(ascending=False)

    results = []
    months = sorted(df["month"].unique())

    for score_col in ["synthetic_isi_score", "overlay_v1", "overlay_v2", "overlay_v3", "overlay_v4"]:
        portfolio_returns = []
        for month in months:
            month_df = df[df["month"] == month].sort_values(f"{score_col}_rank").head(5)
            avg_return = month_df["fwd_return_1m"].mean()
            portfolio_returns.append(avg_return)

        # Calculate performance metrics
        returns_series = pd.Series(portfolio_returns).dropna()
        cumulative = (1 + returns_series).prod()
        n_months = len(returns_series)
        cagr = (cumulative ** (12 / n_months)) - 1 if n_months > 0 else 0

        results.append({
            "score_name": score_col,
            "mean_monthly_return": returns_series.mean(),
            "cumulative_return": cumulative - 1,
            "cagr": cagr,
            "n_months": n_months
        })

    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_DIR / "experiment_a_results.csv", index=False)
    print("Saved Experiment A results to experiment_a_results.csv")
    return results_df


def run_experiment_b(df):
    """Run Rank Advancement Analysis"""
    print("\n=== Experiment B — Rank Advancement Analysis ===")

    # Calculate ranks
    df = df.sort_values(["month", "ticker"])
    df["isi_rank"] = df.groupby("month")["synthetic_isi_score"].rank(ascending=False)
    df["overlay_rank"] = df.groupby("month")["overlay_v2"].rank(ascending=False)

    # First top 5 appearance per ticker for both
    top5_isi = df[df["isi_rank"] <= 5].groupby("ticker")["month"].min().reset_index(name="isi_first_month")
    top5_overlay = df[df["overlay_rank"] <= 5].groupby("ticker")["month"].min().reset_index(name="overlay_first_month")

    # Merge
    rank_adv = pd.merge(top5_isi, top5_overlay, on="ticker", how="outer")
    rank_adv["isi_first_dt"] = pd.to_datetime(rank_adv["isi_first_month"] + "-01")
    rank_adv["overlay_first_dt"] = pd.to_datetime(rank_adv["overlay_first_month"] + "-01")
    rank_adv["lead_time_months"] = (
        (rank_adv["isi_first_dt"] - rank_adv["overlay_first_dt"]).dt.days / 30.44
    ).round(0)

    rank_adv.to_csv(OUTPUT_DIR / "experiment_b_results.csv", index=False)
    print("Saved Experiment B results to experiment_b_results.csv")
    return rank_adv


def run_experiment_c(df):
    """Run Recovery Confirmation Layer"""
    print("\n=== Experiment C — Recovery Confirmation Layer ===")
    state_perf = df.groupby("recovery_state").agg(
        fwd_return_1m_mean=("fwd_return_1m", "mean"),
        fwd_return_1m_median=("fwd_return_1m", "median"),
        fwd_return_3m_mean=("fwd_return_3m", "mean"),
        fwd_return_3m_median=("fwd_return_3m", "median"),
        fwd_return_6m_mean=("fwd_return_6m", "mean"),
        fwd_return_6m_median=("fwd_return_6m", "median"),
        count=("ticker", "count")
    ).reset_index()
    state_order = ["AVOID", "WATCH", "ACCUMULATE", "BUY"]
    state_perf = state_perf.set_index("recovery_state").loc[state_order].reset_index()
    state_perf.to_csv(OUTPUT_DIR / "experiment_c_results.csv", index=False)
    print("Saved Experiment C results to experiment_c_results.csv")
    return state_perf


def run_experiment_d(df):
    """Run BBCA Case Study"""
    print("\n=== Experiment D — BBCA Case Study ===")
    bbca = df[df["ticker"] == "BBCA.JK"].sort_values("Date").copy()
    bbca["isi_rank"] = bbca.groupby("month")["synthetic_isi_score"].rank(ascending=False)
    bbca["recovery_rank"] = bbca.groupby("month")["recovery_score_pctl"].rank(ascending=False)
    bbca["overlay_rank"] = bbca.groupby("month")["overlay_v2"].rank(ascending=False)
    bbca.to_csv(OUTPUT_DIR / "experiment_d_bbca.csv", index=False)
    print("Saved Experiment D results to experiment_d_bbca.csv")
    return bbca


def main():
    df = load_and_prepare_data()
    df = df[(df["Date"] >= "2023-01-01") & (df["Date"] <= "2025-12-31")]

    exp_a = run_experiment_a(df)
    exp_b = run_experiment_b(df)
    exp_c = run_experiment_c(df)
    exp_d = run_experiment_d(df)

    print("\n=== All experiments complete! ===")


if __name__ == "__main__":
    main()
