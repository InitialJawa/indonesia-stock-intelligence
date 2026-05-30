import json
from utils import min_max_normalize

with open("output/fundamentals.json") as f:
    data = json.load(f)

tickers = list(data.keys())

roe_values = []
net_margin_values = []
op_margin_values = []
debt_values = []
fcf_values = []

for ticker, info in data.items():

    roe_values.append(info.get("roe") or 0)
    net_margin_values.append(info.get("net_margin") or 0)
    op_margin_values.append(info.get("operating_margin") or 0)

    debt = info.get("debt_to_equity")

    if debt is None:
        debt = 0

    debt_values.append(debt)

    fcf = info.get("free_cash_flow")

    if fcf is None:
        fcf = 0

    fcf_values.append(fcf)

roe_scores = min_max_normalize(roe_values)

net_margin_scores = min_max_normalize(net_margin_values)

op_margin_scores = min_max_normalize(op_margin_values)

debt_scores = min_max_normalize(debt_values)

fcf_scores = min_max_normalize(fcf_values)

ranking = []

for i, ticker in enumerate(tickers):

    quality_score = (
        roe_scores[i] * 0.25 +
        net_margin_scores[i] * 0.20 +
        op_margin_scores[i] * 0.15 +
        (100 - debt_scores[i]) * 0.20 +
        fcf_scores[i] * 0.20
    )

    ranking.append({
        "ticker": ticker,
        "quality_score": round(quality_score, 2),

        "roe": roe_values[i],
        "net_margin": net_margin_values[i],
        "operating_margin": op_margin_values[i],
        "debt_to_equity": debt_values[i],
        "free_cash_flow": fcf_values[i]
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
        f"Quality={stock['quality_score']}"
    )