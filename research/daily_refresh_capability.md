# Daily Refresh Capability

**Generated:** 2026-06-07

---

## Question A: Can Config B rankings update automatically?

### Answer: PARTIALLY

**What works today:**
- The monthly pipeline (`monthly_pipeline.yml`) runs automatically on the 1st of each month
- It executes `scoring.final_score_v3.py` which produces `output/scores/final_ranking_v3.json` using Config F weights (Q25/G10/V30/M35)
- Config B weights (Q25/G30/V10/M35) can be obtained by changing `config/scoring_weights.json`

**What's missing for TRUE daily automation:**

| Gap | Impact | Fix Required |
|-----|--------|-------------|
| Daily workflow (`daily_radar.yml`) does NOT run the scoring pipeline | Rankings update only once per month | Add scoring modules to daily workflow OR make `data_fetcher.py` write to `output/scores/*.json` |
| `data_fetcher.py` computes inline scores with different formulas | Daily and monthly scores diverge | Change `data_fetcher.py` to call the same scoring modules or replicate the logic |
| `data_fetcher.py` doesn't normalize scores | Daily scores are raw values, not percentile-comparable | Add percentile normalization to `data_fetcher.py` |
| Config switch requires git commit (changing `config/scoring_weights.json`) | Cannot switch between Config B and Config F without a code push | Store config name as workflow input parameter in `monthly_pipeline.yml` |

**Verdict:** Config B rankings CAN update automatically ONCE PER MONTH. True daily updates would require wiring the scoring pipeline into the daily workflow.

---

## Question B: Can Turnaround rankings update automatically?

### Answer: NO

**Current state:**
- **No turnaround ranking script exists** anywhere in the codebase
- The dashboard has a "Sedang Anget" label (momentum 55-85, quality > 45, value > 40) but this is a simple filter, not a ranking
- No turnaround signal logic, score computation, or output file exists

**What's missing:**

| Requirement | Current Status |
|-------------|---------------|
| Turnaround signal definition | Not defined |
| Scoring algorithm | Not implemented |
| Output file (`output/scores/turnaround_ranking.json`) | Does not exist |
| Dashboard integration | Not wired |
| Workflow step | Not added |

**What would be needed to build it:**

1. Define turnaround signal (e.g., recovery_from_60d_low, rs_change_60d_improving, drawdown_compression — from RESEARCH-008B findings)
2. Create `scoring/turnaround_score.py` that reads warehouse data and computes a turnaround score
3. Add to `run_monthly_pipeline.py` between step 10 and 11
4. Add to `dashboard/generate_dashboard.py` to display turnaround state
5. Add `output/scores/turnaround_ranking.json` to monthly pipeline git commit

**Verdict:** Turnaround rankings cannot update because the script does not exist. This is greenfield work.

---

## Question C: Can Dashboard display new rankings without manual edits?

### Answer: PARTIALLY

**What works today:**
- `dashboard/generate_dashboard.py` reads ALL files in `output/scores/*.json` automatically
- It reads `final_ranking_v3.json`, `quality_ranking.json`, `growth_ranking.json`, `value_ranking.json`, `momentum_ranking.json`
- Any additional score file added to `output/scores/` is currently **NOT** read (the script explicitly lists its inputs)

**What would be needed to auto-display new rankings:**

| Change | Effort |
|--------|--------|
| Add new score file name to `generate_dashboard.py` ~line 149-154 | 1 line |
| Add new data field to `stocks_js_list` entries ~line 295-320 | 1-2 lines |
| Add new column to HTML table if visual display desired | 5-10 lines |
| Add new filter/state badge if needed | 10-15 lines |

**Verdict:** Minor code changes needed. The dashboard architecture supports extensibility — each new ranking just needs a few lines added. But it's NOT fully automatic — a developer must edit `generate_dashboard.py`.

---

## Question D: Can a single daily run refresh the entire system?

### Answer: NOT YET

**What a "full refresh" requires:**

```
1. Fetch fundamentals      ───▶ output/raw/fundamentals.json    (API: yfinance)
2. Fetch growth            ───▶ output/raw/growth.json         (API: yfinance)
3. Fetch prices            ───▶ output/raw/prices.json         (API: yfinance)
4. Compute quality scores  ───▶ output/scores/quality_ranking.json
5. Compute growth scores   ───▶ output/scores/growth_ranking.json
6. Compute value scores    ───▶ output/scores/value_ranking.json
7. Compute momentum scores ───▶ output/scores/momentum_ranking.json
8. Compute final scores    ───▶ output/scores/final_ranking_v3.json
9. Archive current state   ───▶ archives/rankings/{YYYY-MM}.json
10. Rebalance portfolio    ───▶ archives/portfolios/{YYYY-MM}.json
11. Generate dashboard     ───▶ dashboard/index.html + data.json
12. Run daily risk radar   ───▶ dashboard/data.json (update)
```

**Current state:**

| Step | Daily Workflow | Monthly Workflow | Combined |
|------|---------------|-----------------|----------|
| 1-3 (API fetch) | `data_fetcher.py` (inline, different format) | `collectors.*` (proper format) | ❌ Different outputs |
| 4-8 (Scoring) | SKIPPED | Full scoring pipeline | ❌ Not in daily |
| 9 (Archive) | SKIPPED | `archive_current_state` | ❌ Not in daily |
| 10 (Rebalance) | SKIPPED | `rebalance` | ❌ Not in daily |
| 11 (Dashboard) | `generate_dashboard` | `generate_dashboard` | ✅ Both |
| 12 (Radar) | `data_fetcher.py` | SKIPPED | ❌ Not in monthly |

**What's needed for a single-run full refresh:**

1. **Merge daily and monthly workflows into one.** Replace `data_fetcher.py` with the full `run_monthly_pipeline.py` in the daily workflow.
2. **Remove duplicate scoring from `data_fetcher.py`.** The monthly scoring pipeline is canonical — `data_fetcher.py` should be deprecated or converted to only fetch radar-specific data.
3. **Add daily radar step to the unified pipeline.** The AI narrative generation (from `run_daily_risk_radar.py`) should run after scoring.
4. **Add daily price fetch.** The monthly pipeline fetches 5 days of prices. A daily run needs the latest close.
5. **Reduce API calls.** Running the full pipeline daily means 30+ yfinance API calls per day. Consider caching or throttling.

**Verdict:** A full daily refresh is architecturally possible but requires merging the two workflows and deprecating the parallel scoring in `data_fetcher.py`. Estimated effort: moderate (2-3 days of refactoring).

---

## Summary

| Question | Answer | Effort Required |
|----------|--------|-----------------|
| A: Config B daily auto-update | PARTIALLY (monthly only) | 1 day to add scoring to daily workflow |
| B: Turnaround auto-update | NO (doesn't exist) | 3-5 days to build from scratch |
| C: New rankings on dashboard | PARTIALLY (minor edits needed) | Hours per new ranking |
| D: Single daily full refresh | NOT YET | 2-3 days to merge workflows |

**Overall assessment:** Dashboard V2 requires BOTH UI work AND backend automation changes. The scoring pipeline is solid but runs only monthly. Daily automation infrastructure exists but produces inconsistent scores. Turnaround ranking is greenfield.

---

*End of Daily Refresh Capability*
