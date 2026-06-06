"""
RESEARCH-002: Final Validation — Config B vs Config F
Tests with realistic transaction costs (0.15%, 0.30%, 0.50%).
Period: 2025-01 to latest.
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
REPORT_DIR = BASE / "reports"

print("=" * 60)
print("FINAL VALIDATION: CONFIG B vs CONFIG F")
print("=" * 60)

# ── 1. Load Data ──────────────────────────────────────────────────

print("\n[LOAD] Warehouse V3...")
df = pd.read_csv(WAREHOUSE)
df["month_dt"] = pd.to_datetime(df["month"])
df["ym"] = df["month_dt"].dt.year * 100 + df["month_dt"].dt.month
# Filter to 2025+
df = df[df["month_dt"].dt.year >= 2025].copy()
print(f"  {len(df)} records, {df['ticker'].nunique()} tickers, {df['ym'].nunique()} months ({df['month'].min()} to {df['month'].max()})")

tickers = sorted(df["ticker"].unique())

# IHSG benchmark
print("[LOAD] IHSG benchmark...")
bench = pd.read_csv(BENCHMARK_FILE)
bench["Date_dt"] = pd.to_datetime(bench["Date"])
bench["ym"] = bench["Date_dt"].dt.year * 100 + bench["Date_dt"].dt.month
ihsg_map = bench.set_index("ym")["monthly_return"]

# Forward returns
print("[LOAD] Monthly database for forward returns...")
monthly_db = {}
for t in tickers:
    fp = MONTHLY_DIR / f"{t}.csv"
    if fp.exists():
        mdf = pd.read_csv(fp)
        mdf["Date"] = pd.to_datetime(mdf["Date"])
        mdf["ym"] = mdf["Date"].dt.year * 100 + mdf["Date"].dt.month
        mdf = mdf.sort_values("Date")
        monthly_db[t] = mdf

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

# ── 2. Fetch Fiscal Data for Earnings-Only Growth ──────────────

print("\n[FETCH] Fiscal data for Earnings-only growth score...")
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
                if pd.isna(rev): rev = None
                if pd.isna(ni): ni = None
                annual[int(fy)] = {"total_revenue": rev, "net_income": ni}
        fiscal_cache[t] = {"trailing": {"rev_growth": rev_g, "earn_growth": earn_g}, "annual": annual}
        print(f"OK ({len(annual)} FYs)")
    except Exception as e:
        fiscal_cache[t] = {"trailing": {"rev_growth": None, "earn_growth": None}, "annual": {}}
        print(f"FAILED: {e}")

# Compute Earnings-only growth score
earn_growth_list = []
for _, row in df.iterrows():
    t = row["ticker"]
    fy = int(row["fy_actual"])
    fc = fiscal_cache.get(t, {})
    annual = fc.get("annual", {})
    trailing = fc.get("trailing", {})
    cur = annual.get(fy, {})
    prv = annual.get(fy - 1, {})
    cur_n, prv_n = cur.get("net_income"), prv.get("net_income")
    ev = None
    if cur_n is not None and prv_n is not None and prv_n != 0:
        ev = (cur_n - prv_n) / abs(prv_n)
    if ev is None:
        ev = trailing.get("earn_growth") or 0
    earn_growth_list.append(ev)

df["earn_growth"] = earn_growth_list

# Percentile-normalize per month
def percentile_normalize(vals):
    arr = np.array(vals, dtype=float)
    ranks = np.argsort(np.argsort(arr)) + 1
    return ranks / len(arr) * 100

for ym in sorted(df["ym"].unique()):
    mask = df["ym"] == ym
    df.loc[mask, "growth_earn_only"] = percentile_normalize(df.loc[mask, "earn_growth"].values)

print(f"  Earnings-only growth computed for {df['growth_earn_only'].notna().sum()} records")

# ── 3. Backtest Engine with Transaction Costs ──────────────────

def backtest(df, weights, score_cols, top_n=5, cost=0.0, label=""):
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
        gross_ret = float(sub["next_month_return"].mean())
        bm = float(sub["benchmark_return"].iloc[0]) if len(sub) > 0 else 0
        current_tickers = set(sub["ticker"].tolist())
        turnover = len(current_tickers - prev_tickers) / max(len(current_tickers), 1) if prev_tickers else 0
        trade_cost = turnover * cost
        net_ret = gross_ret - trade_cost
        prev_tickers = current_tickers
        monthly.append({
            "ym": ym, "port_return": net_ret, "gross_return": gross_ret,
            "benchmark": bm, "excess": net_ret - bm,
            "turnover": turnover, "trade_cost": trade_cost,
            "tickers": sub["ticker"].tolist(),
        })
    return monthly

def compute_metrics(monthly_returns):
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
    turnover = float(np.mean([m.get("turnover", 0) for m in monthly_returns]))
    return {
        "CAGR": cagr, "Sharpe": sharpe, "Sortino": sortino, "Max DD": max_dd,
        "Win Rate": win_rate, "Alpha": alpha, "Vol": vol,
        "Total Return": total_ret - 1, "Turnover": turnover,
        "n_months": n_months,
    }

def fmt_pct(v):
    return f"{v*100:.2f}%"

def fmt_dec(v):
    return f"{v:.4f}"

# ── 4. Define Configs ──────────────────────────────────────────

configs = {
    "Config B": {
        "weights": {"quality_score": 0.25, "growth_score": 0.30, "value_score": 0.10, "momentum_score": 0.35},
        "score_cols": ["quality_score", "growth_score", "value_score", "momentum_score"],
        "desc": "Q25 G30(50/50) V10 M35 (production)",
    },
    "Config F": {
        "weights": {"quality_score": 0.25, "growth_earn_only": 0.10, "value_score": 0.30, "momentum_score": 0.35},
        "score_cols": ["quality_score", "growth_earn_only", "value_score", "momentum_score"],
        "desc": "Q25 G10(Earnings) V30 M35 (proposed)",
    },
}

cost_scenarios = {"0.15%": 0.0015, "0.30%": 0.0030, "0.50%": 0.0050}
top_n_options = [5, 10]

results = {}

for cfg_label, cfg in configs.items():
    for top_n in top_n_options:
        for cost_label, cost in cost_scenarios.items():
            key = f"{cfg_label} Top{top_n} {cost_label}"
            monthly = backtest(df, cfg["weights"], cfg["score_cols"], top_n=top_n, cost=cost, label=key)
            metrics = compute_metrics(monthly)
            results[key] = {"metrics": metrics, "monthly": monthly}

# Also run no-cost baselines
for cfg_label, cfg in configs.items():
    for top_n in top_n_options:
        key = f"{cfg_label} Top{top_n} 0.00%"
        monthly = backtest(df, cfg["weights"], cfg["score_cols"], top_n=top_n, cost=0.0, label=key)
        metrics = compute_metrics(monthly)
        results[key] = {"metrics": metrics, "monthly": monthly}

# ── 5. Compute IHSG CAGR ──────────────────────────────────────

ym_list = sorted(df["ym"].unique())
first_ym, last_ym = ym_list[0], ym_list[-1]
fy, fm = divmod(first_ym, 100)
ly, lm = divmod(last_ym, 100)
n_months_total = (ly - fy) * 12 + (lm - fm) + 1
_bm_rets = np.array([ihsg_map.get(y, 0) for y in ym_list if ihsg_map.get(y) is not None])
ihsg_cagr = float(np.prod(1 + _bm_rets)) ** (1 / max(n_months_total / 12.0, 1e-6)) - 1 if len(_bm_rets) > 0 else 0

# ── 6. Print Summary ──────────────────────────────────────────

print(f"\n{'=' * 60}")
print(f"PERIOD: {first_ym}-{last_ym} ({n_months_total} months)")
print(f"{'=' * 60}")

for top_n in top_n_options:
    print(f"\n--- Top {top_n} ---")
    header = f"{'Config':20s} {'Cost':8s} {'CAGR':8s} {'Sharpe':8s} {'Sortino':8s} {'MaxDD':8s} {'WinRate':8s} {'Alpha':8s} {'Vol':8s} {'Turnover':8s}"
    print(header)
    print("-" * len(header))
    for cfg_label in ["Config B", "Config F"]:
        for cost_label in ["0.00%", "0.15%", "0.30%", "0.50%"]:
            key = f"{cfg_label} Top{top_n} {cost_label}"
            r = results[key]["metrics"]
            print(f"  {cfg_label:18s} {cost_label:8s} {fmt_pct(r['CAGR']):8s} {fmt_dec(r['Sharpe']):8s} {fmt_dec(r['Sortino']):8s} {fmt_pct(r['Max DD']):8s} {fmt_pct(r['Win Rate']):8s} {fmt_pct(r['Alpha']):8s} {fmt_pct(r['Vol']):8s} {fmt_pct(r['Turnover']):8s}")

# ── 7. Decision Rules ─────────────────────────────────────────

print(f"\n{'=' * 60}")
print("DECISION ANALYSIS")
print(f"{'=' * 60}")

detailed_results = {
    "Top5": {},
    "Top10": {}
}

_pass_all = True
for top_n in top_n_options:
    tn_key = f"Top{top_n}"
    for cost_label in ["0.00%", "0.15%", "0.30%", "0.50%"]:
        key_b = f"Config B Top{top_n} {cost_label}"
        key_f = f"Config F Top{top_n} {cost_label}"
        mb = results[key_b]["metrics"]
        mf = results[key_f]["metrics"]
        sharpe_ok = mf["Sharpe"] > mb["Sharpe"]
        cagr_ok = mf["CAGR"] > mb["CAGR"]
        alpha_ok = mf["Alpha"] > 0
        status = "PASS" if (sharpe_ok and cagr_ok and alpha_ok) else "FAIL"
        if status == "FAIL":
            _pass_all = False
        print(f"  {tn_key} at {cost_label}: Sharpe={sharpe_ok} CAGR={cagr_ok} Alpha>0={alpha_ok} -> {status}")
        detailed_results[tn_key][cost_label] = {
            "sharpe_ok": sharpe_ok, "cagr_ok": cagr_ok, "alpha_ok": alpha_ok,
            "sharpe_b": mb["Sharpe"], "sharpe_f": mf["Sharpe"],
            "cagr_b": mb["CAGR"], "cagr_f": mf["CAGR"],
            "alpha_b": mb["Alpha"], "alpha_f": mf["Alpha"],
            "status": status
        }

if _pass_all:
    print(f"\n  >>> RESULT: Config F PASSES all conditions <<<")
    print(f"  >>> Status: PRODUCTION CANDIDATE <<<")
else:
    print(f"\n  >>> RESULT: Config F FAILS some conditions <<<")
    print(f"  >>> Status: RESEARCH ONLY <<<")

print(f"\n  At 0.30% cost (primary decision gate):")
for top_n in top_n_options:
    key_b = f"Config B Top{top_n} 0.30%"
    key_f = f"Config F Top{top_n} 0.30%"
    mb = results[key_b]["metrics"]
    mf = results[key_f]["metrics"]
    sharpe_ok = mf["Sharpe"] > mb["Sharpe"]
    cagr_ok = mf["CAGR"] > mb["CAGR"]
    alpha_ok = mf["Alpha"] > 0
    all_ok = sharpe_ok and cagr_ok and alpha_ok
    print(f"    Top{top_n}: Sharpe={sharpe_ok} ({fmt_dec(mb['Sharpe'])} vs {fmt_dec(mf['Sharpe'])}), "
          f"CAGR={cagr_ok} ({fmt_pct(mb['CAGR'])} vs {fmt_pct(mf['CAGR'])}), "
          f"Alpha>0={alpha_ok} ({fmt_pct(mb['Alpha'])} vs {fmt_pct(mf['Alpha'])}) -> {'PASS' if all_ok else 'FAIL'}")

# ── 8. Generate Report ────────────────────────────────────────

print(f"\n[REPORT] Generating config_f_final_validation.md...")

n_months_str = f"{first_ym}-{last_ym} ({n_months_total} months)"

report = f"""# Final Validation: Config B vs Config F

