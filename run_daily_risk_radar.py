import json
import os
import datetime
import re
from utils.telegram_notifier import send_telegram_alert
from utils.email_notifier import send_email_alert
from collectors.daily_flow_collector import check_volume_shock

HISTORY_FILE = "output/radar_history.json"
STATUS_FILE  = "output/daily_radar_status.json"
MAX_HISTORY  = 5


def get_sedang_anget_watchlist(top_n=5):
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
        return ["ADRO.JK", "ESSA.JK", "BBRI.JK", "BMRI.JK", "MIKA.JK"]


LIVE_PORTFOLIO = get_sedang_anget_watchlist(5)


def load_radar_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return []


def save_radar_history(history: list):
    os.makedirs("output", exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)


def update_radar_history(today_data: dict):
    history = load_radar_history()
    history.append(today_data)
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
    save_radar_history(history)
    print(f"[+] History diperbarui. Total snapshot tersimpan: {len(history)} hari.")
    return history


# ======================================================================
# RS-V2: RADAR CONTEXT COMPUTATION
# ======================================================================
def compute_radar_context(watchlist_tickers: list, history: list) -> dict:
    """
    Compute market context metrics from scoring data.
    """
    ctx = {
        "production_config": "Config F",
        "top5_avg_score": 0,
        "bot5_avg_score": 0,
        "score_gap": 0,
        "score_gap_5d_change": 0,
        "breadth_above_70": 0,
        "breadth_above_60": 0,
        "breadth_below_40": 0,
        "strongest_factor": "—",
        "strongest_factor_score": 0,
        "weakest_factor": "—",
        "weakest_factor_score": 0,
        "top5_turnover": 0,
        "watchlist_count": len(watchlist_tickers),
    }

    try:
        with open("output/scores/final_ranking_v3.json", "r") as f:
            final_scores = json.load(f)
    except Exception:
        print("[!] Gagal membaca final_ranking_v3.json")
        return ctx

    if not isinstance(final_scores, list) or len(final_scores) < 10:
        return ctx

    total = len(final_scores)
    top5 = final_scores[:5]
    bot5 = final_scores[-5:]

    ctx["top5_avg_score"] = round(sum(t.get('final_score', 0) for t in top5) / 5, 1)
    ctx["bot5_avg_score"] = round(sum(t.get('final_score', 0) for t in bot5) / 5, 1)
    ctx["score_gap"] = round(ctx["top5_avg_score"] - ctx["bot5_avg_score"], 1)

    ctx["breadth_above_70"] = sum(1 for t in final_scores if t.get('final_score', 0) >= 70)
    ctx["breadth_above_60"] = sum(1 for t in final_scores if t.get('final_score', 0) >= 60)
    ctx["breadth_below_40"] = sum(1 for t in final_scores if t.get('final_score', 0) < 40)

    # strongest factor in top5
    factors = ['quality_score', 'growth_score', 'value_score', 'momentum']
    factor_labels = {'quality_score': 'Quality', 'growth_score': 'Growth', 'value_score': 'Value', 'momentum': 'Momentum'}
    factor_avgs = {}
    for fk in factors:
        vals = [t.get(fk, 0) or 0 for t in top5]
        factor_avgs[fk] = sum(vals) / len(vals) if vals else 0
    strongest = max(factor_avgs, key=factor_avgs.get)
    weakest_bot = min(factor_avgs, key=factor_avgs.get)
    ctx["strongest_factor"] = factor_labels[strongest]
    ctx["strongest_factor_score"] = round(factor_avgs[strongest], 1)
    ctx["weakest_factor"] = factor_labels[weakest_bot]
    ctx["weakest_factor_score"] = round(factor_avgs[weakest_bot], 1)

    # top5_turnover: compare today's watchlist with oldest history entry's tickers
    try:
        today_top5_tickers = set(watchlist_tickers)
        # extract tickers from oldest history entry's volume detail
        if history:
            oldest_detail = history[0].get("ringkasan_volume_hari_itu", {}).get("detail", [])
            prev_tickers = set()
            for line in oldest_detail:
                m = re.match(r"([A-Z]+\.JK)", line)
                if m:
                    prev_tickers.add(m.group(1))
            if prev_tickers:
                overlap = len(today_top5_tickers & prev_tickers)
                ctx["top5_turnover"] = 5 - overlap
    except Exception:
        pass

    # score_gap_5d_change: compare today's gap with oldest history
    # We can't directly compute old gap from history (it doesn't store scores)
    # So we approximate from breadth change in volume detail
    # For now, compute from the change in breadth counts if previous data exists
    # Simplified: estimate from volume health change
    try:
        if len(history) >= 2:
            old_breadth = sum(1 for d in history[0].get("ringkasan_volume_hari_itu", {}).get("detail", []) if "Wajar" in d)
            new_breadth = sum(1 for d in history[-1].get("ringkasan_volume_hari_itu", {}).get("detail", []) if "Wajar" in d)
            ctx["score_gap_5d_change"] = round((new_breadth - old_breadth) * 2, 1)
    except Exception:
        pass

    return ctx


