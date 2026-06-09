import json
import csv
import datetime
import math
from pathlib import Path

HISTORY_FILE = Path("database/historical/turnaround_history.csv")
LEADERS_FILE = Path("data/current/leaders_latest.csv")
TURNAROUND_FILE = Path("data/current/turnaround_latest.csv")
EXIT_FILE = Path("data/current/exit_watchlist_latest.csv")
WAREHOUSE_FILE = Path("warehouse_historical/warehouse_v3_growth_fix.csv")

CONFIG_B_WEIGHTS = {"quality": 0.25, "growth": 0.30, "value": 0.10, "momentum": 0.35}
FACTOR_COLORS = {"quality": "#3b82f6", "growth": "#10b981", "value": "#a855f7", "momentum": "#f59e0b"}
FACTOR_LABELS = {"quality": "Quality", "growth": "Growth", "value": "Value", "momentum": "Momentum"}

IC_VALUES = {
    "quality": {"ic": 0.0279, "role": "Stabilizer"},
    "growth": {"ic": -0.0126, "role": "Diversifier"},
    "value": {"ic": 0.0555, "role": "Predictive"},
    "momentum": {"ic": 0.0356, "role": "Primary Return Driver"}
}

BACKTEST_RESULTS = {
    "full": {"label": "Full Period (2022-02 \u2192 2026-05)",
        "config_b": {"cagr": 13.22, "sharpe": 0.6072, "max_dd": -27.53, "total_return": 71.29},
        "config_f": {"cagr": 11.07, "sharpe": 0.5701, "max_dd": -22.00, "total_return": 57.60},
        "ihsg": {"cagr": -0.89, "sharpe": -0.08, "max_dd": -28.73, "total_return": -3.82}},
    "pre_2026": {"label": "Before 2026 (2022-02 \u2192 2025-12)",
        "config_b": {"cagr": 23.56, "sharpe": 1.0158, "max_dd": -26.08, "total_return": 129.02},
        "config_f": {"cagr": 17.21, "sharpe": 0.8459, "max_dd": -22.00, "total_return": 86.25},
        "ihsg": {"cagr": -0.60, "sharpe": 0.12, "max_dd": -12.51, "total_return": -2.33}},
    "ytd_2026": {"label": "2026 YTD (2026-01 \u2192 2026-05)",
        "config_b": {"cagr": -55.70, "sharpe": -1.5343, "max_dd": -27.53, "total_return": -23.77},
        "config_f": {"cagr": -35.85, "sharpe": -0.9304, "max_dd": -17.04, "total_return": -13.75},
        "ihsg": {"cagr": -7.81, "sharpe": -0.58, "max_dd": -18.62, "total_return": -2.68}}
}

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

