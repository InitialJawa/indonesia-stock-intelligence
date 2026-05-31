import json
from pathlib import Path

import yfinance as yf

from utils.config_loader import load_universe

OUTPUT_FILE = Path("output/raw/prices.json")


def collect_prices():
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

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=4)

    print(f"\nData harga tersimpan di {OUTPUT_FILE}")


if __name__ == "__main__":
    collect_prices()