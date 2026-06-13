import json
import csv
import math
import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import yfinance as yf
import pandas as pd
from utils.config_loader import load_universe

TICKERS = load_universe("IDX80")

BENCHMARK_TICKER = '^JKSE'

# RESEARCH-009B thresholds
DRAWDOWN_THRESHOLD = -0.25
DISTANCE_THRESHOLD = -0.20

# RESEARCH-008B thresholds
RECOVERY_THRESHOLD = 0.10
VOLUME_RATIO_THRESHOLD = 1.3

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

def compute_features(close_df, vol_df):
    results = []
    if BENCHMARK_TICKER in close_df.columns:
        ihsg_close = close_df[BENCHMARK_TICKER]
    else:
        print(f"  Warning: {BENCHMARK_TICKER} not available")
        ihsg_close = None

    for ticker in TICKERS:
        if ticker not in close_df.columns:
            print(f"  Warning: {ticker} not found, skipping")
            continue
        prices = close_df[ticker].dropna()
        if len(prices) < 60:
            print(f"  Warning: {ticker} insufficient data ({len(prices)} days), skipping")
            continue
        try:
            latest_price = prices.iloc[-1]

            # Drawdown 252d
            max_252 = prices.iloc[-min(252, len(prices)):].max()
            drawdown_252d = (latest_price - max_252) / max_252 if max_252 > 0 else 0

            # Distance from high 252d (same metric)
            distance_from_high_252d = drawdown_252d

            # Volatility 60d
            prices_60d = prices.iloc[-60:]
            daily_returns_60d = prices_60d.pct_change().dropna()
            volatility_60d = float(daily_returns_60d.std())

            # 60-day low for recovery
            low_60d = prices_60d.min()
            recovery_from_60d_low = (latest_price - low_60d) / low_60d if low_60d > 0 else 0

            # RS_CHANGE_60D
            rs_change_60d = 0.0
            rs_60d = 0.0
            if len(prices) >= 120 and ihsg_close is not None and not ihsg_close.empty:
                ihsg_prices = ihsg_close.dropna()
                if len(ihsg_prices) >= 61:
                    tr60 = prices.iloc[-1] / prices.iloc[-61] - 1 if prices.iloc[-61] > 0 else 0
                    ir60 = ihsg_prices.iloc[-1] / ihsg_prices.iloc[-61] - 1 if len(ihsg_prices) >= 61 and ihsg_prices.iloc[-61] > 0 else 0
                    rs_60d = tr60 - ir60
                if len(prices) >= 121 and len(ihsg_prices) >= 121:
                    tr60a = prices.iloc[-61] / prices.iloc[-121] - 1 if prices.iloc[-121] > 0 else 0
                    ir60a = ihsg_prices.iloc[-61] / ihsg_prices.iloc[-121] - 1 if ihsg_prices.iloc[-121] > 0 else 0
                    rs_change_60d = rs_60d - (tr60a - ir60a)

            # Volume Ratio (latest volume vs MA20 volume)
            volume_ratio = 0.0
            if vol_df is not None and ticker in vol_df.columns:
                volumes = vol_df[ticker].dropna()
                if len(volumes) >= 21:
                    ma20_vol = volumes.iloc[-21:].mean()
                    latest_vol = volumes.iloc[-1]
                    volume_ratio = float(latest_vol / ma20_vol) if ma20_vol > 0 else 0

            # Above MA20
            ma20 = prices.iloc[-min(20, len(prices)):].mean()
            above_ma20 = latest_price > ma20

            results.append({
                'ticker': ticker,
                'price': float(latest_price),
                'drawdown_252d': drawdown_252d,
                'distance_from_high_252d': distance_from_high_252d,
                'volatility_60d': volatility_60d,
                'rs_change_60d': rs_change_60d,
                'rs_60d': rs_60d,
                'volume_ratio': volume_ratio,
                'recovery_from_60d_low': recovery_from_60d_low,
                'above_ma20': above_ma20
            })
        except Exception as e:
            print(f"  Warning: Error for {ticker}: {e}")
            continue
    print(f"  Computed features for {len(results)}/{len(TICKERS)} tickers")
    return results

