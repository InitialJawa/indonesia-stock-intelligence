"""
Test script untuk memvalidasi semua file yang sudah difix.
Menguji: syntax, import structure, dan logika dasar.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import ast
import os
import sys
import json

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

PASS = "✅"
FAIL = "❌"
results = []

# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────

def check(name, condition, detail=""):
    status = PASS if condition else FAIL
    msg = f"  {status} {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    results.append(condition)

def syntax_ok(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, str(e)

def has_main_guard(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    return 'if __name__ == "__main__"' in source

def has_function(filepath, func_name):
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            return True
    return False

def has_string(filepath, text):
    with open(filepath, "r", encoding="utf-8") as f:
        return text in f.read()

def load_json_file(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

# ─────────────────────────────────────────────
# TEST 1: SYNTAX CHECK semua file yang diubah
# ─────────────────────────────────────────────
print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 1 — Syntax Check")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

files_to_check = [
    "scoring/final_score_v3.py",
    "run_monthly_pipeline.py",
    "run_daily_risk_radar.py",
    "collectors/prices.py",
    "collectors/daily_flow_collector.py",
    "scoring/utils.py",
    "utils/email_notifier.py",
    "utils/telegram_notifier.py",
    "utils/config_loader.py",
]

for f in files_to_check:
    ok, err = syntax_ok(f)
    check(f, ok, err if not ok else "syntax valid")

# ─────────────────────────────────────────────
# TEST 2: BUG-01 — settings.json tidak ada token
# ─────────────────────────────────────────────
print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 2 — BUG-01: settings.json token aman")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

settings = load_json_file("config/settings.json")
token = settings.get("telegram", {}).get("bot_token", "")
check("Token tidak berisi angka (tidak ada token asli)", not token.startswith("8"), f"token='{token[:10]}...'")
check("Token kosong atau placeholder", token == "" or "YOUR" in token.upper(), f"token='{token}'")

# ─────────────────────────────────────────────
# TEST 3: BUG-02 — final_score_v3.py punya main()
# ─────────────────────────────────────────────
print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 3 — BUG-02: final_score_v3.py struktur")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

check("final_score_v3.py punya fungsi main()", has_function("scoring/final_score_v3.py", "main"))
check("final_score_v3.py punya __main__ guard", has_main_guard("scoring/final_score_v3.py"))
check("final_score_v3.py punya FileNotFoundError handler",
      has_string("scoring/final_score_v3.py", "FileNotFoundError"))

# ─────────────────────────────────────────────
# TEST 4: BUG-03 & BUG-10 — pipeline pakai -m flag
# ─────────────────────────────────────────────
print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 4 — BUG-03 & 10: run_monthly_pipeline.py")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

with open("run_monthly_pipeline.py", "r") as f:
    pipeline_src = f.read()

old_style_calls = [
    "python scoring/",
    "python backtesting/",
    "python dashboard/",
]
for old in old_style_calls:
    check(f"Tidak ada pemanggilan '{old}'", old not in pipeline_src)

new_style_calls = [
    "python -m scoring.quality_score",
    "python -m scoring.growth_score",
    "python -m scoring.value_score",
    "python -m scoring.momentum_score",
    "python -m scoring.final_score_v3",
    "python -m backtesting.rebalance",
    "python -m dashboard.generate_dashboard",
]
for new in new_style_calls:
    check(f"Ada '{new}'", new in pipeline_src)

# ─────────────────────────────────────────────
# TEST 5: BUG-04 — daily_radar.yml punya requests
# ─────────────────────────────────────────────
print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 5 — BUG-04: daily_radar.yml dependencies")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

check("daily_radar.yml install requests",
      has_string(".github/workflows/daily_radar.yml", "requests"))
check("monthly_pipeline.yml ada",
      os.path.exists(".github/workflows/monthly_pipeline.yml"))
check("monthly_pipeline.yml install requests",
      has_string(".github/workflows/monthly_pipeline.yml", "requests"))

# ─────────────────────────────────────────────
# TEST 6: BUG-05 — run_daily_risk_radar.py kirim email
# ─────────────────────────────────────────────
print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 6 — BUG-05: email integration")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

check("run_daily_risk_radar.py import send_email_alert",
      has_string("run_daily_risk_radar.py", "from utils.email_notifier import send_email_alert"))
check("run_daily_risk_radar.py panggil send_email_alert EMERGENCY",
      has_string("run_daily_risk_radar.py", 'send_email_alert(final_message, "EMERGENCY")'))
check("run_daily_risk_radar.py panggil send_email_alert INFO",
      has_string("run_daily_risk_radar.py", 'send_email_alert(safe_msg, "INFO")'))

# ─────────────────────────────────────────────
# TEST 7: BUG-07 — prices.py punya main() & mkdir
# ─────────────────────────────────────────────
print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 7 — BUG-07: collectors/prices.py")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

check("prices.py punya fungsi collect_prices()", has_function("collectors/prices.py", "collect_prices"))
check("prices.py punya __main__ guard", has_main_guard("collectors/prices.py"))
check("prices.py punya mkdir guard", has_string("collectors/prices.py", "mkdir(parents=True, exist_ok=True)"))

# ─────────────────────────────────────────────
# TEST 8: BUG-08 — daily_flow_collector NaN guard
# ─────────────────────────────────────────────
print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 8 — BUG-08: NaN guard")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

check("daily_flow_collector.py punya pd.isna guard",
      has_string("collectors/daily_flow_collector.py", "pd.isna(ma20_volume)"))

# ─────────────────────────────────────────────
# TEST 9: BUG-09 — utils.py pakai 50.0
# ─────────────────────────────────────────────
print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 9 — BUG-09: percentile_normalize logic")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

check("scoring/utils.py memakai 50.0 (bukan 100.0) untuk nilai sama",
      has_string("scoring/utils.py", "return [50.0 for _ in values]"))
# min_max_normalize masih boleh punya 100.0 — yang penting percentile_normalize pakai 50.0
# Verifikasi dengan unit test di TEST 10 di bawah

# ─────────────────────────────────────────────
# TEST 10: Unit test percentile_normalize
# ─────────────────────────────────────────────
print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 10 — Unit Test: scoring/utils.py")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

from scoring.utils import percentile_normalize, min_max_normalize

# Kasus semua nol
result_all_zero = percentile_normalize([0, 0, 0])
check("percentile_normalize([0,0,0]) = [50,50,50]",
      result_all_zero == [50.0, 50.0, 50.0], str(result_all_zero))

# Kasus normal
result_normal = percentile_normalize([10, 20, 30])
check("percentile_normalize([10,20,30]) = [0,50,100]",
      result_normal == [0.0, 50.0, 100.0], str(result_normal))

# Kasus list kosong
result_empty = percentile_normalize([])
check("percentile_normalize([]) = []", result_empty == [], str(result_empty))

# Kasus satu elemen
result_one = percentile_normalize([42])
check("percentile_normalize([42]) = [50.0]", result_one == [50.0], str(result_one))

# min_max_normalize masih bekerja
result_mm = min_max_normalize([0, 50, 100])
check("min_max_normalize([0,50,100]) = [0,50,100]",
      result_mm == [0.0, 50.0, 100.0], str(result_mm))

# ─────────────────────────────────────────────
# TEST 11: BUG-11 — config_loader.py load_universe & load_settings
# ─────────────────────────────────────────────
print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 11 — BUG-11: config_loader.py")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

try:
    from utils.config_loader import load_settings, load_universe
    universe = load_universe()
    check("load_universe() berhasil berjalan", isinstance(universe, list) and len(universe) > 0, f"universe size: {len(universe) if isinstance(universe, list) else 'not a list'}")
    settings = load_settings()
    check("load_settings() berhasil berjalan", isinstance(settings, dict), f"settings type: {type(settings)}")
except Exception as e:
    check("load_universe / load_settings error", False, str(e))


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
total = len(results)
passed = sum(results)
failed = total - passed

print("\n" + "━"*34)
print(f"HASIL: {passed}/{total} test passed")
if failed > 0:
    print(f"       {failed} test GAGAL ⚠️")
else:
    print("       Semua test lulus! Siap push. 🚀")
print("━"*34)

sys.exit(0 if failed == 0 else 1)
