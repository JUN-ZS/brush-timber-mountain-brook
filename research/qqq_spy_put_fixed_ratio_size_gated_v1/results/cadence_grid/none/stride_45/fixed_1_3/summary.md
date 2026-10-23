# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 44 checks; 44 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 437.43 / USD 1,295.32; mean absolute mismatch USD 857.89; mean match score 32.82%.
- Actual selected contract ratios: {'1:3': 44}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 44; entered cohorts: 44; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 44/44 | 32/12/0 | 72.73% (58.15–83.65%) | USD -97.97 | USD 181.80 | USD -4,310.80 | USD -7,101.20 | 0 |
| HOLD_10_SESSIONS | 44/44 | 32/12/0 | 72.73% (58.15–83.65%) | USD -157.75 | USD 306.80 | USD -6,940.80 | USD -7,366.20 | 0 |
| HOLD_20_SESSIONS | 44/44 | 35/9/0 | 79.55% (65.50–88.85%) | USD -330.70 | USD 611.80 | USD -14,550.80 | USD -23,302.20 | 0 |
| EXIT_AT_DTE_LE_7 | 37/44 | 29/8/0 | 78.38% (62.80–88.61%) | USD -497.52 | USD 716.80 | USD -18,408.40 | USD -16,843.20 | 7 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -9.95 | USD -42.82 |
| HOLD_10_SESSIONS | USD -7.82 | USD -104.73 |
| HOLD_20_SESSIONS | USD -42.57 | USD -242.93 |
| EXIT_AT_DTE_LE_7 | USD 11.86 | USD -464.19 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 44 | 72.73% | USD -52.77 | USD -2,322.00 | USD -7,056.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 44 | 72.73% | USD -57.97 | USD -2,550.80 | USD -7,061.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 44 | 72.73% | USD -72.77 | USD -3,202.00 | USD -7,076.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 44 | 72.73% | USD -77.97 | USD -3,430.80 | USD -7,081.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 44 | 72.73% | USD -92.77 | USD -4,082.00 | USD -7,096.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 44 | 72.73% | USD -97.97 | USD -4,310.80 | USD -7,101.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 44 | 72.73% | USD -132.77 | USD -5,842.00 | USD -7,136.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 44 | 72.73% | USD -137.97 | USD -6,070.80 | USD -7,141.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 44 | 75.00% | USD -112.55 | USD -4,952.00 | USD -7,321.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 44 | 75.00% | USD -117.75 | USD -5,180.80 | USD -7,326.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 44 | 75.00% | USD -132.55 | USD -5,832.00 | USD -7,341.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 44 | 75.00% | USD -137.75 | USD -6,060.80 | USD -7,346.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 44 | 72.73% | USD -152.55 | USD -6,712.00 | USD -7,361.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 44 | 72.73% | USD -157.75 | USD -6,940.80 | USD -7,366.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 44 | 72.73% | USD -192.55 | USD -8,472.00 | USD -7,401.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 44 | 72.73% | USD -197.75 | USD -8,700.80 | USD -7,406.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 44 | 79.55% | USD -285.50 | USD -12,562.00 | USD -23,257.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 44 | 79.55% | USD -290.70 | USD -12,790.80 | USD -23,262.20 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 44 | 79.55% | USD -305.50 | USD -13,442.00 | USD -23,277.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 44 | 79.55% | USD -310.70 | USD -13,670.80 | USD -23,282.20 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 44 | 79.55% | USD -325.50 | USD -14,322.00 | USD -23,297.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 44 | 79.55% | USD -330.70 | USD -14,550.80 | USD -23,302.20 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 44 | 79.55% | USD -365.50 | USD -16,082.00 | USD -23,337.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 44 | 79.55% | USD -370.70 | USD -16,310.80 | USD -23,342.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 37 | 78.38% | USD -452.32 | USD -16,736.00 | USD -16,798.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 37 | 78.38% | USD -457.52 | USD -16,928.40 | USD -16,803.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 37 | 78.38% | USD -472.32 | USD -17,476.00 | USD -16,818.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 37 | 78.38% | USD -477.52 | USD -17,668.40 | USD -16,823.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 37 | 78.38% | USD -492.32 | USD -18,216.00 | USD -16,838.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 37 | 78.38% | USD -497.52 | USD -18,408.40 | USD -16,843.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 37 | 78.38% | USD -532.32 | USD -19,696.00 | USD -16,878.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 37 | 78.38% | USD -537.52 | USD -19,888.40 | USD -16,883.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 44/44 (0) | 36.36% (23.78–51.13%) | USD -46.83 | USD -2,060.40 | USD -1,204.60 |
| HOLD_5_SESSIONS | 1 : 6 | 44/44 (0) | 72.73% (58.15–83.65%) | USD -174.69 | USD -7,686.40 | USD -15,946.10 |
| HOLD_5_SESSIONS | 6 : 1 | 44/44 (0) | 22.73% (12.84–36.99%) | USD -153.10 | USD -6,736.40 | USD -2,665.10 |
| HOLD_5_SESSIONS | 4 : 5 | 44/44 (0) | 56.82% (42.22–70.32%) | USD -212.88 | USD -9,366.80 | USD -7,766.70 |
| HOLD_10_SESSIONS | 1 : 1 | 44/44 (0) | 45.45% (31.71–59.93%) | USD -65.33 | USD -2,874.40 | USD -1,351.60 |
| HOLD_10_SESSIONS | 1 : 6 | 44/44 (0) | 72.73% (58.15–83.65%) | USD -296.37 | USD -13,040.40 | USD -16,388.10 |
| HOLD_10_SESSIONS | 6 : 1 | 44/44 (0) | 20.45% (11.15–34.50%) | USD -160.92 | USD -7,080.40 | USD -2,949.10 |
| HOLD_10_SESSIONS | 4 : 5 | 44/44 (0) | 61.36% (46.62–74.28%) | USD -307.52 | USD -13,530.80 | USD -8,413.70 |
| HOLD_20_SESSIONS | 1 : 1 | 44/44 (0) | 40.91% (27.69–55.59%) | USD -146.15 | USD -6,430.40 | USD -4,269.60 |
| HOLD_20_SESSIONS | 1 : 6 | 44/44 (0) | 79.55% (65.50–88.85%) | USD -607.53 | USD -26,731.40 | USD -51,851.10 |
| HOLD_20_SESSIONS | 6 : 1 | 44/44 (0) | 18.18% (9.51–31.96%) | USD -415.49 | USD -18,281.40 | USD -4,371.10 |
| HOLD_20_SESSIONS | 4 : 5 | 44/44 (0) | 70.45% (55.78–81.84%) | USD -676.86 | USD -29,781.80 | USD -26,594.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 37/44 (7) | 43.24% (28.67–59.09%) | USD -165.46 | USD -6,122.20 | USD -3,376.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 37/44 (7) | 78.38% (62.80–88.61%) | USD -995.61 | USD -36,837.70 | USD -37,043.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 37/44 (7) | 24.32% (13.36–40.12%) | USD -162.64 | USD -6,017.70 | USD -4,415.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 37/44 (7) | 78.38% (62.80–88.61%) | USD -827.89 | USD -30,631.90 | USD -20,239.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/44 | 0.00% | USD -86,966.85 | USD -136,658.60 |
| -75% | 0/44 | 0.00% | USD -64,146.58 | USD -100,972.85 |
| -50% | 0/44 | 0.00% | USD -41,326.30 | USD -65,287.10 |
| -40% | 0/44 | 0.00% | USD -32,198.20 | USD -51,012.80 |
| -30% | 0/44 | 0.00% | USD -23,070.09 | USD -36,738.50 |
| -25% | 0/44 | 0.00% | USD -18,506.03 | USD -29,601.35 |
| -20% | 0/44 | 0.00% | USD -13,941.98 | USD -22,509.20 |
| -15% | 0/44 | 0.00% | USD -9,377.92 | USD -15,656.80 |
| -10% | 2/44 | 4.55% | USD -4,800.97 | USD -9,059.30 |
| -5% | 18/44 | 40.91% | USD -486.51 | USD -3,167.65 |
| 0% | 44/44 | 100.00% | USD 835.29 | USD 275.40 |
| 5% | 44/44 | 100.00% | USD 835.29 | USD 275.40 |
| 10% | 44/44 | 100.00% | USD 835.29 | USD 275.40 |
| 20% | 44/44 | 100.00% | USD 835.29 | USD 275.40 |

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