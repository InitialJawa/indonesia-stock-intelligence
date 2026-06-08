# audits/universe_bias_audit.py
"""Universe Bias Audit.
Compares Config B performance across different universe definitions.
Generates a markdown report with a comparison table.
"""
from pathlib import Path
from .helpers import load_monthly_returns, calculate_metrics
from .config import AUDIT_OUTPUT_DIR, UNIVERSES, UNIVERSE_DIR


def load_universe_returns(universe_key: str) -> tuple:
    """Load portfolio and benchmark returns for a given universe.
    Expects a CSV named `momentum_monthly_returns_<key>.csv` under `database/monthly`.
    If the file does not exist, returns None.
    """
    csv_path = Path("database/monthly") / f"momentum_monthly_returns_{universe_key.lower()}.csv"
    if not csv_path.is_file():
        return None
    return load_monthly_returns(csv_path)


def run_universe_bias_audit():
    report_path = AUDIT_OUTPUT_DIR / "universe_bias_audit.md"
    lines = []
    lines.append("# Universe Bias Audit\n\n")
    lines.append("| Universe | CAGR | Sharpe | Max Drawdown |\n")
    lines.append("|---|---|---|---|\n")
    for key, filename in UNIVERSES.items():
        # Attempt to load returns; fallback to default (IDX30) if missing
        data = load_universe_returns(key)
        if data is None:
            # Skip missing universe with a note
            lines.append(f"| {key} ({filename}) | *data missing* | *data missing* | *data missing* |\n")
            continue
        dates, port_ret, bench_ret = data
        metrics = calculate_metrics(port_ret)
        lines.append(f"| {key} ({filename}) | {metrics['cagr']*100:.2f}% | {metrics['sharpe']:.2f} | {metrics['max_drawdown']*100:.2f}% |\n")
    with open(report_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return {"report": str(report_path)}
