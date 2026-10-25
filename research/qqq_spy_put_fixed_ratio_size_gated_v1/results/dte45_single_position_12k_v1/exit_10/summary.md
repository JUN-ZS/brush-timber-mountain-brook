# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 162 checks; 162 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 437.62 / USD 2,636.11; mean absolute mismatch USD 2,198.49; mean match score 16.51%.
- Actual selected contract ratios: {'1:6': 162}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 162; entered cohorts: 162; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_SESSIONS | 160/162 | 118/42/0 | 73.75% (66.43–79.95%) | USD 141.25 | USD 752.40 | USD 22,600.00 | USD -27,025.10 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_10_SESSIONS | USD -67.65 | USD 288.00 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_SESSIONS | 0.000 | 0.00 | 160 | 75.00% | USD 220.35 | USD 35,256.00 | USD -26,946.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 160 | 74.38% | USD 211.25 | USD 33,800.00 | USD -26,955.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 160 | 73.75% | USD 185.35 | USD 29,656.00 | USD -26,981.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 160 | 73.75% | USD 176.25 | USD 28,200.00 | USD -26,990.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 160 | 73.75% | USD 150.35 | USD 24,056.00 | USD -27,016.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 160 | 73.75% | USD 141.25 | USD 22,600.00 | USD -27,025.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 160 | 73.75% | USD 80.35 | USD 12,856.00 | USD -27,086.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 160 | 73.75% | USD 71.25 | USD 11,400.00 | USD -27,095.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_10_SESSIONS | 1 : 1 | 160/162 (2) | 40.00% (32.73–47.74%) | USD -42.25 | USD -6,760.00 | USD -3,033.60 |
| HOLD_10_SESSIONS | 1 : 6 | 160/162 (2) | 73.75% (66.43–79.95%) | USD 141.25 | USD 22,600.00 | USD -27,025.10 |
| HOLD_10_SESSIONS | 6 : 1 | 160/162 (2) | 23.75% (17.82–30.91%) | USD -437.00 | USD -69,920.00 | USD -6,942.10 |
| HOLD_10_SESSIONS | 5 : 5 | 160/162 (2) | 40.00% (32.73–47.74%) | USD -211.25 | USD -33,800.00 | USD -15,168.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/162 | 0.00% | USD -204,916.33 | USD -333,298.55 |
| -75% | 0/162 | 0.00% | USD -151,011.68 | USD -245,853.30 |
| -50% | 0/162 | 0.00% | USD -97,107.03 | USD -158,408.05 |
| -40% | 0/162 | 0.00% | USD -75,545.17 | USD -123,429.95 |
| -30% | 0/162 | 0.00% | USD -53,983.31 | USD -88,451.85 |
| -25% | 0/162 | 0.00% | USD -43,202.38 | USD -71,093.05 |
| -20% | 1/162 | 0.62% | USD -32,421.45 | USD -54,248.95 |
| -15% | 1/162 | 0.62% | USD -21,681.23 | USD -38,128.80 |
| -10% | 4/162 | 2.47% | USD -10,941.11 | USD -22,538.05 |
| -5% | 69/162 | 42.59% | USD -784.74 | USD -7,363.35 |
| 0% | 162/162 | 100.00% | USD 2,158.94 | USD 589.45 |
| 5% | 162/162 | 100.00% | USD 2,158.94 | USD 589.45 |
| 10% | 162/162 | 100.00% | USD 2,158.94 | USD 589.45 |
| 20% | 162/162 | 100.00% | USD 2,158.94 | USD 589.45 |

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