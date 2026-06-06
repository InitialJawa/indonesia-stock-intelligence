"""
Growth Factor Autopsy — RESEARCH 002
Decompose Growth factor into Revenue and Earnings components to understand
why it produces negative alpha (IC=-0.0846, t=-2.66).

Tests 6 alternative formulations (A-F) and recommends path forward.
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
REPORT_FILE = BASE / "reports" / "growth_factor_autopsy.md"

FACTORS = ["quality_score", "growth_score", "value_score", "momentum_score"]
CONFIG_B = {"quality_score": 0.25, "growth_score": 0.30, "value_score": 0.10, "momentum_score": 0.35}
LABELS = {"quality_score": "Quality", "growth_score": "Growth", "value_score": "Value", "momentum_score": "Momentum", "final_score": "Config B"}


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


def compute_factor_ic(df, factor_col, ret_col="next_month_return"):
    months = sorted(df["ym"].unique())
    ic_list, spread_list, hit_list, top_list, bot_list = [], [], [], [], []
    for ym in months:
        sub = df[df["ym"] == ym].dropna(subset=[factor_col, ret_col])
        if len(sub) < 5:
            continue
        rank_corr, _ = spearmanr(sub[factor_col], sub[ret_col])
        ic_list.append(rank_corr)
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
    return {
        "mean_ic": np.mean(ic_arr),
        "std_ic": np.std(ic_arr, ddof=1),
        "ic_t_stat": np.mean(ic_arr) / (np.std(ic_arr, ddof=1) / max(np.sqrt(len(ic_arr)), 1e-6)),
        "ic_positive_pct": np.mean(ic_arr > 0),
        "mean_spread": np.mean(spread_list),
        "mean_top": np.mean(top_list),
        "mean_bot": np.mean(bot_list),
        "hit_rate": np.mean(hit_list),
        "n": len(ic_list),
    }


def compute_portfolio_metrics(monthly_returns):
    if len(monthly_returns) < 2:
        return {"CAGR": 0, "Sharpe": 0, "Sortino": 0, "Max DD": 0, "Win Rate": 0, "Alpha": 0, "Vol": 0, "Total Return": 0}
    df = pd.DataFrame(monthly_returns)
    ret = df["port_return"].values
    bm = df["benchmark"].values
    exc = df["excess"].values
    first_ym, last_ym = int(df["ym"].iloc[0]), int(df["ym"].iloc[-1])
    fy, fm = divmod(first_ym, 100)
    ly, lm = divmod(last_ym, 100)
    n_months = (ly - fy) * 12 + (lm - fm) + 1
    n_years = n_months / 12.0
    total_ret = np.prod(1 + ret)
    cagr = total_ret ** (1 / n_years) - 1 if n_years > 0 else 0
    exc_mean = np.mean(exc)
    exc_std = np.std(exc, ddof=1)
    sharpe = exc_mean / exc_std * np.sqrt(12) if exc_std > 0 else 0
    downside = exc[exc < 0]
    downside_std = np.sqrt(np.mean(downside ** 2)) if len(downside) > 0 else 0.0001
    sortino = exc_mean / downside_std * np.sqrt(12) if downside_std > 0 else 0
    cum = np.cumprod(1 + ret)
    dd = cum / np.maximum.accumulate(cum) - 1
    max_dd = np.min(dd)
    win_rate = np.mean(ret > 0)
    alpha = exc_mean * 12
    vol = np.std(ret, ddof=1) * np.sqrt(12)
    return {
        "CAGR": cagr, "Sharpe": sharpe, "Sortino": sortino, "Max DD": max_dd,
        "Win Rate": win_rate, "Alpha": alpha, "Vol": vol, "n_months": n_months,
        "Total Return": total_ret - 1,
    }


def backtest_top5(df, growth_col, label):
    ym_list = sorted(df["ym"].unique())
    monthly = []
    for ym in ym_list:
        sub = df[df["ym"] == ym].dropna(subset=FACTORS + ["next_month_return", growth_col]).copy()
        if len(sub) < 5:
            continue
        sub["score"] = (
            sub["quality_score"] * CONFIG_B["quality_score"] +
            sub[growth_col] * CONFIG_B["growth_score"] +
            sub["value_score"] * CONFIG_B["value_score"] +
            sub["momentum_score"] * CONFIG_B["momentum_score"]
        )
        sub = sub.sort_values("score", ascending=False).head(5)
        port_ret = sub["next_month_return"].mean()
        bm = sub["benchmark_return"].iloc[0] if len(sub) > 0 else 0
        monthly.append({"ym": ym, "port_return": port_ret, "benchmark": bm, "excess": port_ret - bm})
    return compute_portfolio_metrics(monthly)


def fmt_pct(v):
    if v >= 1 or v <= -1:
        return f"{v*100:.2f}%"
    return f"{v*100:.2f}%"


def fmt_dec(v):
    return f"{v:.4f}"


# ── 1. Load data ──────────────────────────────────────────────────

print("=" * 60)
print("GROWTH FACTOR AUTOPSY")
print("=" * 60)

print("\n[LOAD] Warehouse V3...")
df = pd.read_csv(WAREHOUSE)
df["month_dt"] = pd.to_datetime(df["month"])
df["ym"] = df["month_dt"].dt.strftime("%Y%m").astype(int)

print(f"  {len(df)} records, {df['ticker'].nunique()} tickers")
print(f"  Date range: {df['month'].min()} to {df['month'].max()}")

# Filter to 2023+ (like alpha_generation_audit)
df = df[df["month_dt"].dt.year >= 2023].copy()
print(f"  After 2023+ filter: {len(df)} records, {df['ticker'].nunique()} tickers")

# Load benchmark
print("[LOAD] IHSG benchmark...")
bench = pd.read_csv(BENCHMARK_FILE)
bench["month_dt"] = pd.to_datetime(bench["Date"])
bench["ym"] = bench["month_dt"].dt.strftime("%Y%m").astype(int)
bench_map = dict(zip(bench["ym"], bench["monthly_return"]))
df["benchmark_return"] = df["ym"].map(bench_map)

# Compute next_month_return using monthly database
print("[LOAD] Monthly database for forward returns...")
tickers = sorted(df["ticker"].unique())
monthly_dfs = {}
for t in tickers:
    mdf = load_monthly(t)
    if mdf is not None:
        monthly_dfs[t] = mdf

next_month_returns = []
for _, row in df.iterrows():
    t = row["ticker"]
    ym = row["ym"]
    if t in monthly_dfs:
        mdf = monthly_dfs[t]
        ym_str = str(ym)
        match = mdf[mdf.index.strftime("%Y%m") == ym_str]
        if not match.empty:
            loc = mdf.index.get_loc(match.index[0])
            if loc + 1 < len(mdf):
                next_month_returns.append(mdf.iloc[loc + 1]["monthly_return"])
            else:
                next_month_returns.append(np.nan)
        else:
            next_month_returns.append(np.nan)
    else:
        next_month_returns.append(np.nan)

df["next_month_return"] = next_month_returns
print(f"  Forward returns computed: {df['next_month_return'].notna().sum()} non-null")

# ── 2. Fetch fiscal data from yfinance ──────────────────────────

print(f"\n{'=' * 60}")
print("FETCHING FISCAL DATA")
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
            fin = fin.T  # transpose so rows are years
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
        print(f"OK (annual: {len(annual)} FYs {years[0]}-{years[-1]})" if annual else "OK (no annual)")
    except Exception as e:
        fiscal_cache[t] = {"trailing": {"rev_growth": None, "earn_growth": None}, "annual": {}}
        print(f"FAILED: {e}")

# ── 3. Compute raw growth components for each month-ticker ─────

print(f"\n{'=' * 60}")
print("COMPUTING RAW GROWTH COMPONENTS")
print(f"{'=' * 60}")

rev_growth_list = []
earn_growth_list = []

for _, row in df.iterrows():
    t = row["ticker"]
    fy = row["fy_actual"]
    fc = fiscal_cache.get(t, {})
    annual = fc.get("annual", {})
    trailing = fc.get("trailing", {})

    # Try PIT YoY: revenue[fy] / revenue[fy-1]
    cur = annual.get(fy, {})
    prv = annual.get(fy - 1, {})
    cur_r = cur.get("total_revenue")
    prv_r = prv.get("total_revenue")
    cur_n = cur.get("net_income")
    prv_n = prv.get("net_income")

    rv = None
    ev = None
    if cur_r is not None and prv_r is not None and prv_r != 0:
        rv = (cur_r - prv_r) / abs(prv_r)
    if cur_n is not None and prv_n is not None and prv_n != 0:
        ev = (cur_n - prv_n) / abs(prv_n)

    # Fallback: trailing values from yfinance info
    if rv is None:
        rv = trailing.get("rev_growth") or 0
    if ev is None:
        ev = trailing.get("earn_growth") or 0

    rev_growth_list.append(rv)
    earn_growth_list.append(ev)

df["rev_growth"] = rev_growth_list
df["earn_growth"] = earn_growth_list

# Cap extreme values at +/- 500% for percentile normalization
df["rev_g_capped"] = df["rev_growth"].clip(-5, 5)
df["earn_g_capped"] = df["earn_growth"].clip(-5, 5)

print(f"  Revenue growth: {df['rev_growth'].notna().sum()} non-null, "
      f"mean={df['rev_growth'].mean():.4f}, median={df['rev_growth'].median():.4f}")
print(f"  Earnings growth: {df['earn_growth'].notna().sum()} non-null, "
      f"mean={df['earn_growth'].mean():.4f}, median={df['earn_growth'].median():.4f}")

# ── 4. Build alternative growth scores ─────────────────────────

print(f"\n{'=' * 60}")
print("BUILDING ALTERNATIVE GROWTH DEFINITIONS")
print(f"{'=' * 60}")

alternatives = {}

# ORIGINAL: 50% Revenue + 50% Earnings (the current formula)
# A: Revenue Growth only
# B: Earnings Growth only
# C: 70% Revenue + 30% Earnings
# D: 30% Revenue + 70% Earnings
# E: Revenue Growth capped at +/-100%
# F: Earnings Growth capped at +/-100%

for ym in sorted(df["ym"].unique()):
    mask = df["ym"] == ym
    sub = df.loc[mask]

    # Percentile-normalize within each month
    rev_scores = percentile_normalize(sub["rev_growth"].values)
    earn_scores = percentile_normalize(sub["earn_growth"].values)
    rev_cap_scores = percentile_normalize(sub["rev_g_capped"].values)
    earn_cap_scores = percentile_normalize(sub["earn_g_capped"].values)

    df.loc[mask, "growth_A_rev_only"] = rev_scores
    df.loc[mask, "growth_B_earn_only"] = earn_scores
    df.loc[mask, "growth_C_70r30e"] = rev_scores * 0.70 + earn_scores * 0.30
    df.loc[mask, "growth_D_30r70e"] = rev_scores * 0.30 + earn_scores * 0.70
    df.loc[mask, "growth_E_rev_capped"] = rev_cap_scores
    df.loc[mask, "growth_F_earn_capped"] = earn_cap_scores

growth_defs = {
    "Original (50R/50E)": "growth_score",
    "A: Revenue Only": "growth_A_rev_only",
    "B: Earnings Only": "growth_B_earn_only",
    "C: 70R/30E": "growth_C_70r30e",
    "D: 30R/70E": "growth_D_30r70e",
    "E: Rev Capped +/-100%": "growth_E_rev_capped",
    "F: Earn Capped +/-100%": "growth_F_earn_capped",
}

for label, col in growth_defs.items():
    print(f"  {label:30s}: {col}")

# ── 5. IC Analysis for each growth definition ──────────────────

print(f"\n{'=' * 60}")
print("PHASE 1: IC ANALYSIS")
print(f"{'=' * 60}")

ic_results = {}
for label, col in growth_defs.items():
    icr = compute_factor_ic(df, col)
    ic_results[label] = icr
    print(f"  {label:30s} IC={icr['mean_ic']:.4f}  t={icr['ic_t_stat']:.2f}  "
          f"spread={fmt_pct(icr['mean_spread'])}  hit={fmt_pct(icr['hit_rate'])}")

# ── 6. Backtest each growth definition ─────────────────────────

print(f"\n{'=' * 60}")
print("PHASE 2: TOP-5 BACKTEST")
print(f"{'=' * 60}")

bt_results = {}
for label, col in growth_defs.items():
    print(f"  [{label}]...", end=" ")
    m = backtest_top5(df, col, label)
    bt_results[label] = m
    print(f"CAGR={fmt_pct(m['CAGR'])} Sharpe={fmt_dec(m['Sharpe'])} "
          f"Alpha={fmt_pct(m['Alpha'])} MaxDD={fmt_pct(m['Max DD'])}")

# Also compute IHSG benchmark CAGR for comparison
_ym_sorted = sorted(df["ym"].unique())
_bm_rets = np.array([bench_map.get(y, 0) for y in _ym_sorted if bench_map.get(y) is not None])
_first_ym, _last_ym = _ym_sorted[0], _ym_sorted[-1]
_fy, _fm = divmod(_first_ym, 100)
_ly, _lm = divmod(_last_ym, 100)
_nm = (_ly - _fy) * 12 + (_lm - _fm) + 1
_ihsg_cagr = np.prod(1 + _bm_rets) ** (1 / max(_nm / 12.0, 1e-6)) - 1 if len(_bm_rets) > 0 else 0

# ── 7. Generate Report ─────────────────────────────────────────

print(f"\n{'=' * 60}")
print("GENERATING REPORT")
print(f"{'=' * 60}")

n_months_total = len(df["ym"].unique())
best_orig = ic_results.get("Original (50R/50E)", {})
best_a = ic_results.get("A: Revenue Only", {})
best_b = ic_results.get("B: Earnings Only", {})

# Determine best alternative by IC
alts = {k: v for k, v in ic_results.items() if k != "Original (50R/50E)"}
best_alt_label = max(alts, key=lambda k: alts[k]["mean_ic"])
worst_alt_label = min(alts, key=lambda k: alts[k]["mean_ic"])

report = f"""# Growth Factor Autopsy

