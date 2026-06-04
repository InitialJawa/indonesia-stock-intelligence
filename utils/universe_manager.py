# file: utils/universe_manager.py

import json
from pathlib import Path

def get_active_universe(date_string):
    """
    Mengembalikan set ticker konstituen IDX30 yang aktif pada tanggal/bulan tertentu.
    Mendukung format tanggal YYYY-MM-DD atau YYYY-MM.
    Menerapkan fallback ke file bulan terdekat sebelumnya jika file bulan tersebut tidak ada.
    """
    month_key = date_string[:7]
    base_dir = Path(__file__).resolve().parent.parent
    univ_dir = base_dir / "database" / "historical_universe"
    
    if not univ_dir.exists():
        # Fallback ke universe statis jika dir tidak ditemukan
        univ_file = base_dir / "config" / "universe.json"
        if univ_file.exists():
            with open(univ_file, "r", encoding="utf-8") as f:
                return set(json.load(f))
        return set()
        
    univ_files = sorted(list(univ_dir.glob("*.json")))
    if not univ_files:
        # Fallback ke universe.json
        univ_file = base_dir / "config" / "universe.json"
        if univ_file.exists():
            with open(univ_file, "r", encoding="utf-8") as f:
                return set(json.load(f))
        return set()
        
    selected_file = None
    for file in univ_files:
        file_month = file.stem
        if file_month <= month_key:
            selected_file = file
        else:
            break
            
    if selected_file is None:
        selected_file = univ_files[0]
        
    with open(selected_file, "r", encoding="utf-8") as f:
        return set(json.load(f))
