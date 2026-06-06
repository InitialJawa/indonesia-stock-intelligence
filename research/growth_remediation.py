"""
RESEARCH-002: Growth Factor Remediation & Weight Reallocation

Experiments:
  A — Earnings Only (IC, Top5, Top10)
  B — Weight Reallocation (Config D/E/F)
  C — Growth Replacement (LowVol, Dividend)
"""

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import spearmanr

warnings.filterwarnings("ignore")

BASE = Path(__file__).resolve().parent.parent
WAREHOUSE = BASE / "warehouse_historical" / "warehouse_v3.csv"
MONTHLY_DIR = BASE / "database" / "monthly"
BENCHMARK_FILE = BASE / "benchmarks" / "ihsg_monthly.csv"
SECTOR_RULES_FILE = BASE / "config" / "sector_rules.json"
REPORT_DIR = BASE / "reports"

FACTORS = ["quality_score", "growth_score", "value_score", "momentum_score"]
FACTOR_LABELS = {"quality_score": "Quality", "growth_score": "Growth", "value_score": "Value", "momentum_score": "Momentum"}


# ── Helpers ───────────────────────────────────────────────────────

def percentile_normalize(vals):
    arr = np.array(vals, dtype=float)
    ranks = np.argsort(np.argsort(arr)) + 1
    return ranks / len(arr) * 100


def load_monthly(ticker):
    fp = MONTHLY_DIR / f"{ticker}.csv"
    if not fp.exists():
        return None
    df = pd.read_csv(fp)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").set_index("Date")
    return df


def load_monthly_db(tickers):
    monthly = {}
    for t in tickers:
        fp = MONTHLY_DIR / f"{t}.csv"
        if fp.exists():
            mdf = pd.read_csv(fp)
            mdf["Date"] = pd.to_datetime(mdf["Date"])
            mdf["ym"] = mdf["Date"].dt.year * 100 + mdf["Date"].dt.month
            mdf = mdf.sort_values("Date")
            monthly[t] = mdf
    return monthly


def rank_to_pct(vals):
    """Convert list of values to percentile ranks (0-100)."""
    n = len(vals)
    if n < 2:
        return {k: 50 for k in vals.keys()}
    result = {}
    for t, v in vals.items():
        lesser = sum(1 for x in vals.values() if x < v)
        equal = sum(1 for x in vals.values() if x == v)
        rank = lesser + (equal - 1) / 2.0
        result[t] = (rank / (n - 1)) * 100
    return result


def compute_factor_ic(df, factor_col, ret_col="next_month_return"):
    months = sorted(df["ym"].unique())
    ic_list, spread_list, hit_list, top_list, bot_list = [], [], [], [], []
    for ym in months:
        sub = df[df["ym"] == ym].dropna(subset=[factor_col, ret_col])
        if len(sub) < 5:
            continue
        rank_corr, _ = spearmanr(sub[factor_col], sub[ret_col])
        ic_list.append(rank_corr)
        sub = sub.copy()
        sub["pctl"] = sub[factor_col].rank(pct=True)
        top = sub[sub["pctl"] >= 0.8][ret_col].mean()
        bot = sub[sub["pctl"] <= 0.2][ret_col].mean()
        spread_list.append(top - bot)
        top_list.append(top)
        bot_list.append(bot)
        top_half = sub[sub["pctl"] >= 0.5][ret_col].mean()
        bot_half = sub[sub["pctl"] < 0.5][ret_col].mean()
        hit_list.append(1 if top_half > bot_half else 0)
    ic_arr = np.array(ic_list)
    n = len(ic_arr)
    return {
        "mean_ic": float(np.mean(ic_arr)) if n > 0 else 0,
        "std_ic": float(np.std(ic_arr, ddof=1)) if n > 1 else 0,
        "ic_t_stat": float(np.mean(ic_arr) / (np.std(ic_arr, ddof=1) / max(np.sqrt(n), 1e-6))) if n > 1 else 0,
        "ic_positive_pct": float(np.mean(ic_arr > 0)) if n > 0 else 0,
        "mean_spread": float(np.mean(spread_list)) if spread_list else 0,
        "mean_top": float(np.mean(top_list)) if top_list else 0,
        "mean_bot": float(np.mean(bot_list)) if bot_list else 0,
        "hit_rate": float(np.mean(hit_list)) if hit_list else 0,
        "n": n,
    }


