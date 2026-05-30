import json


TOP_N = 5


with open(
    "output/scores/final_ranking_v3.json",
    "r"
) as f:

    ranking = json.load(f)

portfolio = []

weight = round(
    100 / TOP_N,
    2
)

for stock in ranking[:TOP_N]:

    portfolio.append({
        "ticker":
            stock["ticker"],
        "weight":
            weight,
        "score":
            stock["final_score"]
    })

with open(
    "portfolios/current_portfolio_v3.json",
    "w"
) as f:

    json.dump(
        portfolio,
        f,
        indent=4
    )

print(
    "Saved -> portfolios/current_portfolio_v3.json"
)