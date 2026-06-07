"""
RESEARCH-012 Phase 3 — Replacement Test
=========================================
Question: Is replacing weak holdings better than holding them?

Method: For every rank-drop >10 event, compare:
  Scenario A (HOLD): keep the deteriorated stock for next N months
  Scenario B (REPLACE): sell and buy highest-ranked eligible stock

Then compare both at portfolio level:
  Strategy A: Config B Top 5 monthly, NO replacements (hold through drops)
  Strategy B: Config B Top 5 monthly, REPLACE when rank drop >10

Outputs: CAGR, Alpha, Win Rate (event-level), Drawdown (portfolio-level).
Success: Replacement consistently outperforms hold.
"""

import sys
from pathlib import Path
from collections import OrderedDict

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
    # Monthly prices
    prices = {}
    for fp in sorted(MONTHLY_DIR.glob("*.csv")):
        ticker = fp.stem
        df = pd.read_csv(fp)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")
        prices[ticker] = df

    # Warehouse v3
    wh = pd.read_csv(WH_PATH)
    wh["month"] = pd.to_datetime(wh["month"])
    wh = wh.sort_values(["ticker", "month"]).reset_index(drop=True)

    # IHSG
    ihsg = pd.read_csv(IHSG_PATH)
    ihsg["Date"] = pd.to_datetime(ihsg["Date"])
    ihsg = ihsg.set_index("Date")["monthly_return"]

    print(f"  Prices: {len(prices)} tickers")
    print(f"  Warehouse: {len(wh)} records, {wh['ticker'].nunique()} tickers, {wh['month'].nunique()} months")
    return prices, wh, ihsg


def build_return_matrix(wh, prices):
    """
    Build (month, ticker) -> monthly_return lookup.
    Also return ticker-by-month feature DataFrame.
    """
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
            ret = (np_ / cp) - 1
            records.append({
                "month": month,
                "ticker": ticker,
                "final_score": row["final_score"],
                "monthly_return": ret,
                "price_cur": cp,
                "price_next": np_,
            })

    df = pd.DataFrame(records)
    return df


def find_replacement_events(data):
    """
    For each month where a stock is held in Top 5 and has dropped >10 ranks
    from entry, record the replacement event.

    Returns list of event dicts with:
      - month: when replacement occurs
      - replaced_ticker: stock being sold
      - replacement_ticker: stock being bought
      - replaced_entry_rank: rank when it was first bought
      - replaced_current_rank: current rank
      - rank_drop: how many ranks lost
    """
    print("\nFinding replacement events (Drop > 10)...")
    events = []

    # Simulate Top 5 portfolio month by month with entry rank tracking
    holdings = {}  # ticker -> entry_rank
    prev_selected = set()

    for month, group in data.groupby("month"):
        ranked = group.sort_values("final_score", ascending=False)
        ranked["rank"] = range(1, len(ranked) + 1)
        rank_map = ranked.set_index("ticker")["rank"].to_dict()

        if not prev_selected:
            # First month: buy Top 5
            top5 = ranked.head(5)
            holdings = {t: i+1 for i, t in enumerate(top5["ticker"])}
            prev_selected = set(holdings.keys())
            continue

        # Check existing holdings
        new_holdings = {}
        for ticker, entry_rank in holdings.items():
            if ticker not in rank_map:
                continue
            curr_rank = rank_map[ticker]
            rank_drop = curr_rank - entry_rank

            if rank_drop > 10:
                # REPLACEMENT EVENT: this stock exits
                # Find best replacement
                candidates = ranked[~ranked["ticker"].isin(prev_remaining :=
                    set(t for t in holdings.keys() if (t not in [ticker] or rank_map.get(t, 99) - holdings[t] <= 10)
                        and t in rank_map))]
                # Actually, simpler: find best stock not currently held
                held_tickers = set(k for k, v in holdings.items()
                                   if rank_map.get(k, 99) - v <= 10 or k == ticker)
                # Correction: held tickers are the ones NOT being replaced
                remaining = set()
                for t, er in holdings.items():
                    if t == ticker:
                        continue  # this one is being replaced
                    cr = rank_map.get(t, 99)
                    rd = cr - er
                    if rd <= 10:
                        remaining.add(t)

                best_eligible = ranked[~ranked["ticker"].isin(remaining | {ticker})]
                if len(best_eligible) > 0:
                    replacement = best_eligible.iloc[0]["ticker"]
                    new_holdings[replacement] = rank_map.get(replacement, 99)
                    events.append({
                        "month": month,
                        "replaced_ticker": ticker,
                        "replacement_ticker": replacement,
                        "replaced_entry_rank": entry_rank,
                        "replaced_current_rank": curr_rank,
                        "rank_drop": rank_drop,
                    })
                else:
                    # No eligible replacement, keep holding
                    new_holdings[ticker] = entry_rank
            else:
                new_holdings[ticker] = entry_rank

        # Add any new Top 5 stocks not yet held
        top5_tickers = set(ranked.head(5)["ticker"])
        for t in top5_tickers:
            if t not in new_holdings:
                new_holdings[t] = rank_map.get(t, 99)

        # Limit to 5
        sorted_holdings = sorted(new_holdings.items(), key=lambda x: rank_map.get(x[0], 99))
        holdings = dict(sorted_holdings[:5])
        prev_selected = set(holdings.keys())

    event_df = pd.DataFrame(events)
    print(f"  Total replacement events: {len(event_df)}")
    if len(event_df) > 0:
        print(f"  Unique tickers replaced: {event_df['replaced_ticker'].nunique()}")
        print(f"  Avg rank drop: {event_df['rank_drop'].mean():.1f}")
    return event_df