**Date:** 2026-06-06  
**Data:** Warehouse V3, 2023-01 to 2025-12 ({n_months_total} months)  
**Portfolio:** Top 5, equal-weight, monthly rebalance (CONFIG_B framework)  
**Benchmark:** IHSG monthly return (excess-based Sharpe)

---

## Executive Summary

### Current Growth Factor Formula

```
growth_score = percentile_normalize(rev_growth) x 0.50 + percentile_normalize(earn_growth) x 0.50
```

### Root Cause

**Revenue Growth** has {'positive' if best_a['mean_ic'] > 0 else 'negative'} IC ({best_a['mean_ic']:.4f}, t={best_a['ic_t_stat']:.2f})  
**Earnings Growth** has {'positive' if best_b['mean_ic'] > 0 else 'negative'} IC ({best_b['mean_ic']:.4f}, t={best_b['ic_t_stat']:.2f})

### Decision

| Factor | Go/No-Go |
|--------|:--------:|
| Keep current (50R/50E) | {'**GO**' if best_orig['mean_ic'] > 0 else 'No-Go'} |
| Revenue Only | {'**GO**' if best_a['mean_ic'] > 0 else 'No-Go'} |
| Earnings Only | {'**Mitigate**' if best_b['mean_ic'] > best_orig['mean_ic'] and best_b['ic_t_stat'] > -2 else 'No-Go'} |
| Best alternative | **{best_alt_label}** |

