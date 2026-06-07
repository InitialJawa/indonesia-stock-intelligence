from pathlib import Path
import json

RANKINGS = Path(
    "archives/rankings"
)

PORTFOLIOS = Path(
    "archives/portfolios"
)


def validate():

    ranking_files = sorted(
        RANKINGS.glob("*.json")
    )

    portfolio_files = sorted(
        PORTFOLIOS.glob("*.json")
    )

    print(
        f"Rankings: {len(ranking_files)}"
    )

    print(
        f"Portfolios: {len(portfolio_files)}"
    )

    for file in portfolio_files:

        with open(file) as f:

            portfolio = json.load(f)

        total_weight = sum(
            p["weight"]
            for p in portfolio
        )

        print(
            f"{file.name} -> {total_weight}%"
        )


if __name__ == "__main__":
    validate()