# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 518 checks; 50 qualified; 468 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 4 : SPY SHORT PUT 5; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,820.72 / USD 2,200.70; mean absolute mismatch USD 426.02; mean match score 80.21%.
- Actual selected contract ratios: {'4:5': 50}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 50; entered cohorts: 50; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 50/50 | 22/28/0 | 44.00% (31.16–57.69%) | USD -211.58 | USD -41.70 | USD -10,579.00 | USD -2,682.70 | 0 |
| HOLD_10_SESSIONS | 50/50 | 24/26/0 | 48.00% (34.80–61.49%) | USD -253.38 | USD -58.70 | USD -12,669.00 | USD -3,618.70 | 0 |
| HOLD_20_SESSIONS | 49/50 | 34/15/0 | 69.39% (55.47–80.48%) | USD -179.62 | USD 161.30 | USD -8,801.30 | USD -3,856.70 | 1 |
| EXIT_AT_DTE_LE_7 | 47/50 | 36/11/0 | 76.60% (62.78–86.40%) | USD -261.59 | USD 207.30 | USD -12,294.90 | USD -7,641.70 | 3 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 120.72 | USD -230.60 |
| HOLD_10_SESSIONS | USD -288.08 | USD 136.40 |
| HOLD_20_SESSIONS | USD -860.98 | USD 783.06 |
| EXIT_AT_DTE_LE_7 | USD -792.34 | USD 632.45 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 50 | 56.00% | USD -109.88 | USD -5,494.00 | USD -2,581.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 50 | 54.00% | USD -121.58 | USD -6,079.00 | USD -2,592.70 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 50 | 52.00% | USD -154.88 | USD -7,744.00 | USD -2,626.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 50 | 50.00% | USD -166.58 | USD -8,329.00 | USD -2,637.70 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 50 | 46.00% | USD -199.88 | USD -9,994.00 | USD -2,671.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 50 | 44.00% | USD -211.58 | USD -10,579.00 | USD -2,682.70 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 50 | 34.00% | USD -289.88 | USD -14,494.00 | USD -2,761.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 50 | 34.00% | USD -301.58 | USD -15,079.00 | USD -2,772.70 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 50 | 58.00% | USD -151.68 | USD -7,584.00 | USD -3,517.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 50 | 56.00% | USD -163.38 | USD -8,169.00 | USD -3,528.70 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 50 | 48.00% | USD -196.68 | USD -9,834.00 | USD -3,562.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 50 | 48.00% | USD -208.38 | USD -10,419.00 | USD -3,573.70 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 50 | 48.00% | USD -241.68 | USD -12,084.00 | USD -3,607.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 50 | 48.00% | USD -253.38 | USD -12,669.00 | USD -3,618.70 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 50 | 40.00% | USD -331.68 | USD -16,584.00 | USD -3,697.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 50 | 38.00% | USD -343.38 | USD -17,169.00 | USD -3,708.70 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 49 | 73.47% | USD -77.92 | USD -3,818.00 | USD -3,755.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 49 | 71.43% | USD -89.62 | USD -4,391.30 | USD -3,766.70 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 49 | 71.43% | USD -122.92 | USD -6,023.00 | USD -3,800.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 49 | 71.43% | USD -134.62 | USD -6,596.30 | USD -3,811.70 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 49 | 71.43% | USD -167.92 | USD -8,228.00 | USD -3,845.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 49 | 69.39% | USD -179.62 | USD -8,801.30 | USD -3,856.70 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 49 | 53.06% | USD -257.92 | USD -12,638.00 | USD -3,935.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 49 | 53.06% | USD -269.62 | USD -13,211.30 | USD -3,946.70 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 47 | 78.72% | USD -159.89 | USD -7,515.00 | USD -7,540.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 47 | 78.72% | USD -171.59 | USD -8,064.90 | USD -7,551.70 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 47 | 78.72% | USD -204.89 | USD -9,630.00 | USD -7,585.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 47 | 78.72% | USD -216.59 | USD -10,179.90 | USD -7,596.70 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 47 | 76.60% | USD -249.89 | USD -11,745.00 | USD -7,630.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 47 | 76.60% | USD -261.59 | USD -12,294.90 | USD -7,641.70 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 47 | 63.83% | USD -339.89 | USD -15,975.00 | USD -7,720.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 47 | 63.83% | USD -351.59 | USD -16,524.90 | USD -7,731.70 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 50/50 (0) | 36.00% (24.14–49.86%) | USD -38.54 | USD -1,927.00 | USD -433.60 |
| HOLD_5_SESSIONS | 1 : 6 | 50/50 (0) | 50.00% (36.64–63.36%) | USD -325.64 | USD -16,282.00 | USD -5,175.10 |
| HOLD_5_SESSIONS | 6 : 1 | 50/50 (0) | 34.00% (22.44–47.85%) | USD 55.86 | USD 2,793.00 | USD -2,966.10 |
| HOLD_5_SESSIONS | 4 : 5 | 50/50 (0) | 44.00% (31.16–57.69%) | USD -211.58 | USD -10,579.00 | USD -2,682.70 |
| HOLD_10_SESSIONS | 1 : 1 | 50/50 (0) | 28.00% (17.47–41.67%) | USD -67.34 | USD -3,367.00 | USD -595.60 |
| HOLD_10_SESSIONS | 1 : 6 | 50/50 (0) | 70.00% (56.25–80.90%) | USD 12.56 | USD 628.00 | USD -7,969.10 |
| HOLD_10_SESSIONS | 6 : 1 | 50/50 (0) | 26.00% (15.87–39.55%) | USD -483.94 | USD -24,197.00 | USD -4,023.10 |
| HOLD_10_SESSIONS | 4 : 5 | 50/50 (0) | 48.00% (34.80–61.49%) | USD -253.38 | USD -12,669.00 | USD -3,618.70 |
| HOLD_20_SESSIONS | 1 : 1 | 49/50 (1) | 22.45% (13.03–35.88%) | USD -81.23 | USD -3,980.40 | USD -590.60 |
| HOLD_20_SESSIONS | 1 : 6 | 49/50 (1) | 79.59% (66.36–88.52%) | USD 645.33 | USD 31,621.10 | USD -9,449.10 |
| HOLD_20_SESSIONS | 6 : 1 | 49/50 (1) | 16.33% (8.51–29.04%) | USD -1,213.96 | USD -59,483.90 | USD -3,733.10 |
| HOLD_20_SESSIONS | 4 : 5 | 49/50 (1) | 69.39% (55.47–80.48%) | USD -179.62 | USD -8,801.30 | USD -3,856.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 47/50 (3) | 29.79% (18.65–43.98%) | USD -94.20 | USD -4,427.20 | USD -1,279.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 47/50 (3) | 87.23% (74.83–94.02%) | USD 481.75 | USD 22,642.30 | USD -20,318.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 47/50 (3) | 10.64% (4.63–22.59%) | USD -1,141.12 | USD -53,632.70 | USD -3,792.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 47/50 (3) | 76.60% (62.78–86.40%) | USD -261.59 | USD -12,294.90 | USD -7,641.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/50 | 0.00% | USD -74,083.63 | USD -96,088.85 |
| -75% | 0/50 | 0.00% | USD -54,990.14 | USD -72,164.10 |
| -50% | 0/50 | 0.00% | USD -35,896.65 | USD -48,239.35 |
| -40% | 0/50 | 0.00% | USD -28,259.25 | USD -38,669.45 |
| -30% | 0/50 | 0.00% | USD -20,621.86 | USD -29,099.55 |
| -25% | 0/50 | 0.00% | USD -16,803.16 | USD -24,314.60 |
| -20% | 0/50 | 0.00% | USD -12,984.46 | USD -19,529.65 |
| -15% | 0/50 | 0.00% | USD -9,165.76 | USD -14,744.70 |
| -10% | 1/50 | 2.00% | USD -5,335.13 | USD -9,959.75 |
| -5% | 16/50 | 32.00% | USD -1,494.67 | USD -5,174.80 |
| 0% | 45/50 | 90.00% | USD 329.13 | USD -990.85 |
| 5% | 45/50 | 90.00% | USD 329.13 | USD -990.85 |
| 10% | 45/50 | 90.00% | USD 329.13 | USD -990.85 |
| 20% | 45/50 | 90.00% | USD 329.13 | USD -990.85 |

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