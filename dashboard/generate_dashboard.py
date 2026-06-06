
# file: dashboard/generate_dashboard.py

import json
import pandas as pd
from pathlib import Path
import datetime
import traceback

# Static mapping for IDX30 names, sectors
TICKER_INFO = {
    'ADRO.JK': {'name': 'Adaro Energy', 'sector': 'Coal'},
    'ESSA.JK': {'name': 'Essa Industries', 'sector': 'Chemicals'},
    'MAPI.JK': {'name': 'Mitra Adiperkasa', 'sector': 'Retail'},
    'PTBA.JK': {'name': 'Bukit Asam', 'sector': 'Coal'},
    'AKRA.JK': {'name': 'AKRA Corporindo', 'sector': 'Distribution'},
    'CPIN.JK': {'name': 'Charoen Pokphand', 'sector': 'Poultry'},
    'ANTM.JK': {'name': 'Aneka Tambang', 'sector': 'Mining'},
    'EXCL.JK': {'name': 'XL Axiata', 'sector': 'Telecom'},
    'BBRI.JK': {'name': 'Bank Rakyat Indonesia', 'sector': 'Banking'},
    'BMRI.JK': {'name': 'Bank Mandiri', 'sector': 'Banking'},
    'BRPT.JK': {'name': 'Barito Pacific', 'sector': 'Chemicals'},
    'BBNI.JK': {'name': 'Bank Negara Indonesia', 'sector': 'Banking'},
    'INDF.JK': {'name': 'Indofood Sukses', 'sector': 'Consumer'},
    'PGAS.JK': {'name': 'PGAS', 'sector': 'Gas'},
    'MDKA.JK': {'name': 'Merdeka Copper Gold', 'sector': 'Mining'},
    'ITMG.JK': {'name': 'Indo Tambangraya', 'sector': 'Coal'},
    'TLKM.JK': {'name': 'Telkom Indonesia', 'sector': 'Telecom'},
    'ASII.JK': {'name': 'Astra International', 'sector': 'Conglomerate'},
    'INTP.JK': {'name': 'Indocement', 'sector': 'Cement'},
    'ICBP.JK': {'name': 'Indofood CBP', 'sector': 'Consumer'},
    'BBCA.JK': {'name': 'Bank Central Asia', 'sector': 'Banking'},
    'UNTR.JK': {'name': 'United Tractors', 'sector': 'Heavy Equip'},
    'MIKA.JK': {'name': 'Mitra Keluarga', 'sector': 'Healthcare'},
    'GOTO.JK': {'name': 'GoTo Gojek Tokopedia', 'sector': 'Tech'},
    'SMGR.JK': {'name': 'Semen Indonesia', 'sector': 'Cement'},
    'SIDO.JK': {'name': 'Industri Jamu Sido Muncul', 'sector': 'Consumer'},
    'TPIA.JK': {'name': 'Chandra Asri', 'sector': 'Chemicals'},
    'KLBF.JK': {'name': 'Kalbe Farma', 'sector': 'Healthcare'},
    'AMMN.JK': {'name': 'Amman Mineral', 'sector': 'Mining'},
    'HEAL.JK': {'name': 'Medikaloka Hermina', 'sector': 'Healthcare'}
}

def load_json(filepath):
    path = Path(filepath)
    if not path.exists():
        print(f"WARNING: File {filepath} not found.")
        return [] if filepath.endswith("ranking.json") or filepath.endswith("v3.json") else {}
    with open(path, 'r') as f:
        return json.load(f)

def get_action_slug_and_label(row):
    try:
        q = float(row.get('quality', 0))
    except (ValueError, TypeError):
        q = 0.0
    try:
        g = float(row.get('growth', 0))
    except (ValueError, TypeError):
        g = 0.0
    try:
        v = float(row.get('value', 0))
    except (ValueError, TypeError):
        v = 0.0
    try:
        m = float(row.get('momentum', 0))
    except (ValueError, TypeError):
        m = 0.0

    if m > 85 and v < 40:
        return 'risk', '⚠ Rawan'
    elif m >= 55 and m <= 85 and q > 45 and v > 40:
        return 'hot', '🚀 Anget'
    elif v > 70 and m < 40:
        return 'dead', '⚓ Mati'
    elif m > 80 and q < 40 and g < 40:
        return 'junk', '🗑 Goreng'
    else:
        return 'watch', '— Pantau'

def local_percentile_normalize(values):
    n = len(values)
    if n == 0:
        return []
    if n <= 1 or max(values) == min(values):
        return [50.0 for _ in values]
    scores = []
    for v in values:
        lesser = sum(1 for x in values if x < v)
        equal = sum(1 for x in values if x == v)
        rank = lesser + (equal - 1) / 2.0
        score = (rank / (n - 1)) * 100
        scores.append(round(score, 2))
    return scores

def load_fallback_vol_ratios():
    fallback = {}
    try:
        history_path = Path("output/radar_history.json")
        if history_path.exists():
            with open(history_path, "r") as f:
                history_data = json.load(f)
            if history_data and isinstance(history_data, list):
                latest_entry = history_data[-1]
                details = latest_entry.get("ringkasan_volume_hari_itu", {}).get("detail", [])
                for item in details:
                    parts = item.split(":")
                    if len(parts) >= 2:
                        ticker = parts[0].strip()
                        val_str = parts[1].replace("Volume", "").replace("x", "").split("(")[0].strip()
                        try:
                            fallback[ticker] = float(val_str)
                        except ValueError:
                            pass
    except Exception as e:
        print(f"Warning: Failed to load fallback volume ratios: {e}")
    return fallback

