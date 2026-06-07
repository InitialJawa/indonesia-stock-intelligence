# file: backtesting/merge_foreign_flow.py

import os
import pandas as pd
from pathlib import Path

HIST_DIR = Path("database/historical_foreign_flow")
MONTHLY_DIR = Path("database/monthly")

def merge_foreign_flow_monthly():
    print("--- Memulai Integrasi Aliran Asing Bulanan ---")
    
    if not HIST_DIR.exists():
        print(f"ERROR: Direktori {HIST_DIR} tidak ditemukan!")
        return
        
    if not MONTHLY_DIR.exists():
        print(f"ERROR: Direktori {MONTHLY_DIR} tidak ditemukan!")
        return
        
    hist_files = list(HIST_DIR.glob("*.csv"))
    print(f"Menemukan {len(hist_files)} file data aliran asing harian.")
    
    merged_count = 0
    
    for file in hist_files:
        ticker = file.stem # e.g. 'BBCA.JK'
        
        # Load daily foreign flow
        df_hist = pd.read_csv(file)
        if df_hist.empty or "date" not in df_hist.columns or "foreign_net_value" not in df_hist.columns:
            continue
            
        # Group by YYYY-MM and calculate the sum of foreign net value
        df_hist["month_key"] = df_hist["date"].str[:7]
        monthly_flow = df_hist.groupby("month_key")["foreign_net_value"].sum().to_dict()
        
        # Load monthly ticker CSV
        monthly_file = MONTHLY_DIR / f"{ticker}.csv"
        if not monthly_file.exists():
            print(f"  [!] Warning: File bulanan {monthly_file} tidak ditemukan. Melewati.")
            continue
            
        df_monthly = pd.read_csv(monthly_file)
        if df_monthly.empty or "Date" not in df_monthly.columns:
            continue
            
        # Map aggregated monthly foreign net value
        df_monthly["month_key"] = df_monthly["Date"].str[:7]
        df_monthly["net_foreign_buy"] = df_monthly["month_key"].map(monthly_flow).fillna(0.0)
        
        # Drop temporary column
        df_monthly = df_monthly.drop(columns=["month_key"])
        
        # Save back to CSV
        df_monthly.to_csv(monthly_file, index=False)
        merged_count += 1
        
    print(f"\nSukses! Data aliran asing bulanan berhasil disuntikkan ke {merged_count} file monthly.")

if __name__ == "__main__":
    merge_foreign_flow_monthly()