def get_warehouse_info():
    if not WAREHOUSE_FILE.exists():
        return {"start": "2022-01", "end": "2026-05", "months": 53, "equity_b": [], "equity_f": [], "equity_i": [], "month_labels": []}
    rows = read_csv(WAREHOUSE_FILE)
    months = sorted(set(r['month'] for r in rows), reverse=True)
    if not months:
        return {"start": "2022-01", "end": "2026-05", "months": 53, "equity_b": [], "equity_f": [], "equity_i": [], "month_labels": []}
    n_months = len(months)
    start_m = months[-1][:7]
    end_m = months[0][:7]

    def gen_curve(cagr_pct, max_dd_pct, n_m):
        vals = [100.0]
        for i in range(1, n_m + 1):
            vals.append(100.0 * (1 + cagr_pct / 100) ** (i / 12.0))
        crash_start = max(0, n_m - 6)
        peak_at_crash = vals[crash_start]
        for i in range(crash_start, len(vals)):
            frac = (i - crash_start) / max(1, (len(vals) - 1 - crash_start))
            vals[i] = peak_at_crash * (1 - max_dd_pct / 100 * frac)
        return vals

    n = n_months
    equity_b = gen_curve(13.22, 27.53, n)
    equity_f = gen_curve(11.07, 22.00, n)
    equity_i = [100.0 * (1 - 0.0089) ** (i / 12.0) for i in range(n + 1)]
    month_labels = [m[:7] for m in months][::-1]
    return {
        "start": start_m, "end": end_m, "months": n,
        "equity_b": equity_b, "equity_f": equity_f, "equity_i": equity_i,
        "month_labels": month_labels
    }

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>ISI Dashboard V3 | Read-Only</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'DM Sans','Segoe UI','Inter',sans-serif;background:#0a0e14;color:#e8edf5;min-height:100vh;font-size:14px;line-height:1.5}
.hdr{padding:12px 24px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #1e2633;flex-wrap:wrap;gap:8px}
.logo{font-family:'Space Mono','Courier New',monospace;font-size:13px;color:#00d68f;letter-spacing:.1em}
.logo span{color:#64748b}
.dt{font-size:12px;color:#64748b;font-family:'Space Mono',monospace}
.status-bar{display:flex;gap:6px;flex-wrap:wrap}
.pill{font-size:10px;padding:4px 12px;border-radius:100px;font-family:'Space Mono',monospace;font-weight:600;letter-spacing:.04em}
.pill.prod{background:#064e2e;color:#00d68f;border:1px solid #166534}
.pill.res{background:#0c1929;color:#60a5fa;border:1px solid #1e3a5f}
.pill.warehouse{background:#171b20;color:#94a3b8;border:1px solid #222830}
.tab-nav{display:flex;gap:2px;padding:10px 24px 0;border-bottom:1px solid #1e2633;overflow-x:auto;scrollbar-width:thin}
.tab-btn{padding:8px 16px;font-size:11px;font-family:'Space Mono',monospace;background:transparent;border:none;color:#64748b;cursor:pointer;border-bottom:2px solid transparent;transition:all .15s;white-space:nowrap;letter-spacing:.04em}
.tab-btn:hover{color:#e8edf5}
.tab-btn.active{color:#00d68f;border-bottom-color:#00d68f}
.tc{display:none;padding:16px 24px}
.tc.active{display:block}
.section-title{font-size:13px;font-weight:600;margin-bottom:12px;letter-spacing:.04em;color:#e8edf5;font-family:'Space Mono',monospace}
.card{background:#111820;border:1px solid #1e293b;border-radius:8px;padding:12px;margin-bottom:8px}
.card-label{font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px}
.card-val{font-size:18px;font-weight:700;font-family:'Space Mono',monospace}
.card-sub{font-size:12px;color:#64748b;margin-top:2px;line-height:1.5}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px}
.wide-card{grid-column:1 / -1}
.card-list{display:flex;flex-direction:column;gap:6px}
.card-row{display:flex;justify-content:space-between;align-items:center;padding:4px 0;font-size:12px;border-bottom:1px solid #1e2633}
.g{color:#00c26f}
.r{color:#ef4444}
.y{color:#f59e0b}
.b{color:#60a5fa}
.o{color:#f97316}
.badge{display:inline-block;padding:1px 8px;border-radius:100px;font-size:10px;font-weight:600;font-family:'Space Mono',monospace;letter-spacing:.04em}
.bg-green{background:#064e2e;color:#00d68f;border:1px solid #166534}
.bg-yellow{background:#3b2a04;color:#fbbf24;border:1px solid #5c4308}
.bg-blue{background:#0c1929;color:#60a5fa;border:1px solid #1e3a5f}
.bg-gray{background:#1e293b;color:#64748b;border:1px solid #263040}
.bg-red{background:#3b0a0a;color:#ef4444;border:1px solid #5c1515}
.flag{color:#f59e0b;font-size:10px;margin-left:4px}
.tk{font-family:'Space Mono',monospace;font-weight:600;font-size:12px;letter-spacing:.02em}
.tk-click{cursor:pointer}
.tk-click:hover{opacity:.8}
.sf{font-family:'Space Mono',monospace;font-weight:700;font-size:13px;letter-spacing:.02em}
.sf.high{color:#00d68f}
.sf.mid{color:#f59e0b}
.sf.low{color:#ef4444}
table{width:100%;border-collapse:collapse;font-size:12px;min-width:600px}
th{text-align:left;padding:8px 10px;font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.08em;border-bottom:1px solid #1e2633;font-weight:600;cursor:pointer;user-select:none;white-space:nowrap;font-family:'Space Mono',monospace}
th:hover{color:#94a3b8}
td{padding:6px 10px;border-bottom:1px solid #161f2e;vertical-align:middle}
tr:hover td{background:#111b26}
.table-wrap{overflow-x:auto;border:1px solid #1e2633;border-radius:8px;background:#0d1219}
.bar{display:flex;align-items:center;gap:6px}
.bar-track{flex:1;height:6px;background:#1e293b;border-radius:3px;overflow:hidden;max-width:100px}
.bar-fill{height:100%;border-radius:3px;transition:width .3s}
.bv{font-family:'Space Mono',monospace;font-size:11px;color:#94a3b8;min-width:32px;text-align:right;font-variant-numeric:tabular-nums}
.section-title{font-size:13px;font-weight:600;margin-bottom:4px;letter-spacing:.04em;color:#e8edf5;font-family:'Space Mono',monospace}
.factor-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.factor-card{background:#111820;border:1px solid #1e293b;border-radius:8px;padding:12px}
.factor-hdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
.factor-name{font-size:12px;font-weight:600;font-family:'Space Mono',monospace;color:#e8edf5}
.factor-weight{font-size:10px;color:#64748b;font-family:'Space Mono',monospace}
.factor-ic{font-family:'Space Mono',monospace;font-size:13px;font-weight:700;margin-bottom:2px}
.factor-ic.positive{color:#00d68f}
.factor-ic.negative{color:#ef4444}
.ic-bar{height:4px;background:#1e293b;border-radius:2px;overflow:hidden;margin-bottom:4px}
.ic-fill{height:100%;border-radius:2px}
.factor-role{font-size:10px;color:#64748b}
.insight-hdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;flex-wrap:wrap;gap:4px}
.insight-title{font-size:12px;font-weight:600;color:#e8edf5;font-family:'Space Mono',monospace}
.insight-badge{font-size:10px;padding:2px 10px;border-radius:100px;font-family:'Space Mono',monospace;font-weight:600;letter-spacing:.04em}
.insight-badge.r{background:#3b0a0a;color:#ef4444;border:1px solid #5c1515}
.insight-badge.y{background:#3b2a04;color:#fbbf24;border:1px solid #5c4308}
.insight-badge.n{background:#064e2e;color:#00d68f;border:1px solid #166534}
.insight-badge.b{background:#0c1929;color:#60a5fa;border:1px solid #1e3a5f}
.insight-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px 16px}
.insight-row{display:flex;justify-content:space-between;align-items:center;padding:3px 0;font-size:12px}
.insight-lbl{color:#64748b}
.insight-val{font-weight:600;font-family:'Space Mono',monospace;font-size:11px}
.insight-note{font-size:11px;color:#64748b;margin-top:6px;padding:6px 8px;background:#111820;border-radius:6px;border-left:3px solid #3b82f6;line-height:1.5}
.cfg-nav{display:flex;gap:6px;align-items:center}
.cfg-btn{padding:5px 14px;font-size:10px;font-family:'Space Mono',monospace;border-radius:6px;border:1px solid #334155;background:transparent;cursor:pointer;letter-spacing:.04em;transition:all .15s}
.cfg-btn.active-prod{background:#064e2e;color:#00d68f;border-color:#166534}
.cfg-btn.active-res{background:#0c1929;color:#60a5fa;border-color:#1e3a5f}
.cfg-btn:not(.active-prod):not(.active-res){color:#64748b}
.cfg-label{font-size:10px;color:#64748b}
.top-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:6px;margin-top:8px}
.top-candidate{background:#111820;border:1px solid #1e293b;border-radius:8px;padding:10px;cursor:pointer;transition:border-color .15s}
.top-candidate:hover{border-color:#3b82f6}
.sub-tab-nav{display:flex;gap:2px;margin-bottom:12px;border-bottom:1px solid #1e2633}
.sub-tab-btn{padding:6px 12px;font-size:10px;font-family:'Space Mono',monospace;background:transparent;border:none;color:#64748b;cursor:pointer;border-bottom:2px solid transparent;transition:all .15s;letter-spacing:.04em}
.sub-tab-btn:hover{color:#e8edf5}
.sub-tab-btn.active{color:#00d68f;border-bottom-color:#00d68f}
.sub-tc{display:none}
.sub-tc.active{display:block}
.chart-container{background:#111820;border:1px solid #1e293b;border-radius:8px;padding:16px;margin-bottom:12px}
.comp-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px}
.period-btn{padding:5px 14px;font-size:10px;font-family:'Space Mono',monospace;background:transparent;border:1px solid #334155;border-radius:6px;color:#64748b;cursor:pointer;letter-spacing:.04em;transition:all .15s}
.period-btn.active{background:#0c1929;color:#60a5fa;border-color:#1e3a5f}
.period-btn:hover{color:#e8edf5}
.overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.6);z-index:999;display:none}
.overlay.active{display:block}
.panel{position:fixed;top:0;right:-480px;width:460px;height:100%;background:#0d1219;border-left:1px solid #1e2633;z-index:1000;overflow-y:auto;transition:right .25s ease;padding:0}
.panel.active{right:0}
.panel-hdr{display:flex;justify-content:space-between;align-items:center;padding:16px 20px;border-bottom:1px solid #1e2633;position:sticky;top:0;background:#0d1219;z-index:1}
.panel-hdr .tk{font-size:16px}
.panel-hdr .name{font-size:11px;color:#64748b;margin-top:2px}
.panel-close{background:transparent;border:1px solid #334155;color:#64748b;font-size:16px;cursor:pointer;padding:4px 10px;border-radius:6px}
.panel-close:hover{color:#e8edf5;border-color:#64748b}
.panel-body{padding:16px 20px}
.ai-explain{font-size:12px;color:#c0c8d4;line-height:1.7;padding:12px;background:#111820;border-radius:8px;margin-bottom:12px;border-left:3px solid #3b82f6}
.breakdown-grid{display:grid;gap:6px;margin-top:8px}
.breakdown-row{padding:6px 0}
.bf-hdr{display:flex;justify-content:space-between;font-size:11px;font-family:'Space Mono',monospace;margin-bottom:2px}
.breakdown-total{font-size:13px;font-weight:700;text-align:center;padding:10px;background:#111820;border-radius:8px;margin-top:8px;font-family:'Space Mono',monospace}
.es-exit{color:#ef4444;font-weight:700;font-size:11px;padding:2px 8px;background:#3b0a0a;border-radius:4px;border:1px solid #5c1515;font-family:'Space Mono',monospace}
.es-exit-risk{color:#f59e0b;font-weight:700;font-size:11px;padding:2px 8px;background:#3b2a04;border-radius:4px;border:1px solid #5c4308;font-family:'Space Mono',monospace}
.es-weakening{color:#f97316;font-weight:700;font-size:11px;padding:2px 8px;background:#2d1f04;border-radius:4px;border:1px solid #5c3f08;font-family:'Space Mono',monospace}
.es-exit-watch{color:#60a5fa;font-weight:700;font-size:11px;padding:2px 8px;background:#0c1929;border-radius:4px;border:1px solid #1e3a5f;font-family:'Space Mono',monospace}
.es-healthy{color:#00d68f;font-weight:700;font-size:11px;padding:2px 8px;background:#064e2e;border-radius:4px;border:1px solid #166534;font-family:'Space Mono',monospace}
.timeline{position:relative;padding:16px 0}
.timeline::before{content:'';position:absolute;left:12px;top:0;bottom:0;width:2px;background:#1e293b}
.tl-item{position:relative;padding:4px 0 16px 36px;cursor:pointer;transition:opacity .15s}
.tl-item:hover{opacity:.8}
.tl-item.active .tl-title{color:#00d68f}
.tl-dot{position:absolute;left:6px;top:6px;width:14px;height:14px;border-radius:50%;background:#1e293b;border:2px solid #334155;transition:all .15s}
.tl-item.active .tl-dot{background:#00d68f;border-color:#00d68f;box-shadow:0 0 8px rgba(0,214,143,.4)}
.tl-date{font-size:10px;color:#64748b;font-family:'Space Mono',monospace;margin-bottom:2px}
.tl-title{font-size:13px;font-weight:600;color:#e8edf5;margin-bottom:2px;font-family:'Space Mono',monospace}
.tl-desc{font-size:11px;color:#64748b;line-height:1.5}
.filter-input{background:#1e293b;border:1px solid #334155;border-radius:6px;padding:8px 12px;color:#e8edf5;font-size:12px;width:220px;margin-bottom:12px;outline:none}
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:#0a0e14}
::-webkit-scrollbar-thumb{background:#1e293b;border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:#334155}
</style>
</head>
<body>
<div class="hdr">
<div class="logo">ISI <span>|</span> Read-Only Dashboard <span style="font-size:10px;color:#3b82f6">V3</span></div>
<div class="status-bar">
<span class="pill prod">Config F (Q25/G10/V30/M35)</span>
<span class="pill res">Config B (Q25/G30/V10/M35)</span>
<span class="pill warehouse">{warehouse_range}</span>
</div>
<div class="dt">{report_date}</div>
</div>

<div class="tab-nav">
<button class="tab-btn active" onclick="st(0,this)">Leaders</button>
<button class="tab-btn" onclick="st(1,this)">Turnaround</button>
<button class="tab-btn" onclick="st(2,this)">Candidates</button>
<button class="tab-btn" onclick="st(3,this)">History</button>
<button class="tab-btn" onclick="st(4,this)">Exit</button>
<button class="tab-btn" onclick="st(5,this)">Diagnostics</button>
<button class="tab-btn" onclick="st(6,this)">Simulation Lab</button>
<button class="tab-btn" onclick="st(7,this)">Research</button>
</div>

<div id="insight-leaders" style="padding:8px 24px 0"></div>
<div id="insight-top10" style="padding:4px 24px 0"></div>
<div id="radar-conclusion" style="padding:4px 24px 0"></div>
<div id="insight-ctx" style="padding:4px 24px 0"></div>
<div id="insight-exit" style="padding:4px 24px 0"></div>

<div class="tc active" id="t0">
<div class="section-title">Leaders · Config Switcher</div>
<div style="display:flex;gap:6px;align-items:center;margin-bottom:10px">
<span class="cfg-label">Active Config:</span>
<button class="cfg-btn active-prod" id="cfg-prod" onclick="switchConfig('prod')">Config F (Q25/G10/V30/M35)</button>
<button class="cfg-btn" id="cfg-res" onclick="switchConfig('res')">Config B (Q25/G30/V10/M35)</button>
</div>
<div class="section-title" style="font-size:11px;color:#64748b;margin-bottom:8px">Factor IC Panel</div>
<div class="factor-grid" id="factor-panel"></div>
<div style="margin-top:12px" class="table-wrap">
<table>
<thead><tr>
<th data-key="rank">#</th><th data-key="ticker">Ticker</th><th data-key="score">Score</th><th data-key="quality">Quality</th><th data-key="growth">Growth</th><th data-key="value">Value</th><th data-key="momentum">Momentum</th><th>Detail</th>
</tr></thead>
<tbody id="tbody-leaders"></tbody>
</table>
</div>
</div>

<div class="tc" id="t1">
<div class="section-title">Context / Transition Tracker</div>
<div class="sub-tab-nav">
<button class="tab-btn active" onclick="stSub('1','ctx',this)">Context Match</button>
<button class="tab-btn" onclick="stSub('1','trn',this)">Transition Match</button>
</div>
<div class="sub-tc active" id="t1-ctx">
<div class="card-grid">
<div class="card"><div class="card-label">Context Match Count</div><div class="card-val g">{ctx_match_count}</div><div class="card-sub">stable context alignment</div></div>
<div class="card"><div class="card-label">Transition Match Count</div><div class="card-val g">{trn_match_count}</div><div class="card-sub">active transition phase</div></div>
</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:8px">
<div class="chart-container" style="height:250px"><canvas id="ctx-chart"></canvas></div>
<div class="chart-container" style="height:250px"><canvas id="trn-chart"></canvas></div>
</div>
</div>
<div class="sub-tc" id="t1-trn">
<div class="table-wrap"><table>
<thead><tr><th>Ticker</th><th>Context</th><th>Ctx Days</th><th>Transition</th><th>Trn Days</th><th>Full</th><th>Last Update</th></tr></thead>
<tbody id="tbody-trn"></tbody>
</table></div>
</div>
</div>

<div class="tc" id="t2">
<div class="section-title">Top Candidates</div>
<div style="margin-bottom:8px;font-size:11px;color:#64748b">Top 10 tickers by composite score. Score breakdown = quality, growth, value, momentum factor scores (0-100).</div>
<div class="top-grid" id="top-candidates"></div>
</div>

<div class="tc" id="t3">
<div class="section-title">Candidate Persistence Tracking</div>
<p style="font-size:11px;color:#64748b;margin-bottom:10px">Consecutive days each ticker has maintained context/transition match. Sorted by total active streak.</p>
<div class="table-wrap">
<table>
<thead><tr>
<th data-key="ticker">Ticker</th><th data-key="ctx_days">Context Streak</th><th data-key="trn_days">Transition Streak</th><th>First Detected (Ctx)</th><th>First Detected (Trn)</th><th data-key="total_entries">Total Days Tracked</th>
</tr></thead>
<tbody id="tbody-history"></tbody>
</table>
</div>
</div>

<div class="tc" id="t4">
<div class="section-title">Exit Monitor · Rule-Based Exit Signals</div>
<div class="card" style="margin-bottom:12px">
<div class="card-label">LEGENDA EXIT MONITOR</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 16px;margin-top:8px">
<div style="font-size:12px"><span class="badge" style="background:#1e2633;color:#e8edf5;border:none">A</span> Peringkat Turun (Rank > 10)</div>
<div style="font-size:12px"><span class="badge" style="background:#1e2633;color:#e8edf5;border:none">B</span> Momentum Melemah (RS20 < 0 & RS Chg 20D < 0)</div>
<div style="font-size:12px"><span class="badge" style="background:#1e2633;color:#e8edf5;border:none">C</span> Trend MA50 Rusak (Close < MA50)</div>
<div style="font-size:12px"><span class="badge" style="background:#1e2633;color:#e8edf5;border:none">D</span> Pelemahan Terkonfirmasi (Close < MA100 atau DD > 15%)</div>
<div style="font-size:12px;color:#64748b"><span class="badge" style="background:#1e2633;color:#94a3b8;border:none">Rank Chg</span> Perubahan posisi rank</div>
<div style="font-size:12px;color:#64748b"><span class="badge" style="background:#1e2633;color:#94a3b8;border:none">RS20</span> Relative Strength 20 hari</div>
<div style="font-size:12px;color:#64748b"><span class="badge" style="background:#1e2633;color:#94a3b8;border:none">RS Chg 20D</span> Perubahan RS dalam 20 hari</div>
<div style="font-size:12px;color:#64748b"><span class="badge" style="background:#1e2633;color:#94a3b8;border:none">vs MA50/100</span> Posisi harga terhadap MA50/MA100</div>
<div style="font-size:12px;color:#64748b"><span class="badge" style="background:#1e2633;color:#94a3b8;border:none">DD Entry</span> Drawdown dari harga entry</div>
</div>
</div>
<div style="margin-bottom:10px;display:flex;gap:6px;flex-wrap:wrap">
<button class="tab-btn active" onclick="ef('all',this)" style="font-size:11px;padding:5px 14px">All</button>
<button class="tab-btn" onclick="ef('EXIT',this)" style="font-size:11px;padding:5px 14px;color:#ef4444">Exit</button>
<button class="tab-btn" onclick="ef('EXIT RISK',this)" style="font-size:11px;padding:5px 14px;color:#f59e0b">Exit Risk</button>
<button class="tab-btn" onclick="ef('WEAKENING',this)" style="font-size:11px;padding:5px 14px;color:#f97316">Weakening</button>
<button class="tab-btn" onclick="ef('EXIT WATCH',this)" style="font-size:11px;padding:5px 14px;color:#60a5fa">Exit Watch</button>
<button class="tab-btn" onclick="ef('HEALTHY',this)" style="font-size:11px;padding:5px 14px;color:#00d68f">Healthy</button>
</div>
<div class="table-wrap">
<table>
<thead><tr>
<th data-key="ticker">Ticker</th><th data-key="rank">Rank</th><th data-key="rank_change">Rank Chg</th><th>Exit State</th><th>Rules</th><th data-key="rs_20d">RS20</th><th data-key="rs_change_20d">RS Chg 20D</th><th>vs MA50</th><th>vs MA100</th><th data-key="drawdown_from_entry">DD Entry</th>
</tr></thead>
<tbody id="tbody-exit"></tbody>
</table>
</div>
</div>

<div class="tc" id="t5">
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
<div class="card"><div class="card-label">Last Leaders Update</div><div class="card-val" style="font-size:14px">{file_age_leaders}</div><div class="card-sub">leaders_latest.csv</div></div>
<div class="card"><div class="card-label">Last Turnaround Update</div><div class="card-val" style="font-size:14px">{file_age_turnaround}</div><div class="card-sub">turnaround_latest.csv</div></div>
<div class="card"><div class="card-label">Last Exit Update</div><div class="card-val" style="font-size:14px">{file_age_exit}</div><div class="card-sub">exit_watchlist_latest.csv</div></div>
<div class="card"><div class="card-label">Records Processed</div><div class="card-val g">{universe_size}</div><div class="card-sub">tickers in latest run</div></div>
<div class="card"><div class="card-label">Data Freshness</div><div class="card-val g">{report_date_val}</div><div class="card-sub">report date</div></div>
<div class="card"><div class="card-label">History Records</div><div class="card-val b">{history_len}</div><div class="card-sub">turnaround_history.csv</div></div>
<div class="card"><div class="card-label">Workflow</div><div class="card-val" style="font-size:13px">daily_radar.yml</div><div class="card-sub">cron: 30 9 * * *</div></div>
</div>
</div>

<div class="tc" id="t6">
<div class="section-title">Simulation Lab · Backtest Analysis</div>
<div class="sub-tab-nav">
<button class="sub-tab-btn active" onclick="stSub('6','0',this)">Growth of 100M</button>
<button class="sub-tab-btn" onclick="stSub('6','1',this)">Comparison</button>
<button class="sub-tab-btn" onclick="stSub('6','2',this)">Period Toggle</button>
<button class="sub-tab-btn" onclick="stSub('6','3',this)">Risk vs Return</button>
</div>
<div class="sub-tc active" id="t6-0">
<div class="chart-container"><canvas id="equityChart"></canvas></div>
<p style="font-size:11px;color:#64748b;text-align:center;line-height:1.5">
<span style="color:#60a5fa">Config B</span> (Q25/G30/V10/M35) vs <span style="color:#00d68f">Config F</span> (Q25/G10/V30/M35) vs <span style="color:#94a3b8">IHSG</span>.<br>
Monthly rebalance, equal weight top 5. Approximate equity curves (synthetic).
</p>
</div>
<div class="sub-tc" id="t6-1">
<div class="comp-grid" id="comparison-cards"></div>
</div>
<div class="sub-tc" id="t6-2">
<div style="margin-bottom:12px;text-align:center">
<button class="period-btn active" onclick="switchPeriod('full',this)">Full Period</button>
<button class="period-btn" onclick="switchPeriod('pre_2026',this)">Before 2026</button>
<button class="period-btn" onclick="switchPeriod('ytd_2026',this)">2026 YTD</button>
</div>
<div class="comp-grid" id="period-cards"></div>
</div>
<div class="sub-tc" id="t6-3">
<div class="chart-container"><canvas id="riskChart"></canvas></div>
<p style="font-size:11px;color:#64748b;text-align:center;line-height:1.5">
Annualized return (CAGR) vs Max Drawdown. Bubble size = |Sharpe| ratio.<br>
Ideal position: top-left (high return, low drawdown) or top-right (high return, accepts volatility).
</p>
</div>
</div>

<div class="tc" id="t7">
<div class="section-title">Research Timeline · ISI Project History</div>
<div id="timeline-container"></div>
</div>

<div class="overlay" id="overlay" onclick="closePanel()"></div>
<div class="panel" id="panel">
<div class="panel-hdr">
<div><div class="tk" id="ptk"></div><div class="name" id="pname"></div></div>
<button class="panel-close" onclick="closePanel()">\u2715</button>
</div>
<div class="panel-body" id="pbody"></div>
</div>
<script>
const L = {leaders_json};
const T = {turnaround_json};
const SM = {summary_json};
const SK = {streaks_json};
const EX = {exit_json};
const PF = {profiles_json};
const FD = {fundamentals_json};
const CW_B = {cw_b_json};
const CW_F = {cw_f_json};
const WI = {warehouse_json};
const IC = {ic_json};
const BT = {bt_json};
const FCOLORS = {fcolors_json};
const FNAMES = {fnames_json};

var activeConfig = 'prod';
function getWeights() { return activeConfig === 'prod' ? CW_F : CW_B; }
function configLabel() { return activeConfig === 'prod' ? 'Config F' : 'Config B'; }

function sc(v) { return v >= 60 ? 'high' : v >= 40 ? 'mid' : 'low'; }
function bar(v, k) { var n = +v; return '<div class=\"bar\"><div class=\"bar-track\"><div class=\"bar-fill\" style=\"width:' + Math.min(n, 100) + '%;background:' + k + '\"></div></div><span class=\"bv\">' + n.toFixed(1) + '</span></div>'; }
function badge(v, t) { return v ? '<span class=\"badge ' + t + '\">Yes</span>' : '<span class=\"badge bg-gray\">No</span>'; }
function pct(v) { var n = +v; return (n > 0 ? '+' : '') + n.toFixed(1) + '%'; }
function ctxLabel(r) { return r.context_match ? '<span class=\"badge bg-green\">YES</span>' : '<span class=\"badge bg-gray\">NO</span>'; }
function trnLabel(r) { return r.transition_match ? '<span class=\"badge bg-yellow\">YES</span>' : '<span class=\"badge bg-gray\">NO</span>'; }
function fullLabel(r) { return (r.context_match && r.transition_match) ? '<span class=\"badge bg-blue\">FULL</span>' : r.context_match ? '<span class=\"badge bg-green\">CTX</span>' : r.transition_match ? '<span class=\"badge bg-yellow\">TRN</span>' : '<span class=\"badge bg-gray\">\u2014</span>'; }

function computeFinalScore(r, w) { return r.quality * w.quality + r.growth * w.growth + r.value * w.value + r.momentum * w.momentum; }

function ac(t) {
  var ld = null, td = null, ed = null, tk = t.indexOf('.JK') > 0 ? t : t + '.JK';
  L.forEach(function(d) { if (d.ticker === tk) ld = d; });
  T.forEach(function(d) { if (d.ticker === tk) td = d; });
  EX.forEach(function(d) { if (d.ticker === tk) ed = d; });
  var w = getWeights();
  var score = ld ? computeFinalScore(ld, w) : 0;
  if (ld && score >= 70 && ed && ed.exit_state === 'HEALTHY') return '#00ff88';
  if (ld && score >= 60 && ed && ed.exit_state === 'EXIT RISK') return '#ffcc33';
  if (ld && score >= 60 && ed && ed.exit_state === 'EXIT') return '#ff5555';
  if (td && td.context_match && td.transition_match && (!ed || ed.exit_state !== 'EXIT')) return '#4da3ff';
  return '#cccccc';
}

function sortData(d, s) {
  if (!s.key) return d;
  return d.slice().sort(function(a, b) {
    var va = a[s.key], vb = b[s.key];
    if (typeof va === 'string') return s.dir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
    va = Number(va) || 0; vb = Number(vb) || 0;
    return s.dir === 'asc' ? va - vb : vb - va;
  });
}

function renderLeaders() {
  var w = getWeights();
  var scored = L.map(function(r) { return Object.assign({}, r, { _score: computeFinalScore(r, w) }); });
  scored.sort(function(a, b) { return b._score - a._score; });
  scored.forEach(function(r, i) { r._rank = i + 1; });
  var html = scored.map(function(r) {
    return '<tr><td class=\"tk\" style=\"color:#9CA3AF;font-size:11px\">' + r._rank + '</td><td class=\"tk tk-click\" data-ticker=\"' + r.ticker.split('.')[0] + '\" style=\"color:' + ac(r.ticker) + '\">' + r.ticker.split('.')[0] + (r._rank <= 5 ? '<span class=\"flag\">\u2605</span>' : '') + '</td><td class=\"sf ' + sc(r._score) + '\">' + r._score.toFixed(1) + '</td><td>' + bar(r.quality, FCOLORS.quality) + '</td><td>' + bar(r.growth, FCOLORS.growth) + '</td><td>' + bar(r.value, FCOLORS.value) + '</td><td>' + bar(r.momentum, FCOLORS.momentum) + '</td><td></td></tr>';
  }).join('');
  document.getElementById('tbody-leaders').innerHTML = html;
}
renderLeaders();

function renderFactorPanel() {
  var w = getWeights();
  var order = ['quality', 'growth', 'value', 'momentum'];
  var h = '';
  order.forEach(function(k) {
    var d = IC[k];
    var icv = d.ic;
    var cls = icv > 0 ? 'positive' : 'negative';
    var pctW = (w[k] * 100).toFixed(0);
    var barW = Math.min(Math.abs(icv) * 1000, 100);
    var barC = icv > 0 ? '#00d68f' : '#ef4444';
    h += '<div class=\"factor-card\"><div class=\"factor-hdr\"><span class=\"factor-name\">' + FNAMES[k] + '</span><span class=\"factor-weight\">' + pctW + '%</span></div><div class=\"factor-ic ' + cls + '\">' + (icv > 0 ? '+' : '') + icv.toFixed(4) + '</div><div class=\"ic-bar\"><div class=\"ic-fill\" style=\"width:' + barW + '%;background:' + barC + '\"></div></div><div class=\"factor-role\">' + d.role + '</div></div>';
  });
  document.getElementById('factor-panel').innerHTML = h;
}
renderFactorPanel();

function switchConfig(cfg) {
  activeConfig = cfg;
  document.getElementById('cfg-prod').className = 'cfg-btn' + (cfg === 'prod' ? ' active-prod' : '');
  document.getElementById('cfg-res').className = 'cfg-btn' + (cfg === 'res' ? ' active-res' : '');
  renderLeaders();
  renderFactorPanel();
  renderInsights();
  renderTop();
}

function renderInsights() {
  var w = getWeights();
  var scored = L.map(function(r) { return Object.assign({}, r, { _score: computeFinalScore(r, w) }); });
  scored.sort(function(a, b) { return b._score - a._score; });
  scored.forEach(function(r, i) { r._rank = i + 1; });
  var n = scored.length;
  var top5 = scored.filter(function(d) { return d._rank <= 5; });
  var bot5 = scored.filter(function(d) { return d._rank > n - 5; });
  var factors = ['quality', 'growth', 'value', 'momentum'];
  var avg = function(arr, k) { return arr.reduce(function(s, d) { return s + (+d[k]); }, 0) / arr.length; };
  var t5 = factors.map(function(f) { return { name: f, val: avg(top5, f) }; });
  var allTop5Avg = t5.reduce(function(s, f) { return s + f.val; }, 0) / 4;
  var allBot5Avg = factors.reduce(function(s, f) { return s + avg(bot5, f); }, 0) / 4;
  var gap = allTop5Avg - allBot5Avg;
  var strongest = t5.slice().sort(function(a, b) { return b.val - a.val; })[0];
  var weakest = factors.map(function(f) { return { name: f, val: avg(bot5, f) }; }).sort(function(a, b) { return a.val - b.val; })[0];
  var h = '<div class=\"insight-hdr\"><span class=\"insight-title\">Analisis Leaders \u00b7 ' + configLabel() + '</span><span class=\"insight-badge ' + (gap > 30 ? 'r' : gap > 15 ? 'y' : 'n') + '\">Gap Top5\u2013Bot5: ' + gap.toFixed(1) + '</span></div><div class=\"insight-grid\">';
  h += '<div class=\"insight-row\"><span class=\"insight-lbl\">Rerata Top 5</span><span class=\"insight-val g\">' + allTop5Avg.toFixed(1) + '</span></div>';
  h += '<div class=\"insight-row\"><span class=\"insight-lbl\">Faktor Terkuat Top5</span><span class=\"insight-val g\">' + strongest.name.charAt(0).toUpperCase() + strongest.name.slice(1) + ' (' + strongest.val.toFixed(1) + ')</span></div>';
  h += '<div class=\"insight-row\"><span class=\"insight-lbl\">Rerata Bottom 5</span><span class=\"insight-val r\">' + allBot5Avg.toFixed(1) + '</span></div>';
  h += '<div class=\"insight-row\"><span class=\"insight-lbl\">Faktor Terlemah Bot5</span><span class=\"insight-val r\">' + weakest.name.charAt(0).toUpperCase() + weakest.name.slice(1) + ' (' + weakest.val.toFixed(1) + ')</span></div>';
  h += '</div><div class=\"insight-note\">Kesenjangan ' + gap.toFixed(1) + ' poin \u2014 ' + (gap > 30 ? 'distribusi sangat timpang, dominasi saham unggulan kuat' : gap > 15 ? 'distribusi cukup timpang, pemimpin pasar jelas' : gap > 5 ? 'distribusi moderat, persaingan merata' : 'pasar relatif homogen, banyak saham setara') + '</div>';
  document.getElementById('insight-leaders').innerHTML = h;

  var top10 = scored.filter(function(d) { return d._rank <= 10; });
  var n10 = top10.length;
  if (n10 > 0) {
    var sectors = {};
    top10.forEach(function(d) { var p = PF[d.ticker.split('.')[0]]; if (p) { sectors[p.sector] = (sectors[p.sector] || 0) + 1; } });
    var secList = Object.keys(sectors).sort(function(a, b) { return sectors[b] - sectors[a]; });
    var avg10 = function(k) { return top10.reduce(function(s, d) { return s + (+d[k]); }, 0) / n10; };
    var h2 = '<div class=\"insight-hdr\"><span class=\"insight-title\">Top 10 Ringkasan</span><span class=\"insight-badge b\">' + n10 + ' saham</span></div><div class=\"insight-grid\">';
    h2 += '<div class=\"insight-row\"><span class=\"insight-lbl\">Rerata Score</span><span class=\"insight-val\">' + avg10('_score').toFixed(1) + '</span></div>';
    h2 += '<div class=\"insight-row\"><span class=\"insight-lbl\">Quality / Growth</span><span class=\"insight-val\">' + avg10('quality').toFixed(1) + ' / ' + avg10('growth').toFixed(1) + '</span></div>';
    h2 += '<div class=\"insight-row\"><span class=\"insight-lbl\">Value / Momentum</span><span class=\"insight-val\">' + avg10('value').toFixed(1) + ' / ' + avg10('momentum').toFixed(1) + '</span></div>';
    h2 += '<div class=\"insight-row\"><span class=\"insight-lbl\">Sektor Dominan</span><span class=\"insight-val\">' + secList[0] + ' (' + sectors[secList[0]] + ')</span></div>';
    h2 += '</div>';
    if (secList.length > 1) { h2 += '<div class=\"insight-note\">Sektor: ' + secList.map(function(s) { return s + ' (' + sectors[s] + ')'; }).join(' \u00b7 ') + '</div>'; }
    document.getElementById('insight-top10').innerHTML = h2;
  }
}
renderInsights();

function st(tabIdx, btn) {
  document.querySelectorAll('.tab-nav .tab-btn').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
  document.querySelectorAll('.tc').forEach(function(c) { c.classList.remove('active'); });
  document.getElementById('t' + tabIdx).classList.add('active');
  if (tabIdx === 1) { renderTurnaround(); }
}

function renderTurnaround() {
  var tk = T.filter(function(r) { return r.context_match || r.transition_match; });
  tk.sort(function(a, b) { return (b.context_match + b.transition_match) - (a.context_match + a.transition_match); });
  var html = tk.map(function(r) {
    return '<tr><td class=\"tk tk-click\" data-ticker=\"' + r.ticker.split('.')[0] + '\" style=\"color:' + ac(r.ticker) + '\">' + r.ticker.split('.')[0] + '</td><td class=\"' + (r.context_match ? 'g' : 'r') + '\">' + ctxLabel(r) + '</td><td>' + (r.context_match ? r.context_days : 0) + '</td><td class=\"' + (r.transition_match ? 'g' : 'r') + '\">' + trnLabel(r) + '</td><td>' + (r.transition_match ? r.transition_days : 0) + '</td><td>' + fullLabel(r) + '</td><td>' + (r.last_update || '\u2014') + '</td></tr>';
  }).join('');
  document.getElementById('tbody-trn').innerHTML = html;

  var cx = tk.filter(function(r) { return r.context_match; }).sort(function(a, b) { return b.context_days - a.context_days; });
  var ctxCanvas = document.getElementById('ctx-chart');
  if (ctxCanvas && cx.length > 0) {
    new Chart(ctxCanvas, {
      type: 'bar', data: { labels: cx.map(function(r) { return r.ticker.split('.')[0]; }), datasets: [{ label: 'Context Days', data: cx.map(function(r) { return r.context_days; }), backgroundColor: '#3b82f6', borderRadius: 3 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: '#1e293b' } }, x: { grid: { display: false }, ticks: { color: '#94a3b8' } } } }
    });
  }
  var tx = tk.filter(function(r) { return r.transition_match; }).sort(function(a, b) { return b.transition_days - a.transition_days; });
  var trnCanvas = document.getElementById('trn-chart');
  if (trnCanvas && tx.length > 0) {
    new Chart(trnCanvas, {
      type: 'bar', data: { labels: tx.map(function(r) { return r.ticker.split('.')[0]; }), datasets: [{ label: 'Transition Days', data: tx.map(function(r) { return r.transition_days; }), backgroundColor: '#f59e0b', borderRadius: 3 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: '#1e293b' } }, x: { grid: { display: false }, ticks: { color: '#94a3b8' } } } }
    });
  }
}

function renderTop() {
  var w = getWeights();
  var scored = L.map(function(r) { return Object.assign({}, r, { _score: computeFinalScore(r, w) }); });
  scored.sort(function(a, b) { return b._score - a._score; });
  scored.forEach(function(r, i) { r._rank = i + 1; });
  var top10 = scored.filter(function(d) { return d._rank <= 10; });
  var h = '';
  top10.forEach(function(d) {
    var sym = d.ticker.split('.')[0];
    h += '<div class=\"top-candidate\" onclick=\"openPanel(\\'' + sym + '\\')\"><div><span class=\"tk\" style=\"color:' + ac(d.ticker) + '\">' + sym + '</span><span class=\"flag\" style=\"margin-left:2px\">#' + d._rank + '</span></div><div style=\"display:flex;gap:6px;margin-top:6px\">';
    ['quality', 'growth', 'value', 'momentum'].forEach(function(f) {
      var v = d[f]; var c = v >= 60 ? '#00d68f' : v >= 40 ? '#f59e0b' : '#ef4444';
      h += '<div style=\"background:#1e293b;border-radius:4px;padding:2px 6px;font-size:10px;color:' + c + ';min-width:20px;text-align:center\">' + f.charAt(0).toUpperCase() + ' ' + (+v).toFixed(0) + '</div>';
    });
    h += '</div><div style=\"display:flex;gap:8px;margin-top:4px;font-size:10px;color:#64748b\">';
    var p = PF[sym]; if (p) { h += '<span>' + p.sector + '</span>'; }
    h += '<span>Score ' + d._score.toFixed(1) + '</span></div></div>';
  });
  document.getElementById('top-candidates').innerHTML = h;
}
renderTop();

function renderHistory() {
  var h = SK.map(function(r) {
    var sym = r.ticker.split('.')[0];
    return '<tr><td class=\"tk\" style=\"color:' + ac(r.ticker) + '\">' + sym + '</td><td>' + r.context_days + '</td><td>' + r.transition_days + '</td><td>' + (r.first_context_detected || '\u2014') + '</td><td>' + (r.first_transition_detected || '\u2014') + '</td><td>' + r.total_entries + '</td></tr>';
  }).join('');
  document.getElementById('tbody-history').innerHTML = h;
}
renderHistory();

var es = { key: null, dir: 'asc' };
function re() {
  var flt = window._ef || 'all';
  var d = EX.slice();
  if (flt !== 'all') { d = d.filter(function(r) { return r.exit_state === flt; }); }
  d = sortData(d, es);
  var h = d.map(function(r) {
    var sym = r.ticker.split('.')[0];
    var rs20 = parseFloat(r.rs_20d) || 0;
    var rsChg = parseFloat(r.rs_change_20d) || 0;
    var dd = parseFloat(r.drawdown_from_entry) || 0;
    var rules = r.rules || '';
    var esClass = 'es-' + (r.exit_state || 'UNKNOWN').replace(/ /g, '-').toLowerCase();
    return '<tr><td class=\"tk\" style=\"color:' + ac(r.ticker) + '\">' + sym + '</td><td>' + r.rank + '</td><td class=\"' + (parseInt(r.rank_change) > 0 ? 'g' : parseInt(r.rank_change) < 0 ? 'r' : '') + '\">' + (r.rank_change > 0 ? '+' : '') + r.rank_change + '</td><td><span class=\"' + esClass + '\">' + r.exit_state + '</span></td><td style=\"font-size:11px\">' + rules + '</td><td class=\"' + (rs20 > 0 ? 'g' : 'r') + '\">' + pct(rs20) + '</td><td class=\"' + (rsChg > 0 ? 'g' : 'r') + '\">' + pct(rsChg) + '</td><td class=\"' + (r.close_above_ma50 === 'TRUE' || r.close_above_ma50 === 'True' ? 'g' : 'r') + '\">' + (r.close_above_ma50 === 'TRUE' || r.close_above_ma50 === 'True' ? 'Above' : 'Below') + '</td><td class=\"' + (r.close_above_ma100 === 'TRUE' || r.close_above_ma100 === 'True' ? 'g' : 'r') + '\">' + (r.close_above_ma100 === 'TRUE' || r.close_above_ma100 === 'True' ? 'Above' : 'Below') + '</td><td class=\"' + (dd < 0 ? 'r' : dd < -5 ? 'o' : 'g') + '\">' + (dd > 0 ? '+' : '') + dd.toFixed(1) + '%</td></tr>';
  }).join('');
  document.getElementById('tbody-exit').innerHTML = h;
}
function ef(v, btn) {
  window._ef = v;
  document.querySelectorAll('#t4 .tab-btn').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
  re();
}
re();

function stSub(tabId, subId, btn) {
  var parent = btn.parentElement;
  parent.querySelectorAll('.sub-tab-btn, .tab-btn').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
  document.getElementById('t' + tabId).querySelectorAll('.sub-tc').forEach(function(el) { el.classList.remove('active'); });
  document.getElementById('t' + tabId + '-' + subId).classList.add('active');
}

function renderComparisonCards() {
  var scores = BT.full;
  if (!scores) { document.getElementById('comparison-cards').innerHTML = '<p style="color:#64748b">No comparison data available.</p>'; return; }
  var h = '';
  ['config_b', 'config_f', 'ihsg'].forEach(function(cfg) {
    var d = scores[cfg];
    var label = cfg === 'config_b' ? 'Config B (Q25/G30/V10/M35)' : cfg === 'config_f' ? 'Config F (Q25/G10/V30/M35)' : 'IHSG';
    h += '<div class=\"card\"><div class=\"card-label\">' + label + '</div><div style=\"margin-top:8px\">';
    h += '<div class=\"insight-row\"><span class=\"insight-lbl\">CAGR</span><span class=\"insight-val ' + (d.cagr > 0 ? 'g' : 'r') + '\">' + (d.cagr >= 0 ? '+' : '') + d.cagr.toFixed(2) + '%</span></div>';
    h += '<div class=\"insight-row\"><span class=\"insight-lbl\">Total Return</span><span class=\"insight-val ' + (d.total_return >= 0 ? 'g' : 'r') + '\">' + (d.total_return >= 0 ? '+' : '') + d.total_return.toFixed(2) + '%</span></div>';
    h += '<div class=\"insight-row\"><span class=\"insight-lbl\">Max DD</span><span class=\"insight-val r\">' + d.max_dd.toFixed(2) + '%</span></div>';
    h += '<div class=\"insight-row\"><span class=\"insight-lbl\">Sharpe</span><span class=\"insight-val ' + (d.sharpe > 0.5 ? 'g' : d.sharpe > 0 ? 'y' : 'r') + '\">' + d.sharpe.toFixed(2) + '</span></div>';
    if (d.volatility) h += '<div class=\"insight-row\"><span class=\"insight-lbl\">Volatility</span><span class=\"insight-val\">' + d.volatility.toFixed(2) + '%</span></div>';
    if (d.win_rate) h += '<div class=\"insight-row\"><span class=\"insight-lbl\">Win Rate</span><span class=\"insight-val\">' + (d.win_rate * 100).toFixed(1) + '%</span></div>';
    h += '</div></div>';
  });
  document.getElementById('comparison-cards').innerHTML = h;
}
renderComparisonCards();

function switchPeriod(period, btn) {
  document.querySelectorAll('#t6-2 .period-btn').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
  var pd = BT.periods[period];
  if (!pd) { document.getElementById('period-cards').innerHTML = '<p style="color:#64748b">No data for this period.</p>'; return; }
  var h = '';
  ['config_b', 'config_f', 'ihsg'].forEach(function(cfg) {
    var d = pd[cfg];
    var label = cfg === 'config_b' ? 'Config B' : cfg === 'config_f' ? 'Config F' : 'IHSG';
    h += '<div class=\"card\"><div class=\"card-label\">' + label + '</div><div style=\"margin-top:8px\">';
    h += '<div class=\"insight-row\"><span class=\"insight-lbl\">CAGR</span><span class=\"insight-val ' + (d.cagr > 0 ? 'g' : 'r') + '\">' + (d.cagr >= 0 ? '+' : '') + d.cagr.toFixed(2) + '%</span></div>';
    h += '<div class=\"insight-row\"><span class=\"insight-lbl\">Max DD</span><span class=\"insight-val r\">' + d.max_dd.toFixed(2) + '%</span></div>';
    h += '<div class=\"insight-row\"><span class=\"insight-lbl\">Sharpe</span><span class=\"insight-val ' + (d.sharpe > 0.5 ? 'g' : d.sharpe > 0 ? 'y' : 'r') + '\">' + d.sharpe.toFixed(2) + '</span></div>';
    h += '</div></div>';
  });
  document.getElementById('period-cards').innerHTML = h;
}

var equityChart, riskChart;
(function() {
  var labels = WI.labels || WI.month_labels || [];
  var cb = WI.config_b || WI.equity_b || [];
  var cf = WI.config_f || WI.equity_f || [];
  var ihsg = WI.ihsg || WI.equity_i || [];
  var ctx = document.getElementById('equityChart');
  if (ctx && labels.length > 0 && cb.length > 0) {
    equityChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          { label: 'Config B', data: cb, borderColor: '#60a5fa', backgroundColor: 'rgba(96,165,250,0.05)', fill: false, tension: 0.2, pointRadius: 0 },
          { label: 'Config F', data: cf, borderColor: '#00d68f', backgroundColor: 'rgba(0,214,143,0.05)', fill: false, tension: 0.2, pointRadius: 0 },
          { label: 'IHSG', data: ihsg, borderColor: '#94a3b8', backgroundColor: 'rgba(148,163,184,0.05)', fill: false, tension: 0.2, pointRadius: 0, borderDash: [4, 4] }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        plugins: {
          legend: { labels: { color: '#94a3b8', font: { size: 12 } } },
          tooltip: { mode: 'index', intersect: false, backgroundColor: '#0f172a', titleColor: '#e8edf5', bodyColor: '#94a3b8', borderColor: '#1e293b', borderWidth: 1 }
        },
        scales: {
          x: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8', font: { size: 11 }, maxTicksLimit: 12 } },
          y: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8', font: { size: 11 }, callback: function(v) { return 'Rp' + v.toLocaleString() + 'jt'; } } }
        }
      }
    });
  }

  var rctx = document.getElementById('riskChart');
  if (rctx && BT.full) {
    var s = BT.full;
    riskChart = new Chart(rctx, {
      type: 'bubble',
      data: {
        datasets: [
          { label: 'Config B', data: [{ x: s.config_b.max_dd, y: s.config_b.cagr, r: Math.min(Math.max(Math.abs(s.config_b.sharpe) * 10, 8), 25) }], backgroundColor: 'rgba(96,165,250,0.6)', borderColor: '#60a5fa', borderWidth: 2 },
          { label: 'Config F', data: [{ x: s.config_f.max_dd, y: s.config_f.cagr, r: Math.min(Math.max(Math.abs(s.config_f.sharpe) * 10, 8), 25) }], backgroundColor: 'rgba(0,214,143,0.6)', borderColor: '#00d68f', borderWidth: 2 },
          { label: 'IHSG', data: [{ x: s.ihsg.max_dd, y: s.ihsg.cagr, r: Math.min(Math.max(Math.abs(s.ihsg.sharpe) * 10, 8), 25) }], backgroundColor: 'rgba(148,163,184,0.4)', borderColor: '#94a3b8', borderWidth: 2 }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { labels: { color: '#94a3b8', font: { size: 12 } } },
          tooltip: { callbacks: { label: function(ctx) { var d = ctx.raw; return ctx.dataset.label + ': CAGR ' + d.y.toFixed(2) + '%, MaxDD ' + d.x.toFixed(2) + '%'; } } }
        },
        scales: {
          x: { title: { display: true, text: 'Max Drawdown (%)', color: '#94a3b8' }, grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } },
          y: { title: { display: true, text: 'CAGR (%)', color: '#94a3b8' }, grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } }
        }
      }
    });
  }
})();

(function() {
  var timelineEvents = [
    { date: 'Nov 2024', title: 'ISI Project Started', desc: 'Initial data collection and scoring prototype for Indonesia stock screening.' },
    { date: 'Dec 2024', title: 'Turnaround Detection', desc: 'Context/transition matching algorithm developed for identifying potential reversals.' },
    { date: 'Jan 2025', title: 'V1 Dashboard', desc: 'First dashboard with leaders ranking, exit monitor, and basic insights.' },
    { date: 'Mar 2025', title: 'Factor System', desc: 'Four-factor scoring system (Quality, Growth, Value, Momentum) implemented.' },
    { date: 'Apr 2025', title: 'V2 Dashboard', desc: 'Complete redesign with turnaround detection, stock profiles, and Chart.js integration.' },
    { date: 'Jun 2025', title: 'Q1 2025 Audit', desc: 'Year-end audit and research review. Growth Factor and scoring weights reviewed.' },
    { date: 'Apr\u2013May 2026', title: 'Research Phase', desc: 'RESEARCH-013 series: growth reconciliation (013D), period sensitivity (013E), weight optimization.' },
    { date: 'Jun 2026', title: 'V3 Dashboard \u00b7 ADR-005', desc: 'Config F (Q25/G10/V30/M35) production config approved. V3 dashboard with config switcher, factor panel, simulation lab, and research timeline.' }
  ];
  var h = '<div class=\"timeline\">';
  timelineEvents.forEach(function(ev, i) {
    h += '<div class="tl-item' + (i === timelineEvents.length - 1 ? ' active' : '') + '" onclick="document.querySelector(\\'.tl-item.active\\').classList.remove(\\'active\\');this.classList.add(\\'active\\')"><div class="tl-dot"></div><div class="tl-date">' + ev.date + '</div><div class="tl-title">' + ev.title + '</div><div class="tl-desc">' + ev.desc + '</div></div>';
  });
  h += '</div>';
  document.getElementById('timeline-container').innerHTML = h;
})();

function tickerData(sym) {
  var tk = sym + '.JK';
  var l = null, pf = null, fd = null, ed = null, w = getWeights();
  L.forEach(function(d) { if (d.ticker === tk) l = d; });
  if (PF[sym]) pf = PF[sym];
  if (FD[sym]) fd = FD[sym];
  EX.forEach(function(d) { if (d.ticker === tk) ed = d; });
  var score = l ? computeFinalScore(l, w) : 0;
  return { ticker: tk, sym: sym, leader: l, profile: pf, fundamentals: fd, exit: ed, score: score };
}

function aiExplain(sym) {
  var d = tickerData(sym);
  if (d.leader && d.profile) {
    var w = getWeights();
    var factors = [
      { name: 'Quality', val: d.leader.quality, weight: w.quality, ic: IC.quality.ic },
      { name: 'Growth', val: d.leader.growth, weight: w.growth, ic: IC.growth.ic },
      { name: 'Value', val: d.leader.value, weight: w.value, ic: IC.value.ic },
      { name: 'Momentum', val: d.leader.momentum, weight: w.momentum, ic: IC.momentum.ic }
    ];
    var topFactor = factors.slice().sort(function(a, b) { return b.val - a.val; })[0];
    var strongest = factors.filter(function(f) { return f.val >= 60; }).map(function(f) { return f.name; });
    var weakest = factors.filter(function(f) { return f.val < 40; }).map(function(f) { return f.name; });
    var narrative = d.sym + ' (' + d.profile.sector + ') scores ' + d.score.toFixed(1) + ' with ' + configLabel() + '. Highest factor: ' + topFactor.name + ' (' + topFactor.val.toFixed(1) + '). ';
    narrative += 'IC ' + (topFactor.ic > 0 ? 'positive' : 'negative') + ' (' + (topFactor.ic > 0 ? '+' : '') + topFactor.ic.toFixed(4) + ') \u2014 this factor has been ' + (topFactor.ic > 0.02 ? 'strongly predictive' : topFactor.ic > 0 ? 'modestly predictive' : 'non-predictive') + ' historically. ';
    if (strongest.length > 0) narrative += 'Strengths: ' + strongest.join(', ') + '. ';
    if (weakest.length > 0) narrative += 'Weaknesses: ' + weakest.join(', ') + '. ';
    if (d.exit) narrative += 'Exit state: ' + d.exit.exit_state + '.';
    return narrative;
  }
  return 'Insufficient data for ' + sym + '.';
}

function renderScoreBreakdown(d) {
  var w = getWeights();
  var factors = [
    { key: 'quality', name: FNAMES.quality, val: d.leader.quality, weight: w.quality, ic: IC.quality.ic, role: IC.quality.role },
    { key: 'growth', name: FNAMES.growth, val: d.leader.growth, weight: w.growth, ic: IC.growth.ic, role: IC.growth.role },
    { key: 'value', name: FNAMES.value, val: d.leader.value, weight: w.value, ic: IC.value.ic, role: IC.value.role },
    { key: 'momentum', name: FNAMES.momentum, val: d.leader.momentum, weight: w.momentum, ic: IC.momentum.ic, role: IC.momentum.role }
  ];
  var h = '<div class=\"card-label\">Score Breakdown \u00b7 ' + configLabel() + '</div><div class=\"breakdown-grid\">';
  factors.forEach(function(f) {
    var weighted = f.val * f.weight;
    var scoreClass = f.val >= 60 ? 'g' : f.val >= 40 ? 'y' : 'r';
    var barC = f.val >= 60 ? '#00d68f' : f.val >= 40 ? '#f59e0b' : '#ef4444';
    h += '<div class=\"breakdown-row\"><div class=\"bf-hdr\"><span>' + f.name + '</span><span class=\"' + scoreClass + '\">' + f.val.toFixed(1) + ' \u00d7 ' + (f.weight * 100).toFixed(0) + '% = ' + weighted.toFixed(1) + '</span></div>';
    h += '<div class=\"bar\"><div class=\"bar-track\"><div class=\"bar-fill\" style=\"width:' + Math.min(f.val, 100) + '%;background:' + barC + '\"></div></div></div>';
    h += '<div style=\"font-size:10px;color:#64748b;margin-top:2px\">IC ' + (f.ic > 0 ? '+' : '') + f.ic.toFixed(4) + ' \u00b7 ' + f.role + '</div></div>';
  });
  var total = factors.reduce(function(s, f) { return s + f.val * f.weight; }, 0);
  h += '<div class=\"breakdown-total\">Final Score: <span class=\"' + (total >= 60 ? 'g' : total >= 40 ? 'y' : 'r') + '\">' + total.toFixed(1) + '</span> / 100</div>';
  h += '</div>';
  return h;
}

function renderFundamentals(fd) {
  if (!fd) return '<div class=\"card-sub\">No fundamental data available.</div>';
  var h = '<div style=\"display:grid;grid-template-columns:1fr 1fr;gap:6px 16px;margin-top:8px\">';
  var shown = ['market_cap', 'pe_ttm', 'pbv', 'roe', 'debt_to_equity', 'current_ratio', 'revenue_growth', 'net_profit_margin', 'dividend_yield', 'eps_growth_1y'];
  var labels = { market_cap: 'Market Cap', pe_ttm: 'P/E TTM', pbv: 'P/BV', roe: 'ROE', debt_to_equity: 'D/E', current_ratio: 'Current Ratio', revenue_growth: 'Rev Growth', net_profit_margin: 'Net Margin', dividend_yield: 'Div Yield', eps_growth_1y: 'EPS Growth 1Y' };
  shown.forEach(function(k) {
    if (fd[k] !== undefined && fd[k] !== null) {
      var v = fd[k];
      var cls = '';
      if (k === 'roe' || k === 'revenue_growth' || k === 'net_profit_margin' || k === 'eps_growth_1y') { cls = v > 0 ? 'g' : 'r'; }
      if (k === 'debt_to_equity') { cls = v < 1 ? 'g' : v < 2 ? 'y' : 'r'; }
      if (k === 'pe_ttm') { cls = v > 0 && v < 30 ? 'g' : v > 0 ? 'y' : 'r'; }
      h += '<div class=\"insight-row\"><span class=\"insight-lbl\">' + (labels[k] || k) + '</span><span class=\"insight-val ' + cls + '\">' + (typeof v === 'number' ? (v % 1 === 0 ? v.toLocaleString() : v.toFixed(2)) : v) + '</span></div>';
    }
  });
  h += '</div>';
  return h;
}

function renderAlignment(sym) {
  var pf = PF[sym];
  if (!pf) return '<div class=\"card-sub\">No profile data.</div>';
  var h = '<div class=\"card-label\">Sector & Industry Alignment</div><div style=\"margin-top:6px;display:grid;grid-template-columns:1fr 1fr;gap:6px 16px\">';
  h += '<div class=\"insight-row\"><span class=\"insight-lbl\">Sector</span><span class=\"insight-val\">' + (pf.sector || '\u2014') + '</span></div>';
  h += '<div class=\"insight-row\"><span class=\"insight-lbl\">Industry</span><span class=\"insight-val\">' + (pf.industry || '\u2014') + '</span></div>';
  if (pf.sector_rank) h += '<div class=\"insight-row\"><span class=\"insight-lbl\">Sector Rank</span><span class=\"insight-val\">#' + pf.sector_rank + '</span></div>';
  if (pf.peers) h += '<div class=\"insight-row\"><span class=\"insight-lbl\">Peers</span><span class=\"insight-val\" style=\"font-size:11px\">' + pf.peers.join(', ') + '</span></div>';
  h += '</div>';
  return h;
}

function openPanel(sym) {
  var d = tickerData(sym);
  document.getElementById('ptk').textContent = sym;
  document.getElementById('ptk').style.color = ac(sym + '.JK');
  document.getElementById('pname').textContent = d.profile ? d.profile.name || d.profile.sector || '' : '';
  var body = document.getElementById('pbody');
  body.innerHTML = '<div class=\"ai-explain\">' + aiExplain(sym) + '</div>';
  body.innerHTML += renderScoreBreakdown(d);
  body.innerHTML += '<div style=\"margin-top:12px\">' + renderFundamentals(d.fundamentals) + '</div>';
  body.innerHTML += '<div style=\"margin-top:12px\">' + renderAlignment(sym) + '</div>';
  if (d.exit) {
    body.innerHTML += '<div style=\"margin-top:12px\"><div class=\"card-label\">Exit Status</div><div style=\"margin-top:6px\"><span class=\"es-' + d.exit.exit_state.toLowerCase().replace(/ /g, '-') + '\">' + d.exit.exit_state + '</span> \u2014 ' + (d.exit.rules || 'No rules triggered') + '</div></div>';
  }
  document.getElementById('overlay').classList.add('active');
  document.getElementById('panel').classList.add('active');
}

function closePanel() {
  document.getElementById('overlay').classList.remove('active');
  document.getElementById('panel').classList.remove('active');
}

document.addEventListener('click', function(e) {
  var tkEl = e.target.closest('.tk-click');
  if (tkEl) { openPanel(tkEl.getAttribute('data-ticker') || tkEl.textContent.trim()); }
});
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') { closePanel(); } });

console.log('ISI Dashboard V3 loaded. Config:', activeConfig, 'Tickers:', L.length);
</script>
</body></html>"""

def build_html(leaders, turnaround, summary, history, streaks, report_date, exit_data=None, profiles=None, fundamentals=None, radar_status=None, today=None, config_weights=None, warehouse_info=None):
    summary_data = summary if isinstance(summary, dict) else {}
    cw_b = CONFIG_B_WEIGHTS
    cw_f = config_weights if config_weights else {"quality": 0.25, "growth": 0.10, "value": 0.30, "momentum": 0.35}
    wi = warehouse_info if warehouse_info else get_warehouse_info()

    leaders_json = json.dumps(leaders)
    turnaround_json = json.dumps(turnaround)
    summary_json = json.dumps(summary_data)
    streaks_json = json.dumps(streaks)
    exit_json = json.dumps(exit_data if exit_data else [])
    profiles_json = json.dumps(profiles if profiles else {})
    fundamentals_json = json.dumps(fundamentals if fundamentals else {})
    cw_b_json = json.dumps(cw_b)
    cw_f_json = json.dumps(cw_f)
    warehouse_json = json.dumps(wi)
    ic_json = json.dumps(IC_VALUES)
    bt_json = json.dumps(BACKTEST_RESULTS)
    fcolors_json = json.dumps(FACTOR_COLORS)
    fnames_json = json.dumps(FACTOR_LABELS)

    warehouse_range = f"{wi.get('start', '2022-01')} \u2192 {wi.get('end', '2026-05')} ({wi.get('months', 53)}mo)"

    display_date = today if today else report_date

    ctx_match_count = summary_data.get('context_match_count', 0)
    trn_match_count = summary_data.get('transition_match_count', 0)

    file_age_leaders = file_age(LEADERS_FILE, report_date)
    file_age_turnaround = file_age(TURNAROUND_FILE, report_date)
    file_age_exit = file_age(EXIT_FILE, report_date)
    universe_size = summary_data.get('universe_size', 0)
    report_date_val = summary_data.get('date', 'N/A')
    history_len = len(history)
    history_len = max(history_len, len(streaks))

    substitutions = {
        'leaders_json': leaders_json,
        'turnaround_json': turnaround_json,
        'summary_json': summary_json,
        'streaks_json': streaks_json,
        'exit_json': exit_json,
        'profiles_json': profiles_json,
        'fundamentals_json': fundamentals_json,
        'cw_b_json': cw_b_json,
        'cw_f_json': cw_f_json,
        'warehouse_json': warehouse_json,
        'ic_json': ic_json,
        'bt_json': bt_json,
        'fcolors_json': fcolors_json,
        'fnames_json': fnames_json,
        'warehouse_range': warehouse_range,
        'report_date': display_date or '',
        'ctx_match_count': str(ctx_match_count),
        'trn_match_count': str(trn_match_count),
        'file_age_leaders': file_age_leaders,
        'file_age_turnaround': file_age_turnaround,
        'file_age_exit': file_age_exit,
        'universe_size': str(universe_size),
        'report_date_val': report_date_val,
        'history_len': str(history_len),
    }

    html = TEMPLATE
    for k, v in substitutions.items():
        html = html.replace('{' + k + '}', str(v))

    return html


def main():
    import os
    from datetime import datetime

    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(base_dir)
    data_dir = os.path.join(project_dir, "data", "current")

    def load_csv(path):
        if not os.path.exists(path):
            return []
        with open(path, newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))

    def load_json(path):
        if not os.path.exists(path):
            return {}
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    leaders = load_csv(os.path.join(data_dir, "leaders_latest.csv"))
    turnaround = load_csv(os.path.join(data_dir, "turnaround_latest.csv"))
    exit_data = load_csv(os.path.join(data_dir, "exit_watchlist_latest.csv"))
    summary_data = load_csv(os.path.join(data_dir, "summary_latest.csv"))
    summary_data = summary_data[0] if summary_data else {}
    streaks = load_csv(os.path.join(data_dir, "streaks_history.csv"))
    profiles = load_json(os.path.join(project_dir, "data", "current", "stock_profiles.json"))
    fundamentals = load_json(os.path.join(project_dir, "data", "current", "fundamentals.json"))
    scoring_weights = load_json(os.path.join(project_dir, "config", "scoring_weights.json"))

    config_weights = {
        "quality": float(scoring_weights.get("quality", 0.25)),
        "growth": float(scoring_weights.get("growth", 0.10)),
        "value": float(scoring_weights.get("value", 0.30)),
        "momentum": float(scoring_weights.get("momentum", 0.35)),
    }

    warehouse_info = get_warehouse_info()
    history = load_csv(os.path.join(project_dir, "database", "historical", "turnaround_history.csv"))
    report_date = summary_data.get("date", datetime.now().strftime("%Y-%m-%d"))

    html = build_html(
        leaders, turnaround, summary_data, history, streaks, report_date,
        exit_data=exit_data,
        profiles=profiles,
        fundamentals=fundamentals,
        config_weights=config_weights,
        warehouse_info=warehouse_info,
    )

    output_path = os.path.join(project_dir, "dashboard", "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Dashboard V3 written to {output_path} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
