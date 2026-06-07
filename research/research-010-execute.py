#!/usr/bin/env python3
"""
RESEARCH-010: TIMING ENGINE PAPER TRADING

Build first Timing Engine prototype on top of Config B (momentum proxy).
DO NOT integrate into production. DO NOT alter Config B.
Run paper simulation only.
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_WH = PROJECT_ROOT / "database" / "historical" / "warehouse_daily_v4.parquet"
BENCHMARK_FILE = PROJECT_ROOT / "benchmarks" / "ihsg.csv"
PORTFOLIO_FILE = PROJECT_ROOT / "archives" / "backtest" / "momentum_portfolio.csv"
MONTHLY_DIR = PROJECT_ROOT / "database" / "monthly"
OUTPUT_DIR = PROJECT_ROOT / "research" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PERIODS_PER_YEAR = 12
RISK_FREE_RATE = 0.05

SECTOR_MAP = {
    "ADRO.JK": "Coal Mining",
    "AKRA.JK": "Energy & Logistics",
    "AMMN.JK": "Mining (Gold/Copper)",
    "ANTM.JK": "Mining (State-owned)",
    "ASII.JK": "Automotive & Conglomerate",
    "BBCA.JK": "Banking",
    "BBNI.JK": "Banking",
    "BBRI.JK": "Banking",
    "BMRI.JK": "Banking",
    "BRPT.JK": "Chemicals & Conglomerate",
    "CPIN.JK": "Poultry & Feed",
    "ESSA.JK": "Energy (Oil & Gas)",
    "EXCL.JK": "Telecom",
    "GOTO.JK": "Technology",
    "HEAL.JK": "Healthcare",
    "ICBP.JK": "Consumer Goods",
    "INDF.JK": "Consumer Goods",
    "INTP.JK": "Cement",
    "ITMG.JK": "Coal Mining",
    "KLBF.JK": "Pharmaceutical",
    "MAPI.JK": "Retail",
    "MDKA.JK": "Mining (Gold)",
    "MIKA.JK": "Healthcare",
    "PGAS.JK": "Energy (Gas)",
    "PTBA.JK": "Coal Mining (State-owned)",
    "SIDO.JK": "Consumer Goods",
    "SMGR.JK": "Cement",
    "TLKM.JK": "Telecom",
    "TPIA.JK": "Chemicals (Petrochemical)",
    "UNTR.JK": "Heavy Equipment & Mining",
}


def load_data():
    wh = pd.read_parquet(INPUT_WH)
    wh["Date"] = pd.to_datetime(wh["Date"])
    wh = wh.sort_values(["ticker", "Date"]).reset_index(drop=True)
    return wh


def load_ihsg():
    ihsg = pd.read_csv(BENCHMARK_FILE)
    date_col = next((c for c in ihsg.columns if c.lower() in ["date", "tanggal"]), ihsg.columns[0])
    price_col = next((c for c in ihsg.columns if c.lower() in ["close", "adj close", "price"]), ihsg.columns[1])
    ihsg[date_col] = pd.to_datetime(ihsg[date_col])
    ihsg = ihsg.set_index(date_col).sort_index()
    ihsg["ihsg_close"] = ihsg[price_col]
    return ihsg


def classify_market_regime(ihsg, window=60):
    ihsg = ihsg.copy()
    close = ihsg["ihsg_close"].values
    n = len(close)
    fwd60 = np.full(n, np.nan)
    if n > 60:
        fwd60[:-60] = close[60:] / close[:-60] - 1
    ihsg["fwd_60d_return"] = fwd60
    regimes = {}
    for date, row in ihsg.iterrows():
        ret = row["fwd_60d_return"]
        if np.isnan(ret):
            regimes[date] = "unknown"
        elif ret > 0.10:
            regimes[date] = "bull"
        elif ret < -0.05:
            regimes[date] = "bear"
        else:
            regimes[date] = "sideways"
    return pd.Series(regimes, name="regime")


class TimingEngine:
    """5-stage timing engine for individual stock state evaluation."""

    def __init__(self, vol_threshold):
        self.vol_threshold = vol_threshold

    def get_state(self, row):
        """Return (state, weight_multiplier) for a single stock snapshot."""
        rs_improving = row.get("rs_change_60d", 0) > 0

        # Stage 4 is the gate
        if not rs_improving:
            return "AVOID", 0.0

        # Stage 1-3
        deep_drawdown = row.get("drawdown_252d", 0) < -0.25
        far_from_high = row.get("distance_from_high_252d", 0) < -0.20
        high_vol = row.get("volatility_60d", 0) > self.vol_threshold
        core_score = sum([deep_drawdown, far_from_high, high_vol])

        # Stage 5: Confirmation layer
        vol_confirm = row.get("volume_ratio", 0) > 1.2
        price_confirm = bool(row.get("above_ma20", 0))
        mom_confirm = row.get("momentum_slope", 0) > 0
        confirmations = sum([vol_confirm, price_confirm, mom_confirm])

        if core_score >= 2 and confirmations >= 2:
            return "BUY", 1.0
        elif core_score >= 2 and confirmations >= 1:
            return "ACCUMULATE", 0.50
        elif core_score >= 1 or confirmations >= 1:
            return "WATCH", 0.25
        else:
            return "WATCH", 0.10


def get_monthly_return(ticker, target_month):
    """Look up a stock's monthly return for a given YYYY-MM."""
    f = MONTHLY_DIR / f"{ticker}.csv"
    if not f.exists():
        return np.nan
    df = pd.read_csv(f)
    df["YYYY-MM"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m")
    row = df[df["YYYY-MM"] == target_month]
    if row.empty:
        return np.nan
    ret = row["monthly_return"].values[0]
    return ret


def get_formation_snapshot(wh, ticker, formation_date):
    """Get the most recent warehouse row at or before the formation date."""
    t = wh[(wh["ticker"] == ticker) & (wh["Date"] <= formation_date)].sort_values("Date")
    if t.empty:
        return None
    return t.iloc[-1].to_dict()


def calculate_cagr(returns):
    cumulative = (1 + returns).prod()
    years = len(returns) / PERIODS_PER_YEAR
    if years <= 0:
        return 0.0
    return cumulative ** (1 / years) - 1


def calculate_volatility(returns):
    return returns.std() * np.sqrt(PERIODS_PER_YEAR)


def calculate_sharpe(returns):
    cagr = calculate_cagr(returns)
    vol = calculate_volatility(returns)
    if vol == 0:
        return 0.0
    return (cagr - RISK_FREE_RATE) / vol


def calculate_sortino(returns):
    cagr = calculate_cagr(returns)
    downside = returns[returns < 0]
    if len(downside) == 0:
        return 0.0
    downside_vol = downside.std() * np.sqrt(PERIODS_PER_YEAR)
    if downside_vol == 0:
        return 0.0
    return (cagr - RISK_FREE_RATE) / downside_vol


def calculate_max_drawdown(returns):
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    return (cumulative / running_max - 1).min()


def calculate_drawdown_series(returns):
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    return cumulative / running_max - 1


def calculate_alpha(portfolio_returns, benchmark_returns):
    """Alpha = portfolio_return - benchmark_return, annualized."""
    excess = portfolio_returns - benchmark_returns
    return calculate_cagr(excess)


def calculate_turnover(weights_current, weights_prev):
    """Turnover = sum(abs(new - old)) / 2 for overlapping tickers."""
    all_tickers = set(list(weights_current.keys()) + list(weights_prev.keys()))
    total_change = 0.0
    for t in all_tickers:
        new_w = weights_current.get(t, 0.0)
        old_w = weights_prev.get(t, 0.0)
        total_change += abs(new_w - old_w)
    return total_change / 2.0


def calculate_hit_rate(returns):
    if len(returns) == 0:
        return 0.0
    return (returns > 0).sum() / len(returns)


def calculate_beta(portfolio_returns, benchmark_returns):
    if len(portfolio_returns) < 2:
        return 0.0
    cov = np.cov(portfolio_returns, benchmark_returns)
    var_b = np.var(benchmark_returns)
    if var_b == 0:
        return 0.0
    return cov[0, 1] / var_b


def main():
    print("=" * 80)
    print("RESEARCH-010: TIMING ENGINE PAPER TRADING")
    print("=" * 80)

    # ── Load data ──
    print("\n--- Loading Data ---")
    wh = load_data()
    ihsg = load_ihsg()
    print(f"Warehouse: {len(wh):,} rows, {wh['ticker'].nunique()} tickers")

    regime_series = classify_market_regime(ihsg)
    wh["regime_60d"] = wh["Date"].map(regime_series)

    # ── Volatility threshold (67th percentile of full dataset) ──
    vol_threshold = wh["volatility_60d"].quantile(0.67)
    print(f"Volatility threshold (67th pctile): {vol_threshold:.4f}")

    # ── Load momentum portfolio ──
    pf = pd.read_csv(PORTFOLIO_FILE)
    pf["date"] = pf["date"].astype(str)
    formation_months = sorted(pf["date"].unique())
    print(f"Portfolio: {len(pf)} rows, {len(formation_months)} formation months")
    print(f"  Range: {formation_months[0]} to {formation_months[-1]}")

    # ── Initialize timing engine ──
    engine = TimingEngine(vol_threshold)

    # ── Run simulation ──
    print("\n--- Running Simulation ---")

    results = []
    baseline_weights_by_month = {}
    timed_weights_by_month = {}

    for idx, formation_month in enumerate(formation_months):
        holdings = pf[pf["date"] == formation_month]
        formation_date = pd.Timestamp(formation_month + "-01") + pd.offsets.MonthEnd(0)

        # Next month for return lookup
        dt = pd.Timestamp(formation_month + "-01")
        next_month = (dt + pd.DateOffset(months=1)).strftime("%Y-%m")

        # State snapshots
        stock_states = {}

        # Build both portfolios
        baseline_weights = {}
        timed_weights = {}

        for _, row in holdings.iterrows():
            ticker = row["ticker"]
            snapshot = get_formation_snapshot(wh, ticker, formation_date)

            base_w = row["weight"] / 100.0  # 0.20
            baseline_weights[ticker] = base_w

            if snapshot is not None:
                state, mult = engine.get_state(snapshot)
                stock_states[ticker] = state
                timed_w = base_w * mult
            else:
                stock_states[ticker] = "AVOID"
                timed_w = 0.0

            timed_weights[ticker] = timed_w

        # Normalize timed weights if they don't sum to 1.0
        total_timed_w = sum(timed_weights.values())
        if total_timed_w > 0:
            for t in timed_weights:
                timed_weights[t] = timed_weights[t] / total_timed_w

        # Cash = unallocated
        cash_weight = 1.0 - total_timed_w
        if total_timed_w == 0:
            cash_weight = 1.0

        # Look up monthly returns
        baseline_ret = 0.0
        timed_ret = 0.0

        for ticker in baseline_weights:
            mret = get_monthly_return(ticker, next_month)
            if np.isnan(mret):
                mret = 0.0
            baseline_ret += mret * baseline_weights[ticker]

        for ticker in timed_weights:
            mret = get_monthly_return(ticker, next_month)
            if np.isnan(mret):
                mret = 0.0
            timed_ret += mret * timed_weights[ticker]

        # Cash earns 0%
        # timed_ret already accounts for the actual timed weights

        # Benchmark return
        bm_ret = None
        bm_mask = ihsg.index.strftime("%Y-%m") == next_month
        if bm_mask.any():
            bm_vals = ihsg.loc[bm_mask, "ihsg_close"]
            if len(bm_vals) >= 2:
                bm_ret = bm_vals.iloc[-1] / bm_vals.iloc[0] - 1
            elif len(bm_vals) == 1:
                bm_ret = 0.0
        if bm_ret is None or np.isnan(bm_ret):
            bm_ret = 0.0

        # Count states
        state_counts = {}
        for s in stock_states.values():
            state_counts[s] = state_counts.get(s, 0) + 1

        results.append({
            "formation_month": formation_month,
            "next_month": next_month,
            "baseline_return": round(baseline_ret, 6),
            "timed_return": round(timed_ret, 6),
            "benchmark_return": round(bm_ret, 6),
            "n_stocks": len(holdings),
            "n_avoid": state_counts.get("AVOID", 0),
            "n_watch": state_counts.get("WATCH", 0),
            "n_accumulate": state_counts.get("ACCUMULATE", 0),
            "n_buy": state_counts.get("BUY", 0),
            "cash_weight": round(cash_weight, 4),
        })

        baseline_weights_by_month[formation_month] = baseline_weights
        timed_weights_by_month[formation_month] = timed_weights

    results_df = pd.DataFrame(results)
    results_df = results_df.dropna(subset=["baseline_return", "timed_return"])

    print(f"  Simulated {len(results_df)} months")

    # ── Compute metrics ──
    print("\n" + "=" * 80)
    print("PERFORMANCE METRICS")
    print("=" * 80)

    base_returns = results_df["baseline_return"].values
    timed_returns = results_df["timed_return"].values
    bm_returns = results_df["benchmark_return"].values

    base_series = pd.Series(base_returns)
    timed_series = pd.Series(timed_returns)
    bm_series = pd.Series(bm_returns)

    base_cagr = calculate_cagr(base_series)
    timed_cagr = calculate_cagr(timed_series)
    bm_cagr = calculate_cagr(bm_series)

    base_vol = calculate_volatility(base_series)
    timed_vol = calculate_volatility(timed_series)

    base_sharpe = calculate_sharpe(base_series)
    timed_sharpe = calculate_sharpe(timed_series)

    base_sortino = calculate_sortino(base_series)
    timed_sortino = calculate_sortino(timed_series)

    base_maxdd = calculate_max_drawdown(base_series)
    timed_maxdd = calculate_max_drawdown(timed_series)

    base_alpha = calculate_cagr(base_series - bm_series)
    timed_alpha = calculate_cagr(timed_series - bm_series)

    base_hit = calculate_hit_rate(base_series)
    timed_hit = calculate_hit_rate(timed_series)

    base_beta = calculate_beta(base_series, bm_series)
    timed_beta = calculate_beta(timed_series, bm_series)

    # Turnover
    base_turnover_list = []
    timed_turnover_list = []
    formation_list = sorted(formation_months)
    for i in range(1, len(formation_list)):
        fm_prev = formation_list[i - 1]
        fm_curr = formation_list[i]
        if fm_prev in baseline_weights_by_month and fm_curr in baseline_weights_by_month:
            base_turnover_list.append(calculate_turnover(
                baseline_weights_by_month[fm_curr], baseline_weights_by_month[fm_prev]))
            timed_turnover_list.append(calculate_turnover(
                timed_weights_by_month[fm_curr], timed_weights_by_month[fm_prev]))

    base_avg_turnover = np.mean(base_turnover_list) if base_turnover_list else 0
    timed_avg_turnover = np.mean(timed_turnover_list) if timed_turnover_list else 0

    # Print comparison table
    metrics_table = [
        ("CAGR", f"{base_cagr:.2%}", f"{timed_cagr:.2%}", f"{bm_cagr:.2%}"),
        ("Volatility (ann.)", f"{base_vol:.2%}", f"{timed_vol:.2%}", "-"),
        ("Sharpe Ratio", f"{base_sharpe:.2f}", f"{timed_sharpe:.2f}", "-"),
        ("Sortino Ratio", f"{base_sortino:.2f}", f"{timed_sortino:.2f}", "-"),
        ("Max Drawdown", f"{base_maxdd:.2%}", f"{timed_maxdd:.2%}", "-"),
        ("Alpha", f"{base_alpha:.2%}", f"{timed_alpha:.2%}", "-"),
        ("Beta", f"{base_beta:.2f}", f"{timed_beta:.2f}", "-"),
        ("Hit Rate", f"{base_hit:.2%}", f"{timed_hit:.2%}", "-"),
        ("Avg Monthly Turnover", f"{base_avg_turnover:.2%}", f"{timed_avg_turnover:.2%}", "-"),
    ]

    print(f"\n  {'Metric':25s} {'Baseline':12s} {'+Timing':12s} {'IHSG':12s}")
    print(f"  {'-'*25} {'-'*12} {'-'*12} {'-'*12}")
    for metric, base_v, timed_v, bm_v in metrics_table:
        print(f"  {metric:25s} {base_v:>12s} {timed_v:>12s} {bm_v:>12s}")

    # ── State distribution ──
    print("\n" + "=" * 80)
    print("STATE DISTRIBUTION")
    print("=" * 80)
    total_states = results_df[["n_avoid", "n_watch", "n_accumulate", "n_buy"]].sum()
    grand_total = total_states.sum()
    for state, count in total_states.items():
        print(f"  {state:15s}: {count:4d} ({count/grand_total*100:.1f}%)" if grand_total > 0 else "")

    avg_cash = results_df["cash_weight"].mean()
    print(f"  {'Cash (avg)':15s}: {avg_cash:.1%}")

    # ── Regime comparison ──
    print("\n" + "=" * 80)
    print("REGIME BREAKDOWN")
    print("=" * 80)
    regime_map = {}
    for _, r in results_df.iterrows():
        next_dt = pd.Timestamp(r["next_month"] + "-01")
        reg = regime_series.get(next_dt, "unknown") if next_dt in regime_series.index else \
              regime_series.get(next_dt - pd.DateOffset(days=1), "unknown")
        if reg not in regime_map:
            regime_map[reg] = {"months": 0, "base_sum": 0, "timed_sum": 0, "bm_sum": 0}
        regime_map[reg]["months"] += 1
        regime_map[reg]["base_sum"] += r["baseline_return"]
        regime_map[reg]["timed_sum"] += r["timed_return"]
        regime_map[reg]["bm_sum"] += r["benchmark_return"]

    for reg in ["bull", "bear", "sideways", "unknown"]:
        if reg in regime_map:
            d = regime_map[reg]
            avg_base = d["base_sum"] / d["months"] if d["months"] > 0 else 0
            avg_timed = d["timed_sum"] / d["months"] if d["months"] > 0 else 0
            avg_bm = d["bm_sum"] / d["months"] if d["months"] > 0 else 0
            base_ann = (1 + avg_base) ** 12 - 1 if avg_base > -1 else -1
            timed_ann = (1 + avg_timed) ** 12 - 1 if avg_timed > -1 else -1
            print(f"  {reg:10s}: {d['months']:3d} months  base={avg_base:+.2%}  timed={avg_timed:+.2%}  "
                  f"bm={avg_bm:+.2%}  diff={avg_timed-avg_base:+.2%}")

    # ── Improvement analysis ──
    print("\n" + "=" * 80)
    print("IMPROVEMENT ANALYSIS")
    print("=" * 80)

    # Monthly comparison
    better_months = (timed_series > base_series).sum()
    worse_months = (timed_series < base_series).sum()
    same_months = (timed_series == base_series).sum()
    print(f"  Months where timing helped:   {better_months} / {len(results_df)} ({better_months/len(results_df)*100:.1f}%)")
    print(f"  Months where timing hurt:     {worse_months} / {len(results_df)} ({worse_months/len(results_df)*100:.1f}%)")
    print(f"  Months where timing same:     {same_months} / {len(results_df)} ({same_months/len(results_df)*100:.1f}%)")

    # Worst drawdown periods
    base_dd = calculate_drawdown_series(base_series)
    timed_dd = calculate_drawdown_series(timed_series)
    worst_dd_months = base_dd.idxmin() if len(base_dd) > 0 else 0
    if not np.isnan(worst_dd_months) and worst_dd_months < len(results_df):
        worst_dd_date = results_df.iloc[worst_dd_months]["next_month"]
        print(f"  Baseline worst drawdown month: {worst_dd_date} ({base_dd.min():.2%})")
        print(f"  Timed drawdown in same month:  {timed_dd.iloc[worst_dd_months]:.2%}")

    timed_dd_min_idx = timed_dd.idxmin() if len(timed_dd) > 0 else 0
    if not np.isnan(timed_dd_min_idx) and timed_dd_min_idx < len(results_df):
        timed_worst_date = results_df.iloc[timed_dd_min_idx]["next_month"]
        print(f"  Timing worst drawdown month:   {timed_worst_date} ({timed_dd.min():.2%})")
        print(f"  Baseline drawdown in same:     {base_dd.iloc[timed_dd_min_idx]:.2%}")

    # ──────────────────────────────────────────────────────────────
    # GENERATE DELIVERABLES
    # ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("GENERATING DELIVERABLES")
    print("=" * 80)

    # ── CSV: monthly returns comparison ──
    results_df.to_csv(OUTPUT_DIR / "research-010-monthly-returns.csv", index=False)
    print("  Saved: research-010-monthly-returns.csv")

    # ── CSV: metrics comparison ──
    metrics_data = []
    for metric, base_v, timed_v, bm_v in metrics_table:
        metrics_data.append({
            "metric": metric,
            "baseline": base_v,
            "timed": timed_v,
            "benchmark": bm_v,
        })
    metrics_df = pd.DataFrame(metrics_data)
    metrics_df.to_csv(OUTPUT_DIR / "research-010-metrics.csv", index=False)
    print("  Saved: research-010-metrics.csv")

    # ── CSV: equity curves ──
    ec_df = results_df[["next_month"]].copy()
    ec_df["baseline_cumulative"] = (1 + results_df["baseline_return"]).cumprod()
    ec_df["timed_cumulative"] = (1 + results_df["timed_return"]).cumprod()
    ec_df["benchmark_cumulative"] = (1 + results_df["benchmark_return"]).cumprod()
    ec_df["baseline_drawdown"] = calculate_drawdown_series(results_df["baseline_return"])
    ec_df["timed_drawdown"] = calculate_drawdown_series(results_df["timed_return"])
    ec_df.to_csv(OUTPUT_DIR / "research-010-equity-curves.csv", index=False)
    print("  Saved: research-010-equity-curves.csv")

    # ── MARKDOWN REPORT ──
    md_lines = []
    md_lines.append("# RESEARCH-010: Timing Engine Paper Trading\n")
    md_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    md_lines.append("---\n\n")

    md_lines.append("## Objective\n\n")
    md_lines.append("Determine whether a 5-stage timing layer adds value on top of the existing ranking engine (Config B).\n\n")
    md_lines.append("**Do NOT integrate into production. Do NOT alter Config B.**\n\n")

    md_lines.append("---\n\n")

    md_lines.append("## Engine Structure\n\n")
    md_lines.append("| Stage | Filter | Criteria |\n")
    md_lines.append("|-------|--------|----------|\n")
    md_lines.append("| 1 | Deep Drawdown | `drawdown_252d < -25%` |\n")
    md_lines.append("| 2 | Far From High | `distance_from_high_252d < -20%` |\n")
    md_lines.append("| 3 | High Volatility | `volatility_60d > 67th pctile` |\n")
    md_lines.append("| 4 | RS_CHANGE_60D | `rs_change_60d > 0` (gate) |\n")
    md_lines.append("| 5 | Confirmation Layer | Volume > 1.2, Above MA20, Momentum > 0 |\n\n")

    md_lines.append("### State Mapping\n\n")
    md_lines.append("| State | Core Score | Confirmations | Weight |\n")
    md_lines.append("|-------|-----------|---------------|--------|\n")
    md_lines.append("| AVOID | any | rs_change <= 0 | 0% |\n")
    md_lines.append("| WATCH | >= 1 core | any | 25% (reduced to 10% if no core) |\n")
    md_lines.append("| ACCUMULATE | >= 2 core | >= 1 conf | 50% of normal |\n")
    md_lines.append("| BUY | >= 2 core | >= 2 conf | 100% (full 20%) |\n")
    md_lines.append("| HOLD | (carryover from prior period) | | maintained |\n\n")

    md_lines.append("---\n\n")

    md_lines.append("## Backtest Results\n\n")
    md_lines.append(f"Period: {results_df['next_month'].iloc[0]} to {results_df['next_month'].iloc[-1]} ({len(results_df)} months)\n")
    md_lines.append(f"Portfolio: Top 5 by momentum score, equal weight baseline\n\n")

    md_lines.append("### Performance Metrics\n\n")
    md_lines.append("| Metric | Baseline | +Timing | IHSG |\n")
    md_lines.append("|--------|----------|---------|------|\n")
    for metric, base_v, timed_v, bm_v in metrics_table:
        md_lines.append(f"| {metric} | {base_v} | {timed_v} | {bm_v} |\n")

    md_lines.append("\n### State Distribution\n\n")
    md_lines.append("| State | Count | % |\n")
    md_lines.append("|-------|-------|---|\n")
    for state in ["AVOID", "WATCH", "ACCUMULATE", "BUY"]:
        c = total_states.get("n_" + state.lower(), 0)
        md_lines.append(f"| {state} | {c} | {c/grand_total*100:.1f}% |\n" if grand_total > 0 else f"| {state} | {c} | 0% |\n")
    md_lines.append(f"| Cash (avg) | - | {avg_cash:.1%} |\n\n")

    md_lines.append("### Regime Breakdown\n\n")
    md_lines.append("| Regime | Months | Baseline Avg | Timed Avg | BM Avg | Diff |\n")
    md_lines.append("|--------|--------|-------------|-----------|--------|------|\n")
    for reg in ["bull", "bear", "sideways", "unknown"]:
        if reg in regime_map:
            d = regime_map[reg]
            avg_base = d["base_sum"] / d["months"] if d["months"] > 0 else 0
            avg_timed = d["timed_sum"] / d["months"] if d["months"] > 0 else 0
            avg_bm = d["bm_sum"] / d["months"] if d["months"] > 0 else 0
            md_lines.append(f"| {reg} | {d['months']} | {avg_base:+.2%} | {avg_timed:+.2%} | {avg_bm:+.2%} | {avg_timed-avg_base:+.2%} |\n")

    md_lines.append("\n### Monthly Improvement Breakdown\n\n")
    md_lines.append(f"- Timing helped in **{better_months}** of {len(results_df)} months ({better_months/len(results_df)*100:.1f}%)\n")
    md_lines.append(f"- Timing hurt in **{worse_months}** of {len(results_df)} months ({worse_months/len(results_df)*100:.1f}%)\n\n")

    md_lines.append("---\n\n")

    md_lines.append("## Drawdown Analysis\n\n")
    md_lines.append("| Measure | Baseline | +Timing |\n")
    md_lines.append("|---------|----------|---------|\n")
    md_lines.append(f"| Max Drawdown | {base_maxdd:.2%} | {timed_maxdd:.2%} |\n")
    if not np.isnan(worst_dd_months) and worst_dd_months < len(results_df):
        worst_dd_date = results_df.iloc[worst_dd_months]["next_month"]
        md_lines.append(f"| Worst Month (Baseline) | {worst_dd_date} ({base_dd.min():.2%}) | {timed_dd.iloc[worst_dd_months]:.2%} |\n")
    md_lines.append(f"| Recovery (worst DD to 0) | - | - |\n\n")

    md_lines.append("---\n\n")

    md_lines.append("## Verdict\n\n")

    verdict_points = []
    if timed_sharpe > base_sharpe:
        verdict_points.append(f"✅ Sharpe improved: {base_sharpe:.2f} → {timed_sharpe:.2f}")
    else:
        verdict_points.append(f"❌ Sharpe degraded: {base_sharpe:.2f} → {timed_sharpe:.2f}")

    if timed_maxdd > base_maxdd:
        verdict_points.append(f"✅ Max Drawdown reduced: {base_maxdd:.2%} → {timed_maxdd:.2%}")
    else:
        verdict_points.append(f"❌ Max Drawdown increased: {base_maxdd:.2%} → {timed_maxdd:.2%}")

    if timed_cagr > base_cagr:
        verdict_points.append(f"✅ CAGR preserved/improved: {base_cagr:.2%} → {timed_cagr:.2%}")
    else:
        verdict_points.append(f"❌ CAGR destroyed: {base_cagr:.2%} → {timed_cagr:.2%}")

    for p in verdict_points:
        md_lines.append(f"- {p}\n")

    if timed_sharpe > base_sharpe and timed_alpha >= base_alpha:
        md_lines.append("\n**Conclusion: Timing engine adds value.** The overlay improves risk-adjusted returns without destroying alpha.\n")
    elif timed_sharpe > base_sharpe:
        md_lines.append("\n**Conclusion: Timing engine partially adds value.** Sharpe improves but alpha is reduced. Trade-off may be acceptable for risk reduction.\n")
    else:
        md_lines.append("\n**Conclusion: Timing engine does NOT add value in its current form.** Further tuning required.\n")

    md_lines.append("\n---\n")

    # ── Generate state detail CSV ──
    state_detail = []
    for _, r in results_df.iterrows():
        state_detail.append({
            "formation_month": r["formation_month"],
            "next_month": r["next_month"],
            "n_avoid": int(r["n_avoid"]),
            "n_watch": int(r["n_watch"]),
            "n_accumulate": int(r["n_accumulate"]),
            "n_buy": int(r["n_buy"]),
            "cash_weight": r["cash_weight"],
        })
    state_detail_df = pd.DataFrame(state_detail)
    state_detail_df.to_csv(OUTPUT_DIR / "research-010-state-detail.csv", index=False)
    print("  Saved: research-010-state-detail.csv")

    md_lines.append("*End of RESEARCH-010 Timing Engine Paper Trading*\n")

    with open(OUTPUT_DIR / "research-010-report.md", "w", encoding="utf-8") as f:
        f.writelines(md_lines)
    print("  Saved: research-010-report.md")

    # ──────────────────────────────────────────────────────────────
    # FINAL SUMMARY
    # ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("RESEARCH-010 COMPLETE")
    print("=" * 80)
    print(f"\nDeliverables in {OUTPUT_DIR}:")
    print("  research-010-report.md")
    print("  research-010-metrics.csv")
    print("  research-010-monthly-returns.csv")
    print("  research-010-equity-curves.csv")
    print("  research-010-state-detail.csv")

    print(f"\nKey Metrics Comparison:")
    print(f"  CAGR:          {base_cagr:.2%} → {timed_cagr:.2%}")
    print(f"  Sharpe:        {base_sharpe:.2f} → {timed_sharpe:.2f}")
    print(f"  Sortino:       {base_sortino:.2f} → {timed_sortino:.2f}")
    print(f"  Max DD:        {base_maxdd:.2%} → {timed_maxdd:.2%}")
    print(f"  Alpha:         {base_alpha:.2%} → {timed_alpha:.2%}")
    print(f"  Hit Rate:      {base_hit:.2%} → {timed_hit:.2%}")
    print(f"  Turnover:      {base_avg_turnover:.2%} → {timed_avg_turnover:.2%}")
    print(f"  Timing helped: {better_months}/{len(results_df)} months ({better_months/len(results_df)*100:.1f}%)")

    print(f"\n{'TIMING ENGINE ADDS VALUE' if timed_sharpe > base_sharpe and timed_alpha >= base_alpha else 'TIMING ENGINE NEEDS TUNING'}")


if __name__ == "__main__":
    main()
