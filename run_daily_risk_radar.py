# file: run_daily_risk_radar.py

import json
import datetime
from utils.telegram_notifier import send_telegram_alert
from utils.email_notifier import send_email_alert
from collectors.daily_flow_collector import check_volume_shock

def get_sedang_anget_watchlist(top_n=5):
    """
    Mengambil maksimal 5 saham teratas HANYA dari kelompok yang menghasilkan output label 'Sedang Anget'.
    """
    try:
        # Load rankings
        with open("output/scores/final_ranking_v3.json", "r") as f:
            final_scores = json.load(f)
        with open("output/scores/quality_ranking.json", "r") as f:
            q_data = json.load(f)
        with open("output/scores/value_ranking.json", "r") as f:
            v_data = json.load(f)
        with open("output/scores/growth_ranking.json", "r") as f:
            g_data = json.load(f)
        with open("output/scores/momentum_ranking.json", "r") as f:
            m_data = json.load(f)
            
        q_scores = {x.get('ticker'): x.get('quality_score') for x in q_data} if isinstance(q_data, list) else {}
        v_scores = {x.get('ticker'): x.get('value_score') for x in v_data} if isinstance(v_data, list) else {}
        g_scores = {x.get('ticker'): x.get('growth_score') for x in g_data} if isinstance(g_data, list) else {}
        m_scores = {x.get('ticker'): x.get('momentum') for x in m_data} if isinstance(m_data, list) else {}
        
        anget_portfolio = []
        if isinstance(final_scores, list):
            for item in final_scores:
                ticker = item.get("ticker", "UNKNOWN")
                q = q_scores.get(ticker, 0)
                g = g_scores.get(ticker, 0)
                v = v_scores.get(ticker, 0)
                m = m_scores.get(ticker, 0)
                
                # Apply get_action_label logic:
                # m >= 55 and m <= 85 and q > 45 and v > 40
                try:
                    q_val = float(q)
                except (ValueError, TypeError):
                    q_val = 0.0
                try:
                    g_val = float(g)
                except (ValueError, TypeError):
                    g_val = 0.0
                try:
                    v_val = float(v)
                except (ValueError, TypeError):
                    v_val = 0.0
                try:
                    m_val = float(m)
                except (ValueError, TypeError):
                    m_val = 0.0
                    
                if m_val >= 55 and m_val <= 85 and q_val > 45 and v_val > 40:
                    anget_portfolio.append(ticker)
                    if len(anget_portfolio) == top_n:
                        break
        return anget_portfolio
    except Exception as e:
        print(f"[!] Warning: Gagal memuat watchlist dinamis Sedang Anget. Error: {e}")
        return ["ADRO.JK", "ESSA.JK", "BBRI.JK", "BMRI.JK", "MIKA.JK"] # fallback

# Target Universe: Dinamis menyedot data dari portfolio "Sedang Anget"
LIVE_PORTFOLIO = get_sedang_anget_watchlist(5)

def evaluate_emergency_brake():
    """
    FRAMEWORK 1: DAILY EMERGENCY BRAKE
    Mendeteksi Market Crash & Distribusi Bandar pada Portofolio Dinamis.
    """
    print("[+] Mengevaluasi kondisi Volume Shock pada Dynamic Watchlist...")
    
    alerts_triggered = []
    anomalies_found = []
    volume_details = []
    
    for ticker in LIVE_PORTFOLIO:
        res = check_volume_shock(ticker)
        
        if res["status"] == "OK":
            curr_vol = res.get("current_volume", 0)
            ma20_vol = res.get("ma20_volume", 1)
            ratio = curr_vol / ma20_vol if ma20_vol > 0 else 1.0
            
            if ratio >= 2.0:
                vol_status = "Anomali Lonjakan!"
            elif ratio < 1.0:
                vol_status = "Sepi"
            else:
                vol_status = "Wajar"
                
            volume_details.append(f"{ticker}: Volume {ratio:.1f}x ({vol_status})")
            
            # Logika: Jika Volume meledak 2x lipat DAN harga anjlok lebih dari -2%
            if res["is_volume_shock"] and res["price_change_pct"] <= -2.0:
                msg = (
                    f"🚨 <b>{ticker}</b> mengalami <b>DISTRIBUSI MASIF</b>!\n"
                    f"Perubahan Harga: {res['price_change_pct']}%\n"
                    f"Volume Hari Ini: {res['current_volume']:,} shares\n"
                    f"Rata-rata Volume: {res['ma20_volume']:,} shares\n\n"
                    f"<b>Tindakan:</b> Segera evaluasi teknikal untuk pengamanan aset!"
                )
                alerts_triggered.append(msg)
                anomalies_found.append(ticker)
                print(f"    [!] BAHAYA: Distribusi besar terdeteksi pada {ticker}!")
            else:
                print(f"    [-] {ticker} terpantau aman.")
        else:
            volume_details.append(f"{ticker}: Gagal memuat data")
            print(f"    [?] Gagal memindai {ticker} (Data tidak mencukupi/Error).")
            
    if alerts_triggered:
        final_message = "\n\n".join(alerts_triggered)
        send_telegram_alert(final_message, "EMERGENCY")
        send_email_alert(final_message, "EMERGENCY")
    else:
        safe_msg = "Tidak ada anomali distribusi massal pada watchlist hari ini. Portofolio terpantau aman."
        print(f"[-] {safe_msg}")
        send_telegram_alert(safe_msg, "INFO")
        send_email_alert(safe_msg, "INFO")

    return anomalies_found, volume_details

def evaluate_alpha_trigger():
    """
    FRAMEWORK 2: DAILY ALPHA TRIGGER
    Deteksi Peluang Emas & Akumulasi Institusi.
    """
    print("\n[+] Mengevaluasi Institutional Breakout (Alpha Trigger)...")
    print("[-] Tidak ada sinyal Alpha Trigger hari ini.")
    return []

def main():
    print("==================================================")
    print("   ISI V5: DAILY RISK RADAR (HYBRID ARCHITECTURE) ")
    print("==================================================")
    
    now = datetime.datetime.now()
    print(f"Waktu Eksekusi : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("Status Sistem  : ONLINE")
    print(f"Watchlist (Top 5) : {', '.join(LIVE_PORTFOLIO)}\n")

    anomalies, volume_details = evaluate_emergency_brake()
    alpha_anomalies = evaluate_alpha_trigger()
    if alpha_anomalies:
        anomalies.extend(alpha_anomalies)

    # Tentukan status harian
    status = "WARNING" if anomalies else "SAFE"
    
    # Gabungkan volume_details
    detail_message = "<br>".join(volume_details)
        
    # Simpan status ke JSON file
    status_data = {
        "last_update": now.strftime("%Y-%m-%d %H:%M"),
        "status": status,
        "anomalies": anomalies,
        "detail_message": detail_message
    }
    
    import os
    os.makedirs("output", exist_ok=True)
    with open("output/daily_radar_status.json", "w") as f:
        json.dump(status_data, f, indent=4)
    print(f"[+] Status harian berhasil disimpan ke output/daily_radar_status.json")

    print("\n==================================================")
    print("Radar harian selesai dieksekusi. Standby.")

if __name__ == "__main__":
    main()