# ======================================================================
# RS-V2: CHIEF RISK OFFICER PROMPT + STRUCTURED OUTPUT
# ======================================================================
def generate_ai_narrative(history: list, volume_details: list, watchlist: list, status: str, radar_context: dict) -> dict:
    """
    Returns a dict with RS-V2 structured fields + detail_message.
    Uses Gemini if API key available, else deterministic fallback.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        try:
            with open("config/settings.json", "r") as f:
                settings = json.load(f)
                api_key = settings.get("gemini", {}).get("api_key", "").strip()
        except Exception:
            pass

    if api_key:
        return _gemini_cro_analysis(api_key, history, volume_details, watchlist, status, radar_context)
    else:
        return _deterministic_cro_analysis(history, volume_details, watchlist, status, radar_context)


def _gemini_cro_analysis(api_key: str, history: list, volume_details: list, watchlist: list, status: str, radar_context: dict) -> dict:
    print("[+] GEMINI_API_KEY terdeteksi. Memanggil Gemini AI (CRO mode)...")
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        prompt = (
            "Kamu adalah Chief Risk Officer (CRO) Indonesia Stock Intelligence.\n\n"
            "Karakter:\n"
            "* sangat skeptis\n"
            "* fokus perlindungan modal\n"
            "* tidak peduli narasi media\n"
            "* hanya peduli probabilitas dan risk/reward\n\n"
            "Tugas utama:\n"
            "Menentukan apakah modal investor harus: ditambah, dipertahankan, dikurangi, atau menunggu.\n\n"
            "JANGAN menjadi komentator pasar.\n"
            "JANGAN memberi opini umum.\n"
            "FOKUS pada keputusan modal.\n\n"
            "Berikut data konteks hari ini:\n"
            f"{json.dumps(radar_context, indent=2, ensure_ascii=False)}\n\n"
            f"Volume detail:\n{chr(10).join(volume_details) if volume_details else 'Tidak ada data volume.'}\n\n"
            f"5 hari terakhir:\n{json.dumps(history, indent=2, ensure_ascii=False)}\n\n"
            "WAJIB keluarkan JSON SAJA (tanpa markdown, tanpa penjelasan tambahan) dengan format berikut:\n"
            '{\n'
            '  "status": "SAFE",\n'
            '  "market_health": 72,\n'
            '  "opportunity": 78,\n'
            '  "risk": 34,\n'
            '  "confidence": 69,\n'
            '  "capital_deployment": 70,\n'
            '  "action": "ACCUMULATE",\n'
            '  "rationale": "..."\n'
            '}\n\n'
            "Status: SAFE / WARNING / DANGER\n"
            "Action: BUY / ACCUMULATE / HOLD / WAIT / REDUCE\n"
            "Semua range 0-100 (kecuali status/action string, capital_deployment 0-100).\n"
            "Rationale: maksimal 120 kata, bahasa Indonesia, jelaskan score gap, breadth, volume, faktor dominan, perubahan dibanding 5 hari terakhir."
        )

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        response = model.generate_content(prompt)
        raw = response.text.strip()
        print(f"[+] Respon AI diterima ({len(raw)} karakter).")

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

        parsed = json.loads(raw)
        expected_keys = {"status", "market_health", "opportunity", "risk", "confidence", "capital_deployment", "action", "rationale"}
        missing = expected_keys - set(parsed.keys())
        if missing:
            raise ValueError(f"Missing fields: {missing}")

        parsed["detail_message"] = parsed["rationale"]
        print(f"[+] Narasi CRO berhasil: action={parsed['action']}, health={parsed['market_health']}")
        return parsed

    except Exception as e:
        import traceback
        print(f"[GEMINI ERROR] {type(e).__name__}: {e}")
        traceback.print_exc()
        return _deterministic_cro_analysis(history, volume_details, watchlist, status, radar_context)


def _deterministic_cro_analysis(history: list, volume_details: list, watchlist: list, status: str, radar_context: dict) -> dict:
    """
    Deterministic fallback — computes scores from radar_context data.
    """
    print("[!] Mode deterministik — menghitung skor dari data konteks.")

    ctx = radar_context
    gap = ctx.get("score_gap", 0)
    b70 = ctx.get("breadth_above_70", 0)
    b60 = ctx.get("breadth_above_60", 0)
    b40 = ctx.get("breadth_below_40", 0)
    top5_avg = ctx.get("top5_avg_score", 50)
    turnover = ctx.get("top5_turnover", 0)
    vol_sepi = sum(1 for d in volume_details if "Sepi" in d)
    vol_anomali = sum(1 for d in volume_details if "Anomali" in d or "Lonjakan" in d)
    total_watch = len(volume_details) if volume_details else 1
    vol_healthy = total_watch - vol_sepi - vol_anomali

    market_health = min(100, max(0, int(
        50
        + gap * 0.4
        + b70 * 2
        - b40 * 1.5
        + vol_healthy * 3
    )))

    opportunity = min(100, max(0, int(
        40
        + top5_avg * 0.3
        + b60 * 2
        - turnover * 5
    )))

    risk = min(100, max(0, int(
        20
        + vol_sepi * 8
        + vol_anomali * 6
        + turnover * 8
        - (70 - top5_avg) * 0.5 if top5_avg < 70 else 0
    )))

    if gap < 15:
        risk = min(100, risk + 10)
    if b40 > b70:
        market_health = max(0, market_health - 15)

    confidence = min(100, max(0, int(
        50
        + (market_health - risk) * 0.5
        + opportunity * 0.1
    )))

    capital_deployment = min(100, max(0, int(
        market_health * 0.35
        + opportunity * 0.35
        - risk * 0.2
        + confidence * 0.1
    )))

    if capital_deployment >= 75:
        action = "ACCUMULATE"
    elif capital_deployment >= 55:
        action = "HOLD"
    elif capital_deployment >= 30:
        action = "WAIT"
    else:
        action = "REDUCE"

    if status == "WARNING":
        market_health = max(0, market_health - 15)
        if action in ("ACCUMULATE", "HOLD"):
            action = "WAIT"

    # Build rationale
    parts = []
    if gap > 20:
        parts.append(f"Score gap {gap} poin menunjukkan pemisahan kualitas yang jelas antara top5 dan bottom5.")
    elif gap > 10:
        parts.append(f"Score gap {gap} poin — pemisahan moderat, banyak saham setara di middle.")
    else:
        parts.append(f"Score gap hanya {gap} poin — pasar sangat homogen, sulit membedakan kualitas.")

    strong = ctx.get("strongest_factor", "—")
    weak = ctx.get("weakest_factor", "—")
    parts.append(f"Faktor dominan: {strong} ({ctx.get('strongest_factor_score', 0)}). Faktor terlemah: {weak} ({ctx.get('weakest_factor_score', 0)}).")

    if b70 >= 5:
        parts.append(f"Breadth kuat ({b70} saham >=70).")
    elif b70 > 0:
        parts.append(f"Breadth terbatas ({b70} saham >=70).")
    else:
        parts.append("Tidak ada saham dengan skor >=70 — breadth lemah.")

    if vol_sepi > 0:
        parts.append(f"{vol_sepi} dari {total_watch} saham watchlist volume sepi — likuiditas rendah.")
    if turnover > 0:
        parts.append(f"Top5 turnover {turnover} — rotasi tinggi, stabilitas rendah.")

    rationale = " ".join(parts)
    if len(rationale) > 600:
        rationale = rationale[:597] + "..."

    overall_status = "DANGER" if risk >= 70 else "WARNING" if risk >= 45 or status == "WARNING" else "SAFE"

    return {
        "status": overall_status,
        "market_health": market_health,
        "opportunity": opportunity,
        "risk": risk,
        "confidence": confidence,
        "capital_deployment": capital_deployment,
        "action": action,
        "rationale": rationale,
        "detail_message": rationale
    }


# ======================================================================
# FRAMEWORK 1: DAILY EMERGENCY BRAKE
# ======================================================================
def evaluate_emergency_brake():
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
                vol_status = "Volume Lonjakan"
            elif ratio < 1.0:
                vol_status = "Sepi"
            else:
                vol_status = "Wajar"

            volume_details.append(f"{ticker}: Volume {ratio:.1f}x ({vol_status})")

            if res["is_volume_shock"] and res["price_change_pct"] <= -2.0:
                msg = (
                    f"\U0001f6a8 <b>{ticker}</b> mengalami <b>DISTRIBUSI MASIF</b>!\n"
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
    print("\n[+] Mengevaluasi Institutional Breakout (Alpha Trigger)...")
    print("[-] Tidak ada sinyal Alpha Trigger hari ini.")
    return []


def main():
    print("==================================================")
    print("   RS-V2: CHIEF RISK OFFICER RADAR")
    print("==================================================")

    now = datetime.datetime.now()
    print(f"Waktu Eksekusi : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Watchlist (Top 5) : {', '.join(LIVE_PORTFOLIO)}\n")

    anomalies, volume_details = evaluate_emergency_brake()
    alpha_anomalies = evaluate_alpha_trigger()
    if alpha_anomalies:
        anomalies.extend(alpha_anomalies)

    status = "WARNING" if anomalies else "SAFE"

    sepi_count  = sum(1 for d in volume_details if "Sepi" in d)
    anget_count = sum(1 for d in volume_details if "Anomali" in d)

    today_snapshot = {
        "tanggal": now.strftime("%Y-%m-%d"),
        "jumlah_saham_sedang_anget": len(LIVE_PORTFOLIO),
        "watchlist_tickers": list(LIVE_PORTFOLIO),
        "ringkasan_volume_hari_itu": {
            "status_sistem": status,
            "saham_anomali_lonjakan": anget_count,
            "saham_volume_sepi": sepi_count,
            "detail": volume_details
        }
    }

    history = update_radar_history(today_snapshot)

    print("\n[+] Menghitung konteks radar (RS-V2)...")
    radar_context = compute_radar_context(LIVE_PORTFOLIO, history)
    for k, v in radar_context.items():
        print(f"    {k}: {v}")

    print("\n[+] Memproses analisis CRO...")
    cro_result = generate_ai_narrative(
        history=history,
        volume_details=volume_details,
        watchlist=LIVE_PORTFOLIO,
        status=status,
        radar_context=radar_context
    )

    os.makedirs("output", exist_ok=True)

    status_data = {
        "last_update": now.strftime("%Y-%m-%d %H:%M"),
    }
    status_data.update(cro_result)
    status_data["status"] = cro_result.get("status", status)
    status_data["anomalies"] = anomalies
    status_data["radar_context"] = radar_context
    status_data["volume_details"] = volume_details

    with open(STATUS_FILE, "w") as f:
        json.dump(status_data, f, indent=4, ensure_ascii=False)
    print(f"[+] Status harian berhasil disimpan ke {STATUS_FILE}")

    try:
        import subprocess
        subprocess.run(["python", "scripts/generate_dashboard_v3.py"], check=True)
    except Exception as e:
        print(f"[!] Warning: Gagal memperbarui dashboard HTML: {e}")

    print("\n==================================================")
    print("Radar harian selesai dieksekusi. Standby.")


if __name__ == "__main__":
    main()
