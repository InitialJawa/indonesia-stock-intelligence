import json
import datetime
from pathlib import Path
import yfinance as yf
import pandas as pd
import math

def safe_float(val, default=0.0):
    """Convert value to float safely, handling None, NaN, Inf, and errors.
    Returns default if conversion fails.
    """
    try:
        if val is None:
            return default
        f_val = float(val)
        if math.isnan(f_val) or math.isinf(f_val):
            return default
        return f_val
    except (ValueError, TypeError):
        return default

# IDX30 tickers with .JK suffix (derived from existing TICKER_INFO in generate_dashboard)
TICKERS = [
    'ADRO.JK', 'ESSA.JK', 'MAPI.JK', 'PTBA.JK', 'AKRA.JK', 'CPIN.JK',
    'ANTM.JK', 'EXCL.JK', 'BBRI.JK', 'BMRI.JK', 'BRPT.JK', 'BBNI.JK',
    'INDF.JK', 'PGAS.JK', 'MDKA.JK', 'ITMG.JK', 'TLKM.JK', 'ASII.JK',
    'INTP.JK', 'ICBP.JK', 'BBCA.JK', 'UNTR.JK', 'MIKA.JK', 'GOTO.JK',
    'SMGR.JK', 'SIDO.JK', 'TPIA.JK', 'KLBF.JK', 'AMMN.JK', 'HEAL.JK'
]

def fetch_fundamentals(ticker):
    tk = yf.Ticker(ticker)
    info = tk.info
    # Pull basic fundamentals, using safe .get with defaults and numeric fallbacks
    pe = safe_float(info.get('trailingPE'))
    pb = safe_float(info.get('priceToBook'))
    roe = safe_float(info.get('returnOnEquity'))
    der = safe_float(info.get('debtToEquity'))
    net_margin = safe_float(info.get('netMargins'))
    operating_margin = safe_float(info.get('operatingMargins'))
    free_cash_flow = safe_float(info.get('freeCashflow'))
    # YoY growth calculations using annual financials if available
    growth = {'revenue_growth': 0, 'earnings_growth': 0}
    try:
        fin = tk.financials  # columns are years
        if fin.shape[1] >= 2:
            # Assume last two columns are most recent years
            rev = fin.loc['Total Revenue']
            net = fin.loc['Net Income']
            rev_recent, rev_prev = rev.iloc[0], rev.iloc[1]
            net_recent, net_prev = net.iloc[0], net.iloc[1]
            if rev_prev != 0:
                growth['revenue_growth'] = (rev_recent - rev_prev) / rev_prev
            if net_prev != 0:
                growth['earnings_growth'] = (net_recent - net_prev) / net_prev
    except Exception:
        pass
    return {
        'pe': pe,
        'pb': pb,
        'roe': roe,
        'der': der,
        'net_margin': net_margin,
        'operating_margin': operating_margin,
        'free_cash_flow': free_cash_flow,
        **growth
    }
def fetch_momentum(ticker):
    # 6‑month relative strength vs. its own price, with robust NaN handling and fallbacks
    hist = yf.download(ticker, period='6mo', interval='1d', progress=False)
    if hist.empty or 'Close' not in hist:
        return 0
    close = hist['Close'].dropna()
    if close.empty:
        return 0
    latest = close.iloc[-1]
    past = close.iloc[0]
    try:
        result = (latest - past) / past * 100
        return float(result)
    except Exception:
        return 0
def compute_scores(fund, momentum):
    # Quality: combine ROE and Net Margin (weights 0.6 / 0.4)
    roe = safe_float(fund.get('roe'))
    net_margin = safe_float(fund.get('net_margin'))
    q = roe * 100 * 0.6 + net_margin * 100 * 0.4

    # Growth: combine revenue and earnings YoY (equal weight)
    rev_growth = safe_float(fund.get('revenue_growth'))
    earn_growth = safe_float(fund.get('earnings_growth'))
    g = (rev_growth + earn_growth) / 2 * 100

    # Value: inverse of P/E and P/B (simple average)
    pe = safe_float(fund.get('pe'))
    pb = safe_float(fund.get('pb'))
    v = ((1 / pe) + (1 / pb)) / 2 * 100 if pe and pb else 0

    # Momentum: use provided value or fallback 0
    m = safe_float(momentum) if momentum is not None else 0

    return {
        'quality': round(q, 2),
        'growth': round(g, 2),
        'value': round(v, 2),
        'momentum': round(m, 2)
    }

def main():
    results = []
    for ticker in TICKERS:
        fund = fetch_fundamentals(ticker)
        momentum = fetch_momentum(ticker)
        scores = compute_scores(fund, momentum)
        entry = {
            'ticker': ticker,
            'fundamentals': fund,
            **scores
        }
        results.append(entry)
        print(f"Processed {ticker}")
    # Final sanitization: ensure all score fields are numeric floats, no nulls
    for ent in results:
        for key in ['quality', 'growth', 'value', 'momentum']:
            ent[key] = safe_float(ent.get(key), 0)
    out_path = Path('dashboard/data.json')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"Data written to {out_path.resolve()}")

if __name__ == '__main__':
    main()
