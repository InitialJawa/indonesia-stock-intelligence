# file: collectors/fundamentals.py

import json
import concurrent.futures
from pathlib import Path
from utils.data_provider import MultiSourceProvider

UNIVERSE_FILE = Path("universe/idx30.json")
OUTPUT_FILE = Path("output/raw/fundamentals.json")

def process_single_ticker(ticker, provider):
    """Fungsi pekerja untuk 1 thread"""
    print(f"Mulai fetching {ticker}...")
    data = {
        "roe": provider.get_fundamental_metric(ticker, "roe"),
        "net_margin": provider.get_fundamental_metric(ticker, "net_margin"),
        "operating_margin": provider.get_fundamental_metric(ticker, "operating_margin"),
        "debt_to_equity": provider.get_fundamental_metric(ticker, "debt_to_equity"),
        "free_cash_flow": provider.get_fundamental_metric(ticker, "free_cash_flow"),
        "pe_ratio": provider.get_fundamental_metric(ticker, "pe_ratio"),
        "pb_ratio": provider.get_fundamental_metric(ticker, "pb_ratio"),
        "dividend_yield": provider.get_fundamental_metric(ticker, "dividend_yield")
    }
    print(f"  ✓ Selesai: {ticker}")
    return ticker, data

def collect_fundamentals():
    print("--- Mengumpulkan Data Fundamental (Multithreading ⚡) ---")
    
    with open(UNIVERSE_FILE, "r") as f:
        tickers = json.load(f)
        
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    provider = MultiSourceProvider()
    results = {}

    # Membuka 5 jalur eksekusi paralel (Jangan terlalu banyak agar tidak diblokir API)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Submit semua tugas ke executor
        future_to_ticker = {executor.submit(process_single_ticker, t, provider): t for t in tickers}
        
        # Kumpulkan hasil saat setiap thread selesai
        for future in concurrent.futures.as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                t, data = future.result()
                results[t] = data
            except Exception as exc:
                print(f"  [X] {ticker} menghasilkan error: {exc}")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=4)
    print(f"\nData fundamental tersimpan di {OUTPUT_FILE}")

if __name__ == "__main__":
    collect_fundamentals()