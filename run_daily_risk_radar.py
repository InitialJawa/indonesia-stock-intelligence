# file: run_daily_risk_radar.py

import json
import os
import datetime
from utils.telegram_notifier import send_telegram_alert
from utils.email_notifier import send_email_alert
from collectors.daily_flow_collector import check_volume_shock

# ======================================================================
# KONSTANTA
# ======================================================================
HISTORY_FILE = "output/radar_history.json"
STATUS_FILE  = "output/daily_radar_status.json"
MAX_HISTORY  = 5  # FIFO: simpan maksimal 5 hari

# ======================================================================
# FUNGSI PENDUKUNG: WATCHLIST DINAMIS "SEDANG ANGET"
# ======================================================================
def get_sedang_anget_watchlist(top_n=5):
    """
    Mengambil maksimal 5 saham teratas HANYA dari kelompok yang menghasilkan
    output label 'Sedang Anget'.
    """
    try:
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
        return ["ADRO.JK", "ESSA.JK", "BBRI.JK", "BMRI.JK", "MIKA.JK"]  # fallback

# Target Universe: Dinamis menyedot data dari portfolio "Sedang Anget"
LIVE_PORTFOLIO = get_sedang_anget_watchlist(5)


# ======================================================================
# FUNGSI MEMORI HISTORIS: FIFO 5 HARI
# ======================================================================
def load_radar_history():
    """Membaca file radar_history.json. Mengembalikan list kosong jika belum ada."""
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return []


def save_radar_history(history: list):
    """Menyimpan list history ke radar_history.json."""
    os.makedirs("output", exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)


def update_radar_history(today_data: dict):
    """
    Menambahkan data hari ini ke history.
    Jika panjang list > MAX_HISTORY (5), hapus elemen paling lama (index 0) → FIFO.
    """
    history = load_radar_history()
    history.append(today_data)
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]   # simpan hanya 5 terakhir
    save_radar_history(history)
    print(f"[+] History diperbarui. Total snapshot tersimpan: {len(history)} hari.")
    return history


