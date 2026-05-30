import json
from pathlib import Path

TOP_N = 5


def load_latest_ranking():
    ranking_file = Path(
        "output/scores/final_ranking.json"
    )

    with open(ranking_file, "r") as f:
        return json.load(f)


def build_equal_weight_portfolio():
    ranking = load_latest_ranking()

    top_stocks = ranking[:TOP_N]

    weight = round(100 / TOP_N, 2)

    portfolio = []

    for stock in top_stocks:
        portfolio.append({
            "ticker": stock["ticker"],
            "weight": weight,
            "final_score": stock["final_score"]
        })

    return portfolio


def save_portfolio():
    portfolio = build_equal_weight_portfolio()

    Path("portfolios").mkdir(
        exist_ok=True
    )

    output_file = Path(
        "portfolios/current_portfolio.json"
    )

    with open(output_file, "w") as f:
        json.dump(
            portfolio,
            f,
            indent=4
        )

    print(
        f"Portfolio saved -> {output_file}"
    )


if __name__ == "__main__":
    save_portfolio()