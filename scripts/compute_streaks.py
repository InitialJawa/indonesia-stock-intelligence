import csv, json, os, sys
from collections import defaultdict

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'historical', 'turnaround_history.csv')
OUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'data', 'streaks.json')

rows = defaultdict(list)
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows[r['ticker']].append(r)

def streak_from_end(vals):
    count = 0
    for v in reversed(vals):
        if v.lower() == 'true':
            count += 1
        else:
            break
    return count

def first_true_date(vals, dates):
    for v, d in zip(vals, dates):
        if v.lower() == 'true':
            return d
    return None

result = []
for ticker, entries in rows.items():
    entries.sort(key=lambda x: x['date'])
    dates = [e['date'] for e in entries]
    ctx_vals = [e['context_match'] for e in entries]
    trn_vals = [e['transition_match'] for e in entries]
    result.append({
        'ticker': ticker,
        'context_days': streak_from_end(ctx_vals),
        'transition_days': streak_from_end(trn_vals),
        'first_context_detected': first_true_date(ctx_vals, dates) or '—',
        'first_transition_detected': first_true_date(trn_vals, dates) or '—',
        'total_entries': len(entries)
    })

result.sort(key=lambda x: (-x['context_days'] - x['transition_days'], -x['total_entries']))

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2)

print(f'streaks.json written with {len(result)} tickers')
