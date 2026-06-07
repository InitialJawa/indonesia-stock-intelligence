"""
RESEARCH-012 Phase 2 — Rank Deterioration Test
===============================================
Question: Does leaving Top N or rank collapse justify selling?

Tests:
  A. Exit Top 5   — sell when rank > 5
  B. Exit Top 10  — sell when rank > 10
  C. Exit Top 20  — sell when rank > 20
  D. Drop > 5     — sell when rank drops by >5 from entry
  E. Drop > 10    — sell when rank drops by >10 from entry
  F. Drop > 15    — sell when rank drops by >15 from entry

Baseline: Monthly rebalance, buy Config B Top 5, equal-weight.

Metrics: CAGR, Sharpe, Max Drawdown, Alpha, Turnover.

Data source: warehouse_v3 (Config B scores + ranks) + monthly price files.
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


def load_monthly_prices():
    """Load all ticker monthly price files, return dict ticker->DataFrame."""
    print("Loading monthly price data...")
    prices = {}
    for fp in sorted(MONTHLY_DIR.glob("*.csv")):
        ticker = fp.stem
        df = pd.read_csv(fp)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")
        prices[ticker] = df
    print(f"  Loaded {len(prices)} tickers")
    return prices


def load_warehouse():
    """Load warehouse_v3 with final scores, filter to tickers with price data."""
    print("Loading warehouse_v3...")
    df = pd.read_csv(WH_PATH)
    df["month"] = pd.to_datetime(df["month"])
    df = df.sort_values(["ticker", "month"]).reset_index(drop=True)
    print(f"  {len(df)} records, {df['ticker'].nunique()} tickers, {df['month'].nunique()} months")
    return df


def load_ihsg():
    """Load IHSG monthly returns."""
    ihsg = pd.read_csv(IHSG_PATH)
    ihsg["Date"] = pd.to_datetime(ihsg["Date"])
    ihsg = ihsg.set_index("Date")["monthly_return"]
    return ihsg


def compute_returns(wh_df, prices):
    """
    For each ticker-month, compute monthly return.
    Uses monthly price files for both current and next month prices.
    warehouse_v3 month dates (1st of month) converted to month-end.
    """
    print("Computing ticker-month returns...")

    # Build price lookup: (ticker, Date) -> price
    price_map = {}
    for ticker, df in prices.items():
        for _, row in df.iterrows():
            price_map[(ticker, row["Date"])] = row["month_end_price"]

    # Debug: check first few
    debug_ticker = wh_df["ticker"].iloc[0]
    debug_month = pd.Timestamp(wh_df["month"].iloc[0])
    debug_me = debug_month + pd.offsets.MonthEnd(0)
    print(f"  Debug: {debug_ticker}, warehouse month={debug_month.date()}, month-end={debug_me.date()}")
    found_price = price_map.get((debug_ticker, debug_me))
    print(f"  Price found for ({debug_ticker}, {debug_me.date()}): {found_price}")
    if found_price is None:
        # Show what dates are available for this ticker
        avail_dates = [k[1] for k in price_map.keys() if k[0] == debug_ticker]
        if avail_dates:
            print(f"  Available dates for {debug_ticker}: {sorted(avail_dates)[:5]}")

    rows = []
    no_price_cur = 0
    no_price_next = 0
    matched = 0

    for _, row in wh_df.iterrows():
        ticker = row["ticker"]
        month = pd.Timestamp(row["month"])
        month_end = month + pd.offsets.MonthEnd(0)
        next_month_end = month_end + pd.offsets.MonthEnd(1)

        cur_price = price_map.get((ticker, month_end))
        if cur_price is None or pd.isna(cur_price) or cur_price == 0:
            no_price_cur += 1
            continue

        next_price = price_map.get((ticker, next_month_end))
        if next_price is None or pd.isna(next_price) or next_price == 0:
            no_price_next += 1
            continue

        monthly_return = (next_price / cur_price) - 1
        rows.append({
            "ticker": ticker,
            "month": month,
            "final_score": row["final_score"],
            "monthly_return": monthly_return,
        })
        matched += 1

    result = pd.DataFrame(rows)
    print(f"  {matched} matched, {no_price_cur} no cur price, {no_price_next} no next price")
    print(f"  {len(result)} ticker-month observations")
    return result


def backtest_baseline(data, ihsg_returns, top_n=5):
    """
    Baseline: Monthly rebalance, buy Top N by final_score, equal-weight.
    Returns series of monthly portfolio returns.
    """
    print(f"\n=== Baseline: Config B Top {top_n} ===")
    portfolio_returns = []
    turnover_records = []
    prev_holdings = set()

    for month, group in data.groupby("month"):
        # Rank by final_score descending
        ranked = group.sort_values("final_score", ascending=False)
        top = ranked.head(top_n)

        # Equal-weight portfolio return
        port_return = top["monthly_return"].mean()
        portfolio_returns.append({"month": month, "portfolio_return": port_return})

        # Turnover: fraction changed from prev month
        curr_holdings = set(top["ticker"])
        if prev_holdings:
            changed = len(curr_holdings - prev_holdings) + len(prev_holdings - curr_holdings)
            turnover = changed / (2 * top_n)
        else:
            turnover = 0
        turnover_records.append(turnover)
        prev_holdings = curr_holdings

    ret_series = pd.DataFrame(portfolio_returns).set_index("month")["portfolio_return"]
    avg_turnover = np.mean(turnover_records) if turnover_records else 0
    metrics = compute_metrics(ret_series, ihsg_returns, avg_turnover)
    print(f"  CAGR: {metrics['cagr']:.2f}%  Sharpe: {metrics['sharpe']:.2f}  "
          f"MaxDD: {metrics['max_dd']:.1f}%  Alpha: {metrics['alpha']:.2f}%  "
          f"Turnover: {metrics['turnover']:.1%}")
    return metrics, ret_series


def backtest_exit_threshold(data, ihsg_returns, top_n=5, exit_rank_threshold=10):
    """
    Strategy: Buy Top N monthly. If any holding's rank > exit_rank_threshold,
    replace with highest-ranked ticker not currently held.
    """
    label = f"Exit Top {exit_rank_threshold}"
    print(f"\n=== {label} ===")
    portfolio_returns = []
    turnover_records = []
    prev_holdings = set()

    for month, group in data.groupby("month"):
        # Rank all tickers this month
        ranked = group.sort_values("final_score", ascending=False).copy()
        ranked["rank"] = range(1, len(ranked) + 1)

        if not prev_holdings:
            # First month: just pick Top N
            selected = ranked.head(top_n)
        else:
            # Check which holdings exceed rank threshold
            rank_map = ranked.set_index("ticker")["rank"].to_dict()
            survivors = [t for t in prev_holdings
                         if t in rank_map and rank_map[t] <= exit_rank_threshold]
            to_replace = top_n - len(survivors)

            # Find highest-ranked tickers not already held
            candidates = ranked[~ranked["ticker"].isin(prev_holdings)]
            replacements = candidates.head(to_replace)["ticker"].tolist()
            selected = survivors + replacements

        # Monthly return
        return_map = group.set_index("ticker")["monthly_return"].to_dict()
        port_return = np.mean([return_map.get(t, 0) for t in selected])
        portfolio_returns.append({"month": month, "portfolio_return": port_return})

        # Turnover
        curr_holdings = set(selected)
        if prev_holdings:
            changed = len(curr_holdings - prev_holdings) + len(prev_holdings - curr_holdings)
            turnover = changed / (2 * top_n)
        else:
            turnover = 0
        turnover_records.append(turnover)
        prev_holdings = curr_holdings

    ret_series = pd.DataFrame(portfolio_returns).set_index("month")["portfolio_return"]
    avg_turnover = np.mean(turnover_records) if turnover_records else 0
    metrics = compute_metrics(ret_series, ihsg_returns, avg_turnover)
    print(f"  CAGR: {metrics['cagr']:.2f}%  Sharpe: {metrics['sharpe']:.2f}  "
          f"MaxDD: {metrics['max_dd']:.1f}%  Alpha: {metrics['alpha']:.2f}%  "
          f"Turnover: {metrics['turnover']:.1%}")
    print(f"  Avg holdings: {len(prev_holdings)}  " +
          f"Replacement events: {sum(1 for r in turnover_records if r > 0)}")
    return metrics, ret_series


def backtest_rank_collapse(data, ihsg_returns, top_n=5, drop_threshold=5):
    """
    Strategy: Buy Top N monthly. If any holding's rank drops by > drop_threshold
    from its entry rank, replace with highest-ranked ticker not currently held.
    """
    label = f"Drop > {drop_threshold}"
    print(f"\n=== {label} ===")
    portfolio_returns = []
    turnover_records = []
    prev_holdings = {}  # ticker -> entry_rank

    for month, group in data.groupby("month"):
        ranked = group.sort_values("final_score", ascending=False).copy()
        ranked["rank"] = range(1, len(ranked) + 1)
        rank_map = ranked.set_index("ticker")["rank"].to_dict()

        if not prev_holdings:
            # First month: pick Top N
            selected = ranked.head(top_n)
            selected_tickers = selected["ticker"].tolist()
            entry_ranks = {t: i+1 for i, t in enumerate(selected_tickers)}
        else:
            # Check which holdings exceeded rank drop threshold
            survivors = []
            for t, entry_rank in prev_holdings.items():
                if t not in rank_map:
                    continue
                curr_rank = rank_map[t]
                rank_drop = curr_rank - entry_rank
                if rank_drop <= drop_threshold:
                    survivors.append(t)

            to_replace = top_n - len(survivors)
            candidates = ranked[~ranked["ticker"].isin(prev_holdings.keys())]
            replacements = candidates.head(to_replace)["ticker"].tolist()
            selected_tickers = survivors + replacements

            # Entry ranks for new replacements
            entry_ranks = {}
            for t in survivors:
                entry_ranks[t] = prev_holdings[t]
            for t in replacements:
                entry_ranks[t] = rank_map.get(t, 99)

        # Monthly return
        return_map = group.set_index("ticker")["monthly_return"].to_dict()
        port_return = np.mean([return_map.get(t, 0) for t in selected_tickers])
        portfolio_returns.append({"month": month, "portfolio_return": port_return})

        # Turnover
        curr_set = set(selected_tickers)
        prev_set = set(prev_holdings.keys()) if prev_holdings else set()
        if prev_set:
            changed = len(curr_set - prev_set) + len(prev_set - curr_set)
            turnover = changed / (2 * top_n)
        else:
            turnover = 0
        turnover_records.append(turnover)
        prev_holdings = entry_ranks

    ret_series = pd.DataFrame(portfolio_returns).set_index("month")["portfolio_return"]
    avg_turnover = np.mean(turnover_records) if turnover_records else 0
    metrics = compute_metrics(ret_series, ihsg_returns, avg_turnover)
    print(f"  CAGR: {metrics['cagr']:.2f}%  Sharpe: {metrics['sharpe']:.2f}  "
          f"MaxDD: {metrics['max_dd']:.1f}%  Alpha: {metrics['alpha']:.2f}%  "
          f"Turnover: {metrics['turnover']:.1%}")
    return metrics, ret_series


def compute_metrics(port_returns, ihsg_returns, turnover):
    """
    Compute CAGR, Sharpe, Max Drawdown, Alpha.
    Align dates by normalizing to month periods.
    """
    if len(port_returns) < 3:
        return {"cagr": 0, "sharpe": 0, "max_dd": 0, "alpha": 0, "turnover": turnover}

    # Normalize both to month-start for alignment
    pr = port_returns.copy()
    pr.index = pr.index.to_period("M").to_timestamp()

    ir = ihsg_returns.copy()
    ir.index = ir.index.to_period("M").to_timestamp()

    common = pr.index.intersection(ir.index)
    pr = pr.loc[common]
    ir = ir.loc[common]

    if len(pr) < 3:
        return {"cagr": 0, "sharpe": 0, "max_dd": 0, "alpha": 0, "turnover": turnover}

    n_years = len(pr) / 12
    total_return = (1 + pr).prod() - 1
    cagr = ((1 + total_return) ** (1 / n_years) - 1) * 100 if n_years > 0 else 0
    excess = pr - ir
    alpha = ((1 + excess).prod() ** (1 / n_years) - 1) * 100 if n_years > 0 else 0

    risk_free_monthly = 0.005  # ~6% annual
    sharpe = (pr.mean() - risk_free_monthly) / pr.std() * np.sqrt(12) if pr.std() > 0 else 0

    cum = (1 + pr).cumprod()
    rolling_max = cum.cummax()
    drawdown = (cum - rolling_max) / rolling_max
    max_dd = drawdown.min() * 100

    return {
        "cagr": round(cagr, 2),
        "sharpe": round(sharpe, 2),
        "max_dd": round(max_dd, 1),
        "alpha": round(alpha, 2),
        "turnover": round(turnover, 4),
    }


def main():
    print("=" * 80)
    print("RESEARCH-012 Phase 2: Rank Deterioration Test")
    print("=" * 80)

    prices = load_monthly_prices()
    wh_df = load_warehouse()

    # Restrict to tickers with monthly price files
    available = [t for t in sorted(prices.keys()) if t.replace(".JK", "") + ".JK" in wh_df["ticker"].unique()
                 or t in wh_df["ticker"].unique()]
    # The warehouse uses .JK suffix, monthly files don't
    # Let's handle: monthly files are like ADRO.JK.csv, warehouse has ADRO.JK
    # So they should match directly

    data = compute_returns(wh_df, prices)
    ihsg = load_ihsg()

    print(f"\nBacktest period: {data['month'].min().date()} to {data['month'].max().date()}")
    print(f"  {data['month'].nunique()} months")
    print(f"  {data['ticker'].nunique()} tickers")

    # ---- Baseline ----
    baseline_metrics, _ = backtest_baseline(data, ihsg, top_n=5)

    # ---- Test A, B, C: Exit thresholds ----
    threshold_results = []
    for threshold in [5, 10, 20]:
        metrics, _ = backtest_exit_threshold(data, ihsg, top_n=5, exit_rank_threshold=threshold)
        metrics["test"] = f"Exit Top {threshold}"
        threshold_results.append(metrics)

    # ---- Test D, E, F: Rank collapse ----
    collapse_results = []
    for drop in [5, 10, 15]:
        metrics, _ = backtest_rank_collapse(data, ihsg, top_n=5, drop_threshold=drop)
        metrics["test"] = f"Drop > {drop}"
        collapse_results.append(metrics)

    # ---- Summary table ----
    print("\n" + "=" * 80)
    print("PHASE 2 RESULTS SUMMARY")
    print("=" * 80)
    header = f"{'Strategy':<25} {'CAGR%':<10} {'Sharpe':<10} {'MaxDD%':<10} {'Alpha%':<10} {'Turnover':<10}"
    print(header)
    print("-" * 75)

    rows = [baseline_metrics] + threshold_results + collapse_results
    for r in rows:
        test_name = r.get("test", "Baseline")
        print(f"{test_name:<25} {r['cagr']:<10} {r['sharpe']:<10} "
              f"{r['max_dd']:<10} {r['alpha']:<10} {r['turnover']:<10.1%}")

    # ---- Success criteria check ----
    print("\n" + "=" * 80)
    print("SUCCESS CRITERIA")
    print("=" * 80)
    print("One rule materially improves outcomes vs Baseline.")
    print()

    best_cagr = max(rows, key=lambda r: r["cagr"])
    best_sharpe = max(rows, key=lambda r: r["sharpe"])
    best_alpha = max(rows, key=lambda r: r["alpha"])
    best_dd = min(rows, key=lambda r: r["max_dd"])

    print(f"  Best CAGR:  {best_cagr.get('test', 'Baseline')} ({best_cagr['cagr']}%)")
    print(f"  Best Sharpe: {best_sharpe.get('test', 'Baseline')} ({best_sharpe['sharpe']})")
    print(f"  Best Alpha: {best_alpha.get('test', 'Baseline')} ({best_alpha['alpha']}%)")
    print(f"  Best MaxDD: {best_dd.get('test', 'Baseline')} ({best_dd['max_dd']}%)")

    print()
    baseline = rows[0]
    improvements = []
    for r in rows[1:]:
        cagr_improvement = r["cagr"] - baseline["cagr"]
        sharpe_improvement = r["sharpe"] - baseline["sharpe"]
        alpha_improvement = r["alpha"] - baseline["alpha"]
        dd_improvement = r["max_dd"] - baseline["max_dd"]
        improvements.append({
            "test": r.get("test", "?"),
            "cagr_chg": cagr_improvement,
            "sharpe_chg": sharpe_improvement,
            "alpha_chg": alpha_improvement,
            "dd_chg": dd_improvement,
        })

    best_improvement = max(improvements, key=lambda x: (x["cagr_chg"], x["sharpe_chg"], x["alpha_chg"]))
    print(f"  Most improved vs Baseline: {best_improvement['test']}")
    print(f"    CAGR delta: {best_improvement['cagr_chg']:+.2f}%")
    print(f"    Sharpe delta: {best_improvement['sharpe_chg']:+.2f}")
    print(f"    Alpha delta: {best_improvement['alpha_chg']:+.2f}%")
    print(f"    MaxDD delta: {best_improvement['dd_chg']:+.1f}%")

    # Determine if any rule materially improves outcomes
    meaningful = [x for x in improvements if x["cagr_chg"] > 2 and x["sharpe_chg"] > 0.1]
    if meaningful:
        print(f"\n  [OK] Material improvement detected: {[x['test'] for x in meaningful]}")
        print("  Gate PASSED - rank deterioration can justify selling.")
    else:
        print(f"\n  [NO] No material improvement detected.")
        print("  Gate NOT PASSED - rank deterioration does not justify selling.")

    # Save all results
    results_df = pd.DataFrame([
        {"strategy": "Baseline (Top 5)", **baseline_metrics},
        *[{"strategy": f"Exit Top {t}", **m} for t, m in zip([5, 10, 20], threshold_results)],
        *[{"strategy": f"Drop > {d}", **m} for d, m in zip([5, 10, 15], collapse_results)],
    ])
    out_path = OUTPUT_DIR / "research_012_phase2_results.csv"
    results_df.to_csv(out_path, index=False)
    print(f"\nResults saved: {out_path}")
    print("\nPhase 2 complete.")


if __name__ == "__main__":
    main()
