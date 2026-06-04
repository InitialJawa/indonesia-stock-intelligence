# file: dashboard/generate_dashboard.py

import json
import pandas as pd
from pathlib import Path

def load_json(filepath):
    """Fungsi pembantu untuk memuat file JSON dengan aman."""
    path = Path(filepath)
    if not path.exists():
        print(f"WARNING: File {filepath} tidak ditemukan.")
        return [] 
    with open(path, 'r') as f:
        return json.load(f)

def get_action_label(row):
    """
    Mengklasifikasikan status aksi berdasarkan skor faktor.
    """
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
        return '<span class="badge bg-danger">⚠️ Rawan Pucuk</span>'
    elif m >= 55 and m <= 80 and q > 60 and v > 50:
        return '<span class="badge bg-success">🚀 Sedang Anget</span>'
    elif v > 80 and m < 40:
        return '<span class="badge bg-secondary">⚓ Murah Tapi Mati</span>'
    elif m > 80 and q < 40 and g < 40:
        return '<span class="badge bg-warning text-dark">🗑️ Gorengan Murni</span>'
    else:
        return '<span class="badge bg-light text-dark">➖ Pantau Terbatas</span>'

def generate_dashboard():
    print("--- Membangun ISI V4 Dashboard ---")
    
    # 1. Load Semua Data (Semua berformat List of Dicts)
    final_scores = load_json("output/scores/final_ranking_v3.json")
    q_data = load_json("output/scores/quality_ranking.json")
    v_data = load_json("output/scores/value_ranking.json")
    g_data = load_json("output/scores/growth_ranking.json")
    m_data = load_json("output/scores/momentum_ranking.json")
    
    # Konversi data faktor ke dictionary {ticker: score} untuk pencarian cepat
    q_scores = {x.get('ticker'): x.get('quality_score') for x in q_data} if isinstance(q_data, list) else {}
    v_scores = {x.get('ticker'): x.get('value_score') for x in v_data} if isinstance(v_data, list) else {}
    g_scores = {x.get('ticker'): x.get('growth_score') for x in g_data} if isinstance(g_data, list) else {}
    m_scores = {x.get('ticker'): x.get('momentum') for x in m_data} if isinstance(m_data, list) else {}

    # 3. Load Portfolio Warehouse
    try:
        df_port = pd.read_csv("database/historical/portfolio_warehouse.csv")
        latest_month = df_port['date'].max()
        current_portfolio = df_port[df_port['date'] == latest_month]['ticker'].tolist()
    except Exception as e:
        print(f"WARNING: Gagal membaca Portfolio Warehouse. Error: {e}")
        latest_month = "Unknown"
        current_portfolio = []

    # 4. Load Daily Radar Status
    radar_data = load_json("output/daily_radar_status.json")
    if isinstance(radar_data, dict):
        radar_update = radar_data.get("last_update", "Belum Tersedia")
        radar_status = radar_data.get("status", "UNKNOWN")
        radar_anomalies = radar_data.get("anomalies", [])
        radar_detail = radar_data.get("detail_message", "")
    else:
        radar_update = "Belum Tersedia"
        radar_status = "UNKNOWN"
        radar_anomalies = []
        radar_detail = ""

    # Determine alert class and status text for Daily Radar Card
    if radar_status == "SAFE":
        radar_color = "success"
        radar_badge = "<span class='badge bg-success mx-1'>SAFE / AMAN</span>"
        radar_desc = "Tidak ada anomali distribusi massal pada watchlist hari ini. Portofolio terpantau aman."
    elif radar_status == "WARNING":
        radar_color = "danger"
        radar_badge = "<span class='badge bg-danger mx-1'>WARNING / WASPADA</span>"
        anomalies_str = ", ".join(radar_anomalies)
        radar_desc = f"Terdeteksi anomali volume shock/distribusi masif pada emiten: <strong>{anomalies_str}</strong>. Segera evaluasi!"
    else:
        radar_color = "secondary"
        radar_badge = "<span class='badge bg-secondary mx-1'>BELUM TERSEDIA</span>"
        radar_desc = "Status radar harian belum diperbarui untuk hari ini."

    radar_detail_p = f'<p class="mb-0 text-muted small mt-2 py-1" style="background-color: #1c2128; border-radius: 4px; border: 1px solid #30363d; padding-left: 10px; padding-right: 10px;">{radar_detail}</p>' if radar_detail else ""

    radar_html = f"""
            <div class="row justify-content-center mb-4">
                <div class="col-md-8">
                    <div class="card p-4 border-{radar_color} text-center shadow-sm">
                        <h4 class="mb-1" style="color: #8b949e;">Daily Radar Status</h4>
                        <div class="my-2">{radar_badge}</div>
                        {radar_detail_p}
                        <p class="text-muted small mb-2 mt-3">Terakhir Diperbarui: <strong>{radar_update}</strong></p>
                        <p class="mb-0 small">{radar_desc}</p>
                    </div>
                </div>
            </div>
    """

    # 5. Bangun Baris Tabel HTML
    rows_html = ""
    rank = 1
    
    # PERBAIKAN BUG: Iterasi List of Dicts
    if isinstance(final_scores, list):
        for item in final_scores:
            ticker = item.get("ticker", "UNKNOWN")
            final = item.get("final_score", 0)
            
            # Cek apakah saham masuk ke portofolio
            is_portfolio = "⭐" if ticker in current_portfolio else ""
            row_class = "table-active fw-bold text-info" if ticker in current_portfolio else ""
            
            # Ambil skor komponen
            q = q_scores.get(ticker, "-")
            g = g_scores.get(ticker, "-")
            v = v_scores.get(ticker, "-")
            m = m_scores.get(ticker, "-")

            action_label = get_action_label({
                'quality': q,
                'growth': g,
                'value': v,
                'momentum': m
            })

            rows_html += f"""
            <tr class="{row_class}">
                <td>{rank}</td>
                <td><strong>{ticker}</strong> {is_portfolio}</td>
                <td>{q}</td>
                <td>{g}</td>
                <td>{v}</td>
                <td>{m}</td>
                <td class="text-warning"><strong>{final}</strong></td>
                <td>{action_label}</td>
            </tr>
            """
            rank += 1
    else:
        print("ERROR: Format final_scores tidak dikenali. Pastikan file JSON berformat List of Dicts.")

    # Format Badge Portofolio
    badges = " ".join([f"<span class='badge bg-success mx-1'>{ticker}</span>" for ticker in current_portfolio])

    # 5. Bangun HTML Template (Menggunakan Bootstrap 5 Dark Mode)
    html_template = f"""
    <!DOCTYPE html>
    <html lang="id" data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ISI V4 | Quant Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }}
            .card {{ background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; }}
            .table {{ border-color: #30363d; }}
            .table th {{ background-color: #21262d; color: #58a6ff; font-weight: 600; border-bottom: 2px solid #30363d; }}
            .table-active {{ background-color: #1f6feb20 !important; border-left: 3px solid #58a6ff; }}
            .text-info {{ color: #58a6ff !important; }}
            .text-warning {{ color: #d2a8ff !important; }}
        </style>
    </head>
    <body>
        <div class="container py-5">
            <div class="text-center mb-5">
                <h1 class="fw-bold" style="color: #c9d1d9;">Indonesia Stock Intelligence <span style="color: #58a6ff;">(ISI V4)</span></h1>
                <p class="text-muted">Quantitative Research & Multi-Factor Investing Platform</p>
            </div>

            {radar_html}

            <div class="row justify-content-center mb-5">
                <div class="col-md-8">
                    <div class="card p-4 text-center shadow-sm">
                        <h4 class="mb-1" style="color: #8b949e;">Live Forward Portfolio</h4>
                        <p class="text-muted small mb-3">Target Bulan Imbal Hasil: <strong>{latest_month} (M+1)</strong></p>
                        <h2 class="mb-0">{badges}</h2>
                        <div class="mt-3 text-muted small">Alokasi: Equal Weight (20%)</div>
                    </div>
                </div>
            </div>

            <div class="card p-4 shadow-sm">
                <h5 class="mb-4" style="color: #8b949e;">Universe Ranking Board <span class="badge bg-secondary ms-2 text-dark">Percentile Normalized</span></h5>
                <div class="table-responsive">
                    <table class="table table-hover text-center align-middle mb-0">
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Ticker</th>
                                <th>Quality (30%)</th>
                                <th>Growth (25%)</th>
                                <th>Value (20%)</th>
                                <th>Momentum (25%)</th>
                                <th>Final Score</th>
                                <th>Status Aksi</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="text-center mt-4 text-muted small">
                <p>Generated automatically by ISI Pipeline.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # 6. Simpan File HTML (Menimpa file legacy lama Anda)
    output_path = Path("dashboard/index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
        
    print(f"Sukses! Dashboard HTML telah dibuat di: {output_path}")

if __name__ == "__main__":
    generate_dashboard()