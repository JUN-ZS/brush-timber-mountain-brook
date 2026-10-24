# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 389 checks; 389 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 447.15 / USD 1,320.86; mean absolute mismatch USD 873.71; mean match score 33.61%.
- Actual selected contract ratios: {'1:3': 389}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 389; entered cohorts: 389; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 387/389 | 292/95/0 | 75.45% (70.93–79.48%) | USD 53.57 | USD 292.80 | USD 20,730.60 | USD -11,219.20 | 2 |
| HOLD_20_OR_DTE_LE_7 | 383/389 | 308/75/0 | 80.42% (76.15–84.08%) | USD 179.64 | USD 521.80 | USD 68,802.40 | USD -20,969.20 | 6 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_10_OR_DTE_LE_7 | USD -89.37 | USD 188.14 |
| HOLD_20_OR_DTE_LE_7 | USD -158.05 | USD 382.90 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 387 | 76.49% | USD 98.77 | USD 38,223.00 | USD -11,174.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 387 | 76.49% | USD 93.57 | USD 36,210.60 | USD -11,179.20 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 387 | 76.49% | USD 78.77 | USD 30,483.00 | USD -11,194.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 387 | 76.49% | USD 73.57 | USD 28,470.60 | USD -11,199.20 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 387 | 75.45% | USD 58.77 | USD 22,743.00 | USD -11,214.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 387 | 75.45% | USD 53.57 | USD 20,730.60 | USD -11,219.20 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 387 | 73.39% | USD 18.77 | USD 7,263.00 | USD -11,254.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 387 | 72.61% | USD 13.57 | USD 5,250.60 | USD -11,259.20 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 383 | 80.94% | USD 224.84 | USD 86,114.00 | USD -20,924.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 383 | 80.94% | USD 219.64 | USD 84,122.40 | USD -20,929.20 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 383 | 80.68% | USD 204.84 | USD 78,454.00 | USD -20,944.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 383 | 80.68% | USD 199.64 | USD 76,462.40 | USD -20,949.20 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 383 | 80.68% | USD 184.84 | USD 70,794.00 | USD -20,964.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 383 | 80.42% | USD 179.64 | USD 68,802.40 | USD -20,969.20 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 383 | 80.16% | USD 144.84 | USD 55,474.00 | USD -21,004.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 383 | 80.16% | USD 139.64 | USD 53,482.40 | USD -21,009.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 387/389 (2) | 32.30% (27.83–37.11%) | USD -49.26 | USD -19,063.20 | USD -2,196.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 387/389 (2) | 74.68% (70.12–78.75%) | USD 207.81 | USD 80,421.30 | USD -24,753.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 387/389 (2) | 21.19% (17.41–25.53%) | USD -552.62 | USD -213,863.70 | USD -6,005.10 |
| HOLD_10_OR_DTE_LE_7 | 4 : 5 | 387/389 (2) | 55.81% (50.83–60.68%) | USD -145.62 | USD -56,355.90 | USD -13,297.70 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 383/389 (6) | 38.38% (33.65–43.34%) | USD -53.02 | USD -20,307.80 | USD -4,038.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 383/389 (6) | 80.16% (75.87–83.84%) | USD 528.64 | USD 202,467.70 | USD -46,365.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 383/389 (6) | 17.23% (13.78–21.34%) | USD -899.80 | USD -344,622.30 | USD -5,355.10 |
| HOLD_20_OR_DTE_LE_7 | 4 : 5 | 383/389 (6) | 69.97% (65.20–74.35%) | USD -95.76 | USD -36,676.10 | USD -24,619.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/389 | 0.00% | USD -87,321.55 | USD -137,346.60 |
| -75% | 0/389 | 0.00% | USD -64,431.59 | USD -101,744.85 |
| -50% | 0/389 | 0.00% | USD -41,541.63 | USD -66,143.10 |
| -40% | 0/389 | 0.00% | USD -32,385.65 | USD -51,902.40 |
| -30% | 0/389 | 0.00% | USD -23,229.66 | USD -37,661.70 |
| -25% | 0/389 | 0.00% | USD -18,651.67 | USD -30,739.60 |
| -20% | 0/389 | 0.00% | USD -14,073.68 | USD -24,183.20 |
| -15% | 2/389 | 0.51% | USD -9,495.69 | USD -17,626.80 |
| -10% | 11/389 | 2.83% | USD -4,928.94 | USD -11,070.40 |
| -5% | 148/389 | 38.05% | USD -534.87 | USD -4,514.00 |
| 0% | 389/389 | 100.00% | USD 850.41 | USD 208.40 |
| 5% | 389/389 | 100.00% | USD 851.11 | USD 208.40 |
| 10% | 389/389 | 100.00% | USD 851.11 | USD 208.40 |
| 20% | 389/389 | 100.00% | USD 851.11 | USD 208.40 |

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

## Expiry-guarded exit contract

- Exit signal: planned 10/20 common-session holding limit OR remaining calendar DTE <= 7, whichever occurs first.
- A trigger is not a guaranteed fill. The replay still requires exact selected contracts, valid quotes and sufficient displayed exit-side size; failed closes defer and can remain unresolved at expiry/source end.
- Base engine SHA-256: 2037a21cb3c6b13a2965e08e516e3688f785dfa18d988a5640303b531f6ee40d; patched engine SHA-256: c689e002bb43440f0d7e5a2ad8208e16169984f124435875cd1d5dc4be63e2b6; runner SHA-256: 1ecebff5bb001c5c4441e447247aa99696055611c3634a514d0c5a4fabbe6e73.
