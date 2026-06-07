"""
GATE-001-V2: Decision Layer V2 — Rank Drop Only (No Turnaround Overlay)
=======================================================================
Purpose: Test Decision Layer with ONLY rank drop > 10 SELL + replacement.
         No Turnaround overlay (which was detrimental in V1).

Compare: Config B Top 5 vs Decision Layer V2 (rank drop only)
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


def build_signals(daily_df, wh_df):
    print("\nBuilding signals...")
    wh_df["rank"] = wh_df.groupby("month")["final_score"].rank(
        ascending=False, method="min").astype(int)
    daily_df["month_end"] = daily_df["Date"] + pd.offsets.MonthEnd(0)
    me = daily_df.groupby(["ticker", "month_end"]).last().reset_index()
    r = wh_df[["month", "ticker", "rank"]].copy()
    r["month_end"] = r["month"] + pd.offsets.MonthEnd(0)
    me = me.merge(r[["month_end", "ticker", "rank"]], on=["ticker", "month_end"], how="left")
    me["rank"] = me.groupby("ticker")["rank"].ffill().fillna(99).astype(int)
    me = me[me["rank"] < 99]  # Only months with real ranks
    print(f"  Records: {len(me):,} across {me['month_end'].nunique()} months")
    return me


def run_strategies(signal_df, prices):
    months = sorted(signal_df["month_end"].unique())
    ret_map = {}
    for ticker, df in prices.items():
        for _, row in df.iterrows():
            ret_map[(ticker, row["Date"])] = row["monthly_return"]

    cb_returns = []
    v2_returns = []
    v2_events = []
    v2_turnover = []

    v2_holdings = {}
    first = True

    for month in months:
        slice_df = signal_df[signal_df["month_end"] == month].copy()
        ranked = slice_df.sort_values("rank", ascending=True)
        ret_map_m = {t: ret_map.get((t, month), 0) for t in ranked["ticker"]}

        # Config B: Top 5 by rank
        top5 = ranked.head(5)
        cb_ret = np.mean([ret_map_m.get(t, 0) for t in top5["ticker"]])
        cb_returns.append({"month": month, "portfolio_return": cb_ret})

        # Decision Layer V2: rank drop > 10 only
        if first:
            v2_holdings = {t: r for t, r in zip(top5["ticker"], top5["rank"])}
            first = False
        else:
            rank_map = ranked.set_index("ticker")["rank"].to_dict()
            new_h = {}
            for ticker, entry_rank in v2_holdings.items():
                curr_rank = rank_map.get(ticker, 99)
                rank_drop = curr_rank - entry_rank
                if rank_drop > 10:
                    held_set = set(v2_holdings.keys()) - {ticker}
                    candidates = ranked[~ranked["ticker"].isin(held_set | set(new_h.keys()))]
                    if len(candidates) > 0:
                        repl = candidates.iloc[0]["ticker"]
                        new_h[repl] = rank_map.get(repl, 99)
                        v2_events.append({
                            "month": month, "replaced": ticker,
                            "replacement": repl, "rank_drop": rank_drop,
                            "entry_rank": entry_rank, "curr_rank": curr_rank,
                        })
                    else:
                        new_h[ticker] = entry_rank
                else:
                    new_h[ticker] = entry_rank
            sorted_h = sorted(new_h.items(), key=lambda x: rank_map.get(x[0], 99))
            v2_holdings = dict(sorted_h[:5])

        v2_ret = np.mean([ret_map_m.get(t, 0) for t in v2_holdings])
        v2_returns.append({"month": month, "portfolio_return": v2_ret})
        v2_turnover.append({
            "month": month, "holdings": list(v2_holdings.keys()),
        })

    cb_df = pd.DataFrame(cb_returns).set_index("month")["portfolio_return"]
    v2_df = pd.DataFrame(v2_returns).set_index("month")["portfolio_return"]
    ev_df = pd.DataFrame(v2_events)
    turn_df = pd.DataFrame(v2_turnover)
    print(f"  Months: {len(cb_df)} | V2 replacements: {len(ev_df)}")
    return cb_df, v2_df, ev_df, turn_df


def metrics(ret_s, label, ir):
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
    print(f"  {label:<15} CAGR={cagr:>7.2f}%  Sharpe={sharpe:.2f}  "
          f"MaxDD={max_dd:>6.1f}%  Alpha={alpha:>7.2f}%")
    return {"cagr": cagr, "sharpe": sharpe, "max_dd": max_dd, "alpha": alpha}


def main():
    print("=" * 80)
    print("GATE-001-V2: Decision Layer V2 — Rank Drop Only")
    print("=" * 80)
    daily, wh, ihsg, prices = load_data()
    signals = build_signals(daily, wh)
    cb_ret, v2_ret, ev_df, turn_df = run_strategies(signals, prices)

    ir = ihsg.copy()
    ir.index = ir.index.to_period("M").to_timestamp()

    print("\n--- Performance ---")
    cb_m = metrics(cb_ret, "Config B Top 5", ir)
    v2_m = metrics(v2_ret, "Decision Layer V2", ir)

    # Align
    cb_p = cb_ret.copy(); cb_p.index = cb_p.index.to_period("M").to_timestamp()
    v2_p = v2_ret.copy(); v2_p.index = v2_p.index.to_period("M").to_timestamp()
    common = cb_p.index.intersection(v2_p.index).intersection(ir.index)
    cb_p = cb_p.loc[common]; v2_p = v2_p.loc[common]
    diff = v2_p - cb_p
    wr = (diff > 0).mean()

    print(f"\n  Monthly win rate (V2 vs Config B): {wr*100:.1f}%")
    print(f"  Avg monthly excess: {diff.mean()*100:+.2f}%")
    print(f"  CAGR delta: {v2_m['cagr'] - cb_m['cagr']:+.2f}%")
    print(f"  Sharpe delta: {v2_m['sharpe'] - cb_m['sharpe']:+.2f}")
    print(f"  Alpha delta: {v2_m['alpha'] - cb_m['alpha']:+.2f}%")
    print(f"\n  Events: {len(ev_df)} rank-drop replacements")
    if len(ev_df) > 0:
        print(f"  Avg rank drop: {ev_df['rank_drop'].mean():.1f}")

    # Gate verdict
    passed = v2_m["cagr"] > cb_m["cagr"]
    print("\n" + "=" * 80)
    print("GATE-001-V2 VERDICT")
    print("=" * 80)
    print(f"  CAGR: Config B={cb_m['cagr']:.2f}%  V2={v2_m['cagr']:.2f}%  "
          f"{'BEATS' if passed else 'LAGS'}")
    print(f"  Success Criteria: V2 CAGR > Config B CAGR")
    print(f"  Gate: {'PASSED' if passed else 'NOT PASSED'}")

    pd.DataFrame([{"strategy":"Config B",**cb_m},{"strategy":"DL V2",**v2_m}]
                 ).to_csv(OUTPUT_DIR / "gate_001_v2_summary.csv", index=False)
    if len(ev_df) > 0:
        ev_df.to_csv(OUTPUT_DIR / "gate_001_v2_events.csv", index=False)
    print(f"\nResults saved.")


if __name__ == "__main__":
    main()
