import json
from pathlib import Path

import pandas as pd

MONTHLY_DIR = Path(
    "database/monthly"
)

PORTFOLIO_FILE = Path(
    "portfolios/current_portfolio.json"
)

OUTPUT_FILE = Path(
    "reports/portfolio_returns.csv"
)

TOP_N = 5


def load_portfolio():

    with open(
        PORTFOLIO_FILE,
        "r"
    ) as f:

        return json.load(f)


def load_returns(
    ticker
):

    file = (
        MONTHLY_DIR
        / f"{ticker}.csv"
    )

    df = pd.read_csv(file)

    df = df[
        ["Date", "monthly_return"]
    ]

    df = df.rename(
        columns={
            "monthly_return":
            ticker
        }
    )

    return df


def build_portfolio_returns():

    portfolio = (
        load_portfolio()
    )

    merged = None

    for stock in portfolio:

        ticker = stock["ticker"]

        df = load_returns(
            ticker
        )

        if merged is None:

            merged = df

        else:

            merged = merged.merge(
                df,
                on="Date",
                how="inner"
            )

    tickers = [
        p["ticker"]
        for p in portfolio
    ]

    merged[
        "portfolio_return"
    ] = (
        merged[tickers]
        .mean(axis=1)
    )

    return merged[
        [
            "Date",
            "portfolio_return"
        ]
    ]


def save_portfolio_returns():

    Path("reports").mkdir(
        exist_ok=True
    )

    result = (
        build_portfolio_returns()
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"Saved -> {OUTPUT_FILE}"
    )


if __name__ == "__main__":

    save_portfolio_returns()