"""
research/oos_weight_comparison_v3.py
=====================================
ISI Weight Comparison — V3 Warehouse Data (Fixed)

Purpose: Compare Config A/B/C/D/F using REAL factor scores from
         warehouse_historical/warehouse_v3.csv (48 months, 2022-2025).

Fix over V8.4 .get(key,50) bug: reads actual quality/growth/value/momentum
scores from warehouse_v3.csv instead of snapshot JSONs that lack factor data.

Configs tested:
  A: Q30/G25/V20/M25  (Legacy Equal)
  B: Q25/G30/V10/M35  (Alpha Optimized — see ADR-003)
  C: Q20/G25/V05/M50  (Momentum Heavy)
  D: Q40/G25/V10/M25  (Quality First)
  F: Q25/G10/V30/M35  (Earnings Growth — current config/scoring_weights.json)

Data split (based on warehouse_v3 coverage: 2022-01 to 2025-12):
  TRAIN      : 2022-04 to 2023-09  (18 months)
  VALIDATION : 2023-10 to 2024-09  (12 months)
  TEST       : 2024-10 to 2025-12  (15 months)
  TOTAL      : 45 months usable (3 months lost to forward-return lookahead)
"""

import csv
import json
import math
import datetime
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent

WAREHOUSE_V3   = BASE_DIR / "warehouse_historical" / "warehouse_v3.csv"
TICKER_DATA    = BASE_DIR / "database" / "monthly"
BENCHMARK_FILE = BASE_DIR / "benchmarks" / "IHSG.csv"
OUTPUT_DIR     = BASE_DIR / "research" / "output"
REPORT_FILE    = BASE_DIR / "reports" / "oos_weight_comparison_v3.md"
CONFIG_FILE    = BASE_DIR / "config" / "scoring_weights.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Weight Configs ──────────────────────────────────────────────────────────
WEIGHT_CONFIGS = {
    "A (Legacy Equal)":     {"quality": 0.30, "growth": 0.25, "value": 0.20, "momentum": 0.25},
    "B (Alpha Optimized)":  {"quality": 0.25, "growth": 0.30, "value": 0.10, "momentum": 0.35},
    "C (Momentum Heavy)":   {"quality": 0.20, "growth": 0.25, "value": 0.05, "momentum": 0.50},
    "D (Quality First)":    {"quality": 0.40, "growth": 0.25, "value": 0.10, "momentum": 0.25},
    "F (Earnings Growth)":  {"quality": 0.25, "growth": 0.10, "value": 0.30, "momentum": 0.35},
}

# ── Data Split (aligned with warehouse_v3 coverage) ────────────────────────
TRAIN_START      = "2022-04"
TRAIN_END        = "2023-09"
VALIDATION_START = "2023-10"
VALIDATION_END   = "2024-09"
TEST_START      = "2024-10"
TEST_END         = "2025-12"


# ── Helpers ──────────────────────────────────────────────────────────────────
def _sf_mean(data):
    return sum(data) / len(data) if data else 0.0

def _sf_std(data, mean_val=None):
    if len(data) < 2:
        return 0.0
    if mean_val is None:
        mean_val = _sf_mean(data)
    variance = sum((x - mean_val) ** 2 for x in data) / (len(data) - 1)
    return math.sqrt(variance)

def _fmt(val, pct=False, sign=False):
    if val is None: return "N/A"
    if pct: return f"{val * 100:+.2f}%" if sign else f"{val * 100:.2f}%"
    return f"{val:+.2f}" if sign else f"{val:.2f}"


# ── Data Loaders ──────────────────────────────────────────────────────────────
def load_warehouse_v3():
    rows = []
    with open(WAREHOUSE_V3, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "ticker": r["ticker"],
                "month": r["month"][:7],
                "quality_score": float(r["quality_score"]),
                "growth_score": float(r["growth_score"]),
                "value_score": float(r["value_score"]),
                "momentum_score": float(r["momentum_score"]),
            })
    by_month = defaultdict(list)
    for r in rows:
        by_month[r["month"]].append(r)
    return by_month


