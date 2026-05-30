import pandas as pd

from metrics import calculate_metrics


def main():

    df = pd.read_csv(
        "reports/comparison.csv"
    )

    portfolio_metrics = calculate_metrics(
        df["portfolio_return"].dropna()
    )

    benchmark_metrics = calculate_metrics(
        df["benchmark_return"].dropna()
    )

    print("\n=== PORTFOLIO ===")

    for k, v in portfolio_metrics.items():
        print(f"{k}: {v}")

    print("\n=== IHSG ===")

    for k, v in benchmark_metrics.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()