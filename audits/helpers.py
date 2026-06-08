# audits/helpers.py
"""Helper utilities for RESEARCH-013 audits.
Provides functions to load monthly returns, calculate performance metrics,
and generate markdown reports.
"""
import csv
import math
from pathlib import Path
from typing import List, Tuple, Dict

def load_monthly_returns(csv_path: Path) -> Tuple[List[str], List[float], List[float]]:
    """Load dates, portfolio returns, and benchmark returns from a CSV.
    Expected columns: date, portfolio_return, benchmark_return.
    Returns three parallel lists.
    """
    dates: List[str] = []
    portfolio: List[float] = []
    benchmark: List[float] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dates.append(row["date"].strip())
            portfolio.append(float(row["portfolio_return"]))
            benchmark.append(float(row["benchmark_return"]))
    return dates, portfolio, benchmark

def mean(data: List[float]) -> float:
    return sum(data) / len(data) if data else 0.0

def std(data: List[float], mean_val: float) -> float:
    if len(data) < 2:
        return 0.0
    variance = sum((x - mean_val) ** 2 for x in data) / (len(data) - 1)
    return math.sqrt(variance)

def calculate_metrics(returns: List[float]) -> Dict[str, float]:
    """Calculate CAGR, annualized return, volatility, Sharpe, max drawdown, win rate.
    Assumes monthly returns.
    """
    n = len(returns)
    years = n / 12.0
    equity = 1.0
    equity_curve: List[float] = []
    drawdowns: List[float] = []
    for r in returns:
        equity *= (1.0 + r)
        equity_curve.append(equity)
        peak = max(equity_curve)
        drawdowns.append((peak - equity) / peak)
    cagr = (equity) ** (1.0 / years) - 1.0 if years > 0 else 0.0
    mean_val = mean(returns)
    ann_ret = mean_val * 12.0
    vol = std(returns, mean_val) * math.sqrt(12.0)
    sharpe = ann_ret / vol if vol > 0 else 0.0
    max_dd = max(drawdowns) if drawdowns else 0.0
    win_rate = sum(1 for r in returns if r > 0) / n if n else 0.0
    return {
        "cagr": cagr,
        "ann_return": ann_ret,
        "volatility": vol,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "win_rate": win_rate,
    }

def calculate_beta_alpha(port_returns: List[float], bench_returns: List[float]) -> Tuple[float, float]:
    """Calculate beta and annualized alpha (CAPM) given portfolio and benchmark returns.
    Returns (beta, alpha_annualized).
    """
    if not port_returns or not bench_returns:
        return 0.0, 0.0
    mean_p = mean(port_returns)
    mean_b = mean(bench_returns)
    cov = sum((p - mean_p) * (b - mean_b) for p, b in zip(port_returns, bench_returns)) / (len(port_returns) - 1)
    var_b = sum((b - mean_b) ** 2 for b in bench_returns) / (len(bench_returns) - 1)
    beta = cov / var_b if var_b > 0 else 0.0
    alpha_monthly = mean_p - beta * mean_b
    alpha_annualized = alpha_monthly * 12.0
    return beta, alpha_annualized
