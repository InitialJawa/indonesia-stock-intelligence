# file: scoring/value_score.py

import json
from utils import percentile_normalize

def main():
    with open("output/raw/fundamentals.json") as f:
        data = json.load(f)

    tickers = list(data.keys())

    pe_values = []
    pb_values = []
    dividend_values = []

    for ticker, info in data.items():
        pe = info.get("pe_ratio") or 0
        pb = info.get("pb_ratio") or 0
        dividend = info.get("dividend_yield") or 0

        pe_values.append(pe)
        pb_values.append(pb)
        dividend_values.append(dividend)

    # Menggunakan Percentile Normalization
    pe_scores = percentile_normalize(pe_values)
    pb_scores = percentile_normalize(pb_values)

    # Inversi skor: mahal -> score rendah, murah -> score tinggi
    pe_scores = [100 - s for s in pe_scores]
    pb_scores = [100 - s for s in pb_scores]

    # Dividend tinggi = bagus
    dividend_scores = percentile_normalize(dividend_values)

    ranking = []

    for i, ticker in enumerate(tickers):
        value_score = (
            pe_scores[i] * 0.40 +
            pb_scores[i] * 0.30 +
            dividend_scores[i] * 0.30
        )

        ranking.append({
            "ticker": ticker,
            "value_score": round(value_score, 2),
            "pe_ratio": pe_values[i],
            "pb_ratio": pb_values[i],
            "dividend_yield": dividend_values[i]
        })

    ranking = sorted(
        ranking,
        key=lambda x: x["value_score"],
        reverse=True
    )

    with open("output/scores/value_ranking.json", "w") as f:
        json.dump(ranking, f, indent=4)

    print("\n=== VALUE RANKING (PERCENTILE NORMALIZED) ===\n")
    for i, stock in enumerate(ranking, start=1):
        print(
            f"{i}. {stock['ticker']} | "
            f"Value={stock['value_score']}"
        )

if __name__ == "__main__":
    main()