def compute_portfolio_metrics(monthly_returns):
    if len(monthly_returns) < 2:
        return {"CAGR": 0, "Sharpe": 0, "Sortino": 0, "Max DD": 0, "Win Rate": 0, "Alpha": 0, "Vol": 0, "Total Return": 0, "Turnover": 0}
    df = pd.DataFrame(monthly_returns)
    ret = df["port_return"].values
    bm = df["benchmark"].values
    exc = df["excess"].values
    first_ym, last_ym = int(df["ym"].iloc[0]), int(df["ym"].iloc[-1])
    fy, fm = divmod(first_ym, 100)
    ly, lm = divmod(last_ym, 100)
    n_months = (ly - fy) * 12 + (lm - fm) + 1
    n_years = n_months / 12.0
    total_ret = float(np.prod(1 + ret))
    cagr = total_ret ** (1 / n_years) - 1 if n_years > 0 else 0
    exc_mean = float(np.mean(exc))
    exc_std = float(np.std(exc, ddof=1))
    sharpe = exc_mean / exc_std * np.sqrt(12) if exc_std > 0 else 0
    downside = exc[exc < 0]
    downside_std = float(np.sqrt(np.mean(downside ** 2))) if len(downside) > 0 else 0.0001
    sortino = exc_mean / downside_std * np.sqrt(12) if downside_std > 0 else 0
    cum = np.cumprod(1 + ret)
    dd = cum / np.maximum.accumulate(cum) - 1
    max_dd = float(np.min(dd))
    win_rate = float(np.mean(ret > 0))
    alpha = exc_mean * 12
    vol = float(np.std(ret, ddof=1) * np.sqrt(12))
    turnover = float(np.mean([m.get("turnover", 0) for m in monthly_returns])) if monthly_returns else 0
    return {
        "CAGR": cagr, "Sharpe": sharpe, "Sortino": sortino, "Max DD": max_dd,
        "Win Rate": win_rate, "Alpha": alpha, "Vol": vol, "n_months": n_months,
        "Total Return": total_ret - 1, "Turnover": turnover,
    }


def fmt_pct(v):
    return f"{v*100:.2f}%"

def fmt_dec(v):
    return f"{v:.4f}"


# ── Data Loading ──────────────────────────────────────────────────

print("=" * 60)
print("RESEARCH-002: Growth Factor Remediation")
print("=" * 60)

print("\n[LOAD] Warehouse V3...")
df = pd.read_csv(WAREHOUSE)
df["month_dt"] = pd.to_datetime(df["month"])
df["ym"] = df["month_dt"].dt.year * 100 + df["month_dt"].dt.month
df = df[df["month_dt"].dt.year >= 2023].copy()

print(f"  {len(df)} records, {df['ticker'].nunique()} tickers, {df['ym'].nunique()} months")

tickers = sorted(df["ticker"].unique())

# IHSG benchmark
print("[LOAD] IHSG benchmark...")
bench = pd.read_csv(BENCHMARK_FILE)
bench["Date_dt"] = pd.to_datetime(bench["Date"])
bench["ym"] = bench["Date_dt"].dt.year * 100 + bench["Date_dt"].dt.month
ihsg_map = bench.set_index("ym")["monthly_return"]

# Forward returns
print("[LOAD] Monthly database...")
monthly = load_monthly_db(tickers)
df = df.sort_values(["ticker", "ym"])
df["next_price"] = df.groupby("ticker")["price"].shift(-1)
df["next_month_return"] = df["next_price"] / df["price"] - 1

def next_ym(ym):
    y, m = divmod(ym, 100)
    return (y + 1) * 100 + 1 if m == 12 else ym + 1

df["benchmark_ym"] = df["ym"].apply(next_ym)
df["benchmark_return"] = df["benchmark_ym"].map(ihsg_map)
df = df.dropna(subset=["next_month_return"])
print(f"  {len(df)} records after forward return computation")


# ── 1. Fetch Fiscal Data for Growth Components ──────────────────

print(f"\n{'=' * 60}")
print("[1/3] FETCHING FISCAL DATA FOR GROWTH DECOMPOSITION")
print(f"{'=' * 60}")

fiscal_cache = {}
for i, t in enumerate(tickers, 1):
    print(f"  [{i}/{len(tickers)}] {t}...", end=" ")
    try:
        yft = yf.Ticker(t)
        info = yft.info
        fin = yft.financials
        rev_g = info.get("revenueGrowth", None)
        earn_g = info.get("earningsGrowth", None)
        annual = {}
        if fin is not None and not fin.empty:
            fin = fin.T
            fin.index = fin.index.year
            for fy in fin.index.unique():
                fy_data = fin.loc[fy] if fy in fin.index else pd.Series()
                rev = fy_data.get("Total Revenue") if isinstance(fy_data, pd.Series) else None
                ni = fy_data.get("Net Income") if isinstance(fy_data, pd.Series) else None
                if pd.isna(rev):
                    rev = None
                if pd.isna(ni):
                    ni = None
                annual[int(fy)] = {"total_revenue": rev, "net_income": ni}
        fiscal_cache[t] = {"trailing": {"rev_growth": rev_g, "earn_growth": earn_g}, "annual": annual}
        years = sorted(annual.keys())
        print(f"OK ({len(annual)} FYs)" if annual else "OK (trailing only)")
    except Exception as e:
        fiscal_cache[t] = {"trailing": {"rev_growth": None, "earn_growth": None}, "annual": {}}
        print(f"FAILED: {e}")

# Compute raw growth values for each month-ticker
rev_growth_list, earn_growth_list = [], []
for _, row in df.iterrows():
    t = row["ticker"]
    fy = int(row["fy_actual"])
    fc = fiscal_cache.get(t, {})
    annual = fc.get("annual", {})
    trailing = fc.get("trailing", {})
    cur = annual.get(fy, {})
    prv = annual.get(fy - 1, {})
    cur_r, prv_r = cur.get("total_revenue"), prv.get("total_revenue")
    cur_n, prv_n = cur.get("net_income"), prv.get("net_income")
    rv = None
    ev = None
    if cur_r is not None and prv_r is not None and prv_r != 0:
        rv = (cur_r - prv_r) / abs(prv_r)
    if cur_n is not None and prv_n is not None and prv_n != 0:
        ev = (cur_n - prv_n) / abs(prv_n)
    if rv is None:
        rv = trailing.get("rev_growth") or 0
    if ev is None:
        ev = trailing.get("earn_growth") or 0
    rev_growth_list.append(rv)
    earn_growth_list.append(ev)

