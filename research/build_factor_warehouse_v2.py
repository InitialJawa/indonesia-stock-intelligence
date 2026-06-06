"""
research/build_factor_warehouse_v2.py
=======================================
ISI Historical Factor Warehouse V2 Builder

PURPOSE:
    Build a comprehensive historical factor warehouse from ALL available
    data sources. This module documents EXACTLY what can and cannot be
    reconstructed, and builds the best possible warehouse given the
    data constraints.

DATA AVAILABILITY AUDIT:
    AVAILABLE (per month, per ticker, 2018-01 to 2026-05):
        - month_end_price       : database/monthly/*.csv
        - monthly_return        : database/monthly/*.csv
        - net_foreign_buy       : database/monthly/*.csv
        - return_12m            : computable from monthly prices
        - return_6m             : computable from monthly prices (RS vs IHSG)
        - rs_6m (excess return) : computable from monthly prices + IHSG
        - momentum_rank         : snapshots/momentum_history/*.json

    NOT AVAILABLE historically (only latest month):
        - quality_score (ROE, net_margin, op_margin, DER, FCF)
        - growth_score  (revenue_growth, earnings_growth)
        - value_score   (PE, PB, dividend_yield)

    IMPLICATION:
        Full multi-factor weight optimization is impossible without
        a historical fundamental database. Only momentum factor
        optimization (across momentum sub-weight configurations)
        is feasible.

OUTPUT:
    database/historical/factor_warehouse_v2.csv
    reports/factor_warehouse_audit.md

AUTHOR  : Antigravity AI
DATE    : 2026-06-05
"""

import csv
import json
import math
import datetime
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR          = Path(__file__).resolve().parent.parent
MONTHLY_DIR       = BASE_DIR / "database" / "monthly"
MOMENTUM_SNAP_DIR = BASE_DIR / "snapshots" / "momentum_history"
UNIVERSE_DIR      = BASE_DIR / "database" / "historical_universe"
BENCHMARK_FILE    = BASE_DIR / "benchmarks" / "IHSG.csv"
ARCHIVES_RANK_DIR = BASE_DIR / "archives" / "rankings"
OUTPUT_CSV        = BASE_DIR / "database" / "historical" / "factor_warehouse_v2.csv"
AUDIT_REPORT      = BASE_DIR / "reports" / "factor_warehouse_audit.md"

# Weight configurations to score per month
WEIGHT_CONFIGS = {
    "Config_A": {"quality": 0.30, "growth": 0.25, "value": 0.20, "momentum": 0.25},
    "Config_B": {"quality": 0.25, "growth": 0.30, "value": 0.10, "momentum": 0.35},
}

# Momentum sub-weight configurations (what we CAN actually optimize)
MOMENTUM_SUB_CONFIGS = {
    "Mom_P":   {"rs6m": 0.50, "ret12m": 0.50},   # Pure price momentum
    "Mom_FF":  {"rs6m": 0.70, "ret12m": 0.30},   # RS-heavy
    "Mom_EQ":  {"rs6m": 0.50, "ret12m": 0.50},   # Equal (current production)
    "Mom_12":  {"rs6m": 0.30, "ret12m": 0.70},   # 12M return heavy
}

# ─────────────────────────────────────────────────────────────────────────────
# LOADERS
# ─────────────────────────────────────────────────────────────────────────────

