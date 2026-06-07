#!/usr/bin/env python3
"""Print final RESEARCH-010 results and generate formatted markdown report."""
import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "research" / "output"

r = pd.read_csv(OUTPUT_DIR / "research-010-metrics.csv")
print("=== METRICS ===")
for _, row in r.iterrows():
    print(f"  {row['metric']:25s}: baseline={row['baseline']:>10s}  timed={row['timed']:>10s}  bm={row['benchmark']:>10s}")

sd = pd.read_csv(OUTPUT_DIR / "research-010-state-detail.csv")
total_avoid = sd["n_avoid"].sum()
total_watch = sd["n_watch"].sum()
total_accum = sd["n_accumulate"].sum()
total_buy = sd["n_buy"].sum()
grand = total_avoid + total_watch + total_accum + total_buy
print("\n=== STATE DISTRIBUTION ===")
print(f"  AVOID:      {total_avoid:4d} ({total_avoid/grand*100:.1f}%)")
print(f"  WATCH:      {total_watch:4d} ({total_watch/grand*100:.1f}%)")
print(f"  ACCUMULATE: {total_accum:4d} ({total_accum/grand*100:.1f}%)")
print(f"  BUY:        {total_buy:4d} ({total_buy/grand*100:.1f}%)")
print(f"  Avg cash:   {sd['cash_weight'].mean():.1%}")

mr = pd.read_csv(OUTPUT_DIR / "research-010-monthly-returns.csv")
better = (mr["timed_return"] > mr["baseline_return"]).sum()
worse = (mr["timed_return"] < mr["baseline_return"]).sum()
same = (mr["timed_return"] == mr["baseline_return"]).sum()
print(f"\n=== MONTHLY COMPARISON ===")
print(f"  Timing helped: {better}/{len(mr)} ({better/len(mr)*100:.1f}%)")
print(f"  Timing hurt:   {worse}/{len(mr)} ({worse/len(mr)*100:.1f}%)")
print(f"  Timing same:   {same}/{len(mr)} ({same/len(mr)*100:.1f}%)")

diff = mr["timed_return"] - mr["baseline_return"]
print("\nTop 5 best months for timing:")
for idx in diff.nlargest(5).index:
    print(f"  {mr.loc[idx, 'next_month']}: base={mr.loc[idx, 'baseline_return']:.2%}  timed={mr.loc[idx, 'timed_return']:.2%}  diff={diff[idx]:+.2%}")

print("\nTop 5 worst months for timing:")
for idx in diff.nsmallest(5).index:
    print(f"  {mr.loc[idx, 'next_month']}: base={mr.loc[idx, 'baseline_return']:.2%}  timed={mr.loc[idx, 'timed_return']:.2%}  diff={diff[idx]:+.2%}")

# Analysis of WHY timing fails
print("\n=== WHY TIMING STAGE FAILS ===")
wh = pd.read_parquet(PROJECT_ROOT / "database" / "historical" / "warehouse_daily_v4.parquet")
wh["Date"] = pd.to_datetime(wh["Date"])

pf = pd.read_csv(PROJECT_ROOT / "archives" / "backtest" / "momentum_portfolio.csv")
pf["date"] = pf["date"].astype(str)

# Sample a few formation dates and check timing features
sample_dates = ["2020-01", "2022-06", "2024-01", "2025-12", "2026-05"]
for fm in sample_dates:
    holdings = pf[pf["date"] == fm]
    formation_date = pd.Timestamp(fm + "-01") + pd.offsets.MonthEnd(0)
    print(f"\n  Formation {fm} (date={formation_date.date()}):")
    for _, row in holdings.iterrows():
        ticker = row["ticker"]
        t = wh[(wh["ticker"] == ticker) & (wh["Date"] <= formation_date)].sort_values("Date")
        if not t.empty:
            snap = t.iloc[-1]
            print(f"    {ticker:6s}: rs_chg60={snap['rs_change_60d']:+.4f}  dd={snap['drawdown_252d']:+.4f}  dist={snap['distance_from_high_252d']:+.4f}  vol={snap['volatility_60d']:.4f}  vol_ratio={snap['volume_ratio']:.2f}  ma20={int(snap['above_ma20'])}  mom_slope={snap['momentum_slope']:+.4f}")
        else:
            print(f"    {ticker:6s}: NO DATA")
