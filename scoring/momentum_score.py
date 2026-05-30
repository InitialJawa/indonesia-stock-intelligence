import json
from pathlib import Path

import pandas as pd

INPUT_DIR = Path(
    "database/monthly"
)

OUTPUT_FILE = Path(
    "output/scores/momentum_ranking.json"
)


def minmax(series):

    min_v = series.min()
    max_v = series.max()

    if max_v == min_v:
        return [50] * len(series)

    return (
        (series - min_v)
        / (max_v - min_v)
        * 100
    )


def calculate_momentum():

    rows = []

    files = sorted(
        INPUT_DIR.glob("*.csv")
    )

    for file in files:

        ticker = (
            file.stem
        )

        df = pd.read_csv(
            file
        )

        df = df.dropna()

        if len(df) < 13:
            continue

        latest = (
            len(df) - 1
        )

        return_6m = (
            df.iloc[latest][
                "month_end_price"
            ]
            /
            df.iloc[
                latest - 6
            ][
                "month_end_price"
            ]
            - 1
        )

        return_12m = (
            df.iloc[latest][
                "month_end_price"
            ]
            /
            df.iloc[
                latest - 12
            ][
                "month_end_price"
            ]
            - 1
        )

        rows.append({
            "ticker":
                ticker,
            "return_6m":
                return_6m,
            "return_12m":
                return_12m
        })

    result = pd.DataFrame(
        rows
    )

    result[
        "score_6m"
    ] = minmax(
        result[
            "return_6m"
        ]
    )

    result[
        "score_12m"
    ] = minmax(
        result[
            "return_12m"
        ]
    )

    result[
        "momentum"
    ] = (
        result[
            "score_6m"
        ] * 0.5
        +
        result[
            "score_12m"
        ] * 0.5
    )

    result = result.sort_values(
        "momentum",
        ascending=False
    )

    result = result.round(2)

    output = (
        result[
            [
                "ticker",
                "momentum",
                "return_6m",
                "return_12m"
            ]
        ]
        .to_dict(
            orient="records"
        )
    )

    with open(
        OUTPUT_FILE,
        "w"
    ) as f:

        json.dump(
            output,
            f,
            indent=4
        )

    print(
        f"Saved -> {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    calculate_momentum()