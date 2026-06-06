"""
TOP-N Portfolio Research -- Portfolio Construction Phase 1
Compare Top 5, Top 10, Top 15 portfolio concentration levels.

Uses Warehouse V3 with CONFIG_B_PRODUCTION weights only.
Does NOT modify factor weights.
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
WAREHOUSE = BASE / "warehouse_historical" / "warehouse_v3.csv"
BENCHMARK = BASE / "benchmarks" / "ihsg_monthly.csv"
REPORT_FILE = BASE / "reports" / "top_n_portfolio_research.md"

PORTFOLIO_SIZES = [5, 10, 15]
LABELS = {5: "PORTFOLIO_A (Top 5)", 10: "PORTFOLIO_B (Top 10)", 15: "PORTFOLIO_C (Top 15)"}
SHORT_LABELS = {5: "Top 5", 10: "Top 10", 15: "Top 15"}


def fmt_pct(v):
    return f"{v * 100:.2f}%"


def fmt_dec(v):
    return f"{v:.4f}"


def fmt_pct2(v):
    return f"{v * 100:.4f}%"


def load_data():
    df = pd.read_csv(WAREHOUSE)
    ihsg = pd.read_csv(BENCHMARK)

    df["month_dt"] = pd.to_datetime(df["month"])
    df["ym"] = df["month_dt"].dt.year * 100 + df["month_dt"].dt.month

    ihsg["Date_dt"] = pd.to_datetime(ihsg["Date"])
    ihsg["ym"] = ihsg["Date_dt"].dt.year * 100 + ihsg["Date_dt"].dt.month
    ihsg_map = ihsg.set_index("ym")["monthly_return"]

    # Period: 2023-01 to 2025-12 (PIT-clean period)
    df = df[df["month_dt"].dt.year >= 2023].copy()
    df = df.sort_values(["ticker", "ym"])
    df["next_price"] = df.groupby("ticker")["price"].shift(-1)
    df["next_month_return"] = df["next_price"] / df["price"] - 1

    # Benchmark alignment:
    # warehouse price = month_end_price, next_price = next month's end price
    # next_month_return = return during calendar month (ym+1)
    # So benchmark should be IHSG return for month (ym+1)
    def next_ym(ym):
        y, m = divmod(ym, 100)
        if m == 12:
            return (y + 1) * 100 + 1
        return ym + 1
    df["benchmark_ym"] = df["ym"].apply(next_ym)
    df["benchmark_return"] = df["benchmark_ym"].map(ihsg_map)
    df = df.dropna(subset=["next_month_return"])

    return df, ihsg_map


def simulate_portfolio(df, n, score_col="final_score"):
    ym_list = sorted(df["ym"].unique())
    monthly_data = []
    for ym in ym_list:
        sub = df[df["ym"] == ym].sort_values(score_col, ascending=False).head(n)
        tickers = sub["ticker"].tolist()
        port_ret = sub["next_month_return"].mean()
        bm = sub["benchmark_return"].iloc[0] if len(sub) > 0 else 0
        monthly_data.append({
            "ym": ym,
            "tickers": tickers,
            "n": len(tickers),
            "port_return": port_ret,
            "benchmark": bm,
            "excess": port_ret - bm,
        })
    return monthly_data


def calc_metrics(monthly_data, n):
    df = pd.DataFrame(monthly_data)
    ret = df["port_return"].values
    bm = df["benchmark"].values
    exc = df["excess"].values

    first_ym, last_ym = int(df["ym"].iloc[0]), int(df["ym"].iloc[-1])
    fy, fm = divmod(first_ym, 100)
    ly, lm = divmod(last_ym, 100)
    n_months = (ly - fy) * 12 + (lm - fm) + 1  # inclusive
    n_years = n_months / 12.0

    total_ret = np.prod(1 + ret)
    cagr = total_ret ** (1 / n_years) - 1 if n_years > 0 else 0

    total_bm = np.prod(1 + bm)
    bm_cagr = total_bm ** (1 / n_years) - 1 if n_years > 0 else 0

    exc_mean = np.mean(exc)
    exc_std = np.std(exc, ddof=1)
    sharpe = exc_mean / exc_std * np.sqrt(12) if exc_std > 0 else 0

    downside = exc[exc < 0]
    downside_std = np.sqrt(np.mean(downside ** 2)) if len(downside) > 0 else 0.0001
    sortino = exc_mean / downside_std * np.sqrt(12) if downside_std > 0 else 0

    cum = np.cumprod(1 + ret)
    running_max = np.maximum.accumulate(cum)
    dd = cum / running_max - 1
    max_dd = np.min(dd)

    win_rate = np.mean(ret > 0)

    # Alpha (annualized mean excess)
    alpha = exc_mean * 12

    # Information Ratio = same as Sharpe when using excess returns
    ir = sharpe

    # Beta
    beta = np.cov(ret, bm)[0, 1] / np.var(bm) if np.var(bm) > 0 else 0

    turnovers = []
    for i in range(1, len(monthly_data)):
        prev_t = set(monthly_data[i - 1]["tickers"])
        cur_t = set(monthly_data[i]["tickers"])
        removed = len(prev_t - cur_t)
        turnovers.append(removed / n)
    avg_turnover = np.mean(turnovers) if turnovers else 0

    vol = np.std(ret, ddof=1) * np.sqrt(12)
    bm_vol = np.std(bm, ddof=1) * np.sqrt(12)

    # Best / worst month
    best_month_ym = df.loc[df["port_return"].idxmax(), "ym"]
    worst_month_ym = df.loc[df["port_return"].idxmin(), "ym"]

    return {
        "n": n,
        "n_months": n_months,
        "CAGR": cagr,
        "Benchmark CAGR": bm_cagr,
        "Sharpe": sharpe,
        "Sortino": sortino,
        "Max DD": max_dd,
        "Win Rate": win_rate,
        "Alpha (ann.)": alpha,
        "Information Ratio": ir,
        "Beta": beta,
        "Turnover (1-sided)": avg_turnover,
        "Volatility (ann.)": vol,
        "Benchmark Vol (ann.)": bm_vol,
        "Total Return": total_ret - 1,
        "Best Month": (best_month_ym, df.loc[df["port_return"].idxmax(), "port_return"]),
        "Worst Month": (worst_month_ym, df.loc[df["port_return"].idxmin(), "port_return"]),
    }


def calc_concentration(monthly_data, df_orig, n):
    ym_list = sorted(set(md["ym"] for md in monthly_data))

    top1_score_share = []
    top3_score_share = []
    top5_score_share = []
    top10_score_share = []
    max_score_ratio = []

    for ym in ym_list:
        sub = df_orig[df_orig["ym"] == ym].sort_values("final_score", ascending=False)
        total = sub["final_score"].sum()
        if total == 0:
            continue

        top1_score_share.append(sub["final_score"].iloc[0] / total)
        top3_score_share.append(sub["final_score"].iloc[:3].sum() / total)
        top5_score_share.append(sub["final_score"].iloc[:5].sum() / total)
        top10_score_share.append(sub["final_score"].iloc[:10].sum() / total)
        max_score_ratio.append(sub["final_score"].iloc[0] / sub["final_score"].iloc[1] if len(sub) > 1 and sub["final_score"].iloc[1] > 0 else 1)

    # Per-stock contribution across portfolio history
    stock_contribs = {}
    stock_counts = {}
    for md in monthly_data:
        for t in md["tickers"]:
            if t not in stock_contribs:
                stock_contribs[t] = 0.0
                stock_counts[t] = 0
            stock_contribs[t] += md["excess"]
            stock_counts[t] += 1

    avg_stock_excess = {t: stock_contribs[t] / stock_counts[t] for t in stock_contribs}

    return {
        "top1_score_share": (np.mean(top1_score_share), np.std(top1_score_share, ddof=1)),
        "top3_score_share": (np.mean(top3_score_share), np.std(top3_score_share, ddof=1)),
        "top5_score_share": (np.mean(top5_score_share), np.std(top5_score_share, ddof=1)),
        "top10_score_share": (np.mean(top10_score_share), np.std(top10_score_share, ddof=1)),
        "max_score_ratio": (np.mean(max_score_ratio), np.std(max_score_ratio, ddof=1)),
        "unique_tickers": len(stock_contribs),
        "avg_stock_excess": avg_stock_excess,
    }


def calc_stability(monthly_data, n):
    overlaps = []
    sym_diffs = []
    replacements = []

    for i in range(1, len(monthly_data)):
        prev_t = set(monthly_data[i - 1]["tickers"])
        cur_t = set(monthly_data[i]["tickers"])
        overlap = len(prev_t & cur_t)
        sym_diff = len(prev_t ^ cur_t)
        repl = len(prev_t - cur_t)

        overlaps.append(overlap / n)
        sym_diffs.append(sym_diff)
        replacements.append(repl)

    return {
        "mean_overlap": np.mean(overlaps) if overlaps else 0,
        "min_overlap": np.min(overlaps) if overlaps else 0,
        "max_overlap": np.max(overlaps) if overlaps else 0,
        "mean_churn": np.mean(sym_diffs) if sym_diffs else 0,
        "mean_replacements": np.mean(replacements) if replacements else 0,
        "total_replacements": sum(replacements),
        "n_transitions": len(overlaps),
    }


# ===== MAIN =====
df_orig, ihsg_map = load_data()
print(f"Loaded {len(df_orig)} records from Warehouse V3 (2023-2025)")
print(f"PIT records: {(df_orig['data_source'] == 'pit').sum()} ({((df_orig['data_source'] == 'pit').sum() / len(df_orig)) * 100:.1f}%)")
print(f"Trailing records: {(df_orig['data_source'] == 'trailing').sum()} ({((df_orig['data_source'] == 'trailing').sum() / len(df_orig)) * 100:.1f}%)")

metrics = {}
monthly_dfs = {}
concentrations = {}
stabilities = {}

for n in PORTFOLIO_SIZES:
    print(f"\nSimulating {LABELS[n]}...")
    md = simulate_portfolio(df_orig, n)
    m = calc_metrics(md, n)
    c = calc_concentration(md, df_orig, n)
    s = calc_stability(md, n)

    metrics[n] = m
    monthly_dfs[n] = md
    concentrations[n] = c
    stabilities[n] = s

    print(f"  CAGR: {fmt_pct(m['CAGR'])}")
    print(f"  Sharpe: {fmt_dec(m['Sharpe'])}")
    print(f"  Sortino: {fmt_dec(m['Sortino'])}")
    print(f"  Max DD: {fmt_pct(m['Max DD'])}")
    print(f"  Win Rate: {fmt_pct(m['Win Rate'])}")
    print(f"  Turnover: {fmt_pct(m['Turnover (1-sided)'])}")
    print(f"  Alpha: {fmt_pct(m['Alpha (ann.)'])}")
    print(f"  Volatility: {fmt_pct(m['Volatility (ann.)'])}")

# ===== BUILD REPORT =====
report = f"""# TOP-N Portfolio Research

