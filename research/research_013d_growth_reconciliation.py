"""
research/research_013d_growth_reconciliation.py
================================================
RESEARCH-013D: Growth Reconciliation

Purpose: Re-run all results after changing growth definition from
50/50 (revenue+earnings) blend to earnings-only.

Questions:
  1. Does Config F still beat Config B?
  2. How does Growth IC change?
  3. How does Value IC change?
  4. Does ADR-005 still hold?

Output: reports/research_013d_reconciliation.md
"""

import csv
import math
import json
import sys
import datetime
from pathlib import Path
from collections import defaultdict
from scipy.stats import spearmanr

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

OLD_WH = BASE_DIR / "warehouse_historical" / "warehouse_v3.csv"
NEW_WH = BASE_DIR / "warehouse_historical" / "warehouse_v3_growth_fix.csv"
MONTHLY_DIR = BASE_DIR / "database" / "monthly"
BENCHMARK   = BASE_DIR / "benchmarks" / "IHSG.csv"
SECTOR_RULES = BASE_DIR / "config" / "sector_rules.json"
WEIGHTS_FILE = BASE_DIR / "config" / "scoring_weights.json"
OUTPUT_REPORT = BASE_DIR / "reports" / "research_013d_reconciliation.md"


def _fmt(v, pct=False):
    if v is None: return "N/A"
    if pct: return f"{v*100:.2f}%"
    return f"{v:.4f}"

def _smean(d):
    return sum(d) / len(d) if d else 0.0

def _sstd(d, m=None):
    if len(d) < 2: return 0.0
    if m is None: m = _smean(d)
    return math.sqrt(sum((x - m)**2 for x in d) / (len(d) - 1))


# ── Data Loaders ──────────────────────────────────────────────────────────
def load_warehouse(path):
    wh = defaultdict(dict)
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            wh[r["month"]][r["ticker"]] = {
                "quality_score": float(r["quality_score"]),
                "growth_score": float(r["growth_score"]),
                "value_score": float(r["value_score"]),
                "momentum_score": float(r["momentum_score"]),
            }
    return dict(wh)


