# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: spy_weekly_drop_2pct_corr60_pos — SPY rolling 5-session return crosses from above -2% to <= -2%, with positive Pearson correlation over the prior 60 daily returns; entry no earlier than next observed common session.
- Filter evaluation: 1951 checks; 99 qualified; 1852 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 2 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,089.49 / USD 1,729.27; mean absolute mismatch USD 661.64; mean match score 66.12%.
- Actual selected contract ratios: {'2:6': 99}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 99; entered cohorts: 99; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 98/99 | 76/22/0 | 77.55% (68.34–84.68%) | USD 228.66 | USD 318.60 | USD 22,408.80 | USD -7,598.40 | 1 |
| HOLD_10_SESSIONS | 3/99 | 3/0/0 | 100.00% (43.85–100.00%) | USD 1,040.93 | USD 1,459.60 | USD 3,122.80 | USD 191.60 | 96 |
| HOLD_20_SESSIONS | 0/99 | 0/0/0 | — | — | — | — | — | 99 |
| HOLD_20_OR_DTE_LE_7 | 99/99 | 67/32/0 | 67.68% (57.95–76.08%) | USD -19.01 | USD 239.60 | USD -1,881.60 | USD -18,148.40 | 0 |
| EXIT_AT_DTE_LE_7 | 99/99 | 67/32/0 | 67.68% (57.95–76.08%) | USD -19.01 | USD 239.60 | USD -1,881.60 | USD -18,148.40 | 0 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -289.57 | USD 608.63 |
| HOLD_10_SESSIONS | USD -364.67 | USD 1,496.00 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -154.91 | USD 226.30 |
| EXIT_AT_DTE_LE_7 | USD -154.91 | USD 226.30 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 98 | 83.67% | USD 319.06 | USD 31,268.00 | USD -7,508.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 98 | 83.67% | USD 308.66 | USD 30,248.80 | USD -7,518.40 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 98 | 81.63% | USD 279.06 | USD 27,348.00 | USD -7,548.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 98 | 79.59% | USD 268.66 | USD 26,328.80 | USD -7,558.40 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 98 | 78.57% | USD 239.06 | USD 23,428.00 | USD -7,588.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 98 | 77.55% | USD 228.66 | USD 22,408.80 | USD -7,598.40 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 98 | 71.43% | USD 159.06 | USD 15,588.00 | USD -7,668.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 98 | 70.41% | USD 148.66 | USD 14,568.80 | USD -7,678.40 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 3 | 100.00% | USD 1,131.33 | USD 3,394.00 | USD 282.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 3 | 100.00% | USD 1,120.93 | USD 3,362.80 | USD 271.60 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 3 | 100.00% | USD 1,091.33 | USD 3,274.00 | USD 242.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 3 | 100.00% | USD 1,080.93 | USD 3,242.80 | USD 231.60 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 3 | 100.00% | USD 1,051.33 | USD 3,154.00 | USD 202.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 3 | 100.00% | USD 1,040.93 | USD 3,122.80 | USD 191.60 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 3 | 100.00% | USD 971.33 | USD 2,914.00 | USD 122.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 3 | 100.00% | USD 960.93 | USD 2,882.80 | USD 111.60 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 99 | 75.76% | USD 71.39 | USD 7,068.00 | USD -18,058.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 99 | 75.76% | USD 60.99 | USD 6,038.40 | USD -18,068.40 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 99 | 72.73% | USD 31.39 | USD 3,108.00 | USD -18,098.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 99 | 71.72% | USD 20.99 | USD 2,078.40 | USD -18,108.40 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 99 | 69.70% | USD -8.61 | USD -852.00 | USD -18,138.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 99 | 67.68% | USD -19.01 | USD -1,881.60 | USD -18,148.40 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 99 | 62.63% | USD -88.61 | USD -8,772.00 | USD -18,218.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 99 | 60.61% | USD -99.01 | USD -9,801.60 | USD -18,228.40 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 99 | 75.76% | USD 71.39 | USD 7,068.00 | USD -18,058.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 99 | 75.76% | USD 60.99 | USD 6,038.40 | USD -18,068.40 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 99 | 72.73% | USD 31.39 | USD 3,108.00 | USD -18,098.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 99 | 71.72% | USD 20.99 | USD 2,078.40 | USD -18,108.40 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 99 | 69.70% | USD -8.61 | USD -852.00 | USD -18,138.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 99 | 67.68% | USD -19.01 | USD -1,881.60 | USD -18,148.40 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 99 | 62.63% | USD -88.61 | USD -8,772.00 | USD -18,218.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 99 | 60.61% | USD -99.01 | USD -9,801.60 | USD -18,228.40 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 98/99 (1) | 29.59% (21.46–39.26%) | USD -65.95 | USD -6,462.80 | USD -729.60 |
| HOLD_5_SESSIONS | 1 : 6 | 98/99 (1) | 83.67% (75.11–89.69%) | USD 384.75 | USD 37,705.20 | USD -8,858.10 |
| HOLD_5_SESSIONS | 6 : 1 | 98/99 (1) | 28.57% (20.57–38.19%) | USD -846.38 | USD -82,944.80 | USD -14,124.10 |
| HOLD_5_SESSIONS | 5 : 5 | 98/99 (1) | 29.59% (21.46–39.26%) | USD -329.73 | USD -32,314.00 | USD -3,648.00 |
| HOLD_10_SESSIONS | 1 : 1 | 3/99 (96) | 33.33% (6.15–79.23%) | USD 44.40 | USD 133.20 | USD -251.60 |
| HOLD_10_SESSIONS | 1 : 6 | 3/99 (96) | 100.00% (43.85–100.00%) | USD 1,234.57 | USD 3,703.70 | USD 325.90 |
| HOLD_10_SESSIONS | 6 : 1 | 3/99 (96) | 33.33% (6.15–79.23%) | USD -923.77 | USD -2,771.30 | USD -3,963.10 |
| HOLD_10_SESSIONS | 5 : 5 | 3/99 (96) | 33.33% (6.15–79.23%) | USD 222.00 | USD 666.00 | USD -1,258.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/99 (99) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/99 (99) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/99 (99) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/99 (99) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 99/99 (0) | 28.28% (20.35–37.84%) | USD -62.34 | USD -6,171.40 | USD -627.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 99/99 (0) | 79.80% (70.85–86.52%) | USD 69.75 | USD 6,905.10 | USD -22,419.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 99/99 (0) | 30.30% (22.13–39.95%) | USD -506.11 | USD -50,104.90 | USD -12,159.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 99/99 (0) | 28.28% (20.35–37.84%) | USD -311.69 | USD -30,857.00 | USD -3,138.00 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 99/99 (0) | 28.28% (20.35–37.84%) | USD -62.34 | USD -6,171.40 | USD -627.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 99/99 (0) | 79.80% (70.85–86.52%) | USD 69.75 | USD 6,905.10 | USD -22,419.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 99/99 (0) | 30.30% (22.13–39.95%) | USD -506.11 | USD -50,104.90 | USD -12,159.10 |
| EXIT_AT_DTE_LE_7 | 5 : 5 | 99/99 (0) | 28.28% (20.35–37.84%) | USD -311.69 | USD -30,857.00 | USD -3,138.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/99 | 0.00% | USD -171,464.01 | USD -268,993.20 |
| -75% | 0/99 | 0.00% | USD -126,612.66 | USD -199,796.70 |
| -50% | 0/99 | 0.00% | USD -81,761.31 | USD -130,600.20 |
| -40% | 0/99 | 0.00% | USD -63,820.77 | USD -102,921.60 |
| -30% | 0/99 | 0.00% | USD -45,880.23 | USD -75,243.00 |
| -25% | 0/99 | 0.00% | USD -36,909.96 | USD -61,403.70 |
| -20% | 0/99 | 0.00% | USD -27,939.69 | USD -47,564.40 |
| -15% | 0/99 | 0.00% | USD -18,969.42 | USD -33,725.10 |
| -10% | 2/99 | 2.02% | USD -10,039.02 | USD -19,885.80 |
| -5% | 29/99 | 29.29% | USD -1,506.87 | USD -6,791.50 |
| 0% | 92/99 | 92.93% | USD 733.81 | USD -185.20 |
| 5% | 90/99 | 90.91% | USD 596.99 | USD -465.20 |
| 10% | 90/99 | 90.91% | USD 594.58 | USD -465.20 |
| 20% | 90/99 | 90.91% | USD 594.58 | USD -465.20 |

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