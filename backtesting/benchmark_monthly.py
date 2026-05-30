from pathlib import Path

import pandas as pd

INPUT_FILE = Path(
    "benchmarks/ihsg.csv"
)

OUTPUT_FILE = Path(
    "benchmarks/ihsg_monthly.csv"
)


def main():

    df = pd.read_csv(
        INPUT_FILE
    )

    df["Date"] = pd.to_datetime(
        df["Date"]
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

    result.to_csv(
        OUTPUT_FILE
    )

    print(
        f"Saved -> {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
    