# file: collectors/fundamentals.py

import json
import datetime
import concurrent.futures
from pathlib import Path
from utils.data_provider import YahooFinanceProvider

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
        "dividend_yield": provider.get_fundamental_metric(ticker, "dividend_yield"),
        "roa": provider.get_fundamental_metric(ticker, "roa"),
        "market_cap": provider.get_fundamental_metric(ticker, "market_cap")
    }
    print(f"  ✓ Selesai: {ticker}")
    return ticker, data

def collect_fundamentals():
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print("--- Mengumpulkan Data Fundamental (Multithreading) ---")
    
    with open(UNIVERSE_FILE, "r") as f:
        tickers = json.load(f)
        
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    provider = YahooFinanceProvider()
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

    # === DATA QUALITY RULE - PBV (V1) ===
    # Jika pb_ratio > 100 atau < 0 → INVALID_PBV
    #   1) jika PE dan ROE tersedia → PBV = PE × ROE
    #   2) jika PE atau ROE tidak tersedia → PBV = null
    #   3) catat semua flag ke data_quality_flags.json
    FLAGS_FILE = Path("data/state/data_quality_flags.json")
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    flags = {}
    fix_count = 0
    unfix_count = 0
    for ticker, data in sorted(results.items()):
        pb = data.get("pb_ratio")
        pe = data.get("pe_ratio")
        roe = data.get("roe")
        if pb is None or not (pb > 100 or pb < 0):
            continue
        flag = {"field": "pb_ratio", "original_value": pb}
        if pe is not None and roe is not None and pe > 0 and roe > 0:
            computed_pb = round(pe * roe, 4)
            print(f"  [PBV RULE] {ticker}: INVALID ({pb:.2f}) -> FIXED ({computed_pb:.2f}) via PE*ROE")
            data["pb_ratio"] = computed_pb
            flag["corrected_value"] = computed_pb
            flag["status"] = "FIXED"
            flag["method"] = "PE*ROE"
            fix_count += 1
        else:
            print(f"  [PBV RULE] {ticker}: INVALID ({pb:.2f}) -> NULLIFIED (PE={pe}, ROE={roe})")
            data["pb_ratio"] = None
            flag["corrected_value"] = None
            flag["status"] = "UNFIXABLE"
            flag["reason"] = f"PE={pe}, ROE={roe}"
            unfix_count += 1
        flags[ticker] = flag
    if flags:
        FLAGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(FLAGS_FILE, "w") as f:
            json.dump({"rule": "DATA_QUALITY_RULE_PBV_V1", "date": date_str, "flags": flags}, f, indent=2)
        print(f"  PBV flags: {fix_count} fixed, {unfix_count} unfixable -> {FLAGS_FILE}")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=4)
    print(f"\nData fundamental tersimpan di {OUTPUT_FILE}")

if __name__ == "__main__":
    collect_fundamentals()