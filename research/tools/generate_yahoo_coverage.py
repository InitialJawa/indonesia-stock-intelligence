import yfinance as yf
import pandas as pd
import os

TICKERS = ["BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "ASII.JK"]

# Metrics definitions (simple availability check)
METRICS = [
    "ROE",
    "DER",
    "Net Margin",
    "Operating Margin",
    "FCF",
    "Revenue Growth",
    "Net Income Growth",
    "PE",
    "PB",
]

# Helper to extract years from a DataFrame (columns are timestamps)
def get_years(df):
    if df.empty:
        return []
    # Columns are Timestamp objects or strings representing dates
    years = []
    for col in df.columns:
        try:
            # yfinance uses Timestamp objects
            year = int(col.year)
        except Exception:
            # fallback for string like '2023-12-31'
            try:
                year = int(str(col)[:4])
            except Exception:
                continue
        years.append(year)
    return sorted(set(years))

# Store per‑ticker data
coverage = {}
for ticker in TICKERS:
    tk = yf.Ticker(ticker)
    inc = tk.financials  # Income statement (annual)
    bal = tk.balance_sheet  # Balance sheet (annual)
    cf = tk.cashflow  # Cash flow (annual)
    inc_years = get_years(inc)
    bal_years = get_years(bal)
    cf_years = get_years(cf)
    # Intersection of years where all three statements exist
    common_years = sorted(set(inc_years) & set(bal_years) & set(cf_years))
    coverage[ticker] = {
        "income_years": inc_years,
        "balance_years": bal_years,
        "cashflow_years": cf_years,
        "common_years": common_years,
    }

# Aggregate metric coverage (use common years as proxy, since all required fields are in those statements)
metric_coverage = {}
for metric in METRICS:
    all_years = []
    for t in coverage.values():
        all_years.extend(t["common_years"])
    if all_years:
        earliest = min(all_years)
        latest = max(all_years)
        coverage_count = len(set(all_years))
    else:
        earliest = latest = None
        coverage_count = 0
    metric_coverage[metric] = {
        "earliest": earliest,
        "latest": latest,
        "count": coverage_count,
    }

# Build markdown report
lines = []
lines.append("# Yahoo Historical Coverage Proof")
lines.append("")
lines.append("## Retrieved Data Summary")
lines.append("| Ticker | Income Years | Balance Years | Cash‑Flow Years | Common Years |")
lines.append("|--------|--------------|---------------|----------------|--------------|")
for tk, data in coverage.items():
    inc_str = ", ".join(map(str, data["income_years"]))
    bal_str = ", ".join(map(str, data["balance_years"]))
    cf_str = ", ".join(map(str, data["cashflow_years"]))
    com_str = ", ".join(map(str, data["common_years"]))
    lines.append(f"| {tk} | {inc_str} | {bal_str} | {cf_str} | {com_str} |")
lines.append("")
lines.append("## Metric Coverage")
lines.append("| Metric | Earliest Year | Latest Year | Coverage (distinct years) |")
lines.append("|--------|--------------|------------|--------------------------|")
for metric, cov in metric_coverage.items():
    ear = cov["earliest"] if cov["earliest"] is not None else "-"
    lat = cov["latest"] if cov["latest"] is not None else "-"
    cnt = cov["count"]
    lines.append(f"| {metric} | {ear} | {lat} | {cnt} |")
lines.append("")
# Verdict logic
if metric_coverage["ROE"]["earliest"] is not None and metric_coverage["ROE"]["earliest"] < 2021:
    verdict = "B. Coverage begins before 2021"
elif metric_coverage["ROE"]["earliest"] == 2021:
    verdict = "A. Coverage begins 2021"
else:
    verdict = "C. Coverage insufficient"
lines.append("## Final Verdict")
lines.append(f"**{verdict}**")
lines.append("")

report_path = os.path.join("reports", "yahoo_historical_coverage_proof.md")
os.makedirs(os.path.dirname(report_path), exist_ok=True)
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"Report written to {report_path}")
