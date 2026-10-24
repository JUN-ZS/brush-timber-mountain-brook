# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 834 checks; 81 qualified; 753 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 2 : SPY SHORT PUT 4; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 914.86 / USD 1,758.37; mean absolute mismatch USD 849.38; mean match score 51.28%.
- Actual selected contract ratios: {'2:4': 81}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 81; entered cohorts: 81; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 80/81 | 44/36/0 | 55.00% (44.12–65.42%) | USD -89.67 | USD 101.20 | USD -7,174.00 | USD -1,941.80 | 1 |
| HOLD_10_SESSIONS | 80/81 | 57/23/0 | 71.25% (60.54–80.01%) | USD -158.62 | USD 228.20 | USD -12,690.00 | USD -9,013.80 | 1 |
| HOLD_20_SESSIONS | 78/81 | 64/14/0 | 82.05% (72.10–89.00%) | USD 148.94 | USD 522.20 | USD 11,617.60 | USD -5,581.80 | 3 |
| EXIT_AT_DTE_LE_7 | 71/81 | 57/14/0 | 80.28% (69.58–87.87%) | USD 10.68 | USD 612.20 | USD 758.20 | USD -9,633.80 | 10 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -3.88 | USD -18.00 |
| HOLD_10_SESSIONS | USD -102.12 | USD 11.30 |
| HOLD_20_SESSIONS | USD -222.85 | USD 439.59 |
| EXIT_AT_DTE_LE_7 | USD -200.28 | USD 278.76 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 80 | 56.25% | USD -21.88 | USD -1,750.00 | USD -1,874.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 80 | 56.25% | USD -29.68 | USD -2,374.00 | USD -1,881.80 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 80 | 56.25% | USD -51.88 | USD -4,150.00 | USD -1,904.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 80 | 56.25% | USD -59.67 | USD -4,774.00 | USD -1,911.80 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 80 | 56.25% | USD -81.88 | USD -6,550.00 | USD -1,934.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 80 | 55.00% | USD -89.67 | USD -7,174.00 | USD -1,941.80 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 80 | 52.50% | USD -141.88 | USD -11,350.00 | USD -1,994.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 80 | 51.25% | USD -149.68 | USD -11,974.00 | USD -2,001.80 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 80 | 72.50% | USD -90.83 | USD -7,266.00 | USD -8,946.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 80 | 72.50% | USD -98.62 | USD -7,890.00 | USD -8,953.80 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 80 | 71.25% | USD -120.83 | USD -9,666.00 | USD -8,976.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 80 | 71.25% | USD -128.62 | USD -10,290.00 | USD -8,983.80 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 80 | 71.25% | USD -150.82 | USD -12,066.00 | USD -9,006.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 80 | 71.25% | USD -158.62 | USD -12,690.00 | USD -9,013.80 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 80 | 67.50% | USD -210.82 | USD -16,866.00 | USD -9,066.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 80 | 67.50% | USD -218.62 | USD -17,490.00 | USD -9,073.80 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 78 | 82.05% | USD 216.74 | USD 16,906.00 | USD -5,514.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 78 | 82.05% | USD 208.94 | USD 16,297.60 | USD -5,521.80 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 78 | 82.05% | USD 186.74 | USD 14,566.00 | USD -5,544.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 78 | 82.05% | USD 178.94 | USD 13,957.60 | USD -5,551.80 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 78 | 82.05% | USD 156.74 | USD 12,226.00 | USD -5,574.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 78 | 82.05% | USD 148.94 | USD 11,617.60 | USD -5,581.80 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 78 | 82.05% | USD 96.74 | USD 7,546.00 | USD -5,634.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 78 | 82.05% | USD 88.94 | USD 6,937.60 | USD -5,641.80 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 71 | 81.69% | USD 78.48 | USD 5,572.00 | USD -9,566.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 71 | 81.69% | USD 70.68 | USD 5,018.20 | USD -9,573.80 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 71 | 81.69% | USD 48.48 | USD 3,442.00 | USD -9,596.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 71 | 81.69% | USD 40.68 | USD 2,888.20 | USD -9,603.80 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 71 | 81.69% | USD 18.48 | USD 1,312.00 | USD -9,626.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 71 | 80.28% | USD 10.68 | USD 758.20 | USD -9,633.80 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 71 | 80.28% | USD -41.52 | USD -2,948.00 | USD -9,686.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 71 | 80.28% | USD -49.32 | USD -3,501.80 | USD -9,693.80 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 80/81 (1) | 31.25% (22.15–42.07%) | USD -29.04 | USD -2,323.00 | USD -430.60 |
| HOLD_5_SESSIONS | 1 : 6 | 80/81 (1) | 56.25% (45.34–66.59%) | USD -108.04 | USD -8,643.00 | USD -4,827.10 |
| HOLD_5_SESSIONS | 6 : 1 | 80/81 (1) | 31.25% (22.15–42.07%) | USD -95.22 | USD -7,618.00 | USD -3,928.10 |
| HOLD_5_SESSIONS | 4 : 5 | 80/81 (1) | 46.25% (35.75–57.10%) | USD -131.95 | USD -10,556.00 | USD -2,180.70 |
| HOLD_10_SESSIONS | 1 : 1 | 80/81 (1) | 30.00% (21.06–40.77%) | USD -70.84 | USD -5,667.00 | USD -1,001.60 |
| HOLD_10_SESSIONS | 1 : 6 | 80/81 (1) | 72.50% (61.86–81.08%) | USD -113.21 | USD -9,057.00 | USD -18,784.10 |
| HOLD_10_SESSIONS | 6 : 1 | 80/81 (1) | 22.50% (14.73–32.79%) | USD -382.65 | USD -30,612.00 | USD -4,023.10 |
| HOLD_10_SESSIONS | 4 : 5 | 80/81 (1) | 50.00% (39.30–60.70%) | USD -291.82 | USD -23,346.00 | USD -7,319.70 |
| HOLD_20_SESSIONS | 1 : 1 | 78/81 (3) | 32.05% (22.75–43.04%) | USD -24.13 | USD -1,881.80 | USD -612.60 |
| HOLD_20_SESSIONS | 1 : 6 | 78/81 (3) | 79.49% (69.25–86.96%) | USD 468.86 | USD 36,571.20 | USD -12,548.10 |
| HOLD_20_SESSIONS | 6 : 1 | 78/81 (3) | 19.23% (12.02–29.33%) | USD -637.74 | USD -49,743.80 | USD -4,716.10 |
| HOLD_20_SESSIONS | 4 : 5 | 78/81 (3) | 70.51% (59.62–79.48%) | USD 2.09 | USD 163.40 | USD -3,888.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 71/81 (10) | 32.39% (22.66–43.94%) | USD -53.05 | USD -3,766.60 | USD -1,422.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 71/81 (10) | 83.10% (72.74–90.06%) | USD 238.90 | USD 16,961.90 | USD -23,852.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 71/81 (10) | 12.68% (6.81–22.37%) | USD -610.25 | USD -43,328.10 | USD -4,207.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 71/81 (10) | 70.42% (58.98–79.77%) | USD -153.81 | USD -10,920.70 | USD -8,108.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/81 | 0.00% | USD -96,769.80 | USD -144,865.90 |
| -75% | 0/81 | 0.00% | USD -71,480.49 | USD -107,716.90 |
| -50% | 0/81 | 0.00% | USD -46,191.18 | USD -70,567.90 |
| -40% | 0/81 | 0.00% | USD -36,075.46 | USD -55,708.30 |
| -30% | 0/81 | 0.00% | USD -25,959.74 | USD -40,848.70 |
| -25% | 0/81 | 0.00% | USD -20,901.88 | USD -33,418.90 |
| -20% | 0/81 | 0.00% | USD -15,844.01 | USD -25,989.10 |
| -15% | 0/81 | 0.00% | USD -10,786.15 | USD -18,559.30 |
| -10% | 1/81 | 1.23% | USD -5,726.81 | USD -11,129.50 |
| -5% | 33/81 | 40.74% | USD -797.51 | USD -4,261.00 |
| 0% | 80/81 | 98.77% | USD 809.61 | USD -271.90 |
| 5% | 80/81 | 98.77% | USD 809.61 | USD -271.90 |
| 10% | 80/81 | 98.77% | USD 809.61 | USD -271.90 |
| 20% | 80/81 | 98.77% | USD 809.61 | USD -271.90 |