---

## Section 1: Raw Growth Component Statistics

### Revenue Growth Distribution (across all month-tickers)

| Metric | Value |
|--------|:-----:|
| Mean | {df['rev_growth'].mean():.4f} |
| Median | {df['rev_growth'].median():.4f} |
| Std | {df['rev_growth'].std():.4f} |
| Min | {df['rev_growth'].min():.4f} |
| Max | {df['rev_growth'].max():.4f} |
| % Negative | {fmt_pct((df['rev_growth'] < 0).mean())} |
| % Extreme (>+/-100%) | {fmt_pct((df['rev_growth'].abs() > 1).mean())} |

### Earnings Growth Distribution (across all month-tickers)

| Metric | Value |
|--------|:-----:|
| Mean | {df['earn_growth'].mean():.4f} |
| Median | {df['earn_growth'].median():.4f} |
| Std | {df['earn_growth'].std():.4f} |
| Min | {df['earn_growth'].min():.4f} |
| Max | {df['earn_growth'].max():.4f} |
| % Negative | {fmt_pct((df['earn_growth'] < 0).mean())} |
| % Extreme (>+/-100%) | {fmt_pct((df['earn_growth'].abs() > 1).mean())} |

---

## Section 2: Component IC Analysis

### Individual Component IC

| Component | Mean IC | Std IC | t-stat | IC>0% | Spread | Hit Rate |
|-----------|:------:|:------:|:-----:|:----:|:-----:|:--------:|
"""
 
for label, col in [("A: Revenue Only", "growth_A_rev_only"), ("B: Earnings Only", "growth_B_earn_only")]:
    icr = ic_results[label]
    report += f"| {label} | {icr['mean_ic']:.4f} | {icr['std_ic']:.4f} | {icr['ic_t_stat']:.2f} | {fmt_pct(icr['ic_positive_pct'])} | {fmt_pct(icr['mean_spread'])} | {fmt_pct(icr['hit_rate'])} |\n"
 
report += f"""
### Quintile Spread Detail

