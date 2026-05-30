import json
import os

import yfinance as yf

from utils.config_loader import load_universe


tickers = load_universe()

result = {}

for ticker in tickers:

    print(f"Fetching {ticker}...")

    try:

        stock = yf.Ticker(ticker)
        info = stock.info

        result[ticker] = {

            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),

            "roe": info.get("returnOnEquity"),
            "net_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),

            "revenue": info.get("totalRevenue"),
            "net_income": info.get("netIncomeToCommon"),

            "debt_to_equity": info.get("debtToEquity"),

            "dividend_yield": info.get("dividendYield"),

            "free_cash_flow": info.get("freeCashflow")

        }

        print(f"✓ {ticker}")

    except Exception as e:

        print(f"✗ {ticker} -> {e}")

        result[ticker] = {
            "error": str(e)
        }

os.makedirs(
    "output/raw",
    exist_ok=True
)

with open(
    "output/raw/fundamentals.json",
    "w"
) as f:

    json.dump(
        result,
        f,
        indent=4
    )

print("\nDone!")