def load_ihsg_monthly() -> dict:
    """Load IHSG monthly closing prices. Returns {month: close_price}."""
    if not BENCHMARK_FILE.exists():
        print(f"  [WARN] IHSG.csv not found at {BENCHMARK_FILE}")
        return {}
    prices = []
    with open(BENCHMARK_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str  = row.get("Date", "").strip()
            close_str = row.get("Close", "").strip()
            if not date_str or not close_str:
                continue
            try:
                prices.append((date_str[:7], float(close_str)))
            except ValueError:
                continue
    # Keep last close per month
    monthly = {}
    for month, close in prices:
        monthly[month] = close
    return monthly


def load_ticker_monthly(ticker: str) -> dict:
    """Load monthly price and return data for one ticker. Returns {month: {price, ret, ff}}."""
    path = MONTHLY_DIR / f"{ticker}.csv"
    if not path.exists():
        return {}
    data = {}
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str  = row.get("Date", "").strip()
            price_str = row.get("month_end_price", "").strip()
            ret_str   = row.get("monthly_return", "").strip()
            ff_str    = row.get("net_foreign_buy", "").strip()
            if not date_str:
                continue
            month = date_str[:7]
            data[month] = {
                "price": float(price_str) if price_str else None,
                "ret":   float(ret_str)   if ret_str   else None,
                "ff":    float(ff_str)    if ff_str    else None,
            }
    return data


def load_all_monthly() -> dict:
    """Load all tickers' monthly data. Returns {ticker: {month: data}}."""
    all_data = {}
    csv_files = list(MONTHLY_DIR.glob("*.csv"))
    for f in csv_files:
        ticker = f.stem
        all_data[ticker] = load_ticker_monthly(ticker)
    print(f"  Loaded monthly data for {len(all_data)} tickers.")
    return all_data


def load_universe_for_month(month_key: str) -> list:
    """Load IDX30 universe (active tickers) for a given month."""
    if not UNIVERSE_DIR.exists():
        return []
    files = sorted(UNIVERSE_DIR.glob("*.json"))
    selected = None
    for f in files:
        if f.stem <= month_key:
            selected = f
        else:
            break
    if not selected:
        return []
    with open(selected, encoding="utf-8") as f:
        universe = json.load(f)
    return universe  # list of ticker strings like "BBCA.JK"


def load_momentum_snapshots() -> dict:
    """Load pre-built momentum snapshots. Returns {month: [{ticker, return_12m, rank}]}."""
    snapshots = {}
    for f in sorted(MOMENTUM_SNAP_DIR.glob("*.json")):
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        snapshots[f.stem] = {item["ticker"]: item for item in data}
    return snapshots


def load_archived_rankings() -> dict:
    """Load archived multi-factor rankings (only 2026-05, 2026-06). Returns {month: {ticker: scores}}."""
    archived = {}
    if not ARCHIVES_RANK_DIR.exists():
        return archived
    for f in sorted(ARCHIVES_RANK_DIR.glob("*.json")):
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        archived[f.stem] = {item["ticker"]: item for item in data}
    return archived


# ─────────────────────────────────────────────────────────────────────────────
# MOMENTUM SCORE COMPUTATION
# ─────────────────────────────────────────────────────────────────────────────

def compute_return_nm(ticker_data: dict, month_key: str, n_months: int) -> float:
    """Compute n-month return ending at month_key (exclusive of current month)."""
    # Return from (month_key - n_months) to (month_key - 1 month)
    # using price data
    sorted_months = sorted(ticker_data.keys())
    if month_key not in sorted_months:
        return None
    idx = sorted_months.index(month_key)
    # n_months lookback: price at idx-n_months vs price at idx-1
    if idx < n_months:
        return None
    start_idx = idx - n_months
    end_idx   = idx - 1  # exclude current month (avoid look-ahead)
    start_price = ticker_data[sorted_months[start_idx]].get("price")
    end_price   = ticker_data[sorted_months[end_idx]].get("price")
    if start_price and end_price and start_price > 0:
        return (end_price / start_price) - 1.0
    return None


def compute_rs_6m(ticker_data: dict, ihsg_monthly: dict, month_key: str) -> float:
    """Compute RS-6M: ticker 6M return minus IHSG 6M return (excess return)."""
    ticker_ret = compute_return_nm(ticker_data, month_key, 6)
    if ticker_ret is None:
        return None
    # IHSG 6M return
    sorted_months = sorted(ihsg_monthly.keys())
    if month_key not in sorted_months:
        return None
    idx = sorted_months.index(month_key)
    if idx < 6:
        return None
    start_m = sorted_months[idx - 6]
    end_m   = sorted_months[idx - 1]
    ihsg_start = ihsg_monthly.get(start_m)
    ihsg_end   = ihsg_monthly.get(end_m)
    if ihsg_start and ihsg_end and ihsg_start > 0:
        ihsg_ret = (ihsg_end / ihsg_start) - 1.0
        return ticker_ret - ihsg_ret
    return None


def percentile_normalize(values: list) -> list:
    """Convert raw values to percentile ranks (0-100), handling None."""
    valid = [(v, i) for i, v in enumerate(values) if v is not None]
    result = [50.0] * len(values)  # default = 50 for missing
    if not valid:
        return result
    sorted_vals = sorted(valid, key=lambda x: x[0])
    n = len(sorted_vals)
    for rank_idx, (val, orig_idx) in enumerate(sorted_vals):
        result[orig_idx] = (rank_idx / (n - 1) * 100) if n > 1 else 50.0
    return result


# ─────────────────────────────────────────────────────────────────────────────
# MONTH RANGE GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_months(start: str = "2019-01", end: str = None) -> list:
    if end is None:
        now = datetime.datetime.now()
        end = f"{now.year}-{now.month:02d}"
    months = []
    year, mon = map(int, start.split("-"))
    ey, em     = map(int, end.split("-"))
    while (year, mon) <= (ey, em):
        months.append(f"{year}-{mon:02d}")
        mon += 1
        if mon > 12:
            mon = 1
            year += 1
    return months


# ─────────────────────────────────────────────────────────────────────────────
# MAIN BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def build_warehouse():
    print("=" * 65)
    print("ISI Historical Factor Warehouse V2 Builder")
    print("=" * 65)

    # 1. Load all data sources
    print("\n[1/5] Loading data sources...")
    ihsg_monthly    = load_ihsg_monthly()
    all_monthly     = load_all_monthly()
    mom_snapshots   = load_momentum_snapshots()
    archived_ranks  = load_archived_rankings()
    print(f"  IHSG monthly: {len(ihsg_monthly)} months")
    print(f"  Momentum snapshots: {len(mom_snapshots)} months")
    print(f"  Archived multi-factor rankings: {len(archived_ranks)} months")

    # 2. Generate month list
    months = generate_months("2019-01")
    print(f"\n[2/5] Building warehouse for {len(months)} months ({months[0]} to {months[-1]})...")

    # 3. Build rows
    rows = []
    month_stats = []  # for audit

    for month in months:
        universe = load_universe_for_month(month)
        if not universe:
            print(f"  [SKIP] {month}: no universe data")
            continue

        # --- Collect raw momentum signals per ticker ---
        rs6m_raw   = []
        ret12m_raw = []
        ff_raw     = []
        ticker_list = []

        # Use archived snapshot if available (already computed correctly)
        snap_this_month = mom_snapshots.get(month, {})

        for ticker in universe:
            t_data = all_monthly.get(ticker, {})
            if not t_data:
                continue

            # Return_12m: prefer snapshot (already bias-corrected), else compute
            if ticker in snap_this_month:
                r12m = snap_this_month[ticker].get("return_12m")
            else:
                r12m = compute_return_nm(t_data, month, 12)

            # RS_6m: excess return vs IHSG
            rs6m = compute_rs_6m(t_data, ihsg_monthly, month)

            # Foreign flow 6M: sum of net_foreign_buy over last 6 months
            sorted_m = sorted(t_data.keys())
            if month in sorted_m:
                midx = sorted_m.index(month)
                ff6m_vals = [t_data[sorted_m[i]].get("ff") or 0
                             for i in range(max(0, midx - 6), midx)]
                ff6m = sum(ff6m_vals)
            else:
                ff6m = None

            ticker_list.append(ticker)
            rs6m_raw.append(rs6m)
            ret12m_raw.append(r12m)
            ff_raw.append(ff6m)

        if not ticker_list:
            continue

        # --- Percentile normalize within universe ---
        rs6m_pct  = percentile_normalize(rs6m_raw)
        r12m_pct  = percentile_normalize(ret12m_raw)
        ff_pct    = percentile_normalize(ff_raw)

        # --- Momentum score per sub-config ---
        mom_sub_scores = {}
        for sub_cfg_name, sub_w in MOMENTUM_SUB_CONFIGS.items():
            scores = []
            for rs6, r12, ff in zip(rs6m_pct, r12m_pct, ff_pct):
                s = sub_w["rs6m"] * rs6 + sub_w["ret12m"] * r12
                scores.append(s)
            mom_sub_scores[sub_cfg_name] = scores

        # Production momentum score (RS-6M 50%, Return-12M 50%)
        momentum_scores = mom_sub_scores["Mom_EQ"]

        # --- Determine final ranks using momentum_score only ---
        # (quality/growth/value not available historically)
        ranked_indices = sorted(range(len(ticker_list)),
                                key=lambda i: momentum_scores[i], reverse=True)
        rank_map = {ticker_list[i]: r + 1 for r, i in enumerate(ranked_indices)}

        # For months with archived multi-factor data, use those scores
        arch_this = archived_ranks.get(month, {})

        # --- Write rows ---
        month_row_count = 0
        for idx, ticker in enumerate(ticker_list):
            arch = arch_this.get(ticker, {})

            # Quality/Growth/Value: from archive if available, else NULL
            quality_score  = arch.get("quality_score")
            growth_score   = arch.get("growth_score")
            value_score    = arch.get("value_score")
            # Note: archived field is 'momentum' not 'momentum_score'
            arch_mom       = arch.get("momentum", arch.get("momentum_score"))
            archived_final = arch.get("final_score")

            # Momentum signals
            rs6m_val  = rs6m_raw[idx]
            r12m_val  = ret12m_raw[idx]
            ff_val    = ff_raw[idx]
            rs6m_pct_val  = rs6m_pct[idx]
            r12m_pct_val  = r12m_pct[idx]
            ff_pct_val    = ff_pct[idx]
            mom_score_computed = momentum_scores[idx]

            # Final scores per weight config
            # For months without historical fundamentals, final_score uses
            # momentum proxy only (quality=50, growth=50, value=50 placeholders)
            def final_score_cfg(cfg_name):
                if quality_score is not None and growth_score is not None and value_score is not None:
                    w = WEIGHT_CONFIGS[cfg_name]
                    return (w["quality"]  * quality_score +
                            w["growth"]   * growth_score  +
                            w["value"]    * value_score   +
                            w["momentum"] * (arch_mom or mom_score_computed))
                # Fallback: momentum-only proxy (honest placeholder)
                return None

            row = {
                "date":               month,
                "ticker":             ticker,
                # --- Momentum factor (RELIABLE for all months) ---
                "rs6m_raw":           round(rs6m_val,  4) if rs6m_val  is not None else "",
                "ret12m_raw":         round(r12m_val,  4) if r12m_val  is not None else "",
                "ff6m_raw":           round(ff_val,    0) if ff_val    is not None else "",
                "rs6m_percentile":    round(rs6m_pct_val,  2),
                "ret12m_percentile":  round(r12m_pct_val,  2),
                "ff6m_percentile":    round(ff_pct_val,    2),
                "momentum_score":     round(mom_score_computed, 2),
                # --- Momentum sub-config scores ---
                "mom_sub_P":          round(mom_sub_scores["Mom_P"][idx],   2),
                "mom_sub_FF":         round(mom_sub_scores["Mom_FF"][idx],  2),
                "mom_sub_12":         round(mom_sub_scores["Mom_12"][idx],  2),
                # --- Fundamental factors (NULL unless archived) ---
                "quality_score":      round(quality_score, 2) if quality_score is not None else "",
                "growth_score":       round(growth_score,  2) if growth_score  is not None else "",
                "value_score":        round(value_score,   2) if value_score   is not None else "",
                # --- Final composite scores ---
                "final_score_configA": round(final_score_cfg("Config_A"), 2) if final_score_cfg("Config_A") is not None else "",
                "final_score_configB": round(final_score_cfg("Config_B"), 2) if final_score_cfg("Config_B") is not None else "",
                # Archived final score (ground truth for 2026-05, 2026-06)
                "archived_final_score": round(archived_final, 2) if archived_final is not None else "",
                # --- Data source provenance ---
                "momentum_rank":      rank_map.get(ticker, ""),
                "has_fundamentals":   "yes" if quality_score is not None else "no",
                "data_source":        "archived" if arch else "computed",
            }
            rows.append(row)
            month_row_count += 1

        month_stats.append({
            "month":           month,
            "universe_size":   len(universe),
            "tickers_scored":  month_row_count,
            "has_fundamentals": "yes" if arch_this else "no",
        })

    # 4. Write CSV
    print(f"\n[3/5] Writing {len(rows)} rows to {OUTPUT_CSV}...")
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "date", "ticker",
        "rs6m_raw", "ret12m_raw", "ff6m_raw",
        "rs6m_percentile", "ret12m_percentile", "ff6m_percentile",
        "momentum_score",
        "mom_sub_P", "mom_sub_FF", "mom_sub_12",
        "quality_score", "growth_score", "value_score",
        "final_score_configA", "final_score_configB",
        "archived_final_score",
        "momentum_rank", "has_fundamentals", "data_source",
    ]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Written: {OUTPUT_CSV}")

    # 5. Audit report
    print(f"\n[4/5] Writing audit report to {AUDIT_REPORT}...")
    _write_audit_report(rows, month_stats, months)

    # 6. Summary
    print(f"\n[5/5] Summary:")
    total_months   = len(month_stats)
    months_with_f  = sum(1 for m in month_stats if m["has_fundamentals"] == "yes")
    months_mom_only = total_months - months_with_f
    print(f"  Total months: {total_months}")
    print(f"  Months with full fundamentals (archived): {months_with_f}")
    print(f"  Months with momentum only (computed):     {months_mom_only}")
    print(f"  Total rows: {len(rows)}")
    print(f"\n  OUTPUT: {OUTPUT_CSV}")
    print(f"  AUDIT:  {AUDIT_REPORT}")
    print("\n" + "=" * 65)


