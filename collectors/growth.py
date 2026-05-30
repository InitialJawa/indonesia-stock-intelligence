# file: collectors/growth.py

import json
import concurrent.futures
from pathlib import Path
from utils.data_provider import MultiSourceProvider

UNIVERSE_FILE = Path("universe/idx30.json")
OUTPUT_FILE = Path("output/raw/growth.json")

def process_single_ticker(ticker, provider):
    print(f"Mulai fetching {ticker}...")
    data = {
        "revenue_growth": provider.get_fundamental_metric(ticker, "revenue_growth"),
        "earnings_growth": provider.get_fundamental_metric(ticker, "earnings_growth")
    }
    print(f"  ✓ Selesai: {ticker}")
    return ticker, data

def collect_growth():
    print("--- Mengumpulkan Data Growth (Multithreading ⚡) ---")
    
    with open(UNIVERSE_FILE, "r") as f:
        tickers = json.load(f)
        
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    provider = MultiSourceProvider()
    results = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_ticker = {executor.submit(process_single_ticker, t, provider): t for t in tickers}
        
        for future in concurrent.futures.as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                t, data = future.result()
                results[t] = data
            except Exception as exc:
                print(f"  [X] {ticker} menghasilkan error: {exc}")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=4)
    print(f"\nData growth tersimpan di {OUTPUT_FILE}")

if __name__ == "__main__":
    collect_growth()