def classify(features):
    vol_values = [f['volatility_60d'] for f in features]
    n_vol = len(vol_values)

    def is_high_vol(val):
        if n_vol <= 1:
            return False
        lesser = sum(1 for x in vol_values if x < val)
        vol_pct = (lesser / (n_vol - 1)) * 100
        return vol_pct >= 66.7

    results = []
    for f in features:
        dd = safe_float(f['drawdown_252d'], 0)
        dist = safe_float(f['distance_from_high_252d'], 0)
        vol = safe_float(f['volatility_60d'], 0)
        rs_chg = safe_float(f['rs_change_60d'], 0)
        recov = safe_float(f['recovery_from_60d_low'], 0)
        vr = safe_float(f['volume_ratio'], 0)

        deep_dd = dd < DRAWDOWN_THRESHOLD
        far_from_high = dist < DISTANCE_THRESHOLD
        high_vol = is_high_vol(vol)
        rs_improving = rs_chg > 0
        vol_high = vr > VOLUME_RATIO_THRESHOLD
        above_ma20 = f['above_ma20']
        recovered = recov > RECOVERY_THRESHOLD

        context_match = deep_dd and far_from_high and high_vol
        transition_match = rs_improving
        confirmation_count = sum([vol_high, above_ma20, recovered])

        results.append({
            'ticker': f['ticker'],
            'drawdown_252d': round(f['drawdown_252d'] * 100, 2),
            'distance_from_high_252d': round(f['distance_from_high_252d'] * 100, 2),
            'volatility_60d': round(f['volatility_60d'] * 100, 2),
            'rs_change_60d': round(f['rs_change_60d'] * 100, 2),
            'volume_ratio': round(vr, 2),
            'recovery_from_60d_low': round(recov * 100, 2),
            'above_ma20': above_ma20,
            'deep_drawdown': deep_dd,
            'far_from_high': far_from_high,
            'high_volatility': high_vol,
            'rs_improving': rs_improving,
            'volume_high': vol_high,
            'recovered': recovered,
            'context_match': context_match,
            'transition_match': transition_match,
            'confirmation_count': confirmation_count,
            'full_match': context_match and transition_match
        })
    results.sort(key=lambda x: (
        -int(x['full_match']),
        -int(x['context_match']),
        -int(x['transition_match']),
        -x['confirmation_count'],
        -x['drawdown_252d']
    ))
    for i, r in enumerate(results):
        r['rank'] = i + 1
    return results

def generate_leaders():
    scores_dir = Path('output/scores')
    required = ['final_ranking_v3.json', 'quality_ranking.json', 'growth_ranking.json', 'value_ranking.json', 'momentum_ranking.json']
    for f in required:
        if not (scores_dir / f).exists():
            print(f"  Warning: {f} not found — leaders_latest.csv will be empty")
            return []
    try:
        with open(scores_dir / 'final_ranking_v3.json') as f:
            final_data = json.load(f)
        with open(scores_dir / 'quality_ranking.json') as f:
            q_data = json.load(f)
        with open(scores_dir / 'growth_ranking.json') as f:
            g_data = json.load(f)
        with open(scores_dir / 'value_ranking.json') as f:
            v_data = json.load(f)
        with open(scores_dir / 'momentum_ranking.json') as f:
            m_data = json.load(f)
    except Exception as e:
        print(f"  Error loading factor scores: {e}")
        return []
    q_map = {x['ticker']: x['quality_score'] for x in q_data}
    g_map = {x['ticker']: x['growth_score'] for x in g_data}
    v_map = {x['ticker']: x['value_score'] for x in v_data}
    m_map = {x['ticker']: x['momentum'] for x in m_data}
    W_Q, W_G, W_V, W_M = 0.25, 0.30, 0.10, 0.35
    leaders = []
    for item in final_data:
        ticker = item['ticker']
        q = q_map.get(ticker, 0)
        g_val = g_map.get(ticker, 0)
        v = v_map.get(ticker, 0)
        m = m_map.get(ticker, 0)
        config_b_score = q * W_Q + g_val * W_G + v * W_V + m * W_M
        leaders.append({
            'ticker': ticker,
            'quality': round(q, 2),
            'growth': round(g_val, 2),
            'value': round(v, 2),
            'momentum': round(m, 2),
            'final_score': round(config_b_score, 2)
        })
    leaders.sort(key=lambda x: x['final_score'], reverse=True)
    for i, l in enumerate(leaders):
        l['rank'] = i + 1
    return leaders

def write_csv(data, filepath, fieldnames):
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Written: {filepath} ({len(data)} rows)")

def write_json(data, filepath):
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Written: {filepath}")