## Limitations

- Public EOD preservation mirror; hashes establish file identity, not exchange or OPRA authenticity.
- EOD quotes are not verified fills; displayed size is a screening gate, not guaranteed multi-leg execution.
- Conservative sides: QQQ LONG enters Ask/exits Bid; SPY SHORT enters Bid/exits Ask.
- Missing exit quotes/size at expiry or source end remain unresolved; win-rate denominator is resolved episodes only.
- Option chain source ends in 2025; no 2026 performance is observed here.
- Nominal Wilson interval does not correct for regime clustering, dependence, or prior strategy selection.
- Expiry shock grid charges entry-side slippage/commission once and uses intrinsic-value payoff; exercise/assignment fees, broker margin, forced liquidation, financing and interim path are not modeled.
- Equal premium debit/credit does not equalize Delta, max loss, collateral or assignment risk; SPY short put can dominate downside even when QQQ long put appreciates.
- Fixed-cohort replay does not model portfolio compounding, taxes, financing, or verified fills.
- When overlapping cohorts are enabled, multiple fixed-size trades can be open at once; total portfolio cash, margin, forced liquidation, and stacked assignment obligations are not constrained by this replay.

Files: trade_episodes.csv, entry_cohort.csv, entry_skips.csv, cost_sensitivity.csv, sizing_sensitivity.csv, expiry_shock_grid.csv, source_manifest.json.