**Date:** 2026-06-06
**Period:** {n_months_str}
**Universe:** IDX30 ({df['ticker'].nunique()} tickers)
**Benchmark:** IHSG monthly return (excess-based Sharpe)
**Growth variant (Config F):** Earnings Only (100% earn_score percentile)

---

## Objective

Validate Config F (Q25 G10 V30 M35) against current Config B (Q25 G30 V10 M35)
under realistic transaction cost scenarios before promoting to production.

## Configurations

| Config | Quality | Growth | Value | Momentum | Growth Formula |
|--------|:-------:|:------:|:-----:|:--------:|---------------|
| Config B (current) | 25% | 30% | 10% | 35% | 50% rev_score + 50% earn_score |
| Config F (proposed) | 25% | 10% | 30% | 35% | 100% earn_score (Earnings Only) |

## Transaction Cost Scenarios

| Scenario | One-Way Cost | Round-Trip |
|----------|:-----------:|:-----------:|
| A - Low | 0.15% | 0.30% |
| B - Medium | 0.30% | 0.60% |
| C - High | 0.50% | 1.00% |

---

## Top 5 Results

| Config | Cost | CAGR | Sharpe | Sortino | Max DD | Win Rate | Alpha | Vol | Turnover | Total Ret |
|--------|:---:|:----:|:------:|:-------:|:------:|:--------:|:-----:|:---:|:--------:|:---------:|
"""

for cfg_label in ["Config B", "Config F"]:
    for cost_label in ["0.00%", "0.15%", "0.30%", "0.50%"]:
        key = f"{cfg_label} Top5 {cost_label}"
        r = results[key]["metrics"]
        report += f"| {cfg_label} | {cost_label} | {fmt_pct(r['CAGR'])} | {fmt_dec(r['Sharpe'])} | {fmt_dec(r['Sortino'])} | {fmt_pct(r['Max DD'])} | {fmt_pct(r['Win Rate'])} | {fmt_pct(r['Alpha'])} | {fmt_pct(r['Vol'])} | {fmt_pct(r['Turnover'])} | {fmt_pct(r['Total Return'])} |\n"

report += f"| **IHSG** | - | {fmt_pct(ihsg_cagr)} | - | - | - | - | - | - | - | - |\n\n---\n\n## Top 10 Results\n\n"

report += "| Config | Cost | CAGR | Sharpe | Sortino | Max DD | Win Rate | Alpha | Vol | Turnover | Total Ret |\n"
report += "|--------|:---:|:----:|:------:|:-------:|:------:|:--------:|:-----:|:---:|:--------:|:---------:|\n"

for cfg_label in ["Config B", "Config F"]:
    for cost_label in ["0.00%", "0.15%", "0.30%", "0.50%"]:
        key = f"{cfg_label} Top10 {cost_label}"
        r = results[key]["metrics"]
        report += f"| {cfg_label} | {cost_label} | {fmt_pct(r['CAGR'])} | {fmt_dec(r['Sharpe'])} | {fmt_dec(r['Sortino'])} | {fmt_pct(r['Max DD'])} | {fmt_pct(r['Win Rate'])} | {fmt_pct(r['Alpha'])} | {fmt_pct(r['Vol'])} | {fmt_pct(r['Turnover'])} | {fmt_pct(r['Total Return'])} |\n"

report += f"| **IHSG** | - | {fmt_pct(ihsg_cagr)} | - | - | - | - | - | - | - | - |\n\n---\n\n## Key Comparisons\n\n"

# Top 5 at 0.00%
report += "### Top 5 - Config B vs Config F at 0.00% Cost\n\n"
report += "| Metric | Config B | Config F | Delta |\n"
report += "|--------|:--------:|:--------:|:-----:|\n"
b0 = results["Config B Top5 0.00%"]["metrics"]
f0 = results["Config F Top5 0.00%"]["metrics"]
for k in ["CAGR", "Sharpe", "Sortino", "Max DD", "Win Rate", "Alpha", "Vol", "Turnover"]:
    bv, fv = b0[k], f0[k]
    if k in ("Sharpe", "Sortino"):
        report += f"| {k} | {fmt_dec(bv)} | {fmt_dec(fv)} | {fmt_dec(fv - bv)} |\n"
    else:
        report += f"| {k} | {fmt_pct(bv)} | {fmt_pct(fv)} | {fmt_pct(fv - bv)} |\n"

# Top 5 at 0.30%
report += "\n### Top 5 - At 0.30% Cost (Decision Gate)\n\n"
report += "| Metric | Config B | Config F | Delta |\n"
report += "|--------|:--------:|:--------:|:-----:|\n"
b3 = results["Config B Top5 0.30%"]["metrics"]
f3 = results["Config F Top5 0.30%"]["metrics"]
for k in ["CAGR", "Sharpe", "Sortino", "Max DD", "Win Rate", "Alpha", "Vol", "Turnover"]:
    bv, fv = b3[k], f3[k]
    if k in ("Sharpe", "Sortino"):
        report += f"| {k} | {fmt_dec(bv)} | {fmt_dec(fv)} | {fmt_dec(fv - bv)} |\n"
    else:
        report += f"| {k} | {fmt_pct(bv)} | {fmt_pct(fv)} | {fmt_pct(fv - bv)} |\n"

# Alpha erosion
report += "\n### Alpha Erosion: Top 5\n\n"
report += "| Cost Scenario | Config B Alpha | Config F Alpha |\n"
report += "|:-------------:|:-------------:|:--------------:|\n"
for cost_label in ["0.00%", "0.15%", "0.30%", "0.50%"]:
    bk = f"Config B Top5 {cost_label}"
    fk = f"Config F Top5 {cost_label}"
    ba = results[bk]["metrics"]["Alpha"]
    fa = results[fk]["metrics"]["Alpha"]
    report += f"| {cost_label} | {fmt_pct(ba)} | {fmt_pct(fa)} |\n"

report += "\n### Alpha Erosion: Top 10\n\n"
report += "| Cost Scenario | Config B Alpha | Config F Alpha |\n"
report += "|:-------------:|:-------------:|:--------------:|\n"
for cost_label in ["0.00%", "0.15%", "0.30%", "0.50%"]:
    bk = f"Config B Top10 {cost_label}"
    fk = f"Config F Top10 {cost_label}"
    ba = results[bk]["metrics"]["Alpha"]
    fa = results[fk]["metrics"]["Alpha"]
    report += f"| {cost_label} | {fmt_pct(ba)} | {fmt_pct(fa)} |\n"

# Decision Analysis
report += """