def event_level_comparison(data, events):
    """
    For each replacement event, compare forward returns of:
      - HOLD: keep the replaced stock
      - REPLACE: buy the replacement stock

    Track 1-month, 3-month, 6-month forward returns.
    """
    print("\n=== Event-Level: HOLD vs REPLACE ===")

    # Build return lookup: (ticker, month) -> next month return
    ret_map = {}
    for _, row in data.iterrows():
        ret_map[(row["ticker"], row["month"])] = row["monthly_return"]

    # Also build multi-month forward returns
    # For each ticker, get price series
    def get_fwd_returns(ticker, start_month, horizons_months):
        """Get forward returns for N months after start_month."""
        months = sorted(data[data["ticker"] == ticker]["month"].unique())
        try:
            start_idx = months.index(start_month)
        except ValueError:
            return None

        result = {}
        for h in horizons_months:
            end_idx = start_idx + h
            if end_idx >= len(months):
                return None
            end_month = months[end_idx]
            # Get cumulative return
            cum_ret = 1.0
            for i in range(h):
                m = months[start_idx + i]
                r = ret_map.get((ticker, m))
                if r is None or pd.isna(r):
                    return None
                cum_ret *= (1 + r)
            result[f"{h}m_return"] = cum_ret - 1
        return result

    horizons = [1, 3, 6]
    comparison = []

    for _, ev in events.iterrows():
        month = ev["month"]
        replaced = ev["replaced_ticker"]
        replacement = ev["replacement_ticker"]

        hold_returns = get_fwd_returns(replaced, month, horizons)
        replace_returns = get_fwd_returns(replacement, month, horizons)

        if hold_returns is None or replace_returns is None:
            continue

        comparison.append({
            "month": month,
            "replaced_ticker": replaced,
            "replacement_ticker": replacement,
            "rank_drop": ev["rank_drop"],
            **{f"hold_{k}": v for k, v in hold_returns.items()},
            **{f"replace_{k}": v for k, v in replace_returns.items()},
        })

    comp_df = pd.DataFrame(comparison)
    print(f"  Valid event comparisons: {len(comp_df)}")

    # Compute win rates
    print(f"\n  {'Horizon':<12} {'HOLD Avg':<12} {'REPLACE Avg':<12} {'Diff':<12} {'Win Rate':<12} {'Hit Rate':<12}")
    print(f"  {'-'*60}")
    for h in horizons:
        col_hold = f"hold_{h}m_return"
        col_rep = f"replace_{h}m_return"
        hold_r = comp_df[col_hold]
        rep_r = comp_df[col_rep]
        diff = rep_r - hold_r
        win_rate = (diff > 0).mean()
        hit_rate_rep = (rep_r > 0).mean()
        hit_rate_hold = (hold_r > 0).mean()

        print(f"  {h}M{'':<10} {hold_r.mean()*100:<12.2f}% {rep_r.mean()*100:<12.2f}% "
              f"{diff.mean()*100:<+11.2f}% {win_rate*100:<11.1f}% ({hit_rate_hold*100:.0f}%/{hit_rate_rep*100:.0f}%)")

    return comp_df


