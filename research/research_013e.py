"""
RESEARCH-013E: Config B vs Config F — period sensitivity

Tests whether the winner depends on the evaluation window.
(earnings-only growth fix warehouse, 2022-01 -> 2026-05)
"""

import csv
import math
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent.parent
WH = BASE / "warehouse_historical" / "warehouse_v3_growth_fix.csv"
MONTHLY = BASE / "database" / "monthly"
BENCHMARK = BASE / "benchmarks" / "IHSG.csv"

CONFIG_B = {"quality": 0.25, "growth": 0.30, "value": 0.10, "momentum": 0.35}
CONFIG_F = {"quality": 0.25, "growth": 0.10, "value": 0.30, "momentum": 0.35}

# ── data ──────────────────────────────────────────────────────────
def load_wh():
    wh = {}
    with open(WH) as f:
        for r in csv.DictReader(f):
            m = r["month"]
            if m not in wh: wh[m] = {}
            wh[m][r["ticker"]] = {k: float(r[k]) for k in
                ["quality_score", "growth_score", "value_score", "momentum_score"]}
    return wh

def load_returns():
    tr = defaultdict(dict)
    for f in sorted(MONTHLY.glob("*.csv")):
        t = f.stem.replace(".JK", "")
        with open(f) as fh:
            for r in csv.DictReader(fh):
                d = r.get("Date", "").strip()[:7]
                rv = r.get("monthly_return", "").strip()
                if d and rv:
                    try: tr[t][d] = float(rv)
                    except: pass
    return dict(tr)

def load_ihsg():
    prices = []
    with open(BENCHMARK) as f:
        for r in csv.DictReader(f):
            d, c = r.get("Date", "").strip(), r.get("Close", "").strip()
            if d and c:
                try: prices.append((d[:7], float(c)))
                except: pass
    prices.sort(key=lambda x: x[0])
    ihsg = {}
    for i in range(1, len(prices)):
        p = prices[i]; pp = prices[i - 1]
        if pp[1] > 0: ihsg[p[0]] = (p[1] / pp[1]) - 1.0
    return ihsg

# ── backtest ──────────────────────────────────────────────────────
def run(wh, tr, ihsg, weights, month_subset):
    pr, br = [], []
    sorted_m = sorted(m for m in month_subset)
    for i, m in enumerate(sorted_m):
        if i + 1 >= len(sorted_m): break
        nm = sorted_m[i + 1][:7]
        if nm not in ihsg: continue

        scored = []
        for t, s in wh[m].items():
            cs = sum(weights[k] * s[f"{k}_score"] for k in ["quality", "growth", "value", "momentum"])
            scored.append((cs, t))
        scored.sort(key=lambda x: x[0], reverse=True)
        top5 = scored[:5]

        pr_ret = 0.0
        for _, t in top5:
            t_clean = t.replace(".JK", "")
            ret = tr.get(t_clean, {}).get(nm, 0.0)
            pr_ret += 0.20 * ret
        pr.append(pr_ret)
        br.append(ihsg[nm])

    eq = 1.0
    for r in pr: eq *= (1 + r)
    total_ret = eq - 1.0

    n = len(pr)
    years = n / 12.0
    cagr = eq ** (1.0 / years) - 1.0 if years > 0 else 0.0

    mr = sum(pr) / n if n else 0
    ar = mr * 12.0
    vol = math.sqrt(sum((x - mr)**2 for x in pr) / (n - 1)) * math.sqrt(12) if n > 1 else 0
    sharpe = ar / vol if vol > 0 else 0.0

    eq2 = 1.0; peak = 1.0; maxdd = 0.0
    for r in pr:
        eq2 *= (1 + r); peak = max(peak, eq2)
        dd = (peak - eq2) / peak
        if dd > maxdd: maxdd = dd

    beq = 1.0
    for r in br: beq *= (1 + r)
    btotal = beq - 1.0
    bcagr = beq ** (1.0 / years) - 1.0 if years > 0 else 0.0

    return {"total": total_ret, "cagr": cagr, "sharpe": sharpe, "maxdd": maxdd,
            "bench_total": btotal, "bench_cagr": bcagr, "n": n, "years": years}

# ── main ──────────────────────────────────────────────────────────
def main():
    wh = load_wh()
    tr = load_returns()
    ihsg = load_ihsg()

    all_months = sorted(m for m in wh if "2022-01" <= m[:7] <= "2026-12")
    pre_2026 = [m for m in all_months if m < "2026-01-01"]
    ytd_2026 = [m for m in all_months if m >= "2026-01-01"]

    periods = [
        ("Full: 2022-02 -> 2026-05", all_months),
        ("Before 2026: 2022-02 -> 2025-12", pre_2026),
        ("2026 YTD: 2026-01 -> 2026-05", ytd_2026),
    ]

    for label, months in periods:
        b_res = run(wh, tr, ihsg, CONFIG_B, months)
        f_res = run(wh, tr, ihsg, CONFIG_F, months)
        ihsg_res = {"total": b_res["bench_total"], "cagr": b_res["bench_cagr"]}

        print(f"{'='*60}")
        print(f"{label}")
        print(f"{'='*60}")
        print(f"{'Metric':>15} {'Config B':>15} {'Config F':>15} {'IHSG':>15}")
        print(f"{'-'*60}")
        print(f"{'Total Return':>15} {f'{b_res['total']*100:.2f}%':>15} {f'{f_res['total']*100:.2f}%':>15} {f'{ihsg_res['total']*100:.2f}%':>15}")
        print(f"{'CAGR':>15} {f'{b_res['cagr']*100:.2f}%':>15} {f'{f_res['cagr']*100:.2f}%':>15} {f'{ihsg_res['cagr']*100:.2f}%':>15}")
        print(f"{'Sharpe':>15} {f'{b_res['sharpe']:.4f}':>15} {f'{f_res['sharpe']:.4f}':>15} {'N/A':>15}")
        print(f"{'Max DD':>15} {f'{b_res['maxdd']*100:.2f}%':>15} {f'{f_res['maxdd']*100:.2f}%':>15} {'N/A':>15}")
        print(f"{'Months':>15} {f'{b_res['n']}':>15} {f'{f_res['n']}':>15} {f'{b_res['n']}':>15}")
        winner = "B" if b_res["cagr"] > f_res["cagr"] else "F"
        print(f"{'Winner':>15} {'':>15} {'Config ' + winner:>15}")
        print()

if __name__ == "__main__":
    main()
