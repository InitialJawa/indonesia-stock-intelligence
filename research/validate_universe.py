import json
from pathlib import Path

CURRENT_UNIVERSE_FILE = Path("universe/idx30.json")
HISTORICAL_DIR = Path("database/historical_universe")
OUTPUT_REPORT = Path("reports/universe_change_analysis.md")

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return set(json.load(f))

def main():
    if not CURRENT_UNIVERSE_FILE.exists():
        print(f"ERROR: Current universe file {CURRENT_UNIVERSE_FILE} not found.")
        return
        
    current_universe = load_json(CURRENT_UNIVERSE_FILE)
    
    # List and sort all historical files
    hist_files = sorted(list(HISTORICAL_DIR.glob("*.json")))
    if not hist_files:
        print(f"ERROR: No historical universe files found in {HISTORICAL_DIR}")
        return
        
    report_lines = []
    report_lines.append("# Universe Change Analysis Report\n")
    report_lines.append("Laporan validasi ini membandingkan **Current Universe (Statis per 2026)** dengan **Historical Universe** untuk mengukur tingkat *survivorship bias*, serta melacak perubahan konstituen dari periode ke periode.\n")
    
    report_lines.append("## 1. Perbandingan: Current Universe vs Historical Universe\n")
    report_lines.append("Tabel berikut menunjukkan seberapa banyak konstituen historis yang **hilang/berbeda** jika kita hanya menggunakan semesta modern statis (2026) untuk pengujian masa lalu.\n")
    report_lines.append("| Periode | Jumlah Ticker | Cocok dengan Modern | Ticker Modern Baru (Belum Masuk/IPO) | Ticker Historis Hilang (Survivorship Bias) | Delta Perubahan |\n")
    report_lines.append("| :---: | :---: | :---: | :--- | :--- | :---: |\n")
    
    for file in hist_files:
        period = file.stem
        hist_universe = load_json(file)
        
        overlap = current_universe.intersection(hist_universe)
        modern_only = current_universe - hist_universe
        hist_only = hist_universe - current_universe
        
        modern_only_str = ", ".join(sorted(modern_only)) if modern_only else "-"
        hist_only_str = ", ".join(sorted(hist_only)) if hist_only else "-"
        
        report_lines.append(f"| **{period}** | {len(hist_universe)} | {len(overlap)} | {modern_only_str} | {hist_only_str} | {len(hist_only)} |\n")
        
    report_lines.append("\n## 2. Perubahan Konstituen Dari Periode ke Periode (Historical Rebalancing)\n")
    report_lines.append("Tabel berikut melacak saham yang masuk dan keluar secara riil pada setiap tanggal evaluasi indeks (rebalancing).\n")
    report_lines.append("| Periode Evaluasi | Saham Masuk (*In*) | Saham Keluar (*Out*) | Jumlah Perubahan |\n")
    report_lines.append("| :---: | :--- | :--- | :---: |\n")
    
    prev_period = None
    prev_universe = None
    
    for file in hist_files:
        period = file.stem
        hist_universe = load_json(file)
        
        if prev_universe is not None:
            added = hist_universe - prev_universe
            removed = prev_universe - hist_universe
            
            added_str = ", ".join(sorted(added)) if added else "-"
            removed_str = ", ".join(sorted(removed)) if removed else "-"
            
            report_lines.append(f"| **{prev_period} &rarr; {period}** | {added_str} | {removed_str} | {len(added)} |\n")
            
        prev_period = period
        prev_universe = hist_universe
        
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        f.writelines(report_lines)
        
    print(f"Validation report successfully written to {OUTPUT_REPORT}")

if __name__ == "__main__":
    main()