def portfolio_level_backtest(data, ihsg, events):
    """
    Portfolio-level comparison:
      Strategy A (HOLD): Buy Top 5, keep even if rank drops > 10
      Strategy B (REPLACE): Buy Top 5, replace when rank drops > 10

    Note: This is essentially the same as Phase 2 Drop > 10 vs Baseline.
    """
    print("\n=== Portfolio-Level: HOLD vs REPLACE ===")

    def simulate(strategy_name, do_replace):
        """Run portfolio simulation. If do_replace=True, replace on drop > 10."""
        portfolio_returns = []
        holdings = {}  # ticker -> entry_rank
        first_month = True

        for month, group in data.groupby("month"):
            ranked = group.sort_values("final_score", ascending=False)
            ranked["rank"] = range(1, len(ranked) + 1)
            rank_map = ranked.set_index("ticker")["rank"].to_dict()
            ret_map = group.set_index("ticker")["monthly_return"].to_dict()

            if first_month:
                top5 = ranked.head(5)
                holdings = {t: i+1 for i, t in enumerate(top5["ticker"])}
                first_month = False
            else:
                new_holdings = {}
                for ticker, entry_rank in holdings.items():
                    if ticker not in rank_map:
                        continue
                    curr_rank = rank_map[ticker]
                    rank_drop = curr_rank - entry_rank

                    if do_replace and rank_drop > 10:
                        # Replace with best eligible
                        remaining = set()
                        for t, er in holdings.items():
                            if t == ticker:
                                continue
                            cr = rank_map.get(t, 99)
                            if cr - er <= 10:
                                remaining.add(t)
                        best_eligible = ranked[~ranked["ticker"].isin(remaining | {ticker})]
                        if len(best_eligible) > 0:
                            repl = best_eligible.iloc[0]["ticker"]
                            new_holdings[repl] = rank_map.get(repl, 99)
                        else:
                            new_holdings[ticker] = entry_rank
                    else:
                        new_holdings[ticker] = entry_rank

                top5_tickers = set(ranked.head(5)["ticker"])
                for t in top5_tickers:
                    if t not in new_holdings:
                        new_holdings[t] = rank_map.get(t, 99)

                sorted_h = sorted(new_holdings.items(), key=lambda x: rank_map.get(x[0], 99))
                holdings = dict(sorted_h[:5])

            # Portfolio return
            port_ret = np.mean([ret_map.get(t, 0) for t in holdings.keys()])
            portfolio_returns.append({"month": month, "portfolio_return": port_ret})

        ret_series = pd.DataFrame(portfolio_returns).set_index("month")["portfolio_return"]
        return ret_series

    hold_ret = simulate("HOLD", do_replace=False)
    replace_ret = simulate("REPLACE", do_replace=True)

    # Align
    ir = ihsg.copy()
    ir.index = ir.index.to_period("M").to_timestamp()

    def calc_metrics(ret_s, label):
        pr = ret_s.copy()
        pr.index = pr.index.to_period("M").to_timestamp()
        common = pr.index.intersection(ir.index)
        pr = pr.loc[common]
        ir_s = ir.loc[common]

        n_years = len(pr) / 12
        total_ret = (1 + pr).prod() - 1
        cagr = ((1 + total_ret) ** (1 / n_years) - 1) * 100 if n_years > 0 else 0
        excess = pr - ir_s
        alpha = ((1 + excess).prod() ** (1 / n_years) - 1) * 100 if n_years > 0 else 0
        rf = 0.005
        sharpe = (pr.mean() - rf) / pr.std() * np.sqrt(12) if pr.std() > 0 else 0
        cum = (1 + pr).cumprod()
        dd = (cum - cum.cummax()) / cum.cummax()
        max_dd = dd.min() * 100

        print(f"  {label:<12} CAGR={cagr:.2f}%  Sharpe={sharpe:.2f}  "
              f"MaxDD={max_dd:.1f}%  Alpha={alpha:.2f}%")

        return {"cagr": cagr, "sharpe": sharpe, "max_dd": max_dd, "alpha": alpha}

    h = calc_metrics(hold_ret, "HOLD")
    r = calc_metrics(replace_ret, "REPLACE")

    # Pairwise comparison
    common_m = hold_ret.index.to_period("M").to_timestamp().intersection(
        replace_ret.index.to_period("M").to_timestamp())
    diff = replace_ret.loc[common_m] - hold_ret.loc[common_m]
    win_rate = (diff > 0).mean()

    print(f"\n  Replacement Win Rate (monthly): {win_rate*100:.1f}%")
    print(f"  CAGR improvement: {r['cagr'] - h['cagr']:+.2f}%")
    print(f"  Alpha improvement: {r['alpha'] - h['alpha']:+.2f}%")
    print(f"  Sharpe improvement: {r['sharpe'] - h['sharpe']:+.2f}")
    print(f"  MaxDD improvement: {r['max_dd'] - h['max_dd']:+.1f}% (more negative = worse)")

    return h, r


