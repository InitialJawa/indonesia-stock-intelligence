import json
import os

files = ['leaders.json','turnaround.json','summary.json','streaks.json','exit.json','profiles.json','fundamentals.json','cw_b.json','cw_f.json','warehouse.json','ic.json','bt.json','fcolors.json','fnames.json','radar.json','backtest_monthly.json','market.json']
vars = ['L','T','SM','SK','EX','PF','FD','CW_B','CW_F','WI','IC','BT','FCOLORS','FNAMES','RS','BM','MKT']
fallbacks = [[], [], {}, [], [], {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, [], {}]
dirs = ['docs/data/', 'dashboard/data/']

lines = []
skipped = []
for fname, vname, fb in zip(files, vars, fallbacks):
    content = None
    for base in dirs:
        path = base + fname
        if os.path.exists(path):
            try:
                with open(path) as f:
                    content = json.dumps(json.load(f), separators=(',', ':'))
                break
            except (json.JSONDecodeError, ValueError):
                continue
    if content is not None:
        lines.append(f'var {vname} = {content};')
    else:
        skipped.append(fname)
        lines.append(f'var {vname} = {json.dumps(fb, separators=(",",":"))};')
        print(f'WARN: {fname} not found in {", ".join(dirs)} — var {vname} set to fallback')

with open('dashboard/data/data.js', 'w') as f:
    f.write('\n'.join(lines) + '\n')

print(f'data.js rebuilt with {len(vars)} variables ({len(skipped)} skipped)')
if skipped:
    print('SKIPPED:', ', '.join(skipped))
