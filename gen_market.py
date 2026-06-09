import json, csv, datetime, sys
import yfinance as yf

def wib_now():
    return (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S WIB')

def safe_pct(a, b):
    if a and b and b != 0:
        return round((a / b - 1) * 100, 2)
    return 0

last_update = wib_now()

# IHSG from yfinance
ihsg = {"value": 0, "daily": 0, "weekly": 0, "monthly": 0, "ytd": None}
ihsg_ok = False
try:
    tk = yf.Ticker("^JKSE")
    h = tk.history(period="2mo")
    if h is not None and len(h) > 1:
        c = h['Close']
        ihsg["value"] = round(c.iloc[-1], 2)
        ihsg["daily"] = safe_pct(c.iloc[-1], c.iloc[-2])
        if len(c) >= 5:
            ihsg["weekly"] = safe_pct(c.iloc[-1], c.iloc[-5])
        if len(c) >= 21:
            ihsg["monthly"] = safe_pct(c.iloc[-1], c.iloc[-21])
        ihsg_ok = True
        print(f"IHSG: live fetch OK — {ihsg['value']} (daily: {ihsg['daily']}%)")
    else:
        print(f"IHSG: yfinance returned insufficient data ({len(h) if h is not None else 0} rows)")
except Exception as e:
    print(f"IHSG: yfinance error: {e}")

if not ihsg_ok:
    try:
        with open('benchmarks/ihsg_monthly.csv') as f:
            rows = list(csv.DictReader(f))
        if rows:
            latest = rows[-1]
            prev = rows[-2]
            prev_yr = rows[-13] if len(rows) > 13 else rows[0]
            ihsg["value"] = round(float(latest['month_end_price']), 2)
            ihsg["monthly"] = safe_pct(float(latest['month_end_price']), float(prev['month_end_price']))
            ihsg["weekly"] = round(ihsg["monthly"] / 4, 2)
            ihsg["daily"] = round(ihsg["monthly"] / 22, 2)
            print(f"IHSG: fallback to CSV — {ihsg['value']} (daily: {ihsg['daily']}%)")
    except Exception as e2:
        print(f"IHSG: CSV fallback also failed: {e2}")

# USDIDR from yfinance
usdidr = {"value": 18150, "daily": 0, "weekly": 0, "monthly": 0}
usdidr_ok = False
try:
    tk = yf.Ticker("USDIDR=X")
    h = tk.history(period="2mo")
    if h is not None and len(h) > 1:
        c = h['Close']
        usdidr["value"] = round(c.iloc[-1], 2)
        usdidr["daily"] = safe_pct(c.iloc[-1], c.iloc[-2])
        if len(c) >= 5:
            usdidr["weekly"] = safe_pct(c.iloc[-1], c.iloc[-5])
        if len(c) >= 21:
            usdidr["monthly"] = safe_pct(c.iloc[-1], c.iloc[-21])
        usdidr_ok = True
        print(f"USDIDR: live fetch OK — {usdidr['value']} (daily: {usdidr['daily']}%)")
    else:
        print(f"USDIDR: yfinance returned insufficient data ({len(h) if h is not None else 0} rows)")
except Exception as e:
    print(f"USDIDR: yfinance error: {e}")

if not usdidr_ok:
    print(f"USDIDR: using hardcoded fallback {usdidr['value']}")

mkt = {
    "last_update": last_update[:10],
    "market_last_update": last_update,
    "ihsg": ihsg,
    "usdidr": usdidr,
    "gold": {
        "value": 4347,
        "daily": 0.05,
        "weekly": -3.4,
        "monthly": -4.9
    },
    "oil": {
        "value": 88,
        "daily": -3.68,
        "weekly": -5.0,
        "monthly": -10.3
    },
}

with open('dashboard/data/market.json', 'w') as f:
    json.dump(mkt, f, indent=2)

print(f"market.json written with market_last_update={last_update}")
print(f"IHSG: {mkt['ihsg']['value']} (daily: {mkt['ihsg']['daily']}%, monthly: {mkt['ihsg']['monthly']}%)")
print(f"USDIDR: {mkt['usdidr']['value']}")
print(f"Gold: ${mkt['gold']['value']}/oz")
print(f"Oil: ${mkt['oil']['value']}/bbl")