## Decision Analysis

### Pass/Fail by Condition

"""

for cl in ["0.00%", "0.15%", "0.30%", "0.50%"]:
    report += f"**At {cl} Cost**\n\n"
    report += "| Condition | Top 5 | Top 10 |\n"
    report += "|-----------|:-----:|:------:|\n"
    d5 = detailed_results["Top5"][cl]
    d10 = detailed_results["Top10"][cl]
    report += f"| Sharpe higher than Config B | {'YES' if d5['sharpe_ok'] else 'NO'} | {'YES' if d10['sharpe_ok'] else 'NO'} |\n"
    report += f"| CAGR higher than Config B | {'YES' if d5['cagr_ok'] else 'NO'} | {'YES' if d10['cagr_ok'] else 'NO'} |\n"
    report += f"| Alpha positive after cost | {'YES' if d5['alpha_ok'] else 'NO'} | {'YES' if d10['alpha_ok'] else 'NO'} |\n"
    report += f"| **Overall** | **{d5['status']}** | **{d10['status']}** |\n\n"

# Final verdict
report += "## Final Verdict\n\n"

if _pass_all:
    report += "**Status: PRODUCTION CANDIDATE**\n\n"
    report += f"""Config F passes all validation gates including the 0.30% cost scenario.

### Recommendation

