# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 966 checks; 111 qualified; 855 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 2 : SPY SHORT PUT 4; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 909.87 / USD 1,763.27; mean absolute mismatch USD 853.40; mean match score 51.10%.
- Actual selected contract ratios: {'2:4': 110}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 111; entered cohorts: 110; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 110/110 | 65/45/0 | 59.09% (49.75–67.82%) | USD -25.13 | USD 107.20 | USD -2,764.00 | USD -2,511.80 | 0 |
| HOLD_10_SESSIONS | 109/110 | 82/27/0 | 75.23% (66.36–82.38%) | USD 57.41 | USD 270.20 | USD 6,257.80 | USD -4,617.80 | 1 |
| HOLD_20_SESSIONS | 107/110 | 87/20/0 | 81.31% (72.89–87.56%) | USD 257.02 | USD 510.20 | USD 27,501.40 | USD -4,309.80 | 3 |
| EXIT_AT_DTE_LE_7 | 94/110 | 75/19/0 | 79.79% (70.57–86.66%) | USD 114.16 | USD 560.20 | USD 10,730.80 | USD -9,633.80 | 16 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -118.09 | USD 160.76 |
| HOLD_10_SESSIONS | USD -234.68 | USD 359.89 |
| HOLD_20_SESSIONS | USD -424.60 | USD 749.42 |
| EXIT_AT_DTE_LE_7 | USD -294.00 | USD 475.96 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 110 | 61.82% | USD 42.67 | USD 4,694.00 | USD -2,444.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 110 | 61.82% | USD 34.87 | USD 3,836.00 | USD -2,451.80 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 110 | 61.82% | USD 12.67 | USD 1,394.00 | USD -2,474.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 110 | 60.91% | USD 4.87 | USD 536.00 | USD -2,481.80 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 110 | 60.00% | USD -17.33 | USD -1,906.00 | USD -2,504.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 110 | 59.09% | USD -25.13 | USD -2,764.00 | USD -2,511.80 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 110 | 53.64% | USD -77.33 | USD -8,506.00 | USD -2,564.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 110 | 53.64% | USD -85.13 | USD -9,364.00 | USD -2,571.80 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 109 | 76.15% | USD 125.21 | USD 13,648.00 | USD -4,550.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 109 | 76.15% | USD 117.41 | USD 12,797.80 | USD -4,557.80 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 109 | 76.15% | USD 95.21 | USD 10,378.00 | USD -4,580.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 109 | 76.15% | USD 87.41 | USD 9,527.80 | USD -4,587.80 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 109 | 75.23% | USD 65.21 | USD 7,108.00 | USD -4,610.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 109 | 75.23% | USD 57.41 | USD 6,257.80 | USD -4,617.80 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 109 | 72.48% | USD 5.21 | USD 568.00 | USD -4,670.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 109 | 72.48% | USD -2.59 | USD -282.20 | USD -4,677.80 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 107 | 82.24% | USD 324.82 | USD 34,756.00 | USD -4,242.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 107 | 81.31% | USD 317.02 | USD 33,921.40 | USD -4,249.80 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 107 | 81.31% | USD 294.82 | USD 31,546.00 | USD -4,272.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 107 | 81.31% | USD 287.02 | USD 30,711.40 | USD -4,279.80 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 107 | 81.31% | USD 264.82 | USD 28,336.00 | USD -4,302.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 107 | 81.31% | USD 257.02 | USD 27,501.40 | USD -4,309.80 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 107 | 80.37% | USD 204.82 | USD 21,916.00 | USD -4,362.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 107 | 80.37% | USD 197.02 | USD 21,081.40 | USD -4,369.80 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 94 | 79.79% | USD 181.96 | USD 17,104.00 | USD -9,566.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 94 | 79.79% | USD 174.16 | USD 16,370.80 | USD -9,573.80 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 94 | 79.79% | USD 151.96 | USD 14,284.00 | USD -9,596.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 94 | 79.79% | USD 144.16 | USD 13,550.80 | USD -9,603.80 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 94 | 79.79% | USD 121.96 | USD 11,464.00 | USD -9,626.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 94 | 79.79% | USD 114.16 | USD 10,730.80 | USD -9,633.80 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 94 | 79.79% | USD 61.96 | USD 5,824.00 | USD -9,686.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 94 | 79.79% | USD 54.16 | USD 5,090.80 | USD -9,693.80 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 110/110 (0) | 29.09% (21.42–38.17%) | USD -41.45 | USD -4,560.00 | USD -430.60 |
| HOLD_5_SESSIONS | 1 : 6 | 110/110 (0) | 60.00% (50.66–68.67%) | USD 103.00 | USD 11,330.00 | USD -4,827.10 |
| HOLD_5_SESSIONS | 6 : 1 | 110/110 (0) | 30.00% (22.23–39.12%) | USD -393.18 | USD -43,250.00 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 110/110 (0) | 49.09% (39.94–58.30%) | USD -136.93 | USD -15,062.00 | USD -2,439.70 |
| HOLD_10_SESSIONS | 1 : 1 | 109/110 (1) | 31.19% (23.26–40.40%) | USD -49.97 | USD -5,446.40 | USD -790.60 |
| HOLD_10_SESSIONS | 1 : 6 | 109/110 (1) | 76.15% (67.34–83.17%) | USD 343.40 | USD 37,430.10 | USD -10,501.10 |
| HOLD_10_SESSIONS | 6 : 1 | 109/110 (1) | 18.35% (12.20–26.65%) | USD -693.16 | USD -75,554.90 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 109/110 (1) | 54.13% (44.79–63.18%) | USD -121.20 | USD -13,210.30 | USD -4,602.70 |
| HOLD_20_SESSIONS | 1 : 1 | 107/110 (3) | 36.45% (27.95–45.89%) | USD -47.54 | USD -5,087.20 | USD -792.60 |
| HOLD_20_SESSIONS | 1 : 6 | 107/110 (3) | 80.37% (71.85–86.79%) | USD 832.73 | USD 89,102.30 | USD -9,376.10 |
| HOLD_20_SESSIONS | 6 : 1 | 107/110 (3) | 17.76% (11.67–26.08%) | USD -1,165.54 | USD -124,712.70 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 107/110 (3) | 69.16% (59.87–77.12%) | USD -14.12 | USD -1,510.90 | USD -4,305.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 94/110 (16) | 35.11% (26.22–45.17%) | USD -50.61 | USD -4,757.40 | USD -952.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 94/110 (16) | 81.91% (72.93–88.39%) | USD 487.84 | USD 45,856.60 | USD -20,318.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 94/110 (16) | 18.09% (11.61–27.07%) | USD -842.11 | USD -79,158.40 | USD -4,190.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 94/110 (16) | 72.34% (62.56–80.37%) | USD -94.75 | USD -8,906.80 | USD -7,641.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/110 | 0.00% | USD -96,372.61 | USD -144,665.90 |
| -75% | 0/110 | 0.00% | USD -71,170.09 | USD -107,612.90 |
| -50% | 0/110 | 0.00% | USD -45,967.56 | USD -70,559.90 |
| -40% | 0/110 | 0.00% | USD -35,886.55 | USD -55,738.70 |
| -30% | 0/110 | 0.00% | USD -25,805.55 | USD -40,917.50 |
| -25% | 0/110 | 0.00% | USD -20,765.04 | USD -33,506.90 |
| -20% | 0/110 | 0.00% | USD -15,724.54 | USD -26,096.30 |
| -15% | 0/110 | 0.00% | USD -10,684.03 | USD -18,685.70 |
| -10% | 1/110 | 0.91% | USD -5,641.64 | USD -11,275.10 |
| -5% | 41/110 | 37.27% | USD -671.27 | USD -4,261.00 |
| 0% | 110/110 | 100.00% | USD 819.50 | USD 216.10 |
| 5% | 110/110 | 100.00% | USD 819.50 | USD 216.10 |
| 10% | 110/110 | 100.00% | USD 819.50 | USD 216.10 |
| 20% | 110/110 | 100.00% | USD 819.50 | USD 216.10 |

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