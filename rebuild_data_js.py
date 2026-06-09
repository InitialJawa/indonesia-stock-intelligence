import json

files = ['leaders.json','turnaround.json','summary.json','streaks.json','exit.json','profiles.json','fundamentals.json','cw_b.json','cw_f.json','warehouse.json','ic.json','bt.json','fcolors.json','fnames.json','radar.json','backtest_monthly.json','market.json']
vars = ['L','T','SM','SK','EX','PF','FD','CW_B','CW_F','WI','IC','BT','FCOLORS','FNAMES','RS','BM','MKT']
fallbacks = [[], [], {}, [], [], {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, [], {}]

lines = []
skipped = []
for fname, vname, fb in zip(files, vars, fallbacks):
    try:
        with open('docs/data/' + fname) as f:
            content = json.dumps(json.load(f), separators=(',', ':'))
        lines.append(f'var {vname} = {content};')
    except FileNotFoundError:
        skipped.append(fname)
        lines.append(f'var {vname} = {json.dumps(fb, separators=(",",":"))};')
        print(f'WARN: {fname} not found — var {vname} set to fallback')

with open('dashboard/data/data.js', 'w') as f:
    f.write('\n'.join(lines) + '\n')

print(f'data.js rebuilt with {len(vars)} variables ({len(skipped)} skipped)')
for v in vars:
    print('  var', v)
if skipped:
    print('SKIPPED:', ', '.join(skipped))
