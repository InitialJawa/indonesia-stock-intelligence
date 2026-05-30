import yfinance as yf
import pandas as pd
from pathlib import Path

BENCHMARK = "^JKSE"

OUTPUT_DIR = Path("benchmarks")
OUTPUT_DIR.mkdir(exist_ok=True)


def download_benchmark(start="2018-01-01"):
    data = yf.download(
        BENCHMARK,
        start=start,
        auto_adjust=True,
        progress=False
    )

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.reset_index()

    data["daily_return"] = data["Close"].pct_change()

    output_file = OUTPUT_DIR / "ihsg.csv"

    data.to_csv(output_file, index=False)

    print(f"Saved benchmark -> {output_file}")


if __name__ == "__main__":
    download_benchmark()