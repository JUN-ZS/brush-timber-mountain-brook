# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 392 checks; 392 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 2 : SPY SHORT PUT 4; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 898.29 / USD 1,774.52; mean absolute mismatch USD 877.87; mean match score 50.07%.
- Actual selected contract ratios: {'2:4': 392}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 392; entered cohorts: 392; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 391/392 | 260/131/0 | 66.50% (61.68–70.99%) | USD 0.36 | USD 152.20 | USD 142.20 | USD -8,305.80 | 1 |
| HOLD_10_SESSIONS | 389/392 | 289/100/0 | 74.29% (69.73–78.38%) | USD 38.94 | USD 318.20 | USD 15,145.80 | USD -19,029.80 | 3 |
| HOLD_20_SESSIONS | 384/392 | 314/70/0 | 81.77% (77.60–85.31%) | USD 128.52 | USD 535.20 | USD 49,352.80 | USD -27,571.80 | 8 |
| EXIT_AT_DTE_LE_7 | 344/392 | 281/63/0 | 81.69% (77.26–85.42%) | USD 80.68 | USD 603.20 | USD 27,754.80 | USD -25,221.80 | 48 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -148.48 | USD 216.64 |
| HOLD_10_SESSIONS | USD -208.17 | USD 314.91 |
| HOLD_20_SESSIONS | USD -335.19 | USD 531.51 |
| EXIT_AT_DTE_LE_7 | USD -365.74 | USD 514.22 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 391 | 71.36% | USD 68.16 | USD 26,652.00 | USD -8,238.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 391 | 71.10% | USD 60.36 | USD 23,602.20 | USD -8,245.80 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 391 | 69.57% | USD 38.16 | USD 14,922.00 | USD -8,268.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 391 | 68.80% | USD 30.36 | USD 11,872.20 | USD -8,275.80 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 391 | 66.50% | USD 8.16 | USD 3,192.00 | USD -8,298.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 391 | 66.50% | USD 0.36 | USD 142.20 | USD -8,305.80 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 391 | 60.61% | USD -51.84 | USD -20,268.00 | USD -8,358.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 391 | 60.36% | USD -59.64 | USD -23,317.80 | USD -8,365.80 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 389 | 76.86% | USD 106.74 | USD 41,520.00 | USD -18,962.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 389 | 76.86% | USD 98.94 | USD 38,485.80 | USD -18,969.80 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 389 | 76.35% | USD 76.74 | USD 29,850.00 | USD -18,992.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 389 | 76.09% | USD 68.94 | USD 26,815.80 | USD -18,999.80 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 389 | 74.55% | USD 46.74 | USD 18,180.00 | USD -19,022.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 389 | 74.29% | USD 38.94 | USD 15,145.80 | USD -19,029.80 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 389 | 71.21% | USD -13.26 | USD -5,160.00 | USD -19,082.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 389 | 70.95% | USD -21.06 | USD -8,194.20 | USD -19,089.80 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 384 | 82.81% | USD 196.32 | USD 75,388.00 | USD -27,504.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 384 | 82.81% | USD 188.52 | USD 72,392.80 | USD -27,511.80 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 384 | 82.55% | USD 166.32 | USD 63,868.00 | USD -27,534.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 384 | 82.55% | USD 158.52 | USD 60,872.80 | USD -27,541.80 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 384 | 82.03% | USD 136.32 | USD 52,348.00 | USD -27,564.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 384 | 81.77% | USD 128.52 | USD 49,352.80 | USD -27,571.80 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 384 | 81.25% | USD 76.32 | USD 29,308.00 | USD -27,624.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 384 | 80.99% | USD 68.52 | USD 26,312.80 | USD -27,631.80 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 344 | 82.85% | USD 148.48 | USD 51,078.00 | USD -25,154.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 344 | 82.85% | USD 140.68 | USD 48,394.80 | USD -25,161.80 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 344 | 82.85% | USD 118.48 | USD 40,758.00 | USD -25,184.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 344 | 82.85% | USD 110.68 | USD 38,074.80 | USD -25,191.80 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 344 | 81.98% | USD 88.48 | USD 30,438.00 | USD -25,214.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 344 | 81.69% | USD 80.68 | USD 27,754.80 | USD -25,221.80 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 344 | 81.69% | USD 28.48 | USD 9,798.00 | USD -25,274.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 344 | 81.69% | USD 20.68 | USD 7,114.80 | USD -25,281.80 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 391/392 (1) | 32.48% (28.03–37.27%) | USD -42.68 | USD -16,687.60 | USD -1,278.60 |
| HOLD_5_SESSIONS | 1 : 6 | 391/392 (1) | 69.57% (64.83–73.92%) | USD 171.63 | USD 67,105.90 | USD -15,946.10 |
| HOLD_5_SESSIONS | 6 : 1 | 391/392 (1) | 24.30% (20.31–28.78%) | USD -470.38 | USD -183,919.10 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 391/392 (1) | 49.10% (44.18–54.04%) | USD -127.86 | USD -49,991.70 | USD -7,766.70 |
| HOLD_10_SESSIONS | 1 : 1 | 389/392 (3) | 37.28% (32.62–42.18%) | USD -47.96 | USD -18,656.40 | USD -3,518.60 |
| HOLD_10_SESSIONS | 1 : 6 | 389/392 (3) | 75.84% (71.34–79.82%) | USD 289.18 | USD 112,490.10 | USD -33,500.10 |
| HOLD_10_SESSIONS | 6 : 1 | 389/392 (3) | 21.08% (17.32–25.41%) | USD -624.90 | USD -243,084.90 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 389/392 (3) | 58.35% (53.40–63.15%) | USD -124.41 | USD -48,396.30 | USD -20,070.70 |
| HOLD_20_SESSIONS | 1 : 1 | 384/392 (8) | 41.67% (36.84–46.66%) | USD -57.32 | USD -22,009.40 | USD -4,269.60 |
| HOLD_20_SESSIONS | 1 : 6 | 384/392 (8) | 83.33% (79.28–86.73%) | USD 550.57 | USD 211,419.60 | USD -51,851.10 |
| HOLD_20_SESSIONS | 6 : 1 | 384/392 (8) | 15.62% (12.34–19.60%) | USD -951.78 | USD -365,485.40 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 384/392 (8) | 71.88% (67.18–76.14%) | USD -107.69 | USD -41,351.80 | USD -26,594.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 344/392 (48) | 38.66% (33.67–43.91%) | USD -76.91 | USD -26,458.40 | USD -4,591.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 344/392 (48) | 84.01% (79.77–87.51%) | USD 509.36 | USD 175,220.60 | USD -44,688.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 344/392 (48) | 15.99% (12.49–20.23%) | USD -1,047.76 | USD -360,429.40 | USD -7,887.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 344/392 (48) | 71.80% (66.83–76.30%) | USD -190.40 | USD -65,497.80 | USD -26,385.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/392 | 0.00% | USD -95,595.67 | USD -144,311.90 |
| -75% | 0/392 | 0.00% | USD -70,638.54 | USD -107,251.90 |
| -50% | 0/392 | 0.00% | USD -45,681.42 | USD -70,191.90 |
| -40% | 0/392 | 0.00% | USD -35,698.57 | USD -55,367.90 |
| -30% | 0/392 | 0.00% | USD -25,715.72 | USD -40,543.90 |
| -25% | 0/392 | 0.00% | USD -20,724.29 | USD -33,131.90 |
| -20% | 1/392 | 0.26% | USD -15,732.87 | USD -25,766.70 |
| -15% | 3/392 | 0.77% | USD -10,744.97 | USD -18,617.50 |
| -10% | 11/392 | 2.81% | USD -5,779.16 | USD -11,468.30 |
| -5% | 143/392 | 36.48% | USD -864.96 | USD -4,515.20 |
| 0% | 391/392 | 99.74% | USD 842.68 | USD -353.90 |
| 5% | 391/392 | 99.74% | USD 842.33 | USD -353.90 |
| 10% | 391/392 | 99.74% | USD 842.33 | USD -353.90 |
| 20% | 391/392 | 99.74% | USD 842.33 | USD -353.90 |

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