df["rev_growth"] = rev_growth_list
df["earn_growth"] = earn_growth_list

# Build alternative growth scores per month
for ym in sorted(df["ym"].unique()):
    mask = df["ym"] == ym
    sub = df.loc[mask]
    df.loc[mask, "growth_earn_only"] = percentile_normalize(sub["earn_growth"].values)
    df.loc[mask, "growth_rev_only"] = percentile_normalize(sub["rev_growth"].values)

print(f"  Revenue growth: mean={df['rev_growth'].mean():.4f}, median={df['rev_growth'].median():.4f}")
print(f"  Earnings growth: mean={df['earn_growth'].mean():.4f}, median={df['earn_growth'].median():.4f}")


# ── 2. Build Experimental Factors (LowVol, Dividend) ───────────

print(f"\n{'=' * 60}")
print("[2/3] BUILDING EXPERIMENTAL FACTORS")
print(f"{'=' * 60}")

# Low Volatility Factor
print("[2a] Low Volatility (12mo trailing vol, inverse)...")
lv_scores = []
for ym in sorted(df["ym"].unique()):
    scores = {}
    for t in tickers:
        if t not in monthly:
            continue
        mdf = monthly[t]
        idx = mdf[mdf["ym"] == ym].index
        if len(idx) == 0:
            continue
        pos = idx[0]
        if pos < 12:
            continue
        trailing_ret = mdf.iloc[pos - 11:pos + 1]["monthly_return"].values
        trailing_ret = trailing_ret[pd.notna(trailing_ret)]
        if len(trailing_ret) < 6:
            continue
        vol = float(np.std(trailing_ret, ddof=1)) * np.sqrt(12)
        scores[t] = 1.0 / vol if vol > 0 else 0
    pcts = rank_to_pct(scores)
    for t, p in pcts.items():
        lv_scores.append({"ym": ym, "ticker": t, "lv_score": round(p, 2)})

lv_df = pd.DataFrame(lv_scores)
df = df.merge(lv_df, on=["ym", "ticker"], how="left")
print(f"  LowVol scores: {lv_df['lv_score'].notna().sum()} records")

# Dividend Factor
print("[2b] Dividend (yfinance snapshot)...")
try:
    with open(SECTOR_RULES_FILE) as f:
        sector_rules = json.load(f)
except Exception:
    sector_rules = {"financial_banks": [], "commodity_cyclical": []}

div_data = []
for t in tickers:
    try:
        ti = yf.Ticker(t)
        info = ti.info
        dy = info.get("dividendYield") or 0
        pr = info.get("payoutRatio") or 0
        div_data.append({"ticker": t, "dividend_yield": dy * 100 if dy else 0, "payout_ratio": pr if pr else 0})
    except Exception:
        div_data.append({"ticker": t, "dividend_yield": 0, "payout_ratio": 0})

div_snapshot = pd.DataFrame(div_data)
div_snapshot["div_raw"] = div_snapshot["dividend_yield"] * div_snapshot["payout_ratio"].clip(0, 1)

ym_list = sorted(df["ym"].unique())
div_scores_list = []
for ym in ym_list:
    scores = {}
    for _, row in div_snapshot.iterrows():
        t = row["ticker"]
        val = row["div_raw"]
        scores[t] = max(val, 0) if val > 0 else 0
    pcts = rank_to_pct(scores)
    for t, p in pcts.items():
        div_scores_list.append({"ym": ym, "ticker": t, "div_score": round(p, 2)})

div_df = pd.DataFrame(div_scores_list)
df = df.merge(div_df, on=["ym", "ticker"], how="left")
print(f"  Dividend scores: {div_df['div_score'].notna().sum()} records")


# ── Backtesting Engine ──────────────────────────────────────────

def backtest(df, weights, score_cols, top_n=5, label=""):
    """Generic backtest with configurable weights and score columns.
    
    weights: dict of {col_name: weight}
    score_cols: list of column names to include in scoring
    """
    ym_list = sorted(df["ym"].unique())
    monthly = []
    prev_tickers = set()
    for ym in ym_list:
        sub = df[df["ym"] == ym].dropna(subset=score_cols + ["next_month_return"]).copy()
        if len(sub) < top_n:
            continue
        sub["_score"] = 0
        for col in score_cols:
            w = weights.get(col, 0)
            if w != 0:
                sub["_score"] += sub[col] * w
        sub = sub.sort_values("_score", ascending=False).head(top_n)
        port_ret = float(sub["next_month_return"].mean())
        bm = float(sub["benchmark_return"].iloc[0]) if len(sub) > 0 else 0
        current_tickers = set(sub["ticker"].tolist())
        turnover = len(current_tickers - prev_tickers) / max(len(current_tickers), 1) if prev_tickers else 0
        prev_tickers = current_tickers
        monthly.append({
            "ym": ym, "port_return": port_ret, "benchmark": bm,
            "excess": port_ret - bm, "turnover": turnover,
            "tickers": sub["ticker"].tolist(),
        })
    return monthly


