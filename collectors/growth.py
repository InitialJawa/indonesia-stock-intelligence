import json
import yfinance as yf

with open("tickers.json") as f:
    tickers = json.load(f)

result = {}

for ticker in tickers:

    print(f"Fetching {ticker}")

    try:

        stock = yf.Ticker(ticker)

        info = stock.info

        result[ticker] = {
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth")
        }

    except Exception as e:

        print(f"Error {ticker}: {e}")

with open("output/raw/growth.json", "w") as f:
    json.dump(result, f, indent=4)

print("Growth data saved!")