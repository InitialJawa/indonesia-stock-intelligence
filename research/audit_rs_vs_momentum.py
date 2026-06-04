"""
================================================================================
AUDIT: Factor 006 - Relative Strength vs Momentum
================================================================================
Tujuan  : Mengecek apakah Relative Strength (RS) benar-benar berbeda dari
          faktor Momentum yang sudah ada, atau cuma "Momentum versi lain".

Cara    :
  1. Hitung RS = return saham - return IHSG (excess return)
  2. Ambil return_12m dari snapshot momentum yang sudah ada
  3. Hitung korelasi keduanya
  4. Kalau korelasi > 0.85 → RS redundant (buang)
  5. Kalau korelasi < 0.70 → RS layak diuji lebih lanjut

Jalankan: python research/audit_rs_vs_momentum.py
================================================================================
"""

import os
import json
import glob
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

# ── Path Setup ────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).resolve().parent.parent
PRICE_DIR    = BASE_DIR / "output" / "history_prices"
IHSG_PATH    = BASE_DIR / "benchmarks" / "ihsg.csv"
MOMENTUM_DIR = BASE_DIR / "snapshots" / "momentum_history"
OUTPUT_REPORT = BASE_DIR / "reports" / "rs_vs_momentum_audit.md"

LOOKBACK_MONTHS = [6, 12]
MIN_DATA_POINTS = 20

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def load_ihsg() -> pd.Series:
    df = pd.read_csv(IHSG_PATH)
    date_col  = next((c for c in df.columns if c.lower() in ["date","tanggal"]), df.columns[0])
    price_col = next((c for c in df.columns if c.lower() in ["close","adj close","price"]), df.columns[1])
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col).sort_index()
    print(f"  ✅ IHSG loaded: {len(df)} baris | {df.index[0].date()} → {df.index[-1].date()}")
    return df[price_col].astype(float)


def load_ticker_prices(ticker: str):
    patterns = [
        PRICE_DIR / f"{ticker}.csv",
        PRICE_DIR / f"{ticker.replace('.','_')}.csv",
    ]
    filepath = next((p for p in patterns if p.exists()), None)
    if filepath is None:
        matches = list(PRICE_DIR.glob(f"*{ticker.split('.')[0]}*"))
        filepath = matches[0] if matches else None
    if filepath is None:
        return None
    try:
        df = pd.read_csv(filepath)
        date_col  = next((c for c in df.columns if c.lower() in ["date","tanggal"]), df.columns[0])
        price_col = next((c for c in df.columns if c.lower() in ["close","adj close"]), None)
        if price_col is None:
            price_col = df.columns[4] if len(df.columns) > 4 else df.columns[1]
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col).sort_index()
        return df[price_col].astype(float)
    except Exception as e:
        return None


def compute_return(prices: pd.Series, snapshot_date: str, lookback_months: int):
    end   = pd.Timestamp(snapshot_date) + pd.offsets.MonthEnd(0)
    start = end - pd.DateOffset(months=lookback_months)
    try:
        price_end   = prices.asof(end)
        price_start = prices.asof(start)
        if pd.isna(price_end) or pd.isna(price_start) or price_start == 0:
            return None
        return (price_end / price_start) - 1.0
    except Exception:
        return None


