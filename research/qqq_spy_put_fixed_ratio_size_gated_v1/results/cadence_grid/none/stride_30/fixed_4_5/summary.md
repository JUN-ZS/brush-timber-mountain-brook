# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 66 checks; 66 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 4 : SPY SHORT PUT 5; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,804.30 / USD 2,242.73; mean absolute mismatch USD 441.76; mean match score 79.72%.
- Actual selected contract ratios: {'4:5': 66}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 66; entered cohorts: 66; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 66/66 | 33/33/0 | 50.00% (38.27–61.73%) | USD -181.82 | USD -8.70 | USD -12,000.20 | USD -4,692.70 | 0 |
| HOLD_10_SESSIONS | 65/66 | 42/23/0 | 64.62% (52.48–75.12%) | USD -110.38 | USD 108.30 | USD -7,174.50 | USD -5,058.70 | 1 |
| HOLD_20_SESSIONS | 65/66 | 52/13/0 | 80.00% (68.73–87.92%) | USD 54.59 | USD 204.30 | USD 3,548.50 | USD -5,571.70 | 1 |
| EXIT_AT_DTE_LE_7 | 62/66 | 48/14/0 | 77.42% (65.59–86.04%) | USD -148.65 | USD 214.80 | USD -9,216.40 | USD -20,624.70 | 4 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -382.55 | USD 302.42 |
| HOLD_10_SESSIONS | USD -515.14 | USD 506.46 |
| HOLD_20_SESSIONS | USD -716.25 | USD 872.54 |
| EXIT_AT_DTE_LE_7 | USD -607.68 | USD 560.73 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 66 | 62.12% | USD -80.12 | USD -5,288.00 | USD -4,591.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 66 | 60.61% | USD -91.82 | USD -6,060.20 | USD -4,602.70 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 66 | 54.55% | USD -125.12 | USD -8,258.00 | USD -4,636.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 66 | 54.55% | USD -136.82 | USD -9,030.20 | USD -4,647.70 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 66 | 50.00% | USD -170.12 | USD -11,228.00 | USD -4,681.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 66 | 50.00% | USD -181.82 | USD -12,000.20 | USD -4,692.70 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 66 | 37.88% | USD -260.12 | USD -17,168.00 | USD -4,771.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 66 | 34.85% | USD -271.82 | USD -17,940.20 | USD -4,782.70 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 65 | 70.77% | USD -8.68 | USD -564.00 | USD -4,957.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 65 | 70.77% | USD -20.38 | USD -1,324.50 | USD -4,968.70 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 65 | 67.69% | USD -53.68 | USD -3,489.00 | USD -5,002.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 65 | 66.15% | USD -65.38 | USD -4,249.50 | USD -5,013.70 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 65 | 64.62% | USD -98.68 | USD -6,414.00 | USD -5,047.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 65 | 64.62% | USD -110.38 | USD -7,174.50 | USD -5,058.70 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 65 | 52.31% | USD -188.68 | USD -12,264.00 | USD -5,137.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 65 | 52.31% | USD -200.38 | USD -13,024.50 | USD -5,148.70 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 65 | 83.08% | USD 156.29 | USD 10,159.00 | USD -5,470.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 65 | 81.54% | USD 144.59 | USD 9,398.50 | USD -5,481.70 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 65 | 81.54% | USD 111.29 | USD 7,234.00 | USD -5,515.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 65 | 81.54% | USD 99.59 | USD 6,473.50 | USD -5,526.70 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 65 | 80.00% | USD 66.29 | USD 4,309.00 | USD -5,560.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 65 | 80.00% | USD 54.59 | USD 3,548.50 | USD -5,571.70 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 65 | 66.15% | USD -23.71 | USD -1,541.00 | USD -5,650.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 65 | 66.15% | USD -35.41 | USD -2,301.50 | USD -5,661.70 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 62 | 85.48% | USD -46.95 | USD -2,911.00 | USD -20,523.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 62 | 83.87% | USD -58.65 | USD -3,636.40 | USD -20,534.70 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 62 | 80.65% | USD -91.95 | USD -5,701.00 | USD -20,568.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 62 | 79.03% | USD -103.65 | USD -6,426.40 | USD -20,579.70 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 62 | 77.42% | USD -136.95 | USD -8,491.00 | USD -20,613.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 62 | 77.42% | USD -148.65 | USD -9,216.40 | USD -20,624.70 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 62 | 70.97% | USD -226.95 | USD -14,071.00 | USD -20,703.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 62 | 69.35% | USD -238.65 | USD -14,796.40 | USD -20,714.70 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 66/66 (0) | 27.27% (18.00–39.04%) | USD -57.75 | USD -3,811.60 | USD -983.60 |
| HOLD_5_SESSIONS | 1 : 6 | 66/66 (0) | 72.73% (60.96–82.00%) | USD 188.17 | USD 12,419.40 | USD -4,775.10 |
| HOLD_5_SESSIONS | 6 : 1 | 66/66 (0) | 19.70% (11.89–30.84%) | USD -592.43 | USD -39,100.60 | USD -3,001.10 |
| HOLD_5_SESSIONS | 4 : 5 | 66/66 (0) | 50.00% (38.27–61.73%) | USD -181.82 | USD -12,000.20 | USD -4,692.70 |
| HOLD_10_SESSIONS | 1 : 1 | 65/66 (1) | 36.92% (26.23–49.08%) | USD -50.09 | USD -3,256.00 | USD -746.60 |
| HOLD_10_SESSIONS | 1 : 6 | 65/66 (1) | 75.38% (63.69–84.24%) | USD 399.87 | USD 25,991.50 | USD -11,108.10 |
| HOLD_10_SESSIONS | 6 : 1 | 65/66 (1) | 15.38% (8.58–26.06%) | USD -750.52 | USD -48,783.50 | USD -3,797.10 |
| HOLD_10_SESSIONS | 4 : 5 | 65/66 (1) | 64.62% (52.48–75.12%) | USD -110.38 | USD -7,174.50 | USD -5,058.70 |
| HOLD_20_SESSIONS | 1 : 1 | 65/66 (1) | 40.00% (28.97–52.14%) | USD -27.15 | USD -1,765.00 | USD -975.60 |
| HOLD_20_SESSIONS | 1 : 6 | 65/66 (1) | 84.62% (73.94–91.42%) | USD 788.88 | USD 51,277.50 | USD -12,548.10 |
| HOLD_20_SESSIONS | 6 : 1 | 65/66 (1) | 16.92% (9.72–27.82%) | USD -978.96 | USD -63,632.50 | USD -7,645.10 |
| HOLD_20_SESSIONS | 4 : 5 | 65/66 (1) | 80.00% (68.73–87.92%) | USD 54.59 | USD 3,548.50 | USD -5,571.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 62/66 (4) | 48.39% (36.41–60.55%) | USD -62.37 | USD -3,867.20 | USD -3,458.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 62/66 (4) | 87.10% (76.55–93.31%) | USD 441.85 | USD 27,394.80 | USD -37,410.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 62/66 (4) | 19.35% (11.43–30.85%) | USD -878.47 | USD -54,465.20 | USD -7,887.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 62/66 (4) | 77.42% (65.59–86.04%) | USD -148.65 | USD -9,216.40 | USD -20,624.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/66 | 0.00% | USD -73,264.73 | USD -91,973.85 |
| -75% | 0/66 | 0.00% | USD -54,408.96 | USD -69,041.60 |
| -50% | 0/66 | 0.00% | USD -35,553.20 | USD -46,131.35 |
| -40% | 0/66 | 0.00% | USD -28,010.89 | USD -36,967.25 |
| -30% | 0/66 | 0.00% | USD -20,468.59 | USD -27,803.15 |
| -25% | 0/66 | 0.00% | USD -16,697.43 | USD -23,221.10 |
| -20% | 0/66 | 0.00% | USD -12,926.28 | USD -18,639.05 |
| -15% | 0/66 | 0.00% | USD -9,155.13 | USD -14,057.00 |
| -10% | 2/66 | 3.03% | USD -5,381.21 | USD -9,474.95 |
| -5% | 22/66 | 33.33% | USD -1,332.02 | USD -4,892.90 |
| 0% | 59/66 | 89.39% | USD 391.70 | USD -124.85 |
| 5% | 59/66 | 89.39% | USD 387.57 | USD -124.85 |
| 10% | 59/66 | 89.39% | USD 387.57 | USD -124.85 |
| 20% | 59/66 | 89.39% | USD 387.57 | USD -124.85 |

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