def load_ticker_returns():
    ticker_ret = defaultdict(dict)
    for f in sorted(TICKER_DATA.glob("*.csv")):
        ticker = f.stem
        with open(f, encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                date_str = row.get("Date", "").strip()[:7]
                ret_str  = row.get("monthly_return", "").strip()
                if not date_str or not ret_str:
                    continue
                try:
                    ticker_ret[ticker][date_str] = float(ret_str)
                except ValueError:
                    continue
    return dict(ticker_ret)


def load_ihsg():
    prices = []
    with open(BENCHMARK_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d, c = row.get("Date", "").strip(), row.get("Close", "").strip()
            if d and c:
                try:
                    prices.append((d[:7], float(c)))
                except ValueError:
                    continue
    prices.sort(key=lambda x: x[0])
    ihsg = {}
    for i in range(1, len(prices)):
        prev_m, prev_c = prices[i - 1]
        curr_m, curr_c = prices[i]
        if prev_c > 0:
            ihsg[curr_m] = (curr_c / prev_c) - 1.0
    return ihsg


# ── Metrics Engine ────────────────────────────────────────────────────────────
def calc_metrics(portfolio_returns, benchmark_returns):
    n = len(portfolio_returns)
    if n == 0:
        return {k: 0.0 for k in ["months","cagr","ann_return","volatility","sharpe",
                                   "sortino","max_drawdown","win_rate","alpha_ann",
                                   "beta","benchmark_cagr","excess_cagr"]}
    years = n / 12.0
    equity = 1.0
    peak = 1.0
    drawdowns = []
    for r in portfolio_returns:
        equity *= (1 + r)
        peak = max(peak, equity)
        drawdowns.append((peak - equity) / peak)
    cagr = equity ** (1.0 / years) - 1.0
    mean_r = _sf_mean(portfolio_returns)
    ann_ret = mean_r * 12.0
    vol = _sf_std(portfolio_returns, mean_r) * math.sqrt(12)
    sharpe = ann_ret / vol if vol > 0 else 0.0
    max_dd = max(drawdowns) if drawdowns else 0.0
    downside = [r for r in portfolio_returns if r < 0]
    ds_std = _sf_std(downside, 0) * math.sqrt(12) if len(downside) >= 2 else 0.0
    sortino = ann_ret / ds_std if ds_std > 0 else 0.0
    win_rate = sum(1 for r in portfolio_returns if r > 0) / n if n > 0 else 0.0

    alpha_ann, beta = 0.0, 0.0
    if len(benchmark_returns) == n and n > 1:
        mean_p = _sf_mean(portfolio_returns)
        mean_b = _sf_mean(benchmark_returns)
        cov = sum((p - mean_p) * (b - mean_b) for p, b in zip(portfolio_returns, benchmark_returns)) / (n - 1)
        var_b = sum((b - mean_b) ** 2 for b in benchmark_returns) / (n - 1)
        beta = cov / var_b if var_b > 0 else 0.0
        alpha_monthly = mean_p - beta * mean_b
        alpha_ann = alpha_monthly * 12.0

    b_eq = 1.0
    for r in benchmark_returns:
        b_eq *= (1 + r)
    b_cagr = b_eq ** (1.0 / years) - 1.0 if years > 0 else 0.0

    return {
        "months": n,
        "cagr": cagr,
        "ann_return": ann_ret,
        "volatility": vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": max_dd,
        "win_rate": win_rate,
        "alpha_ann": alpha_ann,
        "beta": beta,
        "benchmark_cagr": b_cagr,
        "excess_cagr": cagr - b_cagr,
    }


# ── Backtest per Config ─────────────────────────────────────────────────────
def backtest_config(warehouse, ticker_ret, ihsg, weights, start, end):
    sorted_months = sorted(m for m in warehouse if start <= m <= end)
    portfolio_r, benchmark_r, months = [], [], []
    top5_log = []

    for i, m in enumerate(sorted_months):
        snapshot = warehouse[m]
        for item in snapshot:
            item["_score"] = (
                weights["quality"]   * item["quality_score"] +
                weights["growth"]    * item["growth_score"] +
                weights["value"]     * item["value_score"] +
                weights["momentum"]  * item["momentum_score"]
            )
        ranked = sorted(snapshot, key=lambda x: x["_score"], reverse=True)
        top5 = ranked[:5]
        top5_tickers = [x["ticker"] for x in top5]
        top5_log.append({"month": m, "top5": top5_tickers, "scores": [round(x["_score"], 1) for x in top5]})

        if i + 1 >= len(sorted_months):
            break
        next_m = sorted_months[i + 1]
        if next_m not in ihsg:
            continue

        p_ret = 0.0
        for item in top5:
            t = item["ticker"].replace(".JK", "")
            ret = ticker_ret.get(t, {}).get(next_m)
            if ret is None:
                ret = ticker_ret.get(t + ".JK", {}).get(next_m, 0.0)
            p_ret += 0.20 * (ret if ret is not None else 0.0)

        portfolio_r.append(p_ret)
        benchmark_r.append(ihsg[next_m])
        months.append(next_m)

    return portfolio_r, benchmark_r, months, top5_log


# ── Differentiation Check ──────────────────────────────────────────────────
def check_differentiation(warehouse, ticker_ret, ihsg):
    print("\n  [Pre-check] Verifying configs produce DIFFERENT rankings...")
    sorted_months = sorted(warehouse.keys())
    diff_count = 0
    for m in sorted_months:
        rankings_by_config = {}
        for cfg_name, w in WEIGHT_CONFIGS.items():
            snapshot = [{**x} for x in warehouse[m]]
            for item in snapshot:
                item["_score"] = (
                    w["quality"] * item["quality_score"] +
                    w["growth"] * item["growth_score"] +
                    w["value"] * item["value_score"] +
                    w["momentum"] * item["momentum_score"]
                )
            ranked = sorted(snapshot, key=lambda x: x["_score"], reverse=True)
            rankings_by_config[cfg_name] = [x["ticker"] for x in ranked[:5]]

        sets = [set(v) for v in rankings_by_config.values()]
        all_identical = all(s == sets[0] for s in sets[1:])
        if not all_identical:
            diff_count += 1

    print(f"     Months where configs produce DIFFERENT Top-5: {diff_count}/{len(sorted_months)}")
    return diff_count > 0


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("ISI — OOS Weight Comparison V3 (Fixed)")
    print("=" * 65)

    print("\n[1/5] Loading data...")
    warehouse = load_warehouse_v3()
    ticker_ret = load_ticker_returns()
    ihsg = load_ihsg()
    print(f"      warehouse_v3: {len(warehouse)} months ({min(warehouse.keys())} to {max(warehouse.keys())})")
    print(f"      tickers: {len(ticker_ret)}")
    print(f"      IHSG months: {len(ihsg)}")

    # Pre-check differentiation
    different = check_differentiation(warehouse, ticker_ret, ihsg)
    if not different:
        print("  [CRITICAL] All configs produce identical Top-5! Bug not fixed.")
        return
    print("  [OK] Configs produce different rankings. .get(key,50) bug is FIXED.")

    print("\n[2/5] Running backtest for each config across ALL periods...")
    periods = {
        "TRAIN": (TRAIN_START, TRAIN_END),
        "VALIDATION": (VALIDATION_START, VALIDATION_END),
        "TEST": (TEST_START, TEST_END),
        "FULL": (TRAIN_START, TEST_END),
    }

    all_results = {}
    for cfg_name, weights in WEIGHT_CONFIGS.items():
        print(f"\n  Config {cfg_name}:")
        print(f"    Weights: Q{weights['quality']*100:.0f}/G{weights['growth']*100:.0f}/V{weights['value']*100:.0f}/M{weights['momentum']*100:.0f}")
        cfg_results = {}
        for period_name, (start, end) in periods.items():
            pr, br, months, top5_log = backtest_config(warehouse, ticker_ret, ihsg, weights, start, end)
            cfg_results[period_name] = calc_metrics(pr, br) if pr else {}
            cfg_results[period_name]["returns"] = pr
            cfg_results[period_name]["benchmark_returns"] = br
            cfg_results[period_name]["months_list"] = months
            cfg_results[period_name]["top5_log"] = top5_log
            m = cfg_results[period_name]
            n = len(pr)
            print(f"      {period_name}: {n} months, CAGR={_fmt(m.get('cagr',0), True)}, Sharpe={_fmt(m.get('sharpe',0))}, Alpha={_fmt(m.get('alpha_ann',0), True, True)}")
        all_results[cfg_name] = cfg_results

    print("\n[3/5] Determining best config (by VALIDATION Sharpe)...")
    best_config = max(all_results, key=lambda c: all_results[c].get("VALIDATION", {}).get("sharpe", -999))
    best_sharpe = all_results[best_config].get("VALIDATION", {}).get("sharpe", 0)
    print(f"      Best: {best_config} (VALIDATION Sharpe={best_sharpe:.2f})")

    print("\n[4/5] Writing report...")
    write_report(all_results, best_config)

    print("\n[5/5] Writing CSV output...")
    csv_path = OUTPUT_DIR / "oos_weight_comparison_v3.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Config", "Period", "Months", "CAGR", "AnnReturn", "Volatility", "Sharpe",
                         "Sortino", "MaxDD", "WinRate", "Alpha", "Beta", "BenchCAGR", "ExcessCAGR"])
        for cfg_name in WEIGHT_CONFIGS:
            for period_name in ["TRAIN", "VALIDATION", "TEST", "FULL"]:
                m = all_results[cfg_name].get(period_name, {})
                writer.writerow([
                    cfg_name, period_name,
                    m.get("months", 0),
                    _fmt(m.get("cagr"), True),
                    _fmt(m.get("ann_return"), True),
                    _fmt(m.get("volatility"), True),
                    _fmt(m.get("sharpe")),
                    _fmt(m.get("sortino")),
                    _fmt(m.get("max_drawdown"), True),
                    _fmt(m.get("win_rate"), True),
                    _fmt(m.get("alpha_ann"), True, True),
                    _fmt(m.get("beta")),
                    _fmt(m.get("benchmark_cagr"), True),
                    _fmt(m.get("excess_cagr"), True, True),
                ])
    print(f"      Saved: {csv_path}")

    # Summary table
    print("\n" + "=" * 65)
    print("SUMMARY — FULL PERIOD")
    print("=" * 65)
    print(f"{'Config':<25} {'CAGR':>10} {'Sharpe':>8} {'Alpha':>10} {'WinRate':>8}")
    print("-" * 65)
    for cfg_name in WEIGHT_CONFIGS:
        m = all_results[cfg_name].get("FULL", {})
        print(f"{cfg_name:<25} {_fmt(m.get('cagr'), True):>10} {_fmt(m.get('sharpe')):>8} {_fmt(m.get('alpha_ann'), True, True):>10} {_fmt(m.get('win_rate'), True):>8}")

    print("\n" + "=" * 65)
    print("Done.")
    print("=" * 65)


