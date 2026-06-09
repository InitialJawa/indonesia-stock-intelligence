import json
import csv
import datetime
from pathlib import Path

HISTORY_FILE = Path("database/historical/turnaround_history.csv")
V2_DIR = Path("dashboard")
LEADERS_FILE = Path("data/current/leaders_latest.csv")
TURNAROUND_FILE = Path("data/current/turnaround_latest.csv")
SUMMARY_FILE = Path("data/state/turnaround_summary.json")
EXIT_FILE = Path("data/current/exit_watchlist_latest.csv")
PROFILES_FILE = Path("data/state/company_profiles.json")
FUND_FILE = Path("output/raw/fundamentals.json")
GROWTH_FILE = Path("output/raw/growth.json")
EXIT_SUMMARY_FILE = Path("data/state/exit_summary.json")
RADAR_STATUS_FILE = Path("output/daily_radar_status.json")

def read_csv(filepath):
    if not filepath.exists():
        return []
    with open(filepath, 'r') as f:
        return list(csv.DictReader(f))

def read_json(filepath):
    if not filepath.exists():
        return {}
    with open(filepath) as f:
        return json.load(f)

def update_history(turnaround_rows, date_str):
    existing = []
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r') as f:
            reader = csv.DictReader(f)
            existing = [r for r in reader]
    new_keys = set()
    new_rows = []
    for r in turnaround_rows:
        key = f"{date_str}|{r['ticker']}"
        if key not in new_keys:
            new_keys.add(key)
            new_rows.append({
                'date': date_str,
                'ticker': r['ticker'],
                'context_match': r['context_match'],
                'transition_match': r['transition_match']
            })
    seen = set()
    deduped = []
    for r in existing + new_rows:
        key = f"{r['date']}|{r['ticker']}"
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'ticker', 'context_match', 'transition_match'])
        writer.writeheader()
        writer.writerows(deduped)
    return deduped

def compute_streaks(history_rows):
    by_ticker = {}
    for r in history_rows:
        t = r['ticker']
        if t not in by_ticker:
            by_ticker[t] = []
        by_ticker[t].append(r)
    streaks = {}
    for ticker, entries in by_ticker.items():
        entries.sort(key=lambda x: x['date'], reverse=True)
        ctx_streak = 0
        trn_streak = 0
        for e in entries:
            if e['context_match'] == 'True':
                ctx_streak += 1
            else:
                break
        for e in entries:
            if e['transition_match'] == 'True':
                trn_streak += 1
            else:
                break
        first_ctx = None
        first_trn = None
        for e in reversed(entries):
            if e['context_match'] == 'True' and first_ctx is None:
                first_ctx = e['date']
            if e['transition_match'] == 'True' and first_trn is None:
                first_trn = e['date']
        streaks[ticker] = {
            'ctx_days': ctx_streak,
            'trn_days': trn_streak,
            'first_ctx': first_ctx or '-',
            'first_trn': first_trn or '-',
            'total_entries': len(entries)
        }
    return streaks

def file_age(path, report_date=None):
    if not path.exists():
        return 'N/A'
    if report_date:
        try:
            ref = datetime.datetime.strptime(report_date, '%Y-%m-%d')
            mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime)
            if mtime < ref:
                age = ref - mtime
                return f"{age.days}d {age.seconds // 3600}h ago" if age.days < 30 else f"{age.days}d ago"
            return "0d 0h ago"
        except (ValueError, TypeError):
            pass
    mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime)
    age = datetime.datetime.now() - mtime
    return f"{age.days}d {age.seconds // 3600}h ago" if age.days < 30 else f"{age.days}d ago"

