# file: run_monthly_pipeline.py

import subprocess

PIPELINE = [
    # =========================
    # Data Collection
    # =========================
    "python -m collectors.fundamentals",
    "python -m collectors.growth",
    "python -m collectors.prices",

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
    # Archives & Warehouse
    # =========================
    "python -m backtesting.archive_current_state",
    "python -m backtesting.archive_fundamentals",
    "python -m backtesting.archive_growth",
    "python -m backtesting.archive_factors",

    # =========================
    # Portfolio Rebalance
    # =========================
    "python -m backtesting.rebalance",

    # =========================
    # Visual Dashboard
    # =========================
    "python -m dashboard.generate_dashboard"
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