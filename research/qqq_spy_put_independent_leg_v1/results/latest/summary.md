# QQQ LONG PUT / SPY SHORT PUT — Independent-Leg Sizing V1

**Status: research-only counterfactual sizing grid. No live sizing, no orders, no merge to main.**

## What this answers

QQQ LONG PUT and SPY SHORT PUT are first measured separately at fixed N=1 through N=9. Every fixed N:M pair under the combined cap is then cross-compared with the original variable-size equal-premium baseline. All rows reuse the frozen V1 selected contracts, entry dates and conservative quote-side exits; this is not a fresh strike selector or a profit-optimized search.

## Source freeze and controls

- Frozen trade input Git blob SHA: 13b4cf574d24250655d8f9e3d5878e3a4d4f1bd5; frozen summary SHA: 968676c093d48579b516e1b07d4ec55619b90349.
- Window, 44 opened cohorts and four exit policies remain those of the equal-premium V1 input (2018-03-01 through 2025-12-15).
- Standalone N sweep: 1–9; paired cross-grid: each leg N>=1 and QQQ+SPY <= 9 contracts.
- Base costs: $0.05 per option share per side plus $0.65 commission per contract per side. Cost checks include ZERO, BASE and ADVERSE ($0.10/share + $0.65/contract/side).
- Exits use QQQ LONG at displayed Bid and SPY SHORT buyback at displayed Ask. Unresolved episodes remain separate and are excluded from resolved-only P&L / win-rate denominators.
- Fixed-N rows are counterfactual: the source output did not persist every entry/exit displayed-size value needed to verify each fixed N. Do not interpret them as confirmed fills or executable capacities. Only the original premium-matched baseline inherits its source run's entry/exit depth screen.

## Existing equal-premium baseline at base assumed costs

| Exit policy | Resolved / opened | Win / loss / flat | Win rate | Mean net P&L | Total net P&L | Worst resolved |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 44 / 44 | 11 / 33 / 0 | 25.00% | $-231.91 | $-10,204.20 | $-4,818.40 |
| HOLD_10_SESSIONS | 44 / 44 | 12 / 32 / 0 | 27.27% | $-331.37 | $-14,580.20 | $-5,406.40 |
| HOLD_20_SESSIONS | 44 / 44 | 8 / 36 / 0 | 18.18% | $-594.66 | $-26,165.20 | $-17,078.40 |
| EXIT_AT_DTE_LE_7 | 36 / 44 | 12 / 24 / 0 | 33.33% | $-668.12 | $-24,052.30 | $-13,506.40 |

## Independent single-leg results at base costs

Each row below runs one leg alone, with the other leg set to zero. The full N sweep and cost sensitivities are in independent_leg_sizing.csv.

| Exit policy | Standalone leg | N | Resolved / opened | Win rate | Mean net P&L | Total net P&L | Worst resolved |
|---|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | QQQ LONG PUT | 1 | 44 / 44 | 25.00% | $-22.46 | $-988.20 | $-510.30 |
| HOLD_5_SESSIONS | QQQ LONG PUT | 4 | 44 / 44 | 25.00% | $-89.84 | $-3,952.80 | $-2,041.20 |
| HOLD_5_SESSIONS | QQQ LONG PUT | 9 | 44 / 44 | 25.00% | $-202.13 | $-8,893.80 | $-4,592.70 |
| HOLD_5_SESSIONS | SPY SHORT PUT | 1 | 44 / 44 | 72.73% | $-24.30 | $-1,069.20 | $-2,948.30 |
| HOLD_5_SESSIONS | SPY SHORT PUT | 4 | 44 / 44 | 72.73% | $-97.20 | $-4,276.80 | $-11,793.20 |
| HOLD_5_SESSIONS | SPY SHORT PUT | 9 | 44 / 44 | 72.73% | $-218.70 | $-9,622.80 | $-26,534.70 |
| HOLD_10_SESSIONS | QQQ LONG PUT | 1 | 44 / 44 | 20.45% | $-29.89 | $-1,315.20 | $-619.30 |
| HOLD_10_SESSIONS | QQQ LONG PUT | 4 | 44 / 44 | 20.45% | $-119.56 | $-5,260.80 | $-2,477.20 |
| HOLD_10_SESSIONS | QQQ LONG PUT | 9 | 44 / 44 | 20.45% | $-269.02 | $-11,836.80 | $-5,573.70 |
| HOLD_10_SESSIONS | SPY SHORT PUT | 1 | 44 / 44 | 75.00% | $-38.00 | $-1,672.20 | $-3,007.30 |
| HOLD_10_SESSIONS | SPY SHORT PUT | 4 | 44 / 44 | 75.00% | $-152.02 | $-6,688.80 | $-12,029.20 |
| HOLD_10_SESSIONS | SPY SHORT PUT | 9 | 44 / 44 | 75.00% | $-342.04 | $-15,049.80 | $-27,065.70 |
| HOLD_20_SESSIONS | QQQ LONG PUT | 1 | 44 / 44 | 20.45% | $-55.91 | $-2,460.20 | $-870.30 |
| HOLD_20_SESSIONS | QQQ LONG PUT | 4 | 44 / 44 | 20.45% | $-223.65 | $-9,840.80 | $-3,481.20 |
| HOLD_20_SESSIONS | QQQ LONG PUT | 9 | 44 / 44 | 20.45% | $-503.22 | $-22,141.80 | $-7,832.70 |
| HOLD_20_SESSIONS | SPY SHORT PUT | 1 | 44 / 44 | 79.55% | $-91.37 | $-4,020.20 | $-9,516.30 |
| HOLD_20_SESSIONS | SPY SHORT PUT | 4 | 44 / 44 | 79.55% | $-365.47 | $-16,080.80 | $-38,065.20 |
| HOLD_20_SESSIONS | SPY SHORT PUT | 9 | 44 / 44 | 79.55% | $-822.31 | $-36,181.80 | $-85,646.70 |
| EXIT_AT_DTE_LE_7 | QQQ LONG PUT | 1 | 36 / 44 | 27.78% | $3.42 | $123.20 | $-878.30 |
| EXIT_AT_DTE_LE_7 | QQQ LONG PUT | 4 | 36 / 44 | 27.78% | $13.69 | $492.80 | $-3,513.20 |
| EXIT_AT_DTE_LE_7 | QQQ LONG PUT | 9 | 36 / 44 | 27.78% | $30.80 | $1,108.80 | $-7,904.70 |
| EXIT_AT_DTE_LE_7 | SPY SHORT PUT | 1 | 36 / 44 | 77.78% | $-175.05 | $-6,301.80 | $-6,733.30 |
| EXIT_AT_DTE_LE_7 | SPY SHORT PUT | 4 | 36 / 44 | 77.78% | $-700.20 | $-25,207.20 | $-26,933.20 |
| EXIT_AT_DTE_LE_7 | SPY SHORT PUT | 9 | 36 / 44 | 77.78% | $-1,575.45 | $-56,716.20 | $-60,599.70 |

