# audits/survivorship_audit.py
"""Survivorship Bias Audit (AUDIT-001)

- Loads monthly portfolio & benchmark returns from the historical
  momentum returns CSV (dynamic IDX30 universe).
- Uses the static modern IDX30 metrics defined in `compare_backtests.py`
  as the "Current Method" baseline.
- Calculates CAGR, Sharpe, Alpha, Max Drawdown, and Turnover (approx.
  using average absolute change in monthly returns) for both methods.
- Writes a CSV summary to `research/output/research_013_survivorship_audit.csv`.
- Generates a markdown report in `reports/RESEARCH-013/survivorship_audit.md`.
- Determines the overall difference level and verdict.
"""
import csv
import math
from pathlib import Path
from typing import List, Tuple, Dict

# Import helpers for loading returns & metric calculations
from .helpers import load_monthly_returns, calculate_metrics, calculate_beta_alpha

# Load static metrics from the existing survivorship script
# Re‑use the same values to avoid duplication
STATIC_METRICS = {
    "cagr": 0.1907,
    "sharpe": 0.77,
    "alpha_annualized": 0.2104,
    "max_drawdown": 0.3699,
    # Turnover for static method is unknown – we approximate with 0 (no change)
    "turnover": 0.0,
}

# Paths
MOMENTUM_CSV = Path("database/historical/momentum_monthly_returns.csv")
CSV_OUTPUT = Path("research/output/research_013_survivorship_audit.csv")
MD_OUTPUT = Path("reports/RESEARCH-013/survivorship_audit.md")

def approximate_turnover(returns: List[float]) -> float:
    """Estimate portfolio turnover as the average absolute month‑to‑month change.
    This is a proxy; the real turnover would require holdings, but the change in
    returns correlates with portfolio turnover for the top‑5 equal‑weight
    strategy.
    """
    if len(returns) < 2:
        return 0.0
    diffs = [abs(returns[i] - returns[i - 1]) for i in range(1, len(returns))]
    return sum(diffs) / len(diffs)

def run_audit():
    # Load dynamic (historical) returns
    dates, port_returns, bench_returns = load_monthly_returns(MOMENTUM_CSV)

    # Metrics for Historical Method (dynamic universe)
    hist_metrics = calculate_metrics(port_returns)
    beta, alpha_annual = calculate_beta_alpha(port_returns, bench_returns)
    hist_metrics["alpha_annualized"] = alpha_annual
    hist_metrics["turnover"] = approximate_turnover(port_returns)

    # Current Method uses static metrics (already defined)
    curr_metrics = STATIC_METRICS.copy()

    # Compute percent differences where applicable
    diff = {}
    for key in ["cagr", "sharpe", "alpha_annualized", "max_drawdown", "turnover"]:
        cur = curr_metrics.get(key, 0.0)
        hist = hist_metrics.get(key, 0.0)
        if cur == 0:
            diff[key] = float('inf') if hist != 0 else 0.0
        else:
            diff[key] = (hist - cur) / abs(cur) * 100.0

    # Write CSV
    CSV_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_OUTPUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Current_Method", "Historical_Method", "Difference_%"])
        for key in ["cagr", "sharpe", "alpha_annualized", "max_drawdown", "turnover"]:
            writer.writerow([
                key,
                f"{curr_metrics.get(key, 0.0):.6f}",
                f"{hist_metrics.get(key, 0.0):.6f}",
                f"{diff[key]:.2f}" if diff[key] != float('inf') else "inf",
            ])

    # Determine overall impact level (max absolute percent diff)
    max_abs = max(abs(v) for v in diff.values() if v != float('inf'))
    if max_abs < 10:
        level = "A"
        verdict = "Survivorship bias minimal."
    elif max_abs <= 25:
        level = "B"
        verdict = "Moderate survivorship impact."
    else:
        level = "C"
        verdict = "Material survivorship bias."

    # Write markdown report
    MD_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(MD_OUTPUT, "w", encoding="utf-8") as f:
        f.write("# Survivorship Bias Audit (AUDIT‑001)\n\n")
        f.write("## Comparison of Metrics\n\n")
        f.write("| Metric | Current Method | Historical Method | Difference % |\n")
        f.write("|---|---|---|---|\n")
        for key in ["cagr", "sharpe", "alpha_annualized", "max_drawdown", "turnover"]:
            f.write(f"| {key} | {curr_metrics.get(key,0.0):.4%} | {hist_metrics.get(key,0.0):.4%} | {diff[key]:.2f}% |\n")
        f.write("\n")
        f.write(f"**Overall Impact Level:** {level} – {verdict}\n")
    return {
        "csv": str(CSV_OUTPUT),
        "markdown": str(MD_OUTPUT),
        "level": level,
        "verdict": verdict,
    }

if __name__ == "__main__":
    result = run_audit()
    print("Survivorship audit completed:", result)
