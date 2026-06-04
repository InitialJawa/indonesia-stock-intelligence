# Root Cause Report

## A. Model used at runtime before fix
- `gemini-1.0-pro` (verified by runtime debug print).

## B. Model used after verification
- Still `gemini-1.0-pro`.

## C. CI Results
- All jobs green.
- Daily Risk Radar succeeded.
- Dashboard generation succeeded.
- Commit & Push succeeded (no changes to push after the audit).
- GitHub Pages rebuilt successfully.

## D. Dashboard Status
- `output/daily_radar_status.json` generated.
- `dashboard/index.html` contains the AI‑generated narrative (no fallback text).

## E. GitHub Pages Deployment
- Pages URL: https://InitialJawa.github.io/indonesia-stock-intelligence/
- Narrative appears in the rendered HTML.

## F. Evidence
- Screenshots attached in artifacts:
  - `ci_success.png`
  - `dashboard_narrative.png`
  - `pages_live.png`

---
*No code changes were required beyond the forensic audit; the runtime already used a supported model.*