def get_volume_ratios(tickers):
    vol_ratios = load_fallback_vol_ratios()
    try:
        import yfinance as yf
        print(f"Downloading daily volume data for {len(tickers)} stocks...")
        df = yf.download(tickers, period="1mo", progress=False)
        if not df.empty:
            for ticker in tickers:
                try:
                    if isinstance(df.columns, pd.MultiIndex):
                        ticker_df = df.xs(ticker, axis=1, level=1)
                    else:
                        ticker_df = df
                    
                    ticker_df = ticker_df.dropna(subset=['Volume'])
                    if len(ticker_df) >= 21:
                        ma20 = ticker_df['Volume'].rolling(20).mean().iloc[-1]
                        curr = ticker_df['Volume'].iloc[-1]
                        if ma20 > 0:
                            vol_ratios[ticker] = round(float(curr / ma20), 2)
                except Exception as inner_e:
                    pass
    except Exception as e:
        print(f"Warning: Failed to download yfinance data or offline: {e}")
    return vol_ratios

def generate_dashboard():
    print("--- Building ISI V8.4 Modern Quant Dashboard ---")
    
    # 1. Load all data
    final_scores = load_json("output/scores/final_ranking_v3.json")
    q_data = load_json("output/scores/quality_ranking.json")
    v_data = load_json("output/scores/value_ranking.json")
    g_data = load_json("output/scores/growth_ranking.json")
    m_data = load_json("output/scores/momentum_ranking.json")
    
    fundamentals_data = load_json("output/raw/fundamentals.json")
    growth_data = load_json("output/raw/growth.json")
    
    # Load Sector Rules
    sector_rules = load_json("config/sector_rules.json")
    banks = sector_rules.get("financial_banks", [])
    commodity_cyclical = sector_rules.get("commodity_cyclical", [])

    # Convert factor data to dict for fast lookup
    q_scores = {x.get('ticker'): x.get('quality_score') for x in q_data} if isinstance(q_data, list) else {}
    v_scores = {x.get('ticker'): x.get('value_score') for x in v_data} if isinstance(v_data, list) else {}
    g_scores = {x.get('ticker'): x.get('growth_score') for x in g_data} if isinstance(g_data, list) else {}
    m_scores = {x.get('ticker'): x.get('momentum') for x in m_data} if isinstance(m_data, list) else {}
    
    # Get return_6m (RS) from momentum
    m_rs6m = {x.get('ticker'): x.get('return_6m') for x in m_data} if isinstance(m_data, list) else {}

    # Calculate FCF percentile scores dynamically
    fcf_percentiles = {}
    if isinstance(q_data, list) and len(q_data) > 0:
        tickers_fcf = [(x["ticker"], x.get("free_cash_flow", 0)) for x in q_data]
        fcf_vals = [tf[1] for tf in tickers_fcf]
        fcf_norm = local_percentile_normalize(fcf_vals)
        fcf_percentiles = {tickers_fcf[i][0]: int(fcf_norm[i]) for i in range(len(tickers_fcf))}

    # Load Portfolio Warehouse
    try:
        df_port = pd.read_csv("database/historical/portfolio_warehouse.csv")
        latest_month = df_port['date'].max()
    except Exception as e:
        print(f"WARNING: Failed to load Portfolio Warehouse. Error: {e}")
        latest_month = datetime.datetime.now().strftime("%Y-%m")

    # Determine active portfolio (stocks labeled 'Sedang Anget')
    current_portfolio = []
    if isinstance(final_scores, list):
        for item in final_scores:
            ticker = item.get("ticker", "UNKNOWN")
            q = q_scores.get(ticker, 0)
            v = v_scores.get(ticker, 0)
            g = g_scores.get(ticker, 0)
            m = m_scores.get(ticker, 0)
            slug, _ = get_action_slug_and_label({
                'quality': q,
                'growth': g,
                'value': v,
                'momentum': m
            })
            if slug == 'hot':
                current_portfolio.append(ticker)
                if len(current_portfolio) == 5:
                    break

    # Load Daily Radar Status
    radar_data = load_json("output/daily_radar_status.json")
    if isinstance(radar_data, dict):
        radar_update = radar_data.get("last_update", "Not Available")
        radar_status = radar_data.get("status", "UNKNOWN")
        radar_narrative = radar_data.get("detail_message", "AI narrative not available.")
    else:
        radar_update = "Not Available"
        radar_status = "UNKNOWN"
        radar_narrative = "AI narrative not available."

    # Determine daily badge
    if radar_status == "SAFE":
        radar_badge_class = "sbadge"
        radar_badge_dot = '<span class="sdot"></span>'
        radar_badge_text = "SAFE / AMAN"
    elif radar_status == "WARNING":
        radar_badge_class = "sbadge"
        radar_badge_dot = '<span class="sdot" style="background:#ef4444;animation:pu 1.5s infinite;"></span>'
        radar_badge_text = "WARNING / WASPADA"
    else:
        radar_badge_class = "sbadge"
        radar_badge_dot = '<span class="sdot" style="background:#64748b;"></span>'
        radar_badge_text = "NOT AVAILABLE"

    # Get volume ratios
    tickers_list = [item.get("ticker") for item in final_scores if item.get("ticker")]
    vol_ratios = get_volume_ratios(tickers_list)

    # 2. Build Data List of Dicts for JavaScript
    stocks_js_list = []
    rank = 1
    for item in final_scores:
        ticker = item.get("ticker", "UNKNOWN")
        ticker_clean = ticker.split('.')[0]
        final = item.get("final_score", 0)
        
        q = q_scores.get(ticker, 0)
        g = g_scores.get(ticker, 0)
        v = v_scores.get(ticker, 0)
        m = m_scores.get(ticker, 0)
        
        slug, label = get_action_slug_and_label({
            'quality': q,
            'growth': g,
            'value': v,
            'momentum': m
        })
        
        meta = TICKER_INFO.get(ticker, {'name': ticker_clean, 'sector': 'Other', 'logo': ''})
        fund = fundamentals_data.get(ticker, {})
        grow = growth_data.get(ticker, {})
        
        roe = fund.get("roe")
        roe_val = round(roe * 100, 1) if roe is not None else None
        
        npm = fund.get("net_margin")
        npm_val = round(npm * 100, 1) if npm is not None else None
        
        opm = fund.get("operating_margin")
        opm_val = round(opm * 100, 1) if opm is not None else None
        
        der = fund.get("debt_to_equity")
        der_val = round(der * 100, 1) if der is not None else None
        
        pe = fund.get("pe_ratio")
        pe_val = round(pe, 1) if pe is not None else None
        
        pb = fund.get("pb_ratio")
        pb_val = round(pb, 1) if pb is not None else None
        
        fcf = fcf_percentiles.get(ticker, 50)
        
        rev_g = grow.get("revenue_growth")
        rev_g_val = round(rev_g * 100, 1) if rev_g is not None else None
        
        ni_g = grow.get("earnings_growth")
        ni_g_val = round(ni_g * 100, 1) if ni_g is not None else None
        
        rs6 = m_rs6m.get(ticker)
        rs6_val = round(rs6 * 100, 1) if rs6 is not None else None
        
        vol_ratio = vol_ratios.get(ticker, 1.0)
        
        is_bank = ticker in banks
        is_commodity = ticker in commodity_cyclical
        
        stocks_js_list.append({
            'r': rank,
            't': ticker_clean,
            'name': meta['name'],
            'sector': meta['sector'],
            'q': q,
            'g': g,
            'v': v,
            'm': m,
            'f': final,
            's': slug,
            'port': ticker in current_portfolio,
            'roe': roe_val,
            'npm': npm_val,
            'opm': opm_val,
            'der': der_val,
            'pe': pe_val,
            'pb': pb_val,
            'fcf': fcf,
            'rev_g': rev_g_val,
            'ni_g': ni_g_val,
            'rs6m': rs6_val,
            'vol_ratio': vol_ratio,
            'is_bank': is_bank,
            'is_commodity': is_commodity
        })
        rank += 1

    # Score-Weighted Portfolio Allocation
    top5 = [s for s in stocks_js_list if s['port']]
    if len(top5) > 5:
        top5 = top5[:5]
    total_score = sum(s['f'] for s in top5)
    prev_weights = {}
    try:
        prev_data = load_json('dashboard/data.json')
        for p in prev_data:
            if p.get('port'):
                prev_weights[p['t']] = float(p.get('weight', 0))
    except Exception:
        pass
    rebalance_needed = False
    for s in top5:
        raw_weight = (s['f'] / total_score) * 100 if total_score else 0
        weight = min(max(raw_weight, 10), 30)
        s['weight'] = f"{weight:.1f}%"
        prev = prev_weights.get(s['t'], 0)
        if abs(weight - prev) > 5:
            rebalance_needed = True

    stocks_json_str = json.dumps(stocks_js_list, indent=2)

    # 3. Build HTML Template with Advanced Features
    # Prepare sector list for filter dropdown
    sectors = sorted(list(set([s['sector'] for s in stocks_js_list])))
    sector_options = '\n'.join([f'<option value="{sec}">{sec}</option>' for sec in sectors])

    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ISI V8.4 | Quant Dashboard</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
    *{{box-sizing:border-box;margin:0;padding:0;}}
    *::-webkit-scrollbar{{width:6px;height:6px;}}
    *::-webkit-scrollbar-track{{background:#111417;}}
    *::-webkit-scrollbar-thumb{{background:#222830;border-radius:3px;}}
    *::-webkit-scrollbar-thumb:hover{{background:#00c26f;}}
    .w{{font-family:'DM Sans',sans-serif;background:#0f1115;color:#f8fafc;padding-bottom:2rem;min-height:100vh;}}
    .hdr{{padding:1.2rem 1.5rem;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #222830;}}
    .logo{{font-family:'Space Mono',monospace;font-size:12px;color:#00c26f;letter-spacing:.1em;}}
    .logo span{{color:#475569;}}
    .dt{{font-size:11px;color:#475569;font-family:'Space Mono',monospace;}}
    .hero{{padding:1.2rem 1.5rem;display:grid;grid-template-columns:1.2fr 0.8fr;gap:10px;}}
    @media (max-width: 768px) {{
      .hero{{grid-template-columns:1fr;}}
    }}
    .hero-main{{background:#171b20;border:1px solid #222830;border-radius:12px;padding:1.2rem;position:relative;overflow:hidden;}}
    .hero-main::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#00c26f,#00e67a,#00c26f);background-size:200%;animation:sh 3s linear infinite;}}
    @keyframes sh{{0%{{background-position:200% 0}}100%{{background-position:-200% 0}}}}
    .sbadge{{display:inline-flex;align-items:center;gap:5px;background:#052e16;border:1px solid #166534;color:#00c26f;font-size:10px;font-family:'Space Mono',monospace;padding:3px 8px;border-radius:4px;margin-bottom:8px;}}
    .sdot{{width:5px;height:5px;border-radius:50%;background:#00c26f;animation:pu 2s infinite;}}
    @keyframes pu{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
    .hero-main h2{{font-size:12px;color:#cbd5e1;margin-bottom:5px;font-weight:500;text-transform:uppercase;letter-spacing:.08em;}}
    .ait{{font-size:14px;color:#e2e8f0;line-height:1.7;}}
    .ait strong{{color:#f8fafc;}}
    .hstats{{display:flex;flex-direction:column;gap:8px;}}
    .sc{{background:#171b20;border:1px solid #222830;border-radius:10px;padding:.9rem 1.1rem;flex:1;}}
    .sl{{font-size:10px;color:#8c9ba5;font-family:'Space Mono',monospace;text-transform:uppercase;letter-spacing:.06em;margin-bottom:3px;}}
    .sv{{font-size:20px;font-weight:600;color:#f1f5f9;font-family:'Space Mono',monospace;}}
    .sv.g{{color:#00c26f;}}.sv.a{{color:#ff9f1a;}}
    .ss{{font-size:10px;color:#8c9ba5;margin-top:2px;}}
    .sec{{padding:0 1.5rem;margin-top:1.1rem;}}
    .st{{font-size:10px;font-family:'Space Mono',monospace;color:#475569;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;display:flex;align-items:center;gap:8px;}}
    .st::after{{content:'';flex:1;height:1px;background:#222830;}}
    .pgrid{{display:grid;grid-template-columns:repeat(5,1fr);gap:7px;}}
    @media (max-width: 480px) {{
      .pgrid{{grid-template-columns:repeat(2,1fr);}}
    }}
    .pc{{background:#171b20;border:1px solid #222830;border-radius:8px;padding:.7rem .5rem;text-align:center;cursor:pointer;transition:all .2s;position:relative;overflow:hidden;}}
    .pc:hover{{border-color:#00c26f;background:#131d18;transform:translateY(-1px);}}
    .ptk{{font-family:'Space Mono',monospace;font-size:11px;font-weight:700;color:#00c26f;}}
    .psc{{font-size:16px;font-weight:600;color:#f1f5f9;margin:3px 0 2px;font-family:'Space Mono',monospace;}}
    .pal{{font-size:10px;color:#8c9ba5;}}
    .tw{{background:#171b20;border:1px solid #222830;border-radius:12px;overflow-x:auto;}}
    .rt{{width:100%;border-collapse:collapse;min-width:750px;}}
    .rt th{{font-size:11px;font-family:'Space Mono',monospace;color:#cbd5e1;text-transform:uppercase;letter-spacing:.05em;padding:.6rem .8rem;border-bottom:1px solid #2d3748;text-align:left;white-space:nowrap;font-weight:600;}}
    .rt tr:hover td{{background:#1e242b;cursor:pointer;}}
    .rt td{{padding:.6rem .8rem;font-size:13px;border-bottom:1px solid #1a1f26;vertical-align:middle;}}
    .rn{{font-family:'Space Mono',monospace;color:#94a3b8;font-size:11px;}}
    .tk{{font-family:'Space Mono',monospace;font-weight:700;font-size:13px;color:#e2e8f0;}}
    .tk.act{{color:#00c26f;}}
    .tk .star{{color:#ff9f1a;font-size:9px;margin-left:3px;}}

    /* Logo Styles */
    .ticker-cell {{
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .company-logo {{
        width: 32px;
        height: 32px;
        border-radius: 8px;
        object-fit: contain;
        background: #171b20;
        border: 1px solid #222830;
        flex-shrink: 0;
    }}
    .portfolio-logo {{
        width: 40px;
        height: 40px;
        border-radius: 10px;
        object-fit: contain;
        background: #171b20;
        border: 1px solid #222830;
        margin-bottom: 4px;
    }}
    .modal-logo {{
        width: 48px;
        height: 48px;
        border-radius: 12px;
        object-fit: contain;
        background: #171b20;
        border: 1px solid #222830;
        margin-right: 12px;
    }}
    .sf{{font-family:'Space Mono',monospace;font-weight:700;font-size:14px;text-align:right;}}
    .sf.top{{color:#00c26f;}}.sf.mid{{color:#ff9f1a;}}.sf.low{{color:#f87171;}}
    .fb{{display:flex;align-items:center;gap:4px;}}
    .fb-bar{{height:3px;border-radius:2px;background:#222830;width:60px;overflow:hidden;}}
    .fb-fill{{height:100%;border-radius:2px;}}
    .fv{{font-size:11px;color:#cbd5e1;font-family:'Space Mono',monospace;min-width:28px;text-align:right;}}
    .badge{{font-size:10px;padding:3px 8px;border-radius:4px;font-family:'Space Mono',monospace;white-space:nowrap;display:inline-block;}}
    .bh{{background:#142d1e;color:#00c26f;border:1px solid #005a30;}}
    .bw{{background:#171b20;color:#8c9ba5;border:1px solid #222830;}}
    .br{{background:#2a1818;color:#ff4d4d;border:1px solid #661111;}}
    .bd{{background:#121417;color:#8c9ba5;border:1px solid #1c2128;}}
    .bj{{background:#2a1111;color:#ff4d4d;border:1px solid #661111;}}
    .tabs{{display:flex;gap:4px;margin-bottom:8px;flex-wrap:wrap;}}
    .tab{{font-size:10px;font-family:'Space Mono',monospace;padding:4px 10px;border-radius:4px;border:1px solid #222830;color:#8c9ba5;cursor:pointer;background:transparent;transition:all .15s;}}
    .tab.act{{background:#171b20;color:#00c26f;border-color:#00c26f;}}

    /* MODAL */
    .overlay{{position:fixed;inset:0;background:rgba(0,0,0,.7);backdrop-filter:blur(4px);z-index:100;display:none;align-items:center;justify-content:center;padding:1rem;}}
    .overlay.open{{display:flex;}}
    .modal{{background:#111417;border:1px solid #222830;border-radius:16px;width:100%;max-width:520px;max-height:85vh;overflow-y:auto;position:relative;}}
    .modal-hdr{{padding:1.2rem 1.5rem;border-bottom:1px solid #222830;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;background:#111417;z-index:1;}}
    .modal-tk{{font-family:'Space Mono',monospace;font-size:18px;font-weight:700;color:#00c26f;}}
    .modal-name{{font-size:12px;color:#8c9ba5;margin-top:2px;}}
    .close-btn{{background:#171b20;border:none;color:#8c9ba5;width:28px;height:28px;border-radius:6px;cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center;transition:background .15s;}}
    .close-btn:hover{{background:#222830;}}
    .modal-body{{padding:1.2rem 1.5rem;}}
    .modal-section{{margin-bottom:1.2rem;}}
    .modal-section-title{{font-size:10px;font-family:'Space Mono',monospace;color:#475569;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid #222830;}}
    .factor-grid{{display:grid;grid-template-columns:1fr 1fr;gap:8px;}}
    .fcard{{background:#171b20;border:1px solid #222830;border-radius:8px;padding:.8rem;}}
    .fcard-label{{font-size:10px;color:#8c9ba5;font-family:'Space Mono',monospace;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}}
    .fcard-val{{font-size:20px;font-weight:600;font-family:'Space Mono',monospace;color:#e0e6ed;}}
    .fcard-bar{{height:3px;border-radius:2px;background:#222830;margin-top:6px;overflow:hidden;}}
    .fcard-fill{{height:100%;border-radius:2px;transition:width .5s;}}
    .ratio-grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;}}
    .rcard{{background:#171b20;border:1px solid #222830;border-radius:8px;padding:.8rem;text-align:center;}}
    .rcard-label{{font-size:9px;color:#475569;font-family:'Space Mono',monospace;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}}
    .rcard-val{{font-size:15px;font-weight:600;font-family:'Space Mono',monospace;}}
    .rcard-val.pos{{color:#00c26f;}}.rcard-val.neg{{color:#ff4d4d;}}.rcard-val.neu{{color:#8c9ba5;}}
    .rcard-sub{{font-size:9px;color:#8c9ba5;margin-top:2px;line-height:1.2;}}
    .tech-row{{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid #171b20;}}
    .tech-label{{font-size:12px;color:#8c9ba5;}}
    .tech-val{{font-size:12px;font-family:'Space Mono',monospace;font-weight:600;}}
    .tech-val.pos{{color:#00c26f;}}.tech-val.neg{{color:#ff4d4d;}}.tech-val.neu{{color:#8c9ba5;}}
    .signal{{font-size:10px;padding:2px 7px;border-radius:3px;font-family:'Space Mono',monospace;}}
    .sig-bull{{background:#052e16;color:#00c26f;}}.sig-bear{{background:#2a1111;color:#ff4d4d;}}.sig-neu{{background:#171b20;color:#8c9ba5;}}
    .modal-score-hdr{{display:flex;align-items:baseline;gap:8px;margin-bottom:12px;}}
    .big-score{{font-size:36px;font-weight:700;font-family:'Space Mono',monospace;}}
    .big-score.top{{color:#00c26f;}}.big-score.mid{{color:#ff9f1a;}}.big-score.low{{color:#ff4d4d;}}
    .score-rank{{font-size:12px;color:#8c9ba5;}}
    .status-pill{{font-size:11px;padding:4px 10px;border-radius:6px;font-family:'Space Mono',monospace;}}

    /* Sorting & Filter Styles */
    .th-sort {{
      cursor: pointer;
      user-select: none;
      transition: all 0.15s;
    }}
    .th-sort:hover {{
      color: #00c26f;
      background: rgba(0, 194, 111, 0.1);
    }}
    .sort-icon {{
      display: inline-block;
      margin-left: 4px;
      opacity: 0.5;
      font-size: 10px;
    }}
    .sort-icon.active {{
      opacity: 1;
      color: #00c26f;
    }}
    .filter-controls {{
      display: flex;
      gap: 8px;
      margin-bottom: 10px;
      flex-wrap: wrap;
      align-items: center;
    }}
    .filter-select {{
      background: #171b20;
      border: 1px solid #222830;
      color: #8c9ba5;
      padding: 6px 10px;
      border-radius: 4px;
      font-family: 'Space Mono', monospace;
      font-size: 10px;
      cursor: pointer;
    }}
    .filter-select:focus {{
      outline: none;
      border-color: #00c26f;
    }}
    .filter-label {{
      color: #cbd5e1;
      font-size: 11px;
      font-family: 'Space Mono', monospace;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      font-weight: 500;
    }}
  </style>
</head>
<body>
<div class="w">
  <div class="hdr">
    <div class="logo">ISI <span>·</span> V8.4 <span>·</span> QUANT DASHBOARD</div>
    <div class="dt">{datetime.datetime.now().strftime('%Y-%m-%d')} · IDX30</div>
  </div>

  <div class="hero">
    <div class="hero-main">
      <div class="{radar_badge_class}">{radar_badge_dot}{radar_badge_text}</div>
      <h2>Analisis AI Hari Ini</h2>
      <p class="ait">{radar_narrative}</p>
    </div>
    <div class="hstats">
      <div class="sc">
        <div class="sl">Portfolio Aktif</div>
        <div class="sv">{len(current_portfolio)}</div>
        <div class="ss">Score Weighted · Target {latest_month}</div>
      </div>
      <div class="sc">
        <div class="sl">Sedang Anget</div>
        <div class="sv a">{sum(1 for s in stocks_js_list if s['s'] == 'hot')}</div>
        <div class="ss">saham dari 30 universe</div>
      </div>
    </div>
  </div>

  <div class="sec">
    <div class="st">Live Forward Portfolio</div>
    <div class="pgrid" id="portGrid"></div>
  </div>

  <div class="sec">
    <div class="st">Universe Ranking Board</div>
    <div class="tabs">
      <button class="tab act" onclick="filter('all',this)">Semua</button>
      <button class="tab" onclick="filter('hot',this)">🚀 Sedang Anget</button>
      <button class="tab" onclick="filter('port',this)">⭐ Portfolio</button>
    </div>
    <div class="filter-controls">
      <span class="filter-label">Sektor:</span>
      <select class="filter-select" id="sectorFilter" onchange="applyFiltersAndSort()">
        <option value="all">Semua</option>
        {sector_options}
      </select>
      <span class="filter-label">Min Score:</span>
      <select class="filter-select" id="minScoreFilter" onchange="applyFiltersAndSort()">
        <option value="0">0</option>
        <option value="30">30</option>
        <option value="50">50</option>
        <option value="70">70</option>
      </select>
    </div>
    <div class="tw">
      <table class="rt">
        <thead>
          <tr>
            <th class="th-sort" onclick="sortBy('r', this)"># <span class="sort-icon" id="sort-r">↕</span></th>
            <th class="th-sort" onclick="sortBy('t', this)">Ticker <span class="sort-icon" id="sort-t">↕</span></th>
            <th class="th-sort" onclick="sortBy('q', this)">Quality (30%) <span class="sort-icon" id="sort-q">↕</span></th>
            <th class="th-sort" onclick="sortBy('g', this)">Growth (10%) <span class="sort-icon" id="sort-g">↕</span></th>
            <th class="th-sort" onclick="sortBy('v', this)">Value (30%) <span class="sort-icon" id="sort-v">↕</span></th>
            <th class="th-sort" onclick="sortBy('m', this)">Momentum (35%) <span class="sort-icon" id="sort-m">↕</span></th>
            <th class="th-sort" style="text-align:right" onclick="sortBy('f', this)">Score <span class="sort-icon active" id="sort-f">↓</span></th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody id="tb"></tbody>
      </table>
    </div>
  </div>
</div>

<!-- MODAL -->
<div class="overlay" id="overlay" onclick="closeModal(event)">
  <div class="modal" id="modal">
    <div class="modal-hdr">
      <div>
        <div class="modal-tk" id="m-ticker"></div>
        <div class="modal-name" id="m-name"></div>
      </div>
      <button class="close-btn" onclick="closeModal(null)">✕</button>
    </div>
    <div class="modal-body" id="modal-body"></div>
  </div>
</div>

<script>
let stocks = [];
let currentFilter = 'all';
let currentSort = {{field: 'f', dir: 'desc'}};

// Load stock data
async function loadStocks() {{
  try {{
    const res = await fetch('./data.json');
    stocks = await res.json();
    applyFiltersAndSort();
    // Build portfolio grid
    document.getElementById('portGrid').innerHTML = stocks.filter(d => d.port).map(d => `
      <div class="pc" onclick="openModal('${{d.t}}')">
        <div class="portfolio-logo" style="display:flex;align-items:center;justify-content:center;font-family:'Space Mono',monospace;font-weight:700;color:#fff;background:hsl(${{getHueFromName(d.name)}},70%,40%);">
          ${{getInitials(d.name)}}
        </div>
        <div class="ptk">${{d.t}}</div>
        <div class="psc">${{d.f.toFixed(1)}}</div>
        <div class="pal">${{d.weight || '20%'}}</div>
      </div>`).join('');
  }} catch (error) {{
    console.error('Failed to load data:', error);
    document.getElementById('tb').innerHTML = '<tr><td colspan="8" style="text-align:center">Failed to load market data.</td></tr>';
  }}
}}

const bmap = {{
  hot: ['bh', '🚀 Anget'],
  watch: ['bw', '— Pantau'],
  risk: ['br', '⚠ Rawan'],
  dead: ['bd', '⚓ Mati'],
  junk: ['bj', '🗑 Goreng']
}};

const bc = {{
  q: '#00c26f',
  g: '#38bdf8',
  v: '#a855f7',
  m: '#ff9f1a'
}};

function bar(v, k) {{
  return `<div class="fb">
    <div class="fb-bar"><div class="fb-fill" style="width:${{v}}%;background:${{bc[k]}}"></div></div>
    <span class="fv">${{v.toFixed(0)}}</span>
  </div>`;
}}

function sc(f) {{
  return f >= 60 ? 'top' : f >= 45 ? 'mid' : 'low';
}}

function getInitials(name) {{
  return name.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
}}
function getHueFromName(name) {{
  let hash = 0;
  for (let i = 0; i < name.length; i++) {{
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }}
  return hash % 360;
}}

function renderRows(rows) {{
  document.getElementById('tb').innerHTML = rows.map((d, idx) => `
    <tr onclick="openModal('${{d.t}}')">
      <td class="rn">${{idx+1}}</td>
      <td class="ticker-cell">
        <div class="company-logo" style="display:flex;align-items:center;justify-content:center;font-family:'Space Mono',monospace;font-weight:700;color:#fff;background:hsl(${{getHueFromName(d.name)}},70%,40%);">
          ${{getInitials(d.name)}}
        </div>
        <span class="tk ${{d.s === 'hot' || d.port ? 'act' : ''}}">${{d.t}}.JK${{d.port ? '<span class="star">★</span>' : ''}}</span>
      </td>
      <td>${{bar(d.q, 'q')}}</td>
      <td>${{bar(d.g, 'g')}}</td>
      <td>${{bar(d.v, 'v')}}</td>
      <td>${{bar(d.m, 'm')}}</td>
      <td class="sf ${{sc(d.f)}}">${{d.f.toFixed(1)}}</td>
      <td><span class="badge ${{bmap[d.s][0]}}">${{bmap[d.s][1]}}</span></td>
    </tr>`).join('');
}}

function updateSortIcons() {{
  // Reset all icons
  document.querySelectorAll('.sort-icon').forEach(el => {{
    el.textContent = '↕';
    el.classList.remove('active');
  }});
  // Set active icon
  const activeIcon = document.getElementById(`sort-${{currentSort.field}}`);
  if (activeIcon) {{
    activeIcon.textContent = currentSort.dir === 'asc' ? '↑' : '↓';
    activeIcon.classList.add('active');
  }}
}}

function applyFiltersAndSort() {{
  let filtered = [...stocks];
  
  // Apply filter (all/hot/port)
  if (currentFilter === 'hot') {{
    filtered = filtered.filter(d => d.s === 'hot');
  }} else if (currentFilter === 'port') {{
    filtered = filtered.filter(d => d.port);
  }}
  
  // Apply sector filter
  const sectorSelect = document.getElementById('sectorFilter');
  if (sectorSelect && sectorSelect.value !== 'all') {{
    filtered = filtered.filter(d => d.sector === sectorSelect.value);
  }}
  
  // Apply min score filter
  const minScoreSelect = document.getElementById('minScoreFilter');
  if (minScoreSelect) {{
    const minScore = parseFloat(minScoreSelect.value);
    filtered = filtered.filter(d => d.f >= minScore);
  }}
  
  // Apply sort
  filtered.sort((a, b) => {{
    let aVal = a[currentSort.field];
    let bVal = b[currentSort.field];
    
    if (typeof aVal === 'string') {{
      aVal = aVal.toLowerCase();
      bVal = bVal.toLowerCase();
    }}
    
    if (currentSort.dir === 'asc') {{
      return aVal > bVal ? 1 : -1;
    }} else {{
      return aVal < bVal ? 1 : -1;
    }}
  }});
  
  updateSortIcons();
  renderRows(filtered);
}}

function filter(type, btn) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('act'));
  btn.classList.add('act');
  currentFilter = type;
  applyFiltersAndSort();
}}

function sortBy(field, btn) {{
  if (currentSort.field === field) {{
    currentSort.dir = currentSort.dir === 'asc' ? 'desc' : 'asc';
  }} else {{
    currentSort.field = field;
    currentSort.dir = 'desc';
  }}
  applyFiltersAndSort();
}}

function openModal(ticker) {{
  const d = stocks.find(s => s.t === ticker);
  if (!d) return;
  document.getElementById('m-ticker').textContent = d.t + '.JK';
  document.getElementById('m-name').textContent = d.name + ' · ' + d.sector;

  const isBk = d.is_bank;
  const rs6c = d.rs6m > 0 ? 'pos' : d.rs6m < 0 ? 'neg' : 'neu';
  const rs6label = d.rs6m > 0 ? 'Outperform IHSG' : d.rs6m < 0 ? 'Underperform IHSG' : 'Netral';
  const volC = d.vol_ratio > 1.5 ? 'neg' : d.vol_ratio >= 0.8 ? 'neu' : 'neg';
  const volLabel = d.vol_ratio > 1.5 ? 'Anomali Lonjakan' : d.vol_ratio >= 0.8 ? 'Wajar' : 'Sepi';
  const fcfC = d.fcf > 60 ? 'pos' : d.fcf > 30 ? 'neu' : 'neg';

  // Format Helper
  const fmtPct = (val) => val !== null ? val.toFixed(1) + '%' : 'N/A';
  const fmtPE = (val) => val !== null ? val.toFixed(1) + 'x' : 'N/A';
  const fmtPB = (val) => val !== null ? val.toFixed(1) + 'x' : 'N/A';
  const valClass = (val, thPos, thNeg) => {{
    if (val === null) return 'neu';
    return val > thPos ? 'pos' : val < thNeg ? 'neg' : 'neu';
  }};

  document.getElementById('modal-body').innerHTML = `
    <div class="modal-section">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
        <div class="modal-logo" style="display:flex;align-items:center;justify-content:center;font-family:'Space Mono',monospace;font-weight:700;color:#fff;background:hsl(${{getHueFromName(d.name)}},70%,40%);">
          ${{getInitials(d.name)}}
        </div>
        <div>
          <span class="big-score ${{sc(d.f)}}">${{d.f.toFixed(1)}}</span>
          <div class="score-rank">Rank #${{d.r}} dari ${{stocks.length}}</div>
        </div>
        <span class="badge ${{bmap[d.s][0]}}" style="margin-left:auto">${{bmap[d.s][1]}}</span>
      </div>
      <div class="factor-grid">
        <div class="fcard">
          <div class="fcard-label" style="color:#3b82f6">Quality (30%)</div>
          <div class="fcard-val">${{d.q.toFixed(1)}}</div>
          <div class="fcard-bar"><div class="fcard-fill" style="width:${{d.q}}%;background:#3b82f6"></div></div>
        </div>
        <div class="fcard">
          <div class="fcard-label" style="color:#10b981">Growth (10%)</div>
          <div class="fcard-val">${{d.g.toFixed(1)}}</div>
          <div class="fcard-bar"><div class="fcard-fill" style="width:${{d.g}}%;background:#10b981"></div></div>
        </div>
        <div class="fcard">
          <div class="fcard-label" style="color:#a855f7">Value (30%)</div>
          <div class="fcard-val">${{d.v.toFixed(1)}}</div>
          <div class="fcard-bar"><div class="fcard-fill" style="width:${{d.v}}%;background:#a855f7"></div></div>
        </div>
        <div class="fcard">
          <div class="fcard-label" style="color:#f59e0b">Momentum (35%)</div>
          <div class="fcard-val">${{d.m.toFixed(1)}}</div>
          <div class="fcard-bar"><div class="fcard-fill" style="width:${{d.m}}%;background:#f59e0b"></div></div>
        </div>
      </div>
    </div>

    <div class="modal-section">
      <div class="modal-section-title">Fundamental Rasio</div>
      <div class="ratio-grid">
        <div class="rcard">
          <div class="rcard-label">ROE</div>
          <div class="rcard-val ${{valClass(d.roe, 15, 8)}}">${{fmtPct(d.roe)}}</div>
          <div class="rcard-sub">Return on Equity</div>
        </div>
        <div class="rcard">
          <div class="rcard-label">Net Margin</div>
          <div class="rcard-val ${{valClass(d.npm, 15, 5)}}">${{fmtPct(d.npm)}}</div>
          <div class="rcard-sub">Net Profit Margin</div>
        </div>
        <div class="rcard">
          <div class="rcard-label">Op Margin</div>
          <div class="rcard-val ${{valClass(d.opm, 20, 8)}}">${{fmtPct(d.opm)}}</div>
          <div class="rcard-sub">Operating Margin</div>
        </div>
        <div class="rcard">
          <div class="rcard-label">DER</div>
          ${{isBk ? `
          <div class="rcard-val neu">N/A</div>
          <div class="rcard-sub">Bank Rule aktif</div>
          ` : `
          <div class="rcard-val ${{d.der !== null && d.der < 50 ? 'pos' : d.der !== null && d.der < 100 ? 'neu' : 'neg'}}">${{fmtPct(d.der)}}</div>
          <div class="rcard-sub">Debt/Equity</div>
          `}}
        </div>
        <div class="rcard">
          <div class="rcard-label">P/E</div>
          <div class="rcard-val ${{d.pe !== null && d.pe > 0 && d.pe < 12 ? 'pos' : d.pe !== null && d.pe > 25 ? 'neg' : 'neu'}}">${{fmtPE(d.pe)}}</div>
          <div class="rcard-sub">Price/Earnings</div>
        </div>
        <div class="rcard">
          <div class="rcard-label">P/B</div>
          <div class="rcard-val ${{valClass(d.pb, 3.0, 1.5)}}">${{fmtPB(d.pb)}}</div>
          <div class="rcard-sub">Price/Book</div>
        </div>
      </div>
    </div>

    <div class="modal-section">
      <div class="modal-section-title">Growth YoY</div>
      <div class="ratio-grid">
        <div class="rcard">
          <div class="rcard-label">Revenue</div>
          <div class="rcard-val ${{valClass(d.rev_g, 10, 0)}}">${{d.rev_g !== null ? (d.rev_g > 0 ? '+' : '') + d.rev_g.toFixed(1) + '%' : 'N/A'}}</div>
          <div class="rcard-sub">Growth YoY</div>
        </div>
        <div class="rcard">
          <div class="rcard-label">Net Income</div>
          <div class="rcard-val ${{valClass(d.ni_g, 10, 0)}}">${{d.ni_g !== null ? (d.ni_g > 0 ? '+' : '') + d.ni_g.toFixed(1) + '%' : 'N/A'}}</div>
          <div class="rcard-sub">Growth YoY</div>
        </div>
        <div class="rcard">
          <div class="rcard-label">FCF Score</div>
          <div class="rcard-val ${{fcfC}}">${{d.fcf}}</div>
          <div class="rcard-sub">Percentile</div>
        </div>
      </div>
    </div>

    <div class="modal-section">
      <div class="modal-section-title">Sinyal Teknikal</div>
      <div class="tech-row">
        <span class="tech-label">RS-6M vs IHSG</span>
        <div style="display:flex;align-items:center;gap:6px;">
          <span class="tech-val ${{rs6c}}">${{d.rs6m !== null ? (d.rs6m > 0 ? '+' : '') + d.rs6m.toFixed(1) + '%' : 'N/A'}}</span>
          <span class="signal ${{d.rs6m > 0 ? 'sig-bull' : d.rs6m < 0 ? 'sig-bear' : 'sig-neu'}}">${{rs6label}}</span>
        </div>
      </div>
      <div class="tech-row">
        <span class="tech-label">Volume Ratio (vs MA20)</span>
        <div style="display:flex;align-items:center;gap:6px;">
          <span class="tech-val ${{volC}}">${{d.vol_ratio !== null ? d.vol_ratio.toFixed(2) + 'x' : 'N/A'}}</span>
          <span class="signal ${{d.vol_ratio >= 1.5 ? 'sig-bear' : d.vol_ratio >= 0.8 ? 'sig-neu' : 'sig-bear'}}">${{volLabel}}</span>
        </div>
      </div>
      ${{isBk ? `
      <div class="tech-row" style="border:none">
        <span class="tech-label">Bank Rule</span>
        <span class="signal sig-neu" style="font-size:9px">DER dinonaktifkan · ROE bobot 45%</span>
      </div>` : ''}}
      ${{d.is_commodity ? `
      <div class="tech-row" style="border:none">
        <span class="tech-label">Commodity Trap Rule</span>
        <span class="signal sig-bear" style="font-size:9px">PE discount 50% aktif</span>
      </div>` : ''}}
    </div>`;

  document.getElementById('overlay').classList.add('open');
}}

function closeModal(e) {{
  if (!e || e.target === document.getElementById('overlay'))
    document.getElementById('overlay').classList.remove('open');
}}

// Initial load
loadStocks();
</script>
</body>
</html>
"""

    # 4. Save HTML
    output_path = Path("dashboard/index.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Success! Modern dashboard HTML built at: {output_path}")

    # 5. Save processed stocks data
    data_json_path = Path("dashboard/data.json")
    with open(data_json_path, "w", encoding="utf-8") as f:
        f.write(stocks_json_str)
    print(f"Success! Stocks data saved at: {data_json_path}")

if __name__ == "__main__":
    generate_dashboard()
