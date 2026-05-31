# file: utils/email_notifier.py

import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

CONFIG_PATH = Path("config/settings.json")

def send_email_alert(message: str, alert_type: str = "INFO"):
    """
    Mengirimkan pesan notifikasi melalui Email (SMTP).
    alert_type: "EMERGENCY", "ALPHA", "INFO"
    """
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            email_cfg = config.get("email", {})
            smtp_server = email_cfg.get("smtp_server", "smtp.gmail.com")
            smtp_port = email_cfg.get("smtp_port", 587)
            sender_email = email_cfg.get("sender_email", "")
            sender_password = email_cfg.get("sender_password", "")
    except FileNotFoundError:
        print("Error: config/settings.json tidak ditemukan.")
        return False

    if not sender_email or sender_email == "your_email@gmail.com" or not sender_password:
        print("Warning: Kredensial Email belum disetel di config/settings.json. Pesan via Email dilewati.")
        return False

    # Menyiapkan Subject berdasarkan tipe alert
    subject = "[ISI V5 INFO] Laporan Sistem Harian"
    if alert_type == "EMERGENCY":
        subject = "🚨 URGENT: [MARKET CRASH RISK / EMERGENCY BRAKE]"
    elif alert_type == "ALPHA":
        subject = "⚡ PELUANG: [DAILY ALPHA TRIGGER / PELUANG EMAS]"

    # Membuat struktur email (Kirim dari Anda, ke Anda sendiri)
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = sender_email  
    msg['Subject'] = subject

    # Body email
    body = f"Sistem Indonesia Stock Intelligence (ISI) V5 memberikan peringatan berikut:\n\n{message}\n\n--\nMesin Radar Otomatis"
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Setup server SMTP dan eksekusi pengiriman
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls() # Mengamankan koneksi (Wajib untuk Gmail)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        print(f"Notifikasi {alert_type} berhasil dikirim via Email.")
        return True
    except Exception as e:
        print(f"Gagal mengirim Email: {e}")
        return False

if __name__ == "__main__":
    send_email_alert(
        "Mesin Indonesia Stock Intelligence V5 berhasil terkoneksi ke modul Email (SMTP).", 
        "INFO"
    )