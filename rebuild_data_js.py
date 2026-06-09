import json
import os

files = ['leaders.json','turnaround.json','summary.json','streaks.json','exit.json','profiles.json','fundamentals.json','cw_b.json','cw_f.json','warehouse.json','ic.json','bt.json','fcolors.json','fnames.json','radar.json','backtest_monthly.json','market.json']
vars = ['L','T','SM','SK','EX','PF','FD','CW_B','CW_F','WI','IC','BT','FCOLORS','FNAMES','RS','BM','MKT']
fallbacks = [[], [], {}, [], [], {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, [], {}]
dirs = ['docs/data/', 'dashboard/data/']

def wi_to_bm(wi):
    if not wi or not wi.get('month_labels'):
        return []
    labels = wi['month_labels']
    cb = wi.get('equity_b') or wi.get('config_b') or []
    cf = wi.get('equity_f') or wi.get('config_f') or []
    ih = wi.get('equity_i') or wi.get('ihsg') or []
    n = min(len(labels), len(cb), len(cf), len(ih))
    SCALE = 1_000_000
    out = []
    for i in range(n):
        out.append({
            'date': labels[i],
            'config_b': round(cb[i] * SCALE, 2),
            'config_f': round(cf[i] * SCALE, 2),
            'ihsg': round(ih[i] * SCALE, 2)
        })
    return out

lines = []
skipped = []
wi_data = None

for fname, vname, fb in zip(files, vars, fallbacks):
    content = None
    for base in dirs:
        path = base + fname
        if os.path.exists(path):
            try:
                with open(path, encoding='utf-8') as f:
                    data = json.load(f)
                content = json.dumps(data, separators=(',', ':'))
                if vname == 'WI':
                    wi_data = data
                break
            except (json.JSONDecodeError, ValueError):
                continue
    if content is not None:
        lines.append(f'var {vname} = {content};')
    else:
        skipped.append(fname)
        if vname == 'BM' and wi_data:
            computed = wi_to_bm(wi_data)
            lines.append('var BM = ' + json.dumps(computed, separators=(',', ':')) + ';')
            print(f'INFO: {fname} not found — BM computed from WI ({len(computed)} months)')
        else:
            lines.append('var ' + vname + ' = ' + json.dumps(fb, separators=(',', ':')) + ';')
            print(f'WARN: {fname} not found in {", ".join(dirs)} — var {vname} set to fallback')

with open('dashboard/data/data.js', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')

print(f'data.js rebuilt with {len(vars)} variables ({len(skipped)} skipped)')
if skipped:
    print('SKIPPED:', ', '.join(skipped))
