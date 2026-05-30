import json
from pathlib import Path

import pandas as pd
import yfinance as yf

START_DATE = "2018-01-01"

OUTPUT_DIR = Path(
    "output/history_prices"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def load_universe():

    with open(
        "universe/idx30.json",
        "r"
    ) as f:
        return json.load(f)


def download_ticker(
    ticker
):

    try:

        data = yf.download(
            ticker,
            start=START_DATE,
            auto_adjust=True,
            progress=False
        )

        if data.empty:
            print(
                f"Skip {ticker}"
            )
            return

        if isinstance(
            data.columns,
            pd.MultiIndex
        ):
            data.columns = (
                data.columns
                .get_level_values(0)
            )

        data = data.reset_index()

        data.to_csv(
            OUTPUT_DIR / f"{ticker}.csv",
            index=False
        )

        print(
            f"Saved {ticker}"
        )

    except Exception as e:

        print(
            f"{ticker} -> {e}"
        )


def main():

    tickers = load_universe()

    for ticker in tickers:

        download_ticker(
            ticker
        )


if __name__ == "__main__":
    main()