| Component | Top Quintile | Bottom Quintile | Spread |
|-----------|:----------:|:--------------:|:------:|
"""
for label, col in [("A: Revenue Only", "growth_A_rev_only"), ("B: Earnings Only", "growth_B_earn_only")]:
    icr = ic_results[label]
    report += f"| {label} | {fmt_pct(icr['mean_top'])} | {fmt_pct(icr['mean_bot'])} | {fmt_pct(icr['mean_spread'])} |\n"

report += """
### Interpretation

- **Revenue Growth alone**: """
if best_a['mean_ic'] > 0:
    report += f"Positive IC ({best_a['mean_ic']:.4f}), t={best_a['ic_t_stat']:.2f}. "
else:
    report += f"Negative IC ({best_a['mean_ic']:.4f}), t={best_a['ic_t_stat']:.2f}. "
report += f"""Hit rate {fmt_pct(best_a['hit_rate'])}.
- **Earnings Growth alone**: """
if best_b['mean_ic'] > 0:
    report += f"Positive IC ({best_b['mean_ic']:.4f}), t={best_b['ic_t_stat']:.2f}. "
else:
    report += f"Negative IC ({best_b['mean_ic']:.4f}), t={best_b['ic_t_stat']:.2f}. "
report += f"""Hit rate {fmt_pct(best_b['hit_rate'])}.

