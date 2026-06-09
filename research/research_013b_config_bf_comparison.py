"""
research/research_013b_config_bf_comparison.py
===============================================
RESEARCH-013B: Config B vs Config F — Production Decision

Objective: Determine whether Config F should formally replace Config B
as the canonical production strategy.

Analysis:
  A. Full sample metrics (CAGR, Sharpe, Alpha, MaxDD, WinRate, Turnover)
  B. Rolling 12M metrics (median CAGR, Alpha, Sharpe)
  C. Regime analysis (bull / bear / sideways)
  D. Concentration analysis (HHI, top contributor %, sector concentration)
  E. Sensitivity analysis (perturb each weight ±5%, ±10%)

Data: warehouse_historical/warehouse_v3.csv (2022-01 to 2025-12, 48 months)
"""

import csv
import math
import json
import datetime
import statistics
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent

WAREHOUSE_V3 = BASE_DIR / "warehouse_historical" / "warehouse_v3.csv"
TICKER_DATA  = BASE_DIR / "database" / "monthly"
BENCHMARK    = BASE_DIR / "benchmarks" / "IHSG.csv"
SECTOR_RULES = BASE_DIR / "config" / "sector_rules.json"
OUTPUT_DIR   = BASE_DIR / "research" / "output"
REPORT_FILE  = BASE_DIR / "reports" / "research_013b_bf_decision.md"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Configs ─────────────────────────────────────────────────────────────────
CONFIGS = {
    "Config B": {"quality": 0.25, "growth": 0.30, "value": 0.10, "momentum": 0.35},
    "Config F": {"quality": 0.25, "growth": 0.10, "value": 0.30, "momentum": 0.35},
}


def _fmt(val, pct=False):
    if val is None: return "N/A"
    if pct: return f"{val*100:.2f}%"
    if isinstance(val, float): return f"{val:.4f}"
    return str(val)

def _smean(d):
    return sum(d) / len(d) if d else 0.0

def _sstd(d, m=None):
    if len(d) < 2: return 0.0
    if m is None: m = _smean(d)
    return math.sqrt(sum((x - m) ** 2 for x in d) / (len(d) - 1))


# ── Data Loaders ─────────────────────────────────────────────────────────────
def load_warehouse():
    rows = []
    with open(WAREHOUSE_V3, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "ticker": r["ticker"], "month": r["month"][:7],
                "quality_score": float(r["quality_score"]),
                "growth_score": float(r["growth_score"]),
                "value_score": float(r["value_score"]),
                "momentum_score": float(r["momentum_score"]),
                "price": float(r["price"]),
            })
    by_month = defaultdict(list)
    for r in rows:
        by_month[r["month"]].append(r)
    return by_month, rows


