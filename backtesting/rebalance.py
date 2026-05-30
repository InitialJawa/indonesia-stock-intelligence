# file: backtesting/rebalance.py

import json
import pandas as pd
from pathlib import Path

RANKING_DIR = Path("archives/rankings")
PORTFOLIO_DIR = Path("archives/portfolios")
WAREHOUSE_FILE = Path("database/historical/portfolio_warehouse.csv")

TOP_N = 5

# Pastikan direktori tersedia
PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
WAREHOUSE_FILE.parent.mkdir(parents=True, exist_ok=True)

def build_portfolio(ranking_file):
    """Membaca file ranking bulanan dan membangun portofolio Top 5."""
    with open(ranking_file, "r") as f:
        ranking = json.load(f)

    # Normalisasi format jika struktur arsip lama berupa Dictionary {"ADRO.JK": 74.01}
    if isinstance(ranking, dict):
        ranking = [{"ticker": k, "final_score": v} for k, v in ranking.items()]

    # Sort descending berdasarkan final score untuk memastikan urutan benar
    ranking = sorted(ranking, key=lambda x: x.get("final_score", 0), reverse=True)

    top_stocks = ranking[:TOP_N]
    weight = round(100 / TOP_N, 2)
    portfolio = []

    for stock in top_stocks:
        portfolio.append({
            "ticker": stock.get("ticker", "UNKNOWN"),
            "weight": weight,
            "final_score": stock.get("final_score", 0)
        })

    return portfolio

def process_all_rankings():
    """Memproses semua arsip ranking untuk membuat snapshot portofolio dan Warehouse CSV."""
    ranking_files = sorted(RANKING_DIR.glob("*.json"))
    warehouse_rows = []

    if not ranking_files:
        print("WARNING: Tidak ada file di archives/rankings/ untuk diproses.")
        return

    print("--- Membangun Portfolio ---")
    
    for ranking_file in ranking_files:
        date_str = ranking_file.stem  # Mengambil string "YYYY-MM"
        portfolio = build_portfolio(ranking_file)

        # 1. Simpan Snapshot JSON (Fungsi Legacy untuk Backup)
        output_file = PORTFOLIO_DIR / ranking_file.name
        with open(output_file, "w") as f:
            json.dump(portfolio, f, indent=4)
        print(f"Backed up -> {output_file}")

        # 2. Siapkan data untuk Warehouse CSV
        for position in portfolio:
            warehouse_rows.append({
                "date": date_str,
                "ticker": position["ticker"],
                "weight": position["weight"],
                "final_score": position["final_score"]
            })

    # 3. Export ke Portfolio Warehouse
    if warehouse_rows:
        df = pd.DataFrame(warehouse_rows)
        # Urutkan berdasarkan tanggal lalu final score terbesar
        df = df.sort_values(by=["date", "final_score"], ascending=[True, False])
        df.to_csv(WAREHOUSE_FILE, index=False)
        print(f"\nSukses! {len(ranking_files)} bulan riwayat portofolio dikonsolidasi ke Warehouse.")
        print(f"Lokasi Warehouse: {WAREHOUSE_FILE}")

if __name__ == "__main__":
    process_all_rankings()