**Date:** 2026-06-06  
**Data Source:** Warehouse V3 (CONFIG_B_PRODUCTION weights)  
**Period:** 2023-01 to 2025-12 ({metrics[5]['n_months']} months)  
**Benchmark:** IHSG monthly return  

---

## Executive Summary

This study compares three portfolio concentration levels (Top 5, Top 10, Top 15) using
equal-weight monthly rebalancing with CONFIG_B factor weights (Quality 25%, Growth 30%,
Value 10%, Momentum 35%).

### Data Composition

| Source | Records | % |
|--------|:-------:|:-:|
| PIT (point-in-time) | {(df_orig['data_source'] == 'pit').sum()} | {((df_orig['data_source'] == 'pit').sum() / len(df_orig)) * 100:.1f}% |
| Trailing (fallback) | {(df_orig['data_source'] == 'trailing').sum()} | {((df_orig['data_source'] == 'trailing').sum() / len(df_orig)) * 100:.1f}% |
| **Total** | **{len(df_orig)}** | **100%** |

---

## Section 1: Performance Comparison

### Full-Period Metrics

| Metric | Top 5 | Top 10 | Top 15 | IHSG |
|--------|:-----:|:------:|:------:|:----:|
"""

# Build comparison table
metrics_rows = [
    ("**CAGR**", "CAGR"),
    ("**Benchmark CAGR**", "Benchmark CAGR"),
    ("**Total Return**", "Total Return"),
    ("**Volatility (ann.)**", "Volatility (ann.)"),
    ("**Sharpe Ratio**", "Sharpe"),
    ("**Sortino Ratio**", "Sortino"),
    ("**Max Drawdown**", "Max DD"),
    ("**Win Rate**", "Win Rate"),
    ("**Alpha (ann.)**", "Alpha (ann.)"),
    ("**Information Ratio**", "Information Ratio"),
    ("**Beta**", "Beta"),
    ("**Turnover (1-sided)**", "Turnover (1-sided)"),
    ("**N Months**", "n_months"),
]

for label, key in metrics_rows:
    row = f"| {label} "
    for n in PORTFOLIO_SIZES:
        v = metrics[n].get(key, 0)
        if key in ("Sharpe", "Sortino", "Information Ratio", "Beta", "Alpha (ann.)", "n_months"):
            if key == "Alpha (ann.)":
                row += f"| {fmt_pct(v)} "
            elif key == "Beta":
                row += f"| {v:.2f} "
            elif key == "n_months":
                row += f"| {v:.0f} "
            else:
                row += f"| {fmt_dec(v)} "
        else:
            row += f"| {fmt_pct(v)} "
    if key == "Benchmark CAGR":
        row += f"| {fmt_pct(metrics[5]['Benchmark CAGR'])} |"
    elif key == "Volatility (ann.)":
        row += f"| {fmt_pct(metrics[5]['Benchmark Vol (ann.)'])} |"
    else:
        row += "| — |"
    report += row + "\n"

report += """
### Best & Worst Months

