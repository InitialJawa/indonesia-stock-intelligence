import json, datetime, sys
import yfinance as yf

OUT = 'dashboard/data/live_market.json'

def wib_now():
    return (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S WIB')

def safe_pct(a, b):
    if a and b and b != 0:
        return round((a / b - 1) * 100, 2)
    return 0

ts = wib_now()

data = {
    "ihsg": {"price": 0, "change_pct": 0, "timestamp": ts},
    "usdidr": {"price": 0, "change_pct": 0, "timestamp": ts}
}

try:
    tk = yf.Ticker("^JKSE")
    h = tk.history(period="5d")
    if h is not None and len(h) > 1:
        c = h['Close']
        data["ihsg"]["price"] = round(float(c.iloc[-1]), 2)
        data["ihsg"]["change_pct"] = safe_pct(c.iloc[-1], c.iloc[-2])
        print(f"IHSG: {data['ihsg']['price']} ({data['ihsg']['change_pct']:+.2f}%)")
    else:
        print(f"IHSG: insufficient data ({len(h) if h is not None else 0} rows)")
except Exception as e:
    print(f"IHSG error: {e}")

try:
    tk = yf.Ticker("USDIDR=X")
    h = tk.history(period="5d")
    if h is not None and len(h) > 1:
        c = h['Close']
        data["usdidr"]["price"] = round(float(c.iloc[-1]), 2)
        data["usdidr"]["change_pct"] = safe_pct(c.iloc[-1], c.iloc[-2])
        print(f"USDIDR: {data['usdidr']['price']} ({data['usdidr']['change_pct']:+.2f}%)")
    else:
        print(f"USDIDR: insufficient data ({len(h) if h is not None else 0} rows)")
except Exception as e:
    print(f"USDIDR error: {e}")

with open(OUT, 'w') as f:
    json.dump(data, f, indent=2)

print(f"written to {OUT}")