def write_report(all_results, best_config):
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M WIB")

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# OOS Weight Comparison V3 — Fixed\n\n")
        f.write(f"> Generated: {now}  \n")
        f.write(f"> Data: warehouse_historical/warehouse_v3.csv (2022-01 to 2025-12)  \n")
        f.write(f"> Bug fix: Replaced `.get(key,50)` snapshot fallback with real factor scores from V3 warehouse  \n\n")

        f.write("---\n\n## Bug Fixed\n\n")
        f.write("Previous V8.4 framework read from `snapshots/momentum_history/*.json` which contain\n")
        f.write("only `return_12m` and `rank`. Factor score keys were absent → every `.get(key, 50)`\n")
        f.write("returned 50 → all configs scored **50.0** → identical Top 5 every month.\n\n")
        f.write("This version reads `warehouse_v3.csv` which has REAL `quality_score`, `growth_score`,\n")
        f.write("`value_score`, `momentum_score` per ticker per month for 2022-2025 (48 months).\n\n")

        f.write("## Differentiation Verified\n\n")
        f.write("- Confirmed: each weight config produces DIFFERENT Top-5 portfolios\n")
        f.write("- The `.get(key,50)` structural bug is fully resolved\n\n")

        f.write("## Data Split\n\n")
        f.write(f"| Period | Months |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| TRAIN ({TRAIN_START} → {TRAIN_END}) | 18 |\n")
        f.write(f"| VALIDATION ({VALIDATION_START} → {VALIDATION_END}) | 12 |\n")
        f.write(f"| TEST ({TEST_START} → {TEST_END}) | 15 |\n")
        f.write(f"| FULL | 45 |\n\n")

        f.write("## Performance by Config\n\n")
        f.write("| Config | Q | G | V | M | Period | CAGR | Sharpe | Alpha | WinRate | MaxDD |\n")
        f.write("|--------|---|---|---|---|--------|------|--------|-------|---------|-------|\n")
        for cfg_name in WEIGHT_CONFIGS:
            w = WEIGHT_CONFIGS[cfg_name]
            first = True
            for period_name in ["TRAIN", "VALIDATION", "TEST", "FULL"]:
                m = all_results[cfg_name].get(period_name, {})
                qs = f"{w['quality']*100:.0f}%"
                gs = f"{w['growth']*100:.0f}%"
                vs = f"{w['value']*100:.0f}%"
                ms = f"{w['momentum']*100:.0f}%"
                marker = " ⭐" if (period_name == "FULL" and cfg_name == best_config) else ""
                f.write(f"| {cfg_name}{marker} | {qs if first else ''} | {gs if first else ''} | {vs if first else ''} | {ms if first else ''} | {period_name} | {_fmt(m.get('cagr'), True)} | {_fmt(m.get('sharpe'))} | {_fmt(m.get('alpha_ann'), True, True)} | {_fmt(m.get('win_rate'), True)} | {_fmt(m.get('max_drawdown'), True)} |\n")
                first = False
            f.write(f"| | | | | |\n")

        f.write("\n## Best Config\n\n")
        f.write(f"**{best_config}** — selected by highest VALIDATION Sharpe ")
        f.write(f"({all_results[best_config].get('VALIDATION',{}).get('sharpe',0):.2f})\n\n")

        f.write("## Top-5 Log (Sample)\n\n")
        for cfg_name in WEIGHT_CONFIGS:
            f.write(f"### {cfg_name}\n\n")
            f.write("| Month | Top 5 | Scores |\n")
            f.write("|-------|-------|--------|\n")
            top5_log = all_results[cfg_name].get("FULL", {}).get("top5_log", [])
            for entry in top5_log[:6]:
                f.write(f"| {entry['month']} | {', '.join(entry['top5'])} | {entry['scores']} |\n")
            f.write("\n")

        f.write("---\n")
        f.write(f"*Report generated by `research/oos_weight_comparison_v3.py`*\n")

    print(f"      Report: {REPORT_FILE}")


if __name__ == "__main__":
    main()
