import json
import csv
import math
import datetime
from pathlib import Path
import yfinance as yf
import pandas as pd

TICKERS = [
    'ADRO.JK', 'ESSA.JK', 'MAPI.JK', 'PTBA.JK', 'AKRA.JK', 'CPIN.JK',
    'ANTM.JK', 'EXCL.JK', 'BBRI.JK', 'BMRI.JK', 'BRPT.JK', 'BBNI.JK',
    'INDF.JK', 'PGAS.JK', 'MDKA.JK', 'ITMG.JK', 'TLKM.JK', 'ASII.JK',
    'INTP.JK', 'ICBP.JK', 'BBCA.JK', 'UNTR.JK', 'MIKA.JK', 'GOTO.JK',
    'SMGR.JK', 'SIDO.JK', 'TPIA.JK', 'KLBF.JK', 'AMMN.JK', 'HEAL.JK'
]

BENCHMARK_TICKER = '^JKSE'
LEADERS_FILE = Path('leaders_latest.csv')
EXIT_CSV = Path('exit_watchlist_latest.csv')
EXIT_JSON = Path('exit_summary.json')
ENTRY_PRICES_FILE = Path('exit_entry_prices.json')

EXIT_STATE_ORDER = {
    'EXIT': 0,
    'EXIT RISK': 1,
    'WEAKENING': 2,
    'EXIT WATCH': 3,
    'HEALTHY': 4
}

def safe_float(val, default=0.0):
    try:
        if val is None:
            return default
        f_val = float(val)
        if math.isnan(f_val) or math.isinf(f_val):
            return default
        return f_val
    except (ValueError, TypeError):
        return default

def load_entry_prices():
    if ENTRY_PRICES_FILE.exists():
        with open(ENTRY_PRICES_FILE) as f:
            return json.load(f)
    return {}

def save_entry_prices(prices):
    ENTRY_PRICES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ENTRY_PRICES_FILE, 'w') as f:
        json.dump(prices, f, indent=2)

