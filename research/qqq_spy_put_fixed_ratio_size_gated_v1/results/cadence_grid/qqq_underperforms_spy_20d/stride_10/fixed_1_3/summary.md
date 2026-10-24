# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 966 checks; 111 qualified; 855 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 456.82 / USD 1,319.97; mean absolute mismatch USD 863.15; mean match score 34.21%.
- Actual selected contract ratios: {'1:3': 110}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 111; entered cohorts: 110; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 110/110 | 64/46/0 | 58.18% (48.84–66.97%) | USD 2.42 | USD 116.80 | USD 266.00 | USD -2,117.20 | 0 |
| HOLD_10_SESSIONS | 109/110 | 83/26/0 | 76.15% (67.34–83.17%) | USD 97.74 | USD 326.80 | USD 10,654.20 | USD -4,203.20 | 1 |
| HOLD_20_SESSIONS | 107/110 | 86/21/0 | 80.37% (71.85–86.79%) | USD 319.04 | USD 520.80 | USD 34,137.60 | USD -3,960.20 | 3 |
| EXIT_AT_DTE_LE_7 | 94/110 | 75/19/0 | 79.79% (70.57–86.66%) | USD 174.31 | USD 617.80 | USD 16,385.20 | USD -8,692.20 | 16 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -57.35 | USD 104.97 |
| HOLD_10_SESSIONS | USD -116.24 | USD 259.18 |
| HOLD_20_SESSIONS | USD -219.05 | USD 583.29 |
| EXIT_AT_DTE_LE_7 | USD -155.43 | USD 374.94 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 110 | 60.91% | USD 47.62 | USD 5,238.00 | USD -2,072.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 110 | 60.91% | USD 42.42 | USD 4,666.00 | USD -2,077.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 110 | 58.18% | USD 27.62 | USD 3,038.00 | USD -2,092.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 110 | 58.18% | USD 22.42 | USD 2,466.00 | USD -2,097.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 110 | 58.18% | USD 7.62 | USD 838.00 | USD -2,112.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 110 | 58.18% | USD 2.42 | USD 266.00 | USD -2,117.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 110 | 56.36% | USD -32.38 | USD -3,562.00 | USD -2,152.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 110 | 56.36% | USD -37.58 | USD -4,134.00 | USD -2,157.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 109 | 76.15% | USD 142.94 | USD 15,581.00 | USD -4,158.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 109 | 76.15% | USD 137.74 | USD 15,014.20 | USD -4,163.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 109 | 76.15% | USD 122.94 | USD 13,401.00 | USD -4,178.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 109 | 76.15% | USD 117.74 | USD 12,834.20 | USD -4,183.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 109 | 76.15% | USD 102.94 | USD 11,221.00 | USD -4,198.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 109 | 76.15% | USD 97.74 | USD 10,654.20 | USD -4,203.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 109 | 76.15% | USD 62.94 | USD 6,861.00 | USD -4,238.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 109 | 74.31% | USD 57.74 | USD 6,294.20 | USD -4,243.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 107 | 81.31% | USD 364.24 | USD 38,974.00 | USD -3,915.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 107 | 81.31% | USD 359.04 | USD 38,417.60 | USD -3,920.20 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 107 | 81.31% | USD 344.24 | USD 36,834.00 | USD -3,935.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 107 | 81.31% | USD 339.04 | USD 36,277.60 | USD -3,940.20 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 107 | 81.31% | USD 324.24 | USD 34,694.00 | USD -3,955.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 107 | 80.37% | USD 319.04 | USD 34,137.60 | USD -3,960.20 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 107 | 80.37% | USD 284.24 | USD 30,414.00 | USD -3,995.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 107 | 80.37% | USD 279.04 | USD 29,857.60 | USD -4,000.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 94 | 79.79% | USD 219.51 | USD 20,634.00 | USD -8,647.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 94 | 79.79% | USD 214.31 | USD 20,145.20 | USD -8,652.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 94 | 79.79% | USD 199.51 | USD 18,754.00 | USD -8,667.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 94 | 79.79% | USD 194.31 | USD 18,265.20 | USD -8,672.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 94 | 79.79% | USD 179.51 | USD 16,874.00 | USD -8,687.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 94 | 79.79% | USD 174.31 | USD 16,385.20 | USD -8,692.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 94 | 79.79% | USD 139.51 | USD 13,114.00 | USD -8,727.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 94 | 79.79% | USD 134.31 | USD 12,625.20 | USD -8,732.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 110/110 (0) | 29.09% (21.42–38.17%) | USD -44.96 | USD -4,946.00 | USD -430.60 |
| HOLD_5_SESSIONS | 1 : 6 | 110/110 (0) | 60.00% (50.66–68.67%) | USD 73.49 | USD 8,084.00 | USD -4,827.10 |
| HOLD_5_SESSIONS | 6 : 1 | 110/110 (0) | 30.91% (23.04–40.07%) | USD -388.24 | USD -42,706.00 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 110/110 (0) | 47.27% (38.19–56.54%) | USD -156.16 | USD -17,178.00 | USD -2,439.70 |
| HOLD_10_SESSIONS | 1 : 1 | 109/110 (1) | 31.19% (23.26–40.40%) | USD -52.44 | USD -5,716.40 | USD -790.60 |
| HOLD_10_SESSIONS | 1 : 6 | 109/110 (1) | 75.23% (66.36–82.38%) | USD 323.03 | USD 35,210.10 | USD -10,453.10 |
| HOLD_10_SESSIONS | 6 : 1 | 109/110 (1) | 18.35% (12.20–26.65%) | USD -690.14 | USD -75,224.90 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 109/110 (1) | 53.21% (43.89–62.31%) | USD -134.68 | USD -14,680.30 | USD -4,602.70 |
| HOLD_20_SESSIONS | 1 : 1 | 107/110 (3) | 36.45% (27.95–45.89%) | USD -47.22 | USD -5,052.20 | USD -792.60 |
| HOLD_20_SESSIONS | 1 : 6 | 107/110 (3) | 80.37% (71.85–86.79%) | USD 868.43 | USD 92,922.30 | USD -9,376.10 |
| HOLD_20_SESSIONS | 6 : 1 | 107/110 (3) | 17.76% (11.67–26.08%) | USD -1,198.95 | USD -128,287.70 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 107/110 (3) | 69.16% (59.87–77.12%) | USD -5.74 | USD -613.90 | USD -4,305.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 94/110 (16) | 35.11% (26.22–45.17%) | USD -53.05 | USD -4,986.40 | USD -952.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 94/110 (16) | 81.91% (72.93–88.39%) | USD 515.35 | USD 48,442.60 | USD -20,318.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 94/110 (16) | 18.09% (11.61–27.07%) | USD -886.67 | USD -83,347.40 | USD -4,190.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 94/110 (16) | 72.34% (62.56–80.37%) | USD -98.51 | USD -9,259.80 | USD -7,641.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/110 | 0.00% | USD -87,644.14 | USD -137,768.60 |
| -75% | 0/110 | 0.00% | USD -64,626.74 | USD -102,177.60 |
| -50% | 0/110 | 0.00% | USD -41,609.34 | USD -66,586.60 |
| -40% | 0/110 | 0.00% | USD -32,402.38 | USD -52,350.20 |
| -30% | 0/110 | 0.00% | USD -23,195.42 | USD -38,113.80 |
| -25% | 0/110 | 0.00% | USD -18,591.94 | USD -30,995.60 |
| -20% | 0/110 | 0.00% | USD -13,988.46 | USD -23,877.40 |
| -15% | 0/110 | 0.00% | USD -9,384.98 | USD -16,759.20 |
| -10% | 1/110 | 0.91% | USD -4,781.64 | USD -9,744.10 |
| -5% | 46/110 | 41.82% | USD -359.87 | USD -3,798.85 |
| 0% | 110/110 | 100.00% | USD 840.55 | USD 228.40 |
| 5% | 110/110 | 100.00% | USD 840.55 | USD 228.40 |
| 10% | 110/110 | 100.00% | USD 840.55 | USD 228.40 |
| 20% | 110/110 | 100.00% | USD 840.55 | USD 228.40 |

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