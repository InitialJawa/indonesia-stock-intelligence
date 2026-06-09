import json, re

files = ['leaders.json','turnaround.json','summary.json','streaks.json','exit.json','profiles.json','fundamentals.json','cw_b.json','cw_f.json','warehouse.json','ic.json','bt.json','fcolors.json','fnames.json','radar.json','backtest_monthly.json','market.json']
vars = ['L','T','SM','SK','EX','PF','FD','CW_B','CW_F','WI','IC','BT','FCOLORS','FNAMES','RS','BM','MKT']

lines = []
for fname, vname in zip(files, vars):
    with open('dashboard/data/' + fname) as f:
        content = json.dumps(json.load(f), separators=(',', ':'))
    lines.append(f'var {vname} = {content};')

with open('dashboard/data/data.js', 'w') as f:
    f.write('\n'.join(lines) + '\n')

print('data.js rebuilt with', len(vars), 'variables')
for v in vars:
    print('  var', v)