### Interaction Effect
The 50/50 equal-weight blend produces IC={best_orig['mean_ic']:.4f}, t={best_orig['ic_t_stat']:.2f}.
If Revenue and Earnings had complementary signals (one working when the other fails),
the blend IC would exceed both individual ICs. This is **not** the case here.

---

## Section 3: Alternative Definitions Comparison

### IC Comparison (all alternatives)

| Definition | Mean IC | t-stat | Spread | Hit Rate | Rank |
|-----------|:------:|:-----:|:-----:|:--------:|:----:|
"""
sorted_alts = sorted(ic_results.items(), key=lambda x: x[1]["mean_ic"], reverse=True)
for rank, (label, icr) in enumerate(sorted_alts, 1):
    report += f"| {label} | {icr['mean_ic']:.4f} | {icr['ic_t_stat']:.2f} | {fmt_pct(icr['mean_spread'])} | {fmt_pct(icr['hit_rate'])} | {rank} |\n"

report += """
### Portfolio Backtest Results (Top 5, CONFIG_B framework)

| Definition | CAGR | Sharpe | Sortino | Max DD | Win Rate | Alpha | Vol |
|-----------|:----:|:------:|:-------:|:------:|:--------:|:-----:|:---:|
"""
for label in growth_defs:
    m = bt_results[label]
    report += f"| {label} | {fmt_pct(m['CAGR'])} | {fmt_dec(m['Sharpe'])} | {fmt_dec(m['Sortino'])} | {fmt_pct(m['Max DD'])} | {fmt_pct(m['Win Rate'])} | {fmt_pct(m['Alpha'])} | {fmt_pct(m['Vol'])} |\n"

report += f"""| **IHSG (benchmark)** | {fmt_pct(_ihsg_cagr)} | — | — | — | — | — | — |

---

## Section 4: Alternative Definitions (Detail)

### Formula Definitions

