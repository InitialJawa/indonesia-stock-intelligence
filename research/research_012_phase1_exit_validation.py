"""
RESEARCH-012 Phase 1 — EXIT Validation
=======================================
Question: Do EXIT stocks actually underperform after the signal?
Method: Reconstruct historical EXIT signals from daily warehouse,
measure forward returns (30/60/90D), compare EXIT vs Non-EXIT.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DAILY_DATA_PATH = PROJECT_ROOT / "database" / "historical" / "warehouse_daily_v4.parquet"
WAREHOUSE_V3_PATH = PROJECT_ROOT / "warehouse_historical" / "warehouse_v3.csv"
OUTPUT_DIR = PROJECT_ROOT / "research" / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TICKERS_IDX30 = [
    'ADRO.JK', 'AKRA.JK', 'AMMN.JK', 'ANTM.JK', 'ASII.JK',
    'BBCA.JK', 'BBNI.JK', 'BBRI.JK', 'BMRI.JK', 'BRPT.JK',
    'CPIN.JK', 'ESSA.JK', 'EXCL.JK', 'GOTO.JK', 'HEAL.JK',
    'ICBP.JK', 'INDF.JK', 'INTP.JK', 'ITMG.JK', 'KLBF.JK',
    'MAPI.JK', 'MDKA.JK', 'MIKA.JK', 'PGAS.JK', 'PTBA.JK',
    'SIDO.JK', 'SMGR.JK', 'TLKM.JK', 'TPIA.JK', 'UNTR.JK',
]


def load_daily_data():
    """Load warehouse_daily_v4.parquet with essential columns."""
    print("Loading warehouse_daily_v4.parquet...")
    cols = [
        "Date", "ticker", "Close",
        "rs_20d", "rs_change_20d",
        "ma20", "ma50", "ma100",
        "drawdown_252d",
    ]
    df = pd.read_parquet(DAILY_DATA_PATH, columns=cols)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["ticker", "Date"]).reset_index(drop=True)
    # Filter to IDX30 tickers only
    df = df[df["ticker"].isin(TICKERS_IDX30)].copy()
    print(f"  Loaded {len(df):,} records ({df['ticker'].nunique()} tickers)")
    print(f"  Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
    return df


def load_warehouse_v3_ranks():
    """
    Load warehouse_v3.csv and compute Config B rank for each ticker each month.
    Config B = final_score (Q25/G30/V10/M35).
    """
    print("Loading warehouse_v3 for Config B ranks...")
    df = pd.read_csv(WAREHOUSE_V3_PATH, usecols=["ticker", "month", "final_score"])
    df["month"] = pd.to_datetime(df["month"])
    df = df[df["ticker"].isin(TICKERS_IDX30)].copy()

    # Compute rank per month (highest final_score = rank 1)
    df["rank"] = df.groupby("month")["final_score"].rank(ascending=False, method="min").astype(int)
    print(f"  Loaded {len(df):,} records, {df['month'].nunique()} months")
    print(f"  Tickers with rank data: {df['ticker'].nunique()}")
    return df[["month", "ticker", "rank"]]


def compute_exit_signals(daily_df, rank_df):
    """
    Reconstruct historical EXIT signals for every day x ticker.
    Uses daily data for technical rules (B/C/D) and monthly rank for Rule A.
    """
    print("\nComputing historical EXIT signals...")

    daily = daily_df.copy()
    daily["date_dt"] = daily["Date"].dt.normalize()

    # Merge monthly ranks: for each day, use the most recent month's rank
    rank_df = rank_df.copy()
    rank_df = rank_df.rename(columns={"month": "date_dt"})
    rank_df["date_dt"] = pd.to_datetime(rank_df["date_dt"])

    # Merge monthly ranks: forward-fill to daily
    # For each ticker, merge rank on exact date match then forward-fill
    daily = daily.merge(rank_df, on=["ticker", "date_dt"], how="left")
    daily["rank"] = daily.groupby("ticker")["rank"].ffill()
    daily["rank"] = daily["rank"].fillna(99).astype(int)

    # Only analyze from 2022-01-01 onwards (when rank data is available)
    before = len(daily)
    daily = daily[daily["date_dt"] >= "2022-01-01"].copy()
    print(f"  Filtered to 2022+: {len(daily):,} (dropped {before - len(daily):,} pre-2022 records)")

    # Apply Exit Rules row-wise
    def classify_row(row):
        close = row["Close"]
        rs_20d = row["rs_20d"]
        rs_change_20d = row["rs_change_20d"]
        ma50 = row["ma50"]
        ma100 = row["ma100"]
        rank = row["rank"]
        drawdown_252d = row.get("drawdown_252d", np.nan)

        if pd.isna(close) or pd.isna(rs_20d):
            return pd.Series({"exit_state": "UNKNOWN", "triggered_rules": "NONE"})

        rule_a = rank > 10
        rule_b = (not pd.isna(rs_20d) and rs_20d < 0
                  and not pd.isna(rs_change_20d) and rs_change_20d < 0)
        rule_c = (not pd.isna(ma50) and close < ma50)

        # D1: Close < MA100 AND RS20 < 0 AND RS_CHANGE_20D < 0
        rule_d1 = (not pd.isna(ma100) and close < ma100
                   and not pd.isna(rs_20d) and rs_20d < 0
                   and not pd.isna(rs_change_20d) and rs_change_20d < 0)
        # D2: Drawdown > 15% (using 252d drawdown as proxy for entry drawdown)
        rule_d2 = (not pd.isna(drawdown_252d) and drawdown_252d < -0.15)

        rule_d = rule_d1 or rule_d2
        triggered = []
        if rule_d:
            state = "EXIT"
            if rule_d1: triggered.append("D1")
            if rule_d2: triggered.append("D2")
        elif rule_c:
            state = "EXIT RISK"
            triggered = ["C"]
        elif rule_b:
            state = "WEAKENING"
            triggered = ["B"]
        elif rule_a:
            state = "EXIT WATCH"
            triggered = ["A"]
        else:
            state = "HEALTHY"
            triggered = []

        return pd.Series({
            "exit_state": state,
            "triggered_rules": "+".join(triggered) if triggered else "NONE"
        })

    result = daily.join(daily.apply(classify_row, axis=1))

    print(f"  Signals computed: {len(result):,}")
    print("  State distribution:")
    print(result["exit_state"].value_counts().to_string())
    return result


def compute_forward_returns(signal_df, daily_df):
    """
    For each EXIT / non-EXIT day, measure 30/60/90 trading day forward returns.
    """
    print("\nComputing forward returns...")

    # Build price lookup: for each ticker, date -> close price
    daily_pivot = daily_df.pivot_table(
        index="Date", columns="ticker", values="Close"
    ).sort_index()
    print(f"  Price matrix: {daily_pivot.shape[0]} days x {daily_pivot.shape[1]} tickers")

    # Prepare signals for evaluation
    signals = signal_df[signal_df["exit_state"] != "UNKNOWN"].copy()
    signals["exit_flag"] = (signals["exit_state"] == "EXIT").astype(int)

    exit_count = signals["exit_flag"].sum()
    non_exit_count = len(signals) - exit_count
    print(f"  EXIT days: {exit_count:,}")
    print(f"  Non-EXIT days: {non_exit_count:,}")

    # Sample non-EXIT for balance (3:1 ratio)
    exit_signals = signals[signals["exit_flag"] == 1].copy()
    non_exit_signals = signals[signals["exit_flag"] == 0].copy()

    sample_size = min(len(non_exit_signals), len(exit_signals) * 3)
    non_exit_sample = non_exit_signals.sample(n=sample_size, random_state=42)
    combined = pd.concat([exit_signals, non_exit_sample], ignore_index=True)
    print(f"  Evaluation set: {len(combined):,} (EXIT={len(exit_signals):,}, Non-EXIT={sample_size:,})")

    horizons = [(21, "30D"), (42, "60D"), (63, "90D")]
    all_forward = []

    for horizon_days, label in horizons:
        count_valid = 0
        records = []
        for idx, row in combined.iterrows():
            ticker = row["ticker"]
            signal_date = row["date_dt"].normalize()

            if ticker not in daily_pivot.columns:
                continue

            price_series = daily_pivot[ticker]
            # Find the closest date in price series (should be exact)
            try:
                loc = price_series.index.get_loc(signal_date)
            except KeyError:
                continue

            signal_price = price_series.iloc[loc]
            if pd.isna(signal_price) or signal_price <= 0:
                continue

            # Look up forward price
            target_loc = loc + horizon_days
            if target_loc >= len(price_series):
                continue

            forward_price = price_series.iloc[target_loc]
            if pd.isna(forward_price) or forward_price <= 0:
                continue

            fwd_return = (forward_price / signal_price) - 1
            records.append({
                "Date": signal_date,
                "ticker": ticker,
                "exit_state": row["exit_state"],
                "exit_flag": row["exit_flag"],
                "rank": row["rank"],
                "triggered_rules": row["triggered_rules"],
                "horizon": label,
                "fwd_return": fwd_return,
            })
            count_valid += 1

        fwd_df = pd.DataFrame(records)
        all_forward.append(fwd_df)
        print(f"  {label}: {count_valid:,} valid forward return pairs")

    return pd.concat(all_forward, ignore_index=True)


def analyze_results(fwd_df):
    """Compute comparison metrics and statistical tests."""
    print("\n" + "=" * 80)
    print("PHASE 1 — EXIT VALIDATION RESULTS")
    print("=" * 80)

    rows = []
    for horizon in ["30D", "60D", "90D"]:
        subset = fwd_df[fwd_df["horizon"] == horizon]
        exit_r = subset[subset["exit_flag"] == 1]["fwd_return"]
        non_r = subset[subset["exit_flag"] == 0]["fwd_return"]

        if len(exit_r) == 0 or len(non_r) == 0:
            print(f"\n  {horizon}: Insufficient data")
            continue

        exit_mean = exit_r.mean()
        non_mean = non_r.mean()
        exit_med = exit_r.median()
        non_med = non_r.median()
        exit_wr = (exit_r > 0).mean()
        non_wr = (non_r > 0).mean()
        excess = exit_mean - non_mean

        # Welch t-test
        from scipy import stats
        t_stat, p_val = stats.ttest_ind(exit_r, non_r, equal_var=False)

        rows.append({
            "horizon": horizon,
            "exit_n": len(exit_r),
            "non_exit_n": len(non_r),
            "exit_avg_return": f"{exit_mean*100:.2f}%",
            "non_exit_avg_return": f"{non_mean*100:.2f}%",
            "exit_median_return": f"{exit_med*100:.2f}%",
            "non_exit_median_return": f"{non_med*100:.2f}%",
            "exit_win_rate": f"{exit_wr*100:.1f}%",
            "non_exit_win_rate": f"{non_wr*100:.1f}%",
            "excess_return": f"{excess*100:.2f}%",
            "excess_return_bp": f"{excess*10000:.0f}",
            "t_stat": f"{t_stat:.4f}",
            "p_value": f"{p_val:.6f}",
            "significant_5pct": "YES" if p_val < 0.05 else "NO",
        })

        print(f"\n  === {horizon} Forward Returns ===")
        print(f"  {'Metric':<35} {'EXIT':<15} {'Non-EXIT':<15}")
        print(f"  {'-'*65}")
        print(f"  {'N':<35} {len(exit_r):<15} {len(non_r):<15}")
        print(f"  {'Average Return':<35} {exit_mean*100:<15.2f}% {non_mean*100:<15.2f}%")
        print(f"  {'Median Return':<35} {exit_med*100:<15.2f}% {non_med*100:<15.2f}%")
        print(f"  {'Win Rate':<35} {exit_wr*100:<15.1f}% {non_wr*100:<15.1f}%")
        print(f"  {'Excess Return (EXIT - Non-EXIT)':<35} {excess*100:<+.2f}%")
        print(f"  {'p-value (Welch t-test)':<35} {p_val:.6f}")
        print(f"  {'Significant at 5%?':<35} {'YES' if p_val < 0.05 else 'NO'}")

    result_df = pd.DataFrame(rows)
    return result_df


def main():
    print("=" * 80)
    print("RESEARCH-012 Phase 1: EXIT Validation")
    print("Do EXIT stocks actually underperform after the signal?")
    print("=" * 80)

    # Step 1: Load data
    daily_df = load_daily_data()
    rank_df = load_warehouse_v3_ranks()

    # Step 2: Reconstruct EXIT signals
    signal_df = compute_exit_signals(daily_df, rank_df)
    signal_out = OUTPUT_DIR / "research_012_phase1_signals.csv"
    signal_df.to_csv(signal_out, index=False)
    print(f"\n  Signals saved: {signal_out}")

    # Step 3: Compute forward returns
    fwd_df = compute_forward_returns(signal_df, daily_df)
    fwd_out = OUTPUT_DIR / "research_012_phase1_forward_returns.csv"
    fwd_df.to_csv(fwd_out, index=False)
    print(f"  Forward returns saved: {fwd_out}")

    # Step 4: Analyze
    metrics = analyze_results(fwd_df)
    metrics_out = OUTPUT_DIR / "research_012_phase1_metrics.csv"
    metrics.to_csv(metrics_out, index=False)
    print(f"\n  Metrics saved: {metrics_out}")

    # Step 5: Summary
    print("\n" + "=" * 80)
    print("SUMMARY — Success Criteria Assessment")
    print("=" * 80)
    for _, row in metrics.iterrows():
        excess = float(row["excess_return"].strip("%"))
        sig = row["significant_5pct"]
        verdict = "CONFIRMED (underperforms)" if excess < 0 else "NOT CONFIRMED"
        print(f"  {row['horizon']}: excess={row['excess_return']}, {sig}, -> {verdict}")

    print("\nPhase 1 complete.")


if __name__ == "__main__":
    main()