def main():
    print("=" * 80)
    print("RESEARCH-012 Phase 3: Replacement Test")
    print("Do replacements outperform holding?")
    print("=" * 80)

    prices, wh, ihsg = load_data()
    data = build_return_matrix(wh, prices)

    print(f"\nBacktest data: {len(data)} obs, {data['month'].nunique()} months")

    # Step 1: Find replacement events
    events = find_replacement_events(data)
    if len(events) == 0:
        print("  No replacement events found. Check rank calculation.")
        return
    events.to_csv(OUTPUT_DIR / "research_012_phase3_events.csv", index=False)

    # Step 2: Event-level comparison
    comp_df = event_level_comparison(data, events)
    comp_df.to_csv(OUTPUT_DIR / "research_012_phase3_event_comparison.csv", index=False)

    # Step 3: Portfolio-level comparison
    hold_m, repl_m = portfolio_level_backtest(data, ihsg, events)

    # Step 4: Summary
    print("\n" + "=" * 80)
    print("PHASE 3 RESULTS SUMMARY")
    print("=" * 80)
    print(f"\n  Event-Level Replacement Win Rate:")
    for h in [1, 3, 6]:
        col = f"replace_{h}m_return"
        col_h = f"hold_{h}m_return"
        if col in comp_df.columns:
            diff = (comp_df[col] - comp_df[col_h])
            wr = (diff > 0).mean()
            print(f"    {h}M: {wr*100:.1f}%")

    print(f"\n  Portfolio-Level Comparison:")
    print(f"    {'Metric':<12} {'HOLD':<12} {'REPLACE':<12} {'Delta':<12}")
    print(f"    {'-'*48}")
    for k in ["cagr", "sharpe", "alpha"]:
        delta = repl_m.get(k, 0) - hold_m.get(k, 0)
        print(f"    {k:<12} {hold_m.get(k, 0):<12.2f} {repl_m.get(k, 0):<12.2f} {delta:<+11.2f}")
    dd_delta = repl_m.get("max_dd", 0) - hold_m.get("max_dd", 0)
    print(f"    {'max_dd':<12} {hold_m.get('max_dd', 0):<12.1f} {repl_m.get('max_dd', 0):<12.1f} {dd_delta:<+11.1f}")

    success = (repl_m["cagr"] > hold_m["cagr"] and repl_m["sharpe"] > hold_m["sharpe"]
               and repl_m["alpha"] > hold_m["alpha"])
    print(f"\n  Success Criteria: Replacement consistently outperforms hold.")
    print(f"  Verdict: {'PASSED' if success else 'NOT PASSED'}")

    # Save summary
    summary = pd.DataFrame([
        {"scenario": "HOLD", **hold_m},
        {"scenario": "REPLACE", **repl_m},
    ])
    summary.to_csv(OUTPUT_DIR / "research_012_phase3_summary.csv", index=False)
    print(f"\nResults saved to {OUTPUT_DIR}")
    print("Phase 3 complete.")


if __name__ == "__main__":
    main()
