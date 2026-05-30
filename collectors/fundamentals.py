import yfinance as yf
import json
import os

# =========================
# Load Tickers
# =========================

with open("tickers.json", "r") as f:
    tickers = json.load(f)

result = {}

# =========================
# Fetch Fundamentals
# =========================

for ticker in tickers:

    print(f"Fetching {ticker}...")

    try:

        stock = yf.Ticker(ticker)
        info = stock.info

        result[ticker] = {

            # =====================
            # Valuation
            # =====================

            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),

            # =====================
            # Profitability
            # =====================

            "roe": info.get("returnOnEquity"),
            "net_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),

            # =====================
            # Business Size
            # =====================

            "revenue": info.get("totalRevenue"),
            "net_income": info.get("netIncomeToCommon"),

            # =====================
            # Financial Health
            # =====================

            "debt_to_equity": info.get("debtToEquity"),

            # =====================
            # Shareholder Return
            # =====================

            "dividend_yield": info.get("dividendYield"),

            # =====================
            # Cash Flow
            # =====================

            "free_cash_flow": info.get("freeCashflow")

        }

        print(f"✓ {ticker}")

    except Exception as e:

        print(f"✗ {ticker} -> {e}")

        result[ticker] = {
            "error": str(e)
        }

# =========================
# Save Output
# =========================

os.makedirs("output", exist_ok=True)

with open("output/fundamentals.json", "w") as f:
    json.dump(result, f, indent=4)

print("\nDone!")
print("Saved: output/fundamentals.json")