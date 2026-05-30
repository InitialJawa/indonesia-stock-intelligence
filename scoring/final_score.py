import json
from datetime import date

# =========================
# Load Config
# =========================

with open("config/scoring_weights.json") as f:
    weights = json.load(f)

# =========================
# Load Rankings
# =========================

with open("output/scores/value_ranking.json") as f:
    value_data = json.load(f)

with open("output/scores/growth_ranking.json") as f:
    growth_data = json.load(f)

with open("output/scores/quality_ranking.json") as f:
    quality_data = json.load(f)

# =========================
# Build Dictionaries
# =========================

value_scores = {
    stock["ticker"]: stock["value_score"]
    for stock in value_data
}

growth_scores = {
    stock["ticker"]: stock["growth_score"]
    for stock in growth_data
}

quality_scores = {
    stock["ticker"]: stock["quality_score"]
    for stock in quality_data
}

# =========================
# Final Ranking
# =========================

final_ranking = []

for ticker in value_scores.keys():

    value = value_scores.get(ticker, 0)
    growth = growth_scores.get(ticker, 0)
    quality = quality_scores.get(ticker, 0)

    final_score = (
        quality * weights["final"]["quality"]
        + growth * weights["final"]["growth"]
        + value * weights["final"]["value"]
    )

    final_ranking.append({
        "ticker": ticker,
        "value": round(value, 2),
        "growth": round(growth, 2),
        "quality": round(quality, 2),
        "final_score": round(final_score, 2)
    })

# =========================
# Sort
# =========================

final_ranking.sort(
    key=lambda x: x["final_score"],
    reverse=True
)

# =========================
# Save Final Ranking
# =========================

with open(
    "output/scores/final_ranking.json",
    "w"
) as f:
    json.dump(
        final_ranking,
        f,
        indent=4
    )

# =========================
# Save History Snapshot
# =========================

today = str(date.today())

with open(
    f"output/history/{today}.json",
    "w"
) as f:
    json.dump(
        final_ranking,
        f,
        indent=4
    )

# =========================
# Display Result
# =========================

print("\n=== FINAL RANKING ===\n")

for i, stock in enumerate(
    final_ranking,
    start=1
):

    print(
        f"{i}. {stock['ticker']} | "
        f"Final={stock['final_score']} | "
        f"Value={stock['value']} | "
        f"Growth={stock['growth']} | "
        f"Quality={stock['quality']}"
    )

print(
    f"\nSaved: output/scores/final_ranking.json"
)

print(
    f"Saved: output/history/{today}.json"
)