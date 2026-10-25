# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 163 checks; 163 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 17–23 (target 20); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,083.80 / USD 1,611.98; mean absolute mismatch USD 550.52; mean match score 67.38%.
- Actual selected contract ratios: {'1:6': 163}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 163; entered cohorts: 163; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_SESSIONS | 149/163 | 127/22/0 | 85.23% (78.66–90.04%) | USD -87.35 | USD 484.90 | USD -13,014.90 | USD -29,275.10 | 14 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_10_SESSIONS | USD -169.56 | USD 161.32 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_SESSIONS | 0.000 | 0.00 | 149 | 86.58% | USD -8.25 | USD -1,229.00 | USD -29,196.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 149 | 86.58% | USD -17.35 | USD -2,584.90 | USD -29,205.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 149 | 85.91% | USD -43.25 | USD -6,444.00 | USD -29,231.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 149 | 85.91% | USD -52.35 | USD -7,799.90 | USD -29,240.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 149 | 85.23% | USD -78.25 | USD -11,659.00 | USD -29,266.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 149 | 85.23% | USD -87.35 | USD -13,014.90 | USD -29,275.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 149 | 82.55% | USD -148.25 | USD -22,089.00 | USD -29,336.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 149 | 82.55% | USD -157.35 | USD -23,444.90 | USD -29,345.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_10_SESSIONS | 1 : 1 | 149/163 (14) | 32.21% (25.24–40.08%) | USD -165.28 | USD -24,626.40 | USD -2,123.60 |
| HOLD_10_SESSIONS | 1 : 6 | 149/163 (14) | 85.23% (78.66–90.04%) | USD -87.35 | USD -13,014.90 | USD -29,275.10 |
| HOLD_10_SESSIONS | 6 : 1 | 149/163 (14) | 31.54% (24.63–39.39%) | USD -1,069.60 | USD -159,369.90 | USD -16,050.10 |
| HOLD_10_SESSIONS | 5 : 5 | 149/163 (14) | 32.21% (25.24–40.08%) | USD -826.39 | USD -123,132.00 | USD -10,618.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/163 | 0.00% | USD -207,323.03 | USD -336,803.55 |
| -75% | 0/163 | 0.00% | USD -153,417.17 | USD -249,892.80 |
| -50% | 0/163 | 0.00% | USD -99,511.31 | USD -162,982.05 |
| -40% | 0/163 | 0.00% | USD -77,948.97 | USD -128,217.75 |
| -30% | 0/163 | 0.00% | USD -56,386.62 | USD -93,453.45 |
| -25% | 0/163 | 0.00% | USD -45,605.45 | USD -76,071.30 |
| -20% | 1/163 | 0.61% | USD -34,824.28 | USD -58,689.15 |
| -15% | 1/163 | 0.61% | USD -24,067.69 | USD -41,307.00 |
| -10% | 3/163 | 1.84% | USD -13,331.27 | USD -25,073.85 |
| -5% | 34/163 | 20.86% | USD -2,822.92 | USD -9,834.90 |
| 0% | 163/163 | 100.00% | USD 1,287.20 | USD 14.45 |
| 5% | 151/163 | 92.64% | USD 527.27 | USD -303.55 |
| 10% | 151/163 | 92.64% | USD 488.63 | USD -303.55 |
| 20% | 151/163 | 92.64% | USD 488.63 | USD -303.55 |

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