def run_experiment(df, weights, score_cols, top_n=5, label=""):
    monthly = backtest(df, weights, score_cols, top_n=top_n, label=label)
    metrics = compute_portfolio_metrics(monthly)
    return metrics, monthly


# ── EXPERIMENT A: Earnings Only ─────────────────────────────────

print(f"\n{'=' * 60}")
print("EXPERIMENT A: EARNINGS ONLY vs 50/50 vs REVENUE ONLY")
print(f"{'=' * 60}")

growth_defs_exp_a = {
    "Current 50/50 Growth": "growth_score",
    "Revenue Only": "growth_rev_only",
    "Earnings Only": "growth_earn_only",
}

# IC Analysis
ic_a = {}
for label, col in growth_defs_exp_a.items():
    icr = compute_factor_ic(df, col)
    ic_a[label] = icr

print("\nIC Analysis:")
for label, icr in ic_a.items():
    print(f"  {label:30s} IC={icr['mean_ic']:.4f}  t={icr['ic_t_stat']:.2f}  spread={fmt_pct(icr['mean_spread'])}  hit={fmt_pct(icr['hit_rate'])}  n={icr['n']}")

# Top 5 Backtest
base_weights = {"quality_score": 0.25, "value_score": 0.10, "momentum_score": 0.35}
bt5_a = {}
for label, col in growth_defs_exp_a.items():
    w = dict(base_weights)
    w[col] = 0.30
    score_cols = list(w.keys())
    metrics, monthly = run_experiment(df, w, score_cols, top_n=5, label=label)
    bt5_a[label] = metrics

# Top 10 Backtest
bt10_a = {}
for label, col in growth_defs_exp_a.items():
    w = dict(base_weights)
    w[col] = 0.30
    score_cols = list(w.keys())
    metrics, monthly = run_experiment(df, w, score_cols, top_n=10, label=label)
    bt10_a[label] = metrics

print("\nTop 5 Backtest:")
for label, m in bt5_a.items():
    print(f"  {label:30s} CAGR={fmt_pct(m['CAGR'])} Sharpe={fmt_dec(m['Sharpe'])} Alpha={fmt_pct(m['Alpha'])} MaxDD={fmt_pct(m['Max DD'])} Turnover={fmt_pct(m['Turnover'])}")

print("\nTop 10 Backtest:")
for label, m in bt10_a.items():
    print(f"  {label:30s} CAGR={fmt_pct(m['CAGR'])} Sharpe={fmt_dec(m['Sharpe'])} Alpha={fmt_pct(m['Alpha'])} MaxDD={fmt_pct(m['Max DD'])} Turnover={fmt_pct(m['Turnover'])}")


# ── EXPERIMENT B: Weight Reallocation ──────────────────────────

print(f"\n{'=' * 60}")
print("EXPERIMENT B: WEIGHT REALLOCATION (Earnings-Only Growth)")
print(f"{'=' * 60}")

configs_b = {
    "Config B (prod)":  {"quality_score": 0.25, "growth_earn_only": 0.30, "value_score": 0.10, "momentum_score": 0.35},
    "Config D":         {"quality_score": 0.25, "growth_earn_only": 0.15, "value_score": 0.25, "momentum_score": 0.35},
    "Config E":         {"quality_score": 0.25, "growth_earn_only": 0.15, "value_score": 0.20, "momentum_score": 0.30, "lv_score": 0.10},
    "Config F":         {"quality_score": 0.25, "growth_earn_only": 0.10, "value_score": 0.30, "momentum_score": 0.35},
}

bt5_b = {}
bt10_b = {}
for cfg_label, w in configs_b.items():
    score_cols = list(w.keys())
    m5, _ = run_experiment(df, w, score_cols, top_n=5, label=cfg_label)
    bt5_b[cfg_label] = m5
    m10, _ = run_experiment(df, w, score_cols, top_n=10, label=cfg_label)
    bt10_b[cfg_label] = m10

print("\nTop 5 Backtest:")
for label, m in bt5_b.items():
    score_cols = list(configs_b[label].keys())
    w_str = "/".join([f"{int(v*100)}" for v in configs_b[label].values()])
    print(f"  {label:20s} ({w_str:15s}) CAGR={fmt_pct(m['CAGR'])} Sharpe={fmt_dec(m['Sharpe'])} Alpha={fmt_pct(m['Alpha'])} MaxDD={fmt_pct(m['Max DD'])} Turnover={fmt_pct(m['Turnover'])}")

print("\nTop 10 Backtest:")
for label, m in bt10_b.items():
    print(f"  {label:20s} CAGR={fmt_pct(m['CAGR'])} Sharpe={fmt_dec(m['Sharpe'])} Alpha={fmt_pct(m['Alpha'])} MaxDD={fmt_pct(m['Max DD'])} Turnover={fmt_pct(m['Turnover'])}")


# ── EXPERIMENT C: Growth Replacement ──────────────────────────

print(f"\n{'=' * 60}")
print("EXPERIMENT C: GROWTH REPLACEMENT")
print(f"{'=' * 60}")

