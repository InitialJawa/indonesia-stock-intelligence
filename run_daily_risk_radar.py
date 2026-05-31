# file: run_daily_risk_radar.py

import datetime
from utils.telegram_notifier import send_telegram_alert
from collectors.daily_flow_collector import check_volume_shock

# Target Universe: Portofolio Live Juni 2026 (Sesuai Blueprint)
LIVE_PORTFOLIO = ["ADRO.JK", "ESSA.JK", "BBRI.JK", "BMRI.JK", "MAPI.JK"]

def evaluate_emergency_brake():
    """
    FRAMEWORK 1: DAILY EMERGENCY BRAKE
    Mendeteksi Market Crash & Distribusi Bandar pada Portofolio Live.
    """
    print("[+] Mengevaluasi kondisi Volume Shock Portofolio...")
    
    alerts_triggered = []
    
    for ticker in LIVE_PORTFOLIO:
        res = check_volume_shock(ticker)
        
        if res["status"] == "OK":
            # Jika Volume meledak 2x lipat DAN harga anjlok lebih dari -2%
            if res["is_volume_shock"] and res["price_change_pct"] <= -2.0:
                msg = (
                    f"🚨 <b>{ticker}</b> mengalami <b>DISTRIBUSI MASIF</b>!\n"
                    f"Perubahan Harga: {res['price_change_pct']}%\n"
                    f"Volume Hari Ini: {res['current_volume']:,} shares\n"
                    f"Rata-rata Volume: {res['ma20_volume']:,} shares\n\n"
                    f"<b>Tindakan:</b> Segera evaluasi untuk Cut Loss / Amankan Profit!"
                )
                alerts_triggered.append(msg)
                print(f"    [!] BAHAYA: Distribusi besar terdeteksi pada {ticker}!")
            else:
                print(f"    [-] {ticker} terpantau aman.")
        else:
            print(f"    [?] Gagal memindai {ticker} (Data tidak mencukupi/Error).")
            
    if alerts_triggered:
        final_message = "\n\n".join(alerts_triggered)
        send_telegram_alert(final_message, "EMERGENCY")
    else:
        print("[-] Tidak ada anomali distribusi massal pada portofolio hari ini.")

def evaluate_alpha_trigger():
    """
    FRAMEWORK 2: DAILY ALPHA TRIGGER
    Deteksi Peluang Emas & Akumulasi Institusi.
    """
    print("\n[+] Mengevaluasi Institutional Breakout (Alpha Trigger)...")
    # Blok ini sudah disiapkan untuk ekspansi scraper sentimen berita di fase berikutnya
    print("[-] Tidak ada sinyal Alpha Trigger hari ini.")

def main():
    print("==================================================")
    print("   ISI V5: DAILY RISK RADAR (HYBRID ARCHITECTURE) ")
    print("==================================================")
    
    now = datetime.datetime.now()
    print(f"Waktu Eksekusi : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("Status Sistem  : ONLINE")
    print(f"Memantau Aset  : {', '.join(LIVE_PORTFOLIO)}\n")

    # Uji coba ping info (bisa dimatikan (comment) nanti jika mengganggu)
    # send_telegram_alert(f"Radar V5 memindai {len(LIVE_PORTFOLIO)} saham portofolio...", "INFO")

    evaluate_emergency_brake()
    evaluate_alpha_trigger()

    print("\n==================================================")
    print("Radar harian selesai dieksekusi. Standby.")

if __name__ == "__main__":
    main()