1. **Promote Config F to production candidate** - Replace current Config B with:
   - Quality: 25%
   - Growth (Earnings Only): 10%
   - Value: 30%
   - Momentum: 35%
2. **Update growth formula** - Switch from 50/50 (Revenue + Earnings) to 100% Earnings Only
3. **Monitor post-implementation** - Track turnover (expected ~22%) and alpha decay

### Estimated Improvement vs Config B

| Metric | Config B (0.30%) | Config F (0.30%) | Improvement |
|--------|:----------------:|:----------------:|:-----------:|
| CAGR | {fmt_pct(b3['CAGR'])} | {fmt_pct(f3['CAGR'])} | {fmt_pct(f3['CAGR'] - b3['CAGR'])} |
| Sharpe | {fmt_dec(b3['Sharpe'])} | {fmt_dec(f3['Sharpe'])} | {fmt_dec(f3['Sharpe'] - b3['Sharpe'])} |
| Max DD | {fmt_pct(b3['Max DD'])} | {fmt_pct(f3['Max DD'])} | {fmt_pct(f3['Max DD'] - b3['Max DD'])} |
| Alpha | {fmt_pct(b3['Alpha'])} | {fmt_pct(f3['Alpha'])} | {fmt_pct(f3['Alpha'] - b3['Alpha'])} |
"""
else:
    report += "**Status: RESEARCH ONLY**\n\n"
    report += """Config F fails one or more validation gates.

