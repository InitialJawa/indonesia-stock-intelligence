# file: run_monthly_pipeline.py

import subprocess

PIPELINE = [
    # =========================
    # Data Collection
    # =========================
    "python -m collectors.fundamentals",
    "python -m collectors.growth",
    "python -m collectors.prices",
    "python -m collectors.historical_foreign_flow",

    # =========================
    # Factor Scores
    # =========================
    "python -m scoring.quality_score",
    "python -m scoring.growth_score",
    "python -m scoring.value_score",
    "python -m scoring.momentum_score",

    # =========================
    # Final Ranking
    # =========================
    "python -m scoring.final_score_v3",

    # =========================
    # Visual Dashboard
    # =========================
    "python scripts/generate_dashboard_v2.py"
]

def run():
    for command in PIPELINE:
        print(f"\nRunning: {command}")
        result = subprocess.run(
            command,
            shell=True
        )
        if result.returncode != 0:
            raise Exception(f"Failed: {command}")

if __name__ == "__main__":
    run()