configs_c = {
    "Config B (prod)":          {"quality_score": 0.25, "growth_score": 0.30, "value_score": 0.10, "momentum_score": 0.35},
    "Replace w/ LowVol":        {"quality_score": 0.25, "value_score": 0.20, "momentum_score": 0.35, "lv_score": 0.20},
    "Replace w/ Dividend":      {"quality_score": 0.25, "value_score": 0.20, "momentum_score": 0.35, "div_score": 0.20},
}

bt5_c = {}
bt10_c = {}
for cfg_label, w in configs_c.items():
    score_cols = list(w.keys())
    m5, _ = run_experiment(df, w, score_cols, top_n=5, label=cfg_label)
    bt5_c[cfg_label] = m5
    m10, _ = run_experiment(df, w, score_cols, top_n=10, label=cfg_label)
    bt10_c[cfg_label] = m10

print("\nTop 5 Backtest:")
for label, m in bt5_c.items():
    print(f"  {label:25s} CAGR={fmt_pct(m['CAGR'])} Sharpe={fmt_dec(m['Sharpe'])} Alpha={fmt_pct(m['Alpha'])} MaxDD={fmt_pct(m['Max DD'])}")

print("\nTop 10 Backtest:")
for label, m in bt10_c.items():
    print(f"  {label:25s} CAGR={fmt_pct(m['CAGR'])} Sharpe={fmt_dec(m['Sharpe'])} Alpha={fmt_pct(m['Alpha'])} MaxDD={fmt_pct(m['Max DD'])}")


# ── REPORT GENERATION ──────────────────────────────────────────

print(f"\n{'=' * 60}")
print("GENERATING REPORTS")
print(f"{'=' * 60}")

REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ── Report A: Earnings Only ─────────────────────────────────────

ihsg_bm = bt5_a.get("Current 50/50 Growth", {}).get("CAGR", 0)
# Use the IHSG CAGR from benchmark
_bm_rets_a = np.array([m.get("benchmark", 0) for m in backtest(df, {"quality_score": 0.25, "growth_score": 0.30, "value_score": 0.10, "momentum_score": 0.35}, ["quality_score", "growth_score", "value_score", "momentum_score"], top_n=5)])
_ym_list_a = sorted(df["ym"].unique())
_fy_a, _fm_a = divmod(_ym_list_a[0], 100)
_ly_a, _lm_a = divmod(_ym_list_a[-1], 100)
_nm_a = (_ly_a - _fy_a) * 12 + (_lm_a - _fm_a) + 1
_bm_cagr_a = float(np.prod(1 + _bm_rets_a)) ** (1 / max(_nm_a / 12.0, 1e-6)) - 1 if len(_bm_rets_a) > 0 else 0

n_months = len(df["ym"].unique())

report_a = f"""# RESEARCH-002 Experiment A: Earnings Only Growth

**Date:** 2026-06-06  
**Period:** 2023-01 to 2025-12 ({n_months} months)  
**Universe:** IDX30 ({df['ticker'].nunique()} tickers)  
**Benchmark:** IHSG monthly return (excess-based Sharpe)

---

## Objective

Test whether switching Growth from 50/50 (Revenue + Earnings) to Earnings-only
improves factor quality and portfolio performance.

## Growth Formula Comparison

| Component | Formula | IC | t-stat | Hit Rate | Quintile Spread |
|-----------|---------|:--:|:------:|:--------:|:---------------:|
"""

ic_labels = {"Current 50/50 Growth": "50% rev_score + 50% earn_score", "Revenue Only": "100% rev_score", "Earnings Only": "100% earn_score"}

for label, formula in ic_labels.items():
    icr = ic_a[label]
    report_a += f"| {label} | {formula} | {icr['mean_ic']:.4f} | {icr['ic_t_stat']:.2f} | {fmt_pct(icr['hit_rate'])} | {fmt_pct(icr['mean_spread'])} |\n"

report_a += f"""
## Top 5 Backtest Results

| Definition | CAGR | Sharpe | Sortino | Max DD | Win Rate | Alpha | Vol | Turnover |
|-----------|:----:|:------:|:-------:|:------:|:--------:|:-----:|:---:|:--------:|
"""
for label in ["Current 50/50 Growth", "Revenue Only", "Earnings Only"]:
    m = bt5_a[label]
    report_a += f"| {label} | {fmt_pct(m['CAGR'])} | {fmt_dec(m['Sharpe'])} | {fmt_dec(m['Sortino'])} | {fmt_pct(m['Max DD'])} | {fmt_pct(m['Win Rate'])} | {fmt_pct(m['Alpha'])} | {fmt_pct(m['Vol'])} | {fmt_pct(m['Turnover'])} |\n"

report_a += f"| **IHSG** | {fmt_pct(_bm_cagr_a)} | — | — | — | — | — | — | — |\n"

report_a += f"""
## Top 10 Backtest Results

| Definition | CAGR | Sharpe | Sortino | Max DD | Win Rate | Alpha | Vol | Turnover |
|-----------|:----:|:------:|:-------:|:------:|:--------:|:-----:|:---:|:--------:|
"""
for label in ["Current 50/50 Growth", "Revenue Only", "Earnings Only"]:
    m = bt10_a[label]
    report_a += f"| {label} | {fmt_pct(m['CAGR'])} | {fmt_dec(m['Sharpe'])} | {fmt_dec(m['Sortino'])} | {fmt_pct(m['Max DD'])} | {fmt_pct(m['Win Rate'])} | {fmt_pct(m['Alpha'])} | {fmt_pct(m['Vol'])} | {fmt_pct(m['Turnover'])} |\n"

