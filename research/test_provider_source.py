import sys
import os

# Ensure project root is in python path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from utils.data_provider import MultiSourceProvider

def get_metric_source(provider, ticker, metric):
    val = provider.get_fundamental_metric(ticker, metric)
    
    # Trace source using the provider caches
    source = "YFINANCE"
    if provider.fmp_api_key:
        ratios_map = {
            "pe_ratio": "priceEarningsRatio",
            "roe": "returnOnEquity",
            "debt_to_equity": "debtEquityRatio",
            "pb_ratio": "priceToBookRatio",
            "dividend_yield": "dividendYield",
            "net_margin": "netProfitMargin",
            "operating_margin": "operatingProfitMargin"
        }
        growth_map = {
            "revenue_growth": "revenueGrowth",
            "earnings_growth": "netIncomeGrowth"
        }
        
        if metric in ratios_map:
            if ticker in provider._fmp_ratios_cache:
                fmp_val = provider._fmp_ratios_cache[ticker].get(ratios_map[metric])
                if fmp_val is not None:
                    source = "FMP"
        elif metric in growth_map:
            if ticker in provider._fmp_growth_cache:
                fmp_val = provider._fmp_growth_cache[ticker].get(growth_map[metric])
                if fmp_val is not None:
                    source = "FMP"
                    
    return val, source

def main():
    provider = MultiSourceProvider()
    ticker = "BBRI.JK"
    
    metrics = {
        "ROE": "roe",
        "PE": "pe_ratio",
        "PB": "pb_ratio",
        "Revenue Growth": "revenue_growth",
        "Earnings Growth": "earnings_growth"
    }
    
    print("==================================================")
    print(f" TESTING DATA SOURCE FOR TICKER: {ticker}")
    print("==================================================")
    
    for label, metric_name in metrics.items():
        val, source = get_metric_source(provider, ticker, metric_name)
        print(f"{label:<15}: {val} (SOURCE = {source})")
    print("==================================================")

if __name__ == "__main__":
    main()
