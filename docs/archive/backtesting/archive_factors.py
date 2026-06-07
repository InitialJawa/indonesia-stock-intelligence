# file: backtesting/archive_factors.py

import os
import json
import shutil
import pandas as pd
from pathlib import Path
from datetime import datetime

MONTH = datetime.today().strftime("%Y-%m")

# Folder konfigurasi
SCORES_DIR = Path("output/scores")
WAREHOUSE_DIR = Path("database/historical")
WAREHOUSE_FILE = WAREHOUSE_DIR / "factor_warehouse.csv"

FILES = {
    "quality": "quality_ranking.json",
    "value": "value_ranking.json",
    "momentum": "momentum_ranking.json",
    "growth": "growth_ranking.json",
    "final": "final_ranking_v3.json"
}

def backup_snapshots():
    """Menyalin output JSON bulanan ke folder snapshots sebagai raw backup."""
    print("--- Memulai Snapshot Backup ---")
    for factor, filename in FILES.items():
        source_file = SCORES_DIR / filename
        
        if not source_file.exists():
            print(f"WARNING: File {source_file} tidak ditemukan. Melewati backup.")
            continue

        target_dir = Path(f"snapshots/{factor}")
        target_dir.mkdir(parents=True, exist_ok=True)
        
        destination = target_dir / f"{MONTH}.json"
        shutil.copy2(source_file, destination)
        print(f"Backed up: {factor} -> {destination}")

def build_warehouse_panel():
    """Mengekstrak seluruh metrik bulanan dan menambahkannya ke Panel Data terpusat."""
    print("\n--- Membangun Historical Factor Warehouse ---")
    
    # Inisialisasi dictionary untuk menampung data gabungan
    master_data = {}

    for factor, filename in FILES.items():
        filepath = SCORES_DIR / filename
        if not filepath.exists():
            print(f"WARNING: File {filepath} tidak ditemukan. Melewati agregasi data.")
            continue
            
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Asumsi struktur JSON: list of dicts, dengan key "ticker"
        for row in data:
            ticker = row.get("ticker")
            if not ticker:
                continue
                
            if ticker not in master_data:
                master_data[ticker] = {
                    "date": MONTH,
                    "ticker": ticker,
                    "quality_score": None,
                    "value_score": None,
                    "momentum_score": None,
                    "growth_score": None,
                    "final_score": None
                }
            
            # Dinamis mengambil skor sesuai nama faktor
            if factor == "final":
                master_data[ticker]["final_score"] = row.get("final_score")
            elif factor == "momentum":
                master_data[ticker]["momentum_score"] = row.get("momentum")
            else:
                master_data[ticker][f"{factor}_score"] = row.get(f"{factor}_score")

    if not master_data:
        print("ERROR: Tidak ada data untuk digabungkan ke Warehouse.")
        return

    # Konversi ke Pandas DataFrame
    df_new = pd.DataFrame(list(master_data.values()))
    
    # Simpan atau Append ke Warehouse CSV
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    
    if WAREHOUSE_FILE.exists():
        # Load existing data
        df_existing = pd.read_csv(WAREHOUSE_FILE)
        
        # Hapus data bulan ini jika skrip dijalankan ulang (mencegah duplikasi)
        df_existing = df_existing[df_existing['date'] != MONTH]
        
        # Append data baru
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_csv(WAREHOUSE_FILE, index=False)
        print(f"Sukses! Data {MONTH} di-append ke Warehouse terpusat.")
    else:
        # Buat file baru
        df_new.to_csv(WAREHOUSE_FILE, index=False)
        print(f"Sukses! File Warehouse baru dibuat dengan data {MONTH}.")

    print(f"Lokasi Warehouse: {WAREHOUSE_FILE}")

def main():
    backup_snapshots()
    build_warehouse_panel()

if __name__ == "__main__":
    main()