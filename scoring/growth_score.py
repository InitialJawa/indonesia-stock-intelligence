import json
from utils import min_max_normalize

with open("output/raw/growth.json") as f:
    data = json.load(f)

tickers = list(data.keys())

revenue_values = []
earnings_values = []

for ticker, info in data.items():

    revenue_values.append(
        info.get("revenue_growth") or 0
    )

    earnings_values.append(
        info.get("earnings_growth") or 0
    )

revenue_scores = min_max_normalize(
    revenue_values
)

earnings_scores = min_max_normalize(
    earnings_values
)

ranking = []

for i, ticker in enumerate(tickers):

    growth_score = (
        revenue_scores[i] * 0.50 +
        earnings_scores[i] * 0.50
    )

    ranking.append({
        "ticker": ticker,
        "growth_score": round(growth_score, 2),

        "revenue_growth": revenue_values[i],
        "earnings_growth": earnings_values[i]
    })

ranking = sorted(
    ranking,
    key=lambda x: x["growth_score"],
    reverse=True
)

with open("output/scores/growth_ranking.json", "w") as f:
    json.dump(ranking, f, indent=4)

print("\n=== GROWTH RANKING ===\n")

for i, stock in enumerate(ranking, start=1):

    print(
        f"{i}. {stock['ticker']} | "
        f"Growth={stock['growth_score']}"
    )