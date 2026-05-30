import json

import yfinance as yf

from utils.config_loader import load_universe


tickers = load_universe()

result = {}

for ticker in tickers:

    print(f"Fetching {ticker}")

    try:

        stock = yf.Ticker(ticker)

        hist = stock.history(period="5d")

        if not hist.empty:

            result[ticker] = {
                "close": float(hist["Close"].iloc[-1]),
                "volume": int(hist["Volume"].iloc[-1])
            }

            print(f"✓ {ticker}")

        else:

            print(f"✗ {ticker} -> no data")

    except Exception as e:

        print(f"✗ {ticker} -> {e}")

with open(
    "output/raw/prices.json",
    "w"
) as f:

    json.dump(
        result,
        f,
        indent=4
    )

print("Done!")