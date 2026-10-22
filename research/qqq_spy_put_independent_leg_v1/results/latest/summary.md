# QQQ LONG PUT / SPY SHORT PUT — Independent-Leg Sizing V2

**Status: independent EOD quote-side replay; research only. No live sizing or orders; no merge to main.**

## Method

- Frozen originally selected cohorts: 44. Requested window: 2018-03-01 to 2025-12-15; common underlying sessions: 1959.
- QQQ LONG PUT standalone: N=1–9; SPY SHORT PUT standalone: N=1–9; fixed paired N:M combinations: 36 with combined count <= 9.
- Exact original contract IDs are reused; each plan starts no earlier than the next common session after the signal. Failed entry-side depth defers; entry is skipped by expiry/source end.
- QQQ standalone entry/exit depends only on QQQ quote and Ask/Bid depth. SPY standalone depends only on SPY quote and Bid/Ask depth. Fixed pairs require both legs at entry and exit.
- Entries use QQQ Ask and SPY Bid; exits use QQQ Bid and SPY Ask. No forward-filling or contract substitutions.
- Costs: zero, base USD 0.05 per option share per side plus USD 0.65 per contract per side, and adverse USD 0.10/share plus USD 0.65/side.
- Displayed EOD depth is a screening gate, not a guaranteed fill. These are not exchange-confirmed executions.

## Entry coverage

- QQQ-only plans: 396; entered 396; skipped 0.
- SPY-only plans: 396; entered 396; skipped 0.
- Pair plans: 1584; entered 1584; skipped 0.
- Candidate-level defer/skip reasons and entry side sizes are recorded in the attempt CSV; exit size values and unresolved states are in the raw trade files.

## Original premium-matched baseline reference (base costs)

Baseline numbers come from the frozen prior run. Entry/outcome coverage and fixed sizing differ across grid cells, so they are reference comparisons, not automatically a matched experiment.

| Exit policy | Resolved/opened | Win/loss | Win rate | Mean net P&L | Total net P&L | Mean QQQ debit | Mean SPY credit | Premium match |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 44/44 | 11/33 | 25.00% | USD -231.91 | USD -10,204.20 | USD 1,615.20 | USD 1,622.70 | 95.43% |
| HOLD_10_SESSIONS | 44/44 | 12/32 | 27.27% | USD -331.37 | USD -14,580.20 | USD 1,615.20 | USD 1,622.70 | 95.43% |
| HOLD_20_SESSIONS | 44/44 | 8/36 | 18.18% | USD -594.66 | USD -26,165.20 | USD 1,615.20 | USD 1,622.70 | 95.43% |
| EXIT_AT_DTE_LE_7 | 36/44 | 12/24 | 33.33% | USD -668.12 | USD -24,052.30 | USD 1,615.20 | USD 1,622.70 | 95.43% |

## Independent legs (base costs)

