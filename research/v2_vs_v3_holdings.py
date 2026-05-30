import json


with open(
    "portfolios/current_portfolio.json"
) as f:

    v2 = json.load(f)

with open(
    "portfolios/current_portfolio_v3.json"
) as f:

    v3 = json.load(f)

v2_set = {
    x["ticker"]
    for x in v2
}

v3_set = {
    x["ticker"]
    for x in v3
}

print(
    "\nRemoved:\n"
)

for x in sorted(
    v2_set - v3_set
):
    print(x)

print(
    "\nAdded:\n"
)

for x in sorted(
    v3_set - v2_set
):
    print(x)