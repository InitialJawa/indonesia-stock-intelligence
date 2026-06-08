# audits/config.py
"""Configuration for RESEARCH-013 audit suite.
Defines data paths and parameters used across audit modules.
"""
from pathlib import Path

# Base project root
PROJECT_ROOT = Path(__file__).parents[2]

# Data directories
DATABASE_DIR = PROJECT_ROOT / "database"
HISTORICAL_DIR = DATABASE_DIR / "historical"
MONTHLY_DIR = DATABASE_DIR / "monthly"
UNIVERSE_DIR = PROJECT_ROOT / "universe"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Common CSV files
MOMENTUM_RETURNS_CSV = MONTHLY_DIR / "momentum_monthly_returns.csv"

# Audit output location
AUDIT_OUTPUT_DIR = REPORTS_DIR / "RESEARCH-013"
AUDIT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Default parameters
DEFAULT_REBALANCE_FREQUENCY = "monthly"  # options: monthly, quarterly, semiannual

# Universe definitions (filenames expected in `universe/`)
UNIVERSES = {
    "A": "idx30.json",   # Current IDX30 (dynamic historical)
    "B": "idx80.json",   # IDX80 (to be added if exists)
    "C": "all_liquid.json",  # All liquid stocks
    "D": "random_large_cap.json",  # Random large-cap subset
}

# Factor files (placeholder paths – to be provided if available)
FACTOR_FILES = {
    "momentum": MONTHLY_DIR / "factor_momentum.csv",
    "growth": MONTHLY_DIR / "factor_growth.csv",
    "quality": MONTHLY_DIR / "factor_quality.csv",
    "value": MONTHLY_DIR / "factor_value.csv",
}