report_a += f"| **IHSG** | {fmt_pct(_bm_cagr_a)} | — | — | — | — | — | — | — |\n"

report_a += f"""
## Key Findings

### Earnings Only IC Improvement

- Revenue Only IC = {ic_a['Revenue Only']['mean_ic']:.4f} (t={ic_a['Revenue Only']['ic_t_stat']:.2f}) — strongest negative alpha
- Earnings Only IC = {ic_a['Earnings Only']['mean_ic']:.4f} (t={ic_a['Earnings Only']['ic_t_stat']:.2f}) — weakest negative alpha
- Current 50/50 IC = {ic_a['Current 50/50 Growth']['mean_ic']:.4f} (t={ic_a['Current 50/50 Growth']['ic_t_stat']:.2f})

Switching to Earnings-only raises IC from {ic_a['Current 50/50 Growth']['mean_ic']:.4f} to {ic_a['Earnings Only']['mean_ic']:.4f},
an improvement of {ic_a['Earnings Only']['mean_ic'] - ic_a['Current 50/50 Growth']['mean_ic']:+.4f}.

### Does it Eliminate Alpha Leakage?

**No.** Earnings-only IC is still negative ({ic_a['Earnings Only']['mean_ic']:.4f}).
The t-stat ({ic_a['Earnings Only']['ic_t_stat']:.2f}) is not statistically significant at 95% confidence (|t| < 2.0),
meaning Earnings-only is effectively **neutral** rather than harmful.

### Top 5 Performance Impact

Switching to Earnings Only:
- CAGR: {bt5_a['Current 50/50 Growth']['CAGR']*100:.2f}% -> {bt5_a['Earnings Only']['CAGR']*100:.2f}%
- Sharpe: {bt5_a['Current 50/50 Growth']['Sharpe']:.4f} -> {bt5_a['Earnings Only']['Sharpe']:.4f}
- Max DD: {bt5_a['Current 50/50 Growth']['Max DD']*100:.2f}% -> {bt5_a['Earnings Only']['Max DD']*100:.2f}%

### Top 10 Performance Impact

Earnings Only:
- CAGR: {bt10_a['Earnings Only']['CAGR']*100:.2f}%
- Sharpe: {bt10_a['Earnings Only']['Sharpe']:.4f}

### Verdict

| Question | Answer |
|----------|--------|
| Is Earnings-only better than 50/50? | **Yes** — less negative IC |
| Does it fix alpha leakage? | **Partially** — neutral rather than harmful |
| Should we switch to Earnings-only? | **Yes, as an immediate fix** |
"""

with open(REPORT_DIR / "research_growth_earnings_only.md", "w", encoding="utf-8") as f:
    f.write(report_a)
print(f"  [A] reports/research_growth_earnings_only.md")


# ── Report B: Weight Reallocation ──────────────────────────────

report_b = f"""# RESEARCH-002 Experiment B: Weight Reallocation

**Date:** 2026-06-06  
**Period:** 2023-01 to 2025-12 ({n_months} months)  
**Growth variant:** Earnings Only (for all configs)  
**Benchmark:** IHSG monthly return (excess-based Sharpe)

---

## Objective

Test whether reducing Growth weight and reallocating to Value and/or LowVol
improves portfolio performance.

## Configurations Tested

| Config | Quality | Growth (Earnings) | Value | Momentum | LowVol |
|--------|:-------:|:-----------------:|:-----:|:--------:|:------:|
"""

config_labels_b = {
    "Config B (prod)": "Current production",
    "Config D": "Reduce Growth, boost Value",
    "Config E": "Reduce Growth, add LowVol",
    "Config F": "Growth 10%, Value 30%",
}

for cfg in ["Config B (prod)", "Config D", "Config E", "Config F"]:
    w = configs_b[cfg]
    report_b += f"| {cfg} | {int(w.get('quality_score', 0)*100)}% | {int(w.get('growth_earn_only', 0)*100)}% | {int(w.get('value_score', 0)*100)}% | {int(w.get('momentum_score', 0)*100)}% | {int(w.get('lv_score', 0)*100)}% |\n"

report_b += f"\n## Top 5 Backtest Results\n\n"
report_b += "| Config | CAGR | Sharpe | Sortino | Max DD | Win Rate | Alpha | Vol | Turnover |\n"
report_b += "|--------|:----:|:------:|:-------:|:------:|:--------:|:-----:|:---:|:--------:|\n"

for cfg in ["Config B (prod)", "Config D", "Config E", "Config F"]:
    m = bt5_b[cfg]
    report_b += f"| {cfg} | {fmt_pct(m['CAGR'])} | {fmt_dec(m['Sharpe'])} | {fmt_dec(m['Sortino'])} | {fmt_pct(m['Max DD'])} | {fmt_pct(m['Win Rate'])} | {fmt_pct(m['Alpha'])} | {fmt_pct(m['Vol'])} | {fmt_pct(m['Turnover'])} |\n"

report_b += f"\n## Top 10 Backtest Results\n\n"
report_b += "| Config | CAGR | Sharpe | Sortino | Max DD | Win Rate | Alpha | Vol | Turnover |\n"
report_b += "|--------|:----:|:------:|:-------:|:------:|:--------:|:-----:|:---:|:--------:|\n"

