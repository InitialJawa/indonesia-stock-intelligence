from pathlib import Path

import pandas as pd

PORTFOLIO_FILE = Path(
    "reports/portfolio_returns.csv"
)

BENCHMARK_FILE = Path(
    "benchmarks/ihsg_monthly.csv"
)

OUTPUT_FILE = Path(
    "reports/comparison.csv"
)


def main():

    portfolio = pd.read_csv(
        PORTFOLIO_FILE
    )

    benchmark = pd.read_csv(
        BENCHMARK_FILE
    )

    benchmark = benchmark[
        [
            "Date",
            "monthly_return"
        ]
    ]

    benchmark = benchmark.rename(
        columns={
            "monthly_return":
            "benchmark_return"
        }
    )

    merged = portfolio.merge(
        benchmark,
        on="Date",
        how="inner"
    )

    merged[
        "portfolio_cumulative"
    ] = (
        1 +
        merged[
            "portfolio_return"
        ]
    ).cumprod()

    merged[
        "benchmark_cumulative"
    ] = (
        1 +
        merged[
            "benchmark_return"
        ]
    ).cumprod()

    merged.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"Saved -> {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()