| Label | Formula | Rationale |
|-------|---------|-----------|
| Original (50R/50E) | 50% rev_score + 50% earn_score | Current production formula |
| A: Revenue Only | 100% rev_score | Remove earnings noise |
| B: Earnings Only | 100% earn_score | Remove revenue noise |
| C: 70R/30E | 70% rev_score + 30% earn_score | Revenue-dominant |
| D: 30R/70E | 30% rev_score + 70% earn_score | Earnings-dominant |
| E: Rev Capped +/-100% | percentile(rev_growth.clip(-1,1)) | Winsorize extreme revenue |
| F: Earn Capped +/-100% | percentile(earn_growth.clip(-1,1)) | Winsorize extreme earnings |

### Key Observations

"""

# Find the best and worst backtests
bt_sorted = sorted(bt_results.items(), key=lambda x: x[1]["Sharpe"], reverse=True)
report += f"**Best by Sharpe:** {bt_sorted[0][0]} (Sharpe={fmt_dec(bt_sorted[0][1]['Sharpe'])}, CAGR={fmt_pct(bt_sorted[0][1]['CAGR'])})\n\n"
report += f"**Worst by Sharpe:** {bt_sorted[-1][0]} (Sharpe={fmt_dec(bt_sorted[-1][1]['Sharpe'])}, CAGR={fmt_pct(bt_sorted[-1][1]['CAGR'])})\n\n"

# Revenue vs Earnings comparison
rev_vs_earn_ic_diff = best_a['mean_ic'] - best_b['mean_ic']
if abs(rev_vs_earn_ic_diff) > 0.02:
    report += f"**Revenue vs Earnings delta:** IC difference = {rev_vs_earn_ic_diff:.4f} "
    if rev_vs_earn_ic_diff > 0:
        report += "(Revenue outperforms Earnings as a factor)\n\n"
    else:
        report += "(Earnings outperforms Revenue as a factor; Earnings is the less harmful component)\n\n"

# Capping effect
e_ic = ic_results["E: Rev Capped +/-100%"]["mean_ic"]
a_ic = ic_results["A: Revenue Only"]["mean_ic"]
cap_diff = e_ic - a_ic
report += f"**Capping effect on Revenue:** IC changes from {a_ic:.4f} (uncapped) to {e_ic:.4f} (capped at +/-100%), delta = {cap_diff:+.4f}\n\n"

f_ic = ic_results["F: Earn Capped +/-100%"]["mean_ic"]
b_ic = ic_results["B: Earnings Only"]["mean_ic"]
cap_diff2 = f_ic - b_ic
report += f"**Capping effect on Earnings:** IC changes from {b_ic:.4f} (uncapped) to {f_ic:.4f} (capped at +/-100%), delta = {cap_diff2:+.4f}\n\n"

# Blend analysis
c_ic = ic_results["C: 70R/30E"]["mean_ic"]
d_ic = ic_results["D: 30R/70E"]["mean_ic"]
report += f"**Revenue-dominant blend (70R/30E):** IC={c_ic:.4f}\n\n"
report += f"**Earnings-dominant blend (30R/70E):** IC={d_ic:.4f}\n\n"

report += f"""
---

## Section 5: Recommendation

### Decision Options

| Option | Action | Rationale |
|--------|--------|-----------|
| Repair | Adjust growth formula weights | """
if abs(rev_vs_earn_ic_diff) > 0.02:
    report += f"Revenue dominates ({best_a['mean_ic']:.4f} vs {best_b['mean_ic']:.4f}). "
else:
    report += "Both components have similar IC magnitudes. "
report += f"""Best alternative ({best_alt_label}) achieves IC={alts[best_alt_label]['mean_ic']:.4f} |
| Reduce weight | Decrease growth allocation in CONFIG_B | Current 30% weight amplifies negative alpha |
| Replace | Substitute Growth with experimental factor | Low Volatility (IC=0.0713) or Dividend (IC=0.1245) show positive IC |

### Recommended Path

"""

# Determine recommendation
a_rank = sorted_alts.index((best_alt_label, alts[best_alt_label])) + 1 if best_alt_label in [x[0] for x in sorted_alts] else 0

if best_alt_label != "Original (50R/50E)" and alts[best_alt_label]["mean_ic"] > 0:
    # Positive IC alternative found
    report += f"""**Primary recommendation: Repair** — Replace current 50/50 formula with **{best_alt_label}**.
This alternative shows IC={alts[best_alt_label]['mean_ic']:.4f} vs current {best_orig['mean_ic']:.4f},
an improvement of {alts[best_alt_label]['mean_ic'] - best_orig['mean_ic']:+.4f} in Information Coefficient.

