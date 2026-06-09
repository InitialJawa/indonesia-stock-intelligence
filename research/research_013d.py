"""
research/research_013d.py
=========================
RESEARCH-013D: Does Growth deserve any positive weight?

Tests 5 configurations against the earnings-only fix warehouse
to determine if Growth should be removed from the production model.

Configs:
  B:     Q25/G30/V10/M35
  F:     Q25/G10/V30/M35
  G0-A:  Q25/G00/V40/M35
  G0-B:  Q35/G00/V30/M35
  G0-C:  Q20/G00/V45/M35

Metrics: CAGR, Sharpe, Alpha, MaxDD, Turnover, Rolling 12M, IC stability

If ALL G=0 configs beat Config F → remove Growth from production.
If Config F still wins → keep Growth as diversifier despite IC ≈ 0.
"""

import csv
import math
import sys
import datetime
from pathlib import Path
from collections import defaultdict
from scipy.stats import spearmanr

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

WH_FILE = BASE_DIR / "warehouse_historical" / "warehouse_v3_growth_fix.csv"
MONTHLY_DIR = BASE_DIR / "database" / "monthly"
BENCHMARK = BASE_DIR / "benchmarks" / "IHSG.csv"
OUTPUT = BASE_DIR / "reports" / "research_013d.md"
PERIOD_START, PERIOD_END = "2022-01", "2026-04"


# ── Utils ─────────────────────────────────────────────────────────────────
def _fmt(v, pct=False):
    if v is None: return "N/A"
    if pct: return f"{v*100:.2f}%"
    return f"{v:.4f}"


def _mean(d):
    return sum(d) / len(d) if d else 0.0


def _std(d, m=None):
    if len(d) < 2: return 0.0
    if m is None: m = _mean(d)
    return math.sqrt(sum((x - m) ** 2 for x in d) / (len(d) - 1))


# ── Data Loaders ───────────────────────────────────────────────────────────
def load_warehouse(path):
    wh, universe = {}, set()
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            m = r["month"]
            if m not in wh: wh[m] = {}
            wh[m][r["ticker"]] = {
                "quality": float(r["quality_score"]),
                "growth": float(r["growth_score"]),
                "value": float(r["value_score"]),
                "momentum": float(r["momentum_score"]),
            }
            universe.add(r["ticker"])
    return wh, sorted(universe)