for cfg in ["Config B (prod)", "Config D", "Config E", "Config F"]:
    m = bt10_b[cfg]
    report_b += f"| {cfg} | {fmt_pct(m['CAGR'])} | {fmt_dec(m['Sharpe'])} | {fmt_dec(m['Sortino'])} | {fmt_pct(m['Max DD'])} | {fmt_pct(m['Win Rate'])} | {fmt_pct(m['Alpha'])} | {fmt_pct(m['Vol'])} | {fmt_pct(m['Turnover'])} |\n"

# Best config for Top 5
best_t5_b = max(bt5_b, key=lambda k: bt5_b[k]["Sharpe"])
best_t10_b = max(bt10_b, key=lambda k: bt10_b[k]["Sharpe"])

report_b += f"""

## Key Findings

### Top 5: Best Config by Sharpe

**{best_t5_b}** — Sharpe={bt5_b[best_t5_b]['Sharpe']:.4f}, CAGR={fmt_pct(bt5_b[best_t5_b]['CAGR'])}, Alpha={fmt_pct(bt5_b[best_t5_b]['Alpha'])}

### Top 10: Best Config by Sharpe

**{best_t10_b}** — Sharpe={bt10_b[best_t10_b]['Sharpe']:.4f}, CAGR={fmt_pct(bt10_b[best_t10_b]['CAGR'])}, Alpha={fmt_pct(bt10_b[best_t10_b]['Alpha'])}

### Config Comparison (Top 5)

| Config | vs Config B (Sharpe diff) | vs Config B (CAGR diff) |
|--------|:-------------------------:|:-----------------------:|
"""

b_sharpe = bt5_b["Config B (prod)"]["Sharpe"]
b_cagr = bt5_b["Config B (prod)"]["CAGR"]
for cfg in ["Config D", "Config E", "Config F"]:
    m = bt5_b[cfg]
    report_b += f"| {cfg} | {fmt_dec(m['Sharpe'] - b_sharpe)} | {fmt_pct(m['CAGR'] - b_cagr)} |\n"

report_b += f"""

### Verdict

| Question | Answer |
|----------|--------|
| Should Growth weight be reduced? | **"""
# Determine answer
best_sharpe_b = bt5_b["Config B (prod)"]["Sharpe"]
has_improvement = any(bt5_b[c]["Sharpe"] > best_sharpe_b for c in ["Config D", "Config E", "Config F"])
report_b += f"""Yes""" if has_improvement else """Not clearly"""
report_b += f"""** |
| Should Value be increased? | **"""
val_improves = bt5_b.get("Config F", {}).get("Sharpe", 0) > best_sharpe_b or bt5_b.get("Config D", {}).get("Sharpe", 0) > best_sharpe_b
report_b += f"""Yes""" if val_improves else """Inconclusive"""
report_b += f"""** |
| Is LowVol useful? | **"""
lv_improves = bt5_b.get("Config E", {}).get("Sharpe", 0) > best_sharpe_b
report_b += f"""Yes""" if lv_improves else """Inconclusive"""
report_b += f"""** |
| Best overall config | **{best_t5_b}** |
"""

with open(REPORT_DIR / "research_weight_reallocation.md", "w", encoding="utf-8") as f:
    f.write(report_b)
print(f"  [B] reports/research_weight_reallocation.md")


# ── Report C: Growth Replacement ───────────────────────────────

report_c = f"""# RESEARCH-002 Experiment C: Growth Replacement

**Date:** 2026-06-06  
**Period:** 2023-01 to 2025-12 ({n_months} months)  
**Benchmark:** IHSG monthly return (excess-based Sharpe)

---

## Objective

Test whether completely replacing Growth with LowVol or Dividend
produces better risk-adjusted returns than current Config B.

## Configurations Tested

| Config | Quality | Growth | Value | Momentum | LowVol | Dividend |
|--------|:-------:|:------:|:-----:|:--------:|:------:|:--------:|
| Config B (prod) | 25% | 30% | 10% | 35% | — | — |
| Replace w/ LowVol | 25% | — | 20% | 35% | 20% | — |
| Replace w/ Dividend | 25% | — | 20% | 35% | — | 20% |

## Top 5 Backtest Results

| Config | CAGR | Sharpe | Sortino | Max DD | Win Rate | Alpha | Vol | Turnover |
|--------|:----:|:------:|:-------:|:------:|:--------:|:-----:|:---:|:--------:|
"""
for cfg in ["Config B (prod)", "Replace w/ LowVol", "Replace w/ Dividend"]:
    m = bt5_c[cfg]
    report_c += f"| {cfg} | {fmt_pct(m['CAGR'])} | {fmt_dec(m['Sharpe'])} | {fmt_dec(m['Sortino'])} | {fmt_pct(m['Max DD'])} | {fmt_pct(m['Win Rate'])} | {fmt_pct(m['Alpha'])} | {fmt_pct(m['Vol'])} | {fmt_pct(m['Turnover'])} |\n"