def build_html(leaders, turnaround, summary, history, streaks, report_date, exit_data=None, profiles=None, fundamentals=None, radar_status=None):
    summary_data = summary if isinstance(summary, dict) else {}
    top_candidates = summary_data.get('top_candidates', [])
    ctx_count = summary_data.get('context_match_count', 0)
    trn_count = summary_data.get('transition_match_count', 0)
    full_count = summary_data.get('full_match_count', 0)
    sig = summary_data.get('signal_diagnostics', {})

    leaders_json = json.dumps(leaders)
    turnaround_json = json.dumps(turnaround)
    summary_json = json.dumps(summary_data)
    streaks_json = json.dumps(streaks)
    exit_json = json.dumps(exit_data if exit_data else [])
    profiles_json = json.dumps(profiles if profiles else {})
    fundamentals_json = json.dumps(fundamentals if fundamentals else {})

    radar_data = radar_status if isinstance(radar_status, dict) else {}
    radar_detail = radar_data.get('detail_message', '')
    radar_status_label = radar_data.get('status', 'SAFE')
    radar_status_escaped = radar_detail.replace('"', '\"').replace("'", "\\'").replace('\n', ' ')

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>ISI Dashboard V2 | Read-Only</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'DM Sans','Segoe UI',sans-serif;background:#0f1115;color:#F5F7FA;min-height:100vh}}
.hdr{{padding:1rem 1.5rem;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #222830;flex-wrap:wrap;gap:8px}}
.logo{{font-family:'Space Mono','Courier New',monospace;font-size:12px;color:#00c26f;letter-spacing:.1em}}
.logo span{{color:#9CA3AF}}
.dt{{font-size:11px;color:#9CA3AF;font-family:'Space Mono',monospace}}
.tab-nav{{display:flex;gap:2px;padding:.75rem 1.5rem 0;border-bottom:1px solid #222830;overflow-x:auto}}
.tab-btn{{padding:8px 18px;font-size:11px;font-family:'Space Mono',monospace;background:transparent;border:none;color:#9CA3AF;cursor:pointer;border-bottom:2px solid transparent;transition:all .15s;white-space:nowrap;letter-spacing:.05em}}
.tab-btn:hover{{color:#C9D1D9}}
.tab-btn.active{{color:#00c26f;border-bottom-color:#00c26f}}
.tc{{display:none;padding:1rem 1.5rem}}
.tc.active{{display:block}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{font-size:11px;font-family:'Space Mono',monospace;color:#C9D1D9;text-transform:uppercase;letter-spacing:.06em;padding:10px 10px;border-bottom:1px solid #222830;text-align:left;white-space:nowrap;font-weight:700;position:sticky;top:0;background:#0f1115;z-index:1;cursor:pointer;user-select:none}}
th:hover{{color:#F5F7FA}}
th .sort-arrow{{color:#9CA3AF;font-size:9px;margin-left:2px}}
td{{padding:8px 10px;border-bottom:1px solid #1a1f26;vertical-align:middle}}
tr:hover td{{background:#1a1e24}}
.tk{{font-family:'Space Mono',monospace;font-weight:700;color:#F5F7FA}}
.sf{{font-family:'Space Mono',monospace;font-weight:700}}
.sf.high{{color:#00c26f}}.sf.mid{{color:#f59e0b}}.sf.low{{color:#ef4444}}
.badge{{font-size:9px;padding:2px 8px;border-radius:3px;font-family:'Space Mono',monospace;display:inline-block}}
.bg-green{{background:#052e16;color:#00c26f;border:1px solid #166534}}
.bg-red{{background:#2a1111;color:#ef4444;border:1px solid #661111}}
.bg-yellow{{background:#2a2411;color:#f59e0b;border:1px solid #665511}}
.bg-gray{{background:#171b20;color:#9CA3AF;border:1px solid #222830}}
.bg-blue{{background:#0c1929;color:#60a5fa;border:1px solid #1e3a5f}}
.bar{{display:flex;align-items:center;gap:6px}}
.bar-track{{height:3px;border-radius:2px;background:#222830;width:50px;overflow:hidden}}
.bar-fill{{height:100%;border-radius:2px}}
.bv{{font-size:10px;color:#9CA3AF;font-family:'Space Mono',monospace;min-width:24px;text-align:right}}
.card-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin-bottom:1rem}}
.card{{background:#171b20;border:1px solid #222830;border-radius:8px;padding:1rem}}
.card-label{{font-size:10px;color:#C9D1D9;font-family:'Space Mono',monospace;text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;font-weight:600}}
.card-val{{font-size:22px;font-weight:700;font-family:'Space Mono',monospace;color:#F5F7FA}}
.card-val.g{{color:#00c26f}}.card-val.r{{color:#ef4444}}.card-val.y{{color:#f59e0b}}.card-val.b{{color:#60a5fa}}
.card-sub{{font-size:10px;color:#9CA3AF;margin-top:4px}}
.wide-card{{grid-column:1/-1}}
.stat-row{{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #1a1f26;font-size:12px}}
.stat-row:last-child{{border:none}}
.stat-label{{color:#C9D1D9}}
.stat-val{{font-family:'Space Mono',monospace;font-weight:600;color:#F5F7FA}}
.ctx-table td{{font-size:12px}}
.sig-bull{{color:#00c26f}}.sig-bear{{color:#ef4444}}.sig-neu{{color:#C9D1D9}}
.streak-bar{{display:inline-flex;align-items:center;gap:4px;background:#171b20;padding:2px 8px;border-radius:4px;font-size:10px;font-family:'Space Mono',monospace}}
.streak-bar .n{{font-weight:700;color:#00c26f}}
.section-title{{font-size:11px;font-family:'Space Mono',monospace;color:#C9D1D9;text-transform:uppercase;letter-spacing:.1em;margin:1rem 0 8px;display:flex;align-items:center;gap:8px}}
.section-title::after{{content:'';flex:1;height:1px;background:#222830}}
.flag{{color:#f59e0b;font-size:10px;margin-left:4px}}
.tip{{display:inline-flex;align-items:center;justify-content:center;width:13px;height:13px;border-radius:50%;background:#222830;color:#9CA3AF;font-size:8px;cursor:help;margin-left:5px;font-family:sans-serif;font-weight:400;vertical-align:middle;line-height:1;font-style:normal;letter-spacing:0}}
.tip:hover{{background:#333a44;color:#F5F7FA}}
.sortable{{cursor:pointer}}
.sortable:hover{{color:#F5F7FA}}
.tk-click{{cursor:pointer;color:inherit;transition:color .15s}}
.tk-click:hover{{color:#93c5fd!important;text-decoration:underline}}
.overlay{{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.5);z-index:99;display:none}}
.overlay.show{{display:block}}
.panel{{position:fixed;top:0;right:-420px;width:400px;height:100vh;background:#161a20;border-left:1px solid #222830;z-index:100;overflow-y:auto;transition:right .25s ease;padding:0}}
.panel.show{{right:0}}
.panel-hdr{{display:flex;align-items:center;justify-content:space-between;padding:1rem 1.25rem;border-bottom:1px solid #222830;position:sticky;top:0;background:#161a20;z-index:2}}
.panel-hdr .tk{{font-size:16px;font-weight:700}}
.panel-hdr .name{{font-size:11px;color:#9CA3AF;font-family:'DM Sans',sans-serif;margin-top:2px}}
.panel-close{{background:transparent;border:none;color:#9CA3AF;font-size:18px;cursor:pointer;padding:4px 8px;border-radius:4px;font-family:'Space Mono',monospace}}
.panel-close:hover{{background:#222830;color:#F5F7FA}}
.panel-body{{padding:1rem 1.25rem}}
.panel-section{{margin-bottom:1.25rem}}
.panel-section-title{{font-size:9px;font-family:'Space Mono',monospace;color:#9CA3AF;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;font-weight:600}}
.panel-row{{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #1a1f26;font-size:12px}}
.panel-row:last-child{{border:none}}
.panel-label{{color:#9CA3AF}}
.panel-val{{font-family:'Space Mono',monospace;font-weight:600;color:#F5F7FA}}
.panel-status{{font-size:11px;padding:8px 12px;border-radius:4px;margin-bottom:8px;line-height:1.5}}
.panel-status.turnaround{{background:#0c1929;border:1px solid #1e3a5f;color:#60a5fa}}
.panel-status.exit{{background:#2a1111;border:1px solid #661111;color:#ef4444}}
.panel-status.portfolio{{background:#052e16;border:1px solid #166534;color:#00c26f}}
.panel-status.healthy{{background:#171b20;border:1px solid #222830;color:#9CA3AF}}
.fd-grid{{display:grid;grid-template-columns:1fr 1fr;gap:4px 12px}}
.fd-item{{display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #1a1f26;font-size:11px}}
.fd-item:nth-last-child(-n+2){{border:none}}
.fd-label{{color:#9CA3AF}}
.fd-val{{font-family:'Space Mono',monospace;font-weight:600;color:#F5F7FA}}
.fd-na{{color:#64748b;font-style:italic}}
.fi-good{{color:#00c26f}} .fi-warn{{color:#f59e0b}} .fi-bad{{color:#ef4444}}
.interp-box{{background:#12151a;border:1px solid #1a1f26;border-radius:6px;padding:10px 12px;margin-bottom:8px}}
.interp-row{{display:flex;justify-content:space-between;font-size:11px;padding:3px 0}}
.interp-label{{color:#9CA3AF}}
.interp-conclusion{{font-size:11px;color:#C9D1D9;line-height:1.5;padding:6px 0 0 0}}
.align-card{{padding:10px 12px;border-radius:6px;margin-bottom:8px;font-size:12px}}
.align-sejalan{{background:#052e16;border:1px solid #166534}}
.align-perhatian{{background:#2a2411;border:1px solid #665511}}
.align-konflik{{background:#2a1711;border:1px solid #663311}}
.align-turnaround{{background:#0c1929;border:1px solid #1e3a5f}}
.align-netral{{background:#171b20;border:1px solid #222830}}
.align-title{{font-weight:700;font-size:12px;margin-bottom:4px}}
.align-desc{{font-size:11px;color:#9CA3AF;line-height:1.5}}
.panel-bullet{{color:#9CA3AF;margin-right:6px}}
.panel-summary{{font-size:12px;color:#C9D1D9;line-height:1.6;padding:8px 0}}
.conc{{margin:0 1.5rem 4px;padding:12px 14px;background:#171b20;border:1px solid #222830;border-radius:8px}}
.conc-hdr{{display:flex;align-items:center;gap:10px;margin-bottom:8px}}
.conc-status{{font-size:10px;font-family:'Space Mono',monospace;font-weight:700;padding:3px 10px;border-radius:4px;text-transform:uppercase;letter-spacing:.08em}}
.conc-status.s-hijau{{background:#052e16;color:#00c26f;border:1px solid #166534}}
.conc-status.s-kuning{{background:#2a2411;color:#f59e0b;border:1px solid #665511}}
.conc-status.s-merah{{background:#2a1111;color:#ef4444;border:1px solid #661111}}
.conc-status.s-biru{{background:#0c1929;color:#60a5fa;border:1px solid #1e3a5f}}
.conc-label{{font-size:10px;font-family:'Space Mono',monospace;color:#9CA3AF;letter-spacing:.08em;font-weight:600}}
.conc-body{{display:flex;gap:16px;flex-wrap:wrap}}
.conc-col{{flex:1;min-width:200px}}
.conc-list{{list-style:none;padding:0;margin:0}}
.conc-list li{{font-size:11px;color:#C9D1D9;padding:2px 0 2px 12px;position:relative;line-height:1.5}}
.conc-list li::before{{content:'\2022';position:absolute;left:0;color:#00c26f}}
.insight-card{{background:#171b20;border:1px solid #222830;border-radius:8px;padding:10px 12px;margin-bottom:10px}}
.insight-hdr{{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;padding-bottom:4px;border-bottom:1px solid #1a1f26}}
.insight-title{{font-size:9px;font-family:'Space Mono',monospace;color:#C9D1D9;text-transform:uppercase;letter-spacing:.08em;font-weight:600}}
.insight-grid{{display:grid;grid-template-columns:1fr 1fr;gap:2px 14px}}
.insight-row{{display:flex;justify-content:space-between;padding:3px 0;font-size:11px;border-bottom:1px solid #1a1f26}}
.insight-row:last-child{{border:none}}
.insight-lbl{{color:#9CA3AF}}
.insight-val{{font-family:'Space Mono',monospace;font-weight:600;color:#F5F7FA}}
.insight-val.g{{color:#00c26f}}.insight-val.r{{color:#ef4444}}.insight-val.y{{color:#f59e0b}}.insight-val.b{{color:#60a5fa}}.insight-val.n{{color:#9CA3AF}}
.insight-badge{{font-size:9px;padding:1px 7px;border-radius:3px;font-family:'Space Mono',monospace;display:inline-block}}
.insight-badge.g{{background:#052e16;color:#00c26f;border:1px solid #166534}}
.insight-badge.y{{background:#2a2411;color:#f59e0b;border:1px solid #665511}}
.insight-badge.r{{background:#2a1111;color:#ef4444;border:1px solid #661111}}
.insight-badge.b{{background:#0c1929;color:#60a5fa;border:1px solid #1e3a5f}}
.insight-badge.n{{background:#171b20;color:#9CA3AF;border:1px solid #222830}}
.insight-note{{font-size:10px;color:#64748b;margin-top:5px;line-height:1.4;padding-top:4px;border-top:1px solid #1a1f26}}
.card-click{{cursor:pointer;transition:all .15s}}
.card-click:hover{{border-color:#00c26f;transform:translateY(-1px);box-shadow:0 2px 8px rgba(0,194,111,.08)}}
.card-click.active{{border-color:#00c26f;background:#0a1f14}}
.fltr-info{{display:none;margin-bottom:1rem;padding:10px 12px;background:#12151a;border:1px solid #1a1f26;border-radius:6px}}
.fltr-info.show{{display:block}}
.fltr-hdr{{font-size:9px;font-family:'Space Mono',monospace;color:#C9D1D9;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;font-weight:600;display:flex;align-items:center;justify-content:space-between}}
.fltr-close{{background:transparent;border:none;color:#9CA3AF;cursor:pointer;font-size:12px;font-family:'Space Mono',monospace}}
.fltr-close:hover{{color:#F5F7FA}}
.fltr-list{{display:flex;flex-wrap:wrap;gap:4px}}
.fltr-tag{{padding:3px 10px;background:#1a1e24;border:1px solid #222830;border-radius:4px;font-size:11px;font-family:'Space Mono',monospace;color:#F5F7FA}}
.fltr-tag:hover{{background:#222830}}
.toast{{position:fixed;background:#171b20;border:1px solid #222830;border-radius:8px;padding:10px 18px;font-size:12px;font-family:'Space Mono',monospace;color:#C9D1D9;z-index:200;display:none;max-width:90vw;box-shadow:0 4px 12px rgba(0,0,0,.4);line-height:1.6;white-space:pre-line}}
.toast.show{{display:block}}
</style>
</head>
<body>
<div class="hdr">
  <div class="logo">ISI <span>·</span> V2 <span>·</span> READ-ONLY DASHBOARD</div>
  <div class="dt">{report_date} · IDX30</div>
</div>
<div id="conclusion"></div>
<div class="tab-nav">
  <button class="tab-btn active" onclick="st(0)">01 · Leaders</button>
  <button class="tab-btn" onclick="st(1)">02 · Turnaround</button>
  <button class="tab-btn" onclick="st(2)">03 · Daily Summary</button>
  <button class="tab-btn" onclick="st(3)">04 · History</button>
  <button class="tab-btn" onclick="st(4)">05 · Diagnostics</button>
  <button class="tab-btn" onclick="st(5)">06 · Exit Monitor</button>
</div>

<div class="tc active" id="t0">
  <div class="section-title">Config B Leaders · Q25/G30/V10/M35</div>
  <div id="insight-leaders"></div>
  <div id="insight-top10"></div>
  <table>
    <thead><tr>
      <th data-key="rank">#</th><th data-key="ticker">Ticker</th><th data-key="final_score">Score</th><th data-key="quality">Quality</th><th data-key="growth">Growth</th><th data-key="value">Value</th><th data-key="momentum">Momentum</th><th>Status</th>
    </tr></thead>
    <tbody id="tbody-leaders"></tbody>
  </table>
</div>

<div class="tc" id="t1">
  <div class="section-title">Turnaround Watchlist · Context + Transition Signals</div>
  <div id="insight-turnaround"></div>
  <div style="margin-bottom:10px;display:flex;gap:6px;flex-wrap:wrap">
    <button class="tab-btn active" onclick="ft('all',this)" style="font-size:10px;padding:4px 12px">All</button>
    <button class="tab-btn" onclick="ft('full',this)" style="font-size:10px;padding:4px 12px">Full Match</button>
    <button class="tab-btn" onclick="ft('context',this)" style="font-size:10px;padding:4px 12px">Context Only</button>
    <button class="tab-btn" onclick="ft('transition',this)" style="font-size:10px;padding:4px 12px">Transition Only</button>
    <button class="tab-btn" onclick="ft('none',this)" style="font-size:10px;padding:4px 12px">No Signal</button>
  </div>
  <table>
    <thead><tr>
      <th>#</th><th data-key="ticker">Ticker</th><th data-key="drawdown_252d">Drawdown</th><th data-key="distance_from_high_252d">Dist High</th><th data-key="volatility_60d">Volatility</th><th data-key="rs_change_60d">RS Chg 60D</th><th data-key="volume_ratio">Vol Ratio</th><th data-key="recovery_from_60d_low">Recovery</th><th>Ctx</th><th>Trn</th>
    </tr></thead>
    <tbody id="tbody-turnaround"></tbody>
  </table>
</div>

<div class="tc" id="t2">
  <div class="section-title">Today's Snapshot</div>
  <div class="card-grid">
    <div class="card card-click" onclick="filterStocks('ctx','fltr-cards',this)"><div class="card-label">SAHAM TERTEKAN<span class="tip" onclick="showTip(event,this)" data-tip-key="ctx">?</span></div><div class="card-val g">{ctx_count}</div><div class="card-sub">Saham yang jatuh berat dan masih dalam kondisi tertekan</div></div>
    <div class="card card-click" onclick="filterStocks('trn','fltr-cards',this)"><div class="card-label">MULAI MEMBAIK<span class="tip" onclick="showTip(event,this)" data-tip-key="trn">?</span></div><div class="card-val y">{trn_count}</div><div class="card-sub">Saham dengan kekuatan relatif yang mulai meningkat</div></div>
    <div class="card card-click" onclick="filterStocks('full','fltr-cards',this)"><div class="card-label">KANDIDAT TURNAROUND<span class="tip" onclick="showTip(event,this)" data-tip-key="full">?</span></div><div class="card-val b">{full_count}</div><div class="card-sub">Saham tertekan yang mulai menunjukkan pemulihan</div></div>
    <div class="card"><div class="card-label">Universe</div><div class="card-val">{summary_data.get('universe_size', 0)}</div><div class="card-sub">IDX30 tickers</div></div>
  </div>
  <div class="fltr-info" id="fltr-cards"></div>
  <div class="section-title">Signal Diagnostics</div>
  <div class="card-grid">
    <div class="card card-click" onclick="filterStocks('rs-pos','fltr-sig',this)"><div class="card-label">KEKUATAN MULAI NAIK<span class="tip" onclick="showTip(event,this)" data-tip-key="rs-pos">?</span></div><div class="card-val g">{sig.get('rs_change_60d_positive_count', 0)}</div><div class="card-sub">Saham yang mulai outperform pasar</div></div>
    <div class="card card-click" onclick="filterStocks('vol-high','fltr-sig',this)"><div class="card-label">MINAT BELI MENINGKAT<span class="tip" onclick="showTip(event,this)" data-tip-key="vol-high">?</span></div><div class="card-val y">{sig.get('volume_ratio_high_count', 0)}</div><div class="card-sub">Aktivitas perdagangan di atas normal</div></div>
    <div class="card"><div class="card-label">DI ATAS TREND PENDEK<span class="tip" onclick="showTip(event,this)" data-tip-key="above-ma20">?</span></div><div class="card-val">{sig.get('above_ma20_count', 0)}</div><div class="card-sub">Harga di atas rata-rata 20 hari</div></div>
    <div class="card card-click" onclick="filterStocks('recovery','fltr-sig',this)"><div class="card-label">PANTUL DARI DASAR<span class="tip" onclick="showTip(event,this)" data-tip-key="recovery">?</span></div><div class="card-val g">{sig.get('recovery_gt_10pct_count', 0)}</div><div class="card-sub">Memantul &gt;10% dari level terendah 60 hari</div></div>
    <div class="card"><div class="card-label">RATA-RATA PENURUNAN<span class="tip" onclick="showTip(event,this)" data-tip-key="avg-dd">?</span></div><div class="card-val r">{sig.get('avg_drawdown_252d', 0)}%</div><div class="card-sub">Rata-rata penurunan dari harga tertinggi</div></div>
    <div class="card"><div class="card-label">RATA-RATA GEJOLAK<span class="tip" onclick="showTip(event,this)" data-tip-key="avg-vol">?</span></div><div class="card-val y">{sig.get('avg_volatility_60d', 0)}%</div><div class="card-sub">Intensitas pergerakan harga rata-rata</div></div>
  </div>
  <div class="fltr-info" id="fltr-sig"></div>
  <div class="section-title">Top Candidates</div>
  <table>
    <thead><tr>
      <th data-key="ticker">Ticker</th><th>Score</th><th data-key="drawdown">Drawdown</th><th data-key="distance_from_high">Dist High</th><th data-key="volatility">Volatility</th><th data-key="rs_change_60d">RS Chg 60D</th><th data-key="volume_ratio">Vol Ratio</th><th data-key="recovery">Recovery</th><th>Match</th>
    </tr></thead>
    <tbody id="tbody-top"></tbody>
  </table>
</div>

<div class="tc" id="t3">
  <div class="section-title">Candidate Persistence Tracking</div>
  <p style="font-size:11px;color:#64748b;margin-bottom:10px">Consecutive days each ticker has maintained context/transition match. Sorted by total active streak.</p>
  <table>
    <thead><tr>
      <th data-key="ticker">Ticker</th><th data-key="ctx_days">Context Streak</th><th data-key="trn_days">Transition Streak</th><th>First Detected (Ctx)</th><th>First Detected (Trn)</th><th data-key="total_entries">Total Days Tracked</th>
    </tr></thead>
    <tbody id="tbody-history"></tbody>
  </table>
</div>

<div class="tc" id="t4">
  <div class="section-title">Pipeline Diagnostics</div>
  <div class="card-grid">
    <div class="card wide-card">
      <div class="card-label">Pipeline Status</div>
      <div style="display:flex;align-items:center;gap:8px;margin-top:4px">
        <span style="width:8px;height:8px;border-radius:50%;background:#00c26f;display:inline-block"></span>
        <span style="font-size:14px;font-weight:600">OPERATIONAL</span>
      </div>
      <div class="card-sub">All systems nominal</div>
    </div>
    <div class="card"><div class="card-label">Last Leaders Update</div><div class="card-val" style="font-size:14px">{file_age(LEADERS_FILE, report_date)}</div><div class="card-sub">leaders_latest.csv</div></div>
    <div class="card"><div class="card-label">Last Turnaround Update</div><div class="card-val" style="font-size:14px">{file_age(TURNAROUND_FILE, report_date)}</div><div class="card-sub">turnaround_latest.csv</div></div>
    <div class="card"><div class="card-label">Last Exit Update</div><div class="card-val" style="font-size:14px">{file_age(EXIT_FILE, report_date)}</div><div class="card-sub">exit_watchlist_latest.csv</div></div>
    <div class="card"><div class="card-label">Records Processed</div><div class="card-val g">{summary_data.get('universe_size', 0)}</div><div class="card-sub">tickers in latest run</div></div>
    <div class="card"><div class="card-label">Data Freshness</div><div class="card-val g">{summary_data.get('date', 'N/A')}</div><div class="card-sub">report date</div></div>
    <div class="card"><div class="card-label">History Records</div><div class="card-val b">{len(history)}</div><div class="card-sub">turnaround_history.csv</div></div>
    <div class="card"><div class="card-label">Workflow</div><div class="card-val" style="font-size:13px">daily_radar.yml</div><div class="card-sub">cron: 30 9 * * * (16:30 WIB)</div></div>
  </div>
</div>

<div class="tc" id="t5">
  <div class="section-title">Exit Monitor · Rule-Based Exit Signals</div>
  <div style="margin-bottom:12px;background:#171b20;border:1px solid #222830;border-radius:6px;padding:10px 12px">
    <div style="font-size:9px;font-family:'Space Mono',monospace;color:#9CA3AF;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;font-weight:600">LEGENDA RULE EXIT</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 12px">
      <div style="font-size:11px"><span style="display:inline-block;background:#222830;color:#F5F7FA;border-radius:3px;padding:1px 5px;font-family:'Space Mono',monospace;font-weight:700;font-size:10px;margin-right:4px">A</span> Peringkat Turun (Rank &gt; 10)</div>
      <div style="font-size:11px"><span style="display:inline-block;background:#222830;color:#F5F7FA;border-radius:3px;padding:1px 5px;font-family:'Space Mono',monospace;font-weight:700;font-size:10px;margin-right:4px">B</span> Momentum Melemah (RS20 &lt; 0 &amp; RS Chg 20D &lt; 0)</div>
      <div style="font-size:11px"><span style="display:inline-block;background:#222830;color:#F5F7FA;border-radius:3px;padding:1px 5px;font-family:'Space Mono',monospace;font-weight:700;font-size:10px;margin-right:4px">C</span> Trend MA50 Rusak (Close &lt; MA50)</div>
      <div style="font-size:11px"><span style="display:inline-block;background:#222830;color:#F5F7FA;border-radius:3px;padding:1px 5px;font-family:'Space Mono',monospace;font-weight:700;font-size:10px;margin-right:4px">D</span> Pelemahan Terkonfirmasi (Close &lt; MA100 atau DD &gt; 15%)</div>
    </div>
  </div>
  <div id="insight-exit"></div>
  <div style="margin-bottom:10px;display:flex;gap:6px;flex-wrap:wrap">
    <button class="tab-btn active" onclick="ef('all',this)" style="font-size:10px;padding:4px 12px">All</button>
    <button class="tab-btn" onclick="ef('EXIT',this)" style="font-size:10px;padding:4px 12px;color:#ef4444">Exit</button>
    <button class="tab-btn" onclick="ef('EXIT RISK',this)" style="font-size:10px;padding:4px 12px;color:#f59e0b">Exit Risk</button>
    <button class="tab-btn" onclick="ef('WEAKENING',this)" style="font-size:10px;padding:4px 12px;color:#f97316">Weakening</button>
    <button class="tab-btn" onclick="ef('EXIT WATCH',this)" style="font-size:10px;padding:4px 12px;color:#60a5fa">Exit Watch</button>
    <button class="tab-btn" onclick="ef('HEALTHY',this)" style="font-size:10px;padding:4px 12px;color:#00c26f">Healthy</button>
  </div>
  <table>
    <thead><tr>
      <th data-key="ticker">Ticker</th><th data-key="rank">Rank</th><th data-key="rank_change">Rank Chg</th><th>Exit State</th><th>Rules</th><th data-key="rs_20d">RS20</th><th data-key="rs_change_20d">RS Chg 20D</th><th>vs MA50</th><th>vs MA100</th><th data-key="drawdown_from_entry">DD Entry</th>
    </tr></thead>
    <tbody id="tbody-exit"></tbody>
  </table>
</div>

<div class="overlay" id="overlay" onclick="closePanel()"></div>
<div class="panel" id="panel">
  <div class="panel-hdr">
    <div><div class="tk" id="ptk"></div><div class="name" id="pname"></div></div>
    <button class="panel-close" onclick="closePanel()">✕</button>
  </div>
  <div class="panel-body" id="pbody"></div>
</div>
<script>
const L={leaders_json};
const T={turnaround_json};
const SM={summary_json};
const SK={streaks_json};
const EX={exit_json};

function sc(v){{return v>=60?'high':v>=40?'mid':'low'}}
function bar(v,k){{return '<div class="bar"><div class="bar-track"><div class="bar-fill" style="width:'+Math.min(v,100)+'%;background:'+k+'"></div></div><span class="bv">'+v.toFixed(1)+'</span></div>'}}
function badge(v,t){{return v?'<span class="badge '+t+'">Yes</span>':'<span class="badge bg-gray">No</span>'}}
function pct(v){{return (v>0?'+':'')+v.toFixed(1)+'%'}}
function ctxLabel(r){{return r.context_match?'<span class="badge bg-green">YES</span>':'<span class="badge bg-gray">NO</span>'}}
function trnLabel(r){{return r.transition_match?'<span class="badge bg-yellow">YES</span>':'<span class="badge bg-gray">NO</span>'}}
function fullLabel(r){{return (r.context_match&&r.transition_match)?'<span class="badge bg-blue">FULL</span>':r.context_match?'<span class="badge bg-green">CTX</span>':r.transition_match?'<span class="badge bg-yellow">TRN</span>':'<span class="badge bg-gray">—</span>'}}
function ac(t){{
  var ld=null,td=null,ed=null,tk=t.indexOf('.JK')>0?t:t+'.JK'
  L.forEach(function(d){{if(d.ticker===tk)ld=d}})
  T.forEach(function(d){{if(d.ticker===tk)td=d}})
  EX.forEach(function(d){{if(d.ticker===tk)ed=d}})
  if(ld&&ld.rank<=10&&ed&&ed.exit_state==='HEALTHY')return'#00ff88'
  if(ld&&ld.rank<=10&&ed&&ed.exit_state==='EXIT RISK')return'#ffcc33'
  if(ld&&ld.rank<=10&&ed&&ed.exit_state==='EXIT')return'#ff5555'
  if(td&&td.context_match&&td.transition_match&&(!ed||ed.exit_state!=='EXIT'))return'#4da3ff'
  return'#cccccc'
}}

function sortData(d,s){{
  if(!s.key)return d
  return d.slice().sort(function(a,b){{
    var va=a[s.key],vb=b[s.key]
    if(typeof va==='string')return s.dir==='asc'?va.localeCompare(vb):vb.localeCompare(va)
    va=Number(va)||0;vb=Number(vb)||0
    return s.dir==='asc'?va-vb:vb-va
  }})
}}
function makeSortable(id,s,fn){{
  var ths=document.getElementById(id).closest('table').querySelectorAll('th[data-key]')
  ths.forEach(function(th){{
    th.addEventListener('click',function(){{
      var k=th.getAttribute('data-key')
      ths.forEach(function(t){{t.innerHTML=t.innerHTML.replace(/ ?[▲▼]$/,'')}})
      if(s.key===k){{s.dir=s.dir==='asc'?'desc':'asc';if(s.dir==='asc'){{s.key=null}}}}
      else{{s.key=k;s.dir='asc'}}
      if(s.key){{th.innerHTML+=s.dir==='asc'?' ▲':' ▼'}}
      fn()
    }})
  }})
}}

(function(){{
  var full=L;var s={{key:null,dir:'asc'}}
  function render(d){{
    document.getElementById('tbody-leaders').innerHTML=d.map(function(r){{
      return '<tr><td class="tk" style="color:#9CA3AF;font-size:11px">'+r.rank+'</td><td class="tk tk-click" data-ticker="'+r.ticker.split('.')[0]+'" style="color:'+ac(r.ticker)+'">'+r.ticker.split('.')[0]+(r.rank<=5?'<span class="flag">★</span>':'')+'</td><td class="sf '+sc(r.final_score)+'">'+r.final_score.toFixed(1)+'</td><td>'+bar(r.quality,'#3b82f6')+'</td><td>'+bar(r.growth,'#10b981')+'</td><td>'+bar(r.value,'#a855f7')+'</td><td>'+bar(r.momentum,'#f59e0b')+'</td><td></td></tr>'
    }}).join('')
  }}
  function refresh(){{render(sortData(full,s))}}
  refresh()
  makeSortable('tbody-leaders',s,refresh)
}})();

(function(){{
  var full=T;var f='all';var s={{key:null,dir:'asc'}}
  function filtered(){{
    if(f==='all')return full
    if(f==='full')return full.filter(function(d){{return d.context_match&&d.transition_match}})
    if(f==='context')return full.filter(function(d){{return d.context_match&&!d.transition_match}})
    if(f==='transition')return full.filter(function(d){{return !d.context_match&&d.transition_match}})
    return full.filter(function(d){{return !d.context_match&&!d.transition_match}})
  }}
  function render(d){{
    document.getElementById('tbody-turnaround').innerHTML=d.map(function(r,i){{
      return '<tr><td style="color:#9CA3AF;font-size:11px;font-family:monospace">'+(i+1)+'</td><td class="tk tk-click" data-ticker="'+r.ticker.split('.')[0]+'" style="color:'+ac(r.ticker)+'">'+r.ticker.split('.')[0]+'</td><td class="sf '+(r.drawdown_252d<-25?'low':r.drawdown_252d<-10?'mid':'high')+'">'+pct(r.drawdown_252d)+'</td><td class="sf '+(r.distance_from_high_252d<-20?'low':r.distance_from_high_252d<-5?'mid':'high')+'">'+pct(r.distance_from_high_252d)+'</td><td>'+r.volatility_60d.toFixed(2)+'%</td><td class="sf '+(r.rs_change_60d>0?'high':'low')+'">'+pct(r.rs_change_60d)+'</td><td>'+r.volume_ratio.toFixed(2)+'x</td><td>'+pct(r.recovery_from_60d_low)+'</td><td>'+ctxLabel(r)+'</td><td>'+trnLabel(r)+'</td></tr>'
    }}).join('')
  }}
  function refresh(){{render(sortData(filtered(),s))}}
  refresh()
  makeSortable('tbody-turnaround',s,refresh)
  window.ft=function(v,b){{f=v;document.querySelectorAll('#t1 .tab-btn').forEach(function(x){{x.classList.remove('active')}});b.classList.add('active');refresh()}}
}})();

(function(){{
  var full=SM.top_candidates||[];var s={{key:null,dir:'asc'}}
  function render(d){{
    document.getElementById('tbody-top').innerHTML=d.map(function(r){{
      return '<tr><td class="tk tk-click" data-ticker="'+r.ticker.split('.')[0]+'" style="color:'+ac(r.ticker)+'">'+r.ticker.split('.')[0]+'</td><td class="sf high">'+(r.full_match?'FULL':r.context_match?'CTX':'TRN')+'</td><td class="sf low">'+pct(r.drawdown)+'</td><td class="sf low">'+pct(r.distance_from_high)+'</td><td>'+r.volatility.toFixed(2)+'%</td><td class="sf '+(r.rs_change_60d>0?'high':'low')+'">'+pct(r.rs_change_60d)+'</td><td>'+r.volume_ratio.toFixed(2)+'x</td><td>'+pct(r.recovery)+'</td><td>'+fullLabel(r)+'</td></tr>'
    }}).join('')
  }}
  function refresh(){{render(sortData(full,s))}}
  refresh()
  makeSortable('tbody-top',s,refresh)
}})();

(function(){{
  var full=SK;var s={{key:null,dir:'asc'}}
  function render(){{
    var keys=Object.keys(full)
    if(s.key){{
      keys=keys.slice().sort(function(a,b){{
        var va=full[a][s.key],vb=full[b][s.key]
        if(typeof va==='string')return s.dir==='asc'?va.localeCompare(vb):vb.localeCompare(va)
        return(Number(va)||0)-(Number(vb)||0)
      }})
    }}else{{
      keys=keys.slice().sort(function(a,b){{return(full[b].ctx_days+full[b].trn_days)-(full[a].ctx_days+full[a].trn_days)}})
    }}
    document.getElementById('tbody-history').innerHTML=keys.map(function(t){{
      var d=full[t]
      return '<tr><td class="tk tk-click" data-ticker="'+t.split('.')[0]+'" style="color:'+ac(t)+'">'+t.split('.')[0]+'</td><td>'+(d.ctx_days>0?'<span class="streak-bar"><span class="n">'+d.ctx_days+'</span>d</span>':'<span class="badge bg-gray">0d</span>')+'</td><td>'+(d.trn_days>0?'<span class="streak-bar"><span class="n" style="color:#f59e0b">'+d.trn_days+'</span>d</span>':'<span class="badge bg-gray">0d</span>')+'</td><td style="font-family:monospace;font-size:11px;color:#9CA3AF">'+d.first_ctx+'</td><td style="font-family:monospace;font-size:11px;color:#9CA3AF">'+d.first_trn+'</td><td style="font-family:monospace;font-size:11px;color:#9CA3AF">'+d.total_entries+' days</td></tr>'
    }}).join('')
  }}
  render()
  makeSortable('tbody-history',s,render)
}})();

(function(){{
  var full=EX;var f='all';var s={{key:null,dir:'asc'}}
  function filtered(){{return f==='all'?full:full.filter(function(d){{return d.exit_state===f}})}}
  function render(d){{
    document.getElementById('tbody-exit').innerHTML=d.map(function(r){{
      var sc=r.exit_state==='EXIT'?'bg-red':r.exit_state==='EXIT RISK'?'bg-yellow':r.exit_state==='WEAKENING'?'bg-yellow':r.exit_state==='EXIT WATCH'?'bg-blue':'bg-green'
      var rc=r.rs_20d>0?'sf high':'sf low'
      var rcc=r.rs_change_20d>0?'sf high':'sf low'
      var m50=r.close<r.ma50?'<span class="badge bg-red">DI BAWAH</span>':'<span class="badge bg-green">DI ATAS</span>'
      var m100=r.close<r.ma100?'<span class="badge bg-red">DI BAWAH</span>':'<span class="badge bg-green">DI ATAS</span>'
      var dd=r.drawdown_from_entry<-15?'sf low':'sf high'
      var rc2=r.rank_change>0?'<span class="sf high">+'+r.rank_change+'</span>':r.rank_change<0?'<span class="sf low">'+r.rank_change+'</span>':'<span style="color:#9CA3AF">0</span>'
      return '<tr><td class="tk tk-click" data-ticker="'+r.ticker.split('.')[0]+'" style="color:'+ac(r.ticker)+'">'+r.ticker.split('.')[0]+'</td><td style="font-family:monospace;font-size:12px;color:#9CA3AF">#'+r.rank+'</td><td style="font-family:monospace;font-size:12px">'+rc2+'</td><td><span class="badge '+sc+'">'+r.exit_state+'</span></td><td style="font-family:monospace;font-size:11px;color:#9CA3AF" title="'+r.triggered_rules.replace(/A/g,'A: Peringkat Turun').replace(/B/g,'B: Momentum Melemah').replace(/C/g,'C: Trend MA50 Rusak').replace(/D/g,'D: Pelemahan Terkonfirmasi')+'">'+r.triggered_rules+'</td><td class="'+rc+'">'+r.rs_20d.toFixed(1)+'%</td><td class="'+rcc+'">'+r.rs_change_20d.toFixed(1)+'%</td><td>'+m50+'</td><td>'+m100+'</td><td class="'+dd+'">'+r.drawdown_from_entry.toFixed(1)+'%</td></tr>'
    }}).join('')
  }}
  function refresh(){{render(sortData(filtered(),s))}}
  refresh()
  makeSortable('tbody-exit',s,refresh)
  window.ef=function(v,b){{f=v;document.querySelectorAll('#t5 .tab-btn').forEach(function(x){{x.classList.remove('active')}});b.classList.add('active');refresh()}}
}})();

function st(i){{document.querySelectorAll('.tab-btn').forEach(function(b,j){{b.classList.toggle('active',j===i)}});document.querySelectorAll('.tc').forEach(function(t,j){{t.classList.toggle('active',j===i)}})}}

const PF={profiles_json};
const FD={fundamentals_json};

/* KESIMPULAN AI — from Gemini via daily_radar_status.json */
const RADAR_STATUS='{radar_status_escaped}';
const RADAR_LABEL='{radar_status_label}';
(function(){{
  var c=RADAR_LABEL==='SAFE'?'s-hijau':RADAR_LABEL==='CAUTION'?'s-kuning':'s-merah'
  var h='<div class="conc"><div class="conc-hdr"><span class="conc-status '+c+'">'+RADAR_LABEL+'</span><span class="conc-label">KESIMPULAN AI — GEMINI</span></div><div class="conc-body"><div class="conc-col" style="min-width:100%"><div style="font-size:12px;color:#C9D1D9;line-height:1.6;padding:4px 0">'+RADAR_STATUS+'</div></div></div></div>'
  document.getElementById('conclusion').innerHTML=h
}})();

/* INSIGHT — Leaders Analysis */
(function(){{
  var n=L.length
  if(n===0){{document.getElementById('insight-leaders').innerHTML='';return}}
  var top5=L.filter(function(d){{return d.rank<=5}})
  var bot5=L.filter(function(d){{return d.rank>n-5}})
  var factors=['quality','growth','value','momentum']
  var avg=function(arr,k){{return arr.reduce(function(s,d){{return s+d[k]}},0)/arr.length}}
  var t5=factors.map(function(f){{return{{name:f,val:avg(top5,f)}}}})
  var allTop5Avg=t5.reduce(function(s,f){{return s+f.val}},0)/4
  var allBot5Avg=factors.reduce(function(s,f){{return s+avg(bot5,f)}},0)/4
  var gap=allTop5Avg-allBot5Avg
  var strongest=t5.slice().sort(function(a,b){{return b.val-a.val}})[0]
  var weakest=factors.map(function(f){{return{{name:f,val:avg(bot5,f)}}}}).sort(function(a,b){{return a.val-b.val}})[0]
  var h='<div class="insight-card"><div class="insight-hdr"><span class="insight-title">Analisis Leaders</span><span class="insight-badge '+(gap>30?'r':gap>15?'y':'n')+'">Gap Top5–Bot5: '+gap.toFixed(1)+'</span></div><div class="insight-grid">'
  h+='<div class="insight-row"><span class="insight-lbl">Rerata Top 5</span><span class="insight-val g">'+allTop5Avg.toFixed(1)+'</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">Faktor Terkuat Top5</span><span class="insight-val g">'+strongest.name.charAt(0).toUpperCase()+strongest.name.slice(1)+' ('+strongest.val.toFixed(1)+')</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">Rerata Bottom 5</span><span class="insight-val r">'+allBot5Avg.toFixed(1)+'</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">Faktor Terlemah Bot5</span><span class="insight-val r">'+weakest.name.charAt(0).toUpperCase()+weakest.name.slice(1)+' ('+weakest.val.toFixed(1)+')</span></div>'
  h+='</div><div class="insight-note">Kesenjangan '+gap.toFixed(1)+' poin — '+(gap>30?'distribusi sangat timpang, dominasi saham unggulan kuat':gap>15?'distribusi cukup timpang, pemimpin pasar jelas':gap>5?'distribusi moderat, persaingan merata':'pasar relatif homogen, banyak saham setara')+'</div></div>'
  document.getElementById('insight-leaders').innerHTML=h
}})();

/* INSIGHT — Top 10 Ringkasan */
(function(){{
  var top10=L.filter(function(d){{return d.rank<=10}})
  var n=top10.length
  if(n===0){{document.getElementById('insight-top10').innerHTML='';return}}
  var sectors={{}}
  top10.forEach(function(d){{
    var p=PF[d.ticker.split('.')[0]]
    if(p){{var sec=p.sector;sectors[sec]=(sectors[sec]||0)+1}}
  }})
  var secList=Object.keys(sectors).sort(function(a,b){{return sectors[b]-sectors[a]}})
  var avg=function(k){{return top10.reduce(function(s,d){{return s+d[k]}},0)/n}}
  var h='<div class="insight-card"><div class="insight-hdr"><span class="insight-title">Top 10 Ringkasan</span><span class="insight-badge b">'+n+' saham</span></div><div class="insight-grid">'
  h+='<div class="insight-row"><span class="insight-lbl">Rerata Score</span><span class="insight-val">'+avg('final_score').toFixed(1)+'</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">Quality / Growth</span><span class="insight-val">'+avg('quality').toFixed(1)+' / '+avg('growth').toFixed(1)+'</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">Value / Momentum</span><span class="insight-val">'+avg('value').toFixed(1)+' / '+avg('momentum').toFixed(1)+'</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">Sektor Dominan</span><span class="insight-val">'+secList[0]+' ('+sectors[secList[0]]+')</span></div>'
  h+='</div>'
  if(secList.length>1){{
    h+='<div class="insight-note">Sektor: '+secList.map(function(s){{return s+' ('+sectors[s]+')'}}).join(' · ')+'</div>'
  }}
  h+='</div>'
  document.getElementById('insight-top10').innerHTML=h
}})();

/* INSIGHT — Turnaround Analysis */
(function(){{
  var full=T.length
  if(full===0){{document.getElementById('insight-turnaround').innerHTML='';return}}
  var fullMatch=T.filter(function(d){{return d.context_match&&d.transition_match}}).length
  var ctxOnly=T.filter(function(d){{return d.context_match&&!d.transition_match}}).length
  var trnOnly=T.filter(function(d){{return !d.context_match&&d.transition_match}}).length
  var none=full-fullMatch-ctxOnly-trnOnly
  var avgDD=T.reduce(function(s,d){{return s+d.drawdown_252d}},0)/full
  var avgRec=T.reduce(function(s,d){{return s+d.recovery_from_60d_low}},0)/full
  var avgVol=T.reduce(function(s,d){{return s+d.volatility_60d}},0)/full
  var rsPos=T.filter(function(d){{return d.rs_change_60d>0}}).length
  var h='<div class="insight-card"><div class="insight-hdr"><span class="insight-title">Analisis Turnaround</span><span class="insight-badge b">'+full+' ticker</span></div><div class="insight-grid">'
  h+='<div class="insight-row"><span class="insight-lbl">Full Match</span><span class="insight-val g">'+fullMatch+'</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">Context Only</span><span class="insight-val y">'+ctxOnly+'</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">Transition Only</span><span class="insight-val b">'+trnOnly+'</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">No Signal</span><span class="insight-val n">'+none+'</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">RS Positive</span><span class="insight-val '+(rsPos>full/2?'g':'r')+'">'+rsPos+'/'+full+'</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">Rerata DD 252d</span><span class="insight-val r">'+avgDD.toFixed(1)+'%</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">Rerata Recovery</span><span class="insight-val '+(avgRec>5?'g':avgRec>0?'y':'r')+'">'+avgRec.toFixed(1)+'%</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">Rerata Vol 60d</span><span class="insight-val '+(avgVol>4?'r':avgVol>3?'y':'g')+'">'+avgVol.toFixed(2)+'%</span></div>'
  h+='</div></div>'
  document.getElementById('insight-turnaround').innerHTML=h
}})();

/* INSIGHT — Exit Analysis */
(function(){{
  var total=EX.length
  if(total===0){{document.getElementById('insight-exit').innerHTML='';return}}
  var exitCount=EX.filter(function(d){{return d.exit_state==='EXIT'}}).length
  var exitRiskCount=EX.filter(function(d){{return d.exit_state==='EXIT RISK'}}).length
  var weakenCount=EX.filter(function(d){{return d.exit_state==='WEAKENING'}}).length
  var watchCount=EX.filter(function(d){{return d.exit_state==='EXIT WATCH'}}).length
  var healthyCount=EX.filter(function(d){{return d.exit_state==='HEALTHY'}}).length
  var avgRS20=EX.reduce(function(s,d){{return s+d.rs_20d}},0)/total
  var avgRSchg=EX.reduce(function(s,d){{return s+d.rs_change_20d}},0)/total
  var ruleCount={{}}
  EX.forEach(function(d){{
    if(d.triggered_rules){{
      d.triggered_rules.split(', ').forEach(function(r){{
        ruleCount[r]=(ruleCount[r]||0)+1
      }})
    }}
  }})
  var ruleList=Object.keys(ruleCount).sort(function(a,b){{return ruleCount[b]-ruleCount[a]}})
  var topRule=ruleList[0]||'—'
  var h='<div class="insight-card"><div class="insight-hdr"><span class="insight-title">Analisis Exit</span><span class="insight-badge '+(exitCount>=3?'r':exitCount>0?'y':'g')+'">'+exitCount+' EXIT</span></div><div class="insight-grid">'
  h+='<div class="insight-row"><span class="insight-lbl">EXIT</span><span class="insight-val r">'+exitCount+'</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">EXIT RISK</span><span class="insight-val y">'+exitRiskCount+'</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">WEAKENING</span><span class="insight-val y">'+weakenCount+'</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">WATCH / HEALTHY</span><span class="insight-val g">'+watchCount+' / '+healthyCount+'</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">Rerata RS20</span><span class="insight-val '+(avgRS20>0?'g':'r')+'">'+avgRS20.toFixed(1)+'%</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">Rerata RS Chg 20D</span><span class="insight-val '+(avgRSchg>0?'g':'r')+'">'+avgRSchg.toFixed(1)+'%</span></div>'
  h+='<div class="insight-row"><span class="insight-lbl">Rule Terbanyak</span><span class="insight-val">'+topRule+' ('+ruleCount[topRule]+'x)</span></div>'
  h+='</div></div>'
  document.getElementById('insight-exit').innerHTML=h
}})();

function tickerData(t){{
  var ld=null,td=null,ed=null
  L.forEach(function(d){{if(d.ticker===t||d.ticker===t+'.JK')ld=d}})
  T.forEach(function(d){{if(d.ticker===t||d.ticker===t+'.JK')td=d}})
  EX.forEach(function(d){{if(d.ticker===t||d.ticker===t+'.JK')ed=d}})
  return{{leader:ld,turnaround:td,exit:ed,profile:PF[t]||PF[t+'.JK']||null,fundamentals:FD[t+'.JK']||null}}
}}

function aiExplain(leaderData,turnaroundData,exitData){{
  var lines=[]
  if(turnaroundData&&turnaroundData.context_match&&turnaroundData.transition_match){{
    lines.push('<div class="panel-status turnaround"><b>KANDIDAT TURNAROUND</b>')
    lines.push('<div style="margin-top:6px;font-size:11px;color:#9CA3AF;font-weight:400">')
    if(turnaroundData.drawdown_252d<-20)lines.push('<span class="panel-bullet">&#8226;</span>Deep drawdown')
    if(turnaroundData.distance_from_high_252d<-15)lines.push('<span class="panel-bullet">&#8226;</span>Far from previous high')
    if(turnaroundData.rs_change_60d>0)lines.push('<span class="panel-bullet">&#8226;</span>Improving RS60')
    if(turnaroundData.volume_ratio>1.3)lines.push('<span class="panel-bullet">&#8226;</span>Elevated volume')
    if(turnaroundData.recovery_from_60d_low>5)lines.push('<span class="panel-bullet">&#8226;</span>Pemulihan dari dasar')
    lines.push('</div></div>')
    lines.push('<div style="font-size:11px;color:#64748b;margin-top:6px;line-height:1.5">Stock remains high risk but shows early signs of accumulation.</div>')
    return lines.join('')
  }}
  if(exitData&&exitData.exit_state==='EXIT'){{
    lines.push('<div class="panel-status exit"><b>SINYAL EXIT AKTIF</b>')
    lines.push('<div style="margin-top:6px;font-size:11px;color:#9CA3AF;font-weight:400">')
    lines.push('<span class="panel-bullet">&#8226;</span>Exit state: '+exitData.exit_state)
    lines.push('<span class="panel-bullet">&#8226;</span>Rules: '+exitData.triggered_rules)
    lines.push('</div></div>')
    lines.push('<div style="font-size:11px;color:#64748b;margin-top:6px;line-height:1.5">Stock shows sustained weakness across multiple indicators.</div>')
    return lines.join('')
  }}
  if(leaderData&&leaderData.rank<=5){{
    lines.push('<div class="panel-status portfolio"><b>PORTOFOLIO AKTIF</b>')
    lines.push('<div style="margin-top:6px;font-size:11px;color:#9CA3AF;font-weight:400">')
    lines.push('<span class="panel-bullet">&#8226;</span>Top 5 in Config B ranking')
    lines.push('<span class="panel-bullet">&#8226;</span>Saat ini masuk portofolio')
    lines.push('</div></div>')
    return lines.join('')
  }}
    lines.push('<div class="panel-status healthy"><b>PEMANTAUAN</b></div>')
  return lines.join('')
}}

function renderFundamentals(fd){{
  if(!fd) return ''
  function fmtMarketCap(v){{
    if(v===null||v===undefined) return 'Tidak tersedia'
    var t=v/1e12
    if(t<1) return Math.round(v/1e9)+' B'
    if(t<10) return t.toFixed(1)+' T'
    return Math.round(t).toLocaleString('id-ID')+' T'
  }}
  var html=''
  html+='<div class="panel-section"><div class="panel-section-title">FUNDAMENTAL SNAPSHOT</div>'
  html+='<div class="fd-grid">'
  function fmt(l,v,u){{
    if(v===null||v===undefined) return '<div class="fd-item"><span class="fd-label">'+l+'</span><span class="fd-na">Tidak tersedia</span></div>'
    var f=Number(v)
    if(u==='%') return '<div class="fd-item"><span class="fd-label">'+l+'</span><span class="fd-val">'+(f*100).toFixed(1)+'%</span></div>'
    if(u==='dy') return '<div class="fd-item"><span class="fd-label">'+l+'</span><span class="fd-val">'+f.toFixed(1)+'%</span></div>'
    if(u==='x') return '<div class="fd-item"><span class="fd-label">'+l+'</span><span class="fd-val">'+f.toFixed(1)+'x</span></div>'
    if(u==='mc') return '<div class="fd-item"><span class="fd-label">'+l+'</span><span class="fd-val">'+fmtMarketCap(f)+'</span></div>'
    return '<div class="fd-item"><span class="fd-label">'+l+'</span><span class="fd-val">'+f.toFixed(1)+'</span></div>'
  }}
  html+=fmt('ROE',fd.roe,'%')
  html+=fmt('ROA',fd.roa,'%')
  html+=fmt('PER',fd.pe_ratio,'x')
  html+=fmt('PBV',fd.pb_ratio,'x')
  html+=fmt('EPS Growth',fd.earnings_growth,'%')
  html+=fmt('Revenue Growth',fd.revenue_growth,'%')
  html+=fmt('DER',fd.debt_to_equity,'x')
  html+=fmt('Dividend Yield',fd.dividend_yield,'dy')
  html+=fmt('Market Cap',fd.market_cap,'mc')
  html+='</div></div>'
  html+='<div class="panel-section"><div class="panel-section-title">INTERPRETASI SEDERHANA</div>'
  html+='<div class="interp-box">'
  var roe=fd.roe!==null&&fd.roe!==undefined?fd.roe:null
  var pl=roe===null?'Tidak tersedia':roe>0.20?'Tinggi':roe>0.10?'Sedang':'Rendah'
  html+='<div class="interp-row"><span class="interp-label">Profitabilitas</span><span class="fd-val">'+pl+'</span></div>'
  var pe=fd.pe_ratio!==null&&fd.pe_ratio!==undefined?fd.pe_ratio:null
  var pb=fd.pb_ratio!==null&&fd.pb_ratio!==undefined?fd.pb_ratio:null
  var vl=pe===null?'Tidak tersedia':pe<10?'Murah':pe<20?'Sedang':'Mahal'
  html+='<div class="interp-row"><span class="interp-label">Valuasi</span><span class="fd-val">'+vl+'</span></div>'
  var rev=fd.revenue_growth!==null&&fd.revenue_growth!==undefined?fd.revenue_growth:null
  var eps=fd.earnings_growth!==null&&fd.earnings_growth!==undefined?fd.earnings_growth:null
  if(rev===null&&eps===null) var gl='Tidak tersedia'; else{{
    var ag=0,ac=0
    if(rev!==null){{ag+=rev;ac++}}
    if(eps!==null){{ag+=eps;ac++}}
    ag/=ac
    var gl=ag>0.10?'Tinggi':ag>=0?'Sedang':'Negatif'
  }}
  html+='<div class="interp-row"><span class="interp-label">Pertumbuhan</span><span class="fd-val">'+gl+'</span></div>'
  var der=fd.debt_to_equity!==null&&fd.debt_to_equity!==undefined?fd.debt_to_equity:null
  var dl=der===null?'Tidak tersedia':der<0.5?'Rendah':der<1.5?'Sedang':'Tinggi'
  html+='<div class="interp-row"><span class="interp-label">Utang</span><span class="fd-val">'+dl+'</span></div>'
  var mc=fd.market_cap!==null&&fd.market_cap!==undefined?fd.market_cap:null
  var szl=mc===null?'Tidak tersedia':mc>=1e14?'Large Cap':mc>=1e13?'Mid Cap':'Small Cap'
  html+='<div class="interp-row"><span class="interp-label">Ukuran Perusahaan</span><span class="fd-val">'+szl+'</span></div>'
  var cc='Perusahaan ini memiliki '
  cc+=pl==='Tinggi'?'profitabilitas yang kuat':pl==='Sedang'?'profitabilitas yang cukup baik':'profitabilitas yang rendah'
  cc+=', '
  cc+=vl==='Murah'?'valuasi yang relatif murah':vl==='Sedang'?'valuasi yang wajar':'valuasi yang relatif mahal'
  cc+=', dengan '
  cc+=gl==='Tinggi'?'pertumbuhan yang tinggi':gl==='Sedang'?'pertumbuhan yang stabil':gl==='Negatif'?'pertumbuhan yang negatif':'data pertumbuhan tidak tersedia'
  cc+='. '
  cc+='Perusahaan ini tergolong '+szl.toLowerCase()+'.'
  html+='<div class="interp-conclusion">'+cc+'</div>'
  html+='</div></div>'
  return html
}}

function renderAlignment(ld,td,ed){{
  var state='netral',label='NETRAL',icon='&#9898;',cls='align-netral',desc='Tidak ada sinyal dominan dari sistem.'
  if(ld&&ld.rank<=10&&ed&&ed.exit_state==='HEALTHY'){{state='sejalan';label='SEJALAN';icon='&#128994;';cls='align-sejalan';desc='Fundamental dan tren harga sejalan.'}}
  else if(ld&&ld.rank<=10&&ed&&ed.exit_state==='EXIT RISK'){{state='perhatian';label='PERLU PERHATIAN';icon='&#128993;';cls='align-perhatian';desc='Fundamental masih kuat dan masuk portofolio, tetapi tren harga belum sepenuhnya pulih.'}}
  else if(ld&&ld.rank<=10&&ed&&ed.exit_state==='EXIT'){{state='konflik';label='KONFLIK';icon='&#128992;';cls='align-konflik';desc='Perusahaan masih berada di peringkat atas Config B, namun Exit Layer mendeteksi pelemahan momentum. Perlu pemantauan tambahan sebelum mengambil keputusan.'}}
  else if(td&&td.context_match&&td.transition_match&&(!ed||ed.exit_state!=='EXIT')){{state='turnaround';label='TURNAROUND';icon='&#128309;';cls='align-turnaround';desc='Masuk kandidat turnaround dengan tanda pemulihan yang mulai muncul.'}}
  var html='<div class="panel-section"><div class="panel-section-title">STATUS KESELARASAN</div>'
  html+='<div class="align-card '+cls+'">'
  html+='<div class="align-title">'+icon+' '+label+'</div>'
  html+='<div class="align-desc">'+desc+'</div>'
  html+='</div></div>'
  return html
}}

function openPanel(ticker){{
  var d=tickerData(ticker)
  document.getElementById('ptk').textContent=ticker
  document.getElementById('pname').textContent=d.profile?(d.profile.name+' &middot; '+d.profile.sector):ticker+'.JK'
  var html=''
  // Status explanation
  html+=aiExplain(d.leader,d.turnaround,d.exit)
  // Company summary
  if(d.profile&&d.profile.summary){{
    html+='<div class="panel-section"><div class="panel-section-title">TENTANG PERUSAHAAN</div>'
    html+='<div class="panel-summary">'+d.profile.summary+'</div></div>'
  }}
  // Fundamental snapshot
  html+=renderFundamentals(d.fundamentals)
  // Dashboard state
  html+='<div class="panel-section"><div class="panel-section-title">STATUS DASHBOARD</div>'
  if(d.leader)html+='<div class="panel-row"><span class="panel-label">Peringkat Leader</span><span class="panel-val">#'+d.leader.rank+'</span></div>'
  if(d.turnaround){{html+='<div class="panel-row"><span class="panel-label">Status Turnaround</span><span class="panel-val">'+(d.turnaround.context_match?'Context':'—')+(d.turnaround.transition_match?' / Transition':'')+'</span></div>'}}
  if(d.exit)html+='<div class="panel-row"><span class="panel-label">Status Exit</span><span class="panel-val">'+d.exit.exit_state+'</span></div>'
  html+='</div>'
  // Signal alignment
  html+=renderAlignment(d.leader,d.turnaround,d.exit)
  // Price & trend
  if(d.turnaround||d.exit){{
    html+='<div class="panel-section"><div class="panel-section-title">HARGA &amp; TREN</div>'
    if(d.exit)html+='<div class="panel-row"><span class="panel-label">Harga Terakhir</span><span class="panel-val">'+d.exit.close+'</span></div>'
    if(d.turnaround){{html+='<div class="panel-row"><span class="panel-label">Penurunan dari Puncak</span><span class="panel-val sf low">'+pct(d.turnaround.drawdown_252d)+'</span></div>'}}
    if(d.turnaround){{html+='<div class="panel-row"><span class="panel-label">Jarak dari Harga Tertinggi</span><span class="panel-val sf low">'+pct(d.turnaround.distance_from_high_252d)+'</span></div>'}}
    if(d.turnaround){{html+='<div class="panel-row"><span class="panel-label">Pemulihan dari Dasar</span><span class="panel-val sf '+(d.turnaround.recovery_from_60d_low>0?'high':'low')+'">'+pct(d.turnaround.recovery_from_60d_low)+'</span></div>'}}
    if(d.turnaround){{html+='<div class="panel-row"><span class="panel-label">Volatilitas 60 Hari</span><span class="panel-val">'+d.turnaround.volatility_60d.toFixed(2)+'%</span></div>'}}
    html+='</div>'
  }}
  // Relative strength
  if(d.exit||d.turnaround){{
    html+='<div class="panel-section"><div class="panel-section-title">KEKUATAN RELATIF</div>'
    if(d.exit){{html+='<div class="panel-row"><span class="panel-label">RS20</span><span class="panel-val sf '+(d.exit.rs_20d>0?'high':'low')+'">'+d.exit.rs_20d.toFixed(1)+'%</span></div>'}}
    if(d.exit){{html+='<div class="panel-row"><span class="panel-label">RS Change 20D</span><span class="panel-val sf '+(d.exit.rs_change_20d>0?'high':'low')+'">'+d.exit.rs_change_20d.toFixed(1)+'%</span></div>'}}
    if(d.turnaround){{html+='<div class="panel-row"><span class="panel-label">RS Change 60D</span><span class="panel-val sf '+(d.turnaround.rs_change_60d>0?'high':'low')+'">'+pct(d.turnaround.rs_change_60d)+'</span></div>'}}
    html+='</div>'
  }}
  // Trend status
  if(d.exit){{
    html+='<div class="panel-section"><div class="panel-section-title">POSISI TERHADAP MA</div>'
    html+='<div class="panel-row"><span class="panel-label">vs MA20</span><span class="panel-val">'+(d.exit.ma20!=null?(d.exit.close<d.exit.ma20?'<span style="color:#ef4444">DI BAWAH</span>':'<span style="color:#00c26f">DI ATAS</span>'):'—')+'</span></div>'
    html+='<div class="panel-row"><span class="panel-label">vs MA50</span><span class="panel-val">'+(d.exit.ma50!=null?(d.exit.close<d.exit.ma50?'<span style="color:#ef4444">DI BAWAH</span>':'<span style="color:#00c26f">DI ATAS</span>'):'—')+'</span></div>'
    html+='<div class="panel-row"><span class="panel-label">vs MA100</span><span class="panel-val">'+(d.exit.ma100!=null?(d.exit.close<d.exit.ma100?'<span style="color:#ef4444">DI BAWAH</span>':'<span style="color:#00c26f">DI ATAS</span>'):'—')+'</span></div>'
    html+='</div>'
  }}
  document.getElementById('pbody').innerHTML=html
  document.getElementById('panel').classList.add('show')
  document.getElementById('overlay').classList.add('show')
}}

function closePanel(){{
  document.getElementById('panel').classList.remove('show')
  document.getElementById('overlay').classList.remove('show')
}}

document.addEventListener('keydown',function(e){{if(e.key==='Escape')closePanel()}})
document.addEventListener('click',function(e){{var t=e.target.closest('.tk-click');if(t){{var tkr=t.getAttribute('data-ticker')||t.textContent.trim();e.stopPropagation();openPanel(tkr)}}}})

/* CARD FILTER — Daily Summary card clicks */
var activeFilter=null
var filterMap={{
  ctx: {{label:'SAHAM TERTEKAN (Context Match)', fn:function(d){{return d.context_match}}}},
  trn: {{label:'MULAI MEMBAIK (Transition Match)', fn:function(d){{return d.transition_match}}}},
  full: {{label:'KANDIDAT TURNAROUND (Full Match)', fn:function(d){{return d.context_match&&d.transition_match}}}},
  'rs-pos': {{label:'KEKUATAN MULAI NAIK (RS Change 60D > 0)', fn:function(d){{return d.rs_change_60d>0}}}},
  'vol-high': {{label:'MINAT BELI MENINGKAT (Volume Ratio >= 1.3)', fn:function(d){{return d.volume_ratio>=1.3}}}},
  recovery: {{label:'PANTUL DARI DASAR (Recovery > 10%)', fn:function(d){{return d.recovery_from_60d_low>10}}}}
}}
function renderFilter(filterType,containerId){{
  var m=filterMap[filterType],el=document.getElementById(containerId)
  if(!m){{el.classList.remove('show');return}}
  var filtered=T.filter(m.fn)
  var html='<div class="fltr-hdr"><span>'+m.label+' \\u2014 '+filtered.length+' saham</span><span class="fltr-close" data-cid="'+containerId+'">\\u2715</span></div>'
  html+='<div class="fltr-list">'
  filtered.forEach(function(d){{
    var ticker=d.ticker.split('.')[0]
    var c=ac(d.ticker)
    html+='<span class="fltr-tag tk-click" data-ticker="'+ticker+'" style="cursor:pointer;color:'+c+'">'+ticker+'</span>'
  }})
  html+='</div>'
  el.innerHTML=html
  el.classList.add('show')
}}
function closeFilter(id){{
  document.getElementById(id).classList.remove('show')
  document.querySelectorAll('.card-click.active').forEach(function(c){{c.classList.remove('active')}})
  activeFilter=null
}}
function filterStocks(type,containerId,el){{
  if(activeFilter===type&&document.getElementById(containerId).classList.contains('show')){{
    closeFilter(containerId)
    el.classList.remove('active')
  }}else{{
    document.querySelectorAll('.card-click.active').forEach(function(c){{c.classList.remove('active')}})
    el.classList.add('active')
    renderFilter(type,containerId)
    activeFilter=type
  }}
}}
document.addEventListener('click',function(e){{var el=e.target.closest('.fltr-close');if(el)closeFilter(el.getAttribute('data-cid'))}})

/* TOOLTIP POPUP — for ? marks (Bahasa Indonesia) */
var toastEl=null
var TIPS={{
  ctx: 'Apa artinya?\\nSaham masih dalam tekanan berat.\\n\\nBagaimana cara menghitungnya?\\nHarga jauh di bawah harga tertinggi sebelumnya\\ndan volatilitas masih tinggi.\\n\\nSumber Riset:\\nResearch-009B',
  trn: 'Apa artinya?\\nSaham mulai menunjukkan pemulihan.\\n\\nBagaimana cara menghitungnya?\\nKekuatan relatif saat ini lebih baik\\ndaripada dua bulan sebelumnya.\\n\\nSumber Riset:\\nResearch-008B / Research-009B',
  full: 'Apa artinya?\\nSaham tertekan yang mulai menunjukkan\\ntanda-tanda pemulihan.\\n\\nBagaimana cara menghitungnya?\\nMemenuhi DUA kondisi:\\n1. Tekanan berat (Context Match)\\n2. Kekuatan relatif membaik (Transition Match)\\n\\nSumber Riset:\\nResearch-008B / Research-009B',
  'rs-pos': 'Apa artinya?\\nSaham mulai mengungguli pasar.\\n\\nBagaimana cara menghitungnya?\\nRS_CHANGE_60D &gt; 0\\nKekuatan relatif meningkat selama 60 hari.\\n\\nSumber Riset:\\nResearch-009',
  'vol-high': 'Apa artinya?\\nAktivitas perdagangan meningkat.\\n\\nBagaimana cara menghitungnya?\\nVolume saat ini setidaknya\\n30% lebih tinggi dari normal.\\n\\nSumber Riset:\\nResearch-008B',
  'above-ma20': 'Apa artinya?\\nHarga bergerak di atas\\ntren jangka pendeknya.\\n\\nBagaimana cara menghitungnya?\\nHarga saat ini di atas\\nharga rata-rata 20 hari terakhir.\\n\\nSumber Riset:\\nResearch-009B',
  recovery: 'Apa artinya?\\nSaham memantul dari\\ntitik terendah baru-baru ini.\\n\\nBagaimana cara menghitungnya?\\nHarga lebih dari 10%\\ndi atas titik terendah\\n60 hari terakhir.\\n\\nSumber Riset:\\nResearch-008B',
  'avg-dd': 'Rata-rata penurunan semua saham dari harga tertinggi masing-masing.\\n\\n(Perhitungan:\\nRata-rata Drawdown_252D\\n— seluruh universe IDX30)',
  'avg-vol': 'Intensitas pergerakan harga rata-rata — semakin tinggi semakin berisiko.\\n\\n(Perhitungan:\\nRata-rata Volatilitas_60D\\n— seluruh universe IDX30)'
}}
function showTip(ev,el){{
  ev.stopPropagation()
  var key=el.getAttribute('data-tip-key')
  var txt=key&&TIPS[key]?TIPS[key]:el.getAttribute('data-tip')||el.getAttribute('title')||''
  if(!toastEl){{
    toastEl=document.createElement('div')
    toastEl.className='toast'
    document.body.appendChild(toastEl)
  }}
  toastEl.classList.remove('show')
  toastEl.textContent=txt
  toastEl.style.left='-9999px'
  toastEl.style.top='-9999px'
  toastEl.classList.add('show')
  var r=el.getBoundingClientRect()
  toastEl.style.left=Math.max(4,Math.min(r.left+r.width/2-toastEl.offsetWidth/2,document.documentElement.clientWidth-toastEl.offsetWidth-4))+'px'
  toastEl.style.top=Math.max(4,r.top-toastEl.offsetHeight-8)+'px'
  setTimeout(function(){{toastEl.classList.remove('show')}},4000)
}}
</script>
</body>
</html>'''

def main():
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    print("=== Dashboard V2 Generator ===")
    print(f"Date: {date_str}")
    leaders = read_csv(LEADERS_FILE)
    turnaround = read_csv(TURNAROUND_FILE)
    summary = read_json(SUMMARY_FILE)
    report_date = summary.get('date', '') if isinstance(summary, dict) else ''
    if not report_date:
        exit_summary = read_json(EXIT_SUMMARY_FILE)
        report_date = exit_summary.get('date', '')
    if not report_date:
        report_date = date_str
    print(f"  Loaded: {len(leaders)} leaders, {len(turnaround)} turnaround, summary")
    print(f"  Report date: {report_date}")
    for r in turnaround:
        r['context_match'] = r.get('context_match', 'False').strip() == 'True'
        r['transition_match'] = r.get('transition_match', 'False').strip() == 'True'
        for key in ['drawdown_252d', 'distance_from_high_252d', 'volatility_60d', 'rs_change_60d', 'volume_ratio', 'recovery_from_60d_low']:
            try:
                r[key] = float(r.get(key, 0))
            except (ValueError, TypeError):
                r[key] = 0.0
    for l in leaders:
        for key in ['quality', 'growth', 'value', 'momentum', 'final_score']:
            try:
                l[key] = float(l.get(key, 0))
            except (ValueError, TypeError):
                l[key] = 0.0
    print("  Updating history archive...")
    history = []
    if turnaround:
        history_rows_for_csv = [
            {'date': date_str, 'ticker': r['ticker'],
             'context_match': str(r['context_match']),
             'transition_match': str(r['transition_match'])}
            for r in turnaround
        ]
        history = update_history(history_rows_for_csv, date_str)
    print(f"  History records: {len(history)}")
    streaks = compute_streaks(history)
    print(f"  Computing streak data for {len(streaks)} tickers")
    exit_data = read_csv(EXIT_FILE)
    for r in exit_data:
        r['rank'] = int(r.get('rank', 0))
        r['rank_change'] = int(r.get('rank_change', 0))
        for key in ['rs_20d', 'rs_change_20d', 'close', 'drawdown_from_entry']:
            try:
                r[key] = float(r.get(key, 0))
            except (ValueError, TypeError):
                r[key] = 0.0
        for key in ['ma20', 'ma50', 'ma100']:
            val = r.get(key)
            if val is None or val == '' or val == 'None':
                r[key] = None
            else:
                try:
                    r[key] = float(val)
                except (ValueError, TypeError):
                    r[key] = None
    print(f"  Loaded {len(exit_data)} exit watchlist records")
    profiles = {}
    if PROFILES_FILE.exists():
        profiles = read_json(PROFILES_FILE)
        print(f"  Loaded {len(profiles)} company profiles")
    else:
        print("  No company_profiles.json found — skipping")
    fundamentals = {}
    if FUND_FILE.exists():
        raw_fund = read_json(FUND_FILE)
        raw_growth = read_json(GROWTH_FILE) if GROWTH_FILE.exists() else {}
        for ticker, data in raw_fund.items():
            fundamentals[ticker] = dict(data)
            if ticker in raw_growth:
                fundamentals[ticker]['revenue_growth'] = raw_growth[ticker].get('revenue_growth')
                fundamentals[ticker]['earnings_growth'] = raw_growth[ticker].get('earnings_growth')
        print(f"  Loaded {len(fundamentals)} fundamental records")
    else:
        print("  No fundamentals data found — skipping")
    print("  Loading radar status...")
    radar_status = read_json(RADAR_STATUS_FILE)
    if radar_status:
        print(f"  Radar status: {radar_status.get('status', 'N/A')} | AI narrative: {len(radar_status.get('detail_message', ''))} chars")
    else:
        print("  No radar status found — skipping AI conclusion")
    print("  Generating HTML...")
    html = build_html(leaders, turnaround, summary, history, streaks, report_date, exit_data, profiles, fundamentals, radar_status)
    V2_DIR.mkdir(parents=True, exist_ok=True)
    output_path = V2_DIR / 'index.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  Written: {output_path.resolve()}")
    print("=== Dashboard V2 Complete ===")

if __name__ == '__main__':
    main()
