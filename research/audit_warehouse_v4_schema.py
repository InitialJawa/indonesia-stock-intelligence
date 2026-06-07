#!/usr/bin/env python3
"""
COMPLETE WAREHOUSE V4 AUDIT (FINAL VERSION)

Comprehensive audit of database/historical/warehouse_daily_v4.parquet
with focus on:
1. Fuzzy column name matching (against candidates list)
2. Feature duplication & inconsistencies
3. Look-ahead bias detection (conservative messaging)
4. Forward return validation
5. Data quality per ticker (coverage relative to longest history)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
from difflib import SequenceMatcher
import warnings
warnings.filterwarnings('ignore')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WAREHOUSE_FILE = PROJECT_ROOT / "database" / "historical" / "warehouse_daily_v4.parquet"
OUTPUT_DIR = PROJECT_ROOT / "research" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
BENCHMARK_FILE = PROJECT_ROOT / "benchmarks" / "ihsg.csv"

# REQUIRED COLUMNS (separate from expected features)
REQUIRED_COLUMNS = ['Date', 'ticker']

def normalize_name(name):
    """Normalize column name for fuzzy matching"""
    return name.lower().replace('_', '').replace(' ', '').replace('-', '')

def fuzzy_match_against_candidates(expected_name, candidates, actual_columns, threshold=0.6):
    """
    Match expected feature against candidate list, then search actual columns
    
    Args:
        expected_name: The feature we're looking for (e.g., "RS_20d")
        candidates: List of candidate names (e.g., ["rs20", "rs_20", "rs_20d", ...])
        actual_columns: List of columns in dataset
        threshold: Minimum match score
    
    Returns:
        (best_match_column, best_score, matched_candidate)
    """
    norm_expected = normalize_name(expected_name)
    best_match = None
    best_score = threshold
    best_candidate = None
    
    # For each candidate variant, search actual columns
    for candidate in candidates:
        norm_candidate = normalize_name(candidate)
        
        # First, exact match on normalized name
        for actual_col in actual_columns:
            norm_actual = normalize_name(actual_col)
            
            if norm_candidate == norm_actual:
                # Perfect match
                return actual_col, 1.0, candidate
            
            # Fuzzy match
            score = SequenceMatcher(None, norm_candidate, norm_actual).ratio()
            if score > best_score:
                best_score = score
                best_match = actual_col
                best_candidate = candidate
    
    return best_match, best_score, best_candidate

print("="*100)
print("COMPLETE WAREHOUSE V4 AUDIT (FINAL VERSION)")
print("="*100)

# ============================================================================
# LOAD DATA
# ============================================================================
print("\n[LOAD DATA]\n")

if not WAREHOUSE_FILE.exists():
    print(f"❌ ERROR: {WAREHOUSE_FILE} not found!")
    exit(1)

try:
    df = pd.read_parquet(WAREHOUSE_FILE)
    print(f"✓ Loaded warehouse_daily_v4.parquet")
    print(f"  Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"  Memory: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
except Exception as e:
    print(f"❌ ERROR loading parquet: {e}")
    exit(1)

# ============================================================================
# VALIDATE REQUIRED COLUMNS (SEPARATE FROM FEATURES)
# ============================================================================
print("\n[VALIDATE REQUIRED COLUMNS]\n")

actual_columns = list(df.columns)
required_issues = []

for req_col in REQUIRED_COLUMNS:
    if req_col not in actual_columns:
        print(f"❌ CRITICAL: Required column '{req_col}' not found!")
        required_issues.append({
            'severity': 'CRITICAL',
            'category': 'Missing Required Column',
            'issue': f"Column '{req_col}' not found in warehouse",
            'impact': 'Cannot perform any analysis',
            'resolution': 'Add column to warehouse'
        })
    else:
        print(f"✓ Required column '{req_col}' found")

if required_issues:
    print(f"\n❌ FATAL: Cannot proceed without required columns!")
    exit(1)

print(f"\nTotal columns in warehouse: {len(actual_columns)}")
print(f"Columns: {actual_columns}\n")

# ============================================================================
# TASK 1: COLUMN MATCHING WITH CANDIDATES
# ============================================================================
print("\n[TASK 1] FUZZY COLUMN MATCHING (AGAINST CANDIDATES)\n")

expected_features = {
    'RS_20d': {
        'candidates': ['rs20', 'rs_20', 'rs_20d', 'relative_strength_20', 'relative_strength_20d', 'rs_20_period'],
        'category': 'Relative Strength',
        'usage': 'Momentum signal'
    },
    'RS_60d': {
        'candidates': ['rs60', 'rs_60', 'rs_60d', 'relative_strength_60', 'relative_strength_60d', 'rs_60_period'],
        'category': 'Relative Strength',
        'usage': 'Momentum signal'
    },
    'RS_120d': {
        'candidates': ['rs120', 'rs_120', 'rs_120d', 'relative_strength_120', 'relative_strength_120d', 'rs_120_period'],
        'category': 'Relative Strength',
        'usage': 'Momentum signal'
    },
    'RS_252d': {
        'candidates': ['rs252', 'rs_252', 'rs_252d', 'relative_strength_252', 'relative_strength_252d', 'rs_252_period'],
        'category': 'Relative Strength',
        'usage': 'Momentum signal'
    },
    'RS_CHANGE_20d': {
        'candidates': ['rs_change_20', 'rs_change_20d', 'rs_delta_20', 'rs_delta_20d', 'rs_momentum_20d', 'rs_20_change'],
        'category': 'Relative Strength Delta',
        'usage': 'Momentum acceleration'
    },
    'RS_CHANGE_60d': {
        'candidates': ['rs_change_60', 'rs_change_60d', 'rs_delta_60', 'rs_delta_60d', 'rs_momentum_60d', 'rs_60_change'],
        'category': 'Relative Strength Delta',
        'usage': 'Momentum acceleration'
    },
    'RECOVERY': {
        'candidates': ['recovery', 'recovery_factor', 'recovery_60d', 'recovery_from_low', 'price_recovery', 'rebound_factor'],
        'category': 'Price Action',
        'usage': 'Reversal signal'
    },
    'DRAWDOWN': {
        'candidates': ['drawdown', 'drawdown_252d', 'max_drawdown', 'dd_252d', 'max_dd', 'drawdown_period'],
        'category': 'Price Action',
        'usage': 'Risk measurement'
    },
    'DISTANCE_FROM_HIGH': {
        'candidates': ['distance_from_high', 'dist_from_high', 'distance_from_high_252d', 'dist_from_52w_high', 'from_high', 'distance_high'],
        'category': 'Price Action',
        'usage': 'Support/resistance'
    },
    'VOLATILITY_20d': {
        'candidates': ['volatility_20d', 'volatility_20', 'vol_20d', 'vol_20', 'volatility_period_20', 'std_20d'],
        'category': 'Volatility',
        'usage': 'Risk measurement'
    },
    'VOLATILITY_60d': {
        'candidates': ['volatility_60d', 'volatility_60', 'vol_60d', 'vol_60', 'volatility_period_60', 'std_60d'],
        'category': 'Volatility',
        'usage': 'Risk measurement'
    },
    'VOLUME_RATIO': {
        'candidates': ['volume_ratio', 'vol_ratio', 'volume_ma_ratio', 'volume_to_ma', 'vol_to_ma20', 'volume_intensity'],
        'category': 'Volume',
        'usage': 'Momentum confirmation'
    },
    'MOMENTUM_SLOPE': {
        'candidates': ['momentum_slope', 'momentum', 'slope', 'momentum_acceleration', 'price_momentum', 'trend_strength'],
        'category': 'Momentum',
        'usage': 'Trend direction'
    },
    'MA20': {
        'candidates': ['ma20', 'ma_20', 'sma20', 'sma_20', 'moving_average_20'],
        'category': 'Moving Average',
        'usage': 'Support/resistance'
    },
    'MA50': {
        'candidates': ['ma50', 'ma_50', 'sma50', 'sma_50', 'moving_average_50'],
        'category': 'Moving Average',
        'usage': 'Support/resistance'
    },
    'MA100': {
        'candidates': ['ma100', 'ma_100', 'sma100', 'sma_100', 'moving_average_100'],
        'category': 'Moving Average',
        'usage': 'Trend filter'
    },
    'MA200': {
        'candidates': ['ma200', 'ma_200', 'sma200', 'sma_200', 'moving_average_200'],
        'category': 'Moving Average',
        'usage': 'Trend filter'
    },
    'ABOVE_MA20': {
        'candidates': ['above_ma20', 'price_above_ma20', 'close_above_ma20', 'is_above_ma20'],
        'category': 'MA Signal',
        'usage': 'Price position'
    },
    'ABOVE_MA50': {
        'candidates': ['above_ma50', 'price_above_ma50', 'close_above_ma50', 'is_above_ma50'],
        'category': 'MA Signal',
        'usage': 'Price position'
    },
    'ABOVE_MA100': {
        'candidates': ['above_ma100', 'price_above_ma100', 'close_above_ma100', 'is_above_ma100'],
        'category': 'MA Signal',
        'usage': 'Price position'
    },
    'ABOVE_MA200': {
        'candidates': ['above_ma200', 'price_above_ma200', 'close_above_ma200', 'is_above_ma200'],
        'category': 'MA Signal',
        'usage': 'Price position'
    },
    'GOLDEN_CROSS': {
        'candidates': ['golden_cross', 'golden_cross_flag', 'gc_flag', 'is_golden_cross'],
        'category': 'MA Signal',
        'usage': 'Bullish crossover'
    },
    'DEATH_CROSS': {
        'candidates': ['death_cross', 'death_cross_flag', 'dc_flag', 'is_death_cross'],
        'category': 'MA Signal',
        'usage': 'Bearish crossover'
    },
    'CLOSE': {
        'candidates': ['close', 'Close', 'adj_close', 'Adj Close', 'price'],
        'category': 'Price',
        'usage': 'Return calculation'
    },
    'VOLUME': {
        'candidates': ['volume', 'Volume', 'vol', 'trading_volume'],
        'category': 'Volume',
        'usage': 'Confirmation'
    }
}

# Perform matching: candidates -> actual columns
feature_mapping = []
found_features = {}
for feature_name, feature_info in expected_features.items():
    best_match, score, matched_candidate = fuzzy_match_against_candidates(
        feature_name,
        feature_info['candidates'],
        actual_columns,
        threshold=0.5
    )
    
    found_features[feature_name] = {
        'found': best_match is not None,
        'column': best_match,
        'score': score,
        'matched_candidate': matched_candidate,
        'category': feature_info['category'],
        'usage': feature_info['usage']
    }
    
    feature_mapping.append({
        'expected_feature': feature_name,
        'candidates_tested': ', '.join(feature_info['candidates'][:3]),
        'actual_column': best_match,
        'matched_candidate': matched_candidate,
        'fuzzy_match_score': round(score, 3),
        'found': best_match is not None,
        'category': feature_info['category']
    })

# Print mapping results
print(f"{'Expected':<20} {'Candidates Tested':<30} {'Actual Column':<25} {'Score':<8} {'Found':<8}")
print("-" * 95)
for fm in feature_mapping:
    found_str = "✓" if fm['found'] else "✗"
    match_col = fm['actual_column'] if fm['actual_column'] else "(none)"
    cand_str = fm['candidates_tested'] + ("..." if "," in fm['candidates_tested'] else "")
    print(f"{fm['expected_feature']:<20} {cand_str:<30} {match_col:<25} {fm['fuzzy_match_score']:<8} {found_str:<8}")

# ============================================================================
# TASK 2: DETECT DUPLICATES & INCONSISTENCIES
# ============================================================================
print("\n[TASK 2] DUPLICATE & INCONSISTENCY DETECTION\n")

duplicates = []
for feature_name, columns_info in found_features.items():
    if columns_info['found']:
        matching_columns = [fm['actual_column'] for fm in feature_mapping if fm['found'] and fm['actual_column'] == columns_info['column']]
        if len(matching_columns) > 1:
            duplicates.append({
                'column': columns_info['column'],
                'features': [f for f, c in found_features.items() if c['column'] == columns_info['column'] and c['found']]
            })

if duplicates:
    print(f"⚠  Found {len(duplicates)} potential duplicates:")
    for dup in duplicates:
        print(f"   Column '{dup['column']}' maps to features: {dup['features']}")
else:
    print(f"✓ No duplicate feature mappings detected")

# ============================================================================
# TASK 3: LOOK-AHEAD BIAS DETECTION (Conservative)
# ============================================================================
print("\n[TASK 3] LOOK-AHEAD BIAS DETECTION (COLUMN NAMES ONLY)\n")

suspicious_columns = [
    'forward', 'future', 'next_', 'tomorrow', 'prediction', 'forecast',
    'fwd_', 'label', 'target', 'y_', 'return_next', 'return_fwd'
]

look_ahead_suspects = []
for col in actual_columns:
    col_lower = col.lower()
    for suspect in suspicious_columns:
        if suspect in col_lower:
            look_ahead_suspects.append({
                'column': col,
                'suspect_pattern': suspect,
                'reason': 'Column name suggests forward-looking data'
            })

if look_ahead_suspects:
    print(f"⚠  Found {len(look_ahead_suspects)} columns suspicious from NAME ANALYSIS:")
    for suspect in look_ahead_suspects:
        print(f"   '{suspect['column']}' (pattern: '{suspect['suspect_pattern']}')") 
else:
    print(f"✓ No suspicious column names detected")

# Conservative disclaimer
print(f"\n📌 IMPORTANT DISCLAIMER:")
print(f"   This scan only checks COLUMN NAMES for suspicious patterns.")
print(f"   It does NOT detect:")
print(f"   - Shifted/lagged calculations (e.g., .shift(-20))")
print(f"   - Forward-looking windows (e.g., rolling(center=True))")
print(f"   - Renamed columns hiding future data")
print(f"   - Feature engineering using future data")
print(f"\n   To fully audit feature construction, manual code review is required.")

# ============================================================================
# TASK 4: FORWARD RETURN VALIDATION
# ============================================================================
print("\n[TASK 4] FORWARD RETURN VALIDATION\n")

forward_return_cols = [col for col in actual_columns if 'fwd' in col.lower() or 'forward' in col.lower()]
print(f"Found {len(forward_return_cols)} forward return columns:")
for col in forward_return_cols:
    print(f"   • {col}")
    
if forward_return_cols:
    print(f"\n⚠  WARNING: Forward return columns detected!")
    print(f"   These should ONLY be used for defining winner events.")
    print(f"   They MUST NOT be used as features for prediction models.")
    for col in forward_return_cols:
        look_ahead_suspects.append({
            'column': col,
            'suspect_pattern': 'forward_return',
            'reason': 'Forward returns should not be used as features',
            'severity': 'CRITICAL'
        })
else:
    print(f"✓ No forward return columns in feature set (GOOD)")

# Check if Close price exists
close_candidates = ['close', 'Close', 'adj_close', 'Adj Close', 'price', 'Price']
close_col = next((c for c in actual_columns if c in close_candidates), None)
if close_col:
    print(f"\n✓ Close price column found: '{close_col}'")
    print(f"  Can verify formula: (close_t+n / close_t) - 1")
else:
    print(f"\n❌ No close price column found!")

# ============================================================================
# TASK 5: DATA QUALITY PER TICKER (COVERAGE RELATIVE TO MAX)
# ============================================================================
print("\n[TASK 5] DATA QUALITY & COVERAGE ANALYSIS\n")

df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

data_quality_stats = []
abnormal_gaps = []

# Calculate reference for coverage
all_records = []
for ticker in df['ticker'].unique():
    ticker_data = df[df['ticker'] == ticker].sort_values('Date')
    all_records.append(len(ticker_data))

max_records = max(all_records) if all_records else 1
longest_ticker = df['ticker'].unique()[all_records.index(max_records)] if all_records else None

for ticker in sorted(df['ticker'].unique()):
    ticker_data = df[df['ticker'] == ticker].sort_values('Date')
    
    first_date = ticker_data['Date'].min()
    last_date = ticker_data['Date'].max()
    row_count = len(ticker_data)
    date_span = (last_date - first_date).days
    
    # Coverage relative to max records
    coverage_pct = (row_count / max_records * 100) if max_records > 0 else 0
    
    # Find largest date gap
    ticker_data_sorted = ticker_data.sort_values('Date')
    date_diffs = ticker_data_sorted['Date'].diff()
    max_gap_days = date_diffs.max().days if len(date_diffs) > 0 else 0
    
    # Flag abnormal gaps (> 10 days for daily data)
    if max_gap_days > 10:
        abnormal_gaps.append({
            'ticker': ticker,
            'max_gap_days': max_gap_days,
            'first_date': first_date,
            'last_date': last_date
        })
    
    data_quality_stats.append({
        'ticker': ticker,
        'first_date': first_date,
        'last_date': last_date,
        'row_count': row_count,
        'date_span_days': date_span,
        'missing_pct': round(ticker_data.isnull().sum().sum() / (len(ticker_data) * len(ticker_data.columns)) * 100, 2) if len(ticker_data) > 0 else 0,
        'max_gap_days': max_gap_days,
        'coverage_pct': round(coverage_pct, 1)
    })

quality_df = pd.DataFrame(data_quality_stats)
print(f"{'Ticker':<10} {'First Date':<15} {'Last Date':<15} {'Rows':<8} {'Coverage %':<12} {'Max Gap':<10}")
print("-" * 70)
for stat in data_quality_stats:
    print(f"{stat['ticker']:<10} {str(stat['first_date'].date()):<15} {str(stat['last_date'].date()):<15} "
          f"{stat['row_count']:<8} {stat['coverage_pct']:<12.1f}% {stat['max_gap_days']:<10}")

if abnormal_gaps:
    print(f"\n⚠  ABNORMAL GAPS DETECTED ({len(abnormal_gaps)} tickers):")
    for gap in abnormal_gaps:
        print(f"   {gap['ticker']}: max gap = {gap['max_gap_days']} days")
else:
    print(f"\n✓ All tickers have normal date continuity (max gap ≤ 10 days)")

# ============================================================================
# SCHEMA & DTYPE ANALYSIS
# ============================================================================
print("\n[SCHEMA ANALYSIS]\n")

column_info = []
for col in df.columns:
    null_count = df[col].isnull().sum()
    null_pct = (null_count / len(df)) * 100
    dtype = str(df[col].dtype)
    
    non_null_vals = df[col].dropna()
    if len(non_null_vals) > 0:
        sample = str(non_null_vals.iloc[0])[:50]
    else:
        sample = "(all null)"
    
    column_info.append({
        'column': col,
        'dtype': dtype,
        'null_count': int(null_count),
        'null_pct': round(null_pct, 2),
        'non_null_count': len(df) - null_count,
        'sample_value': sample
    })

columns_df = pd.DataFrame(column_info)
print(f"{'Column':<25} {'Type':<12} {'Null %':<10} {'Sample':<40}")
print("-" * 87)
for info in column_info:
    print(f"{info['column']:<25} {info['dtype']:<12} {info['null_pct']:<10.2f}% {info['sample_value']:<40}")

# ============================================================================
# ISSUE DETECTION & SEVERITY ASSESSMENT
# ============================================================================
print("\n[ISSUE IDENTIFICATION]\n")

issues = []

# High priority issues
missing_high = [f for f, info in found_features.items() if not info['found'] and f in ['RS_20d', 'RS_60d', 'CLOSE', 'VOLUME']]
if len(missing_high) > 0:
    for feat in missing_high:
        issues.append({
            'severity': 'HIGH',
            'category': 'Missing Feature',
            'issue': f"Important feature '{feat}' not found",
            'impact': f'Cannot compute {feat} signals',
            'resolution': 'Compute from available data or obtain from data provider'
        })

# Medium priority
if len([s for s in data_quality_stats if s['max_gap_days'] > 10]) > 0:
    issues.append({
        'severity': 'MEDIUM',
        'category': 'Data Continuity',
        'issue': f"{len(abnormal_gaps)} tickers have gaps > 10 days",
        'impact': 'Snapshot selection may fail',
        'resolution': 'Handle date gaps gracefully in research script'
    })

# Info level
if duplicates:
    issues.append({
        'severity': 'INFO',
        'category': 'Redundancy',
        'issue': f"{len(duplicates)} columns map to multiple features",
        'impact': 'Potential redundancy in feature set',
        'resolution': 'Review and consolidate if needed'
    })

if len(issues) > 0:
    print(f"Issues found: {len(issues)}")
    critical_count = len([i for i in issues if i['severity'] == 'CRITICAL'])
    high_count = len([i for i in issues if i['severity'] == 'HIGH'])
    
    print(f"  CRITICAL: {critical_count}")
    print(f"  HIGH: {high_count}")
    print(f"  MEDIUM: {len([i for i in issues if i['severity'] == 'MEDIUM'])}")
    print(f"  INFO: {len([i for i in issues if i['severity'] == 'INFO'])}")
    
    print(f"\nDetailed Issues:")
    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. [{issue['severity']}] {issue['category']}")
        print(f"   Problem: {issue['issue']}")
        print(f"   Impact: {issue['impact']}")
        print(f"   Fix: {issue['resolution']}")
else:
    print(f"✓ No issues detected")

# ============================================================================
# SAVE AUDIT RESULTS
# ============================================================================
print("\n[SAVING RESULTS]\n")

# Save feature mapping
feature_df = pd.DataFrame(feature_mapping)
feature_df.to_csv(OUTPUT_DIR / "audit-feature-mapping.csv", index=False)
print(f"✓ audit-feature-mapping.csv")

# Save ticker coverage
quality_df.to_csv(OUTPUT_DIR / "audit-ticker-coverage.csv", index=False)
print(f"✓ audit-ticker-coverage.csv")

# Save columns info
columns_df.to_csv(OUTPUT_DIR / "audit-columns.csv", index=False)
print(f"✓ audit-columns.csv")

# Save issues
issues_df = pd.DataFrame(issues)
issues_df.to_csv(OUTPUT_DIR / "audit-issues.csv", index=False)
print(f"✓ audit-issues.csv")

# Save comprehensive summary
audit_summary = {
    'timestamp': datetime.now().isoformat(),
    'warehouse_file': str(WAREHOUSE_FILE),
    'audit_status': 'READY TO RUN AUDIT',
    'dataset': {
        'shape': {'rows': df.shape[0], 'columns': df.shape[1]},
        'date_range': {
            'min': str(df['Date'].min()),
            'max': str(df['Date'].max()),
            'days_span': int((df['Date'].max() - df['Date'].min()).days)
        },
        'unique_tickers': int(df['ticker'].nunique()),
        'total_records': len(df),
        'longest_ticker': longest_ticker,
        'max_records': max_records
    },
    'features': {
        'total_expected': len(expected_features),
        'found': len([f for f in found_features.values() if f['found']]),
        'missing': len([f for f in found_features.values() if not f['found']]),
        'coverage_pct': round(100 * len([f for f in found_features.values() if f['found']]) / len(expected_features), 1)
    },
    'issues': {
        'total': len(issues),
        'critical': len([i for i in issues if i['severity'] == 'CRITICAL']),
        'high': len([i for i in issues if i['severity'] == 'HIGH']),
        'medium': len([i for i in issues if i['severity'] == 'MEDIUM']),
        'info': len([i for i in issues if i['severity'] == 'INFO'])
    },
    'quality': {
        'look_ahead_bias_suspects': len(look_ahead_suspects),
        'look_ahead_bias_note': 'Column names only - not comprehensive',
        'duplicate_features': len(duplicates),
        'abnormal_gaps': len(abnormal_gaps),
        'coverage_calculation_note': 'Relative to longest ticker history (not adjusted for listing age)'
    },
    'data_quality': {
        'min_coverage_pct': round(quality_df['coverage_pct'].min(), 1) if len(quality_df) > 0 else None,
        'avg_coverage_pct': round(quality_df['coverage_pct'].mean(), 1) if len(quality_df) > 0 else None,
        'max_gap_days': int(quality_df['max_gap_days'].max()) if len(quality_df) > 0 else None
    }
}

with open(OUTPUT_DIR / "audit-summary.json", "w") as f:
    json.dump(audit_summary, f, indent=2)
print(f"✓ audit-summary.json")

# ============================================================================
# GENERATE COMPREHENSIVE AUDIT REPORT
# ============================================================================
print("\n[GENERATING AUDIT REPORT]\n")

report_lines = []
report_lines.append("# RESEARCH-008 WAREHOUSE V4 AUDIT REPORT\n\n")
report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
report_lines.append(f"**Warehouse:** `database/historical/warehouse_daily_v4.parquet`\n\n")

report_lines.append("---\n\n")
report_lines.append("## EXECUTIVE SUMMARY\n\n")

critical_issues = len([i for i in issues if i['severity'] == 'CRITICAL'])
high_issues = len([i for i in issues if i['severity'] == 'HIGH'])
features_found = len([f for f in found_features.values() if f['found']])
features_total = len(expected_features)

# FINAL VERDICT FOR RESEARCH-008 (separate concept)
if critical_issues == 0 and high_issues == 0:
    research_008_verdict = "🟢 **READY FOR RESEARCH-008**\n\n"
elif critical_issues == 0:
    research_008_verdict = f"🟡 **CONDITIONALLY READY FOR RESEARCH-008**\n\n"
else:
    research_008_verdict = f"🔴 **NOT READY FOR RESEARCH-008**\n\n"

report_lines.append(research_008_verdict)

report_lines.append("### Key Metrics\n\n")
report_lines.append(f"| Metric | Value |\n")
report_lines.append(f"|--------|-------|\n")
report_lines.append(f"| **Dataset Shape** | {df.shape[0]:,} rows × {df.shape[1]} columns |\n")
report_lines.append(f"| **Date Range** | {df['Date'].min().date()} to {df['Date'].max().date()} |\n")
report_lines.append(f"| **Unique Tickers** | {df['ticker'].nunique()} |\n")
report_lines.append(f"| **Features Found** | {features_found} / {features_total} ({round(100*features_found/features_total, 1)}%) |\n")
report_lines.append(f"| **Critical Issues** | {critical_issues} |\n")
report_lines.append(f"| **High Priority Issues** | {high_issues} |\n\n")

# Feature Mapping Summary
report_lines.append("---\n\n")
report_lines.append("## FEATURE MAPPING (FUZZY MATCHING)\n\n")
report_lines.append("**Method:** Candidates tested against actual columns using fuzzy matching\n\n")

report_lines.append("### Found Features\n\n")
found_feat_list = [f for f in found_features.items() if f[1]['found']]
for feat_name, feat_info in found_feat_list[:10]:
    report_lines.append(f"- ✓ **{feat_name}** → `{feat_info['column']}` (score: {feat_info['score']:.2f})\n")
if len(found_feat_list) > 10:
    report_lines.append(f"- ... and {len(found_feat_list)-10} more\n")

report_lines.append(f"\n### Missing Features\n\n")
missing_feat_list = [f for f in found_features.items() if not f[1]['found']]
for feat_name, feat_info in missing_feat_list:
    report_lines.append(f"- ✗ **{feat_name}**\n")

# Critical Issues
report_lines.append(f"\n---\n\n## CRITICAL ISSUES\n\n")
if critical_issues > 0:
    for i, issue in enumerate([x for x in issues if x['severity'] == 'CRITICAL'], 1):
        report_lines.append(f"### {i}. {issue['category']}\n\n")
        report_lines.append(f"**Problem:** {issue['issue']}\n\n")
        report_lines.append(f"**Impact:** {issue['impact']}\n\n")
        report_lines.append(f"**Resolution:** {issue['resolution']}\n\n")
else:
    report_lines.append("✓ No critical issues detected.\n\n")

# Look-Ahead Bias Analysis
report_lines.append(f"---\n\n## LOOK-AHEAD BIAS ANALYSIS (COLUMN NAMES ONLY)\n\n")
report_lines.append(f"⚠️ **IMPORTANT:** This audit only scans column names for suspicious patterns.\n\n")
report_lines.append(f"It does NOT detect:\n")
report_lines.append(f"- Shifted/lagged calculations (e.g., `.shift(-20)`)\n")
report_lines.append(f"- Forward-looking windows (e.g., `rolling(window=60, center=True)`)\n")
report_lines.append(f"- Renamed columns hiding future data\n")
report_lines.append(f"- Feature engineering using future data\n\n")
report_lines.append(f"**Manual code review of feature construction is required.**\n\n")

if look_ahead_suspects:
    report_lines.append(f"### Suspicious Columns Found (Name-Based)\n\n")
    report_lines.append(f"{len(look_ahead_suspects)} columns flagged:\n\n")
    for suspect in look_ahead_suspects:
        report_lines.append(f"- `{suspect['column']}` (pattern: `{suspect['suspect_pattern']}`)\n")
else:
    report_lines.append(f"✓ No suspicious column names detected.\n\n")

# Data Quality
report_lines.append(f"---\n\n## DATA QUALITY\n\n")
report_lines.append(f"**Coverage Calculation:** Relative to longest ticker history (not adjusted for listing age)\n\n")
report_lines.append(f"### Ticker Coverage\n\n")
report_lines.append(f"- **Minimum Coverage:** {quality_df['coverage_pct'].min():.1f}%\n")
report_lines.append(f"- **Average Coverage:** {quality_df['coverage_pct'].mean():.1f}%\n")
report_lines.append(f"- **Maximum Gap:** {quality_df['max_gap_days'].max()} days\n")
report_lines.append(f"- **Longest Ticker:** `{longest_ticker}` ({max_records} records)\n\n")

if abnormal_gaps:
    report_lines.append(f"⚠️ **{len(abnormal_gaps)} Tickers with Gaps > 10 Days:**\n\n")
    for gap in abnormal_gaps:
        report_lines.append(f"- `{gap['ticker']}`: {gap['max_gap_days']} days\n")

# Forward Return Validation
report_lines.append(f"\n---\n\n## FORWARD RETURN VALIDATION\n\n")
if forward_return_cols:
    report_lines.append(f"⚠️ **{len(forward_return_cols)} FORWARD RETURN COLUMNS DETECTED**\n\n")
    for col in forward_return_cols:
        report_lines.append(f"- `{col}` (MUST NOT be used as feature)\n\n")
else:
    report_lines.append(f"✓ No forward return columns in feature set (GOOD)\n\n")

if close_col:
    report_lines.append(f"✓ Close price column found: `{close_col}`\n\n")
else:
    report_lines.append(f"❌ No close price column found\n\n")

# Final Verdict
report_lines.append("---\n\n## FINAL VERDICT: RESEARCH-008 READINESS\n\n")

if critical_issues == 0 and high_issues == 0:
    report_lines.append("# 🟢 READY FOR RESEARCH-008\n\n")
    report_lines.append("All critical and high-priority issues resolved.\n")
    report_lines.append("Dataset is suitable for daily winner autopsy analysis.\n\n")
    report_lines.append("**Next Step:** Proceed to run RESEARCH-008.\n\n")
elif critical_issues == 0:
    report_lines.append("# 🟡 CONDITIONALLY READY FOR RESEARCH-008\n\n")
    report_lines.append(f"No critical issues, but {high_issues} high-priority issue(s) require attention.\n")
    report_lines.append("Data quality and feature availability are acceptable with fixes.\n\n")
    report_lines.append("**Next Step:** Address high-priority issues, then run RESEARCH-008.\n\n")
else:
    report_lines.append("# 🔴 NOT READY FOR RESEARCH-008\n\n")
    report_lines.append(f"**{critical_issues} CRITICAL ISSUE(S) MUST BE FIXED FIRST**\n\n")
    report_lines.append("Do not proceed with analysis until all critical issues are resolved.\n\n")
    report_lines.append("**Next Step:** Fix critical issues, regenerate audit, re-evaluate.\n\n")

# Append detailed issue list
report_lines.append("---\n\n## DETAILED ISSUE LOG\n\n")
if issues:
    for i, issue in enumerate(issues, 1):
        report_lines.append(f"{i}. **[{issue['severity']}]** {issue['category']}\n")
        report_lines.append(f"   - **Issue:** {issue['issue']}\n")
        report_lines.append(f"   - **Impact:** {issue['impact']}\n")
        report_lines.append(f"   - **Resolution:** {issue['resolution']}\n\n")
else:
    report_lines.append("No issues detected.\n\n")

# Output file artifacts
report_lines.append("---\n\n## AUDIT ARTIFACTS\n\n")
report_lines.append("Generated files in `research/output/`:\n\n")
report_lines.append("- `audit-columns.csv` - All columns with data types and null %\n")
report_lines.append("- `audit-ticker-coverage.csv` - Coverage per ticker\n")
report_lines.append("- `audit-feature-mapping.csv` - Expected vs actual features (fuzzy matched)\n")
report_lines.append("- `audit-issues.csv` - Detailed issue log\n")
report_lines.append("- `audit-summary.json` - Machine-readable summary\n")

report_text = "".join(report_lines)

with open(OUTPUT_DIR / "research-008-audit-report.md", "w") as f:
    f.write(report_text)
print(f"✓ research-008-audit-report.md")

# ============================================================================
# FINAL CONSOLE OUTPUT
# ============================================================================
print("\n" + "="*100)
print("AUDIT COMPLETE (FINAL VERSION)")
print("="*100)

print(f"\n📊 SUMMARY:\n")
print(f"   Dataset: {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"   Tickers: {df['ticker'].nunique()} ({longest_ticker} is longest with {max_records} records)")
print(f"   Features: {features_found}/{features_total} found ({round(100*features_found/features_total, 1)}%)")
print(f"   Critical Issues: {critical_issues}")
print(f"   High Priority: {high_issues}")

print(f"\n📁 OUTPUT FILES (research/output/):\n")
print(f"   ✓ audit-columns.csv")
print(f"   ✓ audit-ticker-coverage.csv")
print(f"   ✓ audit-feature-mapping.csv")
print(f"   ✓ audit-issues.csv")
print(f"   ✓ audit-summary.json")
print(f"   ✓ research-008-audit-report.md")

print(f"\n🔍 SCRIPT STATUS:\n")
print(f"   ✅ READY TO RUN AUDIT\n")

print(f"📋 RESEARCH-008 READINESS:\n")
if critical_issues == 0 and high_issues == 0:
    print(f"   ✅ READY FOR RESEARCH-008\n")
elif critical_issues == 0:
    print(f"   ⚠️  CONDITIONALLY READY (fix {high_issues} high-priority issue(s))\n")
else:
    print(f"   ❌ NOT READY (fix {critical_issues} critical issue(s))\n")

print("="*100 + "\n")