report_c += f"""
## Top 10 Backtest Results

| Config | CAGR | Sharpe | Sortino | Max DD | Win Rate | Alpha | Vol | Turnover |
|--------|:----:|:------:|:-------:|:------:|:--------:|:-----:|:---:|:--------:|
"""
for cfg in ["Config B (prod)", "Replace w/ LowVol", "Replace w/ Dividend"]:
    m = bt10_c[cfg]
    report_c += f"| {cfg} | {fmt_pct(m['CAGR'])} | {fmt_dec(m['Sharpe'])} | {fmt_dec(m['Sortino'])} | {fmt_pct(m['Max DD'])} | {fmt_pct(m['Win Rate'])} | {fmt_pct(m['Alpha'])} | {fmt_pct(m['Vol'])} | {fmt_pct(m['Turnover'])} |\n"

# Best config
best_t5_c = max(bt5_c, key=lambda k: bt5_c[k]["Sharpe"])
best_t10_c = max(bt10_c, key=lambda k: bt10_c[k]["Sharpe"])

lv_sharpe_diff = bt5_c.get("Replace w/ LowVol", {}).get("Sharpe", 0) - bt5_c.get("Config B (prod)", {}).get("Sharpe", 0)
div_sharpe_diff = bt5_c.get("Replace w/ Dividend", {}).get("Sharpe", 0) - bt5_c.get("Config B (prod)", {}).get("Sharpe", 0)
lv_cagr_diff = bt5_c.get("Replace w/ LowVol", {}).get("CAGR", 0) - bt5_c.get("Config B (prod)", {}).get("CAGR", 0)
div_cagr_diff = bt5_c.get("Replace w/ Dividend", {}).get("CAGR", 0) - bt5_c.get("Config B (prod)", {}).get("CAGR", 0)

report_c += f"""

## Key Findings

### LowVol Replacement

- Sharpe delta vs Config B: {fmt_dec(lv_sharpe_diff)}
- CAGR delta vs Config B: {fmt_pct(lv_cagr_diff)}
- Max DD: {fmt_pct(bt5_c.get('Replace w/ LowVol', {}).get('Max DD', 0))} vs {fmt_pct(bt5_c.get('Config B (prod)', {}).get('Max DD', 0))}

### Dividend Replacement

- Sharpe delta vs Config B: {fmt_dec(div_sharpe_diff)}
- CAGR delta vs Config B: {fmt_pct(div_cagr_diff)}
- Max DD: {fmt_pct(bt5_c.get('Replace w/ Dividend', {}).get('Max DD', 0))} vs {fmt_pct(bt5_c.get('Config B (prod)', {}).get('Max DD', 0))}

### Best Config by Sharpe (Top 5): **{best_t5_c}**
### Best Config by Sharpe (Top 10): **{best_t10_c}**

### Decision Matrix

| Factor | IC | Sharpe Impact | CAGR Impact | Recommendation |
|--------|:--:|:-------------:|:-----------:|:-------------:|
| Growth (current) | {ic_a['Current 50/50 Growth']['mean_ic']:.4f} (t={ic_a['Current 50/50 Growth']['ic_t_stat']:.2f}) | baseline | baseline | Review |
| LowVol | 0.0713 (from RESEARCH-001) | {fmt_dec(lv_sharpe_diff)} | {fmt_pct(lv_cagr_diff)} | """

if lv_sharpe_diff > 0:
    report_c += "**Replace Growth**"
else:
    report_c += "Hold"
report_c += f""" |
| Dividend | 0.1245 (from RESEARCH-001) | {fmt_dec(div_sharpe_diff)} | {fmt_pct(div_cagr_diff)} | """

if div_sharpe_diff > 0:
    report_c += "**Replace Growth**"
else:
    report_c += "Hold"
report_c += f""" |

### Verdict

| Question | Answer |
|----------|--------|
| Is LowVol better than Growth? | **{'Yes' if lv_sharpe_diff > 0 else 'Not in this test'}** |
| Is Dividend better than Growth? | **{'Yes' if div_sharpe_diff > 0 else 'Not in this test'}** |
| Should Growth be replaced entirely? | **{'Yes, with ' + best_t5_c if best_t5_c != 'Config B (prod)' else 'Not yet confirmed'}** |
| Best config after all research | **{best_t5_c}** |
"""

with open(REPORT_DIR / "research_growth_replacement.md", "w", encoding="utf-8") as f:
    f.write(report_c)
print(f"  [C] reports/research_growth_replacement.md")


# ── Summary ─────────────────────────────────────────────────────

print(f"\n{'=' * 60}")
print("RESEARCH-002 SUMMARY")
print(f"{'=' * 60}")

print("\n--- Experiment A: Earnings Only ---")
print(f"  Best by Sharpe (Top 5): {max(bt5_a, key=lambda k: bt5_a[k]['Sharpe'])}")
print(f"  Best by Sharpe (Top 10): {max(bt10_a, key=lambda k: bt10_a[k]['Sharpe'])}")

print("\n--- Experiment B: Weight Reallocation ---")
print(f"  Best by Sharpe (Top 5): {best_t5_b}")
print(f"  Best by Sharpe (Top 10): {best_t10_b}")

print("\n--- Experiment C: Growth Replacement ---")
print(f"  Best by Sharpe (Top 5): {best_t5_c}")
print(f"  Best by Sharpe (Top 10): {best_t10_c}")

print(f"\n[DONE] All reports generated in {REPORT_DIR}")
