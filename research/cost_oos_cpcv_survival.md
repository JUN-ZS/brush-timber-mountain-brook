# Cost × OOS × CPCV × Survival

> Frozen V2.2 Derived path only. **No new parameter carving.**

## Cost multiplier

Baseline `cost_mult=1.0` already includes V2.2 estimated 10% spread. Higher mult adds extra premium drag.

| Cost × | CAGR | MaxDD | CAGR in 10–15% | Band CAGR+DD<-10% | Stretch 12/<5 |
| --- | --- | --- | --- | --- | --- |
| 1.0 | 7.0% | -53.4% | False | False | False |
| 1.25 | 4.1% | -56.3% | False | False | False |
| 1.5 | 1.2% | -59.2% | False | False | False |
| 2.0 | -4.3% | -75.0% | False | False | False |
| 3.0 | -14.6% | -97.7% | False | False | False |

## Era @ cost 1.0

| Era | CAGR | MaxDD | State | Stretch |
| --- | --- | --- | --- | --- |
| 2003-2007 | 8.0% | -14.2% | CALM | False |
| 2008-2009 | -17.8% | -49.0% | TAIL | False |
| 2010-2019 | 9.9% | -19.5% | CALM | False |
| 2020 | 23.0% | -18.9% | UNSTABLE | False |
| 2021-2022 | -11.9% | -35.2% | UNSTABLE | False |
| 2023-2026 | 22.0% | -17.8% | CALM | False |

## Leave-one-era-out (frozen path)

| Held out | Holdout CAGR | Holdout MaxDD | Stretch |
| --- | --- | --- | --- |
| 2003-2007 (BULL) | 8.0% | -14.2% | False |
| 2008-2009 (CRISIS) | -17.8% | -49.0% | False |
| 2010-2019 (BULL) | 9.9% | -19.5% | False |
| 2020 (SHOCK) | 23.0% | -18.9% | False |
| 2021-2022 (BEAR) | -11.9% | -35.2% | False |
| 2023-2026 (CURRENT) | 22.0% | -17.8% | False |

## CPCV-style block summary

- folds: **15**
- test CAGR mean/min/max: **4.7%** / -1.3% / 12.2%
- test MaxDD mean / worst: **-33.8%** / -53.4%
- folds with Stretch pass: **0**
- folds with CAGR in 10–15%: **2**

## Survival verdict

- `THEORETICAL_TARGET_BAND_cagr_10_15_and_maxdd_gt_-10`: **FAIL**
- `STRETCH_12_and_maxdd_gt_-5`: **FAIL**
- `cost_mult_2x_still_cagr_in_10_15`: **FAIL**
- `all_era_holdouts_avoid_stretch_claim`: **PASS**
- `cpcv_stretch_fold_count_is_zero`: **PASS**
- `crisis_era_2008_survives_without_blowup_definition`: **PASS**

### Bottom line

- THEORETICAL_TARGET_BAND (joint): **NOT_SURVIVED as joint CAGR+DD band on frozen V2.2 full path**
- STRETCH_HYPOTHESIS: **REJECTED on frozen V2.2 (full, eras, cost×2, CPCV folds)**
- Useful: Era sensitivity is large; cost↑ hurts CAGR; crisis DD ~-48% dominates any <5% fantasy

Next honest upgrade would be **re-fit CPCV** (re-search inside train only) — not more carved full-sample curves.
