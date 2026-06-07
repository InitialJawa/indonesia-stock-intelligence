# REPOSITORY REFACTOR REPORT

**Date:** 2026-06-07 (updated same day — cleanup round 2)
**Objective:** Repository cleanup and knowledge consolidation for single source of truth.

---

## Files Reviewed

| Category | Count |
|----------|-------|
| Root-level files | ~30 |
| Research files | ~50 |
| Docs | ~10 |
| Data files | ~200+ |
| Total | ~300+ |

## Files Archived

| File | Destination | Reason |
|------|-------------|--------|
| `MASTER_CHRONICLE_V2.md` | `docs/archive/MASTER_CHRONICLE_V2.md` | Superseded by V3 |
| `master_chronicle.txt` | `docs/archive/master_chronicle.txt` | Deprecated Indonesian-language BAB 1-22 |
| `PROJECT_STATUS_2026_06_07.md` | `docs/archive/PROJECT_STATUS_2026_06_07.md` | Superseded by `docs/PROJECT_STATUS.md` |
| `backtesting/` | `docs/archive/backtesting/` | Duplicated in `research/` (PIT backtest) + unused archives utilities |
| `reports/` | `docs/archive/reports/` | 75 research reports superseded by `docs/` + `research/output/` |
| `archives/` | `docs/archive/archives/` | Superseded by `database/historical/` + `output/scores/` |
| `compute_acceptance_test.py` | `docs/archive/root_artifacts/` | One-off research artifact at root |
| `compute_bugfix_report.py` | `docs/archive/root_artifacts/` | One-off research artifact at root |
| `test_bugfix.py` | `docs/archive/root_artifacts/` | One-off research artifact at root |
| `model_audit_report.md` | `docs/archive/root_artifacts/` | One-off research artifact at root |
| `root_cause_report.md` | `docs/archive/root_artifacts/` | One-off research artifact at root |
| `fundamental_audit.md` | `docs/archive/root_artifacts/` | One-off research artifact at root |
| `session-ses_163b.md` | `docs/archive/session_logs/` | Developer session log (7,544 lines) |
| `task.md` | `docs/archive/task.md` | Scratch checklist |
| `index.html` | `docs/archive/index.html` | Root redirect → `dashboard/index.html` (Pages redirect now inactive) |

## Files Created

| File | Purpose |
|------|---------|
| `docs/MASTER_CHRONICLE_V3.md` | Single source of truth — comprehensive project overview |
| `docs/RESEARCH_INDEX.md` | One-page research summary table |
| `docs/LESSONS_LEARNED.md` | Catalog of every major mistake and finding |
| `docs/ARCHITECTURE_TREE.md` | Repository structure with PRODUCTION/RESEARCH/ARCHIVE/OBSOLETE tags |
| `docs/PROJECT_STATUS.md` | Current state — what works and what doesn't |
| `docs/REPOSITORY_REFACTOR_REPORT.md` | This file — summary of cleanup |
| `docs/archive/` | Archive directory for superseded documents |

## Files Consolidated

- 3 chronicle files → 1 canonical (`docs/MASTER_CHRONICLE_V3.md`)
- Scattered research conclusions → 1 research index (`docs/RESEARCH_INDEX.md`)
- Lessons from V2 Sections 4-5 + RESEARCH-011 → 1 lessons file (`docs/LESSONS_LEARNED.md`)
- Status updates → 1 project status (`docs/PROJECT_STATUS.md`)

## Cleared Backlog

All 7 cleanup opportunities from the initial refactor have been completed:

| # | Item | Action | Status |
|---|------|--------|--------|
| 1 | `backtesting/` | Moved to `docs/archive/backtesting/` | ✅ |
| 2 | `archives/` | Moved to `docs/archive/archives/` | ✅ |
| 3 | `reports/` | Moved to `docs/archive/reports/` | ✅ |
| 4 | Root research artifacts | Moved to `docs/archive/root_artifacts/` | ✅ |
| 5 | `session-ses_*.md` | Moved to `docs/archive/session_logs/` | ✅ |
| 6 | `task.md` | Moved to `docs/archive/task.md` | ✅ |
| 7 | `index.html` | Moved to `docs/archive/index.html` | ✅ |

## Remaining

- **`research/out_of_sample_validation.py`** — still at `research/`, blocked by Historical Factor Warehouse V2. Keep in place until V2 is feasible.

## Success Criteria Met

- ✅ A new developer can understand the project in 15 minutes (read `MASTER_CHRONICLE_V3.md`)
- ✅ What the project does: factor-based IDX30 ranking and monitoring system
- ✅ What research has been completed: 8 research projects (R008B through R011 + S01)
- ✅ What failed: timing overlays, predictive sell signals, turnaround as standalone, FMP integration, weight optimization
- ✅ What is production: Config B ranking, dashboard, daily/monthly pipelines
- ✅ What is experimental: turnaround watchlist paper trading, exit monitor
- ✅ Single source of truth: `docs/MASTER_CHRONICLE_V3.md`
- ✅ No historical lessons lost: all archived in `docs/archive/`
- ✅ No duplicated chronicles remain active
