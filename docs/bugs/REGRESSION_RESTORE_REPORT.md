# Regression Restore Report — My Portfolio Cleanup

## Summary
Restored `generate_dashboard_v2.py` and `dashboard/index.html` to clean 6-tab state by surgically removing FEATURE-001 (My Portfolio) code while preserving BUG-005 timestamp fixes.

## Changes Made

### `scripts/generate_dashboard_v2.py` — 10 edit points

| # | What | Why |
|---|------|-----|
| 1 | Removed `PORTFICO_FILE` constant (L15) | Unreferenced after portfolio removal |
| 2 | Removed `classify_action()` and `enrich_portfolio()` functions | Portfolio-specific logic |
| 3 | Removed `portfolio_json = ...` variable | No longer needed in template |
| 4 | Removed `06 · My Portfolio` tab button | Tab deleted; Exit Monitor reindexed `st(6)→st(5)` |
| 5 | Removed portfolio tab section `<div class="tc" id="t5">` | Entire My Portfolio HTML block deleted |
| 6 | Removed `const MP={portfolio_json};` | JS data variable for portfolio |
| 7 | Removed PORTFOLIO/WATCH badge from Leaders rendering | Badge was `r.rank<=5 → PORTFOLIO` / `WATCH` |
| 8 | Removed Portfolio IIFE block | Renders `tbody-portfolio` and `mp-cards` |
| 9 | Removed `fmtRupiah()` function | Only used by portfolio IIFE |
| 10 | Removed `portfolio_data` loading in `main()` | No longer reads or passes portfolio data |

All BUG-005 timestamp changes preserved:
- `report_date` piped through `build_html()` → header
- `file_age(file, report_date)` calls in cards
- `EXIT_SUMMARY_FILE` constant for exit pipeline

### `dashboard/index.html`
Regenerated from cleaned generator — verified no portfolio output remains.

## Verification
- No `My Portfolio` string in output
- No `tbody-portfolio` or `mp-cards` elements
- No `const MP` or `fmtRupiah` in JS
- No `portfolio_json` references
- 6 tabs: Leaders, Turnaround, Daily Summary, History, Diagnostics, Exit Monitor
- PORTFOLIO/WATCH badges removed from Leaders table
- `#t6` → `#t5` for Exit Monitor references

## Scope
- FEATURE-001 My Portfolio tab: **removed**
- PORTFOLIO/WATCH execution tags: **removed**
- Ticker click panel Insight Layer (aiExplain, renderFundamentals, renderAlignment, `panel-status.portfolio`): **preserved**
- BUG-005 timestamp fix: **preserved**