## Paired fixed-N cross-grid examples at base costs

Examples only, not recommendations or optimization winners. The complete pair grid is in fixed_pair_cross_grid.csv and includes expectancy delta versus the equal-premium baseline.

| Exit policy | QQQ long : SPY short | Win rate | Mean net P&L | Delta vs matched baseline expectancy | Total net P&L | Worst resolved |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 36.36% | $-46.76 | $185.15 | $-2,057.40 | $-1,204.60 |
| HOLD_5_SESSIONS | 1 : 5 | 72.73% | $-143.96 | $87.95 | $-6,334.20 | $-12,997.80 |
| HOLD_5_SESSIONS | 4 : 5 | 56.82% | $-211.34 | $20.58 | $-9,298.80 | $-7,766.70 |
| HOLD_5_SESSIONS | 5 : 1 | 22.73% | $-136.60 | $95.32 | $-6,010.20 | $-2,154.80 |
| HOLD_10_SESSIONS | 1 : 1 | 43.18% | $-67.90 | $263.47 | $-2,987.40 | $-1,351.60 |
| HOLD_10_SESSIONS | 1 : 5 | 72.73% | $-219.91 | $111.45 | $-9,676.20 | $-13,380.80 |
| HOLD_10_SESSIONS | 4 : 5 | 61.36% | $-309.59 | $21.78 | $-13,621.80 | $-8,413.70 |
| HOLD_10_SESSIONS | 5 : 1 | 20.45% | $-187.46 | $143.91 | $-8,248.20 | $-2,501.80 |
| HOLD_20_SESSIONS | 1 : 1 | 38.64% | $-147.28 | $447.38 | $-6,480.40 | $-4,269.60 |
| HOLD_20_SESSIONS | 1 : 5 | 79.55% | $-512.75 | $81.91 | $-22,561.20 | $-42,334.80 |
| HOLD_20_SESSIONS | 4 : 5 | 70.45% | $-680.50 | $-85.83 | $-29,941.80 | $-26,594.70 |
| HOLD_20_SESSIONS | 5 : 1 | 18.18% | $-370.94 | $223.73 | $-16,321.20 | $-3,500.80 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 38.89% | $-171.63 | $496.49 | $-6,178.60 | $-3,376.60 |
| EXIT_AT_DTE_LE_7 | 1 : 5 | 77.78% | $-871.83 | $-203.71 | $-31,385.80 | $-30,309.80 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 77.78% | $-861.56 | $-193.44 | $-31,016.20 | $-20,239.70 |
| EXIT_AT_DTE_LE_7 | 5 : 1 | 25.00% | $-157.94 | $510.18 | $-5,685.80 | $-3,536.80 |

## Interpretation boundaries

- Premium parity is a cash-flow match, not equal underlying notional, Delta-dollar, maximum loss, margin or assignment exposure.
- Fixed-N sweeps separate each leg's mark-to-market contribution from paired outcomes, but they do not re-fetch chains or revalidate displayed-size execution capacity.
- Historical EOD quotes are not verified fills. Cohorts can share market regimes; do not select a strategy based on one apparently best grid cell.
- Early assignment, broker margin, financing, taxes, portfolio compounding, forced liquidation and intraday paths are not modeled.

## Files

- independent_leg_sizing.csv: standalone QQQ N and standalone SPY N, each isolated.
- fixed_pair_cross_grid.csv: fixed N:M comparisons under aggregate contract cap.
- premium_matched_baseline.csv: original variable-size baseline by exit rule and cost scenario.
- source_manifest.json: source pins and run parameters.
