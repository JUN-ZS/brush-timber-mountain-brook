# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 14–26 (target 20); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 160.66 / USD 871.69; mean absolute mismatch USD 711.04; mean match score 19.28%.
- Actual selected contract ratios: {'1:6': 195}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 195; entered cohorts: 195; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 148/195 | 87/61/0 | 58.78% (50.73–66.39%) | USD -407.90 | USD 127.40 | USD -60,369.80 | USD -9,372.10 | 47 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| EXIT_AT_DTE_LE_4 | USD 64.52 | USD -393.32 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 0.000 | 0.00 | 148 | 62.84% | USD -328.80 | USD -48,663.00 | USD -9,293.00 |
| EXIT_AT_DTE_LE_4 | 0.000 | 0.65 | 148 | 61.49% | USD -337.90 | USD -50,009.80 | USD -9,302.10 |
| EXIT_AT_DTE_LE_4 | 0.025 | 0.00 | 148 | 60.81% | USD -363.80 | USD -53,843.00 | USD -9,328.00 |
| EXIT_AT_DTE_LE_4 | 0.025 | 0.65 | 148 | 60.81% | USD -372.90 | USD -55,189.80 | USD -9,337.10 |
| EXIT_AT_DTE_LE_4 | 0.050 | 0.00 | 148 | 59.46% | USD -398.80 | USD -59,023.00 | USD -9,363.00 |
| EXIT_AT_DTE_LE_4 | 0.050 | 0.65 | 148 | 58.78% | USD -407.90 | USD -60,369.80 | USD -9,372.10 |
| EXIT_AT_DTE_LE_4 | 0.100 | 0.00 | 148 | 54.73% | USD -468.80 | USD -69,383.00 | USD -9,433.00 |
| EXIT_AT_DTE_LE_4 | 0.100 | 0.65 | 148 | 52.70% | USD -477.90 | USD -70,729.80 | USD -9,442.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| EXIT_AT_DTE_LE_4 | 1 : 1 | 148/195 (47) | 27.03% (20.52–34.70%) | USD -23.63 | USD -3,497.80 | USD -677.60 |
| EXIT_AT_DTE_LE_4 | 1 : 6 | 148/195 (47) | 58.78% (50.73–66.39%) | USD -407.90 | USD -60,369.80 | USD -9,372.10 |
| EXIT_AT_DTE_LE_4 | 6 : 1 | 148/195 (47) | 34.46% (27.28–42.42%) | USD 242.47 | USD 35,885.20 | USD -2,866.10 |
| EXIT_AT_DTE_LE_4 | 5 : 5 | 148/195 (47) | 27.03% (20.52–34.70%) | USD -118.17 | USD -17,489.00 | USD -3,388.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| -75% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| -50% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| -40% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| -30% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| -25% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| -20% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| -15% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| -10% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| -5% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| 0% | 194/195 | 99.49% | USD 671.49 | USD -29.55 |
| 5% | 26/195 | 13.33% | USD -4,370.64 | USD -11,771.30 |
| 10% | 2/195 | 1.03% | USD -14,909.56 | USD -29,188.05 |
| 20% | 0/195 | 0.00% | USD -36,465.36 | USD -64,021.55 |

## Limitations

- Public EOD preservation mirror; hashes establish file identity, not exchange or OPRA authenticity.
- EOD quotes are not verified fills; displayed size is a screening gate, not guaranteed multi-leg execution.
- Conservative sides: QQQ LONG enters Ask/exits Bid; SPY SHORT enters Bid/exits Ask.
- Missing exit quotes/size at expiry or source end remain unresolved; win-rate denominator is resolved episodes only.
- Option chain source ends in 2025; no 2026 performance is observed here.
- Nominal Wilson interval does not correct for regime clustering, dependence, or prior strategy selection.
- Expiry shock grid charges entry-side slippage/commission once and uses intrinsic-value payoff; exercise/assignment fees, broker margin, forced liquidation, financing and interim path are not modeled.
- Equal premium debit/credit does not equalize Delta, max loss, collateral or assignment risk; SPY short call can dominate downside even when QQQ long call appreciates.
- Fixed-cohort replay does not model portfolio compounding, taxes, financing, or verified fills.
- When overlapping cohorts are enabled, multiple fixed-size trades can be open at once; total portfolio cash, margin, forced liquidation, and stacked assignment obligations are not constrained by this replay.

Files: trade_episodes.csv, entry_cohort.csv, entry_skips.csv, cost_sensitivity.csv, sizing_sensitivity.csv, expiry_shock_grid.csv, source_manifest.json.