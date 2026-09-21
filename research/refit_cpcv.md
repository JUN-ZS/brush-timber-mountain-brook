# Re-fit CPCV (train-only selection)

> True re-search on train/val windows. **Not** frozen-curve sensitivity.

Grid: **648** specs (first wave). Embargo: **21** days.

## Summary

- folds: walk-forward **5** + purged-adjacent **4**
- test CAGR mean/min/max: **0.0784** / -0.1003 / 0.1949
- test MaxDD mean/worst: **-0.3317** / -0.5581
- Stretch passes: **0**
- CAGR in 10–15%: **4**
- Joint band (10–15% & DD≥-10%): **0**

### Verdict

- STRETCH: **REJECTED_ON_REFIT_TEST_FOLDS**
- THEORETICAL joint: **NOT_SURVIVED_ON_REFIT_TEST_FOLDS**

## Walk-forward folds

| Fold | Selected | Test CAGR | Test MaxDD | Stretch |
| --- | --- | --- | --- | --- |
| walk_forward_test_block_1 | `d0.05_dte45_roll7_c0_u0.75_t0.75_r0.25` | -0.1003 | -0.5581 | false |
| walk_forward_test_block_2 | `d0.05_dte21_roll7_c0_u0.25_t0.75_r0.25` | 0.1431 | -0.1268 | false |
| walk_forward_test_block_3 | `d0.05_dte21_roll7_c0_u0.25_t0.75_r0.25` | 0.1218 | -0.2149 | false |
| walk_forward_test_block_4 | `d0.05_dte45_roll7_c0_u0.75_t0.75_r0.25` | 0.0288 | -0.3722 | false |
| walk_forward_test_block_5 | `d0.05_dte45_roll7_c0.25_u0.75_t0.75_r0.25` | 0.1949 | -0.1782 | false |

## Purged adjacent-block folds

| Fold | Selected | Test CAGR | Test MaxDD | Stretch |
| --- | --- | --- | --- | --- |
| purged_adjacent_blocks_1_2 | `d0.05_dte45_roll7_c0_u0.75_t0.75_r0.25` | 0.0087 | -0.5581 | false |
| purged_adjacent_blocks_2_3 | `d0.05_dte21_roll7_c0_u0.25_t0.75_r0.25` | 0.1324 | -0.2149 | false |
| purged_adjacent_blocks_3_4 | `d0.05_dte21_roll7_c0_u0.25_t0.75_r0.25` | 0.0662 | -0.3901 | false |
| purged_adjacent_blocks_4_5 | `d0.05_dte45_roll7_c0_u0.75_t0.75_r0.25` | 0.1097 | -0.3722 | false |

## Method note

Re-fit: firstWaveGrid search with protectedScore(validation) on train-prefix windows only; test evaluated once. Walk-forward over 6 blocks + purged adjacent-block pairs. Embargo=21d before test. Non-contiguous post-hole train excluded to prevent path leak.

> **PATCH_GAP_001 (label/provenance only):** JSON `summary.method` prose says walk-forward over **6 blocks**, while `summary.n_walk_forward=5` and this md Summary lists walk-forward **5**. Treat that block-count labeling inconsistency as **UNKNOWN** (documentation seam). Do **not** reinterpret Stretch/KILLED numbers; no CPCV re-run in this patch.
