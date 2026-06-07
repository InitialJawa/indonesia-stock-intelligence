# SELL WATCHLIST: 3-State Classification
**Generated:** 2026-06-07 15:11:20
**Based on:** RESEARCH-S01 Exit Signal Autopsy

---

## State Definitions

### HEALTHY
No deterioration signals. Stock maintains positive relative strength.
- `RS_CHANGE_60D` near or above zero
- Price above both MA20 and MA50
- Drawdown shallower than -15%
- Volume ratio in normal range (0.8x - 1.5x)

### WEAKENING (Early Warning)
Early deterioration signals detected. Monitor closely.
- RS_CHANGE_60D declining or turning negative
- RS_20D turning negative
- Volume starting to dry up (ratio < 0.8x)
- Price approaching MA20 but still above
- Recovery from 60d low decelerating

### EXIT RISK (Confirmed Deterioration)
Multiple signals confirmed. Consider exit.
- Price below MA20 AND below MA50
- RS_CHANGE_60D deeply negative
- RS_20D negative and declining
- Drawdown expanding past -20%
- Volume ratio below 0.7x (drying up)
- Recovery from 60d low stalled or reversing
- Distance from 252d high widening

---
*End of SELL WATCHLIST Classification*
