import json, sys

errors = []

def check_file(path, label):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        errors.append(f"MISSING: {label} ({path})")
        return None
    except json.JSONDecodeError:
        errors.append(f"INVALID JSON: {label} ({path})")
        return None

# 1. market.json
mkt = check_file('dashboard/data/market.json', 'market.json')
if mkt:
    ihsg = mkt.get('ihsg', {})
    usd = mkt.get('usdidr', {})
    if ihsg.get('value') is None or ihsg['value'] == 0:
        errors.append(f"NULL: ihsg.value ({ihsg.get('value')})")
    if usd.get('value') is None or usd['value'] == 0:
        errors.append(f"NULL: usdidr.value ({usd.get('value')})")
    lu = mkt.get('market_last_update')
    if not lu:
        errors.append("MISSING: market_last_update field")
    else:
        print(f"  market_last_update: {lu}")

# 2. radar.json
rad = check_file('dashboard/data/radar.json', 'radar.json')
if rad:
    if rad.get('status') is None:
        errors.append("NULL: radar.status")
    if rad.get('detail_message') is None or rad['detail_message'] == '':
        errors.append("EMPTY: radar.detail_message (AI Summary)")
    # Check timeline regime data
    timeline = rad.get('radar_context')
    if timeline is None:
        errors.append("MISSING: radar.radar_context")

# 3. data.js
try:
    with open('dashboard/data/data.js') as f:
        content = f.read()
    if 'var MKT' not in content:
        errors.append("MISSING: var MKT in data.js")
    if 'var RS' not in content:
        errors.append("MISSING: var RS in data.js")
    print(f"  data.js size: {len(content)} bytes")
except FileNotFoundError:
    errors.append("MISSING: data.js")

print(f"\nValidation complete: {len(errors)} error(s)")
for e in errors:
    print(f"  ERROR: {e}")

if errors:
    sys.exit(1)
else:
    print("All market pipeline checks PASSED")
