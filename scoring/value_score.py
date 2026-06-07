# file: scoring/value_score.py

import json
import os
from scoring.utils import percentile_normalize

def main():
    # 1. Load Sector Rules untuk deteksi Value Trap Komoditas
    try:
        with open("config/sector_rules.json") as f:
            sector_rules = json.load(f)
            commodities = sector_rules.get("commodity_cyclical", [])
    except FileNotFoundError:
        commodities = []

    with open("output/raw/fundamentals.json") as f:
        data = json.load(f)

    tickers = list(data.keys())

    pe_values = []
    pb_values = []
    dividend_values = []
    ticker_is_commodity = []

    for ticker, info in data.items():
        is_commodity = ticker in commodities
        ticker_is_commodity.append(is_commodity)

        # Jika info bernilai None, fallback ke 0
        pe = info.get("pe_ratio") or 0
        pb_raw = info.get("pb_ratio")
        # PBV null = missing data (UNFIXABLE) -> sentinel ekstrem -> skor 0 setelah inversi
        pb = 1e10 if pb_raw is None else pb_raw
        dividend = info.get("dividend_yield") or 0

        pe_values.append(pe)
        pb_values.append(pb)
        dividend_values.append(dividend)

    # 2. Percentile Normalization
    pe_scores = percentile_normalize(pe_values)
    pb_scores = percentile_normalize(pb_values)
    dividend_scores = percentile_normalize(dividend_values)

    # Inversi skor: valuasi mahal -> score rendah, murah -> score tinggi
    pe_scores = [100 - s for s in pe_scores]
    pb_scores = [100 - s for s in pb_scores]

    ranking = []

    for i, ticker in enumerate(tickers):
        is_commodity = ticker_is_commodity[i]

        # RULE: The Value Trap Discount (Anomali Komoditas)
        final_pe_score = pe_scores[i]
        if is_commodity:
            final_pe_score = final_pe_score * 0.5 

        value_score = (
            final_pe_score * 0.40 +
            pb_scores[i] * 0.30 +
            dividend_scores[i] * 0.30
        )

        ranking.append({
            "ticker": ticker,
            "value_score": round(value_score, 2),
            "pe_ratio": pe_values[i],
            "pb_ratio": pb_values[i],
            "dividend_yield": dividend_values[i],
            "is_commodity": is_commodity
        })

    ranking = sorted(
        ranking,
        key=lambda x: x["value_score"],
        reverse=True
    )

    os.makedirs("output/scores", exist_ok=True)
    with open("output/scores/value_ranking.json", "w") as f:
        json.dump(ranking, f, indent=4)

    print("\n=== VALUE RANKING (PERCENTILE NORMALIZED + COMMODITY TRAP FIX) ===\n")
    for i, stock in enumerate(ranking, start=1):
        trap_tag = "[COMMODITY - PE DISCOUNTED]" if stock["is_commodity"] else ""
        print(
            f"{i}. {stock['ticker']} | "
            f"Value={stock['value_score']} {trap_tag}"
        )

if __name__ == "__main__":
    main()