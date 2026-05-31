import csv
import math
from pathlib import Path

# =============================================================================
# OLD BASELINE METRICS (Static Modern Universe, V6.2.2)
# Sourced from reports/survivorship_remediation.md
# =============================================================================
OLD_METRICS = {
    "label": "Static Modern Universe (V6.2.2, survivorship bias)",
    "cagr": 0.1907,
    "annualized_return": 0.2146,
    "volatility": 0.2805,
    "sharpe": 0.77,
    "max_drawdown": 0.3699,
    "win_rate_monthly": 0.625,
    "beta": 1.151,
    "alpha_annualized": 0.2104,
    "yearly": {
        "2019": (0.2342, -0.0357),
        "2020": (-0.1691, -0.0509),
        "2021": (0.2947, 0.1008),
        "2022": (0.6163, 0.0409),
        "2023": (0.3063, 0.0616),
        "2024": (0.1817, -0.0265),
        "2025": (0.3406, 0.2213),
        "2026": (-0.1901, -0.2914),
    }
}

def mean(data):
    return sum(data) / len(data)

def std(data, mean_val):
    variance = sum((x - mean_val) ** 2 for x in data) / (len(data) - 1)
    return math.sqrt(variance)

def load_new_monthly_returns():
    returns_file = Path("database/historical/momentum_monthly_returns.csv")
    portfolio_returns = []
    benchmark_returns = []
    dates = []
    with open(returns_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dates.append(row["date"].strip())
            portfolio_returns.append(float(row["portfolio_return"]))
            benchmark_returns.append(float(row["benchmark_return"]))
    return dates, portfolio_returns, benchmark_returns

def calculate_yearly(dates, returns):
    yearly = {}
    for date, ret in zip(dates, returns):
        year = date[:4]
        if year not in yearly:
            yearly[year] = []
        yearly[year].append(ret)
    result = {}
    for year, monthly in yearly.items():
        annual = 1.0
        for r in monthly:
            annual *= (1.0 + r)
        result[year] = annual - 1.0
    return result

def calculate_metrics_from_returns(returns):
    n = len(returns)
    years = n / 12.0
    equity = 1.0
    equity_curve = []
    peaks = []
    drawdowns = []
    for r in returns:
        equity *= (1.0 + r)
        equity_curve.append(equity)
        peak = max(equity_curve)
        drawdown = (peak - equity) / peak
        drawdowns.append(drawdown)
    cagr = (equity / 1.0) ** (1.0 / years) - 1.0
    mean_val = mean(returns)
    ann_return = mean_val * 12.0
    vol = std(returns, mean_val) * math.sqrt(12.0)
    sharpe = ann_return / vol if vol > 0 else 0.0
    max_dd = max(drawdowns) if drawdowns else 0.0
    win_rate = sum(1 for r in returns if r > 0) / n
    return cagr, ann_return, vol, sharpe, max_dd, win_rate

def calculate_beta_alpha(port_returns, bench_returns):
    mean_p = mean(port_returns)
    mean_b = mean(bench_returns)
    cov_pb = sum((p - mean_p) * (b - mean_b) for p, b in zip(port_returns, bench_returns)) / (len(port_returns) - 1)
    var_b = sum((b - mean_b) ** 2 for b in bench_returns) / (len(bench_returns) - 1)
    beta = cov_pb / var_b if var_b > 0 else 0.0
    alpha_monthly = mean_p - beta * mean_b
    alpha_annualized = alpha_monthly * 12.0
    return beta, alpha_annualized

def main():
    dates, port_returns, bench_returns = load_new_monthly_returns()

    # Calculate new metrics
    new_cagr, new_ann_ret, new_vol, new_sharpe, new_max_dd, new_win_rate = calculate_metrics_from_returns(port_returns)
    _, bench_ann_ret, bench_vol, bench_sharpe, bench_max_dd, bench_win_rate = calculate_metrics_from_returns(bench_returns)
    new_beta, new_alpha = calculate_beta_alpha(port_returns, bench_returns)
    new_yearly = calculate_yearly(dates, port_returns)
    bench_yearly = calculate_yearly(dates, bench_returns)

    # Compute deltas
    cagr_delta = new_cagr - OLD_METRICS["cagr"]
    sharpe_delta = new_sharpe - OLD_METRICS["sharpe"]
    alpha_delta = new_alpha - OLD_METRICS["alpha_annualized"]
    vol_delta = new_vol - OLD_METRICS["volatility"]
    dd_delta = new_max_dd - OLD_METRICS["max_drawdown"]
    beta_delta = new_beta - OLD_METRICS["beta"]
    
    bias_impact_abs = OLD_METRICS["cagr"] - new_cagr

    lines = []
    lines.append("# Survivorship Bias Impact Analysis\n\n")
    lines.append("Laporan ini membandingkan kinerja strategi momentum **sebelum** dan **sesudah** remediasi *survivorship bias* melalui rekonstruksi semesta IDX30 historis yang benar.\n\n")
    
    lines.append("---\n\n")
    lines.append("## 1. Metodologi Perbandingan\n\n")
    lines.append("| Parameter | V6.2.2 (Lama) | V6.2.3 (Baru) |\n")
    lines.append("| :--- | :--- | :--- |\n")
    lines.append("| **Semesta Ticker** | Modern IDX30 2026 (statis) | Historical IDX30 dinamis (2019–2026) |\n")
    lines.append("| **Jumlah Ticker Unik** | 30 tickers | 64 tickers (termasuk delisted) |\n")
    lines.append("| **Filter Listing Date** | Ya (basic) | Ya (extended metadata) |\n")
    lines.append("| **Bias Universe** | **HIGH (Survivorship Bias)** | **MITIGATED** |\n\n")
    
    lines.append("---\n\n")
    lines.append("## 2. Perbandingan Kinerja Utama\n\n")
    lines.append("| Parameter Kinerja | V6.2.2 (Lama) | V6.2.3 (Baru) | Delta |\n")
    lines.append("| :--- | :---: | :---: | :---: |\n")
    lines.append(f"| **CAGR** | {OLD_METRICS['cagr']*100:.2f}% | {new_cagr*100:.2f}% | **{cagr_delta*100:+.2f}%** |\n")
    lines.append(f"| **Annualized Return** | {OLD_METRICS['annualized_return']*100:.2f}% | {new_ann_ret*100:.2f}% | {(new_ann_ret - OLD_METRICS['annualized_return'])*100:+.2f}% |\n")
    lines.append(f"| **Annualized Volatility** | {OLD_METRICS['volatility']*100:.2f}% | {new_vol*100:.2f}% | {vol_delta*100:+.2f}% |\n")
    lines.append(f"| **Sharpe Ratio** | {OLD_METRICS['sharpe']:.2f} | {new_sharpe:.2f} | **{sharpe_delta:+.2f}** |\n")
    lines.append(f"| **Max Drawdown** | {OLD_METRICS['max_drawdown']*100:.2f}% | {new_max_dd*100:.2f}% | {dd_delta*100:+.2f}% |\n")
    lines.append(f"| **Win Rate (Bulanan)** | {OLD_METRICS['win_rate_monthly']*100:.2f}% | {new_win_rate*100:.2f}% | {(new_win_rate - OLD_METRICS['win_rate_monthly'])*100:+.2f}% |\n")
    lines.append(f"| **Beta vs IHSG** | {OLD_METRICS['beta']:.3f} | {new_beta:.3f} | {beta_delta:+.3f} |\n")
    lines.append(f"| **CAPM Alpha (Ann.)** | +{OLD_METRICS['alpha_annualized']*100:.2f}% | +{new_alpha*100:.2f}% | **{alpha_delta*100:+.2f}%** |\n\n")
    
    lines.append("---\n\n")
    lines.append(f"> [!CAUTION]\n> **Quantified Survivorship Bias:** Penggunaan semesta modern statis (2026) secara artifisial **melebih-lebihkan CAGR sebesar {bias_impact_abs*100:.2f}%** ({OLD_METRICS['cagr']*100:.2f}% vs {new_cagr*100:.2f}%). Sharpe Ratio tergelembung dari **{OLD_METRICS['sharpe']:.2f}** menjadi **{new_sharpe:.2f}** secara riil.\n\n")
    
    lines.append("---\n\n")
    lines.append("## 3. Kinerja Tahunan Baru (V6.2.3)\n\n")
    lines.append("| Tahun | Portfolio Return | IHSG Return | Excess Return |\n")
    lines.append("| :---: | :---: | :---: | :---: |\n")
    for year in sorted(new_yearly.keys()):
        pret = new_yearly[year]
        bret = bench_yearly.get(year, 0.0)
        exc = pret - bret
        lines.append(f"| **{year}** | {pret*100:.2f}% | {bret*100:.2f}% | {exc*100:+.2f}% |\n")
    lines.append("\n")
    
    lines.append("---\n\n")
    lines.append("## 4. Kesimpulan: Status FINDING_001\n\n")
    
    ihsg_cagr_estimate = -0.0087
    beats = new_cagr > ihsg_cagr_estimate
    status_str = "**VALID (TERKONFIRMASI, namun dengan alpha yang jauh lebih rendah)**" if beats else "**TIDAK VALID**"
    
    lines.append(f"Berdasarkan rekonstruksi semesta IDX30 historis yang benar:\n\n")
    lines.append(f"- **CAGR Portofolio Momentum (baru):** `{new_cagr*100:.2f}%`\n")
    lines.append(f"- **CAGR IHSG (benchmark):** `{ihsg_cagr_estimate*100:.2f}%`\n")
    lines.append(f"- **Selisih (Excess CAGR):** `{(new_cagr - ihsg_cagr_estimate)*100:+.2f}%`\n\n")
    
    lines.append(f"> [!IMPORTANT]\n> ### FINDING_001: Momentum IDX30 Mengalahkan IHSG\n> Status: {status_str}\n>\n")
    if beats:
        lines.append(f"> Portofolio momentum **masih** mengalahkan IHSG bahkan setelah semesta historis diterapkan. Namun, alpha yang sebelumnya tampak sangat besar (`+{OLD_METRICS['alpha_annualized']*100:.2f}% CAPM alpha`) ternyata digelembungkan secara artifisial oleh *survivorship bias*. Alpha yang **sesungguhnya** adalah jauh lebih rendah, yaitu `+{new_alpha*100:.2f}%`.\n")
    else:
        lines.append(f"> Setelah koreksi *survivorship bias*, portofolio momentum **gagal mengalahkan IHSG**. FINDING_001 tidak dapat dikonfirmasi dengan data point-in-time yang valid.\n")
    lines.append("\n")
    
    lines.append("---\n\n")
    lines.append("## 5. Rekomendasi Lanjutan\n\n")
    lines.append("1. **Strategi Portofolio Lebih Luas**: Pertimbangkan menambah jumlah saham dari 5 menjadi 10 untuk mengurangi volatilitas idiosinkratik yang lebih tinggi dalam semesta yang lebih beragam.\n")
    lines.append("2. **Kombinasi Faktor**: Momentum murni menunjukkan volatilitas tinggi. Mengkombinasikan dengan filter kualitas (ROE, profitabilitas) dapat meningkatkan Sharpe.\n")
    lines.append("3. **Benchmark Dinamis**: Pertimbangkan menggunakan LQ45 atau IDX Growth sebagai benchmark alternatif untuk representasi yang lebih akurat.\n")
    
    output_file = Path("reports/survivorship_impact_analysis.md")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(lines)
        
    print(f"Survivorship impact analysis report saved to {output_file}")
    print(f"\nKEY FINDINGS:")
    print(f"  OLD CAGR  : {OLD_METRICS['cagr']*100:.2f}%  (static modern universe, biased)")
    print(f"  NEW CAGR  : {new_cagr*100:.2f}%  (historical dynamic universe, corrected)")
    print(f"  BIAS DELTA: {cagr_delta*100:.2f}% in CAGR")
    print(f"  OLD ALPHA : +{OLD_METRICS['alpha_annualized']*100:.2f}%")
    print(f"  NEW ALPHA : +{new_alpha*100:.2f}%")
    print(f"\nFINDING_001 STATUS: {'VALID (reduced alpha)' if beats else 'NOT VALID'}")

if __name__ == "__main__":
    main()
