from pathlib import Path
import pandas as pd

PRICE_DIR = Path(
    "output/history_prices"
)


def audit_prices():

    files = sorted(
        PRICE_DIR.glob("*.csv")
    )

    print(
        f"Files: {len(files)}"
    )

    for file in files:

        df = pd.read_csv(file)

        rows = len(df)

        first_date = (
            df["Date"].iloc[0]
        )

        last_date = (
            df["Date"].iloc[-1]
        )

        print(
            f"{file.stem}"
            f" | rows={rows}"
            f" | {first_date}"
            f" -> {last_date}"
        )


if __name__ == "__main__":
    audit_prices()