import json, re

js = open('dashboard/data/data.js').read()

# Check RS
rs_match = re.search(r'var RS = (.+?);', js, re.DOTALL)
if rs_match:
    rs = json.loads(rs_match.group(1))
    print(f'RS: status={rs.get("status")}, action={rs.get("action")}')
    dm = rs.get('detail_message', '')
    print(f'  detail_message length: {len(dm)}, preview: {dm[:60]}')
else:
    print('RS: NOT FOUND')

# Check MKT
mkt_match = re.search(r'var MKT = (.+?);', js, re.DOTALL)
if mkt_match:
    mkt = json.loads(mkt_match.group(1))
    print(f'MKT: ihsg={mkt.get("ihsg")}, usdidr={mkt.get("usdidr")}')
else:
    print('MKT: NOT FOUND')

# Check BM
bm_match = re.search(r'var BM = (.+?);', js, re.DOTALL)
if bm_match:
    bm_raw = bm_match.group(1).strip()
    if bm_raw in ('[]', '{}', '""'):
        print('BM: EMPTY')
    else:
        print(f'BM: {bm_raw[:60]}')
else:
    print('BM: NOT FOUND')

# Check all vars
for v in ['L', 'T', 'EX', 'SK', 'MKT', 'RS', 'BM', 'BM_M', 'IC', 'FCOLORS', 'FNAMES', 'CONFIG_B']:
    if f'var {v}' in js:
        print(f'  var {v}: OK')
    else:
        print(f'  var {v}: MISSING!')
