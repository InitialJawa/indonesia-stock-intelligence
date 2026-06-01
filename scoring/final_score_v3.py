import json
import os
import pandas as pd

from pathlib import Path

# Load weights from config if possible
CONFIG_PATH = Path("config/scoring_weights.json")
if CONFIG_PATH.exists():
    try:
        with open(CONFIG_PATH, "r") as f:
            weights = json.load(f)
        QUALITY_WEIGHT = weights.get("quality", 0.25)
        GROWTH_WEIGHT = weights.get("growth", 0.30)
        VALUE_WEIGHT = weights.get("value", 0.10)
        MOMENTUM_WEIGHT = weights.get("momentum", 0.35)
    except Exception as e:
        print(f"[WARNING] Gagal memuat config/scoring_weights.json: {e}. Menggunakan default weights.")
        QUALITY_WEIGHT = 0.25
        GROWTH_WEIGHT = 0.30
        VALUE_WEIGHT = 0.10
        MOMENTUM_WEIGHT = 0.35
else:
    QUALITY_WEIGHT = 0.25
    GROWTH_WEIGHT = 0.30
    VALUE_WEIGHT = 0.10
    MOMENTUM_WEIGHT = 0.35




def load_json(path):
    with open(path, "r") as f:
        return pd.DataFrame(json.load(f))


def main():
    try:
        quality = load_json("output/scores/quality_ranking.json")[["ticker", "quality_score"]]
        growth = load_json("output/scores/growth_ranking.json")[["ticker", "growth_score"]]
        value = load_json("output/scores/value_ranking.json")[["ticker", "value_score"]]
        momentum = load_json("output/scores/momentum_ranking.json")[["ticker", "momentum"]]
    except FileNotFoundError as e:
        print(f"[ERROR] File input tidak ditemukan: {e}")
        print("[ERROR] Pastikan scoring layer sudah dijalankan sebelum final_score_v3.py")
        raise

    df = (
        quality
        .merge(growth, on="ticker")
        .merge(value, on="ticker")
        .merge(momentum, on="ticker")
    )

    df["final_score"] = (
        df["quality_score"] * QUALITY_WEIGHT
        + df["growth_score"] * GROWTH_WEIGHT
        + df["value_score"] * VALUE_WEIGHT
        + df["momentum"] * MOMENTUM_WEIGHT
    )

    df = df.sort_values("final_score", ascending=False)

    output = df.round(2).to_dict(orient="records")

    os.makedirs("output/scores", exist_ok=True)
    with open("output/scores/final_ranking_v3.json", "w") as f:
        json.dump(output, f, indent=4)

    print("Saved -> output/scores/final_ranking_v3.json")
    print("\n=== TOP 10 V3 ===\n")

    for _, row in df.head(10).iterrows():
        print(f"{row['ticker']:<10}{row['final_score']:.2f}")


if __name__ == "__main__":
    main()