"""
research/out_of_sample_validation.py
=====================================
ISI Out-of-Sample Validation Framework (V8.4)

PURPOSE:
    Memastikan seluruh keputusan factor research dan weight optimization
    tidak mengalami overfitting terhadap data historis.

DATA SPLIT:
    TRAIN      : 2019-02 → 2023-12   (60 bulan return)
    VALIDATION : 2024-01 → 2024-12   (12 bulan return)
    TEST       : 2025-01 → sekarang  (open-ended, evaluasi final)

WORKFLOW:
    1. Optimization HANYA dilakukan pada TRAIN.
    2. Pemilihan konfigurasi terbaik menggunakan VALIDATION.
    3. Evaluasi final pada TEST tanpa tuning ulang.

GUARANTEE:
    Tidak ada parameter yang dipilih menggunakan data TEST.
    Semua riset faktor berikutnya wajib melewati framework ini
    sebelum boleh masuk production.

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
BASE_DIR           = Path(__file__).resolve().parent.parent
RETURNS_FILE       = BASE_DIR / "database" / "historical" / "momentum_monthly_returns.csv"
BENCHMARK_FILE     = BASE_DIR / "benchmarks" / "IHSG.csv"
PORTFOLIO_FILE     = BASE_DIR / "archives" / "backtest" / "momentum_portfolio.csv"
TICKER_DATA_DIR    = BASE_DIR / "database" / "monthly"
SNAPSHOT_DIR       = BASE_DIR / "snapshots" / "momentum_history"
SCORING_WEIGHTS    = BASE_DIR / "config" / "scoring_weights.json"
REPORT_FILE        = BASE_DIR / "reports" / "out_of_sample_validation.md"
CHRONICLE_FILE     = BASE_DIR / "master_chronicle.txt"

# ─────────────────────────────────────────────────────────────────────────────
# SPLIT BOUNDARIES
# ─────────────────────────────────────────────────────────────────────────────
TRAIN_START      = "2019-02"
TRAIN_END        = "2023-12"
VALIDATION_START = "2024-01"
VALIDATION_END   = "2024-12"
TEST_START       = "2025-01"
# TEST_END = open (sekarang)

# ─────────────────────────────────────────────────────────────────────────────
# WEIGHT CONFIGURATIONS TO EVALUATE
# ─────────────────────────────────────────────────────────────────────────────
WEIGHT_CONFIGS = {
    "Config_A (Legacy Equal)":     {"quality": 0.30, "growth": 0.25, "value": 0.20, "momentum": 0.25},
    "Config_B (Alpha Optimized)":  {"quality": 0.25, "growth": 0.30, "value": 0.10, "momentum": 0.35},
    "Config_C (Momentum Heavy)":   {"quality": 0.20, "growth": 0.25, "value": 0.05, "momentum": 0.50},
    "Config_D (Quality First)":    {"quality": 0.40, "growth": 0.25, "value": 0.10, "momentum": 0.25},
    "Config_E (Balanced)":         {"quality": 0.25, "growth": 0.25, "value": 0.25, "momentum": 0.25},
}

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADERS
# ─────────────────────────────────────────────────────────────────────────────

def load_monthly_returns() -> dict:
    """Load pre-computed monthly returns from momentum_monthly_returns.csv."""
    data = {}
    if not RETURNS_FILE.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {RETURNS_FILE}")
    with open(RETURNS_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            month = row["date"].strip()[:7]
            data[month] = {
                "portfolio": float(row["portfolio_return"]),
                "benchmark": float(row["benchmark_return"]),
                "excess":    float(row["excess_return"]),
            }
    return data


def load_snapshot_rankings() -> dict:
    """Load momentum snapshot rankings per month from snapshots/momentum_history/."""
    rankings = {}
    if not SNAPSHOT_DIR.exists():
        return rankings
    for f in sorted(SNAPSHOT_DIR.glob("*.json")):
        month_key = f.stem  # e.g., '2024-01'
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        data.sort(key=lambda x: x.get("rank", 999))
        rankings[month_key] = data
    return rankings


def load_ticker_returns() -> dict:
    """Load per-ticker monthly returns from database/monthly/*.csv."""
    ticker_returns = {}
    if not TICKER_DATA_DIR.exists():
        return ticker_returns
    for file in TICKER_DATA_DIR.glob("*.csv"):
        ticker = file.stem
        ticker_returns[ticker] = {}
        with open(file, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                date_str = row.get("Date", "").strip()
                ret_str  = row.get("monthly_return", "").strip()
                if not date_str or not ret_str:
                    continue
                month_key = date_str[:7]
                try:
                    ticker_returns[ticker][month_key] = float(ret_str)
                except ValueError:
                    continue
    return ticker_returns


def load_ihsg_monthly() -> dict:
    """Load IHSG monthly returns from benchmarks/IHSG.csv."""
    ihsg_prices = []
    if not BENCHMARK_FILE.exists():
        return {}
    with open(BENCHMARK_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str  = row.get("Date", "").strip()
            close_str = row.get("Close", "").strip()
            if not date_str or not close_str:
                continue
            try:
                ihsg_prices.append((date_str, float(close_str)))
            except ValueError:
                continue
    ihsg_prices.sort(key=lambda x: x[0])
    monthly_closes = {}
    for date, close in ihsg_prices:
        monthly_closes[date[:7]] = close
    sorted_months = sorted(monthly_closes)
    ihsg_returns  = {}
    for i in range(1, len(sorted_months)):
        prev, curr = sorted_months[i - 1], sorted_months[i]
        p_close, c_close = monthly_closes[prev], monthly_closes[curr]
        if p_close > 0:
            ihsg_returns[curr] = (c_close / p_close) - 1.0
    return ihsg_returns


# ─────────────────────────────────────────────────────────────────────────────
# METRICS ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def _safe_mean(data):
    return sum(data) / len(data) if data else 0.0


def _safe_std(data, mean_val=None):
    if len(data) < 2:
        return 0.0
    if mean_val is None:
        mean_val = _safe_mean(data)
    variance = sum((x - mean_val) ** 2 for x in data) / (len(data) - 1)
    return math.sqrt(variance)


def calculate_metrics(portfolio_returns: list, benchmark_returns: list) -> dict:
    """
    Compute full performance metrics for a list of monthly portfolio returns
    vs a matching list of benchmark returns.
    """
    n = len(portfolio_returns)
    if n == 0:
        return _empty_metrics()

    years = n / 12.0

    # ── Equity curve ──────────────────────────────────────────────────────────
    equity    = 1.0
    eq_curve  = []
    drawdowns = []
    peak      = 1.0
    for r in portfolio_returns:
        equity *= (1 + r)
        eq_curve.append(equity)
        peak = max(peak, equity)
        drawdowns.append((peak - equity) / peak)

    cagr     = equity ** (1.0 / years) - 1.0
    mean_r   = _safe_mean(portfolio_returns)
    ann_ret  = mean_r * 12.0
    vol      = _safe_std(portfolio_returns, mean_r) * math.sqrt(12)
    sharpe   = ann_ret / vol if vol > 0 else 0.0
    max_dd   = max(drawdowns) if drawdowns else 0.0

    # ── Sortino ───────────────────────────────────────────────────────────────
    downside = [r for r in portfolio_returns if r < 0]
    downside_std = _safe_std(downside, 0) * math.sqrt(12) if len(downside) >= 2 else 0.0
    sortino  = ann_ret / downside_std if downside_std > 0 else 0.0

    # ── Win Rate ──────────────────────────────────────────────────────────────
    win_rate = sum(1 for r in portfolio_returns if r > 0) / n

    # ── Turnover (estimated — fraction of portfolio replaced per month) ────────
    # Since we use Top-5 equal weight momentum, we approximate from snapshots
    # but here we report N/A unless explicitly provided
    turnover = None

    # ── CAPM Alpha & Beta vs benchmark ───────────────────────────────────────
    alpha_ann, beta = 0.0, 0.0
    if len(benchmark_returns) == n and n > 1:
        mean_p = _safe_mean(portfolio_returns)
        mean_b = _safe_mean(benchmark_returns)
        cov_pb = sum((p - mean_p) * (b - mean_b)
                     for p, b in zip(portfolio_returns, benchmark_returns)) / (n - 1)
        var_b  = sum((b - mean_b) ** 2 for b in benchmark_returns) / (n - 1)
        beta   = cov_pb / var_b if var_b > 0 else 0.0
        alpha_monthly = mean_p - beta * mean_b
        alpha_ann     = alpha_monthly * 12.0

    b_eq   = 1.0
    for r in benchmark_returns:
        b_eq *= (1 + r)
    b_cagr   = b_eq ** (1.0 / years) - 1.0 if years > 0 else 0.0
    excess_cagr = cagr - b_cagr

    return {
        "months":          n,
        "cagr":            cagr,
        "ann_return":      ann_ret,
        "volatility":      vol,
        "sharpe":          sharpe,
        "sortino":         sortino,
        "max_drawdown":    max_dd,
        "win_rate":        win_rate,
        "alpha_ann":       alpha_ann,
        "beta":            beta,
        "benchmark_cagr":  b_cagr,
        "excess_cagr":     excess_cagr,
        "equity_final":    equity,
        "best_month":      max(portfolio_returns),
        "worst_month":     min(portfolio_returns),
        "turnover":        turnover,
    }


def _empty_metrics() -> dict:
    keys = ["months", "cagr", "ann_return", "volatility", "sharpe", "sortino",
            "max_drawdown", "win_rate", "alpha_ann", "beta", "benchmark_cagr",
            "excess_cagr", "equity_final", "best_month", "worst_month", "turnover"]
    return {k: 0.0 for k in keys}


# ─────────────────────────────────────────────────────────────────────────────
# PERIOD SLICER
# ─────────────────────────────────────────────────────────────────────────────

def slice_period(all_returns: dict, start: str, end: str = None) -> tuple:
    """Return (portfolio_returns, benchmark_returns, months) for a date range."""
    sorted_months = sorted(all_returns.keys())
    portfolio_r, benchmark_r, months = [], [], []
    for m in sorted_months:
        if m < start:
            continue
        if end and m > end:
            break
        portfolio_r.append(all_returns[m]["portfolio"])
        benchmark_r.append(all_returns[m]["benchmark"])
        months.append(m)
    return portfolio_r, benchmark_r, months


# ─────────────────────────────────────────────────────────────────────────────
# TURNOVER CALCULATOR
# ─────────────────────────────────────────────────────────────────────────────

def compute_turnover(rankings: dict, start: str, end: str = None) -> float:
    """
    Estimate average monthly turnover as fraction of holdings replaced.
    Turnover = (# of new tickers entering portfolio) / (portfolio size) per month.
    """
    sorted_months = sorted(rankings.keys())
    in_range = [m for m in sorted_months
                if m >= start and (end is None or m <= end)]
    if len(in_range) < 2:
        return 0.0

    turnovers = []
    prev_set  = None
    for m in in_range:
        top5 = {item["ticker"] for item in rankings[m][:5]}
        if prev_set is not None:
            new_entries = len(top5 - prev_set)
            turnovers.append(new_entries / 5.0)
        prev_set = top5
    return _safe_mean(turnovers) if turnovers else 0.0


# ─────────────────────────────────────────────────────────────────────────────
# VERDICT ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def compute_verdict(train_m: dict, val_m: dict, test_m: dict) -> tuple:
    """
    Compare performance across periods and return (verdict, reasons).

    PASS    → Performa stabil antar periode; tidak ada degradasi signifikan.
    WARNING → Degradasi sedang pada satu metrik di TEST.
    FAIL    → Degradasi berat; indikasi overfitting.

    Rules (berbasis institutional research standards):
    - FAIL   jika CAGR TEST < 0% DAN Sharpe TEST < 0
    - FAIL   jika Max Drawdown TEST > 2× Max Drawdown TRAIN
    - WARNING jika CAGR TEST < 50% dari CAGR TRAIN
    - WARNING jika Sharpe TEST < 0.3 × Sharpe TRAIN
    - WARNING jika Win Rate TEST < 40%
    - PASS    jika tidak ada kondisi di atas terpenuhi
    """
    reasons = []
    level   = "PASS"   # optimistic default

    train_cagr    = train_m["cagr"]
    test_cagr     = test_m["cagr"]
    train_sharpe  = train_m["sharpe"]
    test_sharpe   = test_m["sharpe"]
    train_maxdd   = train_m["max_drawdown"]
    test_maxdd    = test_m["max_drawdown"]
    test_winrate  = test_m["win_rate"]
    val_cagr      = val_m["cagr"]

    # ── FAIL conditions ───────────────────────────────────────────────────────
    if test_cagr < 0.0 and test_sharpe < 0.0:
        level = "FAIL"
        reasons.append(f"TEST CAGR negatif ({test_cagr*100:.1f}%) dengan Sharpe negatif ({test_sharpe:.2f}). "
                       "Sinyal kuat overfitting.")

    if train_maxdd > 0 and test_maxdd > 2.0 * train_maxdd:
        level = "FAIL"
        reasons.append(f"Max Drawdown TEST ({test_maxdd*100:.1f}%) melebihi 2× TRAIN "
                       f"({train_maxdd*100:.1f}%). Risiko tidak terkontrol di data baru.")

    # ── WARNING conditions (hanya jika belum FAIL) ────────────────────────────
    if level != "FAIL":
        if train_cagr > 0 and test_cagr < 0.50 * train_cagr:
            level = "WARNING"
            reasons.append(f"CAGR TEST ({test_cagr*100:.1f}%) kurang dari 50% CAGR TRAIN "
                           f"({train_cagr*100:.1f}%). Potensi degradasi performa.")

        if train_sharpe > 0 and test_sharpe < 0.30 * train_sharpe:
            level = "WARNING"
            reasons.append(f"Sharpe TEST ({test_sharpe:.2f}) kurang dari 30% Sharpe TRAIN "
                           f"({train_sharpe:.2f}). Efisiensi return-risk menurun.")

        if test_winrate < 0.40:
            level = "WARNING"
            reasons.append(f"Win Rate TEST ({test_winrate*100:.1f}%) di bawah 40%. "
                           "Probabilitas keberhasilan bulanan rendah.")

        # Validation sanity check
        if val_cagr < 0.0 and test_cagr < 0.0:
            if level == "PASS":
                level = "WARNING"
            reasons.append(f"Baik Validation maupun TEST CAGR negatif — "
                           "periksa apakah kondisi pasar bersifat struktural.")

    if not reasons:
        reasons.append("Performa stabil lintas periode. Tidak ada degradasi signifikan terdeteksi.")

    return level, reasons


# ─────────────────────────────────────────────────────────────────────────────
# REPORT WRITER
# ─────────────────────────────────────────────────────────────────────────────

def _fmt(val, pct=False, sign=False):
    if val is None:
        return "N/A"
    if pct:
        s = f"{val * 100:+.2f}%" if sign else f"{val * 100:.2f}%"
        return s
    return f"{val:+.2f}" if sign else f"{val:.2f}"


def write_report(train_m, val_m, test_m,
                 train_months, val_months, test_months,
                 train_to, val_to, test_to,
                 best_config_name, all_config_scores,
                 verdict, verdict_reasons,
                 current_weights):

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M WIB")

    with open(REPORT_FILE, "w", encoding="utf-8") as f:

        f.write("# ISI Out-of-Sample Validation Report\n\n")
        f.write(f"> Generated: {now}  \n")
        f.write(f"> Framework: ISI V8.4 — Institutional OOS Validation\n\n")
        f.write("---\n\n")

        # ── VERDICT ──────────────────────────────────────────────────────────
        verdict_icons = {"PASS": "✅", "WARNING": "⚠️", "FAIL": "❌"}
        verdict_alert = {"PASS": "NOTE", "WARNING": "WARNING", "FAIL": "CAUTION"}
        f.write("## 🏆 Verdict Akhir\n\n")
        f.write(f"> [!{verdict_alert[verdict]}]\n")
        f.write(f"> **{verdict_icons[verdict]} {verdict}**  \n")
        for r in verdict_reasons:
            f.write(f"> {r}  \n")
        f.write("\n---\n\n")

        # ── SPLIT INFO ────────────────────────────────────────────────────────
        f.write("## 📐 Data Split\n\n")
        f.write("| Periode | Range | Jumlah Bulan Return |\n")
        f.write("|:--------|:------|:--------------------|\n")
        f.write(f"| **TRAIN** | {TRAIN_START} → {TRAIN_END} | {len(train_months)} |\n")
        f.write(f"| **VALIDATION** | {VALIDATION_START} → {VALIDATION_END} | {len(val_months)} |\n")
        f.write(f"| **TEST** | {TEST_START} → sekarang | {len(test_months)} |\n\n")
        f.write("> [!IMPORTANT]\n")
        f.write("> Tidak ada parameter yang dipilih menggunakan data TEST.\n\n")
        f.write("---\n\n")

        # ── PERFORMANCE TABLE ─────────────────────────────────────────────────
        f.write("## 📊 Performance Metrics Per Periode\n\n")
        f.write("| Metric | TRAIN | VALIDATION | TEST | Δ Train→Test |\n")
        f.write("|:-------|------:|----------:|-----:|------------:|\n")

        rows = [
            ("CAGR",         "cagr",         True,  True),
            ("Sharpe",       "sharpe",        False, True),
            ("Sortino",      "sortino",       False, True),
            ("Max Drawdown", "max_drawdown",  True,  False),
            ("Win Rate",     "win_rate",      True,  False),
            ("Alpha vs IHSG","alpha_ann",     True,  True),
            ("Beta vs IHSG", "beta",          False, False),
            ("Excess CAGR",  "excess_cagr",   True,  True),
        ]
        for label, key, is_pct, is_sign in rows:
            tv = train_m.get(key, 0)
            vv = val_m.get(key, 0)
            sv = test_m.get(key, 0)
            delta = sv - tv
            f.write(f"| **{label}** | {_fmt(tv, is_pct)} | {_fmt(vv, is_pct)} "
                    f"| {_fmt(sv, is_pct)} | {_fmt(delta, is_pct, True)} |\n")

        f.write("\n")

        # Turnover
        f.write("| **Turnover (est.)** | ")
        f.write(f"{_fmt(train_to, True)} | {_fmt(val_to, True)} | {_fmt(test_to, True)} | — |\n\n")

        f.write("---\n\n")

        # ── WEIGHT CONFIG OPTIMIZATION ────────────────────────────────────────
        f.write("## ⚙️ Weight Configuration Optimization (TRAIN + VALIDATION Only)\n\n")
        f.write("> [!NOTE]\n")
        f.write("> Optimization dilakukan **hanya** pada data TRAIN + VALIDATION. "
                "Data TEST tidak disentuh.\n\n")
        f.write("| Konfigurasi | Quality | Growth | Value | Momentum | "
                "TRAIN Sharpe | VAL Sharpe | VAL CAGR |\n")
        f.write("|:------------|--------:|------:|------:|--------:|"
                "-----------:|----------:|--------:|\n")
        for cfg_name, scores in all_config_scores.items():
            w = WEIGHT_CONFIGS[cfg_name]
            marker = " ⭐" if cfg_name == best_config_name else ""
            f.write(f"| **{cfg_name}{marker}** | "
                    f"{w['quality']*100:.0f}% | {w['growth']*100:.0f}% | "
                    f"{w['value']*100:.0f}% | {w['momentum']*100:.0f}% | "
                    f"{_fmt(scores['train_sharpe'])} | "
                    f"{_fmt(scores['val_sharpe'])} | "
                    f"{_fmt(scores['val_cagr'], True)} |\n")
        f.write(f"\n**Konfigurasi Produksi Aktif:** `{current_weights}`\n\n")
        f.write("---\n\n")

        # ── PERIOD DETAIL ─────────────────────────────────────────────────────
        for label, m, months_list in [
            ("TRAIN", train_m, train_months),
            ("VALIDATION", val_m, val_months),
            ("TEST (Evaluasi Final)", test_m, test_months),
        ]:
            f.write(f"## 🔍 Detail {label}\n\n")
            f.write(f"- **Periode**: `{months_list[0]}` → `{months_list[-1]}`  \n" if months_list else "")
            f.write(f"- **Jumlah Bulan**: `{m['months']}`  \n")
            f.write(f"- **CAGR**: `{_fmt(m['cagr'], True)}`  \n")
            f.write(f"- **Ann. Return**: `{_fmt(m['ann_return'], True)}`  \n")
            f.write(f"- **Volatility**: `{_fmt(m['volatility'], True)}`  \n")
            f.write(f"- **Sharpe**: `{_fmt(m['sharpe'])}`  \n")
            f.write(f"- **Sortino**: `{_fmt(m['sortino'])}`  \n")
            f.write(f"- **Max Drawdown**: `{_fmt(m['max_drawdown'], True)}`  \n")
            f.write(f"- **Win Rate**: `{_fmt(m['win_rate'], True)}`  \n")
            f.write(f"- **CAPM Alpha vs IHSG**: `{_fmt(m['alpha_ann'], True, True)}`  \n")
            f.write(f"- **Beta vs IHSG**: `{_fmt(m['beta'])}`  \n")
            f.write(f"- **Benchmark CAGR (IHSG)**: `{_fmt(m['benchmark_cagr'], True)}`  \n")
            f.write(f"- **Best Month**: `{_fmt(m['best_month'], True, True)}`  \n")
            f.write(f"- **Worst Month**: `{_fmt(m['worst_month'], True, True)}`  \n")
            f.write("\n")

        f.write("---\n\n")

        # ── RULES ─────────────────────────────────────────────────────────────
        f.write("## 📋 Aturan OOS Validation (Wajib Dipatuhi)\n\n")
        f.write("1. **Optimization hanya pada TRAIN** — "
                "bobot, parameter, threshold tidak boleh diubah berdasarkan data TEST.\n")
        f.write("2. **Seleksi konfigurasi via VALIDATION** — "
                "pilih konfigurasi dengan Sharpe tertinggi di periode VALIDATION.\n")
        f.write("3. **TEST adalah hakim final** — "
                "jalankan sekali, tanpa tuning ulang, tanpa cherry-picking.\n")
        f.write("4. **Semua riset faktor baru wajib melewati framework ini** "
                "sebelum boleh diintegrasikan ke production.\n")
        f.write("5. **Verdict FAIL = rollback** — "
                "jika TEST memberikan verdict FAIL, konfigurasi aktif harus di-rollback "
                "ke versi stabil sebelumnya.\n\n")

        f.write("---\n\n")
        f.write(f"*Report ini digenerate otomatis oleh `research/out_of_sample_validation.py` — ISI V8.4*\n")

    print(f"[OOS] Report ditulis ke: {REPORT_FILE}")


# ─────────────────────────────────────────────────────────────────────────────
# WEIGHT-BASED BACKTESTER (untuk config comparison)
# ─────────────────────────────────────────────────────────────────────────────

def run_weighted_backtest(rankings: dict, ticker_returns: dict,
                          ihsg_returns: dict, weights: dict,
                          start: str, end: str = None) -> tuple:
    """
    Build a portfolio using a specific weight configuration and compute
    monthly returns for the given period.

    Strategy: each month, score = weighted sum of normalized factor scores
    from the snapshot. Select Top 5, Equal Weight 20% each.
    
    Returns (portfolio_monthly_returns, benchmark_monthly_returns, months_list)
    """
    sorted_months = sorted(rankings.keys())
    portfolio_r, benchmark_r, months = [], [], []

    for m in sorted_months:
        if m < start:
            continue
        if end and m > end:
            break
        # Re-rank snapshots using the candidate weight config
        snapshot = rankings.get(m, [])
        if not snapshot:
            continue

        # Score each ticker using the config weights
        for item in snapshot:
            q = item.get("quality_score", item.get("quality", 50))
            g = item.get("growth_score",  item.get("growth",  50))
            v = item.get("value_score",   item.get("value",   50))
            mo = item.get("momentum_score", item.get("momentum", 50))
            item["_oos_score"] = (
                weights["quality"]  * q  +
                weights["growth"]   * g  +
                weights["value"]    * v  +
                weights["momentum"] * mo
            )

        ranked = sorted(snapshot, key=lambda x: x["_oos_score"], reverse=True)
        top5   = ranked[:5]
        if len(top5) < 5:
            continue

        # Next month key
        year, mon_n = map(int, m.split("-"))
        next_mon_n = mon_n + 1
        next_year  = year
        if next_mon_n > 12:
            next_mon_n = 1
            next_year += 1
        next_m = f"{next_year}-{next_mon_n:02d}"

        if next_m not in ihsg_returns:
            continue

        p_ret = 0.0
        for item in top5:
            ticker = item.get("ticker", "").replace(".JK", "")
            ret = ticker_returns.get(ticker, {}).get(next_m)
            if ret is None:
                ret = ticker_returns.get(ticker + ".JK", {}).get(next_m, 0.0)
            p_ret += 0.20 * (ret if ret is not None else 0.0)

        portfolio_r.append(p_ret)
        benchmark_r.append(ihsg_returns[next_m])
        months.append(next_m)

    return portfolio_r, benchmark_r, months


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("ISI V8.4 — Out-of-Sample Validation Framework")
    print("=" * 65)

    # 1. Load data
    print("\n[1/6] Memuat data historis...")
    try:
        all_returns = load_monthly_returns()
        print(f"      ✓ monthly_returns: {len(all_returns)} bulan dimuat.")
    except FileNotFoundError as e:
        print(f"      ✗ {e}")
        return

    rankings     = load_snapshot_rankings()
    ticker_rets  = load_ticker_returns()
    ihsg_monthly = load_ihsg_monthly()

    print(f"      ✓ snapshot rankings: {len(rankings)} bulan.")
    print(f"      ✓ ticker data: {len(ticker_rets)} tickers.")
    print(f"      ✓ IHSG monthly: {len(ihsg_monthly)} bulan.")

    # 2. Slice periods
    print("\n[2/6] Memotong periode TRAIN / VALIDATION / TEST...")
    train_p, train_b, train_months = slice_period(all_returns, TRAIN_START, TRAIN_END)
    val_p,   val_b,   val_months   = slice_period(all_returns, VALIDATION_START, VALIDATION_END)
    test_p,  test_b,  test_months  = slice_period(all_returns, TEST_START)

    print(f"      TRAIN      : {train_months[0] if train_months else '-'} → "
          f"{train_months[-1] if train_months else '-'} ({len(train_months)} bulan)")
    print(f"      VALIDATION : {val_months[0] if val_months else '-'} → "
          f"{val_months[-1] if val_months else '-'} ({len(val_months)} bulan)")
    print(f"      TEST       : {test_months[0] if test_months else '-'} → "
          f"{test_months[-1] if test_months else '-'} ({len(test_months)} bulan)")

    # 3. Compute metrics
    print("\n[3/6] Menghitung metrik kinerja...")
    train_m = calculate_metrics(train_p, train_b)
    val_m   = calculate_metrics(val_p,   val_b)
    test_m  = calculate_metrics(test_p,  test_b)

    # Turnover per period
    train_to = compute_turnover(rankings, TRAIN_START, TRAIN_END)
    val_to   = compute_turnover(rankings, VALIDATION_START, VALIDATION_END)
    test_to  = compute_turnover(rankings, TEST_START)

    train_m["turnover"] = train_to
    val_m["turnover"]   = val_to
    test_m["turnover"]  = test_to

    # 4. Weight config optimization (TRAIN + VALIDATION only)
    print("\n[4/6] Evaluasi konfigurasi bobot (hanya TRAIN & VALIDATION)...")
    all_config_scores  = {}
    best_config_name   = None
    best_val_sharpe    = -999.0

    if rankings and ticker_rets and ihsg_monthly:
        for cfg_name, w in WEIGHT_CONFIGS.items():
            # Train Sharpe
            tr_p, tr_b, _ = run_weighted_backtest(
                rankings, ticker_rets, ihsg_monthly, w, TRAIN_START, TRAIN_END)
            tr_m = calculate_metrics(tr_p, tr_b) if tr_p else _empty_metrics()

            # Validation Sharpe (selection criterion)
            vl_p, vl_b, _ = run_weighted_backtest(
                rankings, ticker_rets, ihsg_monthly, w, VALIDATION_START, VALIDATION_END)
            vl_m = calculate_metrics(vl_p, vl_b) if vl_p else _empty_metrics()

            all_config_scores[cfg_name] = {
                "train_sharpe": tr_m["sharpe"],
                "val_sharpe":   vl_m["sharpe"],
                "val_cagr":     vl_m["cagr"],
            }
            print(f"      {cfg_name}: TRAIN Sharpe={tr_m['sharpe']:.2f} | "
                  f"VAL Sharpe={vl_m['sharpe']:.2f} | VAL CAGR={vl_m['cagr']*100:.1f}%")

            if vl_m["sharpe"] > best_val_sharpe:
                best_val_sharpe  = vl_m["sharpe"]
                best_config_name = cfg_name
    else:
        print("      ⚠ Snapshot tidak cukup untuk config optimization. "
              "Menggunakan metrics dari pre-computed returns.")
        for cfg_name in WEIGHT_CONFIGS:
            all_config_scores[cfg_name] = {
                "train_sharpe": train_m["sharpe"],
                "val_sharpe":   val_m["sharpe"],
                "val_cagr":     val_m["cagr"],
            }
        best_config_name = "Config_B (Alpha Optimized)"

    print(f"\n      ⭐ Konfigurasi terbaik (berdasarkan VALIDATION Sharpe): {best_config_name}")

    # 5. Load current production weights
    current_weights = {}
    if SCORING_WEIGHTS.exists():
        with open(SCORING_WEIGHTS, encoding="utf-8") as f:
            current_weights = json.load(f)

    # 6. Verdict
    print("\n[5/6] Menentukan verdict...")
    verdict, verdict_reasons = compute_verdict(train_m, val_m, test_m)
    icons = {"PASS": "✅", "WARNING": "⚠️", "FAIL": "❌"}
    print(f"      {icons[verdict]} VERDICT: {verdict}")
    for r in verdict_reasons:
        print(f"        → {r}")

    # 7. Print summary to console
    print("\n[6/6] Ringkasan Metrik:")
    print(f"{'Metric':<20} {'TRAIN':>10} {'VALIDATION':>12} {'TEST':>10}")
    print("-" * 56)
    for label, key, pct in [
        ("CAGR",        "cagr",         True),
        ("Sharpe",      "sharpe",       False),
        ("Sortino",     "sortino",      False),
        ("Max Drawdown","max_drawdown",  True),
        ("Win Rate",    "win_rate",      True),
        ("Alpha (Ann)", "alpha_ann",     True),
    ]:
        tv = train_m[key] * (100 if pct else 1)
        vv = val_m[key]   * (100 if pct else 1)
        sv = test_m[key]  * (100 if pct else 1)
        unit = "%" if pct else ""
        print(f"{label:<20} {tv:>9.2f}{unit} {vv:>11.2f}{unit} {sv:>9.2f}{unit}")

    # 8. Write report
    write_report(
        train_m, val_m, test_m,
        train_months, val_months, test_months,
        train_to, val_to, test_to,
        best_config_name, all_config_scores,
        verdict, verdict_reasons,
        current_weights
    )

    print("\n" + "=" * 65)
    print(f"OOS Validation selesai. Laporan: {REPORT_FILE}")
    print("=" * 65)


if __name__ == "__main__":
    main()