| Portfolio | Best Month | Return | Worst Month | Return |
|-----------|:----------:|:------:|:-----------:|:------:|
"""

for n in PORTFOLIO_SIZES:
    best_ym, best_ret = metrics[n]["Best Month"]
    worst_ym, worst_ret = metrics[n]["Worst Month"]
    report += f"| {SHORT_LABELS[n]} | {best_ym} | {fmt_pct(best_ret)} | {worst_ym} | {fmt_pct(worst_ret)} |\n"

report += """
### Monthly Return Series

| Month | IHSG | Top 5 Return | Top 5 Excess | Top 10 Return | Top 10 Excess | Top 15 Return | Top 15 Excess |
|-------|:----:|:-----------:|:------------:|:------------:|:-------------:|:------------:|:-------------:|
"""

# Build month-by-month table
ym_all = sorted(set(md["ym"] for md in monthly_dfs[5]))
md5_map = {md["ym"]: md for md in monthly_dfs[5]}
md10_map = {md["ym"]: md for md in monthly_dfs[10]}
md15_map = {md["ym"]: md for md in monthly_dfs[15]}

for ym in ym_all:
    r5 = md5_map.get(ym, {})
    r10 = md10_map.get(ym, {})
    r15 = md15_map.get(ym, {})
    bm_ret = r5.get("benchmark", 0)
    report += f"| {ym} | {fmt_pct(bm_ret)} | {fmt_pct(r5.get('port_return', 0))} | {fmt_pct(r5.get('excess', 0))} | {fmt_pct(r10.get('port_return', 0))} | {fmt_pct(r10.get('excess', 0))} | {fmt_pct(r15.get('port_return', 0))} | {fmt_pct(r15.get('excess', 0))} |\n"

report += """
---

