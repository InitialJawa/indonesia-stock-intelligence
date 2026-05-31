import json
from pathlib import Path
import pandas as pd
import yfinance as yf

START_DATE = "2018-01-01"
OUTPUT_DIR_RAW = Path("output/history_prices")
OUTPUT_DIR_MONTHLY = Path("database/monthly")

# Ensure output directories exist
OUTPUT_DIR_RAW.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR_MONTHLY.mkdir(parents=True, exist_ok=True)

HISTORICAL_TICKERS = [
    "ACES.JK", "ADMR.JK", "AADI.JK", "AMRT.JK", "ARTO.JK", "BBTN.JK",
    "BSDE.JK", "BTPS.JK", "BUKA.JK", "BUMI.JK", "EMTK.JK", "ERAA.JK",
    "GGRM.JK", "HMSP.JK", "HRUM.JK", "INCO.JK", "ISAT.JK", "JPFA.JK",
    "JSMR.JK", "LPKR.JK", "LPPF.JK", "MBMA.JK", "MEDC.JK", "MNCN.JK",
    "PGEO.JK", "PTPP.JK", "PWON.JK", "SRIL.JK", "TBIG.JK", "TINS.JK",
    "TKIM.JK", "TOWR.JK", "WSBP.JK", "WSKT.JK"
]

def download_ticker(ticker):
    try:
        print(f"Downloading raw daily prices for {ticker} from {START_DATE}...")
        data = yf.download(ticker, start=START_DATE, auto_adjust=True, progress=False)
        if data.empty:
            print(f"WARNING: No data found for {ticker}")
            return False
            
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        data = data.reset_index()
        # Standardise the date column name
        if "index" in data.columns:
            data = data.rename(columns={"index": "Date"})
        elif "Date" not in data.columns and "Date" in [c.capitalize() for c in data.columns]:
            data = data.rename(columns={c: "Date" for c in data.columns if c.lower() == "date"})
        elif "Date" not in data.columns:
            data = data.rename(columns={data.columns[0]: "Date"})
            
        raw_csv = OUTPUT_DIR_RAW / f"{ticker}.csv"
        data.to_csv(raw_csv, index=False)
        print(f"Saved raw data for {ticker} to {raw_csv}")
        return True
    except Exception as e:
        print(f"ERROR downloading {ticker}: {e}")
        return False

def process_to_monthly(ticker):
    raw_csv = OUTPUT_DIR_RAW / f"{ticker}.csv"
    if not raw_csv.exists():
        print(f"ERROR: Raw CSV {raw_csv} does not exist. Skipping resampling.")
        return False
        
    try:
        df = pd.read_csv(raw_csv)
        if df.empty or "Date" not in df.columns or "Close" not in df.columns:
            print(f"ERROR: Invalid CSV format for {ticker}")
            return False
            
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")
        
        # Resample to month end
        monthly_prices = df.set_index("Date")["Close"].resample("ME").last()
        monthly_returns = monthly_prices.pct_change()
        
        result = pd.DataFrame({
            "month_end_price": monthly_prices,
            "monthly_return": monthly_returns
        })
        
        # Drop rows where both price and return are NaN (e.g. before IPO)
        result = result.dropna(how='all')
        
        monthly_csv = OUTPUT_DIR_MONTHLY / f"{ticker}.csv"
        result.to_csv(monthly_csv)
        print(f"Saved monthly resampled returns for {ticker} to {monthly_csv}")
        return True
    except Exception as e:
        print(f"ERROR processing {ticker} to monthly: {e}")
        return False

def main():
    print(f"Starting historical data download and preprocessing for {len(HISTORICAL_TICKERS)} tickers...")
    success_count = 0
    for ticker in HISTORICAL_TICKERS:
        if download_ticker(ticker):
            if process_to_monthly(ticker):
                success_count += 1
    print(f"Finished. Successfully downloaded and processed {success_count}/{len(HISTORICAL_TICKERS)} tickers.")

if __name__ == "__main__":
    main()
