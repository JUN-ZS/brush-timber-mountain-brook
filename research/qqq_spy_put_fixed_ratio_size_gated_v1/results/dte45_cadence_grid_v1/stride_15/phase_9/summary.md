# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 129 checks; 129 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 463.71 / USD 2,723.86; mean absolute mismatch USD 2,260.16; mean match score 16.80%.
- Actual selected contract ratios: {'1:6': 129}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 129; entered cohorts: 129; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 128/129 | 99/29/0 | 77.34% (69.36–83.74%) | USD 664.04 | USD 1,512.90 | USD 84,997.20 | USD -28,698.10 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_20_OR_DTE_LE_7 | USD -188.59 | USD 931.73 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 128 | 78.12% | USD 743.14 | USD 95,122.00 | USD -28,619.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 128 | 78.12% | USD 734.04 | USD 93,957.20 | USD -28,628.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 128 | 77.34% | USD 708.14 | USD 90,642.00 | USD -28,654.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 128 | 77.34% | USD 699.04 | USD 89,477.20 | USD -28,663.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 128 | 77.34% | USD 673.14 | USD 86,162.00 | USD -28,689.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 128 | 77.34% | USD 664.04 | USD 84,997.20 | USD -28,698.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 128 | 77.34% | USD 603.14 | USD 77,202.00 | USD -28,759.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 128 | 77.34% | USD 594.04 | USD 76,037.20 | USD -28,768.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 128/129 (1) | 35.94% (28.15–44.55%) | USD -55.90 | USD -7,155.80 | USD -2,801.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 128/129 (1) | 77.34% (69.36–83.74%) | USD 664.04 | USD 84,997.20 | USD -28,698.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 128/129 (1) | 17.19% (11.63–24.65%) | USD -1,055.37 | USD -135,087.80 | USD -4,971.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 128/129 (1) | 35.94% (28.15–44.55%) | USD -279.52 | USD -35,779.00 | USD -14,008.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/129 | 0.00% | USD -205,580.90 | USD -331,564.55 |
| -75% | 0/129 | 0.00% | USD -151,587.98 | USD -244,865.55 |
| -50% | 0/129 | 0.00% | USD -97,595.06 | USD -158,166.55 |
| -40% | 0/129 | 0.00% | USD -75,997.89 | USD -123,486.95 |
| -30% | 0/129 | 0.00% | USD -54,400.72 | USD -89,720.55 |
| -25% | 0/129 | 0.00% | USD -43,602.14 | USD -73,221.05 |
| -20% | 0/129 | 0.00% | USD -32,803.55 | USD -56,721.55 |
| -15% | 1/129 | 0.78% | USD -22,004.97 | USD -40,222.05 |
| -10% | 4/129 | 3.10% | USD -11,249.89 | USD -23,963.55 |
| -5% | 48/129 | 37.21% | USD -1,003.90 | USD -8,435.05 |
| 0% | 129/129 | 100.00% | USD 2,220.61 | USD 657.45 |
| 5% | 129/129 | 100.00% | USD 2,220.61 | USD 657.45 |
| 10% | 129/129 | 100.00% | USD 2,220.61 | USD 657.45 |
| 20% | 129/129 | 100.00% | USD 2,220.61 | USD 657.45 |

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