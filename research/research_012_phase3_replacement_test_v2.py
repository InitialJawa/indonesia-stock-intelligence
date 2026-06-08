"""
RESEARCH-012 Phase 3 — Replacement Test (V2)
===============================================
Question: Is replacing weak holdings better than holding them?

Method: For every rank-drop >10 event, compare:
  Scenario A (HOLD): keep the deteriorated stock for next 1/3/6M
  Scenario B (REPLACE): sell and buy highest-ranked eligible stock

Portfolio-level:
  HOLD strategy: Top 5, no replacements
  REPLACE strategy: Top 5, replace when rank drop > 10
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WH_PATH = PROJECT_ROOT / "warehouse_historical" / "warehouse_v3.csv"
MONTHLY_DIR = PROJECT_ROOT / "database" / "monthly"
IHSG_PATH = PROJECT_ROOT / "benchmarks" / "ihsg_monthly.csv"
OUTPUT_DIR = PROJECT_ROOT / "research" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    print("Loading data...")
    prices = {}
    for fp in sorted(MONTHLY_DIR.glob("*.csv")):
        ticker = fp.stem
        df = pd.read_csv(fp)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")
        prices[ticker] = df

    wh = pd.read_csv(WH_PATH)
    wh["month"] = pd.to_datetime(wh["month"])
    wh = wh.sort_values(["ticker", "month"]).reset_index(drop=True)

    ihsg = pd.read_csv(IHSG_PATH)
    ihsg["Date"] = pd.to_datetime(ihsg["Date"])
    ihsg = ihsg.set_index("Date")["monthly_return"]

    print(f"  Prices: {len(prices)} tickers, Warehouse: {len(wh)} records, "
          f"IHSG: {len(ihsg)} months")
    return prices, wh, ihsg


def build_data(wh, prices):
    """Build ticker-month dataset with returns and scores."""
    price_map = {}
    for ticker, df in prices.items():
        for _, row in df.iterrows():
            price_map[(ticker, row["Date"])] = row["month_end_price"]

    records = []
    for _, row in wh.iterrows():
        ticker = row["ticker"]
        month = pd.Timestamp(row["month"])
        me = month + pd.offsets.MonthEnd(0)
        nme = me + pd.offsets.MonthEnd(1)
        cp = price_map.get((ticker, me))
        np_ = price_map.get((ticker, nme))
        if cp and np_ and cp > 0 and np_ > 0:
            records.append({
                "month": month, "ticker": ticker,
                "final_score": row["final_score"],
                "monthly_return": (np_ / cp) - 1,
            })
    df = pd.DataFrame(records)
    print(f"  Data: {len(df)} obs, {df['month'].nunique()} months, {df['ticker'].nunique()} tickers")
    return df


def simulate_replacements(data):
    """
    Simulate the REPLACE strategy (Drop > 10) and record every replacement event.
    Returns the portfolio return series AND the list of replacement events.
    """
    print("\nSimulating REPLACE strategy and capturing events...")
    portfolio_returns = []
    events = []
    holdings = {}  # ticker -> entry_rank
    first = True

    for month, group in data.groupby("month"):
        ranked = group.sort_values("final_score", ascending=False)
        ranked["rank"] = range(1, len(ranked) + 1)
        rank_map = ranked.set_index("ticker")["rank"].to_dict()
        ret_map = group.set_index("ticker")["monthly_return"].to_dict()

        if first:
            top5 = ranked.head(5)
            holdings = {t: i+1 for i, t in enumerate(top5["ticker"])}
            first = False
        else:
            new_h = {}
            # Process each current holding
            for ticker, entry_rank in holdings.items():
                curr_rank = rank_map.get(ticker, 99)
                rank_drop = curr_rank - entry_rank

                if rank_drop > 10:
                    # REPLACE: find best stock NOT currently held
                    held_set = set(holdings.keys())
                    candidates = ranked[~ranked["ticker"].isin(held_set)]
                    if len(candidates) > 0:
                        repl = candidates.iloc[0]["ticker"]
                        new_h[repl] = rank_map.get(repl, 99)
                        events.append({
                            "month": month,
                            "replaced": ticker,
                            "replacement": repl,
                            "entry_rank": entry_rank,
                            "curr_rank": curr_rank,
                            "rank_drop": rank_drop,
                        })
                    else:
                        new_h[ticker] = entry_rank
                else:
                    new_h[ticker] = entry_rank

            # Sort by current rank, keep top 5
            sorted_h = sorted(new_h.items(), key=lambda x: rank_map.get(x[0], 99))
            holdings = dict(sorted_h[:5])

        port_ret = np.mean([ret_map.get(t, 0) for t in holdings])
        portfolio_returns.append({"month": month, "portfolio_return": port_ret})

    events_df = pd.DataFrame(events)
    ret_series = pd.DataFrame(portfolio_returns).set_index("month")["portfolio_return"]
    print(f"  Replacements found: {len(events_df)}")
    if len(events_df) > 0:
        print(f"  Avg rank drop: {events_df['rank_drop'].mean():.1f}")
        print(f"  Unique tickers replaced: {events_df['replaced'].nunique()}")
    return ret_series, events_df


def simulate_hold(data):
    """HOLD strategy: Top 5, no replacements ever. Just monthly rebalance."""
    print("\nSimulating HOLD strategy...")
    portfolio_returns = []
    for month, group in data.groupby("month"):
        ranked = group.sort_values("final_score", ascending=False)
        top5 = ranked.head(5)
        ret_map = group.set_index("ticker")["monthly_return"].to_dict()
        port_ret = np.mean([ret_map[t] for t in top5["ticker"] if t in ret_map])
        portfolio_returns.append({"month": month, "portfolio_return": port_ret})
    return pd.DataFrame(portfolio_returns).set_index("month")["portfolio_return"]


def event_level_analysis(data, events_df):
    """
    For each replacement event, compare forward returns of:
      - HOLD: keep the replaced stock
      - REPLACE: buy the replacement stock

    1M, 3M, 6M horizons.
    """
    print("\n=== Event-Level: HOLD vs REPLACE ===")
    if len(events_df) == 0:
        print("  No events to analyze.")
        return pd.DataFrame()

    # Build ticker-month return lookup
    ret_map = {}
    for _, row in data.iterrows():
        ret_map[(row["ticker"], row["month"])] = row["monthly_return"]

    # For each event, get the sequence of monthly returns for both tickers
    def multi_month_return(ticker, start_month, n_months):
        """Get cumulative forward return over n_months starting at start_month."""
        ticker_data = data[data["ticker"] == ticker].sort_values("month")
        months = ticker_data["month"].tolist()
        try:
            start = months.index(start_month)
        except ValueError:
            return None
        if start + n_months >= len(months):
            return None
        cum = 1.0
        for i in range(n_months):
            m = months[start + i]
            r = ret_map.get((ticker, m))
            if r is None or pd.isna(r):
                return None
            cum *= (1 + r)
        return cum - 1

    horizons = [1, 3, 6]
    comparisons = []

    for _, ev in events_df.iterrows():
        month = ev["month"]
        repl = ev["replacement"]
        replcd = ev["replaced"]

        row_data = {"month": month, "replaced": replcd, "replacement": repl,
                    "rank_drop": ev["rank_drop"]}

        all_valid = True
        for h in horizons:
            hr = multi_month_return(replcd, month, h)
            rr = multi_month_return(repl, month, h)
            if hr is None or rr is None:
                all_valid = False
                break
            row_data[f"hold_{h}m"] = hr
            row_data[f"replace_{h}m"] = rr
            row_data[f"diff_{h}m"] = rr - hr

        if all_valid:
            comparisons.append(row_data)

    comp_df = pd.DataFrame(comparisons)
    print(f"  Valid comparisons: {len(comp_df)} / {len(events_df)} events")

    print(f"\n  {'Horizon':<10} {'HOLD Avg':<12} {'REPLACE Avg':<12} {'Diff':<12} {'Repl Win%':<12}")
    print(f"  {'-'*58}")
    for h in horizons:
        hold_r = comp_df[f"hold_{h}m"]
        rep_r = comp_df[f"replace_{h}m"]
        diff = rep_r - hold_r
        wr = (diff > 0).mean()
        print(f"  {h}M{'':<8} {hold_r.mean()*100:<12.2f}% {rep_r.mean()*100:<12.2f}% "
              f"{diff.mean()*100:<+11.2f}% {wr*100:<11.1f}%")

    return comp_df


def portfolio_level(data, ihsg):
    """Compare HOLD vs REPLACE at portfolio level."""
    print("\n=== Portfolio-Level: HOLD vs REPLACE ===")

    hold_ret = simulate_hold(data)
    repl_ret, events_df = simulate_replacements(data)

    # Align with IHSG
    ir = ihsg.copy()
    ir.index = ir.index.to_period("M").to_timestamp()

    def metrics(ret_s, label):
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
        sharpe = (pr.mean() - rf) / pr.std() * np.sqrt(12) if pr.std() > 0 else 0
        cum = (1 + pr).cumprod()
        dd = (cum - cum.cummax()) / cum.cummax()
        max_dd = dd.min() * 100

        print(f"  {label:<12} CAGR={cagr:.2f}%  Sharpe={sharpe:.2f}  "
              f"MaxDD={max_dd:.1f}%  Alpha={alpha:.2f}%")
        return {"cagr": cagr, "sharpe": sharpe, "max_dd": max_dd, "alpha": alpha}

    h = metrics(hold_ret, "HOLD")
    r = metrics(repl_ret, "REPLACE")

    diff = repl_ret - hold_ret
    wr = (diff > 0).mean()
    print(f"\n  Monthly win rate (REPLACE vs HOLD): {wr*100:.1f}%")
    print(f"  CAGR delta: {r['cagr'] - h['cagr']:+.2f}%")
    print(f"  Sharpe delta: {r['sharpe'] - h['sharpe']:+.2f}")
    print(f"  Alpha delta: {r['alpha'] - h['alpha']:+.2f}%")

    return h, r, events_df


def main():
    print("=" * 80)
    print("RESEARCH-012 Phase 3: Replacement Test")
    print("Is replacing weak holdings better than holding them?")
    print("=" * 80)

    prices, wh, ihsg = load_data()
    data = build_data(wh, prices)

    # Portfolio-level comparison
    hold_m, repl_m, events_df = portfolio_level(data, ihsg)

    # Event-level comparison
    comp_df = event_level_analysis(data, events_df)

    # Save
    events_df.to_csv(OUTPUT_DIR / "research_012_phase3_events.csv", index=False)
    if len(comp_df) > 0:
        comp_df.to_csv(OUTPUT_DIR / "research_012_phase3_event_comparison.csv", index=False)
    pd.DataFrame([
        {"scenario": "HOLD", **hold_m},
        {"scenario": "REPLACE", **repl_m},
    ]).to_csv(OUTPUT_DIR / "research_012_phase3_summary.csv", index=False)

    # Success criteria
    print("\n" + "=" * 80)
    print("PHASE 3 — SUCCESS CRITERIA")
    print("=" * 80)
    print("Replacement consistently outperforms hold.")

    cagr_ok = repl_m["cagr"] > hold_m["cagr"]
    sharpe_ok = repl_m["sharpe"] > hold_m["sharpe"]
    alpha_ok = repl_m["alpha"] > hold_m["alpha"]

    print(f"\n  CAGR:  HOLD={hold_m['cagr']:.2f}%  REPLACE={repl_m['cagr']:.2f}%  "
          f"{'BEATS' if cagr_ok else 'LAGS'}")
    print(f"  Sharpe: HOLD={hold_m['sharpe']:.2f}  REPLACE={repl_m['sharpe']:.2f}  "
          f"{'BEATS' if sharpe_ok else 'LAGS'}")
    print(f"  Alpha:  HOLD={hold_m['alpha']:.2f}%  REPLACE={repl_m['alpha']:.2f}%  "
          f"{'BEATS' if alpha_ok else 'LAGS'}")

    verdict = (cagr_ok and sharpe_ok and alpha_ok)
    print(f"\n  Verdict: {'PASSED' if verdict else 'NOT PASSED'}")
    print(f"  {'Replacement DOES improve outcomes.' if verdict else 'Replacement does NOT consistently outperform.'}")

    print("\nPhase 3 complete.")


if __name__ == "__main__":
    main()
