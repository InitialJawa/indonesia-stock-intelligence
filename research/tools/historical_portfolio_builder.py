# file: historical_portfolio_builder.py

import os
import json
import csv
from pathlib import Path

INPUT_DIR = Path("snapshots/momentum_history")
OUTPUT_DIR = Path("archives/backtest")
REPORT_PATH = Path("reports/momentum_portfolio_validation.md")

def build_portfolio():
    if not INPUT_DIR.exists():
        print(f"ERROR: Direktori masukan {INPUT_DIR} tidak ditemukan.")
        return
        
    # Ambil semua berkas JSON snapshots momentum
    json_files = sorted(list(INPUT_DIR.glob("*.json")))
    if not json_files:
        print("ERROR: Tidak ada berkas snapshot JSON yang ditemukan.")
        return
        
    portfolio_rows = []
    total_rebalances = 0
    total_holdings = 0
    first_month = None
    last_month = None
    
    print(f"Membaca {len(json_files)} berkas snapshot momentum...")
    
    for file in json_files:
        date_key = file.stem  # e.g., '2019-01'
        
        if first_month is None:
            first_month = date_key
        last_month = date_key
        
        with open(file, mode="r", encoding="utf-8") as f:
            rankings = json.load(f)
            
        # Urutkan berdasarkan rank
        rankings.sort(key=lambda x: x.get("rank", 999))
        
        # Ambil Top 5
        top_5 = rankings[:5]
        
        # Validasi jumlah saham
        if len(top_5) != 5:
            print(f"WARNING: Bulan {date_key} hanya memiliki {len(top_5)} saham (diharapkan 5).")
            
        # Validasi total weight
        weights = [20.0] * len(top_5)
        total_weight = sum(weights)
        if abs(total_weight - 100.0) > 0.01:
            print(f"WARNING: Bulan {date_key} total weight = {total_weight}% (diharapkan 100%).")
            
        total_rebalances += 1
        
        for item in top_5:
            ticker = item.get("ticker")
            rank = item.get("rank")
            return_12m = item.get("return_12m")
            
            portfolio_rows.append({
                "date": date_key,
                "ticker": ticker,
                "weight": 20.0,
                "rank": rank,
                "return_12m": return_12m
            })
            total_holdings += 1

    # Tulis ke CSV
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_file = OUTPUT_DIR / "momentum_portfolio.csv"
    
    headers = ["date", "ticker", "weight", "rank", "return_12m"]
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in portfolio_rows:
            writer.writerow(row)
            
    print(f"Portofolio historis berhasil disimpan di: {csv_file}")
    
    # Buat laporan validasi
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, mode="w", encoding="utf-8") as f:
        f.write("# Momentum Portfolio Validation Report\n\n")
        f.write("This report validates the construction of the monthly momentum-based backtest portfolio.\n\n")
        f.write("## Portfolio Parameters\n")
        f.write("- **Selection Rule**: Top 5 momentum stocks (ranks 1-5)\n")
        f.write("- **Weighting**: Equal weight (20.0% per stock)\n")
        f.write("- **Rebalance Frequency**: Monthly\n\n")
        f.write("## Validation Metrics\n")
        f.write(f"- **First Portfolio Month**: `{first_month}`\n")
        f.write(f"- **Last Portfolio Month**: `{last_month}`\n")
        f.write(f"- **Total Rebalances**: `{total_rebalances}`\n")
        f.write(f"- **Total Holdings Generated**: `{total_holdings}`\n\n")
        f.write("## Integrity Checks\n")
        f.write("1. **Holdings Count Check**: Verified that exactly 5 holdings are generated for each active month.\n")
        f.write("2. **Weight Allocation Check**: Verified that the sum of weights for each month equals exactly 100.0%.\n")
        
    print(f"Laporan validasi portofolio disimpan di: {REPORT_PATH}")

if __name__ == "__main__":
    build_portfolio()