def load_momentum_snapshots() -> dict:
    """
    Format snapshot: list of {ticker, return_12m, rank}
    Kita pakai return_12m sebagai proxy momentum score.
    """
    snapshots = {}
    files = sorted(glob.glob(str(MOMENTUM_DIR / "*.json")))

    for fpath in files:
        month = Path(fpath).stem
        try:
            with open(fpath, "r") as f:
                data = json.load(f)

            month_data = {}

            if isinstance(data, list):
                for item in data:
                    ticker = item.get("ticker") or item.get("symbol")
                    # Pakai return_12m sebagai momentum score
                    score = (
                        item.get("momentum_score")
                        or item.get("score")
                        or item.get("return_12m")
                        or item.get("return12m")
                    )
                    if ticker and score is not None:
                        month_data[ticker] = float(score)

            elif isinstance(data, dict):
                for ticker, val in data.items():
                    if isinstance(val, (int, float)):
                        month_data[ticker] = float(val)
                    elif isinstance(val, dict):
                        score = (
                            val.get("momentum_score")
                            or val.get("score")
                            or val.get("return_12m")
                        )
                        if score is not None:
                            month_data[ticker] = float(score)

            if month_data:
                snapshots[month] = month_data

        except Exception as e:
            print(f"    ⚠️  Skip {month}: {e}")

    print(f"  ✅ Momentum snapshots loaded: {len(snapshots)} bulan")
    return snapshots


