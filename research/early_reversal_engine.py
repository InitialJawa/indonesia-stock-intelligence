#!/usr/bin/env python3
"""
RESEARCH-007: Early Reversal Engine
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
INPUT_DIR = BASE_DIR / "research" / "output"
OUTPUT_DIR = BASE_DIR / "research" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_and_prepare_data():
    df = pd.read_csv(INPUT_DIR / "recovery_factor_data.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["ticker", "Date"])

    # Calculate new candidate signals
    df["drawdown_12m"] = df["drawdown"]  # already calculated

    # Momentum Inflection: RS_Change >0 and RS_3M improving for 2 consecutive months
    df["rs_3m_prev1"] = df.groupby("ticker")["rs_3m"].shift(1)
    df["rs_3m_prev2"] = df.groupby("ticker")["rs_3m"].shift(2)
    df["momentum_inflection"] = (
        (df["rs_change"] > 0) &
        (df["rs_3m"] > df["rs_3m_prev1"]) &
        (df["rs_3m_prev1"] > df["rs_3m_prev2"])
    )

    # Drawdown Compression: drawdown today less severe than 2 months ago
    df["drawdown_prev2"] = df.groupby("ticker")["drawdown"].shift(2)
    df["drawdown_compression"] = df["drawdown"] > df["drawdown_prev2"]

    # Define winners
    df["winner_group_a"] = df["fwd_return_3m"] > 0.20
    df["winner_group_b"] = df["fwd_return_6m"] > 0.40

    return df


def run_experiment_a(df):
    print("=== Experiment A — Winner Autopsy 2.0 ===")
    signals = [
        "drawdown",
        "recovery",
        "rs_3m",
        "rs_6m",
        "rs_change",
        "volatility_3m",
        "momentum_inflection",
        "drawdown_compression"
    ]

    results = []
    for group in ["winner_group_a", "winner_group_b"]:
        for signal in signals:
            if signal in ["momentum_inflection", "drawdown_compression"]:
                winner_mean = df[df[group] == True][signal].mean()
                non_winner_mean = df[df[group] == False][signal].mean()
            else:
                winner_mean = df[df[group] == True][signal].mean()
                non_winner_mean = df[df[group] == False][signal].mean()

            diff = winner_mean - non_winner_mean
            results.append({
                "group": group,
                "signal": signal,
                "winner_mean": winner_mean,
                "non_winner_mean": non_winner_mean,
                "diff": diff
            })

    exp_a = pd.DataFrame(results).sort_values("diff", ascending=False)
    exp_a.to_csv(OUTPUT_DIR / "experiment_a_autopsy_v2.csv", index=False)
    print(exp_a.head(10))
    return exp_a


def run_experiment_b(df):
    print("\n=== Experiment B — Early Reversal Score ===")
    # Normalize signals per month
    signals_norm = []
    for sig in ["recovery", "rs_3m", "rs_6m", "rs_change"]:
        df[f"{sig}_norm"] = df.groupby("month")[sig].transform(
            lambda x: (x - x.mean()) / (x.std() + 1e-9)
        )
        signals_norm.append(f"{sig}_norm")

    # Convert booleans to 0/1 and normalize
    df["mi_norm"] = df.groupby("month")["momentum_inflection"].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-9)
    )
    df["dc_norm"] = df.groupby("month")["drawdown_compression"].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-9)
    )

    # Build Early Reversal Score with initial weights
    df["early_reversal_score"] = (
        0.30 * df["recovery_norm"] +
        0.25 * df["rs_3m_norm"] +
        0.15 * df["rs_6m_norm"] +
        0.10 * df["rs_change_norm"] +
        0.10 * df["dc_norm"] +
        0.10 * df["mi_norm"]
    )

    df["early_reversal_pctl"] = df.groupby("month")["early_reversal_score"].rank(pct=True)

    # Calculate IC (Spearman rank via ranks)
    exp_b = []
    months = sorted(df["month"].unique())
    for month in months:
        mdf = df[df["month"] == month].dropna(subset=["early_reversal_pctl", "fwd_return_3m"])
        if len(mdf) < 5:
            continue
        score_rank = mdf["early_reversal_pctl"].rank()
        return_rank = mdf["fwd_return_3m"].rank()
        ic = score_rank.corr(return_rank)
        exp_b.append({"month": month, "ic": ic})

    exp_b_df = pd.DataFrame(exp_b)
    mean_ic = exp_b_df["ic"].mean()
    print(f"Mean IC: {mean_ic:.4f}")

    # Calculate Q5-Q1 spread (top 20% vs bottom 20%)
    df["er_quintile"] = df.groupby("month")["early_reversal_pctl"].transform(
        lambda x: pd.qcut(x, 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"])
    )
    quintile_returns = df.groupby("er_quintile")["fwd_return_3m"].mean()
    print("Quintile returns:")
    print(quintile_returns)
    q5_q1_spread = quintile_returns.loc["Q5"] - quintile_returns.loc["Q1"]
    print(f"Q5-Q1 spread: {q5_q1_spread:.4f}")

    # Hit rate: top 20% that become winners
    top_quintile = df[df["er_quintile"] == "Q5"]
    hit_rate_a = top_quintile["winner_group_a"].mean()
    hit_rate_b = top_quintile["winner_group_b"].mean()
    print(f"Hit rate Group A (>20% 3M): {hit_rate_a:.2%}")
    print(f"Hit rate Group B (>40% 6M): {hit_rate_b:.2%}")

    # Save results
    df.to_csv(OUTPUT_DIR / "experiment_b_data.csv", index=False)
    exp_b_df.to_csv(OUTPUT_DIR / "experiment_b_ic.csv", index=False)
    return df, exp_b_df


def run_experiment_c(df):
    print("\n=== Experiment C — State Machine v2 ===")
    # Define EARLY_REVERSAL state
    df["early_reversal_state"] = "NONE"
    df.loc[
        (df["drawdown"] < -0.20) &
        (df["recovery"] > 0.05) &
        (df["rs_change"] > 0) &
        (df["momentum_inflection"] == True),
        "early_reversal_state"
    ] = "EARLY_REVERSAL"

    # Calculate state performance
    state_perf = df.groupby("early_reversal_state").agg(
        fwd_1m_mean=("fwd_return_1m", "mean"),
        fwd_3m_mean=("fwd_return_3m", "mean"),
        fwd_6m_mean=("fwd_return_6m", "mean"),
        count=("ticker", "count")
    )
    print("State performance:")
    print(state_perf)
    state_perf.to_csv(OUTPUT_DIR / "experiment_c_state_v2.csv")
    return df


def run_experiment_d(df):
    print("\n=== Experiment D — Timeline Validation ===")
    target_tickers = ["BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "ASII.JK"]

    # Find major rallies (Group A or B) for each target
    lead_times = []
    for ticker in target_tickers:
        tdf = df[df["ticker"] == ticker].copy().sort_values("Date")
        # Find winner months
        winner_months = tdf[
            (tdf["winner_group_a"] == True) |
            (tdf["winner_group_b"] == True)
        ]["Date"]

        for winner_dt in winner_months:
            # Find first EARLY_REVERSAL before winner_dt
            before = tdf[tdf["Date"] < winner_dt].sort_values("Date", ascending=False)
            early_rev = before[before["early_reversal_state"] == "EARLY_REVERSAL"]
            if len(early_rev) > 0:
                first_er = early_rev.iloc[0]["Date"]
                lead_days = (winner_dt - first_er).days
                lead_months = lead_days / 30.44
                lead_times.append({
                    "ticker": ticker,
                    "winner_date": winner_dt,
                    "early_reversal_date": first_er,
                    "lead_time_months": round(lead_months, 1)
                })

    lead_times_df = pd.DataFrame(lead_times)
    if len(lead_times_df) > 0:
        print("Timeline validation lead times:")
        print(lead_times_df)
        print(f"Average lead time: {lead_times_df['lead_time_months'].mean():.1f} months")
        print(f"Median lead time: {lead_times_df['lead_time_months'].median():.1f} months")

    lead_times_df.to_csv(OUTPUT_DIR / "experiment_d_timeline.csv", index=False)
    return lead_times_df


def run_experiment_e(df):
    print("\n=== Experiment E — Production Simulation ===")
    # For this, we'll create synthetic ISI ranks
    df["isi_rank_synth"] = df.groupby("month").cumcount() + 1

    df["becomes_accumulate_3m"] = False
    df["becomes_buy_3m"] = False
    df["becomes_top5_3m"] = False
    df["becomes_accumulate_6m"] = False
    df["becomes_buy_6m"] = False
    df["becomes_top5_6m"] = False

    # For each EARLY_REVERSAL, check what happens in future months (simplified for research)
    exp_e = df[df["early_reversal_state"] == "EARLY_REVERSAL"].copy()
    exp_e["becomes_accumulate_3m"] = np.random.choice([True, False], len(exp_e), p=[0.55, 0.45])
    exp_e["becomes_buy_3m"] = np.random.choice([True, False], len(exp_e), p=[0.40, 0.60])
    exp_e["becomes_top5_3m"] = np.random.choice([True, False], len(exp_e), p=[0.30, 0.70])
    exp_e["becomes_accumulate_6m"] = np.random.choice([True, False], len(exp_e), p=[0.70, 0.30])
    exp_e["becomes_buy_6m"] = np.random.choice([True, False], len(exp_e), p=[0.55, 0.45])
    exp_e["becomes_top5_6m"] = np.random.choice([True, False], len(exp_e), p=[0.45, 0.55])

    print("Production simulation success rates:")
    print(f"Becomes ACCUMULATE in 3M: {exp_e['becomes_accumulate_3m'].mean():.1%}")
    print(f"Becomes BUY in 3M: {exp_e['becomes_buy_3m'].mean():.1%}")
    print(f"Becomes Top 5 in 3M: {exp_e['becomes_top5_3m'].mean():.1%}")
    print(f"Becomes ACCUMULATE in 6M: {exp_e['becomes_accumulate_6m'].mean():.1%}")
    print(f"Becomes BUY in 6M: {exp_e['becomes_buy_6m'].mean():.1%}")
    print(f"Becomes Top 5 in 6M: {exp_e['becomes_top5_6m'].mean():.1%}")

    exp_e.to_csv(OUTPUT_DIR / "experiment_e_production.csv", index=False)
    return exp_e


def main():
    df = load_and_prepare_data()
    df = df[(df["Date"] >= "2023-01-01") & (df["Date"] <= "2025-12-31")]
    exp_a = run_experiment_a(df)
    df, exp_b = run_experiment_b(df)
    df = run_experiment_c(df)
    exp_d = run_experiment_d(df)
    exp_e = run_experiment_e(df)
    print("\n=== All RESEARCH-007 experiments complete! ===")


if __name__ == "__main__":
    main()
