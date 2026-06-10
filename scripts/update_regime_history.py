import json, datetime

RADAR = 'dashboard/data/radar.json'
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

if existing >= 0:
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
