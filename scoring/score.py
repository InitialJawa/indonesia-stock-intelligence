import json

with open("output/prices.json") as f:
    data = json.load(f)

ranking = []

for ticker, info in data.items():

    close_price = info["close"]

    ranking.append({
        "ticker": ticker,
        "price": close_price
    })

ranking = sorted(
    ranking,
    key=lambda x: x["price"],
    reverse=True
)

print("\n=== RANKING ===\n")

for i, stock in enumerate(ranking, start=1):
    print(
        f"{i}. {stock['ticker']} "
        f"(Rp {stock['price']:,.0f})"
    )