def main():
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    print("=== Daily Turnaround Watchlist ===")
    print(f"Date: {date_str}")
    print("\n--- Step 1: Config B Leaders ---")
    leaders = generate_leaders()
    leaders_fields = ['rank', 'ticker', 'quality', 'growth', 'value', 'momentum', 'final_score']
    write_csv(leaders, 'data/current/leaders_latest.csv', leaders_fields)
    if leaders:
        top5_str = ' | '.join(f"{l['ticker']}({l['final_score']})" for l in leaders[:5])
        print(f"  Top 5: {top5_str}")
    print("\n--- Step 2: Download Daily Data ---")
    close_df, vol_df = fetch_daily_data()
    print("\n--- Step 3: Compute Features ---")
    features = compute_features(close_df, vol_df)
    if not features:
        print("  ERROR: No features computed. Aborting.")
        return
    print("\n--- Step 4: Classify ---")
    classified = classify(features)
    n_ctx = sum(1 for r in classified if r['context_match'])
    n_trn = sum(1 for r in classified if r['transition_match'])
    n_full = sum(1 for r in classified if r['full_match'])
    print(f"  Context Match: {n_ctx}/30 | Transition Match: {n_trn}/30 | Full Match: {n_full}/30")
    print("\n--- Step 5: Output turnaround_latest.csv ---")
    turnaround_fields = [
        'rank', 'ticker',
        'drawdown_252d', 'distance_from_high_252d', 'volatility_60d',
        'rs_change_60d', 'volume_ratio', 'recovery_from_60d_low',
        'context_match', 'transition_match'
    ]
    csv_rows = [{k: r[k] for k in turnaround_fields} for r in classified]
    write_csv(csv_rows, 'data/current/turnaround_latest.csv', turnaround_fields)
    print("\n  Full Match (Context + Transition):")
    for r in classified:
        if r['full_match']:
            print(f"    {r['ticker']}: DD={r['drawdown_252d']}% Dist={r['distance_from_high_252d']}% "
                  f"Vol={r['volatility_60d']}% RSchg={r['rs_change_60d']}% "
                  f"VR={r['volume_ratio']}x Recov={r['recovery_from_60d_low']}% "
                  f"Conf={r['confirmation_count']}/3")
    if n_full == 0:
        print("    (none)")
    print("\n  Context Match Only:")
    for r in classified:
        if r['context_match'] and not r['transition_match']:
            print(f"    {r['ticker']}: DD={r['drawdown_252d']}% Dist={r['distance_from_high_252d']}% "
                  f"Vol={r['volatility_60d']}% RSchg={r['rs_change_60d']}%")
    print("\n  Transition Match Only:")
    for r in classified:
        if r['transition_match'] and not r['context_match']:
            print(f"    {r['ticker']}: RSchg={r['rs_change_60d']}% DD={r['drawdown_252d']}% "
                  f"Dist={r['distance_from_high_252d']}% Vol={r['volatility_60d']}%")
    print("\n--- Step 6: Output turnaround_summary.json ---")
    top_candidates = []
    for r in classified[:10]:
        entry = {
            'ticker': str(r['ticker']),
            'drawdown': float(r['drawdown_252d']),
            'distance_from_high': float(r['distance_from_high_252d']),
            'volatility': float(r['volatility_60d']),
            'rs_change_60d': float(r['rs_change_60d']),
            'volume_ratio': float(r['volume_ratio']),
            'recovery': float(r['recovery_from_60d_low']),
            'context_match': bool(r['context_match']),
            'transition_match': bool(r['transition_match']),
            'full_match': bool(r['full_match']),
            'confirmation_count': int(r['confirmation_count'])
        }
        top_candidates.append(entry)
    context_tickers = {
        'deep_drawdown': [str(r['ticker']) for r in classified if r['deep_drawdown']],
        'far_from_high': [str(r['ticker']) for r in classified if r['far_from_high']],
        'high_volatility': [str(r['ticker']) for r in classified if r['high_volatility']]
    }
    signal_diagnostics = {
        'rs_change_60d_positive_count': int(sum(1 for r in classified if r['rs_improving'])),
        'volume_ratio_high_count': int(sum(1 for r in classified if r['volume_high'])),
        'above_ma20_count': int(sum(1 for r in classified if r['above_ma20'])),
        'recovery_gt_10pct_count': int(sum(1 for r in classified if r['recovered'])),
        'avg_drawdown_252d': float(round(sum(r['drawdown_252d'] for r in classified) / len(classified), 2)),
        'avg_volatility_60d': float(round(sum(r['volatility_60d'] for r in classified) / len(classified), 2))
    }
    summary = {
        'date': date_str,
        'universe_size': len(classified),
        'context_match_count': n_ctx,
        'transition_match_count': n_trn,
        'full_match_count': n_full,
        'context_classification': context_tickers,
        'signal_diagnostics': signal_diagnostics,
        'top_candidates': top_candidates
    }
    write_json(summary, 'data/state/turnaround_summary.json')
    print("\n=== Daily Turnaround Watchlist Complete ===")
    print(f"Outputs: leaders_latest.csv ({len(leaders)} rows), "
          f"turnaround_latest.csv ({len(classified)} rows), "
          f"turnaround_summary.json")

if __name__ == '__main__':
    main()
