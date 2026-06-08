"""
RESEARCH-012 Phase 5 — Turnaround Promotion Test
==================================================
Question: When should Turnaround candidates replace weak holdings?

Method: For each month where a weak holding (EXIT or rank drop >10)
coexists with a Full Match Turnaround candidate not in portfolio,
compare: HOLD (keep weak stock) vs REPLACE (buy Turnaround).

Full Match = Context Match (drawdown<-25%, far from high<-20%,
high vol top 33.3%) AND Transition Match (rs_change_60d>0).

Outputs: Return Differential, Hit Rate, Alpha (1M/3M/6M forward).
Success: Turnaround replacement creates measurable improvement.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DAILY_PATH = PROJECT_ROOT / "database" / "historical" / "warehouse_daily_v4.parquet"
WH_PATH = PROJECT_ROOT / "warehouse_historical" / "warehouse_v3.csv"
MONTHLY_DIR = PROJECT_ROOT / "database" / "monthly"
IHSG_PATH = PROJECT_ROOT / "benchmarks" / "ihsg_monthly.csv"
OUTPUT_DIR = PROJECT_ROOT / "research" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    print("Loading data...")
    daily = pd.read_parquet(DAILY_PATH)
    daily["Date"] = pd.to_datetime(daily["Date"])
    daily = daily.sort_values(["ticker", "Date"])

    wh = pd.read_csv(WH_PATH)
    wh["month"] = pd.to_datetime(wh["month"])
    wh = wh.sort_values(["ticker", "month"])

    ihsg = pd.read_csv(IHSG_PATH)
    ihsg["Date"] = pd.to_datetime(ihsg["Date"])
    ihsg = ihsg.set_index("Date")["monthly_return"]

    prices = {}
    for fp in sorted(MONTHLY_DIR.glob("*.csv")):
        t = fp.stem
        df = pd.read_csv(fp)
        df["Date"] = pd.to_datetime(df["Date"])
        prices[t] = df.sort_values("Date")

    print(f"  Daily: {len(daily):,} | Warehouse: {len(wh):,} | IHSG: {len(ihsg)} | Prices: {len(prices)} tickers")
    return daily, wh, ihsg, prices


def compute_monthly_turnaround(daily_df, wh_df):
    """
    Compute Turnaround signals at monthly frequency.
    For each month, use the last day's data to determine turnaround status.
    """
    print("\nComputing monthly Turnaround signals...")

    # Get month-end snapshots from daily
    daily_df["month_end"] = daily_df["Date"] + pd.offsets.MonthEnd(0)
    month_ends = daily_df.groupby(["ticker", "month_end"]).last().reset_index()

    # Features needed for Turnaround
    ta_cols = ["ticker", "month_end", "drawdown_252d", "distance_from_high_252d",
               "volatility_60d", "rs_change_60d", "volume_ratio",
               "recovery_from_60d_low", "above_ma20"]

    # Filter to available columns
    avail = [c for c in ta_cols if c in month_ends.columns]
    ta = month_ends[avail].copy()

    # Compute high_volatility percentile per month_end
    ta["vol_pct"] = ta.groupby("month_end")["volatility_60d"].rank(pct=True)

    # Compute match flags
    ta["deep_drawdown"] = ta["drawdown_252d"] < -0.25
    ta["far_from_high"] = ta["distance_from_high_252d"] < -0.20
    ta["high_volatility"] = ta["vol_pct"] >= 0.667
    ta["context_match"] = ta["deep_drawdown"] & ta["far_from_high"] & ta["high_volatility"]
    ta["transition_match"] = ta["rs_change_60d"] > 0
    ta["full_match"] = ta["context_match"] & ta["transition_match"]
    ta["volume_high"] = ta["volume_ratio"] > 1.3
    ta["recovered"] = ta["recovery_from_60d_low"] > 0.10
    ta["confirmation_count"] = ta["volume_high"].astype(int) + ta["above_ma20"].astype(int) + ta["recovered"].astype(int)

    print(f"  Turnaround records: {len(ta):,}")
    print(f"  Full Match occurrences: {ta['full_match'].sum():,}")
    return ta


def compute_monthly_exit(daily_df, monthly_ranks):
    """
    Compute EXIT state at monthly frequency (month-end).
    """
    print("Computing monthly EXIT states...")
    daily_df["month_end"] = daily_df["Date"] + pd.offsets.MonthEnd(0)
    me = daily_df.groupby(["ticker", "month_end"]).last().reset_index()

    # Merge ranks — warehouse uses 1st of month, daily uses month-end
    r = monthly_ranks.copy()
    r["month_end"] = r["month"] + pd.offsets.MonthEnd(0)
    me = me.merge(r[["month_end", "ticker", "rank"]], on=["ticker", "month_end"], how="left")
    me["rank"] = me.groupby("ticker")["rank"].ffill().fillna(99).astype(int)

    # Compute exit state using renamed rank column
    def classify(row):
        close = row["Close"]
        rs20 = row["rs_20d"]
        rsc = row["rs_change_20d"]
        ma50 = row["ma50"]
        ma100 = row["ma100"]
        rnk = row["rank"]
        dd = row.get("drawdown_252d", np.nan)

        if pd.isna(close) or pd.isna(rs20):
            return "UNKNOWN"

        rule_a = rnk > 10
        rule_b = (not pd.isna(rs20) and rs20 < 0 and not pd.isna(rsc) and rsc < 0)
        rule_c = (not pd.isna(ma50) and close < ma50)
        rule_d1 = (not pd.isna(ma100) and close < ma100 and not pd.isna(rs20) and rs20 < 0 and not pd.isna(rsc) and rsc < 0)
        rule_d2 = (not pd.isna(dd) and dd < -0.15)

        if rule_d1 or rule_d2:
            return "EXIT"
        elif rule_c:
            return "EXIT RISK"
        elif rule_b:
            return "WEAKENING"
        elif rule_a:
            return "EXIT WATCH"
        else:
            return "HEALTHY"

    me["exit_state"] = me.apply(classify, axis=1)
    me = me[me["exit_state"] != "UNKNOWN"]
    print(f"  Exit states: {len(me):,}")
    return me


def load_monthly_ranks(wh_df):
    """Get Config B monthly ranks."""
    wh_df["rank"] = wh_df.groupby("month")["final_score"].rank(ascending=False, method="min").astype(int)
    return wh_df[["month", "ticker", "rank"]]


def simulate_replacement_strategy(ta_df, exit_df, monthly_prices):
    """
    Simulate a portfolio strategy that replaces weak holdings with
    Full Match Turnaround candidates.

    Methodology:
    - Each month, hold Top 5 Config B
    - If any holding is in EXIT state AND a Full Match Turnaround exists,
      replace the worst holding with the best Turnaround candidate.
    - Compare: keep holding vs replace with Turnaround
    """
    print("\nSimulating Turnaround replacement strategy...")

    # Build month-by-month analysis
    months = sorted(exit_df["month_end"].unique())
    events = []
    returns_map = {}
    for ticker, df in monthly_prices.items():
        for _, row in df.iterrows():
            returns_map[(ticker, row["Date"])] = row["monthly_return"]

    for month in months:
        # Current month's data
        exit_slice = exit_df[exit_df["month_end"] == month].copy()
        ta_slice = ta_df[ta_df["month_end"] == month].copy()

        # Rank tickers by Config B score
        ranked = exit_slice.sort_values("rank", ascending=True)
        top5 = ranked.head(5)

        # Find weak holdings (in EXIT state)
        weak = top5[top5["exit_state"] == "EXIT"]
        full_match = ta_slice[ta_slice["full_match"] == True]

        if len(weak) > 0 and len(full_match) > 0:
            # Get the worst weak holding (highest rank = lowest scoring)
            worst_weak = weak.sort_values("rank", ascending=False).iloc[0]
            # Get the best turnaround candidate not already held
            held = set(top5["ticker"])
            candidates = full_match[~full_match["ticker"].isin(held)]
            if len(candidates) > 0:
                # Pick the one with highest confirmation count
                best_ta = candidates.sort_values("confirmation_count", ascending=False).iloc[0]

                events.append({
                    "month": month,
                    "weak_ticker": worst_weak["ticker"],
                    "weak_rank": worst_weak["rank"],
                    "weak_exit_state": worst_weak["exit_state"],
                    "turnaround_ticker": best_ta["ticker"],
                    "ta_confirmation": best_ta["confirmation_count"],
                    "ta_context": best_ta["context_match"],
                    "ta_transition": best_ta["transition_match"],
                })

    events_df = pd.DataFrame(events)
    print(f"  Replacement events found: {len(events_df)}")
    return events_df


def event_returns(events_df, monthly_prices):
    """
    For each event, compare forward returns (1M, 3M, 6M) of:
      - HOLD: keep the weak stock
      - REPLACE: buy the Turnaround candidate
    """
    print("\n=== Event-Level: HOLD vs REPLACE ===")
    if len(events_df) == 0:
        print("  No events to analyze.")
        return pd.DataFrame()

    # Build return lookup
    ret_map = {}
    for ticker, df in monthly_prices.items():
        for _, row in df.iterrows():
            ret_map[(ticker, row["Date"])] = row["monthly_return"]

    def multi_ret(ticker, start_month, n):
        """Get cumulative return over n months."""
        td = monthly_prices.get(ticker)
        if td is None:
            return None
        dates = td["Date"].tolist()
        try:
            idx = dates.index(start_month)
        except ValueError:
            return None
        if idx + n >= len(dates):
            return None
        cum = 1.0
        for i in range(n):
            m = dates[idx + i]
            r = ret_map.get((ticker, m))
            if r is None or pd.isna(r):
                return None
            cum *= (1 + r)
        return cum - 1

    horizons = [1, 3, 6]
    comparisons = []

    for _, ev in events_df.iterrows():
        month = ev["month"]
        weak = ev["weak_ticker"]
        ta = ev["turnaround_ticker"]
        row_data = {"month": month, "weak": weak, "turnaround": ta}

        valid = True
        for h in horizons:
            hr = multi_ret(weak, month, h)
            tr = multi_ret(ta, month, h)
            if hr is None or tr is None:
                valid = False
                break
            row_data[f"hold_{h}m"] = hr
            row_data[f"replace_{h}m"] = tr
            row_data[f"diff_{h}m"] = tr - hr

        if valid:
            comparisons.append(row_data)

    comp_df = pd.DataFrame(comparisons)
    print(f"  Valid comparisons: {len(comp_df)} / {len(events_df)} events")

    print(f"\n  {'Horizon':<10} {'HOLD Avg':<12} {'REPLACE Avg':<12} {'Diff':<12} {'Repl Win%':<12}")
    print(f"  {'-'*58}")
    for h in horizons:
        hr = comp_df[f"hold_{h}m"]
        tr = comp_df[f"replace_{h}m"]
        diff = tr - hr
        wr = (diff > 0).mean()
        print(f"  {h}M{'':<8} {hr.mean()*100:<12.2f}% {tr.mean()*100:<12.2f}% "
              f"{diff.mean()*100:<+11.2f}% {wr*100:<11.1f}%")

    return comp_df


def main():
    print("=" * 80)
    print("RESEARCH-012 Phase 5: Turnaround Promotion Test")
    print("When should Turnaround candidates replace holdings?")
    print("=" * 80)

    daily, wh, ihsg, prices = load_data()
    monthly_ranks = load_monthly_ranks(wh)

    # Compute Turnaround signals
    ta_df = compute_monthly_turnaround(daily, wh)
    ta_df.to_csv(OUTPUT_DIR / "research_012_phase5_turnaround_signals.csv", index=False)

    # Compute EXIT states
    exit_df = compute_monthly_exit(daily, monthly_ranks)

    # Find replacement events
    events_df = simulate_replacement_strategy(ta_df, exit_df, prices)
    events_df.to_csv(OUTPUT_DIR / "research_012_phase5_events.csv", index=False)

    # Event-level comparison
    comp_df = event_returns(events_df, prices)
    if len(comp_df) > 0:
        comp_df.to_csv(OUTPUT_DIR / "research_012_phase5_comparison.csv", index=False)

    # Summary
    print("\n" + "=" * 80)
    print("PHASE 5 RESULTS SUMMARY")
    print("=" * 80)

    if len(comp_df) > 0:
        print(f"\n  Event-Level Results:")
        for h in [1, 3, 6]:
            hr = comp_df[f"hold_{h}m"]
            tr = comp_df[f"replace_{h}m"]
            diff = tr - hr
            wr = (diff > 0).mean()
            avg_diff = diff.mean()
            print(f"    {h}M: Diff={avg_diff*100:+.2f}%  WinRate={wr*100:.1f}%  "
                  f"HOLD={hr.mean()*100:+.2f}%  REPLACE={tr.mean()*100:+.2f}%")

        # Overall assessment
        avg_diff_all = np.mean([comp_df[f"diff_{h}m"].mean() for h in [1, 3, 6]])
        wr_all = np.mean([(comp_df[f"diff_{h}m"] > 0).mean() for h in [1, 3, 6]])
        cagr_like = ((1 + comp_df["diff_6m"]).prod() ** (12 / (6 * len(comp_df))) - 1) * 100 if len(comp_df) > 0 else 0

        print(f"\n  Overall:")
        print(f"    Avg Diff across horizons: {avg_diff_all*100:+.2f}%")
        print(f"    Avg Win Rate across horizons: {wr_all*100:.1f}%")

        verdict = avg_diff_all > 0 and wr_all > 0.50
        print(f"\n  Success Criteria: Turnaround replacement creates measurable improvement.")
        print(f"  Verdict: {'PASSED' if verdict else 'NOT PASSED'}")
    else:
        print("\n  No valid events found for comparison.")

    print("\nPhase 5 complete.")


if __name__ == "__main__":
    main()