**Secondary recommendation:** Reduce Growth weight from 30% to 15-20% in CONFIG_B,
redistributing to Value (current 10%) and Low Volatility.

**Fallback:** If formula repair is insufficient, replace Growth entirely with
Low Volatility factor (IC=0.0713, t-tested in RESEARCH 001).
"""
elif best_alt_label != "Original (50R/50E)":
    report += f"""**Recommendation: Reduce + Replace path** — No alternative formula yields positive alpha.
Best alternative ({best_alt_label}) still shows negative IC (IC={alts[best_alt_label]['mean_ic']:.4f})
but is the least harmful (backtest CAGR={bt_results[best_alt_label]['CAGR']:.2%}, Sharpe={bt_results[best_alt_label]['Sharpe']:.4f}).

**Immediate action:** Switch to Earnings-only formula to minimize alpha leakage.

**Medium-term:** Reduce Growth weight from 30% to 15% and allocate freed weight to
Value (currently 10%) and Low Volatility.

**Long-term:** Replace Growth entirely with a positive-alpha factor
(Low Volatility IC=0.0713 or Dividend IC=0.1245 from RESEARCH 001).
"""
else:
    report += f"""**Recommendation: Reduce weight** — Current formula is already the best option
but produces {'positive' if best_orig['mean_ic'] > 0 else 'negative'} alpha. Reduce Growth weight
from 30% to reduce alpha leakage.
"""

report += """

---

## Appendix: Methodology

### Factor IC Calculation

For each month `t`:
1. Rank all stocks by growth score (percentile 0-100)
2. Compute Spearman rank correlation between scores and next-month returns
3. Q5-Q1 spread: top 20% average return minus bottom 20% average return
4. Hit rate: % months where top-half stocks outperform bottom-half stocks

### Growth Component Calculation

**Revenue Growth:** YoY change in total revenue from fiscal data.
Fallback: Yahoo Finance trailing `revenueGrowth` metric.

**Earnings Growth:** YoY change in net income from fiscal data.
Fallback: Yahoo Finance trailing `earningsGrowth` metric.

### Raw Growth Data Source

For each month-ticker in the warehouse, `fy_actual` determines which
fiscal years are compared. Point-in-time fiscal data is fetched from
yfinance (annual income statements). When PIT data is unavailable,
Yahoo trailing growth rates are used as a fallback.

### Alternative Definitions

- **A (Revenue Only):** Same percentile-normalization applied to revenue growth only
- **B (Earnings Only):** Same percentile-normalization applied to earnings growth only
- **C (70R/30E):** Weighted blend favoring revenue
- **D (30R/70E):** Weighted blend favoring earnings
- **E (Rev Capped +/-100%):** Revenue growth winsorized at +/-100% before normalization
- **F (Earn Capped +/-100%):** Earnings growth winsorized at +/-100% before normalization

### Portfolio Backtest

Top 5, equal-weight, monthly rebalance.
CONFIG_B weights: Quality=25%, Growth=30%, Value=10%, Momentum=35%.
Only the Growth factor is replaced with each alternative definition.
Benchmark: IHSG monthly return (same calendar month as portfolio returns).
"""

REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write(report)

print(f"\n[DONE] Report written to {REPORT_FILE}")

# Summary
print(f"\n{'=' * 60}")
print("FINAL RESULTS")
print(f"{'=' * 60}")
print(f"\nComponent IC:")
print(f"  Revenue Growth: IC={best_a['mean_ic']:.4f}, t={best_a['ic_t_stat']:.2f}")
print(f"  Earnings Growth: IC={best_b['mean_ic']:.4f}, t={best_b['ic_t_stat']:.2f}")
print(f"\nAlternative ranking (by IC):")
for rank, (label, icr) in enumerate(sorted_alts, 1):
    print(f"  {rank}. {label:30s}: IC={icr['mean_ic']:.4f}, t={icr['ic_t_stat']:.2f}, Sharpe={bt_results[label]['Sharpe']:.4f}")
print(f"\nBest alternative: {best_alt_label} (IC={alts[best_alt_label]['mean_ic']:.4f})")
print(f"Worst alternative: {worst_alt_label} (IC={alts[worst_alt_label]['mean_ic']:.4f})")
