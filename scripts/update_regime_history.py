import json, datetime

RADAR = 'dashboard/data/radar.json'
MARKET = 'dashboard/data/market.json'
LIVE_MARKET = 'dashboard/data/live_market.json'
HISTORY = 'dashboard/data/regime_history.json'
MAX_DAYS = 30

status_map = {'SAFE': 'RISK ON', 'WARNING': 'NETRAL', 'DANGER': 'RISK OFF'}
action_map = {'ACCUMULATE': 'AKUMULASI', 'HOLD': 'TAHAN', 'WAIT': 'TUNGGU', 'REDUCE': 'KURANGI'}

today = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=7)
today_str = today.strftime('%Y-%m-%d')

radar = {}
try:
    with open(RADAR) as f:
        radar = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    pass

raw_status = radar.get('status', '')
raw_action = radar.get('action', '')
regime = status_map.get(raw_status, raw_status)
action = action_map.get(raw_action, raw_action)

if not regime or not action:
    print("regime_history: no radar data to record")
    exit(0)

ihsg_raw = radar.get('market_health', None)
ihsg_val = None
ihsg_chg = None

mkt = {}
try:
    with open(MARKET) as f:
        mkt = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    try:
        with open(LIVE_MARKET) as f:
            mkt = json.load(f)
        if mkt.get('ihsg'):
            mkt['ihsg'] = {'value': mkt['ihsg']['price'], 'daily': mkt['ihsg']['change_pct']}
    except (FileNotFoundError, json.JSONDecodeError):
        pass

if mkt.get('ihsg'):
    ihsg_val = mkt['ihsg'].get('value')
    ihsg_chg = mkt['ihsg'].get('daily')

note_parts = []
if ihsg_val is not None:
    if ihsg_chg is not None:
        direction = 'menguat' if ihsg_chg > 0 else 'melemah' if ihsg_chg < 0 else 'flat'
        mag = 'signifikan' if abs(ihsg_chg) > 3 else 'moderat' if abs(ihsg_chg) > 1 else 'terbatas'
        note_parts.append(f"IHSG {ihsg_val:.0f} ({direction} {mag}, {ihsg_chg:+.2f}%)")
    else:
        note_parts.append(f"IHSG {ihsg_val:.0f}")

rc = radar.get('radar_context', {})
if rc.get('score_gap') is not None:
    gap = rc['score_gap']
    if gap > 30:
        note_parts.append(f"score gap {gap:.0f} (sangat timpang)")
    elif gap > 15:
        note_parts.append(f"score gap {gap:.0f} (cukup timpang)")

bc = rc.get('breadth_above_60', None)
wc = rc.get('watchlist_count', 1)
if bc is not None:
    ratio = bc / max(wc, 1)
    if ratio > 0.4:
        note_parts.append(f"{bc}/{wc} saham >60")
    else:
        note_parts.append(f"breadth terbatas {bc}/{wc}")

note = '; '.join(note_parts) if note_parts else ''

history = []
try:
    with open(HISTORY) as f:
        history = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    pass

existing = -1
for i, entry in enumerate(history):
    if entry.get('date') == today_str:
        existing = i
        break

entry = {'date': today_str, 'regime': regime, 'action': action}
if ihsg_val is not None:
    entry['ihsg_close'] = ihsg_val
if ihsg_chg is not None:
    entry['change_pct'] = ihsg_chg
if note:
    entry['note'] = note

if existing >= 0:
    old = history[existing]
    if old.get('note') and not note:
        entry['note'] = old['note']
    for k in ('ihsg_close', 'change_pct'):
        if old.get(k) is not None and entry.get(k) is None:
            entry[k] = old[k]
    history[existing] = entry
    print(f"regime_history: updated existing entry for {today_str}")
else:
    history.append(entry)
    print(f"regime_history: appended new entry for {today_str}")

history.sort(key=lambda x: x.get('date', ''), reverse=True)
history = history[:MAX_DAYS]

with open(HISTORY, 'w') as f:
    json.dump(history, f, indent=2)

print(f"regime_history: {len(history)} entries (max {MAX_DAYS}), saved to {HISTORY}")
