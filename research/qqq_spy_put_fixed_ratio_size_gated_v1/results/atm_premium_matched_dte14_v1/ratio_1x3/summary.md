# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 392 checks; 392 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 703.28 / USD 698.83; mean absolute mismatch USD 170.18; mean match score 79.90%.
- Actual selected contract ratios: {'1:3': 392}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 392; entered cohorts: 392; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 390/392 | 232/158/0 | 59.49% (54.55–64.24%) | USD -2.62 | USD 50.30 | USD -1,021.00 | USD -7,565.20 | 2 |
| HOLD_10_SESSIONS | 46/392 | 32/14/0 | 69.57% (55.19–80.92%) | USD -601.03 | USD 56.80 | USD -27,647.20 | USD -14,733.20 | 346 |
| HOLD_20_SESSIONS | 0/392 | 0/0/0 | — | — | — | — | — | 392 |
| HOLD_20_OR_DTE_LE_7 | 391/392 | 229/162/0 | 58.57% (53.62–63.34%) | USD -67.10 | USD 32.80 | USD -26,234.20 | USD -10,688.20 | 1 |
| EXIT_AT_DTE_LE_7 | 391/392 | 229/162/0 | 58.57% (53.62–63.34%) | USD -67.10 | USD 32.80 | USD -26,234.20 | USD -10,688.20 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -154.76 | USD 197.34 |
| HOLD_10_SESSIONS | USD 55.26 | USD -611.09 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -101.24 | USD 79.34 |
| EXIT_AT_DTE_LE_7 | USD -101.24 | USD 79.34 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 390 | 67.18% | USD 42.58 | USD 16,607.00 | USD -7,520.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 390 | 66.41% | USD 37.38 | USD 14,579.00 | USD -7,525.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 390 | 63.85% | USD 22.58 | USD 8,807.00 | USD -7,540.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 390 | 62.82% | USD 17.38 | USD 6,779.00 | USD -7,545.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 390 | 60.00% | USD 2.58 | USD 1,007.00 | USD -7,560.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 390 | 59.49% | USD -2.62 | USD -1,021.00 | USD -7,565.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 390 | 53.08% | USD -37.42 | USD -14,593.00 | USD -7,600.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 390 | 51.54% | USD -42.62 | USD -16,621.00 | USD -7,605.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 46 | 71.74% | USD -555.83 | USD -25,568.00 | USD -14,688.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 46 | 71.74% | USD -561.03 | USD -25,807.20 | USD -14,693.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 46 | 69.57% | USD -575.83 | USD -26,488.00 | USD -14,708.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 46 | 69.57% | USD -581.03 | USD -26,727.20 | USD -14,713.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 46 | 69.57% | USD -595.83 | USD -27,408.00 | USD -14,728.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 46 | 69.57% | USD -601.03 | USD -27,647.20 | USD -14,733.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 46 | 58.70% | USD -635.83 | USD -29,248.00 | USD -14,768.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 46 | 56.52% | USD -641.03 | USD -29,487.20 | USD -14,773.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 391 | 67.52% | USD -21.90 | USD -8,561.00 | USD -10,643.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 391 | 67.01% | USD -27.10 | USD -10,594.20 | USD -10,648.20 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 391 | 62.66% | USD -41.90 | USD -16,381.00 | USD -10,663.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 391 | 62.40% | USD -47.10 | USD -18,414.20 | USD -10,668.20 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 391 | 60.10% | USD -61.90 | USD -24,201.00 | USD -10,683.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 391 | 58.57% | USD -67.10 | USD -26,234.20 | USD -10,688.20 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 391 | 49.10% | USD -101.90 | USD -39,841.00 | USD -10,723.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 391 | 48.08% | USD -107.10 | USD -41,874.20 | USD -10,728.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 391 | 67.52% | USD -21.90 | USD -8,561.00 | USD -10,643.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 391 | 67.01% | USD -27.10 | USD -10,594.20 | USD -10,648.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 391 | 62.66% | USD -41.90 | USD -16,381.00 | USD -10,663.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 391 | 62.40% | USD -47.10 | USD -18,414.20 | USD -10,668.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 391 | 60.10% | USD -61.90 | USD -24,201.00 | USD -10,683.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 391 | 58.57% | USD -67.10 | USD -26,234.20 | USD -10,688.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 391 | 49.10% | USD -101.90 | USD -39,841.00 | USD -10,723.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 391 | 48.08% | USD -107.10 | USD -41,874.20 | USD -10,728.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 390/392 (2) | 28.72% (24.45–33.40%) | USD -111.58 | USD -43,515.00 | USD -1,335.60 |
| HOLD_5_SESSIONS | 1 : 6 | 390/392 (2) | 82.82% (78.76–86.24%) | USD 160.82 | USD 62,720.00 | USD -17,691.10 |
| HOLD_5_SESSIONS | 6 : 1 | 390/392 (2) | 27.69% (23.49–32.33%) | USD -941.86 | USD -367,325.00 | USD -13,332.10 |
| HOLD_5_SESSIONS | 5 : 5 | 390/392 (2) | 28.72% (24.45–33.40%) | USD -557.88 | USD -217,575.00 | USD -6,678.00 |
| HOLD_10_SESSIONS | 1 : 1 | 46/392 (346) | 30.43% (19.08–44.81%) | USD -171.03 | USD -7,867.60 | USD -2,506.60 |
| HOLD_10_SESSIONS | 1 : 6 | 46/392 (346) | 80.43% (66.83–89.35%) | USD -1,246.01 | USD -57,316.60 | USD -33,073.10 |
| HOLD_10_SESSIONS | 6 : 1 | 46/392 (346) | 36.96% (24.52–51.40%) | USD 48.77 | USD 2,243.40 | USD -10,106.10 |
| HOLD_10_SESSIONS | 5 : 5 | 46/392 (346) | 30.43% (19.08–44.81%) | USD -855.17 | USD -39,338.00 | USD -12,533.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/392 (392) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 391/392 (1) | 29.67% (25.36–34.38%) | USD -97.39 | USD -38,079.60 | USD -1,257.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 391/392 (1) | 79.54% (75.26–83.24%) | USD -21.65 | USD -8,466.10 | USD -24,834.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 391/392 (1) | 30.69% (26.33–35.43%) | USD -660.08 | USD -258,091.10 | USD -14,167.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 391/392 (1) | 29.67% (25.36–34.38%) | USD -486.95 | USD -190,398.00 | USD -6,288.00 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 391/392 (1) | 29.67% (25.36–34.38%) | USD -97.39 | USD -38,079.60 | USD -1,257.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 391/392 (1) | 79.54% (75.26–83.24%) | USD -21.65 | USD -8,466.10 | USD -24,834.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 391/392 (1) | 30.69% (26.33–35.43%) | USD -660.08 | USD -258,091.10 | USD -14,167.10 |
| EXIT_AT_DTE_LE_7 | 5 : 5 | 391/392 (1) | 29.67% (25.36–34.38%) | USD -486.95 | USD -190,398.00 | USD -6,288.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/392 | 0.00% | USD -88,241.85 | USD -139,399.60 |
| -75% | 0/392 | 0.00% | USD -65,400.32 | USD -103,693.10 |
| -50% | 0/392 | 0.00% | USD -42,558.80 | USD -67,986.60 |
| -40% | 0/392 | 0.00% | USD -33,422.19 | USD -53,704.00 |
| -30% | 0/392 | 0.00% | USD -24,285.58 | USD -39,496.70 |
| -25% | 0/392 | 0.00% | USD -19,717.27 | USD -32,464.35 |
| -20% | 0/392 | 0.00% | USD -15,148.97 | USD -25,432.00 |
| -15% | 2/392 | 0.51% | USD -10,580.66 | USD -18,399.65 |
| -10% | 5/392 | 1.28% | USD -6,020.42 | USD -11,367.30 |
| -5% | 63/392 | 16.07% | USD -1,531.67 | USD -4,620.10 |
| 0% | 311/392 | 79.34% | USD 332.29 | USD -261.60 |
| 5% | 152/392 | 38.78% | USD -19.68 | USD -672.60 |
| 10% | 152/392 | 38.78% | USD -25.28 | USD -672.60 |
| 20% | 152/392 | 38.78% | USD -27.05 | USD -672.60 |

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