import yfinance as yf
import json

with open("tickers.json") as f:
    tickers = json.load(f)

result = {}

for ticker in tickers:

    print(f"Fetching {ticker}")

    stock = yf.Ticker(ticker)

    info = stock.info

    result[ticker] = {
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "pb_ratio": info.get("priceToBook"),
        "roe": info.get("returnOnEquity"),
        "revenue": info.get("totalRevenue"),
        "net_income": info.get("netIncomeToCommon")
    }

with open("output/fundamentals.json", "w") as f:
    json.dump(result, f, indent=4)

print("Done!")