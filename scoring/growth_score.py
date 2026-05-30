import json

with open("output/growth.json") as f:
    data = json.load(f)

ranking = []

for ticker, info in data.items():

    revenue_growth = info.get("revenue_growth") or 0
    earnings_growth = info.get("earnings_growth") or 0

    score = (
        revenue_growth * 50 +
        earnings_growth * 50
    )

    ranking.append({
        "ticker": ticker,
        "growth_score": round(score, 2),
        "revenue_growth": revenue_growth,
        "earnings_growth": earnings_growth
    })

ranking = sorted(
    ranking,
    key=lambda x: x["growth_score"],
    reverse=True
)

with open("output/growth_ranking.json", "w") as f:
    json.dump(ranking, f, indent=4)

print("\n=== GROWTH RANKING ===\n")

for i, stock in enumerate(ranking, start=1):

    print(
        f"{i}. {stock['ticker']} | "
        f"Growth Score={stock['growth_score']} | "
        f"Revenue={stock['revenue_growth']:.2%} | "
        f"Earnings={stock['earnings_growth']:.2%}"
    )