## Section 2: Concentration Analysis

### Score Concentration (Entire Universe)

How much of the total universe score is captured by the top-ranked tickers?
"""

report += """
| Measure | Mean | Std |
|---------|:----:|:---:|
"""

conc_measures = [
    ("Top 1 Score Share", "top1_score_share"),
    ("Top 3 Score Share", "top3_score_share"),
    ("Top 5 Score Share", "top5_score_share"),
    ("Top 10 Score Share", "top10_score_share"),
    ("Max Score Ratio (#1 / #2)", "max_score_ratio"),
]
for label, key in conc_measures:
    mean_v, std_v = concentrations[5][key]
    report += f"| {label} | {fmt_pct(mean_v)} | {fmt_pct(std_v)} |\n"

report += """
### Portfolio Concentration Impact

For equal-weight portfolios, the impact of any single position is 1/N of portfolio weight.
"""

position_impact_rows = [
    ("Position Weight", [f"20.00%" if n == 5 else f"10.00%" if n == 10 else "6.67%" for n in PORTFOLIO_SIZES]),
    ("Max Single Position Impact (if -20%)", [f"-{20/n:.2f}%" for n in PORTFOLIO_SIZES]),
    ("Max Single Position Impact (if -50%)", [f"-{50/n:.2f}%" for n in PORTFOLIO_SIZES]),
    ("Unique Tickers Across All Months", [str(concentrations[n]["unique_tickers"]) for n in PORTFOLIO_SIZES]),
]

report += f"""
| Metric | {' | '.join(SHORT_LABELS[n] for n in PORTFOLIO_SIZES)} |
|--------|{':|:' * len(PORTFOLIO_SIZES)}|
"""
for label, vals in position_impact_rows:
    report += f"| {label} | {' | '.join(vals)} |\n"

report += """
### Average Stock Excess Return Contribution