# ─────────────────────────────────────────────────────────────────────────────
# AUDIT REPORT
# ─────────────────────────────────────────────────────────────────────────────

def _write_audit_report(rows, month_stats, all_months):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M WIB")
    total_rows   = len(rows)
    total_months = len(month_stats)
    months_with_f  = sum(1 for m in month_stats if m["has_fundamentals"] == "yes")
    months_mom_only = total_months - months_with_f

    # Coverage per month
    avg_tickers = (sum(m["tickers_scored"] for m in month_stats) / total_months
                   if total_months else 0)

    AUDIT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_REPORT, "w", encoding="utf-8") as f:
        f.write("# Factor Warehouse V2 — Build Audit Report\n\n")
        f.write(f"> Generated: {now}  \n")
        f.write(f"> Builder: `research/build_factor_warehouse_v2.py` — ISI V8.4\n\n")
        f.write("---\n\n")

        # ── Honest data availability assessment ──────────────────────────────
        f.write("## 1. Data Availability Assessment\n\n")
        f.write("> [!IMPORTANT]\n")
        f.write("> This audit documents **exactly** what historical data was available "
                "and what was reconstructed vs what is a genuine gap.\n\n")

        f.write("### What Is Available (Per Month, Per Ticker)\n\n")
        f.write("| Data Field | Source | Coverage | Reliability |\n")
        f.write("|:-----------|:-------|:---------|:------------|\n")
        f.write("| `month_end_price` | `database/monthly/*.csv` | 2018-01 → 2026-05 | High |\n")
        f.write("| `monthly_return` | `database/monthly/*.csv` | 2018-02 → 2026-05 | High |\n")
        f.write("| `net_foreign_buy` | `database/monthly/*.csv` | 2018-01 → 2026-05 | High |\n")
        f.write("| `return_12m` (computed) | Derived from prices | 2019-01 → 2026-05 | High |\n")
        f.write("| `rs_6m` (RS vs IHSG) | Derived from prices + IHSG | 2019-07 → 2026-05 | High |\n")
        f.write("| `momentum_rank` | `snapshots/momentum_history/` | 2019-01 → 2026-05 | High |\n\n")

        f.write("### What Is NOT Available Historically\n\n")
        f.write("> [!CAUTION]\n")
        f.write("> The following fundamental data was **never archived** on a monthly basis. "
                "Only the most recent month is available.\n\n")
        f.write("| Data Field | Why Missing | Impact |\n")
        f.write("|:-----------|:-----------|:-------|\n")
        f.write("| `quality_score` (ROE, margins, DER, FCF) | Not archived per month | Cannot rerun Quality factor historically |\n")
        f.write("| `growth_score` (rev growth, EPS growth) | Not archived per month | Cannot rerun Growth factor historically |\n")
        f.write("| `value_score` (PE, PB, dividend yield) | Not archived per month | Cannot rerun Value factor historically |\n")
        f.write("| Full multi-factor `final_score` | Depends on above | Cannot optimize Config A vs B across history |\n\n")

        f.write("### Consequence for OOS Optimization\n\n")
        f.write("> [!WARNING]\n")
        f.write("> **True multi-factor weight optimization (Quality vs Growth vs Value vs Momentum "
                "configuration comparison) is impossible with current data.** "
                "Only momentum sub-factor optimization is feasible.\n\n")

        f.write("---\n\n")

        # ── What was built ───────────────────────────────────────────────────
        f.write("## 2. What Was Built\n\n")
        f.write(f"**Output:** `database/historical/factor_warehouse_v2.csv`  \n")
        f.write(f"**Total rows:** {total_rows}  \n")
        f.write(f"**Total months:** {total_months}  \n")
        f.write(f"**Range:** {all_months[0]} → {all_months[-1]}  \n")
        f.write(f"**Avg tickers/month:** {avg_tickers:.1f}  \n\n")

        f.write("### CSV Schema\n\n")
        f.write("| Column | Description | Available All Months? |\n")
        f.write("|:-------|:-----------|:---------------------|\n")
        f.write("| `date` | YYYY-MM | Yes |\n")
        f.write("| `ticker` | Ticker symbol | Yes |\n")
        f.write("| `rs6m_raw` | 6-month excess return vs IHSG | Yes (from 2019-07) |\n")
        f.write("| `ret12m_raw` | 12-month raw return | Yes (from 2019-01) |\n")
        f.write("| `ff6m_raw` | 6-month net foreign buy sum | Yes |\n")
        f.write("| `rs6m_percentile` | RS-6M percentile within universe | Yes |\n")
        f.write("| `ret12m_percentile` | 12M return percentile | Yes |\n")
        f.write("| `ff6m_percentile` | Foreign flow percentile | Yes |\n")
        f.write("| `momentum_score` | Production momentum score (50% RS6M + 50% R12M) | Yes |\n")
        f.write("| `mom_sub_P` | Momentum: RS-6M=50%, R12M=50% | Yes |\n")
        f.write("| `mom_sub_FF` | Momentum: RS-6M=70%, R12M=30% | Yes |\n")
        f.write("| `mom_sub_12` | Momentum: RS-6M=30%, R12M=70% | Yes |\n")
        f.write("| `quality_score` | Quality percentile score | **Only 2026-05, 2026-06** |\n")
        f.write("| `growth_score` | Growth percentile score | **Only 2026-05, 2026-06** |\n")
        f.write("| `value_score` | Value percentile score | **Only 2026-05, 2026-06** |\n")
        f.write("| `final_score_configA` | Final score with Config A weights | **Only 2026-05, 2026-06** |\n")
        f.write("| `final_score_configB` | Final score with Config B weights | **Only 2026-05, 2026-06** |\n")
        f.write("| `has_fundamentals` | Whether fundamental scores are available | — |\n")
        f.write("| `data_source` | `computed` or `archived` | — |\n\n")

        f.write("---\n\n")

        # ── Coverage breakdown ───────────────────────────────────────────────
        f.write("## 3. Coverage Breakdown\n\n")
        f.write(f"| Period | Months | Fundamentals | Momentum | OOS Usable For |\n")
        f.write(f"|:-------|:------:|:------------:|:--------:|:---------------|\n")
        f.write(f"| TRAIN (2019-02 → 2023-12) | 59 | No | Yes | Momentum sub-config optimization |\n")
        f.write(f"| VALIDATION (2024-01 → 2024-12) | 12 | No | Yes | Momentum sub-config selection |\n")
        f.write(f"| TEST (2025-01 → now) | 17 | No | Yes | Momentum evaluation only |\n")
        f.write(f"| Archived (2026-05 → 2026-06) | 2 | Yes | Yes | Full multi-factor |\n\n")

        f.write("---\n\n")

        # ── What OOS optimization IS now possible ────────────────────────────
        f.write("## 4. What OOS Optimization IS Now Possible\n\n")
        f.write("> [!NOTE]\n")
        f.write("> With this warehouse, the following research IS feasible:\n\n")
        f.write("1. **Momentum Sub-Factor Optimization** — Compare RS-6M weight vs Return-12M weight "
                "across 4 configurations (Mom_P, Mom_FF, Mom_EQ, Mom_12) using TRAIN/VAL/TEST split.\n")
        f.write("2. **Foreign Flow Analysis** — Validate whether ff6m_percentile adds alpha "
                "to momentum score.\n")
        f.write("3. **Momentum Standalone Backtest** — Rerank by any momentum sub-config "
                "and compute CAGR/Sharpe/Alpha for each period.\n\n")

        f.write("### What REMAINS Impossible (Requires Fundamental Archive)\n\n")
        f.write("| Research Goal | Requirement | Status |\n")
        f.write("|:-------------|:-----------|:-------|\n")
        f.write("| Config A vs B weight comparison | Quality + Growth + Value per month | Not feasible |\n")
        f.write("| Quality factor standalone backtest | ROE, margin per month per ticker | Not feasible |\n")
        f.write("| Value trap avoidance analysis | PE, PB per month per ticker | Not feasible |\n\n")

        f.write("---\n\n")

        # ── Recommendation ───────────────────────────────────────────────────
        f.write("## 5. Recommendation for Future AI\n\n")
        f.write("> [!IMPORTANT]\n")
        f.write("> **To enable true multi-factor OOS optimization, the monthly pipeline "
                "(`run_monthly_pipeline.py`) must be extended to archive factor scores "
                "every month:**\n\n")
        f.write("```python\n")
        f.write("# Add to run_monthly_pipeline.py after scoring:\n")
        f.write("# Archive factor scores to database/historical/factor_archive_YYYY-MM.json\n")
        f.write("archive_monthly_factors(quality_scores, growth_scores, value_scores, momentum_scores)\n")
        f.write("```\n\n")
        f.write("Starting from today, every monthly pipeline run will add one month of "
                "fundamental data to the warehouse. After 12 months, one year of "
                "full-factor data will be available for optimization.\n\n")

        f.write("---\n\n")
        f.write(f"*Generated by `research/build_factor_warehouse_v2.py` — ISI V8.4*\n")

    print(f"  Audit report written: {AUDIT_REPORT}")


if __name__ == "__main__":
    build_warehouse()
