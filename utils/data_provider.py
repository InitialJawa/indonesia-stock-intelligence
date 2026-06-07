# file: utils/data_provider.py

import yfinance as yf

class YahooFinanceProvider:
    def __init__(self):
        # Sistem Caching Memori untuk mencegah Rate-Limiting & Spam Request
        self._yf_cache = {}

    def get_fundamental_metric(self, ticker, metric_name):
        """Mengambil metrik fundamental menggunakan Yahoo Finance."""
        try:
            return self._fetch_from_yfinance(ticker, metric_name)
        except Exception:
            return None

    def _fetch_from_yfinance(self, ticker, metric_name):
        yf_metric_map = {
            "pe_ratio": "trailingPE",
            "roe": "returnOnEquity",
            "debt_to_equity": "debtToEquity",
            "pb_ratio": "priceToBook",
            "dividend_yield": "dividendYield",
            "net_margin": "profitMargins",
            "operating_margin": "operatingMargins",
            "free_cash_flow": "freeCashflow",
            "revenue_growth": "revenueGrowth",
            "earnings_growth": "earningsGrowth",
            "roa": "returnOnAssets",
            "market_cap": "marketCap"
        }

        if metric_name not in yf_metric_map:
            return None
            
        # Cache YFinance (Hanya tarik .info 1 kali per ticker)
        if ticker not in self._yf_cache:
            stock = yf.Ticker(ticker)
            self._yf_cache[ticker] = stock.info
            
        val = self._yf_cache[ticker].get(yf_metric_map[metric_name])
        
        if val is not None and metric_name == "debt_to_equity":
            val = val / 100.0
            
        return val