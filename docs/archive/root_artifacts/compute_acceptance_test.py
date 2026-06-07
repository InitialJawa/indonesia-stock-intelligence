import pandas as pd, os, json

csv_path = os.path.join('warehouse', 'monthly_snapshots', '2026-06.csv')
report_path = os.path.join('reports', 'forward_warehouse_acceptance_test.md')

# Load data
df = pd.read_csv(csv_path)

total_rows = len(df)
total_columns = len(df.columns)

# Columns to check null percentages
cols = ['quality_score','growth_score','value_score','momentum_score','final_score','quality_rank','growth_rank','value_rank','momentum_rank','final_rank']
null_perc = (df[cols].isnull().mean()*100).round(2)

# Sample rows (first 5)
sample_cols = ['ticker','quality_score','growth_score','value_score','momentum_score','final_score']
sample_rows = df[sample_cols].head(5)

# Build markdown report
lines = []
lines.append('# Forward Warehouse Acceptance Test')
lines.append('')
lines.append('## Summary')
lines.append(f'- **Total rows:** {total_rows}')
lines.append(f'- **Total columns:** {total_columns}')
lines.append('')
lines.append('## Null Percentage for Key Columns')
for col in cols:
    if col in null_perc:
        lines.append(f'- {col}: {null_perc[col]}% null')
lines.append('')
lines.append('## Sample Rows (first 5)')
lines.append('```')
lines.append(sample_rows.to_csv(index=False))
lines.append('```')
lines.append('')
lines.append('## Final Verdict')
# Determine pass/fail: all required columns must have 0% null
if all(null_perc[col] == 0 for col in cols):
    lines.append('**PASS**')
else:
    lines.append('**FAIL**')

os.makedirs(os.path.dirname(report_path), exist_ok=True)
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f'Report written to {report_path}')
