# file: historical_momentum_builder.py

import os
import csv
import json
from pathlib import Path

INPUT_DIR = Path("database/monthly")
OUTPUT_DIR = Path("snapshots/momentum_history")

def load_all_ticker_data():
    ticker_data = {}
    csv_files = list(INPUT_DIR.glob("*.csv"))
    
    print(f"Mengunduh data dari {len(csv_files)} berkas CSV di {INPUT_DIR}...")
    
    for file in csv_files:
        ticker = file.stem
        ticker_data[ticker] = {}
        
        with open(file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                date_str = row.get("Date", "").strip()
                price_str = row.get("month_end_price", "").strip()
                
                if not date_str or not price_str:
                    continue
                
                # Ubah YYYY-MM-DD ke YYYY-MM
                month_key = date_str[:7]
                try:
                    price = float(price_str)
                    ticker_data[ticker][month_key] = price
                except ValueError:
                    continue
                    
    return ticker_data

def generate_month_list():
    months = []
    # Dari 2019-01 sampai 2026-05
    for year in range(2019, 2027):
        end_month = 5 if year == 2026 else 12
        for month in range(1, end_month + 1):
            months.append(f"{year}-{month:02d}")
    return months

def load_universe_for_month(month_key):
    univ_dir = Path("database/historical_universe")
    univ_files = sorted(list(univ_dir.glob("*.json")))
    
    selected_file = None
    for file in univ_files:
        file_month = file.stem
        if file_month <= month_key:
            selected_file = file
        else:
            break
            
    if selected_file is None and univ_files:
        selected_file = univ_files[0]
        
    if selected_file:
        with open(selected_file, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def calculate_momentum_for_month(month_key, ticker_data, metadata=None):
    month_momentum = []
    
    # Load universe for this month
    active_universe = load_universe_for_month(month_key)
    
    year, month = map(int, month_key.split("-"))
    # Hitung base month (12 bulan lalu)
    base_year = year - 1
    base_month = month
    base_month_key = f"{base_year}-{base_month:02d}"
    
    for ticker, history in ticker_data.items():
        # Check if the ticker is active in this month's universe
        if ticker not in active_universe:
            continue
            
        if metadata and ticker in metadata:
            listing_month = metadata[ticker][:7]
            if month_key < listing_month:
                continue
                
        if month_key not in history:
            continue
            
        P_t = history[month_key]
        
        # Cari base price
        if base_month_key in history:
            P_base = history[base_month_key]
            if P_base > 0:
                return_12m = (P_t / P_base) - 1.0
            else:
                return_12m = 0.0
        else:
            # Fallback ke data terawal jika belum mencapai 12 bulan
            sorted_months = sorted(history.keys())
            oldest_month = sorted_months[0]
            
            if month_key == oldest_month:
                return_12m = 0.0
            else:
                P_base = history[oldest_month]
                if P_base > 0:
                    return_12m = (P_t / P_base) - 1.0
                else:
                    return_12m = 0.0
                    
        month_momentum.append({
            "ticker": ticker,
            "return_12m": round(return_12m, 4)
        })
        
    # Urutkan berdasarkan return_12m secara descending
    month_momentum.sort(key=lambda x: x["return_12m"], reverse=True)
    
    # Tambahkan rank
    for rank, item in enumerate(month_momentum, start=1):
        item["rank"] = rank
        
    return month_momentum

def main():
    ticker_data = load_all_ticker_data()
    if not ticker_data:
        print("ERROR: Tidak ada data ticker yang ditemukan.")
        return
        
    # Muat metadata tanggal listing
    metadata = {}
    metadata_file = Path("database/historical/ticker_metadata.csv")
    if metadata_file.exists():
        with open(metadata_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                metadata[row["ticker"]] = row["listing_date"]
                
    months = generate_month_list()
    
    # Bersihkan file JSON lama di direktori output
    if OUTPUT_DIR.exists():
        for f in OUTPUT_DIR.glob("*.json"):
            try:
                f.unlink()
            except OSError:
                pass
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    successful_months = 0
    
    for month in months:
        rankings = calculate_momentum_for_month(month, ticker_data, metadata)
        
        if not rankings:
            continue
            
        output_file = OUTPUT_DIR / f"{month}.json"
        with open(output_file, mode="w", encoding="utf-8") as f:
            json.dump(rankings, f, indent=4)
            
        successful_months += 1
        
    print(f"\nProses Rekonstruksi Selesai!")
    print(f"Jumlah bulan yang berhasil direkonstruksi: {successful_months} bulan")
    print(f"Berkas peringkat disimpan di: {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