def read_leaders():
    if not LEADERS_FILE.exists():
        print(f"  Warning: {LEADERS_FILE} not found")
        return []
    leaders = []
    with open(LEADERS_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['rank'] = int(row['rank'])
            row['final_score'] = safe_float(row.get('final_score', 0))
            leaders.append(row)
    return leaders

def fetch_daily_data():
    all_tickers = TICKERS + [BENCHMARK_TICKER]
    print(f"Downloading daily data for {len(all_tickers)} tickers...")
    df = yf.download(all_tickers, period='1y', interval='1d', progress=False, auto_adjust=True)
    if df.empty:
        raise RuntimeError("Failed to download data")
    if isinstance(df.columns, pd.MultiIndex):
        close_df = df.xs('Close', axis=1, level=0)
        vol_df = df.xs('Volume', axis=1, level=0) if 'Volume' in df.columns.get_level_values(0) else None
    else:
        close_df = df[['Close']] if 'Close' in df else df
        vol_df = df[['Volume']] if 'Volume' in df else None
    close_df = close_df.dropna(how='all')
    if vol_df is not None:
        vol_df = vol_df.dropna(how='all')
    print(f"  Downloaded {len(close_df)} days, {len(close_df.columns)} tickers")
    return close_df, vol_df

def compute_exit_features(close_df, vol_df):
    results = {}
    if BENCHMARK_TICKER in close_df.columns:
        ihsg_close = close_df[BENCHMARK_TICKER].dropna()
    else:
        print(f"  Warning: {BENCHMARK_TICKER} not available")
        ihsg_close = None

    for ticker in TICKERS:
        if ticker not in close_df.columns:
            print(f"  Warning: {ticker} not found, skipping")
            continue
        prices = close_df[ticker].dropna()
        if len(prices) < 100:
            print(f"  Warning: {ticker} insufficient data ({len(prices)} days), skipping")
            continue
        try:
            latest_price = prices.iloc[-1]

            # MA values
            ma20 = prices.rolling(20).mean().iloc[-1] if len(prices) >= 20 else None
            ma50 = prices.rolling(50).mean().iloc[-1] if len(prices) >= 50 else None
            ma100 = prices.rolling(100).mean().iloc[-1] if len(prices) >= 100 else None

            # RS_20D
            rs_20d = 0.0
            rs_change_20d = 0.0
            if ihsg_close is not None and len(ihsg_close) >= 21 and len(prices) >= 21:
                tr20 = prices.iloc[-1] / prices.iloc[-21] - 1
                ir20 = ihsg_close.iloc[-1] / ihsg_close.iloc[-21] - 1
                rs_20d = tr20 - ir20

                # RS_CHANGE_20D: change in RS_20D over the last 20 days
                if len(prices) >= 41 and len(ihsg_close) >= 41:
                    tr20_prev = prices.iloc[-21] / prices.iloc[-41] - 1
                    ir20_prev = ihsg_close.iloc[-21] / ihsg_close.iloc[-41] - 1
                    rs_20d_prev = tr20_prev - ir20_prev
                    rs_change_20d = rs_20d - rs_20d_prev

            results[ticker] = {
                'close': float(latest_price),
                'ma20': float(ma20) if ma20 is not None and not pd.isna(ma20) else None,
                'ma50': float(ma50) if ma50 is not None and not pd.isna(ma50) else None,
                'ma100': float(ma100) if ma100 is not None and not pd.isna(ma100) else None,
                'rs_20d': rs_20d,
                'rs_change_20d': rs_change_20d,
            }
        except Exception as e:
            print(f"  Warning: Error for {ticker}: {e}")
            continue

    print(f"  Computed features for {len(results)}/{len(TICKERS)} tickers")
    return results

def classify_exit(features, leaders, entry_prices):
    leader_by_ticker = {l['ticker']: l for l in leaders}
    results = []
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    updated_entry_prices = dict(entry_prices)

    for ticker in TICKERS:
        if ticker not in features:
            continue
        feat = features[ticker]
        close = feat['close']
        ma20 = feat['ma20']
        ma50 = feat['ma50']
        ma100 = feat['ma100']
        rs_20d = feat['rs_20d']
        rs_change_20d = feat['rs_change_20d']

        leader = leader_by_ticker.get(ticker)
        rank = leader['rank'] if leader else 99
        prev_rank = updated_entry_prices.get(ticker, {}).get('current_rank', rank)

        # Track entry price for top 10 tickers
        entry_info = updated_entry_prices.get(ticker, {})
        entry_price = entry_info.get('entry_price')
        if rank <= 10 and entry_price is None:
            entry_price = close
            updated_entry_prices[ticker] = {
                'entry_price': entry_price,
                'entry_date': date_str,
                'current_rank': rank
            }

        # Update current rank
        if ticker in updated_entry_prices:
            updated_entry_prices[ticker]['current_rank'] = rank

        rank_change = prev_rank - rank if prev_rank != rank else 0

        # Compute drawdown from entry
        drawdown_from_entry = 0.0
        if entry_price is not None and entry_price > 0:
            drawdown_from_entry = (close - entry_price) / entry_price

        # Apply exit rules
        triggered_rules = []

        # Rule A: RANK EXIT - stock leaves Config B Top 10
        rule_a = rank > 10
        if rule_a:
            triggered_rules.append('A')

        # Rule B: MOMENTUM EXIT - RS_20D < 0 AND RS_CHANGE_20D < 0
        rule_b = rs_20d < 0 and rs_change_20d < 0
        if rule_b:
            triggered_rules.append('B')

        # Rule C: TREND EXIT - Close < MA50
        rule_c = ma50 is not None and close < ma50
        if rule_c:
            triggered_rules.append('C')

        # Rule D: CONFIRMED EXIT - (Close < MA100 AND RS20 < 0 AND RS_CHANGE_20D < 0) OR Drawdown from entry > 15%
        rule_d1 = ma100 is not None and close < ma100 and rs_20d < 0 and rs_change_20d < 0
        rule_d2 = drawdown_from_entry < -0.15
        rule_d = rule_d1 or rule_d2
        if rule_d:
            triggered_rules.append('D')

        # Determine exit state (highest priority triggered rule)
        if rule_d:
            state = 'EXIT'
        elif rule_c:
            state = 'EXIT RISK'
        elif rule_b:
            state = 'WEAKENING'
        elif rule_a:
            state = 'EXIT WATCH'
        else:
            state = 'HEALTHY'

        results.append({
            'ticker': ticker,
            'rank': rank,
            'rank_change': rank_change,
            'close': round(close, 2),
            'ma20': round(ma20, 2) if ma20 is not None else None,
            'ma50': round(ma50, 2) if ma50 is not None else None,
            'ma100': round(ma100, 2) if ma100 is not None else None,
            'rs_20d': round(rs_20d * 100, 2),
            'rs_change_20d': round(rs_change_20d * 100, 2),
            'drawdown_from_entry': round(drawdown_from_entry * 100, 2),
            'exit_state': state,
            'triggered_rules': ', '.join(triggered_rules) if triggered_rules else 'NONE'
        })

    # Sort by state priority (EXIT first), then by rank
    results.sort(key=lambda x: (EXIT_STATE_ORDER.get(x['exit_state'], 99), x['rank']))

    # Save updated entry prices
    save_entry_prices(updated_entry_prices)

    return results

def write_csv(data, filepath):
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    fieldnames = [
        'Date', 'ticker', 'rank', 'rank_change', 'close',
        'rs_20d', 'rs_change_20d',
        'ma20', 'ma50', 'ma100',
        'drawdown_from_entry', 'exit_state', 'triggered_rules'
    ]
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in data:
            row = {k: r.get(k) for k in fieldnames}
            row['Date'] = date_str
            writer.writerow(row)
    print(f"Written: {filepath} ({len(data)} rows)")

def write_json(data, filepath, summary_counts):
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    output = {
        'date': datetime.datetime.now().strftime('%Y-%m-%d'),
        'universe_size': len(data),
        **summary_counts
    }
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"Written: {filepath}")

