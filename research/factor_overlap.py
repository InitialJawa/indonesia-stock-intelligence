import json


def top5(path):

    with open(path, "r") as f:
        data = json.load(f)

    return {
        row["ticker"]
        for row in data[:5]
    }


quality = top5(
    "output/scores/quality_ranking.json"
)

growth = top5(
    "output/scores/growth_ranking.json"
)

value = top5(
    "output/scores/value_ranking.json"
)

momentum = top5(
    "output/scores/momentum_ranking.json"
)

final = top5(
    "output/scores/final_ranking.json"
)

print("\n=== OVERLAP ===\n")

print(
    "QUALITY ∩ FINAL :",
    len(quality & final)
)

print(
    "GROWTH ∩ FINAL  :",
    len(growth & final)
)

print(
    "VALUE ∩ FINAL   :",
    len(value & final)
)

print(
    "MOMENTUM ∩ FINAL:",
    len(momentum & final)
)

print("\nFINAL TOP5")

for ticker in sorted(final):
    print(ticker)