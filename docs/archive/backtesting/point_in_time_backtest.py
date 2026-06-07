# file: backtesting/point_in_time_backtest.py

import pandas as pd
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta

PORTFOLIO_FILE = Path("database/historical/portfolio_warehouse.csv")
IHSG_FILE = Path("benchmarks/ihsg_monthly.csv")
STOCK_DB_DIR = Path("database/monthly")
REPORT_FILE = Path("reports/comparison.csv")

def get_next_month(date_str):
    """Menambahkan 1 bulan ke format 'YYYY-MM' untuk simulasi Point-In-Time."""
    date_obj = datetime.strptime(date_str, "%Y-%m")
    next_month = date_obj + relativedelta(months=1)
    return next_month.strftime("%Y-%m")

def run_backtest():
    print("--- Memulai Point-In-Time Backtest ---")

    if not PORTFOLIO_FILE.exists():
        print(f"ERROR: {PORTFOLIO_FILE} tidak ditemukan.")
        return

    # 1. Load Portfolio History
    df_portfolios = pd.read_csv(PORTFOLIO_FILE)
    if df_portfolios.empty:
        print("ERROR: Portfolio Warehouse kosong.")
        return
        
    # Ambil daftar unik bulan di mana portofolio dibentuk (Bulan T)
    formation_months = sorted(df_portfolios['date'].unique())
    
    # 2. Load Benchmark (IHSG)
    df_ihsg = pd.read_csv(IHSG_FILE)
    # Konversi tanggal (misal 2018-01-31) menjadi YYYY-MM
    df_ihsg['YYYY-MM'] = pd.to_datetime(df_ihsg['Date']).dt.strftime("%Y-%m")
    df_ihsg = df_ihsg.set_index('YYYY-MM')

    results = []

    for formation_date in formation_months:
        # Bulan di mana return akan dihitung (T+1)
        target_month = get_next_month(formation_date)
        print(f"\nSimulasi: Portofolio dibentuk {formation_date} -> Evaluasi Return {target_month}")
        
        # Ambil saham-saham pilihan di bulan T
        holdings = df_portfolios[df_portfolios['date'] == formation_date]
        
        portfolio_return = 0.0
        valid_stocks = 0

        # 3. Hitung Imbal Hasil Gabungan
        for _, row in holdings.iterrows():
            ticker = row['ticker']
            weight = row['weight'] / 100.0  # Konversi 20.0 menjadi 0.20
            
            stock_file = STOCK_DB_DIR / f"{ticker}.csv"
            if not stock_file.exists():
                print(f"  [!] Missing Data: {ticker}.csv tidak ditemukan.")
                continue
                
            df_stock = pd.read_csv(stock_file)
            df_stock['YYYY-MM'] = pd.to_datetime(df_stock['Date']).dt.strftime("%Y-%m")
            
            # Cari return saham tersebut di bulan T+1
            stock_data = df_stock[df_stock['YYYY-MM'] == target_month]
            
            if not stock_data.empty:
                stock_ret = stock_data['monthly_return'].values[0]
                # Tangani kemungkinan NaN
                if pd.isna(stock_ret):
                    stock_ret = 0.0
                
                portfolio_return += stock_ret * weight
                valid_stocks += 1
            else:
                print(f"  [!] Missing Return: {ticker} tidak memiliki data untuk {target_month}")
                
        # Jika tidak ada data harga sama sekali di bulan target, lewati
        if valid_stocks == 0:
            print(f"  [LEWATI] Tidak ada data harga yang valid untuk evaluasi {target_month}")
            continue
            
        # 4. Ambil Imbal Hasil Benchmark
        ihsg_return = 0.0
        if target_month in df_ihsg.index:
            ihsg_return = df_ihsg.loc[target_month, 'monthly_return']
            if pd.isna(ihsg_return):
                ihsg_return = 0.0
                
        # Kalkulasi Alpha
        alpha = portfolio_return - ihsg_return
        
        results.append({
            "evaluation_month": target_month,
            "formation_month": formation_date,
            "portfolio_return": round(portfolio_return, 4),
            "benchmark_return": round(ihsg_return, 4),
            "alpha": round(alpha, 4)
        })
        
        print(f"  Hasil: Portofolio={portfolio_return:.2%}, IHSG={ihsg_return:.2%}, Alpha={alpha:.2%}")

    # 5. Export ke Laporan Final
    if results:
        df_results = pd.DataFrame(results)
        df_results.to_csv(REPORT_FILE, index=False)
        print(f"\nSukses! Simulasi Walk-Forward selesai. Laporan disimpan di: {REPORT_FILE}")
    else:
        print("\nGagal. Tidak ada data simulasi yang dapat dihitung.")

if __name__ == "__main__":
    run_backtest()