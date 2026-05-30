# file: utils/data_provider.py

import yfinance as yf
import requests
import os
import time

class MultiSourceProvider:
    def __init__(self):
        self.fmp_api_key = os.environ.get("FMP_API_KEY")
        if not self.fmp_api_key:
            print("  [INFO] FMP_API_KEY tidak ditemukan. Fallback murni ke YFinance.")
            
        # Sistem Caching Memori untuk mencegah Rate-Limiting & Spam Request
        self._fmp_ratios_cache = {}
        self._fmp_growth_cache = {}
        self._yf_cache = {}

    def get_fundamental_metric(self, ticker, metric_name):
        """Mengambil metrik dengan prioritas FMP -> Fallback YFinance menggunakan cache."""
        if self.fmp_api_key:
            try:
                val = self._fetch_from_fmp(ticker, metric_name)
                if val is not None:
                    return val
            except Exception:
                pass # Silently fallback jika FMP gagal/limit habis

        try:
            return self._fetch_from_yfinance(ticker, metric_name)
        except Exception:
            return None

    def _fetch_from_fmp(self, ticker, metric_name):
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

        # Tarik data Ratios (Hanya 1 request per Ticker)
        if metric_name in ratios_map:
            if ticker not in self._fmp_ratios_cache:
                url = f"https://financialmodelingprep.com/api/v3/ratios/{ticker}?limit=1&apikey={self.fmp_api_key}"
                res = requests.get(url, timeout=5)
                if res.status_code == 200 and res.json():
                    self._fmp_ratios_cache[ticker] = res.json()[0]
                else:
                    self._fmp_ratios_cache[ticker] = {}
            return self._fmp_ratios_cache[ticker].get(ratios_map[metric_name])

        # Tarik data Growth (Hanya 1 request per Ticker)
        elif metric_name in growth_map:
            if ticker not in self._fmp_growth_cache:
                url = f"https://financialmodelingprep.com/api/v3/financial-growth/{ticker}?limit=1&apikey={self.fmp_api_key}"
                res = requests.get(url, timeout=5)
                if res.status_code == 200 and res.json():
                    self._fmp_growth_cache[ticker] = res.json()[0]
                else:
                    self._fmp_growth_cache[ticker] = {}
            return self._fmp_growth_cache[ticker].get(growth_map[metric_name])
                
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
            "earnings_growth": "earningsGrowth"
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