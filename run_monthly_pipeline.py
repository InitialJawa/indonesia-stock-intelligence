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
    "python scoring/quality_score.py",
    "python scoring/growth_score.py",
    "python scoring/value_score.py",
    "python scoring/momentum_score.py",

    # =========================
    # Final Ranking
    # =========================
    "python scoring/final_score_v3.py",

    # =========================
    # Archives & Warehouse
    # =========================
    "python backtesting/archive_current_state.py",
    "python backtesting/archive_fundamentals.py",
    "python backtesting/archive_growth.py",
    "python backtesting/archive_factors.py",

    # =========================
    # Portfolio Rebalance
    # =========================
    "python backtesting/rebalance.py",
    
    # =========================
    # Visual Dashboard
    # =========================
    "python dashboard/generate_dashboard.py"
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