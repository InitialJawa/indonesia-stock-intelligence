"""
RESEARCH-012 Phase 1 — EXIT Validation (V2: Event-based)
=========================================================
Question: Do EXIT stocks actually underperform after the signal?
Method: Reconstruct historical EXIT signals, use FIRST event only
(no consecutive day overlap), measure 30/60/90D forward returns.
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
    print("Loading warehouse_daily_v4.parquet...")
    cols = [
        "Date", "ticker", "Close",
        "rs_20d", "rs_change_20d",
        "ma20", "ma50", "ma100", "above_ma100",
        "drawdown_252d",
    ]
    df = pd.read_parquet(DAILY_DATA_PATH, columns=cols)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["ticker", "Date"]).reset_index(drop=True)
    df = df[df["ticker"].isin(TICKERS_IDX30)].copy()
    print(f"  {len(df):,} records, {df['ticker'].nunique()} tickers")
    print(f"  {df['Date'].min().date()} to {df['Date'].max().date()}")
    return df


def load_warehouse_v3_ranks():
    print("Loading warehouse_v3 for Config B ranks...")
    df = pd.read_csv(WAREHOUSE_V3_PATH, usecols=["ticker", "month", "final_score"])
    df["month"] = pd.to_datetime(df["month"])
    df = df[df["ticker"].isin(TICKERS_IDX30)].copy()
    df["rank"] = df.groupby("month")["final_score"].rank(ascending=False, method="min").astype(int)
    print(f"  {len(df):,} records, {df['month'].nunique()} months, {df['ticker'].nunique()} tickers")
    return df[["month", "ticker", "rank"]]


def compute_exit_signals(daily_df, rank_df):
    print("\nComputing historical EXIT signals...")
    daily = daily_df.copy()
    daily["date_dt"] = daily["Date"].dt.normalize()

    # Merge monthly ranks (forward-fill)
    rank_df = rank_df.rename(columns={"month": "date_dt"})
    daily = daily.merge(rank_df, on=["ticker", "date_dt"], how="left")
    daily["rank"] = daily.groupby("ticker")["rank"].ffill()
    daily["rank"] = daily["rank"].fillna(99).astype(int)

    # Filter to 2022+ (when rank data exists)
    daily = daily[daily["date_dt"] >= "2022-01-01"].copy()

    # Classify each row
    def classify_row(row):
        close = row["Close"]
        rs_20d = row["rs_20d"]
        rs_change_20d = row["rs_change_20d"]
        ma50 = row["ma50"]
        ma100 = row["ma100"]
        rank = row["rank"]
        dd = row.get("drawdown_252d", np.nan)

        if pd.isna(close) or pd.isna(rs_20d):
            return pd.Series({"exit_state": "UNKNOWN", "state_code": -1})

        rule_a = rank > 10
        rule_b = (not pd.isna(rs_20d) and rs_20d < 0
                  and not pd.isna(rs_change_20d) and rs_change_20d < 0)
        rule_c = (not pd.isna(ma50) and close < ma50)
        rule_d1 = (not pd.isna(ma100) and close < ma100
                   and not pd.isna(rs_20d) and rs_20d < 0
                   and not pd.isna(rs_change_20d) and rs_change_20d < 0)
        rule_d2 = (not pd.isna(dd) and dd < -0.15)

        if rule_d1 or rule_d2:
            # Determine which D rule triggered
            if rule_d1 and rule_d2:
                triggers = "D1+D2"
                sc = 1
            elif rule_d1:
                triggers = "D1"
                sc = 1
            else:
                triggers = "D2"
                sc = 1
            state = "EXIT"
        elif rule_c:
            triggers = "C"
            sc = 2
            state = "EXIT RISK"
        elif rule_b:
            triggers = "B"
            sc = 3
            state = "WEAKENING"
        elif rule_a:
            triggers = "A"
            sc = 4
            state = "EXIT WATCH"
        else:
            triggers = ""
            sc = 5
            state = "HEALTHY"

        return pd.Series({"exit_state": state, "state_code": sc, "triggers": triggers})

    result = daily.join(daily.apply(classify_row, axis=1))
    result = result[result["exit_state"] != "UNKNOWN"]
    print(f"  {len(result):,} signals (2022+)")
    print(result["exit_state"].value_counts().to_string())
    return result


def find_first_events(signal_df):
    """
    For each ticker, identify the FIRST day it enters each state.
    This eliminates consecutive-day overlap.
    """
    print("\nFinding first-entry events per ticker...")
    df = signal_df.sort_values(["ticker", "date_dt"]).copy()

    # Mark when state changes (within each ticker)
    df["prev_state"] = df.groupby("ticker")["state_code"].shift(1)
    df["is_new_event"] = df["state_code"] != df["prev_state"]

    # For EXIT: first event is when state_code becomes 1 from a different state
    exit_entries = df[(df["exit_state"] == "EXIT") & (df["is_new_event"])].copy()

    # For Non-EXIT (HEALTHY): first event is when stock becomes healthy
    healthy_entries = df[(df["exit_state"] == "HEALTHY") & (df["is_new_event"])].copy()

    # Also collect all other state transitions
    weakening_entries = df[(df["exit_state"] == "WEAKENING") & (df["is_new_event"])].copy()
    exitrisk_entries = df[(df["exit_state"] == "EXIT RISK") & (df["is_new_event"])].copy()
    exitwatch_entries = df[(df["exit_state"] == "EXIT WATCH") & (df["is_new_event"])].copy()

    events = pd.concat([
        exit_entries, healthy_entries,
        weakening_entries, exitrisk_entries, exitwatch_entries
    ], ignore_index=True).sort_values(["ticker", "date_dt"])

    print(f"  EXIT first events:     {len(exit_entries):,}")
    print(f"  HEALTHY first events:  {len(healthy_entries):,}")
    print(f"  WEAKENING first events:{len(weakening_entries):,}")
    print(f"  EXIT RISK first events:{len(exitrisk_entries):,}")
    print(f"  EXIT WATCH first events:{len(exitwatch_entries):,}")
    print(f"  Total events: {len(events):,}")
    return events


def compute_forward_returns_events(events_df, daily_df):
    """Compute 30/60/90D forward returns from each event date."""
    print("\nComputing forward returns from events...")
    daily_pivot = daily_df.pivot_table(
        index="Date", columns="ticker", values="Close"
    ).sort_index()
    print(f"  Price matrix: {daily_pivot.shape[0]} days x {daily_pivot.shape[1]} tickers")

    # Filter to EXIT + HEALTHY for comparison
    events = events_df[events_df["exit_state"].isin(["EXIT", "HEALTHY"])].copy()
    events["exit_flag"] = (events["exit_state"] == "EXIT").astype(int)

    print(f"  EXIT events: {(events['exit_flag']==1).sum()}")
    print(f"  HEALTHY events: {(events['exit_flag']==0).sum()}")

    horizons = [(21, "30D"), (42, "60D"), (63, "90D")]
    all_fwd = []

    for horizon_days, label in horizons:
        records = []
        for idx, row in events.iterrows():
            ticker = row["ticker"]
            ev_date = row["date_dt"]
            if ticker not in daily_pivot.columns:
                continue
            ps = daily_pivot[ticker]
            try:
                loc = ps.index.get_loc(ev_date)
            except KeyError:
                continue
            px = ps.iloc[loc]
            if pd.isna(px) or px <= 0:
                continue
            tloc = loc + horizon_days
            if tloc >= len(ps):
                continue
            fpx = ps.iloc[tloc]
            if pd.isna(fpx) or fpx <= 0:
                continue
            records.append({
                "Date": ev_date,
                "ticker": ticker,
                "exit_state": row["exit_state"],
                "exit_flag": row["exit_flag"],
                "triggers": row.get("triggers", ""),
                "rank": row["rank"],
                "horizon": label,
                "fwd_return": (fpx / px) - 1,
            })
        fdf = pd.DataFrame(records)
        all_fwd.append(fdf)
        print(f"  {label}: {len(fdf):,} events")

    return pd.concat(all_fwd, ignore_index=True)


def analyze(fwd_df):
    print("=" * 80)
    print("PHASE 1 — EXIT VALIDATION (EVENT-BASED)")
    print("=" * 80)

    rows = []
    for horizon in ["30D", "60D", "90D"]:
        sub = fwd_df[fwd_df["horizon"] == horizon]
        exit_r = sub[sub["exit_flag"] == 1]["fwd_return"]
        healthy_r = sub[sub["exit_flag"] == 0]["fwd_return"]

        if len(exit_r) == 0 or len(healthy_r) == 0:
            continue

        from scipy import stats
        em, hm = exit_r.mean(), healthy_r.mean()
        e_med, h_med = exit_r.median(), healthy_r.median()
        e_wr, h_wr = (exit_r > 0).mean(), (healthy_r > 0).mean()
        excess = em - hm
        t, p = stats.ttest_ind(exit_r, healthy_r, equal_var=False)

        rows.append({
            "horizon": horizon,
            "exit_n": len(exit_r),
            "healthy_n": len(healthy_r),
            "exit_avg_return": f"{em*100:.2f}%",
            "healthy_avg_return": f"{hm*100:.2f}%",
            "exit_median_return": f"{e_med*100:.2f}%",
            "healthy_median_return": f"{h_med*100:.2f}%",
            "exit_win_rate": f"{e_wr*100:.1f}%",
            "healthy_win_rate": f"{h_wr*100:.1f}%",
            "excess_return": f"{excess*100:.2f}%",
            "p_value": f"{p:.6f}",
            "significant_5pct": "YES" if p < 0.05 else "NO",
        })

        print(f"\n  === {horizon} ===")
        print(f"  {'Metric':<35} {'EXIT':<15} {'HEALTHY':<15}")
        print(f"  {'-'*65}")
        print(f"  {'N':<35} {len(exit_r):<15} {len(healthy_r):<15}")
        print(f"  {'Average Return':<35} {em*100:<15.2f}% {hm*100:<15.2f}%")
        print(f"  {'Median Return':<35} {e_med*100:<15.2f}% {h_med*100:<15.2f}%")
        print(f"  {'Win Rate':<35} {e_wr*100:<15.1f}% {h_wr*100:<15.1f}%")
        print(f"  {'Excess (EXIT - Healthy)':<35} {excess*100:<+.2f}%")
        print(f"  {'p-value':<35} {p:.6f}")
        print(f"  {'Significant?':<35} {'YES' if p < 0.05 else 'NO'}")

    return pd.DataFrame(rows)


def analyze_by_trigger(fwd_df):
    """Break down EXIT by trigger rule (D1 vs D2 vs D1+D2)."""
    print("\n" + "=" * 80)
    print("EXIT BY TRIGGER SUBTYPE — 30D Returns")
    print("=" * 80)

    sub30 = fwd_df[fwd_df["horizon"] == "30D"].copy()
    exit_data = sub30[sub30["exit_flag"] == 1]
    healthy_30 = sub30[sub30["exit_flag"] == 0]["fwd_return"]

    if len(healthy_30) == 0:
        print("  No healthy data to compare")
        return

    from scipy import stats
    print(f"\n  {'Trigger':<15} {'N':<8} {'Avg':<10} {'Med':<10} {'Win%':<8} {'vsHealthy':<12} {'p-val':<10}")
    print(f"  {'-'*70}")
    for trigger in ["D1", "D2", "D1+D2"]:
        r = exit_data[exit_data["triggers"] == trigger]["fwd_return"]
        if len(r) == 0:
            continue
        em, hm = r.mean(), healthy_30.mean()
        excess_vs_h = em - hm
        t, p = stats.ttest_ind(r, healthy_30, equal_var=False)
        print(f"  {trigger:<15} {len(r):<8} {em*100:<10.2f}% {r.median()*100:<10.2f}% {(r>0).mean()*100:<8.1f}% {excess_vs_h*100:<+11.2f}% {p:<10.6f}")


def main():
    print("=" * 80)
    print("RESEARCH-012 Phase 1: EXIT Validation (Event-Based)")
    print("=" * 80)

    daily_df = load_daily_data()
    rank_df = load_warehouse_v3_ranks()

    signal_df = compute_exit_signals(daily_df, rank_df)
    events_df = find_first_events(signal_df)
    events_df.to_csv(OUTPUT_DIR / "research_012_phase1_events.csv", index=False)

    fwd_df = compute_forward_returns_events(events_df, daily_df)
    fwd_df.to_csv(OUTPUT_DIR / "research_012_phase1_event_forward_returns.csv", index=False)

    metrics = analyze(fwd_df)
    metrics.to_csv(OUTPUT_DIR / "research_012_phase1_event_metrics.csv", index=False)

    analyze_by_trigger(fwd_df)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for _, row in metrics.iterrows():
        excess = float(row["excess_return"].strip("%"))
        verdict = "CONFIRMED (underperforms)" if excess < 0 else "NOT CONFIRMED"
        print(f"  {row['horizon']}: excess={row['excess_return']}, {row['significant_5pct']} -> {verdict}")

    print("\nPhase 1 complete.")


if __name__ == "__main__":
    main()
