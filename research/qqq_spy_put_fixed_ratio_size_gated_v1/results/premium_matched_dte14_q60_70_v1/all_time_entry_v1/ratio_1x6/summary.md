# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 1908 checks; 1908 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 909.19 / USD 1,362.67; mean absolute mismatch USD 482.16; mean match score 69.57%.
- Actual selected contract ratios: {'1:6': 1907}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 1908; entered cohorts: 1907; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1896/1907 | 1443/453/0 | 76.11% (74.14–77.97%) | USD 35.48 | USD 277.40 | USD 67,269.40 | USD -21,727.10 | 11 |
| HOLD_10_SESSIONS | 175/1907 | 149/26/0 | 85.14% (79.12–89.66%) | USD -333.39 | USD 427.90 | USD -58,342.50 | USD -32,965.10 | 1732 |
| HOLD_20_SESSIONS | 0/1907 | 0/0/0 | — | — | — | — | — | 1907 |
| HOLD_20_OR_DTE_LE_7 | 1903/1907 | 1398/505/0 | 73.46% (71.43–75.40%) | USD -25.06 | USD 253.90 | USD -47,698.30 | USD -26,768.10 | 4 |
| EXIT_AT_DTE_LE_7 | 1903/1907 | 1398/505/0 | 73.46% (71.43–75.40%) | USD -25.06 | USD 253.90 | USD -47,698.30 | USD -26,768.10 | 4 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -146.22 | USD 260.80 |
| HOLD_10_SESSIONS | USD -86.29 | USD -168.00 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -120.70 | USD 174.74 |
| EXIT_AT_DTE_LE_7 | USD -120.70 | USD 174.74 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 1896 | 81.17% | USD 114.58 | USD 217,243.00 | USD -21,648.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 1896 | 80.80% | USD 105.48 | USD 199,989.40 | USD -21,657.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 1896 | 79.43% | USD 79.58 | USD 150,883.00 | USD -21,683.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 1896 | 78.90% | USD 70.48 | USD 133,629.40 | USD -21,692.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 1896 | 76.85% | USD 44.58 | USD 84,523.00 | USD -21,718.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 1896 | 76.11% | USD 35.48 | USD 67,269.40 | USD -21,727.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 1896 | 71.04% | USD -25.42 | USD -48,197.00 | USD -21,788.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 1896 | 70.41% | USD -34.52 | USD -65,450.60 | USD -21,797.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 175 | 85.14% | USD -254.29 | USD -44,500.00 | USD -32,886.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 175 | 85.14% | USD -263.39 | USD -46,092.50 | USD -32,895.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 175 | 85.14% | USD -289.29 | USD -50,625.00 | USD -32,921.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 175 | 85.14% | USD -298.39 | USD -52,217.50 | USD -32,930.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 175 | 85.14% | USD -324.29 | USD -56,750.00 | USD -32,956.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 175 | 85.14% | USD -333.39 | USD -58,342.50 | USD -32,965.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 175 | 84.57% | USD -394.29 | USD -69,000.00 | USD -33,026.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 175 | 84.00% | USD -403.39 | USD -70,592.50 | USD -33,035.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 1903 | 78.46% | USD 54.04 | USD 102,829.00 | USD -26,689.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 1903 | 78.14% | USD 44.94 | USD 85,511.70 | USD -26,698.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 1903 | 76.77% | USD 19.04 | USD 36,224.00 | USD -26,724.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 1903 | 76.25% | USD 9.94 | USD 18,906.70 | USD -26,733.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 1903 | 74.36% | USD -15.96 | USD -30,381.00 | USD -26,759.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 1903 | 73.46% | USD -25.06 | USD -47,698.30 | USD -26,768.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 1903 | 68.42% | USD -85.96 | USD -163,591.00 | USD -26,829.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 1903 | 67.47% | USD -95.06 | USD -180,908.30 | USD -26,838.10 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 1903 | 78.46% | USD 54.04 | USD 102,829.00 | USD -26,689.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 1903 | 78.14% | USD 44.94 | USD 85,511.70 | USD -26,698.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 1903 | 76.77% | USD 19.04 | USD 36,224.00 | USD -26,724.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 1903 | 76.25% | USD 9.94 | USD 18,906.70 | USD -26,733.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 1903 | 74.36% | USD -15.96 | USD -30,381.00 | USD -26,759.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 1903 | 73.46% | USD -25.06 | USD -47,698.30 | USD -26,768.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 1903 | 68.42% | USD -85.96 | USD -163,591.00 | USD -26,829.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 1903 | 67.47% | USD -95.06 | USD -180,908.30 | USD -26,838.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 1896/1907 (11) | 32.91% (30.83–35.06%) | USD -125.35 | USD -237,666.60 | USD -2,271.60 |
| HOLD_5_SESSIONS | 1 : 6 | 1896/1907 (11) | 76.11% (74.14–77.97%) | USD 35.48 | USD 67,269.40 | USD -21,727.10 |
| HOLD_5_SESSIONS | 6 : 1 | 1896/1907 (11) | 31.01% (28.97–33.13%) | USD -912.94 | USD -1,730,935.60 | USD -18,738.10 |
| HOLD_5_SESSIONS | 5 : 5 | 1896/1907 (11) | 32.91% (30.83–35.06%) | USD -626.76 | USD -1,188,333.00 | USD -11,358.00 |
| HOLD_10_SESSIONS | 1 : 1 | 175/1907 (1732) | 30.29% (23.96–37.46%) | USD -136.89 | USD -23,955.00 | USD -2,398.60 |
| HOLD_10_SESSIONS | 1 : 6 | 175/1907 (1732) | 85.14% (79.12–89.66%) | USD -333.39 | USD -58,342.50 | USD -32,965.10 |
| HOLD_10_SESSIONS | 6 : 1 | 175/1907 (1732) | 30.29% (23.96–37.46%) | USD -624.81 | USD -109,342.50 | USD -10,574.10 |
| HOLD_10_SESSIONS | 5 : 5 | 175/1907 (1732) | 30.29% (23.96–37.46%) | USD -684.43 | USD -119,775.00 | USD -11,993.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/1907 (1907) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/1907 (1907) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/1907 (1907) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/1907 (1907) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 1903/1907 (4) | 32.32% (30.25–34.45%) | USD -114.18 | USD -217,283.80 | USD -2,294.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 1903/1907 (4) | 73.46% (71.43–75.40%) | USD -25.06 | USD -47,698.30 | USD -26,768.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 1903/1907 (4) | 31.21% (29.17–33.33%) | USD -774.19 | USD -1,473,288.30 | USD -17,581.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 1903/1907 (4) | 32.32% (30.25–34.45%) | USD -570.90 | USD -1,086,419.00 | USD -11,473.00 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 1903/1907 (4) | 32.32% (30.25–34.45%) | USD -114.18 | USD -217,283.80 | USD -2,294.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 1903/1907 (4) | 73.46% (71.43–75.40%) | USD -25.06 | USD -47,698.30 | USD -26,768.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 1903/1907 (4) | 31.21% (29.17–33.33%) | USD -774.19 | USD -1,473,288.30 | USD -17,581.10 |
| EXIT_AT_DTE_LE_7 | 5 : 5 | 1903/1907 (4) | 32.32% (30.25–34.45%) | USD -570.90 | USD -1,086,419.00 | USD -11,473.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/1907 | 0.00% | USD -209,495.98 | USD -341,670.55 |
| -75% | 0/1907 | 0.00% | USD -155,405.49 | USD -254,747.05 |
| -50% | 0/1907 | 0.00% | USD -101,315.01 | USD -167,823.55 |
| -40% | 0/1907 | 0.00% | USD -79,678.81 | USD -133,054.15 |
| -30% | 0/1907 | 0.00% | USD -58,042.62 | USD -98,365.45 |
| -25% | 0/1907 | 0.00% | USD -47,224.52 | USD -81,100.80 |
| -20% | 2/1907 | 0.10% | USD -36,406.42 | USD -64,439.95 |
| -15% | 4/1907 | 0.21% | USD -25,593.23 | USD -47,796.85 |
| -10% | 18/1907 | 0.94% | USD -14,795.72 | USD -31,153.75 |
| -5% | 240/1907 | 12.59% | USD -4,146.68 | USD -14,510.65 |
| 0% | 1872/1907 | 98.16% | USD 1,038.91 | USD -219.55 |
| 5% | 1611/1907 | 84.48% | USD 438.68 | USD -1,189.55 |
| 10% | 1609/1907 | 84.37% | USD 415.92 | USD -1,189.55 |
| 20% | 1609/1907 | 84.37% | USD 413.93 | USD -1,189.55 |

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