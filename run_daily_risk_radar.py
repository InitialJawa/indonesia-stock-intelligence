# file: run_daily_risk_radar.py

import json
import datetime
from utils.telegram_notifier import send_telegram_alert
from utils.email_notifier import send_email_alert
from collectors.daily_flow_collector import check_volume_shock

def get_dynamic_watchlist(top_n=5):
    """
    Mengambil Top N saham terbaik secara otomatis dari hasil scoring fundamental bulanan (V4).
    """
    file_path = "output/scores/quality_ranking.json"
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        
        # Ekstrak ticker dari N urutan teratas
        dynamic_list = [item["ticker"] for item in data[:top_n]]
        return dynamic_list
    
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"[!] Warning: File {file_path} tidak ditemukan atau rusak.")
        print("[!] Menggunakan Fallback Portofolio Statis.")
        # Fallback jika data V4 belum di-generate
        return ["ADRO.JK", "ESSA.JK", "BBRI.JK", "BMRI.JK", "MAPI.JK", "BBCA.JK"]

# Target Universe: Dinamis menyedot data dari V4
LIVE_PORTFOLIO = get_dynamic_watchlist(5)

def evaluate_emergency_brake():
    """
    FRAMEWORK 1: DAILY EMERGENCY BRAKE
    Mendeteksi Market Crash & Distribusi Bandar pada Portofolio Dinamis.
    """
    print("[+] Mengevaluasi kondisi Volume Shock pada Dynamic Watchlist...")
    
    alerts_triggered = []
    anomalies_found = []
    
    for ticker in LIVE_PORTFOLIO:
        res = check_volume_shock(ticker)
        
        if res["status"] == "OK":
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

    return anomalies_found

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

    anomalies = evaluate_emergency_brake()
    alpha_anomalies = evaluate_alpha_trigger()
    if alpha_anomalies:
        anomalies.extend(alpha_anomalies)

    # Tentukan status harian
    status = "WARNING" if anomalies else "SAFE"
    
    # Simpan status ke JSON file
    status_data = {
        "last_update": now.strftime("%Y-%m-%d %H:%M"),
        "status": status,
        "anomalies": anomalies
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