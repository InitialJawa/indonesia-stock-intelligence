# file: scoring/momentum_score.py

import json
from pathlib import Path
import pandas as pd

INPUT_DIR = Path("database/monthly")
OUTPUT_FILE = Path("output/scores/momentum_ranking.json")

def calculate_percentile(series):
    """
    Menggunakan rank-based percentile bawaan Pandas
    untuk mencegah outlier mendistorsi skor momentum.
    """
    if series.empty:
        return series
    if series.nunique() == 1:
        return pd.Series([100.0] * len(series), index=series.index)
    return series.rank(pct=True) * 100

def calculate_momentum():
    rows = []
    files = sorted(INPUT_DIR.glob("*.csv"))

    for file in files:
        ticker = file.stem
        df = pd.read_csv(file)
        
        # Hapus NA hanya pada kolom price agar tidak tidak sengaja membuang 
        # baris jika data foreign_flow kosong di masa lalu
        if "month_end_price" in df.columns:
            df = df.dropna(subset=["month_end_price"])
        else:
            df = df.dropna()

        if len(df) < 13:
            continue

        latest = len(df) - 1

        return_6m = (
            df.iloc[latest]["month_end_price"] / 
            df.iloc[latest - 6]["month_end_price"] - 1
        )

        return_12m = (
            df.iloc[latest]["month_end_price"] / 
            df.iloc[latest - 12]["month_end_price"] - 1
        )

        # RULE: Injeksi Foreign Flow (Bandar Asing)
        # Cek eksistensi kolom agar skrip tidak crash jika collector V4 belum diperbarui
        foreign_flow_6m = 0
        ff_col = None
        for col in ["net_foreign_buy", "foreign_flow", "net_foreign_flow"]:
            if col in df.columns:
                ff_col = col
                break
        
        if ff_col:
            # Akumulasi arus dana asing selama 6 bulan terakhir
            foreign_flow_6m = df[ff_col].iloc[latest-6:latest+1].sum()

        rows.append({
            "ticker": ticker,
            "return_6m": return_6m,
            "return_12m": return_12m,
            "foreign_flow_6m": foreign_flow_6m
        })

    if not rows:
        print("Warning: Tidak ada data yang cukup untuk menghitung momentum.")
        return

    result = pd.DataFrame(rows)

    # Implementasi Normalisasi Persentil
    result["score_6m"] = calculate_percentile(result["return_6m"])
    result["score_12m"] = calculate_percentile(result["return_12m"])
    result["score_ff"] = calculate_percentile(result["foreign_flow_6m"])

    # Kalkulasi Akhir Momentum dengan Integrasi Asing
    result["momentum"] = (
        result["score_6m"] * 0.35 + 
        result["score_12m"] * 0.35 +
        result["score_ff"] * 0.30
    )

    result = result.sort_values("momentum", ascending=False)
    result = result.round(2)

    output = (
        result[["ticker", "momentum", "return_6m", "return_12m", "foreign_flow_6m"]]
        .to_dict(orient="records")
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=4)

    print(f"Saved -> {OUTPUT_FILE} (PERCENTILE NORMALIZED + FOREIGN FLOW INJECTION)")

if __name__ == "__main__":
    calculate_momentum()