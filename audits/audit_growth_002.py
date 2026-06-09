"""
audits/audit_growth_002.py
==========================
AUDIT-GROWTH-002: Growth Definition Comparison

Compares 5 growth definitions to determine if earnings_growth is the best factor.

Definitions:
  1. earnings_growth        — current standalone scoring approach
  2. revenue_growth         — the excluded input
  3. earnings + revenue     — 50/50 blend (warehouse V3 approach)
  4. earnings_acceleration  — change in earnings growth rate
  5. 3Y earnings CAGR       — 3-year compound annual growth rate of net income

Data sources:
  - 2024-06.csv snapshot (raw revenue_growth, earnings_growth for 29 tickers)
  - warehouse_v3.csv (monthly growth scores for definition 3)
  - yfinance Ticker.financials (for 3Y CAGR computation)
  - database/monthly/*.csv (forward returns)

Output: audits/AUDIT_GROWTH_002_REPORT.md
"""

import csv
import json
import math
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from scipy.stats import spearmanr

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from scoring.utils import percentile_normalize

SNAPSHOT    = BASE_DIR / "warehouse_historical" / "2024-06.csv"
WAREHOUSE   = BASE_DIR / "warehouse_historical" / "warehouse_v3.csv"
MONTHLY_DIR = BASE_DIR / "database" / "monthly"
SECTOR_FILE = BASE_DIR / "config" / "sector_rules.json"
BENCHMARK   = BASE_DIR / "benchmarks" / "IHSG.csv"
OUTPUT_REPORT = BASE_DIR / "audits" / "AUDIT_GROWTH_002_REPORT.md"


# ── Helpers ──────────────────────────────────────────────────────────────
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


# ── 1. Load Snapshot Data ───────────────────────────────────────────────
def load_snapshot():
    """Load June 2024 snapshot with raw revenue_growth, earnings_growth."""
    rows = []
    with open(SNAPSHOT, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "ticker": r["ticker"],
                "revenue_growth": float(r["revenue_growth"]) if r.get("revenue_growth") else None,
                "earnings_growth": float(r["earnings_growth"]) if r.get("earnings_growth") else None,
                "growth_score": float(r["growth_score"]),
                "is_commodity": r.get("is_commodity", "False") == "True",
            })
    return rows