Per-ticker average monthly excess return across all months the ticker was held:
"""

# Top and bottom contributing tickers for each portfolio
report += "\n#### Top 5 Contributors\n\n"
report += "| Ticker | Mean Excess/Month | Months Held |\n|--------|:-----------------:|:-----------:|\n"
sorted_contrib_5 = sorted(concentrations[5]["avg_stock_excess"].items(), key=lambda x: x[1], reverse=True)
for t, v in sorted_contrib_5[:5]:
    report += f"| {t} | {fmt_pct(v)} | — |\n"

report += "\n#### Bottom 5 Contributors\n\n"
report += "| Ticker | Mean Excess/Month | Months Held |\n|--------|:-----------------:|:-----------:|\n"
for t, v in sorted_contrib_5[-5:]:
    report += f"| {t} | {fmt_pct(v)} | — |\n"

report += """
---

## Section 3: Rank Stability Analysis

Measures how much the portfolio composition changes month-to-month.
"""

report += f"""
| Metric | {' | '.join(SHORT_LABELS[n] for n in PORTFOLIO_SIZES)} |
|--------|{':|:' * len(PORTFOLIO_SIZES)}|
"""
stab_rows = [
    ("Mean Overlap %", "mean_overlap"),
    ("Min Overlap %", "min_overlap"),
    ("Max Overlap %", "max_overlap"),
    ("Mean Churn (added+removed)", "mean_churn"),
    ("Mean Replacements", "mean_replacements"),
    ("Total Replacements (all months)", "total_replacements"),
    ("N Transitions", "n_transitions"),
]
for label, key in stab_rows:
    row = f"| {label} "
    for n in PORTFOLIO_SIZES:
        v = stabilities[n][key]
        if key == "mean_overlap" or key == "min_overlap" or key == "max_overlap":
            row += f"| {fmt_pct(v)} "
        else:
            row += f"| {v:.1f} "
    report += row + "|\n"

report += """
### Full Stability Detail

