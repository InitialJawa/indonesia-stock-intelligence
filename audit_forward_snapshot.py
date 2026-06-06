import pandas as pd, pathlib, sys
monthly_path = pathlib.Path(r"c:/Users/Bedil Gaib/.gemini/antigravity/scratch/indonesia-stock-intelligence/warehouse/monthly_snapshots/2026-06.csv")
universe_path = pathlib.Path(r"c:/Users/Bedil Gaib/.gemini/antigravity/scratch/indonesia-stock-intelligence/warehouse/universe/2026-06.csv")
monthly = pd.read_csv(monthly_path)
universe = pd.read_csv(universe_path)
rows, cols = monthly.shape
report = []
report.append('## Monthly Snapshot Summary')
report.append(f'- Total rows: {rows}')
report.append(f'- Total columns: {cols}')
null_pct = (monthly.isna().sum() / rows * 100).round(2)
report.append('### Null Percentage by Column')
report.append(null_pct.to_string())
report.append('#### Top 10 columns with highest missing values')
report.append(null_pct.sort_values(ascending=False).head(10).to_string())
# Rank consistency
def rank_mismatches(score_col, rank_col):
    derived = monthly[score_col].rank(ascending=False, method='min')
    return ((derived != monthly[rank_col]) & (~monthly[rank_col].isna())).sum()
rank_issues = {}
for s,r in [('quality_score','quality_rank'),('growth_score','growth_rank'),('value_score','value_rank'),('momentum_score','momentum_rank'),('final_score','final_rank')]:
    if s in monthly.columns and r in monthly.columns:
        rank_issues[f'{s}/{r}'] = rank_mismatches(s,r)
report.append('### Rank Consistency')
for k,v in rank_issues.items():
    report.append(f'- {k}: {v} mismatches')
# Duplicate ticker
dup = monthly['ticker'].duplicated().sum()
report.append('### Duplicate Ticker Check')
report.append(f'- Duplicate tickers: {dup}')
# Metadata completeness
meta_cols = ['collection_date','source','weight_configuration','universe_version','factor_formula_version']
meta_missing = monthly[meta_cols].isna().sum().sum()
report.append('### Metadata Completeness')
report.append(f'- Missing metadata fields across all rows: {meta_missing}')
# Universe summary
u_rows, u_cols = universe.shape
report.append('## Universe Snapshot Summary')
report.append(f'- Total rows: {u_rows}')
report.append(f'- Total columns: {u_cols}')
report.append(f'- Duplicate tickers in universe: {universe["ticker"].duplicated().sum()}')
# Health score
score = 0
avg_null = null_pct.mean()
if avg_null < 5:
    score += 2
elif avg_null < 15:
    score += 1
total_mism = sum(rank_issues.values())
if total_mism == 0:
    score += 2
elif total_mism < rows:
    score += 1
if dup == 0:
    score += 2
if meta_missing == 0:
    score += 2
grade = {8:'A',6:'B',4:'C',2:'D',0:'F'}.get(score,'F')
report.append('### Warehouse Health Score')
report.append(f'- Score: {score}/8 => Grade: {grade}')
print('\n'.join(report))