| Policy | Standalone leg | N | Entered/candidate | Resolved/entered | Win rate | Mean net P&L | Total net P&L | Worst resolved |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | QQQ LONG PUT | 1 | 44/44 | 44/44 | 25.00% | USD -21.60 | USD -950.20 | USD -510.30 |
| HOLD_5_SESSIONS | QQQ LONG PUT | 4 | 44/44 | 44/44 | 25.00% | USD -31.38 | USD -1,380.80 | USD -2,041.20 |
| HOLD_5_SESSIONS | QQQ LONG PUT | 9 | 44/44 | 44/44 | 25.00% | USD 90.16 | USD 3,967.20 | USD -4,592.70 |
| HOLD_5_SESSIONS | SPY SHORT PUT | 1 | 44/44 | 44/44 | 72.73% | USD -25.87 | USD -1,138.20 | USD -2,948.30 |
| HOLD_5_SESSIONS | SPY SHORT PUT | 4 | 44/44 | 44/44 | 72.73% | USD -102.29 | USD -4,500.80 | USD -11,793.20 |
| HOLD_5_SESSIONS | SPY SHORT PUT | 9 | 44/44 | 44/44 | 75.00% | USD -199.68 | USD -8,785.80 | USD -26,534.70 |
| HOLD_10_SESSIONS | QQQ LONG PUT | 1 | 44/44 | 44/44 | 20.45% | USD -29.89 | USD -1,315.20 | USD -619.30 |
| HOLD_10_SESSIONS | QQQ LONG PUT | 4 | 44/44 | 44/44 | 20.45% | USD -74.56 | USD -3,280.80 | USD -2,477.20 |
| HOLD_10_SESSIONS | QQQ LONG PUT | 9 | 44/44 | 44/44 | 20.45% | USD -32.15 | USD -1,414.80 | USD -5,573.70 |
| HOLD_10_SESSIONS | SPY SHORT PUT | 1 | 44/44 | 44/44 | 75.00% | USD -38.00 | USD -1,672.20 | USD -3,007.30 |
| HOLD_10_SESSIONS | SPY SHORT PUT | 4 | 44/44 | 44/44 | 75.00% | USD -184.84 | USD -8,132.80 | USD -12,029.20 |
| HOLD_10_SESSIONS | SPY SHORT PUT | 9 | 44/44 | 44/44 | 75.00% | USD -415.88 | USD -18,298.80 | USD -27,065.70 |
| HOLD_20_SESSIONS | QQQ LONG PUT | 1 | 44/44 | 44/44 | 20.45% | USD -54.89 | USD -2,415.20 | USD -870.30 |
| HOLD_20_SESSIONS | QQQ LONG PUT | 4 | 44/44 | 44/44 | 20.45% | USD -206.84 | USD -9,100.80 | USD -3,481.20 |
| HOLD_20_SESSIONS | QQQ LONG PUT | 9 | 44/44 | 44/44 | 20.45% | USD -374.97 | USD -16,498.80 | USD -7,337.70 |
| HOLD_20_SESSIONS | SPY SHORT PUT | 1 | 44/44 | 44/44 | 79.55% | USD -91.89 | USD -4,043.20 | USD -9,516.30 |
| HOLD_20_SESSIONS | SPY SHORT PUT | 4 | 44/44 | 44/44 | 79.55% | USD -369.11 | USD -16,240.80 | USD -38,065.20 |
| HOLD_20_SESSIONS | SPY SHORT PUT | 9 | 44/44 | 44/44 | 79.55% | USD -830.50 | USD -36,541.80 | USD -85,646.70 |
| EXIT_AT_DTE_LE_7 | QQQ LONG PUT | 1 | 44/44 | 37/44 | 27.03% | USD -4.81 | USD -178.10 | USD -878.30 |
| EXIT_AT_DTE_LE_7 | QQQ LONG PUT | 4 | 44/44 | 36/44 | 27.78% | USD 0.91 | USD 32.80 | USD -3,513.20 |
| EXIT_AT_DTE_LE_7 | QQQ LONG PUT | 9 | 44/44 | 36/44 | 27.78% | USD 287.55 | USD 10,351.80 | USD -7,517.70 |
| EXIT_AT_DTE_LE_7 | SPY SHORT PUT | 1 | 44/44 | 43/44 | 81.40% | USD -91.28 | USD -3,924.90 | USD -6,337.30 |
| EXIT_AT_DTE_LE_7 | SPY SHORT PUT | 4 | 44/44 | 43/44 | 81.40% | USD -403.71 | USD -17,359.60 | USD -26,933.20 |
| EXIT_AT_DTE_LE_7 | SPY SHORT PUT | 9 | 44/44 | 42/44 | 83.33% | USD -504.34 | USD -21,182.40 | USD -60,599.70 |

## Fixed paired examples (base costs; premium cash flows shown)

