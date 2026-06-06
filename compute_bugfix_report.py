import pandas as pd, os
csv_path = os.path.join('warehouse','monthly_snapshots','2026-06.csv')
df = pd.read_csv(csv_path)
# Basic stats
total_rows = len(df)
total_columns = len(df.columns)
# Null percentages for each column
null_stats = (df.isnull().mean()*100).round(2)
# Focus on score columns
score_cols = ['quality_score','growth_score','value_score','momentum_score','final_score']
rank_cols = ['quality_rank','growth_rank','value_rank','momentum_rank','final_rank']
report_lines = []
report_lines.append('# Forward Warehouse BUGFIX-003 Report')
report_lines.append('')
report_lines.append(f'**Total rows (data records):** {total_rows}')
report_lines.append(f'**Total columns:** {total_columns}')
report_lines.append('')
report_lines.append('## Null Percentage by Column')
for col in df.columns:
    report_lines.append(f'- {col}: {null_stats[col]}%')
report_lines.append('')
report_lines.append('## Score Columns Null Summary')
for col in score_cols:
    if col in df.columns:
        report_lines.append(f'- {col}: {null_stats[col]}% null')
report_lines.append('')
report_lines.append('## Rank Columns Null Summary')
for col in rank_cols:
    if col in df.columns:
        report_lines.append(f'- {col}: {null_stats[col]}% null')
report_lines.append('')
report_path = os.path.join('reports','forward_warehouse_bugfix_003.md')
os.makedirs('reports', exist_ok=True)
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report_lines))
print(f'Report written to {report_path}')
