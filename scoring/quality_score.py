import json

with open("output/fundamentals.json") as f:
    data = json.load(f)

ranking = []

for ticker, info in data.items():

    score = 0

    roe = info.get("roe") or 0
    market_cap = info.get("market_cap") or 0
    net_income = info.get("net_income") or 0

    # ROE (0-30)
    score += min(roe * 100, 30)

    # Profitability (0-30)
    if net_income > 0:
        score += 30

    # Company Size (0-40)
    if market_cap > 300_000_000_000_000:
        score += 40
    elif market_cap > 100_000_000_000_000:
        score += 30
    elif market_cap > 50_000_000_000_000:
        score += 20
    else:
        score += 10

    ranking.append({
        "ticker": ticker,
        "quality_score": round(score, 2),
        "roe": roe,
        "market_cap": market_cap
    })

ranking = sorted(
    ranking,
    key=lambda x: x["quality_score"],
    reverse=True
)

with open("output/quality_ranking.json", "w") as f:
    json.dump(ranking, f, indent=4)

print("\n=== QUALITY RANKING ===\n")

for i, stock in enumerate(ranking, start=1):

    print(
        f"{i}. {stock['ticker']} | "
        f"Quality={stock['quality_score']} | "
        f"ROE={stock['roe']:.2%}"
    )