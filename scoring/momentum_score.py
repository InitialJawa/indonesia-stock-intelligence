# file: scoring/momentum_score.py

import json
from pathlib import Path
import pandas as pd
from scoring.utils import percentile_normalize

INPUT_DIR = Path("database/monthly")
BENCHMARK_FILE = Path("benchmarks/ihsg.csv")
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
    # Load IHSG benchmark prices
    if not BENCHMARK_FILE.exists():
        print(f"Warning: Benchmark file not found at {BENCHMARK_FILE}. Defaulting IHSG returns to 0.")
        ihsg = None
    else:
        try:
            ihsg_df = pd.read_csv(BENCHMARK_FILE)
            date_col = next((c for c in ihsg_df.columns if c.lower() in ["date", "tanggal"]), ihsg_df.columns[0])
            price_col = next((c for c in ihsg_df.columns if c.lower() in ["close", "adj close", "price"]), ihsg_df.columns[1])
            ihsg_df[date_col] = pd.to_datetime(ihsg_df[date_col])
            ihsg = ihsg_df.set_index(date_col).sort_index()[price_col].astype(float)
        except Exception as e:
            print(f"Warning: Failed to load IHSG: {e}. Defaulting IHSG returns to 0.")
            ihsg = None

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

        # Calculate IHSG return for the same 6-month period
        return_ihsg_6m = 0.0
        if ihsg is not None:
            try:
                date_latest = pd.to_datetime(df.iloc[latest]["Date"])
                date_6m_ago = pd.to_datetime(df.iloc[latest - 6]["Date"])
                ihsg_latest = ihsg.asof(date_latest)
                ihsg_6m_ago = ihsg.asof(date_6m_ago)
                if not pd.isna(ihsg_latest) and not pd.isna(ihsg_6m_ago) and ihsg_6m_ago > 0:
                    return_ihsg_6m = (ihsg_latest / ihsg_6m_ago) - 1.0
            except Exception as e:
                print(f"Warning: Gagal menghitung return IHSG untuk {ticker}: {e}")

        return_saham_6m = return_6m
        return_IHSG_6m = return_ihsg_6m
        RS_6M_value = return_saham_6m - return_IHSG_6m

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
            "rs_6m": RS_6M_value,
            "return_12m": return_12m,
            "foreign_flow_6m": foreign_flow_6m
        })

    if not rows:
        print("Warning: Tidak ada data yang cukup untuk menghitung momentum.")
        return

    result = pd.DataFrame(rows)

    # Implementasi Normalisasi Persentil Secara Ketat (Menggunakan scoring.utils)
    result["RS_6M_percentile"] = percentile_normalize(result["rs_6m"].tolist())
    result["score_12m"] = calculate_percentile(result["return_12m"])

    # Kalkulasi Akhir Momentum Ekuilibrium Murni (50% RS-6M + 50% Return-12M)
    result["momentum"] = (
        result["RS_6M_percentile"] * 0.50 + 
        result["score_12m"] * 0.50
    )

    result = result.sort_values("momentum", ascending=False)
    result = result.round(2)

    # Rename rs_6m back to return_6m in the output to maintain compatibility with downstream tasks
    output = (
        result[["ticker", "momentum", "rs_6m", "return_12m", "foreign_flow_6m"]]
        .rename(columns={"rs_6m": "return_6m"})
        .to_dict(orient="records")
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=4)

    print(f"Saved -> {OUTPUT_FILE} (RS-6M PERCENTILE NORMALIZED + FOREIGN FLOW INJECTION)")

if __name__ == "__main__":
    calculate_momentum()