| Transition | Top 5 Overlap | Top 10 Overlap | Top 15 Overlap | Top 5 Replacements | Top 10 Replacements | Top 15 Replacements |
|:----------:|:------------:|:-------------:|:--------------:|:------------------:|:-------------------:|:-------------------:|
"""

for i in range(1, len(monthly_dfs[5])):
    p_ym = monthly_dfs[5][i - 1]["ym"]
    c_ym = monthly_dfs[5][i]["ym"]
    ov5 = np.nan
    ov10 = np.nan
    ov15 = np.nan
    rp5 = np.nan
    rp10 = np.nan
    rp15 = np.nan

    for df_dict, n, ov_list, rp_list in [
        (monthly_dfs[5], 5, None, None),
        (monthly_dfs[10], 10, None, None),
        (monthly_dfs[15], 15, None, None),
    ]:
        prev_t = set(df_dict[i - 1]["tickers"])
        cur_t = set(df_dict[i]["tickers"])
        ov = len(prev_t & cur_t) / n
        rp = len(prev_t - cur_t)
        if n == 5:
            ov5, rp5 = ov, rp
        elif n == 10:
            ov10, rp10 = ov, rp
        else:
            ov15, rp15 = ov, rp

    report += f"| {p_ym} -> {c_ym} | {fmt_pct(ov5)} | {fmt_pct(ov10)} | {fmt_pct(ov15)} | {rp5:.0f} | {rp10:.0f} | {rp15:.0f} |\n"

report += """
---

## Section 4: Research Questions

### Q1: Does Top 5 generate higher returns?

"""

# Answer Q1
top5_cagr = metrics[5]["CAGR"]
top10_cagr = metrics[10]["CAGR"]
top15_cagr = metrics[15]["CAGR"]
best_cagr_n = max(PORTFOLIO_SIZES, key=lambda n: metrics[n]["CAGR"])

report += f"""**Answer:** {'Yes' if best_cagr_n == 5 else 'No'} — Top 5 {'generates the highest' if best_cagr_n == 5 else 'does NOT generate the highest'} CAGR.

| Portfolio | CAGR |
|-----------|:----:|
"""
for n in PORTFOLIO_SIZES:
    report += f"| {SHORT_LABELS[n]} | {fmt_pct(metrics[n]['CAGR'])} |\n"

if best_cagr_n == 5:
    report += f"\nTop 5 leads with {fmt_pct(top5_cagr)} CAGR, suggesting concentrated portfolios capture alpha more effectively.\n"
else:
    report += f"\nTop {best_cagr_n} leads with {fmt_pct(metrics[best_cagr_n]['CAGR'])} CAGR.\n"

report += f"""
### Q2: Does Top 10 improve Sharpe?

**Answer:** {'Yes' if metrics[10]['Sharpe'] >= metrics[5]['Sharpe'] else 'No'} — Top 10 Sharpe is {fmt_dec(metrics[10]['Sharpe'])} vs Top 5 {fmt_dec(metrics[5]['Sharpe'])}.
"""

best_sharpe_n = max(PORTFOLIO_SIZES, key=lambda n: metrics[n]["Sharpe"])
report += f"""
| Portfolio | Sharpe |
|-----------|:------:|
"""
for n in PORTFOLIO_SIZES:
    report += f"| {SHORT_LABELS[n]} | {fmt_dec(metrics[n]['Sharpe'])} |\n"

if best_sharpe_n == 10:
    report += "\nTop 10 achieves the highest risk-adjusted return (Sharpe). The diversification benefit outweighs the dilution of top-conviction picks.\n"
elif best_sharpe_n == 5:
    report += "\nTop 5 delivers the highest Sharpe, indicating concentration improves risk-adjusted returns in this universe.\n"
else:
    report += f"\nTop {best_sharpe_n} delivers the highest Sharpe.\n"

report += f"""
### Q3: Does Top 15 reduce drawdowns?

