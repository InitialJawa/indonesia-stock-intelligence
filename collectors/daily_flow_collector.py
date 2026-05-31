# file: collectors/daily_flow_collector.py

import yfinance as yf
import pandas as pd

def check_volume_shock(ticker: str) -> dict:
    """
    Mengambil data harga dan volume 30 hari perdagangan terakhir.
    Mengevaluasi apakah terjadi Volume Shock (> 2x MA-20 Volume) hari ini.
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1mo")
        
        if len(df) < 21:
            return {"ticker": ticker, "status": "INSUFFICIENT_DATA"}
            
        # Kalkulasi Moving Average 20 Hari untuk Volume
        df['MA20_Volume'] = df['Volume'].rolling(window=20).mean()
        
        # Ambil data hari terakhir (penutupan terbaru)
        latest_data = df.iloc[-1]
        prev_data = df.iloc[-2]
        
        current_volume = latest_data['Volume']
        ma20_volume = latest_data['MA20_Volume']
        current_close = latest_data['Close']
        prev_close = prev_data['Close']
        
        # Kalkulasi persentase perubahan harga
        price_change_pct = ((current_close - prev_close) / prev_close) * 100
        
        # Logika Volume Shock: Volume hari ini > 2x rata-rata 20 hari
        is_volume_shock = current_volume > (2 * ma20_volume)
        
        return {
            "ticker": ticker,
            "status": "OK",
            "date": df.index[-1].strftime('%Y-%m-%d'),
            "price_change_pct": round(price_change_pct, 2),
            "current_volume": int(current_volume),
            "ma20_volume": int(ma20_volume),
            "is_volume_shock": is_volume_shock
        }
        
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return {"ticker": ticker, "status": "ERROR"}

def scan_portfolio_risks():
    """
    Memindai sampel saham IDX30 secara real-time.
    """
    print("Memulai pemindaian Volume Shock pada saham...")
    
    # Sampel uji coba: Bank, Komoditas, dan Teknologi
    test_tickers = ["BBCA.JK", "ADRO.JK", "GOTO.JK"]
    
    results = []
    for ticker in test_tickers:
        print(f"Mengunduh data harian {ticker}...")
        res = check_volume_shock(ticker)
        if res["status"] == "OK":
            results.append(res)
            
    print("\n=== HASIL PEMINDAIAN VOLUME HARIAN ===")
    for r in results:
        shock_tag = "⚠️ SHOCK TERDETEKSI" if r["is_volume_shock"] else "Aman"
        print(
            f"{r['ticker']} | "
            f"Perubahan: {r['price_change_pct']}% | "
            f"Vol: {r['current_volume']} (Rata-rata: {r['ma20_volume']}) | "
            f"Status: {shock_tag}"
        )

if __name__ == "__main__":
    scan_portfolio_risks()
    