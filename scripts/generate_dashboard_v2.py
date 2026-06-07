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
PORTFOLIO_FILE = Path("data/state/portfolio_simulator.json")

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

def calculate_portfolio(portfolio_raw, leaders, exit_data, profiles):
    leader_map = {}
    for l in leaders:
        t = l['ticker'].replace('.JK', '')
        leader_map[t] = l
    exit_map = {}
    for e in exit_data:
        t = e['ticker'].replace('.JK', '')
        exit_map[t] = e
    result = []
    for h in portfolio_raw:
        ticker = h['ticker']
        investment = float(h.get('investment', 0))
        entry_price = float(h.get('entry_price', 0))
        estimated_shares = investment / entry_price if entry_price > 0 else 0
        ed = exit_map.get(ticker, {})
        current_price = entry_price
        if ed and 'close' in ed and ed['close']:
            try:
                current_price = float(ed['close'])
            except (ValueError, TypeError):
                pass
        current_value = estimated_shares * current_price
        profit_loss = current_value - investment
        profit_loss_pct = (profit_loss / investment * 100) if investment > 0 else 0.0
        ld = leader_map.get(ticker, {})
        rank = int(ld.get('rank', 99)) if ld else 99
        exit_status = ed.get('exit_state', 'HEALTHY') if ed else 'HEALTHY'
        sector = (profiles.get(ticker, {})).get('sector', '') if profiles else ''
        result.append({
            'ticker': ticker,
            'investment': investment,
            'entry_price': entry_price,
            'estimated_shares': round(estimated_shares, 2),
            'current_price': current_price,
            'current_value': round(current_value, 2),
            'profit_loss': round(profit_loss, 2),
            'profit_loss_pct': round(profit_loss_pct, 2),
            'rank': rank if rank <= 30 else 99,
            'exit_status': exit_status,
            'sector': sector
        })
    total_value = sum(r['current_value'] for r in result)
    for r in result:
        r['weight'] = round((r['current_value'] / total_value * 100), 2) if total_value > 0 else 0
    result.sort(key=lambda x: x['ticker'])
    return result

def file_age(path):
    if not path.exists():
        return 'N/A'
    mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime)
    age = datetime.datetime.now() - mtime
    return f"{age.days}d {age.seconds // 3600}h ago" if age.days < 30 else f"{age.days}d ago"