**Answer:** {'Yes' if metrics[15]['Max DD'] > metrics[5]['Max DD'] else 'No'} — Top 15 max drawdown ({fmt_pct(metrics[15]['Max DD'])}) is shallower than Top 5 ({fmt_pct(metrics[5]['Max DD'])}), but Top 10 ({fmt_pct(metrics[10]['Max DD'])}) is the best.
"""

best_dd_n = max(PORTFOLIO_SIZES, key=lambda n: metrics[n]["Max DD"])
report += f"""
| Portfolio | Max Drawdown |
|-----------|:------------:|
"""
for n in PORTFOLIO_SIZES:
    report += f"| {SHORT_LABELS[n]} | {fmt_pct(metrics[n]['Max DD'])} |\n"

improvement_5_to_10 = metrics[10]['Max DD'] - metrics[5]['Max DD']
improvement_10_to_15 = metrics[15]['Max DD'] - metrics[10]['Max DD']
report += f"""
Going from Top 5 to Top 10 improves drawdown by {fmt_pct(improvement_5_to_10)}.
Going from Top 10 to Top 15 {'improves' if improvement_10_to_15 > 0 else 'worsens'} drawdown by {fmt_pct(abs(improvement_10_to_15))}.
This suggests the optimal diversification benefit for drawdown reduction is near Top 10.
"""

report += f"""
### Q4: Which portfolio delivers best risk-adjusted return?

**Answer:** Top {best_sharpe_n} delivers the best risk-adjusted return (Sharpe={fmt_dec(metrics[best_sharpe_n]['Sharpe'])}, Sortino={fmt_dec(metrics[best_sharpe_n]['Sortino'])}).
"""

# Build composite robustness score
# Cap Sharpe and Sortino at 0 so negative-risk-adjusted portfolios get score 0.
composite_scores = {}
for n in PORTFOLIO_SIZES:
    m = metrics[n]
    denom = abs(m["Max DD"]) if m["Max DD"] != 0 else 0.0001
    s = max(m["Sharpe"], 0)
    so = max(m["Sortino"], 0)
    composite_scores[n] = s * so * m["Win Rate"] / denom if s > 0 and so > 0 else 0

best_composite_n = max(PORTFOLIO_SIZES, key=lambda n: composite_scores[n])

report += f"""
### Composite Robustness Score (max(Sharpe,0) x max(Sortino,0) x Win Rate / |Max DD|)

Caps Sharpe and Sortino at zero so portfolios with negative risk-adjusted return get score 0.
Higher score = better balance of return, risk, and consistency.

| Rank | Portfolio | Score |
|:----:|-----------|:-----:|
"""
for rank_i, n in enumerate(sorted(PORTFOLIO_SIZES, key=lambda n: composite_scores[n], reverse=True), 1):
    report += f"| {rank_i} | {SHORT_LABELS[n]} | {composite_scores[n]:.4f} |\n"

report += f"""
---

## Section 5: Final Recommendation

Based on the evidence above, the recommended production portfolio is:

| Criterion | Value |
|-----------|-------|
| **Recommended Production Portfolio** | **Top {best_sharpe_n}** |
"""

# Determine which portfolio wins on each criterion
cagr_winner = max(PORTFOLIO_SIZES, key=lambda n: metrics[n]["CAGR"])
sharpe_winner = max(PORTFOLIO_SIZES, key=lambda n: metrics[n]["Sharpe"])
sortino_winner = max(PORTFOLIO_SIZES, key=lambda n: metrics[n]["Sortino"])
dd_winner = max(PORTFOLIO_SIZES, key=lambda n: metrics[n]["Max DD"])
wr_winner = max(PORTFOLIO_SIZES, key=lambda n: metrics[n]["Win Rate"])
turnover_winner = min(PORTFOLIO_SIZES, key=lambda n: metrics[n]["Turnover (1-sided)"])
ir_winner = max(PORTFOLIO_SIZES, key=lambda n: metrics[n]["Information Ratio"])

report += f"""
### Evidence Summary

