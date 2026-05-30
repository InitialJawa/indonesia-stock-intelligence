import json


def top5(path):

    with open(path, "r") as f:
        data = json.load(f)

    return [
        row["ticker"]
        for row in data[:5]
    ]


v2 = top5(
    "output/scores/final_ranking.json"
)

v3 = top5(
    "output/scores/final_ranking_v3.json"
)

print("\n=== V2 ===\n")

for t in v2:
    print(t)

print("\n=== V3 ===\n")

for t in v3:
    print(t)

print(
    "\nOverlap:",
    len(set(v2) & set(v3))
)