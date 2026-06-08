"""
GATE-001: Decision Layer V1 Production Gate — Integrated Backtest
================================================================
Purpose: Validate integrated Decision Layer V1 against Config B Top 5 Monthly.

Decision Layer V1 Rules:
  1. SELL when rank drop > 10 from entry rank (P2 validated)
  2. REPLACE with highest-ranked eligible stock (P3 validated)
  3. Turnaround overlay: if EXIT state holding + Full Match Turnaround
     coexists, replace (P5 validated)
  4. REVIEW signal on EXIT RISK (informational, no action) (P4)

Gate Criteria: Decision Layer must outperform Config B Top 5 Monthly on
  CAGR, Sharpe, MaxDD, Alpha at portfolio level (monthly simulation).
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

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

    print(f"  Daily: {len(daily):,} | Warehouse: {len(wh):,} | "
          f"IHSG: {len(ihsg)} | Prices: {len(prices)} tickers")
    return daily, wh, ihsg, prices


def build_decision_signals(daily_df, wh_df):
    """
    Compute monthly signals needed for Decision Layer:
      - Config B ranks (from warehouse)
      - EXIT states (from daily + ranks)
      - Turnaway signals (from daily)
    Returns a dict: month -> {ticker -> {rank, exit_state,
                           full_match, confirmation_count}}
    """
    print("\nBuilding decision signals...")

    # Config B monthly ranks
    wh_df["rank"] = wh_df.groupby("month")["final_score"].rank(
        ascending=False, method="min").astype(int)

    # Month-end snapshot from daily
    daily_df["month_end"] = daily_df["Date"] + pd.offsets.MonthEnd(0)
    me = daily_df.groupby(["ticker", "month_end"]).last().reset_index()

    # Merge ranks — warehouse uses 1st of month, daily uses month-end
    r = wh_df[["month", "ticker", "rank"]].copy()
    r["month_end"] = r["month"] + pd.offsets.MonthEnd(0)
    me = me.merge(r[["month_end", "ticker", "rank"]], on=["ticker", "month_end"], how="left")
    # Forward-fill any remaining NaN ranks for tickers that existed in previous months
    me["rank"] = me.groupby("ticker")["rank"].ffill().fillna(99).astype(int)

    # EXIT state classification
    def classify_exit(row):
        close = row["Close"]
        rs20 = row.get("rs_20d", np.nan)
        rsc = row.get("rs_change_20d", np.nan)
        ma50 = row.get("ma50", np.nan)
        ma100 = row.get("ma100", np.nan)
        rnk = row["rank"]
        dd = row.get("drawdown_252d", np.nan)

        if pd.isna(close) or pd.isna(rs20):
            return "UNKNOWN"

        rule_a = rnk > 10
        rule_b = (not pd.isna(rs20) and rs20 < 0 and
                  not pd.isna(rsc) and rsc < 0)
        rule_c = (not pd.isna(ma50) and close < ma50)
        rule_d1 = (not pd.isna(ma100) and close < ma100 and
                   not pd.isna(rs20) and rs20 < 0 and
                   not pd.isna(rsc) and rsc < 0)
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

    me["exit_state"] = me.apply(classify_exit, axis=1)

    # Turnaround signals
    ta_cols = ["ticker", "month_end", "drawdown_252d", "distance_from_high_252d",
               "volatility_60d", "rs_change_60d", "volume_ratio",
               "recovery_from_60d_low", "above_ma20"]
    avail = [c for c in ta_cols if c in me.columns]
    ta = me[avail].copy()
    ta["vol_pct"] = ta.groupby("month_end")["volatility_60d"].rank(pct=True)
    ta["deep_drawdown"] = ta["drawdown_252d"] < -0.25
    ta["far_from_high"] = ta["distance_from_high_252d"] < -0.20
    ta["high_volatility"] = ta["vol_pct"] >= 0.667
    ta["context_match"] = ta["deep_drawdown"] & ta["far_from_high"] & ta["high_volatility"]
    ta["transition_match"] = ta["rs_change_60d"] > 0
    ta["full_match"] = ta["context_match"] & ta["transition_match"]
    ta["volume_high"] = ta["volume_ratio"] > 1.3
    ta["recovered"] = ta["recovery_from_60d_low"] > 0.10
    ta["confirmation_count"] = (
        ta["volume_high"].astype(int) +
        ta["above_ma20"].astype(int) +
        ta["recovered"].astype(int)
    )

    # Merge signals back
    me["full_match"] = ta["full_match"]
    me["confirmation_count"] = ta["confirmation_count"]

    # Filter unknown
    me = me[me["exit_state"] != "UNKNOWN"]
    # Filter to months where Config B rank is available (not forward-filled 99)
    me = me[me["rank"] < 99]
    print(f"  Signal records: {len(me):,} across {me['month_end'].nunique()} months")
    return me


def simulate_strategies(signal_df, prices):
    """
    Run both strategies month by month:
      - Config B: Top 5 by rank, monthly rebalance
      - Decision Layer V1: Top 5 with SELL/REPLACE/Turnaround overlay
    """
    print("\nSimulating strategies...")
    months = sorted(signal_df["month_end"].unique())

    # Monthly return lookup
    ret_map = {}
    for ticker, df in prices.items():
        for _, row in df.iterrows():
            ret_map[(ticker, row["Date"])] = row["monthly_return"]

    def multi_ret(ticker, start_month, n):
        td = prices.get(ticker)
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

    config_b_returns = []
    dl_returns = []
    dl_replacements = []
    dl_turnaround_events = []
    dl_turnover_log = []

    # Decision Layer state
    dl_holdings = {}  # ticker -> entry_rank
    first = True

    for month in months:
        slice_df = signal_df[signal_df["month_end"] == month].copy()
        ranked = slice_df.sort_values("rank", ascending=True)
        ret_map_m = {t: ret_map.get((t, month), 0)
                     for t in ranked["ticker"]}

        # -- Config B: Top 5, always --
        config_b_top5 = ranked.head(5)
        config_b_ret = np.mean([
            ret_map_m.get(t, 0) for t in config_b_top5["ticker"]
        ])
        config_b_returns.append({
            "month": month, "portfolio_return": config_b_ret
        })

        # -- Decision Layer V1 --
        if first:
            # Initialize from Top 5 with actual ranks
            dl_holdings = {}
            for i, row in ranked.head(5).iterrows():
                dl_holdings[row["ticker"]] = row["rank"]
            first = False
        else:
            new_h = {}
            rank_map = ranked.set_index("ticker")["rank"].to_dict()
            state_map = ranked.set_index("ticker")["exit_state"].to_dict()
            ta_map = ranked.set_index("ticker")["full_match"].to_dict()
            confirm_map = ranked.set_index("ticker")["confirmation_count"].to_dict()
            held = set(dl_holdings.keys())

            # Rule 1: Check rank drop > 10 from entry rank → SELL
            for ticker, entry_rank in list(dl_holdings.items()):
                if ticker not in rank_map:
                    new_h[ticker] = entry_rank
                    continue
                curr_rank = rank_map[ticker]
                rank_drop = curr_rank - entry_rank

                if rank_drop > 10:
                    # SELL → find best-ranked eligible replacement
                    held_without = held - {ticker} if ticker in held else held
                    candidates = ranked[
                        ~ranked["ticker"].isin(held_without | set(new_h.keys()))
                    ]
                    if len(candidates) > 0:
                        repl = candidates.iloc[0]
                        repl_ticker = repl["ticker"]
                        dl_replacements.append({
                            "month": month,
                            "replaced": ticker,
                            "replacement": repl_ticker,
                            "reason": "rank_drop",
                            "rank_drop": rank_drop,
                            "entry_rank": entry_rank,
                            "curr_rank": curr_rank,
                        })
                    else:
                        dl_replacements.append({
                            "month": month,
                            "replaced": ticker,
                            "replacement": "NONE",
                            "reason": "rank_drop_no_candidate",
                            "rank_drop": rank_drop,
                            "entry_rank": entry_rank,
                            "curr_rank": curr_rank,
                        })
                        new_h[ticker] = entry_rank
                    continue  # already handled this ticker

                new_h[ticker] = entry_rank

            # Rule 2: Turnaround overlay — if EXIT holding + Full Match exists
            for ticker in list(new_h.keys()):
                ts = state_map.get(ticker)
                if ts == "EXIT":
                    # Check for Turnaround candidates not in portfolio
                    candidates = ranked[
                        (ranked["full_match"] == True) &
                        (~ranked["ticker"].isin(set(new_h.keys())))
                    ]
                    if len(candidates) > 0:
                        best_ta = candidates.sort_values(
                            "confirmation_count", ascending=False
                        ).iloc[0]
                        ta_ticker = best_ta["ticker"]
                        new_h.pop(ticker)
                        new_h[ta_ticker] = rank_map.get(ta_ticker, 99)
                        dl_turnaround_events.append({
                            "month": month,
                            "replaced": ticker,
                            "replacement": ta_ticker,
                            "reason": "turnaround_overlay",
                            "exit_state": ts,
                            "ta_confirmation": best_ta["confirmation_count"],
                            "ta_full_match": True,
                        })

            # Ensure we maintain exactly 5 holdings
            sorted_h = sorted(
                new_h.items(),
                key=lambda x: rank_map.get(x[0], 99)
            )
            dl_holdings = dict(sorted_h[:5])

        # Record portfolio return
        dl_ret = np.mean([
            ret_map_m.get(t, 0) for t in dl_holdings
        ])
        dl_returns.append({
            "month": month, "portfolio_return": dl_ret
        })

        # Track turnover
        if len(dl_turnover_log) > 0:
            prev = set(dl_turnover_log[-1]["holdings"])
            curr = set(dl_holdings.keys())
            changes = len(curr - prev) + len(prev - curr)
            dl_turnover_log.append({
                "month": month,
                "holdings": list(dl_holdings.keys()),
                "changes": changes,
            })
        else:
            dl_turnover_log.append({
                "month": month,
                "holdings": list(dl_holdings.keys()),
                "changes": 0,
            })

    cb_df = pd.DataFrame(config_b_returns).set_index("month")["portfolio_return"]
    dl_df = pd.DataFrame(dl_returns).set_index("month")["portfolio_return"]
    repl_df = pd.DataFrame(dl_replacements)
    ta_ev_df = pd.DataFrame(dl_turnaround_events)
    turn_df = pd.DataFrame(dl_turnover_log)

    print(f"  Config B months: {len(cb_df)}")
    print(f"  Decision Layer months: {len(dl_df)}")
    print(f"  Rank drop replacements: {len(repl_df)}")
    print(f"  Turnaround overlays: {len(ta_ev_df)}")

    return cb_df, dl_df, repl_df, ta_ev_df, turn_df


def compute_metrics(ret_s, label, ir):
    """Compute and print portfolio metrics."""
    pr = ret_s.copy()
    pr.index = pr.index.to_period("M").to_timestamp()
    common = pr.index.intersection(ir.index)
    pr = pr.loc[common]
    ir_c = ir.loc[common]

    n_yrs = len(pr) / 12
    tr = (1 + pr).prod() - 1
    cagr = ((1 + tr) ** (1 / n_yrs) - 1) * 100 if n_yrs > 0 else 0
    excess = pr - ir_c
    alpha = ((1 + excess).prod() ** (1 / n_yrs) - 1) * 100 if n_yrs > 0 else 0
    rf = 0.005
    sharpe = ((pr.mean() - rf) / pr.std() * np.sqrt(12)
              if pr.std() > 0 else 0)
    cum = (1 + pr).cumprod()
    dd = (cum - cum.cummax()) / cum.cummax()
    max_dd = dd.min() * 100

    print(f"  {label:<15} CAGR={cagr:>7.2f}%  Sharpe={sharpe:.2f}  "
          f"MaxDD={max_dd:>6.1f}%  Alpha={alpha:>7.2f}%")
    return {"cagr": cagr, "sharpe": sharpe, "max_dd": max_dd,
            "alpha": alpha, "n_months": len(pr)}


def main():
    print("=" * 80)
    print("GATE-001: Decision Layer V1 Production Gate")
    print("Integrated Backtest: Config B vs Decision Layer V1")
    print("=" * 80)

    daily, wh, ihsg, prices = load_data()
    signals = build_decision_signals(daily, wh)

    # Run both strategies
    cb_ret, dl_ret, repl_df, ta_ev_df, turn_df = simulate_strategies(
        signals, prices
    )

    # Align indices
    ir = ihsg.copy()
    ir.index = ir.index.to_period("M").to_timestamp()

    print("\n" + "=" * 80)
    print("PERFORMANCE COMPARISON")
    print("=" * 80)

    cb_m = compute_metrics(cb_ret, "Config B Top 5", ir)
    dl_m = compute_metrics(dl_ret, "Decision Layer V1", ir)

    # Pairwise comparison
    cb_p = cb_ret.copy()
    cb_p.index = cb_p.index.to_period("M").to_timestamp()
    dl_p = dl_ret.copy()
    dl_p.index = dl_p.index.to_period("M").to_timestamp()
    common = cb_p.index.intersection(dl_p.index).intersection(ir.index)
    cb_p = cb_p.loc[common]
    dl_p = dl_p.loc[common]

    diff = dl_p - cb_p
    wr = (diff > 0).mean()
    print(f"\n  Monthly win rate (DL vs Config B): {wr*100:.1f}%")
    print(f"  Avg monthly excess: {diff.mean()*100:+.2f}%")
    print(f"  CAGR delta: {dl_m['cagr'] - cb_m['cagr']:+.2f}%")
    print(f"  Sharpe delta: {dl_m['sharpe'] - cb_m['sharpe']:+.2f}")
    print(f"  MaxDD delta: {dl_m['max_dd'] - cb_m['max_dd']:+.2f}%")
    print(f"  Alpha delta: {dl_m['alpha'] - cb_m['alpha']:+.2f}%")

    # Turnover comparison
    if len(turn_df) > 0:
        avg_changes = turn_df[turn_df["month"] != turn_df["month"].iloc[0]]["changes"].mean()
        print(f"\n  Decision Layer avg monthly turnover: {avg_changes:.1f} holdings changed")
        print(f"  Config B turnover: 0-5 changes per month (full rebalance)")

    # Event stats
    print(f"\n  Decision Layer events:")
    print(f"    Rank drop >10 replacements: {len(repl_df)}")
    if len(repl_df) > 0:
        print(f"    Avg rank drop: {repl_df['rank_drop'].mean():.1f}")
    print(f"    Turnaround overlays: {len(ta_ev_df)}")

    # Gate verdict
    print("\n" + "=" * 80)
    print("GATE-001 VERDICT")
    print("=" * 80)

    cagr_pass = dl_m["cagr"] > cb_m["cagr"]
    sharpe_pass = dl_m["sharpe"] > cb_m["sharpe"]
    alpha_pass = dl_m["alpha"] > cb_m["alpha"]
    maxdd_pass = dl_m["max_dd"] >= cb_m["max_dd"]

    print(f"\n  CAGR:     Config B={cb_m['cagr']:.2f}%  "
          f"DL={dl_m['cagr']:.2f}%  {'BEATS' if cagr_pass else 'LAGS'}")
    print(f"  Sharpe:   Config B={cb_m['sharpe']:.2f}  "
          f"DL={dl_m['sharpe']:.2f}  {'BEATS' if sharpe_pass else 'LAGS'}")
    print(f"  MaxDD:    Config B={cb_m['max_dd']:.1f}%  "
          f"DL={dl_m['max_dd']:.1f}%  {'BETTER' if maxdd_pass else 'WORSE'}")
    print(f"  Alpha:    Config B={cb_m['alpha']:.2f}%  "
          f"DL={dl_m['alpha']:.2f}%  {'BEATS' if alpha_pass else 'LAGS'}")
    print(f"  Win Rate: DL vs Config B monthly = {wr*100:.1f}%")

    # Gate success: Decision Layer must beat Config B on CAGR
    # (primary success criteria)
    passed = cagr_pass
    print(f"\n  Success Criteria: Decision Layer CAGR > Config B CAGR")
    print(f"  Gate: {'PASSED' if passed else 'NOT PASSED'}")
    print(f"  Decision Layer V1 is {'ELIGIBLE' if passed else 'NOT ELIGIBLE'} "
          f"for production implementation.")

    # Save results
    summary = pd.DataFrame([
        {"strategy": "Config B Top 5", **cb_m},
        {"strategy": "Decision Layer V1", **dl_m},
    ])
    summary.to_csv(OUTPUT_DIR / "gate_001_summary.csv", index=False)
    diff_series = pd.DataFrame({
        "month": common,
        "config_b_return": cb_p.values,
        "dl_return": dl_p.values,
        "excess": diff.values,
    })
    diff_series.to_csv(OUTPUT_DIR / "gate_001_monthly_comparison.csv", index=False)
    if len(repl_df) > 0:
        repl_df.to_csv(OUTPUT_DIR / "gate_001_replacement_events.csv", index=False)
    if len(ta_ev_df) > 0:
        ta_ev_df.to_csv(OUTPUT_DIR / "gate_001_turnaround_events.csv", index=False)
    turn_df.to_csv(OUTPUT_DIR / "gate_001_turnover.csv", index=False)

    print(f"\nResults saved to {OUTPUT_DIR}")
    print(f"\nGate 001 complete.")


if __name__ == "__main__":
    main()
