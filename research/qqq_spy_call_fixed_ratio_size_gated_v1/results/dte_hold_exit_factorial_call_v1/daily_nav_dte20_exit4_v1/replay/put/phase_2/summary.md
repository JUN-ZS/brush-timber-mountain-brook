# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 14–26 (target 20); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 302.45 / USD 1,766.83; mean absolute mismatch USD 1,464.38; mean match score 17.11%.
- Actual selected contract ratios: {'1:6': 195}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 195; entered cohorts: 195; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 180/195 | 149/31/0 | 82.78% (76.59–87.59%) | USD 79.65 | USD 817.90 | USD 14,337.00 | USD -25,101.10 | 15 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| EXIT_AT_DTE_LE_4 | USD -67.32 | USD 226.07 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 0.000 | 0.00 | 180 | 83.33% | USD 158.75 | USD 28,575.00 | USD -25,022.00 |
| EXIT_AT_DTE_LE_4 | 0.000 | 0.65 | 180 | 82.78% | USD 149.65 | USD 26,937.00 | USD -25,031.10 |
| EXIT_AT_DTE_LE_4 | 0.025 | 0.00 | 180 | 82.78% | USD 123.75 | USD 22,275.00 | USD -25,057.00 |
| EXIT_AT_DTE_LE_4 | 0.025 | 0.65 | 180 | 82.78% | USD 114.65 | USD 20,637.00 | USD -25,066.10 |
| EXIT_AT_DTE_LE_4 | 0.050 | 0.00 | 180 | 82.78% | USD 88.75 | USD 15,975.00 | USD -25,092.00 |
| EXIT_AT_DTE_LE_4 | 0.050 | 0.65 | 180 | 82.78% | USD 79.65 | USD 14,337.00 | USD -25,101.10 |
| EXIT_AT_DTE_LE_4 | 0.100 | 0.00 | 180 | 82.22% | USD 18.75 | USD 3,375.00 | USD -25,162.00 |
| EXIT_AT_DTE_LE_4 | 0.100 | 0.65 | 180 | 81.67% | USD 9.65 | USD 1,737.00 | USD -25,171.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 1 : 1 | 180/195 (15) | 31.11% (24.80–38.21%) | USD -52.24 | USD -9,403.00 | USD -1,421.60 |
| EXIT_AT_DTE_LE_4 | 1 : 6 | 180/195 (15) | 82.78% (76.59–87.59%) | USD 79.65 | USD 14,337.00 | USD -25,101.10 |
| EXIT_AT_DTE_LE_4 | 6 : 1 | 180/195 (15) | 16.67% (11.93–22.80%) | USD -445.32 | USD -80,158.00 | USD -7,232.10 |
| EXIT_AT_DTE_LE_4 | 5 : 5 | 180/195 (15) | 31.11% (24.80–38.21%) | USD -261.19 | USD -47,015.00 | USD -7,108.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/195 | 0.00% | USD -209,016.68 | USD -338,781.55 |
| -75% | 0/195 | 0.00% | USD -155,002.58 | USD -251,565.05 |
| -50% | 0/195 | 0.00% | USD -100,988.49 | USD -164,348.55 |
| -40% | 0/195 | 0.00% | USD -79,382.85 | USD -129,461.95 |
| -30% | 0/195 | 0.00% | USD -57,777.21 | USD -94,575.35 |
| -25% | 0/195 | 0.00% | USD -46,974.39 | USD -77,192.30 |
| -20% | 0/195 | 0.00% | USD -36,171.57 | USD -60,141.35 |
| -15% | 0/195 | 0.00% | USD -25,368.76 | USD -43,090.40 |
| -10% | 2/195 | 1.03% | USD -14,593.74 | USD -26,039.45 |
| -5% | 21/195 | 10.77% | USD -3,964.36 | USD -11,443.25 |
| 0% | 195/195 | 100.00% | USD 1,374.31 | USD 304.45 |
| 5% | 195/195 | 100.00% | USD 1,424.83 | USD 304.45 |
| 10% | 195/195 | 100.00% | USD 1,424.83 | USD 304.45 |
| 20% | 195/195 | 100.00% | USD 1,424.83 | USD 304.45 |

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