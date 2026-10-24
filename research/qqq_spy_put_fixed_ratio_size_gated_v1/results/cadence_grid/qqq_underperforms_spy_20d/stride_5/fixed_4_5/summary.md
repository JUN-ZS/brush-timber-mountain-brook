# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 1164 checks; 199 qualified; 965 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 4 : SPY SHORT PUT 5; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,842.42 / USD 2,268.06; mean absolute mismatch USD 459.59; mean match score 79.29%.
- Actual selected contract ratios: {'4:5': 198}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 199; entered cohorts: 198; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 197/198 | 100/97/0 | 50.76% (43.83–57.66%) | USD -117.10 | USD 12.30 | USD -23,068.90 | USD -3,488.70 | 1 |
| HOLD_10_SESSIONS | 195/198 | 107/88/0 | 54.87% (47.86–61.69%) | USD -109.15 | USD 33.30 | USD -21,284.50 | USD -4,602.70 | 3 |
| HOLD_20_SESSIONS | 192/198 | 135/57/0 | 70.31% (63.50–76.33%) | USD 22.76 | USD 184.30 | USD 4,369.60 | USD -4,305.70 | 6 |
| EXIT_AT_DTE_LE_7 | 170/198 | 124/46/0 | 72.94% (65.81–79.06%) | USD -0.17 | USD 231.80 | USD -29.00 | USD -7,641.70 | 28 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -275.05 | USD 259.64 |
| HOLD_10_SESSIONS | USD -442.40 | USD 434.95 |
| HOLD_20_SESSIONS | USD -779.71 | USD 904.17 |
| EXIT_AT_DTE_LE_7 | USD -797.53 | USD 899.06 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 197 | 55.84% | USD -15.40 | USD -3,034.00 | USD -3,387.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 197 | 55.84% | USD -27.10 | USD -5,338.90 | USD -3,398.70 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 197 | 55.33% | USD -60.40 | USD -11,899.00 | USD -3,432.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 197 | 54.31% | USD -72.10 | USD -14,203.90 | USD -3,443.70 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 197 | 51.27% | USD -105.40 | USD -20,764.00 | USD -3,477.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 197 | 50.76% | USD -117.10 | USD -23,068.90 | USD -3,488.70 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 197 | 38.07% | USD -195.40 | USD -38,494.00 | USD -3,567.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 197 | 36.55% | USD -207.10 | USD -40,798.90 | USD -3,578.70 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 195 | 63.08% | USD -7.45 | USD -1,453.00 | USD -4,501.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 195 | 62.56% | USD -19.15 | USD -3,734.50 | USD -4,512.70 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 195 | 58.46% | USD -52.45 | USD -10,228.00 | USD -4,546.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 195 | 57.44% | USD -64.15 | USD -12,509.50 | USD -4,557.70 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 195 | 55.90% | USD -97.45 | USD -19,003.00 | USD -4,591.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 195 | 54.87% | USD -109.15 | USD -21,284.50 | USD -4,602.70 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 195 | 44.62% | USD -187.45 | USD -36,553.00 | USD -4,681.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 195 | 43.08% | USD -199.15 | USD -38,834.50 | USD -4,692.70 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 192 | 73.44% | USD 124.46 | USD 23,896.00 | USD -4,204.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 192 | 73.44% | USD 112.76 | USD 21,649.60 | USD -4,215.70 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 192 | 72.92% | USD 79.46 | USD 15,256.00 | USD -4,249.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 192 | 71.88% | USD 67.76 | USD 13,009.60 | USD -4,260.70 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 192 | 71.88% | USD 34.46 | USD 6,616.00 | USD -4,294.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 192 | 70.31% | USD 22.76 | USD 4,369.60 | USD -4,305.70 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 192 | 62.50% | USD -55.54 | USD -10,664.00 | USD -4,384.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 192 | 60.94% | USD -67.24 | USD -12,910.40 | USD -4,395.70 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 170 | 78.24% | USD 101.53 | USD 17,260.00 | USD -7,540.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 170 | 77.65% | USD 89.83 | USD 15,271.00 | USD -7,551.70 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 170 | 75.29% | USD 56.53 | USD 9,610.00 | USD -7,585.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 170 | 74.71% | USD 44.83 | USD 7,621.00 | USD -7,596.70 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 170 | 72.94% | USD 11.53 | USD 1,960.00 | USD -7,630.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 170 | 72.94% | USD -0.17 | USD -29.00 | USD -7,641.70 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 170 | 64.12% | USD -78.47 | USD -13,340.00 | USD -7,720.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 170 | 62.94% | USD -90.17 | USD -15,329.00 | USD -7,731.70 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 197/198 (1) | 31.98% (25.86–38.78%) | USD -39.43 | USD -7,768.20 | USD -544.60 |
| HOLD_5_SESSIONS | 1 : 6 | 197/198 (1) | 64.97% (58.08–71.29%) | USD 163.71 | USD 32,251.30 | USD -7,267.10 |
| HOLD_5_SESSIONS | 6 : 1 | 197/198 (1) | 28.93% (23.05–35.62%) | USD -439.74 | USD -86,628.70 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 197/198 (1) | 50.76% (43.83–57.66%) | USD -117.10 | USD -23,068.90 | USD -3,488.70 |
| HOLD_10_SESSIONS | 1 : 1 | 195/198 (3) | 30.26% (24.24–37.03%) | USD -46.21 | USD -9,011.00 | USD -790.60 |
| HOLD_10_SESSIONS | 1 : 6 | 195/198 (3) | 75.38% (68.89–80.90%) | USD 332.24 | USD 64,786.50 | USD -10,501.10 |
| HOLD_10_SESSIONS | 6 : 1 | 195/198 (3) | 20.51% (15.44–26.72%) | USD -655.71 | USD -127,863.50 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 195/198 (3) | 54.87% (47.86–61.69%) | USD -109.15 | USD -21,284.50 | USD -4,602.70 |
| HOLD_20_SESSIONS | 1 : 1 | 192/198 (6) | 39.06% (32.44–46.11%) | USD -36.69 | USD -7,045.20 | USD -792.60 |
| HOLD_20_SESSIONS | 1 : 6 | 192/198 (6) | 81.25% (75.14–86.14%) | USD 810.97 | USD 155,706.80 | USD -11,587.10 |
| HOLD_20_SESSIONS | 6 : 1 | 192/198 (6) | 16.15% (11.61–22.01%) | USD -1,067.83 | USD -205,023.20 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 192/198 (6) | 70.31% (63.50–76.33%) | USD 22.76 | USD 4,369.60 | USD -4,305.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 170/198 (28) | 38.24% (31.27–45.72%) | USD -42.17 | USD -7,169.00 | USD -952.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 170/198 (28) | 81.18% (74.64–86.34%) | USD 800.39 | USD 136,066.00 | USD -20,318.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 170/198 (28) | 18.24% (13.15–24.72%) | USD -1,095.58 | USD -186,249.00 | USD -5,483.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 170/198 (28) | 72.94% (65.81–79.06%) | USD -0.17 | USD -29.00 | USD -7,641.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/198 | 0.00% | USD -74,369.48 | USD -94,322.85 |
| -75% | 0/198 | 0.00% | USD -55,220.57 | USD -70,290.60 |
| -50% | 0/198 | 0.00% | USD -36,071.67 | USD -46,850.35 |
| -40% | 0/198 | 0.00% | USD -28,412.10 | USD -37,653.85 |
| -30% | 0/198 | 0.00% | USD -20,752.54 | USD -28,457.35 |
| -25% | 0/198 | 0.00% | USD -16,922.76 | USD -23,859.10 |
| -20% | 0/198 | 0.00% | USD -13,092.98 | USD -19,260.85 |
| -15% | 0/198 | 0.00% | USD -9,263.19 | USD -14,662.60 |
| -10% | 1/198 | 0.51% | USD -5,430.35 | USD -10,064.35 |
| -5% | 66/198 | 33.33% | USD -1,255.18 | USD -5,466.10 |
| 0% | 174/198 | 87.88% | USD 378.05 | USD -990.85 |
| 5% | 174/198 | 87.88% | USD 374.78 | USD -990.85 |
| 10% | 174/198 | 87.88% | USD 374.78 | USD -990.85 |
| 20% | 174/198 | 87.88% | USD 374.78 | USD -990.85 |

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