def build_html(leaders, turnaround, summary, history, streaks, date_str, exit_data=None, profiles=None, fundamentals=None, portfolio_data=None):
    date_short = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
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
    portfolio_json = json.dumps(portfolio_data if portfolio_data else [])
    hlp_dict = {
        'leaders': '<div class="help-section"><div class="help-section-title">Apa Artinya?</div><ul><li>Peringkat 30 saham IDX30 berdasarkan 4 faktor nilai: Kualitas, Pertumbuhan, Nilai, dan Momentum</li><li>Setiap faktor dihitung secara persentil (0-100) lalu digabung dengan bobot tetap</li></ul></div><div class="help-section"><div class="help-section-title">Mengapa Penting?</div><ul><li>Membantu memilih 5 saham terbaik setiap bulan untuk portofolio</li><li>Sistem ini sudah melalui riset dan pengujian sejak 2019</li></ul></div><div class="help-section"><div class="help-section-title">Cara Membaca?</div><ul><li>Semakin tinggi skor, semakin baik peringkatnya</li><li>Top 5 (label PORTFOLIO) adalah posisi yang saat ini ditempati</li><li>Skor setiap faktor menunjukkan kekuatan di area tersebut</li></ul></div>',
        'turnaround': '<div class="help-section"><div class="help-section-title">Apa Artinya?</div><ul><li>Mendeteksi saham yang mungkin berbalik arah dari tekanan menuju pemulihan</li><li>Saham diperiksa dari dua sisi: apakah masih tertekan dan apakah sudah mulai pulih</li></ul></div><div class="help-section"><div class="help-section-title">Mengapa Penting?</div><ul><li>Menangkap peluang pemulihan lebih awal sebelum harga naik signifikan</li><li>Membantu mengidentifikasi saham yang mungkin akan masuk peringkat teratas</li></ul></div><div class="help-section"><div class="help-section-title">Cara Membaca?</div><ul><li>Status Ctx (tekanan) = YES berarti saham masih dalam tekanan besar</li><li>Status Trn (pemulihan) = YES berarti mulai menunjukkan perbaikan</li><li>Keduanya YES = kandidat terkuat untuk dipantau</li><li>Gunakan filter untuk memfilter berdasarkan status</li></ul></div>',
        'diagnostics': '<div class="help-section"><div class="help-section-title">Apa Artinya?</div><ul><li>Menampilkan status kesehatan sistem dan kesegaran data</li><li>Memastikan pipeline berjalan sesuai jadwal</li></ul></div><div class="help-section"><div class="help-section-title">Mengapa Penting?</div><ul><li>Data yang basi dapat menghasilkan sinyal yang menyesatkan</li><li>Memantau apakah pipeline harian dan bulanan berjalan normal</li></ul></div><div class="help-section"><div class="help-section-title">Cara Membaca?</div><ul><li>Operational = pipeline berjalan normal</li><li>File ages menunjukkan waktu sejak data terakhir diperbarui</li><li>Jika lebih dari 24 jam (harian) atau 35 hari (bulanan), ada masalah</li></ul></div>',
        'exit': '<div class="help-section"><div class="help-section-title">Apa Artinya?</div><ul><li>Sistem aturan untuk mendeteksi saham yang perlu diwaspadai atau dikeluarkan dari portofolio</li><li>Menggunakan 4 tingkat peringatan: A (awal) hingga D (keluar)</li></ul></div><div class="help-section"><div class="help-section-title">Mengapa Penting?</div><ul><li>Melindungi portofolio dari penurunan lebih dalam</li><li>Memberikan sinyal objektif kapan harus waspada, bukan keputusan emosional</li></ul></div><div class="help-section"><div class="help-section-title">Cara Membaca?</div><ul><li>HEALTHY = tidak ada masalah</li><li>EXIT WATCH (A) = peringkat turun di luar 10 besar, waspada</li><li>WEAKENING (B) = momentum melemah, perlu perhatian</li><li>EXIT RISK (C) = trend rusak, risiko meningkat</li><li>EXIT (D) = pelemahan terkonfirmasi, sinyal keluar</li></ul></div>',
        'saham_tertekan': '<div class="help-section"><div class="help-section-title">Apa Artinya?</div><ul><li>Saham masih berada dalam tekanan besar</li><li>Jauh dari harga tertinggi sebelumnya</li><li>Belum menunjukkan pemulihan yang kuat</li></ul></div><div class="help-section"><div class="help-section-title">Mengapa Penting?</div><ul><li>Menjadi sumber kandidat turnaround</li><li>Menunjukkan area pasar yang masih lemah</li></ul></div><div class="help-section"><div class="help-section-title">Cara Membaca?</div><ul><li>Angka lebih tinggi = lebih banyak saham tertekan</li><li>Angka lebih rendah = tekanan pasar berkurang</li></ul></div>',
        'mulai_membaik': '<div class="help-section"><div class="help-section-title">Apa Artinya?</div><ul><li>Saham yang kekuatan relatifnya mulai meningkat</li><li>Dibanding dua bulan sebelumnya, performa saham ini membaik</li></ul></div><div class="help-section"><div class="help-section-title">Mengapa Penting?</div><ul><li>Bisa menjadi sinyal awal pemulihan pasar</li><li>Menunjukkan minat investor mulai kembali</li></ul></div><div class="help-section"><div class="help-section-title">Cara Membaca?</div><ul><li>Angka lebih tinggi = semakin banyak saham pulih</li><li>Jika angka terus meningkat, pasar memasuki fase pemulihan</li></ul></div>',
        'kandidat_turnaround': '<div class="help-section"><div class="help-section-title">Apa Artinya?</div><ul><li>Saham yang memenuhi dua syarat: masih tertekan dan mulai menunjukkan pemulihan</li><li>Ini adalah kandidat yang berpotensi berbalik arah</li></ul></div><div class="help-section"><div class="help-section-title">Mengapa Penting?</div><ul><li>Menangkap peluang pemulihan lebih awal</li><li>Bisa menjadi tambahan portofolio jika pemulihan berlanjut</li></ul></div><div class="help-section"><div class="help-section-title">Cara Membaca?</div><ul><li>Bukan sinyal beli otomatis, tetapi radar untuk dipantau</li><li>Semakin tinggi angka, semakin banyak peluang potensial</li></ul></div>',
        'kekuatan_mulai_naik': '<div class="help-section"><div class="help-section-title">Apa Artinya?</div><ul><li>Jumlah saham yang mulai mengungguli pergerakan pasar</li><li>Menunjukkan perubahan momentum secara luas</li></ul></div><div class="help-section"><div class="help-section-title">Mengapa Penting?</div><ul><li>Mendeteksi pemulihan pasar lebih awal</li><li>Jika jumlahnya meningkat, pasar sedang menguat</li></ul></div><div class="help-section"><div class="help-section-title">Cara Membaca?</div><ul><li>Angka lebih tinggi = pemulihan semakin meluas</li><li>Angka rendah = hanya sedikit saham yang menguat</li></ul></div>',
        'minat_beli_meningkat': '<div class="help-section"><div class="help-section-title">Apa Artinya?</div><ul><li>Volume perdagangan minimal 30% lebih tinggi dari normal</li><li>Menunjukkan aktivitas investor di atas rata-rata</li></ul></div><div class="help-section"><div class="help-section-title">Mengapa Penting?</div><ul><li>Volume tinggi bisa memperkuat sinyal pergerakan harga</li><li>Volume tinggi + harga naik = minat beli nyata</li><li>Volume tinggi + harga turun = bisa distribusi</li></ul></div><div class="help-section"><div class="help-section-title">Cara Membaca?</div><ul><li>Angka lebih tinggi = semakin banyak saham dengan volume tinggi</li><li>Perhatikan arah harga saat volume meningkat</li></ul></div>',
        'di_atas_trend_pendek': '<div class="help-section"><div class="help-section-title">Apa Artinya?</div><ul><li>Harga saham di atas rata-rata 20 hari terakhir</li><li>Menunjukkan tren jangka pendek yang positif</li></ul></div><div class="help-section"><div class="help-section-title">Mengapa Penting?</div><ul><li>Mengonfirmasi momentum naik jangka pendek</li><li>Saham yang konsisten di atas MA20 biasanya sehat</li></ul></div><div class="help-section"><div class="help-section-title">Cara Membaca?</div><ul><li>Angka lebih tinggi = semakin banyak saham di atas MA20</li><li>Jika mendekati 0, pasar sedang lemah</li><li>Ini indikator jangka pendek, kombinasikan dengan indikator lain</li></ul></div>',
        'pantul_dari_dasar': '<div class="help-section"><div class="help-section-title">Apa Artinya?</div><ul><li>Saham yang naik lebih dari 10% dari titik terendah 60 hari</li><li>Menunjukkan usaha pemulihan setelah penurunan</li></ul></div><div class="help-section"><div class="help-section-title">Mengapa Penting?</div><ul><li>Mengonfirmasi bahwa saham mulai bangkit</li><li>Semakin banyak yang memantul, semakin besar potensi pemulihan pasar</li></ul></div><div class="help-section"><div class="help-section-title">Cara Membaca?</div><ul><li>Angka lebih tinggi = semakin banyak saham pulih</li><li>Gunakan bersama indikator volume dan kekuatan relatif</li></ul></div>',
        'rata_penurunan': '<div class="help-section"><div class="help-section-title">Apa Artinya?</div><ul><li>Rata-rata penurunan semua saham IDX30 dari harga tertinggi 1 tahun</li><li>Gambaran kesehatan pasar secara keseluruhan</li></ul></div><div class="help-section"><div class="help-section-title">Mengapa Penting?</div><ul><li>Mengetahui apakah pasar sedang dalam tekanan luas</li><li>Membantu mengatur ekspektasi risiko</li></ul></div><div class="help-section"><div class="help-section-title">Cara Membaca?</div><ul><li>Di atas -15% = pasar relatif sehat</li><li>-15% hingga -30% = waspada</li><li>Di bawah -30% = tekanan luas</li></ul></div>',
        'rata_gejolak': '<div class="help-section"><div class="help-section-title">Apa Artinya?</div><ul><li>Rata-rata intensitas pergerakan harga seluruh IDX30 dalam 60 hari</li><li>Mengukur tingkat ketidakpastian pasar</li></ul></div><div class="help-section"><div class="help-section-title">Mengapa Penting?</div><ul><li>Volatilitas tinggi = pergerakan harga lebih ekstrem</li><li>Membantu menyesuaikan strategi dan ekspektasi risiko</li></ul></div><div class="help-section"><div class="help-section-title">Cara Membaca?</div><ul><li>Di bawah 2% = pasar tenang</li><li>2% hingga 4% = normal</li><li>Di atas 4% = volatilitas tinggi, risiko meningkat</li></ul></div>',
    }
    hlp_json = json.dumps(hlp_dict)

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
.tip{{display:inline-flex;align-items:center;justify-content:center;width:16px;height:16px;border-radius:50%;background:#222830;color:#9CA3AF;font-size:9px;cursor:pointer;margin-left:5px;font-family:sans-serif;font-weight:400;vertical-align:middle;line-height:1;font-style:normal;letter-spacing:0;transition:all .15s}}
.tip:hover{{background:#333a44;color:#F5F7FA}}
.sortable{{cursor:pointer}}
.sortable:hover{{color:#F5F7FA}}
.tk-click{{cursor:pointer;color:inherit;transition:color .15s}}
.tk-click:hover{{color:#93c5fd!important;text-decoration:underline}}
.overlay{{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.5);z-index:99;display:none}}
.overlay.show{{display:block}}
.panel{{position:fixed;top:0;right:-420px;width:400px;height:100vh;background:#161a20;border-left:1px solid #222830;z-index:100;overflow-y:auto;transition:right .25s ease;padding:0;touch-action:pan-y}}
.panel.show{{right:0}}
.panel-dragging{{transition:none!important}}
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
.conc{{padding:.75rem 1.5rem 0}}
.conc-hdr{{display:flex;align-items:center;gap:10px;margin-bottom:8px}}
.conc-status{{font-size:10px;font-family:'Space Mono',monospace;font-weight:700;padding:3px 10px;border-radius:4px;text-transform:uppercase;letter-spacing:.08em}}
.conc-status.s-hijau{{background:#052e16;color:#00c26f;border:1px solid #166534}}
.conc-status.s-kuning{{background:#2a2411;color:#f59e0b;border:1px solid #665511}}
.conc-status.s-merah{{background:#2a1111;color:#ef4444;border:1px solid #661111}}
.conc-status.s-biru{{background:#0c1929;color:#60a5fa;border:1px solid #1e3a5f}}
.conc-label{{font-size:10px;font-family:'Space Mono',monospace;color:#9CA3AF;letter-spacing:.08em;font-weight:600}}
.conc-body{{display:flex;gap:16px;flex-wrap:wrap}}
.conc-col{{flex:1;min-width:200px}}
.conc-sub{{font-size:9px;font-family:'Space Mono',monospace;color:#C9D1D9;text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;font-weight:700}}
.conc-list{{list-style:none;padding:0;margin:0}}
.conc-list li{{font-size:11px;color:#C9D1D9;padding:2px 0 2px 12px;position:relative;line-height:1.5}}
.conc-list li::before{{content:'\2022';position:absolute;left:0;color:#00c26f}}
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
.pi-input{{background:#0f1115;border:1px solid #222830;border-radius:4px;padding:6px 10px;color:#F5F7FA;font-size:12px;font-family:'Space Mono',monospace;outline:none;transition:border-color .15s}}
.pi-input:focus{{border-color:#00c26f}}
.pi-input::placeholder{{color:#64748b}}
.pi-add{{background:#00c26f;border:none;border-radius:4px;padding:6px 14px;color:#0f1115;font-size:12px;font-weight:700;cursor:pointer;font-family:'Space Mono',monospace;transition:background .15s}}
.pi-add:hover{{background:#00e67a}}
.del-btn{{background:transparent;border:none;color:#ef4444;cursor:pointer;font-size:14px;padding:2px 6px;border-radius:3px;opacity:.6;transition:opacity .15s;font-family:sans-serif;line-height:1}}
.del-btn:hover{{opacity:1;background:#2a1111}}
.help-modal{{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);width:380px;max-width:90vw;max-height:80vh;background:#161a20;border:1px solid #222830;border-radius:8px;z-index:101;padding:0;display:none;overflow-y:auto}}
.help-modal.show{{display:block}}
.help-hdr{{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:1px solid #222830;position:sticky;top:0;background:#161a20;z-index:2}}
.help-title{{font-size:12px;font-weight:700;color:#F5F7FA;font-family:'Space Mono',monospace}}
.help-close{{background:transparent;border:none;color:#9CA3AF;font-size:18px;cursor:pointer;padding:2px 8px;border-radius:4px;font-family:'Space Mono',monospace}}
.help-close:hover{{background:#222830;color:#F5F7FA}}
.help-body{{padding:12px 16px}}
.help-section{{margin-bottom:12px}}
.help-section-title{{font-size:10px;font-family:'Space Mono',monospace;color:#00c26f;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;font-weight:600}}
.help-body ul{{list-style:none;padding:0;margin:0}}
.help-body li{{font-size:11px;color:#C9D1D9;padding:3px 0 3px 12px;position:relative;line-height:1.5}}
.help-body li::before{{content:'\2022';position:absolute;left:0;color:#9CA3AF}}
</style>
</head>
<body>
<div class="hdr">
  <div class="logo">ISI <span>·</span> V2 <span>·</span> READ-ONLY DASHBOARD</div>
  <div class="dt">{date_short} · IDX30</div>
</div>
<div id="conclusion"></div>
<div class="tab-nav">
  <button class="tab-btn active" onclick="st(0)">01 · Leaders</button>
  <button class="tab-btn" onclick="st(1)">02 · Turnaround</button>
  <button class="tab-btn" onclick="st(2)">03 · Daily Summary</button>
  <button class="tab-btn" onclick="st(3)">04 · History</button>
  <button class="tab-btn" onclick="st(4)">05 · Diagnostics</button>
  <button class="tab-btn" onclick="st(5)">06 · Portfolio Simulator</button>
  <button class="tab-btn" onclick="st(6)">07 · Exit Monitor</button>
</div>

<div class="tc active" id="t0">
  <div class="section-title">Config B Leaders · Q25/G30/V10/M35<span class="tip" onclick="showHelp('leaders')">?</span></div>
  <table>
    <thead><tr>
      <th data-key="rank">#</th><th data-key="ticker">Ticker</th><th data-key="final_score">Score</th><th data-key="quality">Quality</th><th data-key="growth">Growth</th><th data-key="value">Value</th><th data-key="momentum">Momentum</th><th>Status</th>
    </tr></thead>
    <tbody id="tbody-leaders"></tbody>
  </table>
</div>

<div class="tc" id="t1">
  <div class="section-title">Turnaround Watchlist<span class="tip" onclick="showHelp('turnaround')">?</span></div>
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
    <div class="card"><div class="card-label">SAHAM TERTEKAN<span class="tip" onclick="showHelp('saham_tertekan')">?</span></div><div class="card-val g">{ctx_count}</div><div class="card-sub">Saham yang jatuh berat dan masih dalam kondisi tertekan</div></div>
    <div class="card"><div class="card-label">MULAI MEMBAIK<span class="tip" onclick="showHelp('mulai_membaik')">?</span></div><div class="card-val y">{trn_count}</div><div class="card-sub">Saham dengan kekuatan relatif yang mulai meningkat</div></div>
    <div class="card"><div class="card-label">KANDIDAT TURNAROUND<span class="tip" onclick="showHelp('kandidat_turnaround')">?</span></div><div class="card-val b">{full_count}</div><div class="card-sub">Saham tertekan yang mulai menunjukkan pemulihan</div></div>
    <div class="card"><div class="card-label">Universe</div><div class="card-val">{summary_data.get('universe_size', 0)}</div><div class="card-sub">IDX30 tickers</div></div>
  </div>
  <div class="section-title">Signal Diagnostics</div>
  <div class="card-grid">
    <div class="card"><div class="card-label">KEKUATAN MULAI NAIK<span class="tip" onclick="showHelp('kekuatan_mulai_naik')">?</span></div><div class="card-val g">{sig.get('rs_change_60d_positive_count', 0)}</div><div class="card-sub">Saham yang mulai outperform pasar</div></div>
    <div class="card"><div class="card-label">MINAT BELI MENINGKAT<span class="tip" onclick="showHelp('minat_beli_meningkat')">?</span></div><div class="card-val y">{sig.get('volume_ratio_high_count', 0)}</div><div class="card-sub">Aktivitas perdagangan di atas normal</div></div>
    <div class="card"><div class="card-label">DI ATAS TREND PENDEK<span class="tip" onclick="showHelp('di_atas_trend_pendek')">?</span></div><div class="card-val">{sig.get('above_ma20_count', 0)}</div><div class="card-sub">Harga di atas rata-rata 20 hari</div></div>
    <div class="card"><div class="card-label">PANTUL DARI DASAR<span class="tip" onclick="showHelp('pantul_dari_dasar')">?</span></div><div class="card-val g">{sig.get('recovery_gt_10pct_count', 0)}</div><div class="card-sub">Memantul &gt;10% dari level terendah 60 hari</div></div>
    <div class="card"><div class="card-label">RATA-RATA PENURUNAN<span class="tip" onclick="showHelp('rata_penurunan')">?</span></div><div class="card-val r">{sig.get('avg_drawdown_252d', 0)}%</div><div class="card-sub">Rata-rata penurunan dari harga tertinggi</div></div>
    <div class="card"><div class="card-label">RATA-RATA GEJOLAK<span class="tip" onclick="showHelp('rata_gejolak')">?</span></div><div class="card-val y">{sig.get('avg_volatility_60d', 0)}%</div><div class="card-sub">Intensitas pergerakan harga rata-rata</div></div>
  </div>
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
  <div class="section-title">Pipeline Diagnostics<span class="tip" onclick="showHelp('diagnostics')">?</span></div>
  <div class="card-grid">
    <div class="card wide-card">
      <div class="card-label">Pipeline Status</div>
      <div style="display:flex;align-items:center;gap:8px;margin-top:4px">
        <span style="width:8px;height:8px;border-radius:50%;background:#00c26f;display:inline-block"></span>
        <span style="font-size:14px;font-weight:600">OPERATIONAL</span>
      </div>
      <div class="card-sub">All systems nominal</div>
    </div>
    <div class="card"><div class="card-label">Last Leaders Update</div><div class="card-val" style="font-size:14px">{file_age(LEADERS_FILE)}</div><div class="card-sub">leaders_latest.csv</div></div>
    <div class="card"><div class="card-label">Last Turnaround Update</div><div class="card-val" style="font-size:14px">{file_age(TURNAROUND_FILE)}</div><div class="card-sub">turnaround_latest.csv</div></div>
    <div class="card"><div class="card-label">Last Exit Update</div><div class="card-val" style="font-size:14px">{file_age(EXIT_FILE)}</div><div class="card-sub">exit_watchlist_latest.csv</div></div>
    <div class="card"><div class="card-label">Records Processed</div><div class="card-val g">{summary_data.get('universe_size', 0)}</div><div class="card-sub">tickers in latest run</div></div>
    <div class="card"><div class="card-label">Data Freshness</div><div class="card-val g">{summary_data.get('date', 'N/A')}</div><div class="card-sub">report date</div></div>
    <div class="card"><div class="card-label">History Records</div><div class="card-val b">{len(history)}</div><div class="card-sub">turnaround_history.csv</div></div>
    <div class="card"><div class="card-label">Workflow</div><div class="card-val" style="font-size:13px">daily_radar.yml</div><div class="card-sub">cron: 30 9 * * * (16:30 WIB)</div></div>
  </div>
</div>

<div class="tc" id="t5">
  <div class="section-title">Portfolio Simulator · Investment Simulation</div>
  <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;align-items:center">
    <input type="text" id="pi-ticker" class="pi-input" placeholder="Ticker" style="width:100px">
    <input type="number" id="pi-investment" class="pi-input" placeholder="Investment (Rp)" style="width:140px">
    <input type="number" id="pi-entry" class="pi-input" placeholder="Entry Price" style="width:120px">
    <button class="pi-add" onclick="addPosition()">+ Add</button>
  </div>
  <div class="card-grid" id="mp-cards"></div>
  <table>
    <thead><tr>
      <th data-key="ticker">Ticker</th><th data-key="investment">Investment</th><th data-key="entry_price">Entry Price</th><th data-key="current_price">Current Price</th><th data-key="estimated_shares">Est. Shares</th><th data-key="current_value">Current Value</th><th data-key="profit_loss">P/L Rp</th><th data-key="profit_loss_pct">P/L %</th><th data-key="weight">Weight</th><th data-key="rank" style="font-size:9px;color:#64748b">Rank</th><th data-key="exit_status" style="font-size:9px;color:#64748b">Exit</th><th data-key="sector" style="font-size:9px;color:#64748b">Sector</th><th style="width:30px"></th>
    </tr></thead>
    <tbody id="tbody-portfolio"></tbody>
  </table>
</div>

<div class="tc" id="t6">
  <div class="section-title">Exit Monitor<span class="tip" onclick="showHelp('exit')">?</span></div>
  <div style="margin-bottom:12px;background:#171b20;border:1px solid #222830;border-radius:6px;padding:10px 12px">
    <div style="font-size:9px;font-family:'Space Mono',monospace;color:#9CA3AF;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;font-weight:600">LEGENDA RULE EXIT</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 12px">
      <div style="font-size:11px"><span style="display:inline-block;background:#222830;color:#F5F7FA;border-radius:3px;padding:1px 5px;font-family:'Space Mono',monospace;font-weight:700;font-size:10px;margin-right:4px">A</span> Peringkat Turun (Rank &gt; 10)</div>
      <div style="font-size:11px"><span style="display:inline-block;background:#222830;color:#F5F7FA;border-radius:3px;padding:1px 5px;font-family:'Space Mono',monospace;font-weight:700;font-size:10px;margin-right:4px">B</span> Momentum Melemah (RS20 &lt; 0 &amp; RS Chg 20D &lt; 0)</div>
      <div style="font-size:11px"><span style="display:inline-block;background:#222830;color:#F5F7FA;border-radius:3px;padding:1px 5px;font-family:'Space Mono',monospace;font-weight:700;font-size:10px;margin-right:4px">C</span> Trend MA50 Rusak (Close &lt; MA50)</div>
      <div style="font-size:11px"><span style="display:inline-block;background:#222830;color:#F5F7FA;border-radius:3px;padding:1px 5px;font-family:'Space Mono',monospace;font-weight:700;font-size:10px;margin-right:4px">D</span> Pelemahan Terkonfirmasi (Close &lt; MA100 atau DD &gt; 15%)</div>
    </div>
  </div>
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

<div class="overlay" id="overlay"></div>
<div class="panel" id="panel">
  <div class="panel-hdr">
    <div><div class="tk" id="ptk"></div><div class="name" id="pname"></div></div>
    <button class="panel-close" onclick="closePanel()">✕</button>
  </div>
  <div class="panel-body" id="pbody"></div>
</div>

<div class="help-modal" id="help">
  <div class="help-hdr">
    <div class="help-title" id="htitle"></div>
    <button class="help-close" onclick="closeHelp()">✕</button>
  </div>
  <div class="help-body" id="hbody"></div>
</div>

<script>
const L={leaders_json};
const T={turnaround_json};
const SM={summary_json};
const SK={streaks_json};
const EX={exit_json};
const MP={portfolio_json};
const HLP={hlp_json};

function fmtRupiah(v){{return (v>=0?'':'−')+'Rp '+Math.abs(v).toLocaleString('id-ID')}}
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
      return '<tr><td class="tk" style="color:#9CA3AF;font-size:11px">'+r.rank+'</td><td class="tk tk-click" data-ticker="'+r.ticker.split('.')[0]+'" style="color:'+ac(r.ticker)+'">'+r.ticker.split('.')[0]+(r.rank<=5?'<span class="flag">★</span>':'')+'</td><td class="sf '+sc(r.final_score)+'">'+r.final_score.toFixed(1)+'</td><td>'+bar(r.quality,'#3b82f6')+'</td><td>'+bar(r.growth,'#10b981')+'</td><td>'+bar(r.value,'#a855f7')+'</td><td>'+bar(r.momentum,'#f59e0b')+'</td><td>'+(r.rank<=5?'<span class="badge bg-green">PORTFOLIO</span>':'<span class="badge bg-gray">WATCH</span>')+'</td></tr>'
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
  window.ef=function(v,b){{f=v;document.querySelectorAll('#t6 .tab-btn').forEach(function(x){{x.classList.remove('active')}});b.classList.add('active');refresh()}}
}})();

(function(){{
  var DATA=[];var s={{key:null,dir:'asc'}}
  function loadData(){{
    var st=localStorage.getItem('isi_portfolio')
    if(st){{try{{DATA=JSON.parse(st)}}catch(e){{DATA=[]}}}}else if(MP&&MP.length>0){{
      DATA=MP.map(function(r){{return{{ticker:r.ticker,investment:r.investment,entry_price:r.entry_price}}}})
      localStorage.setItem('isi_portfolio',JSON.stringify(DATA))
    }}
  }}
  function enrich(item){{
    var tk=item.ticker.indexOf('.JK')>0?item.ticker:item.ticker+'.JK'
    var inv=Number(item.investment)||0;var ep=Number(item.entry_price)||0
    var shares=ep>0?inv/ep:0
    var ed=null;EX.forEach(function(d){{if(d.ticker===tk)ed=d}})
    var ld=null;L.forEach(function(d){{if(d.ticker===tk)ld=d}})
    var cp=ep;if(ed&&ed.close)cp=Number(ed.close)||ep
    var cv=shares*cp;var pl=cv-inv;var pct=inv>0?(pl/inv*100):0
    var rank=ld?(Number(ld.rank)<=30?Number(ld.rank):99):99
    var es=ed?ed.exit_state:'HEALTHY'
    var tc=tk.replace('.JK','')
    var sec=(PF[tc]&&PF[tc].sector)||(PF[tk]&&PF[tk].sector)||''
    return{{ticker:tc,investment:inv,entry_price:ep,estimated_shares:shares,current_price:cp,current_value:cv,profit_loss:pl,profit_loss_pct:pct,rank:rank,exit_status:es,sector:sec}}
  }}
  function render(){{
    var enriched=DATA.map(enrich)
    var total=enriched.reduce(function(s,r){{return s+r.current_value}},0)
    enriched.forEach(function(r){{r.weight=total>0?(r.current_value/total*100):0}})
    enriched.sort(function(a,b){{return a.ticker.localeCompare(b.ticker)}})
    var ti=enriched.reduce(function(s,r){{return s+r.investment}},0)
    var tv=enriched.reduce(function(s,r){{return s+r.current_value}},0)
    var tp=enriched.reduce(function(s,r){{return s+r.profit_loss}},0)
    var ret=ti>0?((tv-ti)/ti*100):0
    var secs={{}},sl=[]
    enriched.forEach(function(r){{var sc=r.sector||'Unknown';if(!secs[sc]){{secs[sc]=0;sl.push(sc)}}secs[sc]++}})
    var ts=sl.sort(function(a,b){{return secs[b]-secs[a]}}).slice(0,3).join(', ')
    document.getElementById('mp-cards').innerHTML=
      '<div class="card"><div class="card-label">Total Invested</div><div class="card-val">'+fmtRupiah(ti)+'</div><div class="card-sub">Total modal dimasukkan</div></div>'+
      '<div class="card"><div class="card-label">Current Value</div><div class="card-val">'+fmtRupiah(tv)+'</div><div class="card-sub">Nilai portofolio saat ini</div></div>'+
      '<div class="card"><div class="card-label">Profit / Loss</div><div class="card-val'+(tp>=0?' g':' r')+'">'+(tp>=0?'+':'')+fmtRupiah(tp)+'</div><div class="card-sub">Laba/rugi keseluruhan</div></div>'+
      '<div class="card"><div class="card-label">Portfolio Return</div><div class="card-val'+(ret>=0?' g':' r')+'">'+(ret>=0?'+':'')+ret.toFixed(2)+'%</div><div class="card-sub">Return investasi</div></div>'+
      '<div class="card"><div class="card-label">Holdings</div><div class="card-val b">'+enriched.length+'</div><div class="card-sub">Jumlah posisi</div></div>'+
      '<div class="card"><div class="card-label">Sector Exposure</div><div class="card-val b" style="font-size:14px">'+(ts||'—')+'</div><div class="card-sub">Sektor dominan</div></div>'
    document.getElementById('tbody-portfolio').innerHTML=enriched.map(function(r){{
      var eb=r.exit_status==='EXIT'?'bg-red':r.exit_status==='EXIT RISK'?'bg-yellow':r.exit_status==='WEAKENING'?'bg-yellow':r.exit_status==='EXIT WATCH'?'bg-blue':'bg-green'
      var rnk=r.rank>0&&r.rank<99?'#'+r.rank:'—'
      var plCls=r.profit_loss>=0?'high':'low'
      return '<tr><td class="tk tk-click" data-ticker="'+r.ticker+'">'+r.ticker+'</td><td style="font-family:Space Mono,monospace;font-weight:600">'+fmtRupiah(r.investment)+'</td><td style="font-family:Space Mono,monospace;font-weight:600">'+fmtRupiah(r.entry_price)+'</td><td style="font-family:Space Mono,monospace;font-weight:600">'+fmtRupiah(r.current_price)+'</td><td style="font-family:Space Mono,monospace">'+r.estimated_shares.toFixed(0)+'</td><td style="font-family:Space Mono,monospace;font-weight:600">'+fmtRupiah(r.current_value)+'</td><td class="sf '+plCls+'">'+(r.profit_loss>=0?'+':'')+fmtRupiah(r.profit_loss)+'</td><td class="sf '+plCls+'">'+(r.profit_loss_pct>=0?'+':'')+r.profit_loss_pct.toFixed(2)+'%</td><td style="font-family:Space Mono,monospace;color:#9CA3AF">'+r.weight.toFixed(1)+'%</td><td style="font-family:Space Mono,monospace;font-size:10px;color:#64748b">'+rnk+'</td><td style="font-size:10px"><span class="badge '+eb+'" style="font-size:8px">'+r.exit_status+'</span></td><td style="font-size:10px;color:#64748b">'+(r.sector||'—')+'</td><td><button class="del-btn" onclick="removePosition(\\''+r.ticker+'\\')">✕</button></td></tr>'
    }}).join('')
  }}
  loadData();render()
  window.addPosition=function(){{
    var t=document.getElementById('pi-ticker').value.trim().toUpperCase()
    var i=parseFloat(document.getElementById('pi-investment').value)||0
    var e=parseFloat(document.getElementById('pi-entry').value)||0
    if(!t||i<=0||e<=0)return
    DATA.push({{ticker:t,investment:i,entry_price:e}})
    localStorage.setItem('isi_portfolio',JSON.stringify(DATA))
    document.getElementById('pi-ticker').value='';document.getElementById('pi-investment').value='';document.getElementById('pi-entry').value=''
    render()
  }}
  window.removePosition=function(t){{
    DATA=DATA.filter(function(r){{return r.ticker!==t}})
    localStorage.setItem('isi_portfolio',JSON.stringify(DATA));render()
  }}
}})();

(function(){{
  try{{
  EX.forEach(function(d){{
    if(d.exit_state==='EXIT')exitCount++
    else if(d.exit_state==='EXIT RISK')exitRiskCount++
    else if(d.exit_state==='WEAKENING')weakeningCount++
    else if(d.exit_state==='EXIT WATCH')exitWatchCount++
    else if(d.exit_state==='HEALTHY')healthyCount++
  }})
  var top5=[];L.forEach(function(d){{if(d.rank<=5)top5.push(d.ticker)}})
  var portfolioExit=EX.filter(function(d){{return top5.indexOf(d.ticker)>=0&&d.exit_state!=='HEALTHY'}})
  var fullMatchCount=SM.full_match_count||0
  var sd=SM.signal_diagnostics||{{}}
  var avgDD=sd.avg_drawdown_252d||0
  var avgVol=sd.avg_volatility_60d||0
  var aboveMA20=sd.above_ma20_count||0
  var rsPositive=sd.rs_change_60d_positive_count||0
  var bigDrops=EX.filter(function(d){{return d.rank_change<=-2}}).length
  var rankDrops=EX.filter(function(d){{return d.rank_change<0}}).length
  var status='TIDAK ADA AKSI',cls='s-hijau',reasons=[],focuses=[]
  if(exitCount>=3){{
    status='RISIKO MENINGKAT';cls='s-merah'
    reasons.push(exitCount+' saham dalam status EXIT — tekanan keluar meluas')
    reasons.push(exitRiskCount+' EXIT RISK, '+weakeningCount+' weakening — sistem dalam tekanan')
  }}else if(exitCount>=1&&portfolioExit.length>0){{
    status='REVIEW';cls='s-kuning'
    reasons.push(exitCount+' saham EXIT, '+portfolioExit.length+' di antaranya dari portofolio 5 besar')
  }}else if(exitCount>=1||exitRiskCount>=2){{
    status='REVIEW';cls='s-kuning'
    if(exitCount>=1)reasons.push(exitCount+' saham EXIT terdeteksi')
    else reasons.push(exitRiskCount+' saham EXIT RISK — perhatikan perkembangan')
  }}else if(fullMatchCount>=3||avgDD<-25||avgVol>3.5||aboveMA20===0){{
    status='TAHAN';cls='s-biru'
    if(fullMatchCount>=3)reasons.push(fullMatchCount+' kandidat turnaround terdeteksi')
    if(avgDD<-25)reasons.push('Rata-rata penurunan IDX30 '+avgDD.toFixed(1)+'%')
    if(avgVol>3.5)reasons.push('Volatilitas '+avgVol.toFixed(2)+'% — fluktuasi di atas normal')
    if(aboveMA20===0)reasons.push('Seluruh IDX30 di bawah MA20 — tren pendek lemah')
  }}else{{
    reasons.push('Tidak ada sinyal exit signifikan')
    reasons.push('Rata-rata penurunan '+avgDD.toFixed(1)+'% — dalam batas wajar')
  }}
  if(reasons.length<2){{
    if(exitCount>0)reasons.push(exitCount+' saham EXIT, '+exitRiskCount+' EXIT RISK')
    else if(avgDD>-15)reasons.push('Penurunan pasar minimal ('+avgDD.toFixed(1)+'%)')
    else if(rsPositive>15)reasons.push(rsPositive+' dari 30 saham mulai menguat')
    else reasons.push(healthyCount+' dari '+EX.length+' saham dalam kondisi sehat')
  }}
  if(portfolioExit.length>0){{
    var tkr=portfolioExit.map(function(d){{return d.ticker.split('.')[0]}}).join(', ')
    focuses.push('Portofolio: '+tkr+' masuk sinyal exit — pantau pergerakan')
  }}else if(exitCount>0){{
    var ex=EX.filter(function(d){{return d.exit_state==='EXIT'}}).slice(0,3).map(function(d){{return d.ticker.split('.')[0]}}).join(', ')
    focuses.push('Pantau '+ex+' — saham dengan sinyal EXIT aktif')
  }}else if(fullMatchCount>=3&&SM.top_candidates){{
    var tkr=SM.top_candidates.filter(function(d){{return d.full_match}}).slice(0,3).map(function(d){{return d.ticker.split('.')[0]}}).join(', ')
    if(tkr)focuses.push('Pantau '+tkr+' — kandidat turnaround penuh')
    else focuses.push(fullMatchCount+' kandidat turnaround — pantau perkembangannya')
  }}else{{
    focuses.push('Pantau perubahan ranking harian — '+rankDrops+' saham turun peringkat')
  }}
  if(avgDD<-25){{
    focuses.push('Waspada tekanan pasar — rata-rata penurunan '+avgDD.toFixed(1)+'%')
  }}else if(aboveMA20===0){{
    focuses.push('Pasar melemah — 0 saham berhasil bertahan di atas MA20')
  }}else if(rsPositive>15){{
    focuses.push(rsPositive+' dari 30 saham menunjukkan penguatan — positif')
  }}else{{
    focuses.push(rankDrops+' saham turun peringkat hari ini — perhatikan distribusi')
  }}
  if(focuses.length>2)focuses=focuses.slice(0,2)
  if(reasons.length>3)reasons=reasons.slice(0,3)
  var h='<div class="conc"><div class="conc-hdr"><span class="conc-status '+cls+'">'+status+'</span><span class="conc-label">KESIMPULAN HARI INI</span></div><div class="conc-body"><div class="conc-col"><div class="conc-sub">Alasan</div><ul class="conc-list">'
  reasons.forEach(function(r){{h+='<li>'+r+'</li>'}})
  h+='</ul></div><div class="conc-col"><div class="conc-sub">Fokus Hari Ini</div><ul class="conc-list">'
  focuses.forEach(function(f){{h+='<li>'+f+'</li>'}})
  h+='</ul></div></div></div>'
  document.getElementById('conclusion').innerHTML=h
  }}catch(e){{console.error('Conclusion IIFE error:',e);document.getElementById('conclusion').innerHTML='<div class="conc" style="padding:12px;color:#ef4444;font-size:11px">Error loading conclusion: '+e.message+'</div>'}}
}})();

function st(i){{document.querySelectorAll('.tab-btn').forEach(function(b,j){{b.classList.toggle('active',j===i)}});document.querySelectorAll('.tc').forEach(function(t,j){{t.classList.toggle('active',j===i)}})}}

const PF={profiles_json};
const FD={fundamentals_json};

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
    lines.push('<div class="panel-status portfolio"><b>TOP 5 CONFIG B</b>')
    lines.push('<div style="margin-top:6px;font-size:11px;color:#9CA3AF;font-weight:400">')
    lines.push('<span class="panel-bullet">&#8226;</span>Peringkat 5 besar ranking engine')
    lines.push('<span class="panel-bullet">&#8226;</span>Bukan rekomendasi beli')
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

function showHelp(k){{
  var h=HLP[k]
  if(!h)return
  var titles={{leaders:'Config B Leaders',turnaround:'Turnaround Watchlist',diagnostics:'Pipeline Diagnostics',exit:'Exit Monitor',saham_tertekan:'Saham Tertekan',mulai_membaik:'Mulai Membaik',kandidat_turnaround:'Kandidat Turnaround',kekuatan_mulai_naik:'Kekuatan Mulai Naik',minat_beli_meningkat:'Minat Beli Meningkat',di_atas_trend_pendek:'Di Atas Trend Pendek',pantul_dari_dasar:'Pantul Dari Dasar',rata_penurunan:'Rata-Rata Penurunan',rata_gejolak:'Rata-Rata Gejolak'}}
  document.getElementById('htitle').textContent=titles[k]||k
  document.getElementById('hbody').innerHTML=h
  document.getElementById('help').classList.add('show')
  document.getElementById('overlay').classList.add('show')
}}

function closeHelp(){{
  document.getElementById('help').classList.remove('show')
  document.getElementById('overlay').classList.remove('show')
}}

function closeAll(){{closePanel();closeHelp()}}

document.addEventListener('keydown',function(e){{if(e.key==='Escape')closeAll()}})
document.addEventListener('click',function(e){{
  var t=e.target.closest('.tk-click')
  if(t){{var tkr=t.getAttribute('data-ticker')||t.textContent.trim();e.stopPropagation();openPanel(tkr);return}}
  var tip=e.target.closest('.tip')
  if(tip)return
  var h=e.target.closest('.help-modal')
  var o=e.target.closest('#overlay')
  var p=e.target.closest('#panel')
  if(o){{closePanel();if(!h)closeHelp()}}
  if(!h&&document.getElementById('help').classList.contains('show'))closeHelp()
}})
;(function(){{
  var p=document.getElementById('panel'),o=document.getElementById('overlay')
  var sx=0,sy=0,dx=0,dragging=false,th=80
  p.addEventListener('touchstart',function(e){{
    if(!p.classList.contains('show'))return
    var t=e.touches[0];sx=t.clientX;sy=t.clientY;dx=0;dragging=false
  }},{{passive:true}})
  p.addEventListener('touchmove',function(e){{
    if(!p.classList.contains('show')||sx===0)return
    var cx=e.touches[0].clientX-sx,cy=e.touches[0].clientY-sy
    if(!dragging){{
      if(Math.abs(cx)<10&&Math.abs(cy)<10)return
      if(Math.abs(cx)<Math.abs(cy))return
      if(cx<0)return
      dragging=true;p.classList.add('panel-dragging')
    }}
    dx=cx
    if(dx>window.innerWidth)dx=window.innerWidth
    p.style.transform='translateX('+dx+'px)'
    o.style.opacity=Math.max(0,.5*(1-dx/window.innerWidth))
  }},{{passive:false}})
  p.addEventListener('touchend',function(){{
    if(sx===0)return
    if(dragging){{
      p.classList.remove('panel-dragging')
      if(dx>th){{p.style.transform='';o.style.opacity='';closePanel()}}
      else{{p.style.transform='';o.style.opacity=''}}
    }}
    sx=0;dragging=false
  }},{{passive:true}})
}})()
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
    print(f"  Loaded: {len(leaders)} leaders, {len(turnaround)} turnaround, summary")
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
    portfolio_data = []
    if PORTFOLIO_FILE.exists():
        portfolio_raw = read_json(PORTFOLIO_FILE)
        if portfolio_raw:
            portfolio_data = calculate_portfolio(portfolio_raw, leaders, exit_data, profiles)
            print(f"  Calculated {len(portfolio_data)} portfolio positions")
        else:
            print("  No portfolio positions found")
    else:
        print("  No portfolio_simulator.json found — skipping")
    print("  Generating HTML...")
    html = build_html(leaders, turnaround, summary, history, streaks, date_str, exit_data, profiles, fundamentals, portfolio_data)
    V2_DIR.mkdir(parents=True, exist_ok=True)
    output_path = V2_DIR / 'index.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  Written: {output_path.resolve()}")
    print("=== Dashboard V2 Complete ===")

if __name__ == '__main__':
    main()
