# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 966 checks; 111 qualified; 855 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 4 : SPY SHORT PUT 5; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,819.75 / USD 2,204.09; mean absolute mismatch USD 432.64; mean match score 79.94%.
- Actual selected contract ratios: {'4:5': 110}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 111; entered cohorts: 110; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 110/110 | 54/56/0 | 49.09% (39.94–58.30%) | USD -132.68 | USD -17.70 | USD -14,595.00 | USD -2,439.70 | 0 |
| HOLD_10_SESSIONS | 109/110 | 60/49/0 | 55.05% (45.69–64.05%) | USD -120.74 | USD 38.30 | USD -13,160.30 | USD -4,602.70 | 1 |
| HOLD_20_SESSIONS | 107/110 | 74/33/0 | 69.16% (59.87–77.12%) | USD -11.93 | USD 166.30 | USD -1,276.90 | USD -4,305.70 | 3 |
| EXIT_AT_DTE_LE_7 | 93/110 | 68/25/0 | 73.12% (63.32–81.08%) | USD -88.31 | USD 193.30 | USD -8,213.10 | USD -7,641.70 | 17 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -240.44 | USD 209.45 |
| HOLD_10_SESSIONS | USD -475.60 | USD 456.56 |
| HOLD_20_SESSIONS | USD -868.41 | USD 958.18 |
| EXIT_AT_DTE_LE_7 | USD -594.19 | USD 607.58 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 110 | 52.73% | USD -30.98 | USD -3,408.00 | USD -2,338.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 110 | 51.82% | USD -42.68 | USD -4,695.00 | USD -2,349.70 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 110 | 51.82% | USD -75.98 | USD -8,358.00 | USD -2,383.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 110 | 51.82% | USD -87.68 | USD -9,645.00 | USD -2,394.70 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 110 | 50.00% | USD -120.98 | USD -13,308.00 | USD -2,428.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 110 | 49.09% | USD -132.68 | USD -14,595.00 | USD -2,439.70 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 110 | 37.27% | USD -210.98 | USD -23,208.00 | USD -2,518.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 110 | 36.36% | USD -222.68 | USD -24,495.00 | USD -2,529.70 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 109 | 65.14% | USD -19.04 | USD -2,075.00 | USD -4,501.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 109 | 65.14% | USD -30.74 | USD -3,350.30 | USD -4,512.70 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 109 | 60.55% | USD -64.04 | USD -6,980.00 | USD -4,546.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 109 | 59.63% | USD -75.74 | USD -8,255.30 | USD -4,557.70 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 109 | 56.88% | USD -109.04 | USD -11,885.00 | USD -4,591.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 109 | 55.05% | USD -120.74 | USD -13,160.30 | USD -4,602.70 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 109 | 43.12% | USD -199.04 | USD -21,695.00 | USD -4,681.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 109 | 40.37% | USD -210.74 | USD -22,970.30 | USD -4,692.70 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 107 | 73.83% | USD 89.77 | USD 9,605.00 | USD -4,204.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 107 | 72.90% | USD 78.07 | USD 8,353.10 | USD -4,215.70 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 107 | 72.90% | USD 44.77 | USD 4,790.00 | USD -4,249.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 107 | 71.96% | USD 33.07 | USD 3,538.10 | USD -4,260.70 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 107 | 71.03% | USD -0.23 | USD -25.00 | USD -4,294.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 107 | 69.16% | USD -11.93 | USD -1,276.90 | USD -4,305.70 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 107 | 60.75% | USD -90.23 | USD -9,655.00 | USD -4,384.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 107 | 58.88% | USD -101.93 | USD -10,906.90 | USD -4,395.70 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 93 | 77.42% | USD 13.39 | USD 1,245.00 | USD -7,540.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 93 | 77.42% | USD 1.69 | USD 156.90 | USD -7,551.70 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 93 | 74.19% | USD -31.61 | USD -2,940.00 | USD -7,585.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 93 | 74.19% | USD -43.31 | USD -4,028.10 | USD -7,596.70 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 93 | 73.12% | USD -76.61 | USD -7,125.00 | USD -7,630.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 93 | 73.12% | USD -88.31 | USD -8,213.10 | USD -7,641.70 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 93 | 61.29% | USD -166.61 | USD -15,495.00 | USD -7,720.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 93 | 60.22% | USD -178.31 | USD -16,583.10 | USD -7,731.70 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 110/110 (0) | 30.00% (22.23–39.12%) | USD -40.82 | USD -4,490.00 | USD -430.60 |
| HOLD_5_SESSIONS | 1 : 6 | 110/110 (0) | 60.00% (50.66–68.67%) | USD 112.14 | USD 12,335.00 | USD -4,827.10 |
| HOLD_5_SESSIONS | 6 : 1 | 110/110 (0) | 30.00% (22.23–39.12%) | USD -397.86 | USD -43,765.00 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 110/110 (0) | 49.09% (39.94–58.30%) | USD -132.68 | USD -14,595.00 | USD -2,439.70 |
| HOLD_10_SESSIONS | 1 : 1 | 109/110 (1) | 31.19% (23.26–40.40%) | USD -50.19 | USD -5,470.40 | USD -790.60 |
| HOLD_10_SESSIONS | 1 : 6 | 109/110 (1) | 76.15% (67.34–83.17%) | USD 349.87 | USD 38,136.10 | USD -10,501.10 |
| HOLD_10_SESSIONS | 6 : 1 | 109/110 (1) | 18.35% (12.20–26.65%) | USD -701.18 | USD -76,428.90 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 109/110 (1) | 55.05% (45.69–64.05%) | USD -120.74 | USD -13,160.30 | USD -4,602.70 |
| HOLD_20_SESSIONS | 1 : 1 | 107/110 (3) | 35.51% (27.09–44.94%) | USD -48.07 | USD -5,143.20 | USD -792.60 |
| HOLD_20_SESSIONS | 1 : 6 | 107/110 (3) | 81.31% (72.89–87.56%) | USD 853.61 | USD 91,336.30 | USD -9,376.10 |
| HOLD_20_SESSIONS | 6 : 1 | 107/110 (3) | 17.76% (11.67–26.08%) | USD -1,190.08 | USD -127,338.70 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 107/110 (3) | 69.16% (59.87–77.12%) | USD -11.93 | USD -1,276.90 | USD -4,305.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 93/110 (17) | 35.48% (26.51–45.61%) | USD -49.63 | USD -4,615.80 | USD -952.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 93/110 (17) | 81.72% (72.66–88.26%) | USD 501.45 | USD 46,634.70 | USD -20,318.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 93/110 (17) | 18.28% (11.74–27.34%) | USD -848.87 | USD -78,945.30 | USD -4,190.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 93/110 (17) | 73.12% (63.32–81.08%) | USD -88.31 | USD -8,213.10 | USD -7,641.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/110 | 0.00% | USD -74,384.81 | USD -94,322.85 |
| -75% | 0/110 | 0.00% | USD -55,223.28 | USD -70,290.60 |
| -50% | 0/110 | 0.00% | USD -36,061.75 | USD -46,850.35 |
| -40% | 0/110 | 0.00% | USD -28,397.14 | USD -37,653.85 |
| -30% | 0/110 | 0.00% | USD -20,732.52 | USD -28,457.35 |
| -25% | 0/110 | 0.00% | USD -16,900.22 | USD -23,859.10 |
| -20% | 0/110 | 0.00% | USD -13,067.91 | USD -19,260.85 |
| -15% | 0/110 | 0.00% | USD -9,235.61 | USD -14,662.60 |
| -10% | 1/110 | 0.91% | USD -5,396.27 | USD -10,064.35 |
| -5% | 34/110 | 30.91% | USD -1,260.12 | USD -5,466.10 |
| 0% | 95/110 | 86.36% | USD 333.50 | USD -990.85 |
| 5% | 95/110 | 86.36% | USD 333.50 | USD -990.85 |
| 10% | 95/110 | 86.36% | USD 333.50 | USD -990.85 |
| 20% | 95/110 | 86.36% | USD 333.50 | USD -990.85 |

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