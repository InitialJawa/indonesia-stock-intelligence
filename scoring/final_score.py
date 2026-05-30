import json

with open("output/ranking.json") as f:
    value_data = json.load(f)

with open("output/growth_ranking.json") as f:
    growth_data = json.load(f)

with open("output/quality_ranking.json") as f:
    quality_data = json.load(f)

value_scores = {}
growth_scores = {}
quality_scores = {}

for stock in value_data:
    value_scores[stock["ticker"]] = stock["score"]

for stock in growth_data:
    growth_scores[stock["ticker"]] = stock["growth_score"]

for stock in quality_data:
    quality_scores[stock["ticker"]] = stock["quality_score"]


def normalize(score, min_score, max_score):

    if max_score == min_score:
        return 50

    return (
        (score - min_score)
        /
        (max_score - min_score)
    ) * 100


value_min = min(value_scores.values())
value_max = max(value_scores.values())

growth_min = min(growth_scores.values())
growth_max = max(growth_scores.values())

quality_min = min(quality_scores.values())
quality_max = max(quality_scores.values())

final_ranking = []

for ticker in value_scores:

    value_norm = normalize(
        value_scores[ticker],
        value_min,
        value_max
    )

    growth_norm = normalize(
        growth_scores[ticker],
        growth_min,
        growth_max
    )

    quality_norm = normalize(
        quality_scores[ticker],
        quality_min,
        quality_max
    )

    final_score = (
        value_norm * 0.20 +
        growth_norm * 0.30 +
        quality_norm * 0.50
    )

    final_ranking.append({
        "ticker": ticker,
        "value": round(value_norm, 2),
        "growth": round(growth_norm, 2),
        "quality": round(quality_norm, 2),
        "final_score": round(final_score, 2)
    })

final_ranking = sorted(
    final_ranking,
    key=lambda x: x["final_score"],
    reverse=True
)

with open("output/final_ranking.json", "w") as f:
    json.dump(final_ranking, f, indent=4)

print("\n=== FINAL RANKING ===\n")

for i, stock in enumerate(final_ranking, start=1):

    print(
        f"{i}. {stock['ticker']} | "
        f"Final={stock['final_score']}"
    )