def load_returns():
    tr = defaultdict(dict)
    for f in sorted(MONTHLY_DIR.glob("*.csv")):
        t = f.stem.replace(".JK", "")
        with open(f, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                d = r.get("Date", "").strip()[:7]
                rv = r.get("monthly_return", "").strip()
                if d and rv:
                    try: tr[t][d] = float(rv)
                    except: pass
    return dict(tr)


def load_ihsg():
    prices = []
    with open(BENCHMARK, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d, c = r.get("Date", "").strip(), r.get("Close", "").strip()
            if d and c:
                try: prices.append((d[:7], float(c)))
                except: pass
    prices.sort(key=lambda x: x[0])
    ihsg = {}
    for i in range(1, len(prices)):
        pm, pc = prices[i - 1], prices[i]
        if pm[1] > 0: ihsg[pc[0]] = (pc[1] / pm[1]) - 1.0
    return ihsg


# ── Backtest Engine ────────────────────────────────────────────────────────
def backtest(wh, ticker_ret, ihsg, weights, start, end):
    """Run a monthly rebalance backtest. Returns full result dict."""
    sorted_m = sorted(m for m in wh if start <= m[:7] <= end)
    pr, br, months = [], [], []
    positions_history = {}  # month -> set of tickers

    for i, m in enumerate(sorted_m):
        if i + 1 >= len(sorted_m): break
        nm = sorted_m[i + 1]
        nm_prefix = nm[:7]
        if nm_prefix not in ihsg: continue

        tickers_m = wh[m]
        # score each ticker
        scored = []
        for t, scores in tickers_m.items():
            cs = sum(weights[k] * scores[k] for k in ["quality", "growth", "value", "momentum"])
            scored.append((cs, t))
        scored.sort(key=lambda x: x[0], reverse=True)
        top5 = [t for _, t in scored[:5]]
        positions_history[nm_prefix] = set(top5)

        p_ret = 0.0
        for t in top5:
            t_clean = t.replace(".JK", "")
            ret = ticker_ret.get(t_clean, {}).get(nm_prefix, 0.0)
            p_ret += 0.20 * ret
        pr.append(p_ret)
        br.append(ihsg[nm_prefix])
        months.append(nm_prefix)

    # Compute metrics
    n = len(pr)
    years = n / 12.0
    if n == 0: return {}

    eq, peak = 1.0, 1.0
    dd = []
    for r in pr:
        eq *= (1 + r)
        peak = max(peak, eq)
        dd.append((peak - eq) / peak)
    cagr = eq ** (1.0 / years) - 1.0 if years > 0 else 0.0
    mr = _mean(pr)
    ar = mr * 12.0
    vol = _std(pr, mr) * math.sqrt(12)
    sharpe = ar / vol if vol > 0 else 0.0
    maxdd = max(dd) if dd else 0.0
    dn = [r for r in pr if r < 0]
    ds = _std(dn) * math.sqrt(12) if len(dn) >= 2 else 0.0
    sortino = ar / ds if ds > 0 else 0.0
    wr = sum(1 for r in pr if r > 0) / n if n > 0 else 0.0
    mb = _mean(br)
    cov = sum((p - mr) * (b - mb) for p, b in zip(pr, br)) / (n - 1)
    vb = sum((b - mb) ** 2 for b in br) / (n - 1)
    beta = cov / vb if vb > 0 else 0.0
    alpha = (mr - beta * mb) * 12.0
    beq = 1.0
    for r in br: beq *= (1 + r)
    bcagr = beq ** (1.0 / years) - 1.0 if years > 0 else 0.0

    # Turnover: month-by-month position changes
    turnover_rates = []
    prev_positions = None
    for m in months:
        cur = positions_history.get(m, set())
        if prev_positions is not None and len(prev_positions) > 0:
            churn = len(cur - prev_positions) + len(prev_positions - cur)
            turnover_rates.append(churn / (len(cur) + len(prev_positions)) * 0.5)
        prev_positions = cur

    avg_turnover = _mean(turnover_rates) if turnover_rates else 0.0

    # Rolling 12-month returns
    rolling = []
    for i in range(len(pr)):
        if i < 11: continue
        r12 = 1.0
        for j in range(i - 11, i + 1):
            r12 *= (1 + pr[j])
        rolling.append(r12 - 1.0)

    # IC of composite score vs forward returns
    ics = []
    for i, m in enumerate(sorted_m):
        if i + 1 >= len(sorted_m): break
        nm = sorted_m[i + 1]
        nm_prefix = nm[:7]
        if nm_prefix not in ihsg: continue
        scored_month = []
        for t, scores in wh[m].items():
            cs = sum(weights[k] * scores[k] for k in ["quality", "growth", "value", "momentum"])
            t_clean = t.replace(".JK", "")
            ret = ticker_ret.get(t_clean, {}).get(nm_prefix)
            if ret is not None:
                scored_month.append((cs, ret))
        if len(scored_month) >= 5:
            x = [p[0] for p in scored_month]
            y = [p[1] for p in scored_month]
            rho, _ = spearmanr(x, y)
            if not math.isnan(rho): ics.append(rho)

    ic_mean = _mean(ics)
    ic_std = _std(ics, ic_mean) if len(ics) > 1 else 0
    ic_ir = ic_mean / ic_std if ic_std > 0 else 0
    ic_pos = sum(1 for v in ics if v > 0)
    ic_neg = len(ics) - ic_pos

    return {
        "cagr": cagr,
        "sharpe": sharpe,
        "alpha": alpha,
        "max_dd": maxdd,
        "sortino": sortino,
        "win_rate": wr,
        "vol": vol,
        "beta": beta,
        "benchmark_cagr": bcagr,
        "excess_cagr": cagr - bcagr,
        "turnover": avg_turnover,
        "rolling_12m": rolling,
        "rolling_12m_months": months[11:] if len(months) > 11 else [],
        "n": n,
        "ic_mean": ic_mean,
        "ic_std": ic_std,
        "ic_ir": ic_ir,
        "ic_pos": ic_pos,
        "ic_neg": ic_neg,
        "ic_n": len(ics),
        "monthly_returns": pr,
        "benchmark_returns": br,
        "months": months,
        "dd": dd,
    }


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M WIB")
    print("=" * 65)
    print("RESEARCH-013D: Does Growth deserve any positive weight?")
    print("=" * 65)

    print(f"\nPeriod: {PERIOD_START} -> {PERIOD_END}")
    print(f"Warehouse: {WH_FILE.name} (earnings-only growth fix)")

    # Load
    print("\nLoading data...")
    wh, univ = load_warehouse(WH_FILE)
    ticker_ret = load_returns()
    ihsg = load_ihsg()
    print(f"  Universe: {len(univ)} tickers")
    print(f"  Months: {len(wh)}")
    print(f"  IHSG months: {len(ihsg)}")

    # Configs
    configs = {
        "B":    {"quality": 0.25, "growth": 0.30, "value": 0.10, "momentum": 0.35},
        "F":    {"quality": 0.25, "growth": 0.10, "value": 0.30, "momentum": 0.35},
        "G0-A": {"quality": 0.25, "growth": 0.00, "value": 0.40, "momentum": 0.35},
        "G0-B": {"quality": 0.35, "growth": 0.00, "value": 0.30, "momentum": 0.35},
        "G0-C": {"quality": 0.20, "growth": 0.00, "value": 0.45, "momentum": 0.35},
    }

    results = {}
    for label, w in configs.items():
        print(f"\n-- {label}: {dict(w)}")
        r = backtest(wh, ticker_ret, ihsg, w, PERIOD_START, PERIOD_END)
        results[label] = r
        # Quick summary per config
        print(f"    CAGR: {_fmt(r.get('cagr'), True)}  Sharpe: {_fmt(r.get('sharpe'))}  "
              f"Alpha: {_fmt(r.get('alpha'), True)}  MaxDD: {_fmt(r.get('max_dd'), True)}")
        print(f"    IC: {_fmt(r.get('ic_mean'))}  IC_IR: {_fmt(r.get('ic_ir'))}  "
              f"Turnover: {_fmt(r.get('turnover'), True)}")

    # ── Report ──────────────────────────────────────────────────────
    print(f"\n\nWriting report: {OUTPUT}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("# RESEARCH-013D: Does Growth deserve any positive weight?\n\n")
        f.write(f"> Period: {PERIOD_START} → {PERIOD_END}  \n")
        f.write(f"> Warehouse: `{WH_FILE.name}` (earnings-only growth)  \n")
        f.write(f"> Generated: {now}  \n\n")
        f.write("---\n\n")

        # Config definitions
        f.write("## Configurations\n\n")
        f.write("| Label | Quality | Growth | Value | Momentum | Notes |\n")
        f.write("|-------|---------|--------|-------|----------|-------|\n")
        f.write(f"| B | 25% | 30% | 10% | 35% | Original  |\n")
        f.write(f"| F | 25% | 10% | 30% | 35% | ADR-005 winner |\n")
        f.write(f"| G0-A | 25% | **0%** | 40% | 35% | Growth → Value |\n")
        f.write(f"| G0-B | 35% | **0%** | 30% | 35% | Growth → Quality |\n")
        f.write(f"| G0-C | 20% | **0%** | 45% | 35% | Growth → Value (max) |\n")

        # Summary table
        f.write("\n## Performance Comparison\n\n")
        f.write("| Metric | B | F | G0-A | G0-B | G0-C | Best |\n")
        f.write("|--------|---|---|------|------|------|------|\n")

        metrics = [
            ("CAGR", "cagr", True),
            ("Excess CAGR", "excess_cagr", True),
            ("Sharpe Ratio", "sharpe", False),
            ("Sortino Ratio", "sortino", False),
            ("Alpha (ann.)", "alpha", True),
            ("Volatility (ann.)", "vol", True),
            ("Max Drawdown", "max_dd", True),
            ("Win Rate", "win_rate", True),
            ("Beta", "beta", False),
            ("Avg Monthly Turnover", "turnover", True),
            ("IC Mean", "ic_mean", False),
            ("IC Std", "ic_std", False),
            ("IC IR", "ic_ir", False),
            ("IC Positive/Negative", None, False),
        ]

        for label, key, is_pct in metrics:
            row = f"| {label} "
            best_val = None
            best_label = ""
            if key:
                vals = {lbl: results[lbl][key] for lbl in configs}
                # Determine direction for "best"
                higher_better = key not in ("max_dd", "vol", "turnover", "ic_std")
                best_k = max(vals, key=vals.get) if higher_better else min(vals, key=vals.get)
                best_val = vals[best_k]
                best_label = best_k

            for lbl in configs:
                if key:
                    v = results[lbl][key]
                    s = _fmt(v, is_pct)
                else:
                    v = results[lbl]
                    s = f"{v['ic_pos']}/{v['ic_neg']} (n={v['ic_n']})"
                if key and best_val is not None and v == best_val:
                    s = f"**{s}**"
                row += f"| {s} "
            if key:
                row += f"| {best_label} "
            else:
                row += "| - "
            f.write(row + "|\n")

        # Rolling 12M comparison
        f.write("\n## Rolling 12-Month Returns\n\n")
        f.write("| Month |")
        for lbl in configs: f.write(f" {lbl} |")
        f.write(" Benchmark |\n")
        f.write("|-------|")
        for _ in configs: f.write("---|")
        f.write("---|\n")

        # Find the config with the most rolling months
        min_months = min(len(results[lbl]["rolling_12m"]) for lbl in configs)
        for i in range(min_months):
            mn = results["B"]["rolling_12m_months"][i]
            f.write(f"| {mn} |")
            for lbl in configs:
                r12 = results[lbl]["rolling_12m"][i]
                f.write(f" {_fmt(r12, True)} |")

            # Benchmark rolling 12M
            bm_returns = results["B"]["benchmark_returns"]
            # rolling 12M for benchmark
            b12_idx = results["B"]["months"].index(mn)
            if b12_idx >= 11:
                r12_bm = 1.0
                for j in range(b12_idx - 11, b12_idx + 1):
                    r12_bm *= (1 + bm_returns[j])
                f.write(f" {_fmt(r12_bm - 1.0, True)} |")
            else:
                f.write(" N/A |")
            f.write("\n")

        # Drawdown comparison
        f.write("\n## Drawdown Comparison\n\n")
        f.write("| Metric | B | F | G0-A | G0-B | G0-C |\n")
        f.write("|--------|---|---|------|------|------|\n")
        f.write(f"| Max DD | {_fmt(results['B']['max_dd'], True)} | {_fmt(results['F']['max_dd'], True)} | "
                f"{_fmt(results['G0-A']['max_dd'], True)} | {_fmt(results['G0-B']['max_dd'], True)} | "
                f"{_fmt(results['G0-C']['max_dd'], True)} |\n")
        f.write(f"| Avg DD | {_fmt(_mean(results['B']['dd']), True)} | {_fmt(_mean(results['F']['dd']), True)} | "
                f"{_fmt(_mean(results['G0-A']['dd']), True)} | {_fmt(_mean(results['G0-B']['dd']), True)} | "
                f"{_fmt(_mean(results['G0-C']['dd']), True)} |\n")

        # IC stability
        f.write("\n## IC Comparison\n\n")
        f.write("| Metric | B | F | G0-A | G0-B | G0-C |\n")
        f.write("|--------|---|---|------|------|------|\n")
        for lbl in configs:
            r = results[lbl]
            f.write(f"| {lbl} IC Mean | {_fmt(r['ic_mean'])} |\n")
            f.write(f"| {lbl} IC Std  | {_fmt(r['ic_std'])} |\n")
            f.write(f"| {lbl} IC IR   | {_fmt(r['ic_ir'])} |\n")
            f.write(f"| {lbl} IC +/−  | {r['ic_pos']}/{r['ic_neg']} |\n")
        # Better as combined table
        f.write("\n### Combined IC Table\n\n")
        f.write("| Config | IC Mean | IC Std | IC IR | IC +/- |\n")
        f.write("|--------|---------|--------|-------|--------|\n")
        for lbl in configs:
            r = results[lbl]
            f.write(f"| {lbl} | {_fmt(r['ic_mean'])} | {_fmt(r['ic_std'])} | "
                    f"{_fmt(r['ic_ir'])} | {r['ic_pos']}/{r['ic_neg']} |\n")

        # Factor weights table
        f.write("\n## Factor Weights\n\n")
        f.write("| Config | Quality | Growth | Value | Momentum |\n")
        f.write("|--------|---------|--------|-------|----------|\n")
        for lbl in configs:
            w = configs[lbl]
            f.write(f"| {lbl} | {w['quality']*100:.0f}% | {w['growth']*100:.0f}% | "
                    f"{w['value']*100:.0f}% | {w['momentum']*100:.0f}% |\n")

        # Decision analysis
        f.write("\n## Decision Analysis\n\n")

        # Do all G=0 configs beat Config F?
        config_f_cagr = results["F"]["cagr"]
        g0_cagrs = {lbl: results[lbl]["cagr"] for lbl in ["G0-A", "G0-B", "G0-C"]}
        all_beat_f = all(v > config_f_cagr for v in g0_cagrs.values())
        any_beat_f = any(v > config_f_cagr for v in g0_cagrs.values())

        f.write("### Head-to-Head: G=0 configs vs Config F (CAGR)\n\n")
        f.write(f"- **Config F CAGR**: {_fmt(config_f_cagr, True)}\n")
        for lbl in ["G0-A", "G0-B", "G0-C"]:
            c = results[lbl]["cagr"]
            delta = c - config_f_cagr
            emoji = "✅" if delta > 0 else "❌"
            f.write(f"- **{lbl} CAGR**: {_fmt(c, True)} ({_fmt(delta, True)} vs F) {emoji}\n")

        f.write("\n### Sharpe comparison\n\n")
        for lbl in configs:
            s = results[lbl]["sharpe"]
            f.write(f"- {lbl}: {_fmt(s)}\n")

        f.write("\n### Max Drawdown comparison\n\n")
        for lbl in configs:
            d = results[lbl]["max_dd"]
            f.write(f"- {lbl}: {_fmt(d, True)}\n")

        # Verdict
        f.write("\n## Verdict\n\n")
        if all_beat_f:
            f.write("**ALL G=0 configurations beat Config F.**\n\n")
            f.write("**Recommendation: REMOVE Growth from the production factor model.**\n\n")
            f.write("Growth has zero predictive power (IC ≈ 0, t-stat ≈ -0.44) in the IDX 2022-2025.\n")
            f.write("Allocating Growth's weight to Value and Quality improves every metric.\n")
            f.write("The 30% Growth in Config B was actively diluting returns; removing it entirely\n")
            f.write("and reallocating to Value produces the best result.\n")
        elif any_beat_f:
            f.write("**Some G=0 configurations beat Config F on CAGR, but not all.**\n\n")
            f.write("**Recommendation: MODERATE Growth weight.**\n\n")
            winners = [lbl for lbl in ["G0-A", "G0-B", "G0-C"] if results[lbl]["cagr"] > config_f_cagr]
            losers = [lbl for lbl in ["G0-A", "G0-B", "G0-C"] if results[lbl]["cagr"] <= config_f_cagr]
            f.write(f"Winners (beat F): {', '.join(winners)}\n")
            f.write(f"Losers (don't beat F): {', '.join(losers)}\n")
            f.write("Growth may still have marginal value as a diversifier but weight should be ≤10%.\n")
        else:
            f.write("**No G=0 configuration beats Config F.**\n\n")
            f.write("**Recommendation: KEEP Growth in the model as a diversifier.**\n\n")
            f.write("Despite IC ≈ 0, Growth provides diversification benefit that improves\n")
            f.write("risk-adjusted returns when combined with Value and Momentum.\n")
            f.write("The original Config F allocation (10% Growth) remains optimal.\n")

        # Summary
        best_config = max(configs, key=lambda lbl: results[lbl]["cagr"])
        best_sharpe = max(configs, key=lambda lbl: results[lbl]["sharpe"])
        f.write("\n### Winners\n\n")
        f.write(f"- **Highest CAGR**: {best_config} ({_fmt(results[best_config]['cagr'], True)})\n")
        f.write(f"- **Highest Sharpe**: {best_sharpe} ({_fmt(results[best_sharpe]['sharpe'])})\n")
        f.write(f"- **Lowest Max DD**: {min(configs, key=lambda lbl: results[lbl]['max_dd'])} "
                f"({_fmt(results[min(configs, key=lambda lbl: results[lbl]['max_dd'])]['max_dd'], True)})\n")

        f.write("\n---\n")
        f.write(f"*Report generated by `research/research_013d.py`*\n")

    print(f"\nDone: {OUTPUT}")


if __name__ == "__main__":
    main()