def load_ticker_returns():
    tr = defaultdict(dict)
    for f in sorted(MONTHLY_DIR.glob("*.csv")):
        t = f.stem
        with open(f, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                d = r.get("Date", "").strip()[:7]
                rv = r.get("monthly_return", "").strip()
                if d and rv:
                    try: tr[t][d] = float(rv)
                    except: continue
    return dict(tr)


def load_ihsg():
    prices = []
    with open(BENCHMARK, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d, c = r.get("Date", "").strip(), r.get("Close", "").strip()
            if d and c:
                try: prices.append((d[:7], float(c)))
                except: continue
    prices.sort(key=lambda x: x[0])
    ihsg = {}
    for i in range(1, len(prices)):
        pm, pc = prices[i-1]; cm, cc = prices[i]
        if pc > 0: ihsg[cm] = (cc / pc) - 1.0
    return ihsg


# ── Backtest Engine ───────────────────────────────────────────────────────
def run_backtest(wh, ticker_ret, ihsg, weights, start, end):
    sorted_m = sorted(m for m in wh if start <= m[:7] <= end)
    pr, br, months = [], [], []
    for i, m in enumerate(sorted_m):
        if i + 1 >= len(sorted_m): break
        nm = sorted_m[i + 1]
        nm_prefix = nm[:7]
        if nm_prefix not in ihsg: continue
        ss = list(wh[m].values())
        for item in ss:
            item["_score"] = sum(weights[k] * item[f"{k}_score"] for k in ["quality", "growth", "value", "momentum"])
        ranked = sorted(ss, key=lambda x: x["_score"], reverse=True)
        top5 = ranked[:5]
        p_ret = 0.0
        for item in top5:
            t = item.get("_ticker", "")
            if not t: continue
            ret = ticker_ret.get(t, {}).get(nm_prefix)
            if ret is None: ret = 0.0
            p_ret += 0.20 * ret
        pr.append(p_ret); br.append(ihsg[nm_prefix]); months.append(nm_prefix)
    return pr, br

def calc_metrics(portfolio_r, benchmark_r):
    n = len(portfolio_r); years = n / 12.0
    if n == 0: return {}
    eq = 1.0; peak = 1.0; dd = []
    for r in portfolio_r:
        eq *= (1 + r); peak = max(peak, eq); dd.append((peak - eq) / peak)
    cagr = eq ** (1.0 / years) - 1.0 if years > 0 else 0
    mr = _smean(portfolio_r); ar = mr * 12.0; vol = _sstd(portfolio_r, mr) * math.sqrt(12)
    sharpe = ar / vol if vol > 0 else 0.0
    maxdd = max(dd) if dd else 0.0
    dn = [r for r in portfolio_r if r < 0]
    ds = _sstd(dn, 0) * math.sqrt(12) if len(dn) >= 2 else 0.0
    sortino = ar / ds if ds > 0 else 0.0
    wr = sum(1 for r in portfolio_r if r > 0) / n
    mb = _smean(benchmark_r)
    cov = sum((p - mr) * (b - mb) for p, b in zip(portfolio_r, benchmark_r)) / (n - 1)
    vb = sum((b - mb) ** 2 for b in benchmark_r) / (n - 1)
    beta = cov / vb if vb > 0 else 0.0
    alpha = (mr - beta * mb) * 12.0
    beq = 1.0
    for r in benchmark_r: beq *= (1 + r)
    bcagr = beq ** (1.0 / years) - 1.0
    return {"cagr": cagr, "sharpe": sharpe, "alpha": alpha, "max_dd": maxdd,
            "win_rate": wr, "volatility": vol, "sortino": sortino, "beta": beta,
            "benchmark_cagr": bcagr, "excess_cagr": cagr - bcagr, "n": n}


def compute_factor_ic(wh, ticker_ret, factor="growth_score", start="2022-01", end="2025-12"):
    sorted_m = sorted(m for m in wh if start <= m[:7] <= end)
    ics = []
    for i, m in enumerate(sorted_m):
        if i + 1 >= len(sorted_m): break
        nm = sorted_m[i + 1]; nm_prefix = nm[:7]
        tickers_m = wh[m]
        pairs = []
        for t, scores in tickers_m.items():
            t_clean = t.replace(".JK", "")
            ret = ticker_ret.get(t, {}).get(nm_prefix)
            if ret is None: ret = ticker_ret.get(t_clean, {}).get(nm_prefix)
            if ret is not None:
                pairs.append((scores[factor], ret))
        if len(pairs) < 5: continue
        x = [p[0] for p in pairs]; y = [p[1] for p in pairs]
        rho, _ = spearmanr(x, y)
        if not math.isnan(rho): ics.append(rho)
    return ics


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M WIB")

    print("=" * 65)
    print("RESEARCH-013D: Growth Reconciliation")
    print("=" * 65)

    print("\nLoading data...")
    wh_old = load_warehouse(OLD_WH)
    wh_new = load_warehouse(NEW_WH)
    ticker_ret = load_ticker_returns()
    ihsg = load_ihsg()

    start, end = "2022-01", "2025-12"
    print(f"  Old warehouse: {len(wh_old)} months")
    print(f"  New warehouse: {len(wh_new)} months")

    # Fix: add _ticker key to each score dict for backtest
    for wh in [wh_old, wh_new]:
        for m, tickers in wh.items():
            for t, scores in tickers.items():
                scores["_ticker"] = t

    cfg_b = {"quality": 0.25, "growth": 0.30, "value": 0.10, "momentum": 0.35}
    cfg_f = {"quality": 0.25, "growth": 0.10, "value": 0.30, "momentum": 0.35}

    results = {}

    for label, wh in [("Old (50/50 blend)", wh_old), ("New (earnings-only)", wh_new)]:
        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"{'='*60}")

        # Config B
        pr_b, br_b = run_backtest(wh, ticker_ret, ihsg, cfg_b, start, end)
        m_b = calc_metrics(pr_b, br_b)

        # Config F
        pr_f, br_f = run_backtest(wh, ticker_ret, ihsg, cfg_f, start, end)
        m_f = calc_metrics(pr_f, br_f)

        # IC
        g_ics = compute_factor_ic(wh, ticker_ret, "growth_score", start, end)
        v_ics = compute_factor_ic(wh, ticker_ret, "value_score", start, end)
        q_ics = compute_factor_ic(wh, ticker_ret, "quality_score", start, end)
        m_ics = compute_factor_ic(wh, ticker_ret, "momentum_score", start, end)

        results[label] = {
            "config_b": m_b,
            "config_f": m_f,
            "ic": {
                "growth": {"mean": _smean(g_ics), "n": len(g_ics)},
                "value": {"mean": _smean(v_ics), "n": len(v_ics)},
                "quality": {"mean": _smean(q_ics), "n": len(q_ics)},
                "momentum": {"mean": _smean(m_ics), "n": len(m_ics)},
            }
        }

        print(f"  Config B: CAGR={_fmt(m_b.get('cagr'), True)}, Sharpe={_fmt(m_b.get('sharpe'))}")
        print(f"  Config F: CAGR={_fmt(m_f.get('cagr'), True)}, Sharpe={_fmt(m_f.get('sharpe'))}")
        print(f"  Growth IC: {_fmt(_smean(g_ics))} ({len(g_ics)} months)")
        print(f"  Value IC:  {_fmt(_smean(v_ics))} ({len(v_ics)} months)")
        print(f"  Quality IC: {_fmt(_smean(q_ics))} ({len(q_ics)} months)")
        print(f"  Momentum IC: {_fmt(_smean(m_ics))} ({len(m_ics)} months)")

    # ── Write Report ───────────────────────────────────────────────
    print(f"\nWriting report: {OUTPUT_REPORT}")
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        f.write("# RESEARCH-013D: Growth Reconciliation\n\n")
        f.write(f"> Generated: {now}  \n")
        f.write(f"> Period: {start} → {end}  \n\n")
        f.write("---\n\n")

        # Comparison Table
        f.write("## Before vs After: Growth Definition Change\n\n")
        f.write("| Metric | Old Warehouse (50/50 blend) | New Warehouse (earnings-only) | Delta |\n")
        f.write("|--------|---------------------------|------------------------------|-------|\n")

        rows = []
        for metric, old_key, new_key in [
            ("Config B CAGR", ("config_b", "cagr"), ("config_b", "cagr")),
            ("Config B Sharpe", ("config_b", "sharpe"), ("config_b", "sharpe")),
            ("Config B Alpha", ("config_b", "alpha"), ("config_b", "alpha")),
            ("Config B Max DD", ("config_b", "max_dd"), ("config_b", "max_dd")),
            ("Config F CAGR", ("config_f", "cagr"), ("config_f", "cagr")),
            ("Config F Sharpe", ("config_f", "sharpe"), ("config_f", "sharpe")),
            ("Config F Alpha", ("config_f", "alpha"), ("config_f", "alpha")),
            ("Config F Max DD", ("config_f", "max_dd"), ("config_f", "max_dd")),
            ("CAGR Difference (F - B)", ("config_f", "cagr"), ("config_f", "cagr")),
        ]:
            o = results["Old (50/50 blend)"]
            n = results["New (earnings-only)"]
            ov = o[old_key[0]][old_key[1]]
            nv = n[new_key[0]][new_key[1]]
            is_pct = "CAGR" in metric or "Alpha" in metric or "Max DD" in metric
            if "Difference" in metric:
                # Compute difference
                ob = o["config_b"]["cagr"]; of = o["config_f"]["cagr"]
                nb = n["config_b"]["cagr"]; nf = n["config_f"]["cagr"]
                ov = of - ob; nv = nf - nb
            rows.append((metric, ov, nv))
            f.write(f"| {metric} | {_fmt(ov, is_pct)} | {_fmt(nv, is_pct)} | {_fmt(nv - ov, is_pct and 'CAGR' in metric or 'Alpha' in metric)} |\n")

        # IC comparison
        f.write("\n## Factor IC Comparison\n\n")
        f.write("| Factor | Old Warehouse | New Warehouse | Delta |\n")
        f.write("|--------|--------------|--------------|-------|\n")
        for factor in ["growth", "value", "quality", "momentum"]:
            o_ic = results["Old (50/50 blend)"]["ic"][factor]["mean"]
            n_ic = results["New (earnings-only)"]["ic"][factor]["mean"]
            o_n = results["Old (50/50 blend)"]["ic"][factor]["n"]
            n_n = results["New (earnings-only)"]["ic"][factor]["n"]
            f.write(f"| {factor.title()} | {_fmt(o_ic)} (n={o_n}) | {_fmt(n_ic)} (n={n_n}) | {_fmt(n_ic - o_ic)} |\n")

        # Config B vs Config F vote
        f.write("\n## Config B vs Config F\n\n")
        o_b_cagr = results["Old (50/50 blend)"]["config_b"]["cagr"]
        o_f_cagr = results["Old (50/50 blend)"]["config_f"]["cagr"]
        n_b_cagr = results["New (earnings-only)"]["config_b"]["cagr"]
        n_f_cagr = results["New (earnings-only)"]["config_f"]["cagr"]

        f.write("| Comparison | Old Warehouse | New Warehouse |\n")
        f.write("|-----------|--------------|--------------|\n")
        f.write(f"| Config B | {_fmt(o_b_cagr, True)} | {_fmt(n_b_cagr, True)} |\n")
        f.write(f"| Config F | {_fmt(o_f_cagr, True)} | {_fmt(n_f_cagr, True)} |\n")
        f.write(f"| Winner | {'Config F' if o_f_cagr > o_b_cagr else 'Config B'} | {'Config F' if n_f_cagr > n_b_cagr else 'Config B'} |\n")

        # Analysis
        f.write("\n## Analysis\n\n")

        growth_ic_old = results["Old (50/50 blend)"]["ic"]["growth"]["mean"]
        growth_ic_new = results["New (earnings-only)"]["ic"]["growth"]["mean"]

        f.write("### Growth IC Transformation\n\n")
        f.write(f"- Old (50/50 blend): **{_fmt(growth_ic_old)}**\n")
        f.write(f"- New (earnings-only): **{_fmt(growth_ic_new)}**\n")

        if growth_ic_new > growth_ic_old:
            f.write(f"- Improvement: **+{_fmt(growth_ic_new - growth_ic_old)}**\n")
            if growth_ic_new > 0:
                f.write("- **Verdict**: Growth IC turned POSITIVE — the old definition was actively harming the factor.\n")
            else:
                f.write("- Still negative, but significantly improved.\n")
        else:
            f.write("- No improvement or worsened.\n")

        # Adr-005 assessment
        f.write("\n### ADR-005 Assessment\n\n")
        if n_f_cagr > n_b_cagr:
            f.write(f"**Config F STILL WINS** after growth reconciliation (CAGR: {_fmt(n_f_cagr, True)} vs {_fmt(n_b_cagr, True)}).\n")
            f.write("ADR-005 (promote Config F) is **strengthened** by the definition fix.\n")
        else:
            f.write(f"**Config F LOSES** after growth reconciliation (CAGR: {_fmt(n_f_cagr, True)} vs {_fmt(n_b_cagr, True)}).\n")
            f.write("ADR-005 must be **reconsidered**.\n")

        # Narrative impact
        o_diff = o_f_cagr - o_b_cagr
        n_diff = n_f_cagr - n_b_cagr
        f.write(f"\n### Narrative Impact\n\n")
        f.write(f"- Before: Config F beats Config B by {_fmt(o_diff, True)}\n")
        f.write(f"- After: Config F beats Config B by {_fmt(n_diff, True)}\n")
        if abs(n_diff) < abs(o_diff):
            f.write("- The gap **narrowed** — Growth definition was inflating the difference.\n")
        elif abs(n_diff) > abs(o_diff):
            f.write("- The gap **widened** — earnings-only growth makes Config F even stronger.\n")
        else:
            f.write("- The gap **stayed the same**.\n")
        if (n_f_cagr > n_b_cagr) == (o_f_cagr > o_b_cagr):
            f.write("- **Winner unchanged** — conclusions are robust to definition change.\n")
        else:
            f.write("- **Winner flipped** — conclusions were definition-dependent.\n")

        f.write("\n### Overall Assessment\n\n")
        config_b_wins = n_b_cagr > n_f_cagr
        growth_now_positive = growth_ic_new > 0

        if not config_b_wins and growth_now_positive:
            f.write("**Best case**: Config F still wins, Growth IC is now positive. Definition fix was correct.\n")
        elif not config_b_wins and not growth_now_positive:
            f.write("**Mixed**: Config F still wins, but Growth IC is still negative. Other factors drive the edge.\n")
        elif config_b_wins and growth_now_positive:
            f.write("**New finding**: Config B wins when Growth is properly defined. ADR-005 may need reversal.\n")
        else:
            f.write("**Unexpected**: Config B wins and Growth IC still negative. Further investigation needed.\n")

        f.write("\n---\n")
        f.write(f"*Report generated by `research/research_013d_growth_reconciliation.py`*\n")

    print(f"\nDone: {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