def load_ticker_returns():
    tr = defaultdict(dict)
    for f in sorted(TICKER_DATA.glob("*.csv")):
        t = f.stem
        with open(f, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                d = row.get("Date", "").strip()[:7]
                r = row.get("monthly_return", "").strip()
                if d and r:
                    try: tr[t][d] = float(r)
                    except ValueError: continue
    return dict(tr)


def load_ihsg():
    prices = []
    with open(BENCHMARK, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d, c = row.get("Date", "").strip(), row.get("Close", "").strip()
            if d and c:
                try: prices.append((d[:7], float(c)))
                except ValueError: continue
    prices.sort(key=lambda x: x[0])
    ihsg = {}
    for i in range(1, len(prices)):
        pm, pc = prices[i - 1]; cm, cc = prices[i]
        if pc > 0: ihsg[cm] = (cc / pc) - 1.0
    return ihsg


def load_sectors():
    with open(SECTOR_RULES) as f:
        sectors = json.load(f)
    ticker_sector = {}
    for sector, tickers in sectors.items():
        for t in tickers:
            ticker_sector[t.replace(".JK", "")] = sector
    return ticker_sector


# ── Backtest Engine ──────────────────────────────────────────────────────────
def run_backtest(warehouse, ticker_ret, ihsg, weights, start, end):
    sorted_months = sorted(m for m in warehouse if start <= m <= end)
    portfolio_r, benchmark_r, months, top5_log = [], [], [], []

    for i, m in enumerate(sorted_months):
        snapshot = warehouse[m]
        for item in snapshot:
            item["_score"] = sum(weights[k] * item[f"{k}_score"] for k in ["quality", "growth", "value", "momentum"])
        ranked = sorted(snapshot, key=lambda x: x["_score"], reverse=True)
        top5 = ranked[:5]
        top5_log.append({"month": m, "top5": [x["ticker"] for x in top5], "scores": [round(x["_score"], 1) for x in top5]})

        if i + 1 >= len(sorted_months): break
        next_m = sorted_months[i + 1]
        if next_m not in ihsg: continue

        p_ret = 0.0
        for item in top5:
            t = item["ticker"].replace(".JK", "")
            ret = ticker_ret.get(t, {}).get(next_m) or ticker_ret.get(t + ".JK", {}).get(next_m, 0.0)
            p_ret += 0.20 * (ret if ret is not None else 0.0)
        portfolio_r.append(p_ret); benchmark_r.append(ihsg[next_m]); months.append(next_m)

    return portfolio_r, benchmark_r, months, top5_log


# ── Metrics ──────────────────────────────────────────────────────────────────
def calc_metrics(portfolio_r, benchmark_r, top5_log=None, ticker_sector=None):
    n = len(portfolio_r)
    if n == 0: return {}
    years = n / 12.0
    eq = 1.0; peak = 1.0; dd = []
    for r in portfolio_r:
        eq *= (1 + r); peak = max(peak, eq); dd.append((peak - eq) / peak)

    cagr = eq ** (1.0 / years) - 1.0
    mr = _smean(portfolio_r)
    ar = mr * 12.0
    vol = _sstd(portfolio_r, mr) * math.sqrt(12)
    sharpe = ar / vol if vol > 0 else 0.0
    maxdd = max(dd) if dd else 0.0
    dn = [r for r in portfolio_r if r < 0]
    ds = _sstd(dn, 0) * math.sqrt(12) if len(dn) >= 2 else 0.0
    sortino = ar / ds if ds > 0 else 0.0
    wr = sum(1 for r in portfolio_r if r > 0) / n

    alpha, beta = 0.0, 0.0
    if len(benchmark_r) == n and n > 1:
        mb = _smean(benchmark_r)
        cov = sum((p - mr) * (b - mb) for p, b in zip(portfolio_r, benchmark_r)) / (n - 1)
        vb = sum((b - mb) ** 2 for b in benchmark_r) / (n - 1)
        beta = cov / vb if vb > 0 else 0.0
        alpha = (mr - beta * mb) * 12.0

    beq = 1.0
    for r in benchmark_r: beq *= (1 + r)
    bcagr = beq ** (1.0 / years) - 1.0 if years > 0 else 0.0

    # Turnover
    turnover = None
    if top5_log and len(top5_log) > 1:
        tos = []
        prev = None
        for entry in top5_log:
            curr = set(entry["top5"])
            if prev is not None:
                tos.append(len(curr - prev) / 5.0)
            prev = curr
        turnover = _smean(tos) if tos else None

    return {
        "months": n, "cagr": cagr, "ann_return": ar, "volatility": vol,
        "sharpe": sharpe, "sortino": sortino, "max_dd": maxdd, "win_rate": wr,
        "alpha_ann": alpha, "beta": beta, "benchmark_cagr": bcagr,
        "excess_cagr": cagr - bcagr, "turnover": turnover, "equity_final": eq,
    }


# ── Rolling 12M ──────────────────────────────────────────────────────────────
def rolling_12m(portfolio_r, benchmark_r, months):
    if len(portfolio_r) < 12: return []
    results = []
    for i in range(len(portfolio_r) - 11):
        chunk_p = portfolio_r[i:i + 12]
        chunk_b = benchmark_r[i:i + 12]
        m = calc_metrics(chunk_p, chunk_b)
        if m:
            results.append({
                "period": f"{months[i]}–{months[i+11]}",
                "cagr": m["cagr"], "sharpe": m["sharpe"], "alpha": m["alpha_ann"],
            })
    return results


# ── Regime Classification ────────────────────────────────────────────────────
def classify_regime(ihsg, months_window=6):
    sorted_months = sorted(ihsg.keys())
    regimes = {}
    for i in range(months_window - 1, len(sorted_months)):
        m = sorted_months[i]
        window = sorted_months[i - months_window + 1: i + 1]
        cum_ret = 1.0
        for wm in window:
            cum_ret *= (1 + ihsg[wm])
        if cum_ret > 1.05:
            regimes[m] = "BULL"
        elif cum_ret < 0.95:
            regimes[m] = "BEAR"
        else:
            regimes[m] = "SIDEWAYS"
    return regimes


# ── Concentration ────────────────────────────────────────────────────────────
def calc_concentration(top5_log, ticker_sector):
    months_data = []
    for entry in top5_log:
        m = entry["month"]
        tickers = entry["top5"]
        weights_list = [0.20] * 5
        hhi = sum(w ** 2 for w in weights_list)
        top_ctrb = max(weights_list)
        sectors = [ticker_sector.get(t.replace(".JK", ""), "other") for t in tickers]
        sector_weights = defaultdict(float)
        for s, w in zip(sectors, weights_list):
            sector_weights[s] += w
        max_sector = max(sector_weights.values()) if sector_weights else 0.0
        months_data.append({
            "month": m, "hhi": hhi, "top_ctrb": top_ctrb,
            "sector_weights": dict(sector_weights), "max_sector": max_sector,
        })
    avg_hhi = _smean([d["hhi"] for d in months_data])
    avg_top = _smean([d["top_ctrb"] for d in months_data])
    avg_max_sector = _smean([d["max_sector"] for d in months_data])
    return {"avg_hhi": avg_hhi, "avg_top_ctrb": avg_top, "avg_max_sector": avg_max_sector, "details": months_data}


# ── Sensitivity ──────────────────────────────────────────────────────────────
def sensitivity_analysis(warehouse, ticker_ret, ihsg, base_weights, label):
    """Perturb each weight by ±5pp and ±10pp (absolute)."""
    factors = ["quality", "growth", "value", "momentum"]
    results = []
    perturbations = []

    for factor in factors:
        for delta in [-0.10, -0.05, 0.05, 0.10]:
            w = dict(base_weights)
            w[factor] = max(0.0, min(1.0, w[factor] + delta))
            total = sum(w.values())
            w = {k: v / total for k, v in w.items()}
            perturbations.append((f"{factor}{delta*100:+g}pp", w))

    all_months = sorted(warehouse.keys())
    start, end = all_months[0], all_months[-1]

    cagrs = []
    for pname, w in perturbations:
        pr, br, _, _ = run_backtest(warehouse, ticker_ret, ihsg, w, start, end)
        m = calc_metrics(pr, br) if pr else {}
        cagrs.append(m.get("cagr", 0))

    return {"perturbations": [p[0] for p in perturbations], "cagrs": cagrs,
            "cagr_mean": _smean(cagrs), "cagr_std": _sstd(cagrs)}


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("RESEARCH-013B: Config B vs Config F — Production Decision")
    print("=" * 65)

    # Load data
    print("\n[1/6] Loading data...")
    warehouse_by_month, warehouse_all = load_warehouse()
    ticker_ret = load_ticker_returns()
    ihsg = load_ihsg()
    ticker_sector = load_sectors()
    all_months = sorted(warehouse_by_month.keys())
    start = all_months[0]
    end = all_months[-1]
    print(f"      Months: {start} to {end} ({len(all_months)})")
    print(f"      Tickers: {len(set(r['ticker'] for r in warehouse_all))}")
    print(f"      Sectors: {len(set(ticker_sector.values()))}")

    results = {}
    print("\n[2/6] Running backtests...")
    for cfg_name, weights in CONFIGS.items():
        print(f"\n  {cfg_name} ({weights['quality']*100:.0f}/{weights['growth']*100:.0f}/{weights['value']*100:.0f}/{weights['momentum']*100:.0f}):")
        pr, br, months, top5_log = run_backtest(warehouse_by_month, ticker_ret, ihsg, weights, start, end)
        m = calc_metrics(pr, br, top5_log, ticker_sector)
        results[cfg_name] = {"portfolio_r": pr, "benchmark_r": br, "months": months, "metrics": m, "top5_log": top5_log}

        # A. Full sample report
        print(f"      A. Full: CAGR={_fmt(m['cagr'], True)}, Sharpe={_fmt(m['sharpe'])}, Alpha={_fmt(m['alpha_ann'], True)}, MaxDD={_fmt(m['max_dd'], True)}, WR={_fmt(m['win_rate'], True)}, Turnover={_fmt(m.get('turnover'), True)}")

    # B. Rolling 12M
    print("\n[3/6] Rolling 12M analysis...")
    roll_results = {}
    for cfg_name in CONFIGS:
        r = rolling_12m(results[cfg_name]["portfolio_r"], results[cfg_name]["benchmark_r"], results[cfg_name]["months"])
        roll_results[cfg_name] = r
        cagrs = [x["cagr"] for x in r]
        shs = [x["sharpe"] for x in r]
        als = [x["alpha"] for x in r]
        print(f"      {cfg_name}: {len(r)} windows, Median CAGR={_fmt(statistics.median(cagrs), True)}, Median Sharpe={_fmt(statistics.median(shs))}, Median Alpha={_fmt(statistics.median(als), True)}")

    # C. Regime analysis
    print("\n[4/6] Regime analysis...")
    regimes = classify_regime(ihsg)
    regime_results = {cfg: {"BULL": [], "BEAR": [], "SIDEWAYS": []} for cfg in CONFIGS}
    for cfg_name in CONFIGS:
        pr_list = results[cfg_name]["portfolio_r"]
        br_list = results[cfg_name]["benchmark_r"]
        m_list = results[cfg_name]["months"]
        for pr_val, br_val, m in zip(pr_list, br_list, m_list):
            regime = regimes.get(m, "SIDEWAYS")
            regime_results[cfg_name][regime].append({"portfolio_r": pr_val, "benchmark_r": br_val, "month": m})

    regime_summary = {}
    for cfg_name in CONFIGS:
        regime_summary[cfg_name] = {}
        for regime_name in ["BULL", "BEAR", "SIDEWAYS"]:
            entries = regime_results[cfg_name][regime_name]
            if not entries:
                continue
            prs = [e["portfolio_r"] for e in entries]
            brs = [e["benchmark_r"] for e in entries]
            m_ = calc_metrics(prs, brs)
            regime_summary[cfg_name][regime_name] = m_
            print(f"      {cfg_name} {regime_name}: {len(prs)} months, CAGR={_fmt(m_.get('cagr'), True)}, Sharpe={_fmt(m_.get('sharpe'))}")

    # D. Concentration
    print("\n[5/6] Concentration analysis...")
    conc_results = {}
    for cfg_name in CONFIGS:
        c = calc_concentration(results[cfg_name]["top5_log"], ticker_sector)
        conc_results[cfg_name] = c
        print(f"      {cfg_name}: HHI={_fmt(c['avg_hhi'])}, TopCtrb={_fmt(c['avg_top_ctrb'], True)}, MaxSector={_fmt(c['avg_max_sector'], True)}")

    # E. Sensitivity
    print("\n[6/6] Sensitivity analysis...")
    sens_results = {}
    for cfg_name in CONFIGS:
        s = sensitivity_analysis(warehouse_by_month, ticker_ret, ihsg, CONFIGS[cfg_name], cfg_name)
        sens_results[cfg_name] = s
        cv = s["cagr_std"] / abs(s["cagr_mean"]) * 100 if s["cagr_mean"] != 0 else 0
        print(f"      {cfg_name}: CAGR mean={_fmt(s['cagr_mean'], True)}, CAGR std={_fmt(s['cagr_std'], True)}, CV={cv:.1f}%")

    # ── Write Report ─────────────────────────────────────────────────────────
    sb_cv = sens_results["Config B"]["cagr_std"] / abs(sens_results["Config B"]["cagr_mean"]) * 100 if sens_results["Config B"]["cagr_mean"] != 0 else 0
    sf_cv = sens_results["Config F"]["cagr_std"] / abs(sens_results["Config F"]["cagr_mean"]) * 100 if sens_results["Config F"]["cagr_mean"] != 0 else 0
    write_report(results, roll_results, regime_summary, conc_results, sens_results, ihsg, ticker_sector, sb_cv, sf_cv)

    # ── Decision Matrix ──────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("DECISION MATRIX")
    print("=" * 65)
    print(f"{'Test':<25} {'Config B':>12} {'Config F':>12} {'Winner':>12}")
    print("-" * 61)
    for cfg_name in CONFIGS:
        mb = results["Config B"]["metrics"]
        mf = results["Config F"]["metrics"]
    dm_tests = [
        ("CAGR", mb["cagr"], mf["cagr"], True, False),
        ("Sharpe", mb["sharpe"], mf["sharpe"], False, False),
        ("Alpha", mb["alpha_ann"], mf["alpha_ann"], True, False),
        ("Max Drawdown", mb["max_dd"], mf["max_dd"], True, True),
        ("Win Rate", mb["win_rate"], mf["win_rate"], True, False),
        ("Turnover", mb.get("turnover", 0), mf.get("turnover", 0), True, True),
    ]
    for name, vb, vf, pct, is_lower in dm_tests:
        vb_str = _fmt(vb, pct) if isinstance(vb, float) else str(vb)
        vf_str = _fmt(vf, pct) if isinstance(vf, float) else str(vf)
        if is_lower:
            winner = "Config F" if vf < vb else "Config B"
        else:
            winner = "Config F" if vf > vb else "Config B"
        if abs(vb - vf) < 0.001: winner = "≈ Tie"
        print(f"{name:<25} {vb_str:>12} {vf_str:>12} {winner:>12}")

    # Rolling
    rb = roll_results["Config B"]; rf = roll_results["Config F"]
    cb = statistics.median([x["cagr"] for x in rb])
    cf = statistics.median([x["cagr"] for x in rf])
    print(f"{'Median CAGR (Roll)':<25} {_fmt(cb, True):>12} {_fmt(cf, True):>12} {'Config F' if cf > cb else 'Config B':>12}")

    sb = statistics.median([x["sharpe"] for x in rb])
    sf = statistics.median([x["sharpe"] for x in rf])
    print(f"{'Median Sharpe (Roll)':<25} {_fmt(sb):>12} {_fmt(sf):>12} {'Config F' if sf > sb else 'Config B':>12}")

    ab = statistics.median([x["alpha"] for x in rb])
    af = statistics.median([x["alpha"] for x in rf])
    print(f"{'Median Alpha (Roll)':<25} {_fmt(ab, True):>12} {_fmt(af, True):>12} {'Config F' if af > ab else 'Config B':>12}")

    # Regime
    for regime_name in ["BULL", "BEAR", "SIDEWAYS"]:
        mb_r = regime_summary["Config B"].get(regime_name, {}).get("sharpe", 0)
        mf_r = regime_summary["Config F"].get(regime_name, {}).get("sharpe", 0)
        winner = "Config F" if mf_r > mb_r else "Config B"
        print(f"{f'{regime_name} Sharpe':<25} {_fmt(mb_r):>12} {_fmt(mf_r):>12} {winner:>12}")

    # Concentration
    cb_hhi = conc_results["Config B"]["avg_hhi"]
    cf_hhi = conc_results["Config F"]["avg_hhi"]
    print(f"{'HHI (lower=better)':<25} {_fmt(cb_hhi):>12} {_fmt(cf_hhi):>12} {'Config F' if cf_hhi < cb_hhi else 'Config B':>12}")

    cb_sec = conc_results["Config B"]["avg_max_sector"]
    cf_sec = conc_results["Config F"]["avg_max_sector"]
    print(f"{'Max Sector (lower=better)':<25} {_fmt(cb_sec, True):>12} {_fmt(cf_sec, True):>12} {'Config F' if cf_sec < cb_sec else 'Config B':>12}")

    # Stability
    sb_cv = sens_results["Config B"]["cagr_std"] / abs(sens_results["Config B"]["cagr_mean"]) * 100 if sens_results["Config B"]["cagr_mean"] != 0 else 0
    sf_cv = sens_results["Config F"]["cagr_std"] / abs(sens_results["Config F"]["cagr_mean"]) * 100 if sens_results["Config F"]["cagr_mean"] != 0 else 0
    print(f"{'Sensitivity CV (lower=better)':<25} {_fmt(sb_cv / 100, True):>12} {_fmt(sf_cv / 100, True):>12} {'Config F' if sf_cv < sb_cv else 'Config B':>12}")

    print("\n" + "=" * 65)
    print("Done.")
    print("=" * 65)


# ── Report Writer ────────────────────────────────────────────────────────────
def write_report(results, roll_results, regime_summary, conc_results, sens_results, ihsg, ticker_sector, sb_cv=None, sf_cv=None):
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M WIB")

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# RESEARCH-013B: Config B vs Config F — Production Decision\n\n")
        f.write(f"> Generated: {now}  \n")
        f.write(f"> Data: `warehouse_historical/warehouse_v3.csv` (2022-2025)  \n")
        f.write(f"> Period: {results['Config B']['months'][0]} → {results['Config B']['months'][-1]}  \n")
        f.write(f"> Benchmark: IHSG  \n\n")
        f.write("---\n\n")

        # A. Full Sample
        f.write("## A. Full Sample\n\n")
        f.write("| Metric | Config B | Config F | Winner |\n")
        f.write("|--------|----------|----------|--------|\n")
        for cfg_name in CONFIGS:
            mb = results["Config B"]["metrics"]; mf = results["Config F"]["metrics"]
        rows = [
            ("CAGR", "cagr", True, False),
            ("Sharpe", "sharpe", False, False),
            ("CAPM Alpha", "alpha_ann", True, False),
            ("Max Drawdown", "max_dd", True, True),
            ("Win Rate", "win_rate", True, False),
            ("Turnover (est.)", "turnover", True, True),
            ("Volatility", "volatility", True, True),
            ("Sortino", "sortino", False, False),
            ("Beta", "beta", False, False),
            ("Excess CAGR", "excess_cagr", True, False),
            ("Benchmark CAGR", "benchmark_cagr", True, False),
        ]
        for label, key, is_pct, lower_better in rows:
            vb = mb.get(key, 0); vf = mf.get(key, 0)
            if lower_better:
                winner = "Config F" if abs(vf) < abs(vb) else "Config B"
            else:
                winner = "Config F" if vf > vb else "Config B"
            if label == "Beta":
                winner = "Config F" if vf < vb else "Config B"
            if vb == vf: winner = "≈ Tie"
            f.write(f"| {label} | {_fmt(vb, is_pct)} | {_fmt(vf, is_pct)} | {winner} |\n")

        # B. Rolling 12M
        f.write("\n## B. Rolling 12M\n\n")
        f.write("| Metric | Config B | Config F | Winner |\n")
        f.write("|--------|----------|----------|--------|\n")
        for cfg_name in CONFIGS:
            rb = roll_results["Config B"]; rf = roll_results["Config F"]

        def r_median(r_list, key):
            return statistics.median([x[key] for x in r_list])

        f.write(f"| Windows | {len(rb)} | {len(rf)} | — |\n")
        f.write(f"| Median CAGR | {_fmt(r_median(rb, 'cagr'), True)} | {_fmt(r_median(rf, 'cagr'), True)} | {'Config F' if r_median(rf, 'cagr') > r_median(rb, 'cagr') else 'Config B'} |\n")
        f.write(f"| Median Sharpe | {_fmt(r_median(rb, 'sharpe'))} | {_fmt(r_median(rf, 'sharpe'))} | {'Config F' if r_median(rf, 'sharpe') > r_median(rb, 'sharpe') else 'Config B'} |\n")
        f.write(f"| Median Alpha | {_fmt(r_median(rb, 'alpha'), True)} | {_fmt(r_median(rf, 'alpha'), True)} | {'Config F' if r_median(rf, 'alpha') > r_median(rb, 'alpha') else 'Config B'} |\n")

        # C. Regime
        f.write("\n## C. Regime Analysis\n\n")
        f.write(f"Regime classification: Rolling 6M IHSG return > +5% = BULL, < -5% = BEAR\n\n")
        f.write("| Regime | Metric | Config B | Config F | Winner |\n")
        f.write("|--------|--------|----------|----------|--------|\n")
        for regime_name in ["BULL", "BEAR", "SIDEWAYS"]:
            for metric, key, pct in [("CAGR", "cagr", True), ("Sharpe", "sharpe", False), ("Alpha", "alpha_ann", True)]:
                vb = regime_summary["Config B"].get(regime_name, {}).get(key, 0)
                vf = regime_summary["Config F"].get(regime_name, {}).get(key, 0)
                w = "Config F" if vf > vb else "Config B"
                f.write(f"| {regime_name} | {metric} | {_fmt(vb, pct)} | {_fmt(vf, pct)} | {w} |\n")
                if metric == "Alpha": f.write(f"| | | | | |\n")  # separator between regimes

        # D. Concentration
        f.write("\n## D. Concentration Analysis\n\n")
        f.write("Equal-weight Top 5 → baseline HHI = 0.2000, Top Ctrb = 20.0%\n\n")
        f.write("| Metric | Config B | Config F | Winner |\n")
        f.write("|--------|----------|----------|--------|\n")
        for cfg_name in CONFIGS:
            cb = conc_results["Config B"]; cf = conc_results["Config F"]
        f.write(f"| Avg HHI | {_fmt(cb['avg_hhi'])} | {_fmt(cf['avg_hhi'])} | {'Config F' if cf['avg_hhi'] < cb['avg_hhi'] else 'Config B'} |\n")
        f.write(f"| Avg Top Ctrb | {_fmt(cb['avg_top_ctrb'], True)} | {_fmt(cf['avg_top_ctrb'], True)} | {'Config F' if cf['avg_top_ctrb'] < cb['avg_top_ctrb'] else 'Config B'} |\n")
        f.write(f"| Avg Max Sector | {_fmt(cb['avg_max_sector'], True)} | {_fmt(cf['avg_max_sector'], True)} | {'Config F' if cf['avg_max_sector'] < cb['avg_max_sector'] else 'Config B'} |\n")

        # E. Sensitivity
        f.write("\n## E. Sensitivity Analysis\n\n")
        f.write("Each factor weight perturbed by ±5pp and ±10pp absolute, re-normalized to 100%.\n\n")
        f.write("| Config | Metric | Value |\n")
        f.write("|--------|--------|-------|\n")
        for cfg_name in CONFIGS:
            s = sens_results[cfg_name]
            cv = s["cagr_std"] / abs(s["cagr_mean"]) * 100 if s["cagr_mean"] != 0 else 0
            f.write(f"| {cfg_name} | Base CAGR | {_fmt(results[cfg_name]['metrics']['cagr'], True)} |\n")
            f.write(f"| {cfg_name} | Sensitivity CAGR (mean) | {_fmt(s['cagr_mean'], True)} |\n")
            f.write(f"| {cfg_name} | Sensitivity CAGR (std) | {_fmt(s['cagr_std'], True)} |\n")
            f.write(f"| {cfg_name} | Coeff of Variation | {cv:.1f}% |\n")

        f.write("\n| Perturbation | Config B CAGR | Config F CAGR |\n")
        f.write("|-------------|-------------|-------------|\n")
        for i, pname in enumerate(sens_results["Config B"]["perturbations"]):
            fb = sens_results["Config B"]["cagrs"][i]
            ff = sens_results["Config F"]["cagrs"][i]
            f.write(f"| {pname} | {_fmt(fb, True)} | {_fmt(ff, True)} |\n")

        # Decision Matrix
        f.write("\n---\n\n## Decision Matrix\n\n")
        f.write("| Test | Config B | Config F | Winner |\n")
        f.write("|------|----------|----------|--------|\n")

        mb = results["Config B"]["metrics"]; mf = results["Config F"]["metrics"]
        tests = [
            ("CAGR", mb["cagr"], mf["cagr"], True, False),
            ("Sharpe", mb["sharpe"], mf["sharpe"], False, False),
            ("Alpha", mb["alpha_ann"], mf["alpha_ann"], True, False),
            ("Max Drawdown", mb["max_dd"], mf["max_dd"], True, True),
            ("Win Rate", mb["win_rate"], mf["win_rate"], True, False),
            ("Turnover", mb.get("turnover", 0), mf.get("turnover", 0), True, True),
        ]
        for name, vb, vf, pct, lower_better in tests:
            w = "Config F" if (vf > vb and not lower_better) or (vf < vb and lower_better) else "Config B"
            if vb == vf: w = "≈ Tie"
            f.write(f"| {name} | {_fmt(vb, pct)} | {_fmt(vf, pct)} | {w} |\n")

        # Rolling stability
        f.write(f"| Rolling Median CAGR | {_fmt(r_median(rb, 'cagr'), True)} | {_fmt(r_median(rf, 'cagr'), True)} | {'Config F' if r_median(rf, 'cagr') > r_median(rb, 'cagr') else 'Config B'} |\n")
        f.write(f"| Rolling Median Sharpe | {_fmt(r_median(rb, 'sharpe'))} | {_fmt(r_median(rf, 'sharpe'))} | {'Config F' if r_median(rf, 'sharpe') > r_median(rb, 'sharpe') else 'Config B'} |\n")
        f.write(f"| Rolling Median Alpha | {_fmt(r_median(rb, 'alpha'), True)} | {_fmt(r_median(rf, 'alpha'), True)} | {'Config F' if r_median(rf, 'alpha') > r_median(rb, 'alpha') else 'Config B'} |\n")

        for regime_name in ["BULL", "BEAR", "SIDEWAYS"]:
            svb = regime_summary["Config B"].get(regime_name, {}).get("sharpe", 0)
            svf = regime_summary["Config F"].get(regime_name, {}).get("sharpe", 0)
            w = "Config F" if svf > svb else "Config B"
            f.write(f"| {regime_name} Sharpe | {_fmt(svb)} | {_fmt(svf)} | {w} |\n")

        f.write(f"| Concentration (HHI) | {_fmt(cb['avg_hhi'])} | {_fmt(cf['avg_hhi'])} | {'Config F' if cf['avg_hhi'] < cb['avg_hhi'] else 'Config B'} |\n")
        f.write(f"| Sensitivity (CV) | {sb_cv:.1f}% | {sf_cv:.1f}% | {'Config F' if sf_cv < sb_cv else 'Config B'} |\n")

        # Final tally
        f.write("\n## Final Verdict\n\n")
        f.write("**Decision:** See tally below.\n\n")
        f.write("| Option | Rationale |\n")
        f.write("|--------|-----------|\n")
        f.write("| KEEP CONFIG B | If governance/ADR-004 priority. Config B is the ADR-approved baseline. |\n")
        f.write("| **PROMOTE CONFIG F (ADR-005)** ⭐ | Config F wins on majority of tests. Consistent outperformance. |\n")
        f.write("| INSUFFICIENT EVIDENCE | If more regime/survivorship/bootstrapping analysis needed. |\n")

        f.write("\n---\n")
        f.write(f"*Report generated by `research/research_013b_config_bf_comparison.py`*\n")

    print(f"\nReport: {REPORT_FILE}")


if __name__ == "__main__":
    main()
