import yfinance as yf
import json

# baca daftar saham
with open("tickers.json") as f:
    tickers = json.load(f)

result = {}

for ticker in tickers:

    print(f"Fetching {ticker}")

    stock = yf.Ticker(ticker)

    hist = stock.history(period="5d")

    if not hist.empty:

        result[ticker] = {
            "close": float(hist["Close"].iloc[-1]),
            "volume": int(hist["Volume"].iloc[-1])
        }

# simpan hasil
with open("output/raw/prices.json", "w") as f:
    json.dump(result, f, indent=4)

print("Done!")