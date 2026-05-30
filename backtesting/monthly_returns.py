from pathlib import Path

import pandas as pd

INPUT_DIR = Path(
    "output/history_prices"
)

OUTPUT_DIR = Path(
    "database/monthly"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def process_file(csv_file):

    df = pd.read_csv(csv_file)

    df["Date"] = pd.to_datetime(
        df["Date"]
    )

    df = df.sort_values(
        "Date"
    )

    monthly_prices = (
        df
        .set_index("Date")
        ["Close"]
        .resample("ME")
        .last()
    )

    monthly_returns = (
        monthly_prices
        .pct_change()
    )

    result = pd.DataFrame({
        "month_end_price":
            monthly_prices,
        "monthly_return":
            monthly_returns
    })

    output_file = (
        OUTPUT_DIR
        / csv_file.name
    )

    result.to_csv(
        output_file
    )

    print(
        f"Saved {csv_file.name}"
    )


def main():

    files = sorted(
        INPUT_DIR.glob("*.csv")
    )

    for file in files:

        process_file(
            file
        )


if __name__ == "__main__":
    main()