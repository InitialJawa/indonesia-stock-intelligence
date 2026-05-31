# file: utils/telegram_notifier.py

import json
import urllib.request
import urllib.parse
from pathlib import Path

CONFIG_PATH = Path("config/settings.json")

def send_telegram_alert(message: str, alert_type: str = "INFO"):
    """
    Mengirimkan pesan notifikasi ke Telegram User.
    alert_type: "EMERGENCY", "ALPHA", "INFO"
    """
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            bot_token = config.get("telegram", {}).get("bot_token", "")
            chat_id = config.get("telegram", {}).get("chat_id", "")
    except FileNotFoundError:
        print("Error: config/settings.json tidak ditemukan.")
        return False

    if not bot_token or not chat_id or bot_token == "YOUR_BOT_TOKEN_HERE":
        print("Warning: Telegram Bot Token / Chat ID belum disetel di config/settings.json. Pesan dilewati.")
        return False

    # Formatting emoji berdasarkan tipe alert
    prefix = "ℹ️ [INFO]"
    if alert_type == "EMERGENCY":
        prefix = "🚨 [MARKET CRASH RISK / EMERGENCY BRAKE]"
    elif alert_type == "ALPHA":
        prefix = "⚡ [DAILY ALPHA TRIGGER / PELUANG EMAS]"

    full_message = f"{prefix}\n\n{message}"

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": full_message,
        "parse_mode": "HTML"
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            if res_data.get("ok"):
                print(f"Notifikasi {alert_type} berhasil dikirim ke Telegram.")
                return True
            else:
                print(f"Gagal mengirim Telegram: {res_data}")
                return False
    except Exception as e:
        print(f"Koneksi ke API Telegram gagal: {e}")
        return False

if __name__ == "__main__":
    send_telegram_alert(
        "Mesin Indonesia Stock Intelligence V5 berhasil terkoneksi ke modul Telegram.", 
        "INFO"
    )