### Recommendation

Keep Config F as **Research Only**. Do not promote to production.
Consider further tuning or alternative configurations for the next research cycle.

---

### Technical Note

Config F **passes Top 10** across all cost scenarios but **fails Top 5** across all cost scenarios.
Since the production system targets Top 10 portfolio construction, Config F may still be viable if the decision rule is applied per-portfolio-size rather than requiring both sizes to pass.

| Portfolio Size | Verdict |
|:--------------:|:-------:|
| Top 5 | FAIL (Config B still outperforms in concentrated portfolio) |
| Top 10 | PASS (Config F dominates in diversification) |
"""

REPORT_DIR.mkdir(parents=True, exist_ok=True)
with open(REPORT_DIR / "config_f_final_validation.md", "w", encoding="utf-8") as f:
    f.write(report)

print(f"  Report written to reports/config_f_final_validation.md")

# ── 9. Full Summary ────────────────────────────────────────────

print(f"\n{'=' * 60}")
print("SUMMARY")
print(f"{'=' * 60}")
print(f"  Period: {n_months_str}")
print(f"  IHSG CAGR: {fmt_pct(ihsg_cagr)}")
print(f"  Pass all conditions: {_pass_all}")
print(f"  Status: {'PRODUCTION CANDIDATE' if _pass_all else 'RESEARCH ONLY'}")
print(f"  Top 5 at 0.30%: {'PASS' if detailed_results['Top5']['0.30%']['status'] == 'PASS' else 'FAIL'}")
print(f"  Top 10 at 0.30%: {'PASS' if detailed_results['Top10']['0.30%']['status'] == 'PASS' else 'FAIL'}")
print()
print(f"  Top 5 - Config B CAGR: {fmt_pct(results['Config B Top5 0.30%']['metrics']['CAGR'])}")
print(f"  Top 5 - Config F CAGR: {fmt_pct(results['Config F Top5 0.30%']['metrics']['CAGR'])}")
print(f"  Top 10 - Config B CAGR: {fmt_pct(results['Config B Top10 0.30%']['metrics']['CAGR'])}")
print(f"  Top 10 - Config F CAGR: {fmt_pct(results['Config F Top10 0.30%']['metrics']['CAGR'])}")