def load_forward_returns(base_month="2024-06"):
    """Load forward 1M, 3M, 6M returns from ticker monthly data."""
    fwd = {}
    for f in sorted(MONTHLY_DIR.glob("*.csv")):
        t = f.stem
        prices = []
        with open(f, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                d = r.get("Date", "").strip()
                p = r.get("month_end_price", "").strip()
                if d and p:
                    try: prices.append((d[:7], float(p)))
                    except ValueError: continue
        prices.sort(key=lambda x: x[0])
        # Find index of base_month
        idx = None
        for i, (m, p) in enumerate(prices):
            if m == base_month:
                idx = i
                break
        if idx is None: continue
        base_price = prices[idx][1]
        if base_price <= 0: continue
        returns = {}
        for offset, label in [(1, "1M"), (3, "3M"), (6, "6M")]:
            if idx + offset < len(prices):
                fwd_p = prices[idx + offset][1]
                if fwd_p > 0:
                    returns[label] = (fwd_p / base_price) - 1.0
        if returns:
            fwd[t] = returns
    return fwd


# ── 2. Compute Alternative Growth Scores ───────────────────────────────
def compute_growth_definitions(snapshot, forward_rets):
    """Compute all 5 growth definitions and their IC against forward returns."""

    # Filter to tickers with both revenue and earnings data
    valid = [r for r in snapshot if r["revenue_growth"] is not None and r["earnings_growth"] is not None]
    tickers = [r["ticker"] for r in valid]

    # Raw values
    rev_g = [r["revenue_growth"] for r in valid]
    ern_g = [r["earnings_growth"] for r in valid]

    # Def 1: earnings_growth (standalone scoring)
    ern_scores = percentile_normalize(ern_g)

    # Def 2: revenue_growth
    rev_scores = percentile_normalize(rev_g)

    # Def 3: earnings + revenue (50/50 — warehouse V3 approach)
    comb_scores = [(ern_scores[i] + rev_scores[i]) / 2.0 for i in range(len(valid))]

    # For Def 4 & 5, try yfinance
    print("\n[2] Fetching yfinance data for earnings_acceleration & 3Y CAGR...")
    import yfinance as yf
    ern_acc_scores = []
    cagr3y_scores = []
    ern_acc_raw = []
    cagr3y_raw = []
    yf_tickers_with_data = 0

    for r in valid:
        t = r["ticker"]
        try:
            stock = yf.Ticker(t)
            fs = stock.financials
            if fs is None or len(fs.columns) < 3:
                ern_acc_raw.append(None)
                cagr3y_raw.append(None)
                print(f"  WARN: {t} insufficient financial history")
                continue

            # Get net income from last 4 fiscal years
            ni_values = []
            for col_idx in range(min(4, len(fs.columns))):
                for label in ["Net Income", "Net Income Common Stockholders"]:
                    if label in fs.index:
                        val = fs.loc[label].iloc[col_idx]
                        if val == val and val is not None:
                            ni_values.append(val)
                            break
                else:
                    ni_values.append(None)

            if len(ni_values) >= 3 and all(v is not None for v in ni_values[:3]):
                # Def 4: earnings_acceleration = change in NI growth rate
                # growth_t1→t0 minus growth_t2→t1
                g1 = (ni_values[0] - ni_values[1]) / abs(ni_values[1]) if ni_values[1] != 0 else 0
                g2 = (ni_values[1] - ni_values[2]) / abs(ni_values[2]) if ni_values[2] != 0 else 0
                ea = g1 - g2
                ern_acc_raw.append(ea)

                # Def 5: 3Y CAGR
                if ni_values[2] > 0 and ni_values[0] > 0:
                    cagr = (ni_values[0] / ni_values[2]) ** (1.0 / 2.0) - 1.0
                    cagr3y_raw.append(cagr)
                else:
                    cagr3y_raw.append(None)
                yf_tickers_with_data += 1
            else:
                ern_acc_raw.append(None)
                cagr3y_raw.append(None)
        except Exception as e:
            ern_acc_raw.append(None)
            cagr3y_raw.append(None)
            print(f"  WARN: {t} yfinance failed: {e}")

    # Percentile normalize (filtering None)
    ern_acc_nonull = [(v, i) for i, v in enumerate(ern_acc_raw) if v is not None]
    cagr3y_nonull = [(v, i) for i, v in enumerate(cagr3y_raw) if v is not None]

    def make_scores(raw_list, nonull_pairs):
        result = [None] * len(raw_list)
        if len(nonull_pairs) < 3:
            return result
        vals = [p[0] for p in nonull_pairs]
        p_scores = percentile_normalize(vals)
        for p_score, (_, idx) in zip(p_scores, nonull_pairs):
            result[idx] = p_score
        return result

    ern_acc_scores = make_scores(ern_acc_raw, ern_acc_nonull)
    cagr3y_scores = make_scores(cagr3y_raw, cagr3y_nonull)

    print(f"  yfinance data: {yf_tickers_with_data}/{len(valid)} tickers")

    # ── Compute IC for each definition ──────────────────────────────────
    def compute_ic(scores_list, forward_dict, label):
        ics = {}
        for period in ["1M", "3M", "6M"]:
            pairs = []
            for i, t in enumerate(tickers):
                s = scores_list[i]
                if s is None: continue
                if t not in forward_dict: continue
                r = forward_dict[t].get(period)
                if r is None: continue
                pairs.append((s, r))
            if len(pairs) < 5:
                ics[period] = None
                continue
            x = [p[0] for p in pairs]
            y = [p[1] for p in pairs]
            rho, pval = spearmanr(x, y)
            ics[period] = rho if not math.isnan(rho) else None
        return ics

    # ── CAGR as standalone factor ──────────────────────────────────────
    def compute_cagr(scores_list, forward_dict, label):
        """Simulate top-5 equal-weight portfolio and compute CAGR."""
        pairs = [(scores_list[i], t) for i, t in enumerate(tickers) if scores_list[i] is not None]
        if len(pairs) < 5: return None
        pairs.sort(key=lambda x: x[0], reverse=True)
        top5 = [p[1] for p in pairs[:5]]
        # Compute 1-month forward return for each ticker, average, annualize
        rets = []
        for t in top5:
            if t in forward_dict and "1M" in forward_dict[t]:
                rets.append(forward_dict[t]["1M"])
        if not rets: return None
        avg_ret_1m = _smean(rets)
        # Annualized from 1-month snapshot — very rough estimate
        cagr_est = (1 + avg_ret_1m) ** 12 - 1.0
        return cagr_est, top5, avg_ret_1m

    results = {}
    for label, scores in [
        ("earnings_growth", ern_scores),
        ("revenue_growth", rev_scores),
        ("earnings+revenue", comb_scores),
        ("earnings_acceleration", ern_acc_scores),
        ("3Y earnings CAGR", cagr3y_scores),
    ]:
        ic = compute_ic(scores, forward_rets, label)
        cagr_info = compute_cagr(scores, forward_rets, label)
        results[label] = {
            "ic": ic,
            "cagr": cagr_info[0] if cagr_info else None,
            "top5": cagr_info[1] if cagr_info else [],
            "avg_1m_ret": cagr_info[2] if cagr_info else None,
        }
        print(f"  {label:>25}: 1M IC={_fmt(ic.get('1M')) if ic else 'N/A':>8}, CAGR={_fmt(results[label]['cagr'], True) if results[label]['cagr'] is not None else 'N/A'}")

    return results, tickers, ern_scores, rev_scores, comb_scores


# ── 3. Warehouse vs Standalone Comparison ──────────────────────────────
def compare_warehouse_standalone(snapshot):
    """Compare warehouse growth_score (50/50 blend) vs standalone earnings-only."""
    print("\n[3] Warehouse vs Standalone Growth Score Comparison...")
    
    # Warehouse scores from snapshot (50/50 rev+earn blend)
    wh_scores = {r["ticker"]: r["growth_score"] for r in snapshot}

    # Standalone earnings-only scores (recomputed from snapshot raw data)
    valid = [r for r in snapshot if r["earnings_growth"] is not None]
    ern_vals = [r["earnings_growth"] for r in valid]
    ern_pct = percentile_normalize(ern_vals)
    st_scores = {valid[i]["ticker"]: ern_pct[i] for i in range(len(valid))}

    # Compare
    print(f"{'Ticker':>12} {'WH(G50+R50)':>12} {'ST(Ern100)':>12} {'Diff':>8} {'WH Rank':>8} {'ST Rank':>8}")
    print("-" * 64)
    all_t = sorted(set(list(wh_scores.keys()) + list(st_scores.keys())))
    wh_ranked = sorted(wh_scores.items(), key=lambda x: x[1], reverse=True)
    st_ranked = sorted(st_scores.items(), key=lambda x: x[1], reverse=True)
    wh_ranks = {t: i+1 for i, (t, _) in enumerate(wh_ranked)}
    st_ranks = {t: i+1 for i, (t, _) in enumerate(st_ranked)}
    diffs = []
    for t in all_t:
        wh = wh_scores.get(t)
        st = st_scores.get(t)
        if wh is not None and st is not None:
            d = wh - st
            diffs.append(abs(d))
            wr = wh_ranks.get(t, "-")
            sr = st_ranks.get(t, "-")
            print(f"{t:>12} {wh:>12.2f} {st:>12.2f} {d:>+8.2f} {wr:>8} {sr:>8}")
    print(f"\nMean absolute diff: {_smean(diffs):.2f}")
    print(f"Max diff: {max(diffs):.2f}")

    return wh_scores, st_scores


# ── 4. Multi-Month Warehouse IC ────────────────────────────────────────
def compute_warehouse_ic():
    """Compute the warehouse growth_score IC across all 47 months."""
    print("\n[4] Multi-Month Warehouse Growth Score IC (47 months)...")
    wh = defaultdict(dict)
    with open(WAREHOUSE, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            wh[r["month"]][r["ticker"]] = float(r["growth_score"])

    forward_rets = defaultdict(dict)
    for f in sorted(MONTHLY_DIR.glob("*.csv")):
        t = f.stem
        prices = []
        with open(f, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                d = r.get("Date", "").strip()[:7]
                p = r.get("month_end_price", "").strip()
                if d and p:
                    try: prices.append((d, float(p)))
                    except: continue
        prices.sort(key=lambda x: x[0])
        for i in range(len(prices) - 1):
            cm, cp = prices[i]
            nm, np_ = prices[i + 1]
            if cp > 0:
                forward_rets[cm][t] = (np_ / cp) - 1.0

    sorted_months = sorted(wh.keys())
    ics_1m = []
    for i, m in enumerate(sorted_months):
        if i + 1 >= len(sorted_months): break
        nm = sorted_months[i + 1]
        m_prefix = m[:7]
        nm_prefix = nm[:7]
        tickers_m = wh[m]
        pairs = []
        for t, score in tickers_m.items():
            t_clean = t.replace(".JK", "")
            ret = forward_rets.get(m_prefix, {}).get(t)
            if ret is None:
                ret = forward_rets.get(m_prefix, {}).get(t_clean)
            if ret is None:
                ret = forward_rets.get(m_prefix, {}).get(t.replace(".JK", "") + ".JK")
            if ret is not None:
                pairs.append((score, ret))
        if len(pairs) < 5: continue
        x = [p[0] for p in pairs]; y = [p[1] for p in pairs]
        rho, _ = spearmanr(x, y)
        if not math.isnan(rho): ics_1m.append(rho)

    mean_ic = _smean(ics_1m) if ics_1m else 0
    ic_sr = mean_ic / _sstd(ics_1m) * math.sqrt(12) if len(ics_1m) >= 2 and _sstd(ics_1m) > 0 else 0
    pos = sum(1 for x in ics_1m if x > 0)
    neg = sum(1 for x in ics_1m if x < 0)
    print(f"  Warehouse Growth Score (50/50 blend) — 47 months")
    print(f"  Mean IC: {_fmt(mean_ic)}, IC>0: {pos}/{len(ics_1m)}, IC<0: {neg}/{len(ics_1m)}, IC SR: {_fmt(ic_sr)}")
    return mean_ic, ics_1m


# ── 5. Write Report ────────────────────────────────────────────────────
def write_report(results, tickers, snapshot, forward_rets, wh_ic, ics, ern_scores, rev_scores, comb_scores):
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M WIB")

    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        f.write("# AUDIT-GROWTH-002: Growth Definition Comparison\n\n")
        f.write(f"> Generated: {now}  \n")
        f.write(f"> Data: 2024-06 snapshot (29 IDX30 tickers) + yfinance + warehouse_v3 (47 months)  \n\n")
        f.write("---\n\n")

        # ── Critical Discrepancy ──
        f.write("## Critical Finding: Warehouse vs Standalone Definition Mismatch\n\n")
        f.write("| Component | Growth Formula | Source |\n")
        f.write("|-----------|---------------|--------|\n")
        f.write("| `scoring/growth_score.py` (standalone) | **Earnings only** (100% earnings percentile) | `scoring/growth_score.py:25` |\n")
        f.write("| `build_warehouse_v3.py` (production) | **50% Revenue + 50% Earnings percentile** | `build_warehouse_v3.py:507` |\n")
        f.write("| `research_013c_factor_attribution.py` | Uses warehouse scores (50/50 blend) | warehouse_v3.csv |\n\n")
        f.write("**Impact**: All RESEARCH-013C conclusions about \"Growth having negative IC\" were based on the **50/50 blend** (warehouse), NOT the standalone earnings-only definition. The two definitions produce materially different rankings.\n\n")

        # ── Definition Comparison Table ──
        f.write("## Growth Definition Comparison\n\n")
        f.write("| Definition | 1M IC | 3M IC | 6M IC | CAGR (Top5) | Top 5 Picks | Notes |\n")
        f.write("|-----------|-------|-------|-------|-------------|-------------|-------|\n")
        for label in ["earnings_growth", "revenue_growth", "earnings+revenue", "earnings_acceleration", "3Y earnings CAGR"]:
            r = results.get(label, {})
            ic = r.get("ic", {})
            ic_1 = _fmt(ic.get("1M")) if ic and ic.get("1M") is not None else "N/A"
            ic_3 = _fmt(ic.get("3M")) if ic and ic.get("3M") is not None else "N/A"
            ic_6 = _fmt(ic.get("6M")) if ic and ic.get("6M") is not None else "N/A"
            cagr = _fmt(r.get("cagr"), True) if r.get("cagr") is not None else "N/A"
            top5 = ", ".join(r.get("top5", []))
            notes = ""
            if label == "earnings_growth": notes = "Current standalone definition"
            elif label == "earnings+revenue": notes = "Current warehouse definition"
            elif label == "earnings_acceleration": notes = "yfinance annual data"
            f.write(f"| {label} | {ic_1} | {ic_3} | {ic_6} | {cagr} | {top5} | {notes} |\n")

        # ── Snapshot raw data ──
        f.write("\n## Snapshot Raw Data (2024-06)\n\n")
        f.write("| Ticker | Rev Growth | Ern Growth | Ern Score | Rev Score | Comb Score |\n")
        f.write("|--------|-----------|-----------|-----------|----------|------------|\n")
        for i, t in enumerate(tickers):
            if i >= 15: break  # first 15 for brevity
            r = next(x for x in snapshot if x["ticker"] == t)
            f.write(f"| {t} | {_fmt(r['revenue_growth'], True)} | {_fmt(r['earnings_growth'], True)} | {_fmt(ern_scores[i])} | {_fmt(rev_scores[i])} | {_fmt(comb_scores[i])} |\n")
        if len(tickers) > 15:
            f.write(f"| ... | ... | ... | ... | ... | ... |\n\n")

        # ── Warehouse IC (47 months) ──
        f.write("\n## Warehouse Growth Score Multi-Month IC (2022-2025)\n\n")
        f.write(f"This is the IC of the **50/50 blend** (current warehouse definition) across all 47 months.\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| Mean IC (1M forward) | {_fmt(wh_ic)} |\n")
        f.write(f"| IC > 0 | {sum(1 for x in ics if x > 0)}/{len(ics)} |\n")
        f.write(f"| IC < 0 | {sum(1 for x in ics if x < 0)}/{len(ics)} |\n")
        f.write(f"| IC Sharpe | {_fmt(wh_ic / _sstd(ics) * math.sqrt(12) if _sstd(ics) > 0 else 0)} |\n\n")

        # ── Final Analysis ──
        f.write("## Analysis & Conclusions\n\n")

        f.write("### 1. Definition Comparison Results\n\n")
        f.write("From the snapshot comparison (June 2024, single-period):\n\n")
        # Find best IC
        best_def = max(results.keys(), key=lambda k: results[k].get("ic", {}).get("1M", -99) if results[k].get("ic") and results[k]["ic"].get("1M") is not None else -99)
        worst_def = min(results.keys(), key=lambda k: results[k].get("ic", {}).get("1M", 99) if results[k].get("ic") and results[k]["ic"].get("1M") is not None else 99)
        
        f.write(f"- **Best 1M IC**: {best_def} (IC = {_fmt(results[best_def]['ic']['1M'])})\n")
        f.write(f"- **Worst 1M IC**: {worst_def} (IC = {_fmt(results[worst_def]['ic']['1M'])})\n\n")

        f.write("### 2. The Real Problem: Definition Inconsistency\n\n")
        f.write("The most critical finding is **not** which definition is best, but that the codebase has TWO conflicting definitions:\n\n")
        f.write("1. **`scoring/growth_score.py`**: Earnings-only (100% earnings_growth percentile).\n")
        f.write("   The comment at line 24 states: `Menghilangkan Revenue Growth yang menghasilkan alpha negatif`.\n\n")
        f.write("2. **`build_warehouse_v3.py`**: 50% Revenue + 50% Earnings blend (line 507).\n")
        f.write("   This was introduced silently when the V3 warehouse was built. No corresponding update was made to\n")
        f.write("   the standalone scoring script, and the reason for including revenue growth again is undocumented.\n\n")
        f.write("This means:\n")
        f.write("- The standalone scoring pipeline produces **different growth scores** than the warehouse.\n")
        f.write("- All backtests (RESEARCH-013A, 013B, 013C) used the **warehouse definition** (50/50 blend).\n")
        f.write("- The RESEARCH-013C conclusion that \"Growth has negative IC\" applies to the **50/50 blend**, not earnings-only.\n")
        f.write("- The comment claiming revenue_growth has negative alpha may refer to a different time period or was\n")
        f.write("  never validated against the V3 data.\n\n")

        f.write("### 3. Why This Matters\n\n")
        f.write("If earnings-only growth has a different (potentially positive) IC, then the RESEARCH-013C conclusion\n")
        f.write("that \"Growth has negative IC\" becomes:\n\n")
        f.write('> **"The warehouse 50/50 growth blend has negative IC"**\n\n')
        f.write("This is a fundamentally different statement. The standalone earnings-only definition might have\n")
        f.write("positive IC, which would mean:\n")
        f.write("- Config B (G=30%) might not drag as much with earnings-only growth.\n")
        f.write("- The Config B vs Config F comparison might change.\n")
        f.write("- The recommendation to favor Config F might be less robust.\n\n")

        f.write("### 4. Recommendations\n\n")
        f.write("| # | Recommendation | Priority |\n")
        f.write("|---|---------------|----------|\n")
        f.write("| R1 | **Reconcile the two definitions** — either update `scoring/growth_score.py` to match warehouse (50/50 blend) or update warehouse to match standalone (earnings-only). Having two definitions is a bug. | **HIGH** |\n")
        f.write("| R2 | **Re-run RESEARCH-013C** with the earnings-only growth definition to determine which IC is actually positive/negative. | **HIGH** |\n")
        f.write("| R3 | **Document the reason** for including/excluding revenue growth. If revenue_growth was excluded for negative alpha, show the evidence. If it was re-included in V3, show the evidence. | MEDIUM |\n")
        f.write("| R4 | **Validate with longer data** — the single-month snapshot comparison is insufficient. Run the V3 warehouse builder with raw growth values captured, then compute IC for all 5 definitions across 47 months. | MEDIUM |\n\n")

        f.write("### 5. Root Cause\n\n")
        f.write("The root cause of this audit is not about factor selection but **pipeline drift**:\n\n")
        f.write("1. Original design (growth_score.py): earnings-only growth.\n")
        f.write("2. Warehouse V3 (build_warehouse_v3.py): 50/50 blend — introduced without updating the scoring script.\n")
        f.write("3. RESEARCH-013C tested the warehouse scores and concluded \"Growth IC negative.\"\n")
        f.write("4. But this conclusion applies only to the 50/50 warehouse blend, not the original earnings-only definition.\n\n")
        f.write("**The question \"Is earnings_growth the best definition?\" cannot be answered until the codebase uses a single definition.**\n")

        f.write("\n---\n")
        f.write(f"*Report generated by `audits/audit_growth_002.py`*\n")

    print(f"\nReport: {OUTPUT_REPORT}")


# ── Main ────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("AUDIT-GROWTH-002: Growth Definition Comparison")
    print("=" * 65)

    print("\n[1] Loading snapshot data (2024-06)...")
    snapshot = load_snapshot()
    print(f"      {len(snapshot)} tickers loaded")

    print("\n[1b] Loading forward returns...")
    forward_rets = load_forward_returns()
    print(f"      {len(forward_rets)} tickers with forward returns")

    # Compute all definitions
    print("\n" + "=" * 65)
    print("COMPUTING GROWTH DEFINITIONS")
    print("=" * 65)
    results, tickers, ern_scores, rev_scores, comb_scores = compute_growth_definitions(snapshot, forward_rets)

    # Warehouse vs standalone comparison
    compare_warehouse_standalone(snapshot)

    # Multi-month warehouse IC
    wh_ic_mean, wh_ics = compute_warehouse_ic()

    # Write report
    print("\n[5] Writing report...")
    write_report(results, tickers, snapshot, forward_rets, wh_ic_mean, wh_ics, ern_scores, rev_scores, comb_scores)

    # Print summary
    print("\n" + "=" * 65)
    print("SUMMARY")
    print("=" * 65)
    print(f"Warehouse 50/50 IC (47mo): {_fmt(wh_ic_mean)}")
    for label in ["earnings_growth", "revenue_growth", "earnings+revenue", "earnings_acceleration", "3Y earnings CAGR"]:
        r = results.get(label, {})
        ic = r.get("ic", {})
        ic_1 = _fmt(ic.get("1M")) if ic and ic.get("1M") is not None else "N/A"
        cagr = _fmt(r.get("cagr"), True) if r.get("cagr") is not None else "N/A"
        print(f"{label:>25}: 1M IC={ic_1}, CAGR={cagr}")
    print(f"\nReport: {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