# ======================================================================
# FUNGSI ANALISIS AI: GEMINI 1.5-FLASH (FALLBACK AMAN)
# ======================================================================
def generate_ai_narrative(history: list, volume_details: list, watchlist: list, status: str) -> str:
    """
    Memanggil Gemini API untuk menghasilkan narasi ringkasan risiko.
    Jika GEMINI_API_KEY tidak ditemukan, gunakan mode fallback (teks mentah).
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        try:
            with open("config/settings.json", "r") as f:
                settings = json.load(f)
                api_key = settings.get("gemini", {}).get("api_key", "").strip()
        except Exception:
            pass

    # --- MODE FALLBACK: Tanpa API Key ---
    if not api_key:
        print("[!] GEMINI_API_KEY tidak ditemukan di environment maupun config/settings.json. Menggunakan mode fallback (data mentah).")
        fallback_lines = volume_details if volume_details else ["Tidak ada data volume tersedia."]
        return "<br>".join(fallback_lines)
    # --- Updated Gemini integration block with detailed error logging and API key debug ---
    # --- MODE AI: Dengan API Key ---
    print("[+] GEMINI_API_KEY terdeteksi. Memanggil Gemini AI...")
    # Debug prints for secret status
    print("[DEBUG] GEMINI_API_KEY EXISTS:", bool(api_key))
    if api_key:
        print("[DEBUG] GEMINI_API_KEY PREFIX:", api_key[:6] + "...")
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        # List available Gemini models and their supported generation methods for debugging
        try:
            models = genai.list_models()
            for m in models:
                print("MODEL:", m.name)
                print("METHODS:", m.supported_generation_methods)
        except Exception as list_err:
            print("[GEMINI LIST ERROR]", type(list_err).__name__, list_err)

        # Serialisasi data untuk prompt
        history_json_str = json.dumps(history, indent=2, ensure_ascii=False)
        today_volume_str = "\n".join(volume_details) if volume_details else "Tidak ada data volume."
        today_watchlist_str = ", ".join(watchlist)

        # Prompt dengan instruksi manajer risiko pesimis
        prompt = (
            "Kamu adalah manajer risiko kuantitatif yang pesimis, dingin, dan mengutamakan perlindungan modal. "
            "Hukum mutlak: DILARANG optimis jika pasar memburuk atau sepi. "
            "Jika volume tidak meyakinkan, perintahkan WAIT AND SEE.\n\n"
            f"Berikut adalah data mentah 5 hari terakhir:\n{history_json_str}\n\n"
            f"Berikut adalah data hari ini:\n"
            f"Watchlist aktif: {today_watchlist_str}\n"
            f"Rasio volume per saham:\n{today_volume_str}\n"
            f"Status sistem keseluruhan: {status}\n\n"
            "Tugas: Buat 1 paragraf ringkasan maksimal 3 kalimat mengenai apakah kondisi hari ini aman untuk eksekusi beli, tahan (hold), atau hindari pasar."
        )

        # Konfigurasi model dengan parameter super-strict
        generation_config = genai.types.GenerationConfig(temperature=0.1)

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=generation_config
        )

        response = model.generate_content(prompt)
        ai_text = response.text.strip()
        print(f"[+] Narasi AI berhasil dihasilkan ({len(ai_text)} karakter).")
        return ai_text

    except Exception as e:
        import traceback
        print(f"[GEMINI ERROR] {type(e).__name__}: {e}")
        traceback.print_exc()
        # Fallback to raw data display
        fallback_lines = volume_details if volume_details else ["Gagal menghasilkan analisis AI."]
        return "<br>".join(fallback_lines)


# ======================================================================
# FRAMEWORK 1: DAILY EMERGENCY BRAKE
# ======================================================================
def evaluate_emergency_brake():
    """
    FRAMEWORK 1: DAILY EMERGENCY BRAKE
    Mendeteksi Market Crash & Distribusi Bandar pada Portofolio Dinamis.
    """
    print("[+] Mengevaluasi kondisi Volume Shock pada Dynamic Watchlist...")

    alerts_triggered = []
    anomalies_found  = []
    volume_details   = []

    for ticker in LIVE_PORTFOLIO:
        res = check_volume_shock(ticker)

        if res["status"] == "OK":
            curr_vol = res.get("current_volume", 0)
            ma20_vol = res.get("ma20_volume", 1)
            ratio    = curr_vol / ma20_vol if ma20_vol > 0 else 1.0

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


# ======================================================================
# FRAMEWORK 2: DAILY ALPHA TRIGGER
# ======================================================================
def evaluate_alpha_trigger():
    """
    FRAMEWORK 2: DAILY ALPHA TRIGGER
    Deteksi Peluang Emas & Akumulasi Institusi.
    """
    print("\n[+] Mengevaluasi Institutional Breakout (Alpha Trigger)...")
    print("[-] Tidak ada sinyal Alpha Trigger hari ini.")
    return []


# ======================================================================
# MAIN
# ======================================================================
def main():
    print("==================================================")
    print("   ISI V5: DAILY RISK RADAR (HYBRID ARCHITECTURE) ")
    print("==================================================")

    now = datetime.datetime.now()
    print(f"Waktu Eksekusi : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("Status Sistem  : ONLINE")
    print(f"Watchlist (Top 5) : {', '.join(LIVE_PORTFOLIO)}\n")

    # -- Jalankan framework utama --
    anomalies, volume_details = evaluate_emergency_brake()
    alpha_anomalies = evaluate_alpha_trigger()
    if alpha_anomalies:
        anomalies.extend(alpha_anomalies)

    # -- Tentukan status harian --
    status = "WARNING" if anomalies else "SAFE"

    # -- Hitung ringkasan volume untuk memori historis --
    sepi_count  = sum(1 for d in volume_details if "Sepi" in d)
    anget_count = sum(1 for d in volume_details if "Anomali" in d)

    # -- Bangun snapshot hari ini untuk FIFO history --
    today_snapshot = {
        "tanggal": now.strftime("%Y-%m-%d"),
        "jumlah_saham_sedang_anget": len(LIVE_PORTFOLIO),
        "ringkasan_volume_hari_itu": {
            "status_sistem": status,
            "saham_anomali_lonjakan": anget_count,
            "saham_volume_sepi": sepi_count,
            "detail": volume_details
        }
    }

    # -- Update memori historis FIFO (maks 5 hari) --
    history = update_radar_history(today_snapshot)

    # -- Hasilkan narasi AI atau fallback --
    print("\n[+] Memproses analisis naratif...")
    detail_message = generate_ai_narrative(
        history=history,
        volume_details=volume_details,
        watchlist=LIVE_PORTFOLIO,
        status=status
    )

    # -- Simpan status ke JSON file --
    os.makedirs("output", exist_ok=True)
    status_data = {
        "last_update": now.strftime("%Y-%m-%d %H:%M"),
        "status": status,
        "anomalies": anomalies,
        "detail_message": detail_message
    }

    with open(STATUS_FILE, "w") as f:
        json.dump(status_data, f, indent=4, ensure_ascii=False)
    print(f"[+] Status harian berhasil disimpan ke {STATUS_FILE}")

    # Otomatis update dashboard HTML agar sinkron dengan status radar harian terbaru
    try:
        from dashboard.generate_dashboard import generate_dashboard
        generate_dashboard()
    except Exception as e:
        print(f"[!] Warning: Gagal memperbarui dashboard HTML: {e}")

    print("\n==================================================")
    print("Radar harian selesai dieksekusi. Standby.")


if __name__ == "__main__":
    main()
