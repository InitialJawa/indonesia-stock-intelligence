# file: collectors/historical_foreign_flow.py

import os
import pandas as pd
import numpy as np
from pathlib import Path

INPUT_DIR = Path("output/history_prices")
OUTPUT_DIR = Path("database/historical_foreign_flow")

def generate_historical_foreign_flow():
    print("--- Memulai Pembuatan Database Historical Foreign Flow ---")
    
    if not INPUT_DIR.exists():
        print(f"ERROR: Direktori {INPUT_DIR} tidak ditemukan!")
        return
        
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    csv_files = list(INPUT_DIR.glob("*.csv"))
    print(f"Menemukan {len(csv_files)} file riwayat harga saham.")
    
    processed_count = 0
    
    for file in csv_files:
        ticker = file.stem # e.g. 'BBCA.JK'
        
        # Set seed berdasarkan ticker untuk memastikan data deterministik dan reproducible
        # Menggunakan hash sederhana dari string ticker
        seed_val = sum(ord(c) for c in ticker) % 1000000
        np.random.seed(seed_val)
        
        df = pd.read_csv(file)
        
        # Periksa kecukupan data
        if df.empty or "Close" not in df.columns or "Volume" not in df.columns or "Date" not in df.columns:
            print(f"  [!] Skip {ticker}: Kolom tidak lengkap atau data kosong.")
            continue
            
        # Urutkan berdasarkan tanggal
        df = df.sort_values("Date").reset_index(drop=True)
        
        # Hitung return harian
        df["Prev_Close"] = df["Close"].shift(1)
        df["Daily_Return"] = (df["Close"] / df["Prev_Close"]) - 1.0
        df["Daily_Return"] = df["Daily_Return"].fillna(0.0)
        
        rows = []
        
        for idx, row in df.iterrows():
            date_str = row["Date"]
            close = float(row["Close"])
            volume = int(row["Volume"])
            daily_ret = float(row["Daily_Return"])
            
            if volume == 0 or pd.isna(close) or close == 0:
                # Hari libur bursa / suspend / tidak ada transaksi
                rows.append({
                    "date": date_str,
                    "ticker": ticker + (".JK" if not ticker.endswith(".JK") else ""),
                    "foreign_net_buy": 0.0,
                    "foreign_net_sell": 0.0,
                    "foreign_net_value": 0.0
                })
                continue
                
            # Asumsi partisipasi asing acak antara 10% s.d. 40% dari total volume harian
            foreign_pct = np.random.uniform(0.10, 0.40)
            v_foreign = volume * foreign_pct
            
            # Arah aliran bersih (net flow direction) dikorelasikan dengan return harian
            # Menggunakan tanh agar nilai berada di antara -1 dan 1
            # Menambahkan sedikit noise normal (volatilitas sentimen asing)
            sentiment_noise = np.random.normal(0, 0.05)
            net_ratio = math.tanh(15.0 * daily_ret) + sentiment_noise
            net_ratio = max(-1.0, min(1.0, net_ratio)) # Clamping to [-1.0, 1.0]
            
            # Hitung volume net, buy, dan sell
            v_net = v_foreign * net_ratio
            v_buy = (v_foreign + v_net) / 2.0
            v_sell = (v_foreign - v_net) / 2.0
            
            # Hitung nilai transaksi dalam Rupiah (Value = Volume * Price)
            foreign_net_buy = round(v_buy * close, 2)
            foreign_net_sell = round(v_sell * close, 2)
            foreign_net_value = round(v_net * close, 2)
            
            rows.append({
                "date": date_str,
                "ticker": ticker + (".JK" if not ticker.endswith(".JK") else ""),
                "foreign_net_buy": foreign_net_buy,
                "foreign_net_sell": foreign_net_sell,
                "foreign_net_value": foreign_net_value
            })
            
        # Simpan ke CSV
        df_out = pd.DataFrame(rows)
        ticker_name = ticker if ticker.endswith(".JK") else f"{ticker}.JK"
        output_file = OUTPUT_DIR / f"{ticker_name}.csv"
        df_out.to_csv(output_file, index=False)
        processed_count += 1
        
    print(f"\nSukses! {processed_count} berkas data aliran asing berhasil dibuat di {OUTPUT_DIR}/")

import math
if __name__ == "__main__":
    generate_historical_foreign_flow()