def main():
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    print("=== Daily Exit Watchlist ===")
    print(f"Date: {date_str}")

    print("\n--- Step 1: Load Config B Leaders ---")
    leaders = read_leaders()
    print(f"  Loaded {len(leaders)} leaders")

    print("\n--- Step 2: Load Entry Prices ---")
    entry_prices = load_entry_prices()
    print(f"  Tracked tickers with entry prices: {len(entry_prices)}")

    print("\n--- Step 3: Download Daily Data ---")
    close_df, vol_df = fetch_daily_data()

    print("\n--- Step 4: Compute Exit Features ---")
    features = compute_exit_features(close_df, vol_df)
    if not features:
        print("  ERROR: No features computed. Aborting.")
        return

    print("\n--- Step 5: Apply Exit Rules ---")
    classified = classify_exit(features, leaders, entry_prices)
    state_counts = {}
    for r in classified:
        s = r['exit_state']
        state_counts[s] = state_counts.get(s, 0) + 1

    for state in ['HEALTHY', 'EXIT WATCH', 'WEAKENING', 'EXIT RISK', 'EXIT']:
        c = state_counts.get(state, 0)
        print(f"  {state}: {c}/{len(classified)}")

        # Print EXIT state tickers
    exit_tickers = [r for r in classified if r['exit_state'] == 'EXIT']
    if exit_tickers:
        print("\n  EXIT (Rule D):")
        for r in exit_tickers:
            reasons = []
            if r['close'] < (r['ma100'] or 0) and r['rs_20d'] < 0 and r['rs_change_20d'] < 0:
                reasons.append(f"Close<MA100 + RS20<0 + RSChg<0")
            if r['drawdown_from_entry'] < -15:
                reasons.append(f"Drawdown {r['drawdown_from_entry']}%")
            print(f"    {r['ticker']}: {' | '.join(reasons)}")

    print("\n--- Step 6: Output exit_watchlist_latest.csv ---")
    write_csv(classified, EXIT_CSV)

    print("\n--- Step 7: Output exit_summary.json ---")
    summary_counts = {
        'Healthy': state_counts.get('HEALTHY', 0),
        'Exit Watch': state_counts.get('EXIT WATCH', 0),
        'Weakening': state_counts.get('WEAKENING', 0),
        'Exit Risk': state_counts.get('EXIT RISK', 0),
        'Exit': state_counts.get('EXIT', 0)
    }
    write_json(classified, EXIT_JSON, summary_counts)

    print("\n=== Daily Exit Watchlist Complete ===")
    print(f"Outputs: {EXIT_CSV} ({len(classified)} rows), {EXIT_JSON}")

if __name__ == '__main__':
    main()