def run_audit():
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}  AUDIT: Factor 006 (Relative Strength) vs Momentum{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")

    print("📂 Loading data...\n")
    ihsg      = load_ihsg()
    snapshots = load_momentum_snapshots()

    if not snapshots:
        print(f"{RED}❌ Tidak ada snapshot momentum ditemukan di {MOMENTUM_DIR}{RESET}")
        return

    all_tickers = set()
    for md in snapshots.values():
        all_tickers.update(md.keys())

    print(f"\n📊 Total ticker unik  : {len(all_tickers)}")
    print(f"📅 Periode snapshot   : {min(snapshots.keys())} → {max(snapshots.keys())}\n")

    # Cek apakah file harga tersedia
    sample_ticker = next(iter(all_tickers))
    sample_prices = load_ticker_prices(sample_ticker)
    if sample_prices is None:
        print(f"{YELLOW}⚠️  File harga tidak ditemukan untuk '{sample_ticker}'")
        print(f"   Pastikan folder output/history_prices/ berisi file CSV per ticker.")
        print(f"   Contoh nama file yang dicari: {sample_ticker}.csv atau {sample_ticker.replace('.','_')}.csv{RESET}\n")

    print("⚙️  Menghitung Relative Strength per ticker per bulan...\n")

    results       = {lb: [] for lb in LOOKBACK_MONTHS}
    processed_months = 0
    skipped_no_price = 0
    skipped_no_return = 0

    for month, momentum_data in sorted(snapshots.items()):
        if not momentum_data:
            continue

        ihsg_returns = {}
        for lb in LOOKBACK_MONTHS:
            ihsg_returns[lb] = compute_return(ihsg, month, lb)

        for ticker, momentum_score in momentum_data.items():
            prices = load_ticker_prices(ticker)
            if prices is None:
                skipped_no_price += 1
                continue

            for lb in LOOKBACK_MONTHS:
                stock_ret = compute_return(prices, month, lb)
                ihsg_ret  = ihsg_returns[lb]

                if stock_ret is None or ihsg_ret is None:
                    skipped_no_return += 1
                    continue

                rs_score = stock_ret - ihsg_ret  # excess return vs IHSG

                results[lb].append({
                    "month"         : month,
                    "ticker"        : ticker,
                    "rs_score"      : rs_score,
                    "momentum_score": momentum_score,
                })

        processed_months += 1

    print(f"  ✅ Processed       : {processed_months} bulan")
    print(f"  ⚠️  Skip no price  : {skipped_no_price} ticker-bulan")
    print(f"  ⚠️  Skip no return : {skipped_no_return} ticker-bulan\n")

    # ── Korelasi ──────────────────────────────────────────────────────────────
    print(f"{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}  HASIL KORELASI: RS vs Momentum (return_12m){RESET}")
    print(f"{BOLD}{'='*70}{RESET}\n")

    audit_results = {}
    has_result    = False

    for lb in LOOKBACK_MONTHS:
        df = pd.DataFrame(results[lb]).dropna()

        if len(df) < MIN_DATA_POINTS:
            print(f"  ⚠️  RS-{lb}M: Data tidak cukup ({len(df)} poin). Skip.\n")
            continue

        has_result = True
        pearson_r,  pearson_p  = stats.pearsonr(df["rs_score"], df["momentum_score"])
        spearman_r, spearman_p = stats.spearmanr(df["rs_score"], df["momentum_score"])

        if abs(pearson_r) > 0.85:
            verdict     = f"{RED}❌ REDUNDANT — Terlalu mirip Momentum{RESET}"
            verdict_raw = "REDUNDANT"
        elif abs(pearson_r) > 0.70:
            verdict     = f"{YELLOW}⚠️  BORDERLINE — Perlu uji alpha lebih dalam{RESET}"
            verdict_raw = "BORDERLINE"
        else:
            verdict     = f"{GREEN}✅ LAYAK DIUJI — Memberikan informasi independen{RESET}"
            verdict_raw = "INDEPENDENT"

        print(f"  📐 RS-{lb}M vs Momentum (return_12m):")
        print(f"     Data points    : {len(df)}")
        print(f"     Pearson  r     : {pearson_r:+.4f}  (p={pearson_p:.4f})")
        print(f"     Spearman r     : {spearman_r:+.4f}  (p={spearman_p:.4f})")
        print(f"     Verdict        : {verdict}\n")

        audit_results[f"RS_{lb}M"] = {
            "pearson_r" : round(pearson_r, 4),
            "spearman_r": round(spearman_r, 4),
            "n"         : len(df),
            "verdict"   : verdict_raw,
        }

    # ── Rekomendasi ───────────────────────────────────────────────────────────
    print(f"{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}  REKOMENDASI FINAL{RESET}")
    print(f"{BOLD}{'='*70}{RESET}\n")

    if not has_result:
        print(f"  {RED}{BOLD}⛔ AUDIT GAGAL — Data tidak cukup untuk dihitung.{RESET}")
        print(f"  Kemungkinan penyebab:")
        print(f"  1. File CSV harga di output/history_prices/ tidak ditemukan")
        print(f"  2. Nama file ticker tidak cocok (cek: ls output/history_prices/)")
        print(f"  3. Format tanggal di CSV harga tidak terbaca\n")
        print(f"  Jalankan dulu: python -c \"import os; print(os.listdir('output/history_prices/'))\"")
        return

    verdicts = [v["verdict"] for v in audit_results.values()]

    if all(v == "REDUNDANT" for v in verdicts):
        print(f"  {RED}{BOLD}❌ Factor 006 DITOLAK{RESET}")
        print(f"  RS terlalu kolinear dengan Momentum. Tidak menambah alpha baru.")
    elif all(v == "INDEPENDENT" for v in verdicts):
        print(f"  {GREEN}{BOLD}✅ Factor 006 LOLOS — Lanjut ke backtest alpha{RESET}")
        print(f"  RS memberikan sinyal yang berbeda dari Momentum.")
    else:
        print(f"  {YELLOW}{BOLD}⚠️  Factor 006 MIXED{RESET}")
        print(f"  Gunakan hanya period RS yang menunjukkan independensi.")

    # Simpan laporan
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_REPORT, "w") as f:
        f.write("# Audit: Factor 006 (Relative Strength) vs Momentum\n\n")
        f.write(f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## Hasil Korelasi\n\n")
        f.write("| Metric | Pearson r | Spearman r | N | Verdict |\n")
        f.write("|--------|-----------|------------|---|---------|\n")
        for key, val in audit_results.items():
            f.write(f"| {key} | {val['pearson_r']:+.4f} | {val['spearman_r']:+.4f} | {val['n']} | {val['verdict']} |\n")
        f.write("\n## Skala Interpretasi\n\n")
        f.write("- **> 0.85**: Redundant\n- **0.70–0.85**: Borderline\n- **< 0.70**: Independent\n")

    print(f"\n  📄 Laporan: {OUTPUT_REPORT}\n")
    print(f"{CYAN}{'='*70}{RESET}\n")


if __name__ == "__main__":
    run_audit()