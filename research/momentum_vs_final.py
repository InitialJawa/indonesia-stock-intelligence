import json


def top5(path):

    with open(path, "r") as f:
        data = json.load(f)

    return data[:5]


print("\n=== FINAL TOP 5 ===\n")

for row in top5(
    "output/scores/final_ranking.json"
):
    print(row["ticker"])

print("\n=== MOMENTUM TOP 5 ===\n")

for row in top5(
    "output/scores/momentum_ranking.json"
):
    print(row["ticker"])