from pathlib import Path


def count_files(path):

    if not Path(path).exists():
        return 0

    return len(
        list(
            Path(path).glob("*")
        )
    )


def main():

    print(
        "\n=== ISI STATUS ==="
    )

    print(
        f"Historical Prices: "
        f"{count_files('output/history_prices')}"
    )

    print(
        f"Monthly Database: "
        f"{count_files('database/monthly')}"
    )

    print(
        f"Ranking Archives: "
        f"{count_files('archives/rankings')}"
    )

    print(
        f"Portfolio Archives: "
        f"{count_files('archives/portfolios')}"
    )


if __name__ == "__main__":
    main()