| Policy | QQQ:SPY | Entered/candidate | Resolved/entered | Win rate | Mean net P&L | Mean QQQ debit | Mean SPY credit | Match score | Worst resolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1:1 | 44/44 | 44/44 | 36.36% | USD -47.46 | USD 438.45 | USD 432.20 | 86.51% | USD -1,204.60 |
| HOLD_5_SESSIONS | 1:5 | 44/44 | 44/44 | 72.73% | USD -149.12 | USD 437.43 | USD 2,158.86 | 19.69% | USD -12,997.80 |
| HOLD_5_SESSIONS | 4:4 | 44/44 | 44/44 | 38.64% | USD -175.04 | USD 1,746.18 | USD 1,725.09 | 86.48% | USD -4,818.40 |
| HOLD_5_SESSIONS | 4:5 | 44/44 | 44/44 | 56.82% | USD -206.63 | USD 1,746.18 | USD 2,156.36 | 77.76% | USD -7,766.70 |
| HOLD_5_SESSIONS | 5:1 | 44/44 | 44/44 | 22.73% | USD -79.35 | USD 2,187.84 | USD 431.70 | 20.99% | USD -2,154.80 |
| HOLD_10_SESSIONS | 1:1 | 44/44 | 44/44 | 43.18% | USD -67.90 | USD 438.45 | USD 432.20 | 86.51% | USD -1,351.60 |
| HOLD_10_SESSIONS | 1:5 | 44/44 | 44/44 | 72.73% | USD -250.16 | USD 437.43 | USD 2,158.86 | 19.69% | USD -13,380.80 |
| HOLD_10_SESSIONS | 4:4 | 44/44 | 44/44 | 45.45% | USD -258.40 | USD 1,746.18 | USD 1,725.09 | 86.48% | USD -5,406.40 |
| HOLD_10_SESSIONS | 4:5 | 44/44 | 44/44 | 61.36% | USD -305.02 | USD 1,746.18 | USD 2,156.36 | 77.76% | USD -8,413.70 |
| HOLD_10_SESSIONS | 5:1 | 44/44 | 44/44 | 20.45% | USD -139.78 | USD 2,187.84 | USD 431.70 | 20.99% | USD -2,501.80 |
| HOLD_20_SESSIONS | 1:1 | 44/44 | 44/44 | 38.64% | USD -146.78 | USD 438.45 | USD 432.20 | 86.51% | USD -4,269.60 |
| HOLD_20_SESSIONS | 1:5 | 44/44 | 44/44 | 79.55% | USD -515.25 | USD 437.43 | USD 2,158.86 | 19.69% | USD -42,334.80 |
| HOLD_20_SESSIONS | 4:4 | 44/44 | 44/44 | 40.91% | USD -578.31 | USD 1,746.18 | USD 1,725.09 | 86.48% | USD -17,078.40 |
| HOLD_20_SESSIONS | 4:5 | 44/44 | 44/44 | 70.45% | USD -672.20 | USD 1,746.18 | USD 2,156.36 | 77.76% | USD -26,594.70 |
| HOLD_20_SESSIONS | 5:1 | 44/44 | 44/44 | 18.18% | USD -352.05 | USD 2,187.84 | USD 431.70 | 20.99% | USD -3,500.80 |
| EXIT_AT_DTE_LE_7 | 1:1 | 44/44 | 37/44 | 40.54% | USD -159.63 | USD 438.45 | USD 432.20 | 86.51% | USD -3,134.60 |
| EXIT_AT_DTE_LE_7 | 1:5 | 44/44 | 37/44 | 78.38% | USD -829.58 | USD 437.43 | USD 2,158.86 | 19.69% | USD -30,309.80 |
| EXIT_AT_DTE_LE_7 | 4:4 | 44/44 | 36/44 | 41.67% | USD -681.73 | USD 1,746.18 | USD 1,725.09 | 86.48% | USD -13,506.40 |
| EXIT_AT_DTE_LE_7 | 4:5 | 44/44 | 36/44 | 77.78% | USD -857.92 | USD 1,746.18 | USD 2,156.36 | 77.76% | USD -20,239.70 |
| EXIT_AT_DTE_LE_7 | 5:1 | 44/44 | 36/44 | 25.00% | USD -163.52 | USD 2,187.84 | USD 431.70 | 20.99% | USD -3,536.80 |

## Limits

- This replay fixes the earlier flaw: each standalone leg has its own entry attempts, exit trigger, quote availability and depth gate. Paired positions still close as a pair.
- Fixed N:M does not imply equal premium or equal risk. Inspect debit, credit, mismatch and match score before comparing paired results.
- Unresolved and entry-skipped outcomes stay separate and are not assigned zero. Premium-matched baseline has dynamic quantities and a different denominator/entry policy from fixed grid cells.
- EOD quote history is from a public preservation mirror; SHA pins establish file identity, not exchange authenticity. No early assignment, broker margin, financing, taxes, compounding, forced liquidation or intraday path is modeled.

## Files

- entry_attempts.csv: one row per cohort and tested sizing plan, with deferrals and final entry result.
- independent_leg_trades.csv: standalone positions with leg-specific exits and quote depth.
- fixed_pair_trades.csv: pairs with both-leg entry/exit depth checks.
- independent_leg_sizing.csv: standalone N performance, three cost assumptions.
- fixed_pair_cross_grid.csv: all paired N:M cases under the total contract cap.
- premium_matched_baseline.csv: frozen prior run, recalculated under the cost assumptions.
- source_manifest.json: pinned output inputs and hashes.
