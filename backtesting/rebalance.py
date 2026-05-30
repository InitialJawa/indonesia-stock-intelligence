import json
from pathlib import Path

RANKING_DIR = Path(
    "archives/rankings"
)

PORTFOLIO_DIR = Path(
    "archives/portfolios"
)

TOP_N = 5

PORTFOLIO_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def build_portfolio(
    ranking_file
):

    with open(
        ranking_file,
        "r"
    ) as f:

        ranking = json.load(f)

    top_stocks = ranking[:TOP_N]

    weight = round(
        100 / TOP_N,
        2
    )

    portfolio = []

    for stock in top_stocks:

        portfolio.append({
            "ticker":
                stock["ticker"],
            "weight":
                weight,
            "final_score":
                stock["final_score"]
        })

    return portfolio


def process_all_rankings():

    ranking_files = sorted(
        RANKING_DIR.glob(
            "*.json"
        )
    )

    for ranking_file in ranking_files:

        portfolio = build_portfolio(
            ranking_file
        )

        output_file = (
            PORTFOLIO_DIR
            / ranking_file.name
        )

        with open(
            output_file,
            "w"
        ) as f:

            json.dump(
                portfolio,
                f,
                indent=4
            )

        print(
            f"Created -> {output_file}"
        )


if __name__ == "__main__":
    process_all_rankings()