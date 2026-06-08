# REGRESSION: My Portfolio Tab Reappearance

## Root Cause

**Incomplete rollback in commit `0ba2f1d`.**

The rollback `0ba2f1d` ("rollback: revert FEATURE-001/002 — dashboard to 81d71b1, generator to 9995704") had asymmetric targets:

| Artifact | Reverted To | State |
|----------|-------------|-------|
| `dashboard/index.html` | `81d71b1` | Pre-FEATURE (no My Portfolio) |
| `scripts/generate_dashboard_v2.py` | `9995704` | **FEATURE-001** (HAS My Portfolio) |

Commit `9995704` ("feat: add My Portfolio monitoring module") is the commit that **introduced** My Portfolio. Reverting the generator to `9995704` means the generator retained all portfolio code. The intended rollback target for the generator should have been `81d71b1` (pre-FEATURE), matching the dashboard.

The My Portfolio tab lay dormant in the generator because no one regenerated the dashboard after the rollback. The BUG-005 fix (`e0b5124`) triggered regeneration, which caused the generator to emit the portfolio tab into the output.

## Trigger Event

Commit `e0b5124` — BUG-005: Dashboard Timestamp Drift fix.
Running `generate_dashboard_v2.py` produced `dashboard/index.html` with Tab 06 (My Portfolio), which was rendered from dormant generator code.

## Timeline

| Step | Commit | Event |
|------|--------|-------|
| 1 | `9995704` | FEATURE-001: My Portfolio tab added to **both** generator and dashboard |
| 2 | `0f56275` | FEATURE-002: Portfolio Simulator added |
| 3 | **`0ba2f1d`** | **Rollback**: dashboard → `81d71b1`, generator → `9995704` (asymmetric — generator keeps portfolio code) |
| 4 | `fab65a9` | Merge: accepts main branch `index.html` (no portfolio tab) |
| 5 | `96f5307` | "Dashboard V2 read-only" — generator not run |
| 6 | **`e0b5124`** | **BUG-005**: regenerates `index.html` → generator emits My Portfolio tab → tab reappears |

## Files Affected

| File | Role |
|------|------|
| `scripts/generate_dashboard_v2.py` | Contains dormant My Portfolio code lineage from `9995704`. The `enrich_portfolio()` function, `PORTFOLIO_FILE` constant, tab button `<button>06 · My Portfolio</button>`, portfolio section HTML, JS IIFE for portfolio rendering, and `portfolio_data` loading in `main()` all originate from FEATURE-001. |
| `dashboard/index.html` | Regenerated output; currently includes Tab 06. |

## Commit IDs

| Commit | Description |
|--------|-------------|
| `9995704` | `feat: add My Portfolio monitoring module` — introduced FEATURE-001 |
| `0ba2f1d` | `rollback: revert FEATURE-001/002 — dashboard to 81d71b1, generator to 9995704` — **incomplete rollback** |
| `81d71b1` | `fix: show all Leader Board columns on mobile, compact bars` — pre-FEATURE baseline (expected rollback target for both) |
| `e0b5124` | `fix: BUG-005 Dashboard Timestamp Drift` — triggered regeneration |

## Branch Origin

All portfolio code traces to the Insight Layer feature branch (PR #1 branch at `a2c428a`), which was merged into parent 2 of `fab65a9`. The `0ba2f1d` rollback was on that branch. The merge `fab65a9` accepted main's `index.html` (clean) but kept the branch's `generate_dashboard_v2.py` (contaminated).

## Recommended Fix

Remove portfolio-related code from `generate_dashboard_v2.py`:

1. Remove `PORTFOLIO_FILE` constant
2. Remove `enrich_portfolio()` function
3. Remove `classify_action()` function (only used by `enrich_portfolio`)
4. Remove portfolio tab button from HTML template (`06 · My Portfolio`)
5. Remove portfolio section HTML from template
6. Remove `portfolio_json` variable and `const MP=...` JS injection
7. Remove portfolio IIFE JS block
8. Remove portfolio data loading from `main()`
9. Remove `portfolio_data` parameter from `build_html()` call
10. Remove `.panel-status.portfolio` CSS rule

Then regenerate `dashboard/index.html`.