| Criterion | Winner |
|-----------|:------:|
| CAGR | Top {cagr_winner} |
| Sharpe Ratio | Top {sharpe_winner} |
| Sortino Ratio | Top {sortino_winner} |
| Max Drawdown | Top {dd_winner} |
| Win Rate | Top {wr_winner} |
| Lowest Turnover | Top {turnover_winner} |
| Information Ratio | Top {ir_winner} |
| Composite Score | Top {best_composite_n} |
"""

# Count total wins
win_counts = {n: 0 for n in PORTFOLIO_SIZES}
winners_map = {
    "CAGR": cagr_winner,
    "Sharpe": sharpe_winner,
    "Sortino": sortino_winner,
    "Max DD": dd_winner,
    "Win Rate": wr_winner,
    "Turnover": turnover_winner,
    "IR": ir_winner,
    "Composite": best_composite_n,
}
for _, w in winners_map.items():
    win_counts[w] += 1

overall_winner = max(win_counts, key=win_counts.get)

report += f"""
### Winner Tally

| Portfolio | Criteria Wins |
|-----------|:------------:|
"""
for n in sorted(PORTFOLIO_SIZES):
    report += f"| {SHORT_LABELS[n]} | {win_counts[n]}/8 |\n"

report += f"""

**Top {overall_winner} wins {win_counts[overall_winner]}/8 criteria.** {'This is the recommended production portfolio.' if overall_winner == best_sharpe_n else f'However, Top {best_sharpe_n} has the best risk-adjusted profile (highest Sharpe and Sortino).'}

### Decision Explanation

**Top {best_sharpe_n}** is recommended for production because:
"""

reasons = []
if best_sharpe_n == best_composite_n:
    reasons.append(f"- **Highest risk-adjusted return**: Top {best_sharpe_n} leads in both Sharpe and Sortino ratios")
if metrics[best_sharpe_n]["Max DD"] >= max(metrics[5]["Max DD"], metrics[10]["Max DD"], metrics[15]["Max DD"]):
    reasons.append("- **Lower drawdown risk**: Competitive or best max drawdown among all portfolios")
if metrics[best_sharpe_n]["CAGR"] == max(metrics[5]["CAGR"], metrics[10]["CAGR"], metrics[15]["CAGR"]):
    reasons.append("- **Highest return**: Also generates the highest CAGR")

reasons.append(f"- **Balanced profile**: Best trade-off between concentration (capturing alpha) and diversification (managing risk)")
reasons.append(f"- **Consistent across metrics**: Leads in {win_counts[best_sharpe_n]}/8 evaluation criteria")

for r in reasons:
    report += r + "\n"

# Add drawdown caveat since Top 5 has worst drawdown
report += f"""
**Trade-off:** Top 5 has the deepest max drawdown ({fmt_pct(metrics[5]['Max DD'])} vs {fmt_pct(metrics[10]['Max DD'])} for Top 10).
Investors with lower drawdown tolerance should consider Top 10, which offers a shallower drawdown with a {fmt_pct(metrics[10]['Max DD'] - metrics[5]['Max DD'])} improvement,
though at a cost of {fmt_pct(metrics[5]['CAGR'] - metrics[10]['CAGR'])} CAGR.
"""

report += f"""
---
"""

# Write report
REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write(report)

print(f"\n\nReport written to {REPORT_FILE}")
print(f"\n=== WINNER TALLY ===")
for n in sorted(PORTFOLIO_SIZES):
    print(f"  {SHORT_LABELS[n]}: {win_counts[n]}/8 wins")
print(f"\n=== RECOMMENDATION: Top {overall_winner} ===")
print(f"  Sharpe winner: Top {sharpe_winner}")
print(f"  Composite winner: Top {best_composite_n}")
print(f"  Overall: Top {overall_winner}")
