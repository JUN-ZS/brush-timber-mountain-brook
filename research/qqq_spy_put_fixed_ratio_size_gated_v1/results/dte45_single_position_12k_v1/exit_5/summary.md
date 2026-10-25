# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 278 checks; 278 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 454.85 / USD 2,738.16; mean absolute mismatch USD 2,283.31; mean match score 16.66%.
- Actual selected contract ratios: {'1:6': 278}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 278; entered cohorts: 278; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 277/278 | 190/87/0 | 68.59% (62.90–73.77%) | USD 172.14 | USD 435.90 | USD 47,682.30 | USD -15,946.10 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -68.91 | USD 320.14 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 277 | 72.20% | USD 251.24 | USD 69,593.00 | USD -15,867.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 277 | 71.48% | USD 242.14 | USD 67,072.30 | USD -15,876.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 277 | 70.40% | USD 216.24 | USD 59,898.00 | USD -15,902.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 277 | 70.40% | USD 207.14 | USD 57,377.30 | USD -15,911.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 277 | 69.68% | USD 181.24 | USD 50,203.00 | USD -15,937.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 277 | 68.59% | USD 172.14 | USD 47,682.30 | USD -15,946.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 277 | 65.34% | USD 111.24 | USD 30,813.00 | USD -16,007.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 277 | 64.98% | USD 102.14 | USD 28,292.30 | USD -16,016.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 277/278 (1) | 33.94% (28.61–39.70%) | USD -38.15 | USD -10,567.20 | USD -1,204.60 |
| HOLD_5_SESSIONS | 1 : 6 | 277/278 (1) | 68.59% (62.90–73.77%) | USD 172.14 | USD 47,682.30 | USD -15,946.10 |
| HOLD_5_SESSIONS | 6 : 1 | 277/278 (1) | 25.99% (21.18–31.46%) | USD -439.18 | USD -121,652.70 | USD -7,478.10 |
| HOLD_5_SESSIONS | 5 : 5 | 277/278 (1) | 33.94% (28.61–39.70%) | USD -190.74 | USD -52,836.00 | USD -6,023.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/278 | 0.00% | USD -205,097.24 | USD -336,601.55 |
| -75% | 0/278 | 0.00% | USD -151,232.34 | USD -249,385.05 |
| -50% | 0/278 | 0.00% | USD -97,367.45 | USD -162,168.55 |
| -40% | 0/278 | 0.00% | USD -75,821.49 | USD -127,281.95 |
| -30% | 0/278 | 0.00% | USD -54,275.53 | USD -92,395.35 |
| -25% | 0/278 | 0.00% | USD -43,502.55 | USD -74,952.05 |
| -20% | 0/278 | 0.00% | USD -32,729.57 | USD -57,508.75 |
| -15% | 0/278 | 0.00% | USD -21,956.60 | USD -40,096.80 |
| -10% | 7/278 | 2.52% | USD -11,197.28 | USD -23,222.05 |
| -5% | 112/278 | 40.29% | USD -887.86 | USD -7,910.20 |
| 0% | 278/278 | 100.00% | USD 2,240.05 | USD 610.45 |
| 5% | 278/278 | 100.00% | USD 2,243.76 | USD 610.45 |
| 10% | 278/278 | 100.00% | USD 2,243.76 | USD 610.45 |
| 20% | 278/278 | 100.00% | USD 2,243.76 | USD 610.45 |

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