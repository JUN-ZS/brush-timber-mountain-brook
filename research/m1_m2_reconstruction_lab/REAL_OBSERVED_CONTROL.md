# REAL OBSERVED M1/M2 CONTROL — V1

## Purpose

This is the simplest **real** historical term-structure lane available in the lab.

It does not reconstruct M1/M2.

It does not infer M1/M2 from VIX.

It directly consumes the observed M1/M2 dataset and then applies the recovered archive policy.

## Exact formula

```
TS_t = (M2_t - M1_t) / M1_t
ΔTS_t = TS_t - TS_{t-1}
Δ²TS_t = ΔTS_t - ΔTS_{t-1}
```

Interpretation:

- TS > 0: contango
- TS = 0: flat
- TS < 0: backwardation

## Exact archive gate

For each aligned historical day:

```
Shock =
    rV > 0.06
 OR VIX > 35
 OR rQ < -0.03

High-Spread = halfSpreadV(VIX) > 0.14

Decay-Optimal =
    TS >= 0
 AND VIX < 28

Action:
    Shock OR TS < 0  -> QQQ_CC_ONLY
    otherwise        -> PAIR
```

VXX carry is eligible exactly when the archive action is PAIR.

## Data

Observed external M1/M2:
- 1,540 rows
- 2016-03-01 → 2022-04-08
- Status: EXTERNAL_OBSERVED / UNVALIDATED_AGAINST_OFFICIAL_SOURCE

Overlap with archived QQQ/VXX spot data:
- 1,060 aligned rows
- 2018-01-25 → 2022-04-08

## Observed term-structure facts

Across all 1,540 observed rows:

- Mean TS: **+6.62%**
- Median TS: **+7.35%**
- 10th percentile: **−1.94%**
- 90th percentile: **+14.39%**
- Minimum TS: **−24.86%**
- Maximum TS: **+28.28%**
- Backwardation rows: **15.39%**
- Backwardation episodes: **42**
- Longest consecutive backwardation run: **52 rows**

Critically, M1 is not VIX:

- Mean (M1 − VIX): **+0.657 VX points**
- Median: **+0.89**
- 10th percentile: **−0.73**
- 90th percentile: **+2.30**
- Minimum: **−17.22**

Example:
- 2020-03-12: VIX 75.47, M1 58.25, M2 45.89, TS −21.22%.
- 2022-02-25: VIX 27.59, M1 27.30, M2 26.95, TS −1.28%.
- 2022-04-08: VIX 21.16, M1 22.60, M2 24.60, TS +8.85%.

These observations are the direct reason a VIX-as-M1 proxy is not a faithful term-structure reconstruction.

## What this lane can truthfully answer

It can answer:

> "If the old archive policy had access to the observed M1/M2 on that historical day, what term state/action would it have produced?"

For the 1,060 overlapping rows, the REAL lane is the ground-truth reference for that question.

It cannot by itself prove the historical 12.5% portfolio CAGR because that additionally requires the original option contract identity, execution timing, premiums, rolls, and complete P&L contract.

## Live rule

When real M1/M2 are unavailable:

```
M1/M2 = UNKNOWN
```

Do **not** substitute VIX, VIX-MA20, VXX, or another futures curve for the real values and label them observed.

The deployment engine may continue non-term monitoring, but any term-dependent decision must remain explicitly marked UNKNOWN or use a separately labelled simulated lane.

## Control hierarchy

```
REAL_OBSERVED_CONTROL
        ↓
empirical / simulated reconstruction candidates
        ↓
compare against REAL_OBSERVED_CONTROL
        ↓
only promote if OOS-stable and provenance-clean
```
