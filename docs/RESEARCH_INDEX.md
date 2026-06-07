# RESEARCH INDEX

| ID | Status | Question | Conclusion | Decision |
|----|--------|----------|------------|----------|
| R001-007 | COMPLETE | Define and validate factor scoring framework | Momentum strongest standalone alpha (19.07% CAGR). Quality stabilizes drawdown. Value drags alpha. | All factors accepted. Percentile normalization adopted. |
| R008 | COMPLETE | Find optimal factor weights | Config B (Q25/G30/V10/M35) wins 3/4 core metrics | Config B = PRODUCTION (locked). ADR-003. |
| R008B | COMPLETE | When does a rally actually start? | RS_CHANGE_60D shifts 57% of total movement 40-20 days before rally start. | Used in Turnaround Transition Match signal. |
| R009 | COMPLETE | Is RS_CHANGE_60D a valid timing signal? | Base precision 21.4%, stable across 6 walk-forward windows. Regime-dependent (37.7% bull vs 13.8% bear). | Accepted — requires context filter. |
| R009B | COMPLETE | Why does signal precision vary by ticker? | Volatility is the root cause. High-vol: 43% precision. Low-vol: 4.5%. | Context filter essential for signal quality. |
| R010 | COMPLETE | Can a timing overlay improve Config B? | Timing degraded all metrics. Sharpe: -0.15 to -0.18. CAGR: 0.81% to -0.53%. | NOT PRODUCTION. Timing does not add value. |
| R011 | COMPLETE | Can Turnaround ranking generate alpha? | Marginal alpha (3.05% CAPM). Negative CAGR (-0.17%). Config B superior in all metrics. | Watchlist tool. Not standalone strategy. |
| S01 | COMPLETE | Can we predict sell signals? | No. Losers look HEALTHY at T0 (strong RS, above MA20, elevated volume). Shift to rule-based exits. | Exit Layer V1.1 built. Predictive sell abandoned. |
| AUDIT-001 | COMPLETE | Data quality audit | 2 critical (PBV 8 ticker, DY 100×), 1 medium (AMMN revenue). PBV fix PE×ROE applied. DY format `'dy'` fixed. | DATA_QUALITY_RULE_PBV_V1 formalized. |
| AUDIT-002 | COMPLETE | Yahoo PBV field verification | bookValue/priceToBook salah untuk 8/30 ticker. bookValuePerShare/totalEquity always None. PE×ROE error <10%. | PE×ROE adopted as canonical fallback. MDKA accepted as data limitation. |
