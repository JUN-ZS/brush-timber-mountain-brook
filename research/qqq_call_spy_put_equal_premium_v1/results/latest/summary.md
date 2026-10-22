# QQQ LONG CALL / SPY SHORT PUT — Equal-Premium Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ-call/SPY-put chain dates: 2025-12-15 / 2025-12-12.
- Position rule: buy QQQ CALL at Ask and sell SPY PUT at Bid. Per cohort, integer contract counts minimize relative mismatch between call premium paid and put premium received, subject to a total-contract cap of 9 and entry-side displayed sizes.
- Average QQQ call premium debit: USD 1,289.00; average SPY put premium credit: USD 1,288.80; average absolute mismatch: USD 63.80; average matching score: 95.60%.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25. Base costs: USD 0.050/option-share/side + USD 0.65/contract/side.

## Selected matched-premium ratios

| QQQ LONG CALL : SPY SHORT PUT | Cohorts | Mean QQQ premium debit | Mean SPY premium credit | Mean mismatch | Mean premium-match % |
|---:|---:|---:|---:|---:|---:|
| 1 : 1 | 1 | USD 712.00 | USD 801.00 | USD 89.00 | 88.89% |
| 2 : 3 | 1 | USD 748.00 | USD 735.00 | USD 13.00 | 98.26% |
| 3 : 2 | 4 | USD 783.00 | USD 785.50 | USD 10.00 | 98.86% |
| 3 : 3 | 1 | USD 1,443.00 | USD 1,461.00 | USD 18.00 | 98.77% |
| 3 : 4 | 2 | USD 1,839.00 | USD 1,818.00 | USD 79.00 | 95.77% |
| 3 : 5 | 1 | USD 909.00 | USD 890.00 | USD 19.00 | 97.91% |
| 3 : 6 | 2 | USD 1,978.50 | USD 2,064.00 | USD 118.50 | 94.99% |
| 4 : 2 | 2 | USD 800.00 | USD 800.00 | USD 14.00 | 98.17% |
| 4 : 3 | 3 | USD 1,168.00 | USD 1,159.00 | USD 9.00 | 98.94% |
| 4 : 4 | 6 | USD 1,448.67 | USD 1,434.00 | USD 90.67 | 93.41% |
| 4 : 5 | 3 | USD 1,485.33 | USD 1,605.00 | USD 119.67 | 92.70% |
| 5 : 1 | 1 | USD 740.00 | USD 751.00 | USD 11.00 | 98.54% |
| 5 : 2 | 4 | USD 861.25 | USD 840.00 | USD 29.75 | 96.82% |
| 5 : 3 | 4 | USD 1,158.75 | USD 1,147.50 | USD 47.75 | 96.25% |
| 5 : 4 | 3 | USD 1,896.67 | USD 1,754.67 | USD 142.00 | 92.28% |
| 6 : 2 | 1 | USD 1,626.00 | USD 1,736.00 | USD 110.00 | 93.66% |
| 6 : 3 | 3 | USD 1,596.00 | USD 1,603.00 | USD 93.00 | 94.02% |
| 7 : 2 | 2 | USD 1,480.50 | USD 1,454.00 | USD 69.50 | 95.31% |

Equal premium dollars means debit/credit parity only; it does not equalize Delta exposure, notional, collateral, assignment risk, or maximum loss.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 44; entered cohorts: 44; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 44/44 | 22/22/0 | 50.00% (35.83–64.17%) | USD -178.71 | USD 3.80 | USD -7,863.10 | USD -6,593.10 | 0 |
| HOLD_10_SESSIONS | 43/44 | 28/15/0 | 65.12% (50.17–77.58%) | USD 10.19 | USD 615.30 | USD 438.00 | USD -7,919.70 | 1 |
| HOLD_20_SESSIONS | 42/44 | 29/13/0 | 69.05% (53.97–80.93%) | USD 773.09 | USD 1,071.45 | USD 32,469.70 | USD -6,855.70 | 2 |
| EXIT_AT_DTE_LE_7 | 34/44 | 27/7/0 | 79.41% (63.20–89.65%) | USD 2,204.13 | USD 1,697.60 | USD 74,940.40 | USD -536.10 | 10 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -79.73 | USD -15.00 |
| HOLD_10_SESSIONS | USD -48.00 | USD 142.28 |
| HOLD_20_SESSIONS | USD 282.21 | USD 574.55 |
| EXIT_AT_DTE_LE_7 | USD 1,054.12 | USD 1,230.44 |

## Transaction-cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 44 | 59.09% | USD -94.73 | USD -4,168.00 | USD -6,514.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 44 | 56.82% | USD -104.39 | USD -4,593.10 | USD -6,523.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 44 | 54.55% | USD -131.89 | USD -5,803.00 | USD -6,549.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 44 | 54.55% | USD -141.55 | USD -6,228.10 | USD -6,558.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 44 | 50.00% | USD -169.05 | USD -7,438.00 | USD -6,584.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 44 | 50.00% | USD -178.71 | USD -7,863.10 | USD -6,593.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 44 | 47.73% | USD -243.36 | USD -10,708.00 | USD -6,654.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 44 | 47.73% | USD -253.03 | USD -11,133.10 | USD -6,663.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 43 | 67.44% | USD 94.28 | USD 4,054.00 | USD -7,818.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 43 | 67.44% | USD 84.60 | USD 3,638.00 | USD -7,829.70 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 43 | 67.44% | USD 57.07 | USD 2,454.00 | USD -7,863.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 43 | 67.44% | USD 47.40 | USD 2,038.00 | USD -7,874.70 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 43 | 67.44% | USD 19.86 | USD 854.00 | USD -7,908.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 43 | 65.12% | USD 10.19 | USD 438.00 | USD -7,919.70 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 43 | 60.47% | USD -54.56 | USD -2,346.00 | USD -7,998.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 43 | 60.47% | USD -64.23 | USD -2,762.00 | USD -8,009.70 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 42 | 69.05% | USD 856.76 | USD 35,984.00 | USD -6,754.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 42 | 69.05% | USD 847.14 | USD 35,579.70 | USD -6,765.70 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 42 | 69.05% | USD 819.74 | USD 34,429.00 | USD -6,799.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 42 | 69.05% | USD 810.11 | USD 34,024.70 | USD -6,810.70 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 42 | 69.05% | USD 782.71 | USD 32,874.00 | USD -6,844.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 42 | 69.05% | USD 773.09 | USD 32,469.70 | USD -6,855.70 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 42 | 64.29% | USD 708.67 | USD 29,764.00 | USD -6,934.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 42 | 61.90% | USD 699.04 | USD 29,359.70 | USD -6,945.70 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 34 | 88.24% | USD 2,284.56 | USD 77,675.00 | USD -457.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 34 | 82.35% | USD 2,275.31 | USD 77,360.40 | USD -466.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 34 | 79.41% | USD 2,248.97 | USD 76,465.00 | USD -492.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 34 | 79.41% | USD 2,239.72 | USD 76,150.40 | USD -501.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 34 | 79.41% | USD 2,213.38 | USD 75,255.00 | USD -527.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 34 | 79.41% | USD 2,204.13 | USD 74,940.40 | USD -536.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 34 | 79.41% | USD 2,142.21 | USD 72,835.00 | USD -597.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 34 | 79.41% | USD 2,132.95 | USD 72,520.40 | USD -606.10 |

## Fixed contract-ratio sensitivity (same selected contracts and quote path)

- Grid includes all fixed whole-contract combinations with QQQ CALL + SPY PUT total contracts ≤ 9; it rescales the same per-leg historical gross P&L and is not a fresh contract-selection replay.
- Full grid is in sizing_sensitivity.csv. Results inherit the base replay's resolved/unresolved cohort status; no size-dependent market impact is modeled.

## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff. Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/44 | 0.00% | USD -127,024.01 | USD -309,083.85 |
| -75% | 0/44 | 0.00% | USD -93,851.94 | USD -228,883.35 |
| -50% | 0/44 | 0.00% | USD -60,679.86 | USD -148,682.85 |
| -40% | 0/44 | 0.00% | USD -47,411.04 | USD -116,602.65 |
| -30% | 0/44 | 0.00% | USD -34,142.21 | USD -84,522.45 |
| -25% | 0/44 | 0.00% | USD -27,507.79 | USD -68,482.35 |
| -20% | 0/44 | 0.00% | USD -20,873.38 | USD -52,442.25 |
| -15% | 0/44 | 0.00% | USD -14,238.96 | USD -36,402.15 |
| -10% | 0/44 | 0.00% | USD -7,604.55 | USD -20,362.05 |
| -5% | 5/44 | 11.36% | USD -1,645.94 | USD -6,002.85 |
| 0% | 11/44 | 25.00% | USD -42.19 | USD -222.85 |
| 5% | 28/44 | 63.64% | USD 765.21 | USD -222.85 |
| 10% | 44/44 | 100.00% | USD 6,847.22 | USD 1,879.40 |
| 20% | 44/44 | 100.00% | USD 20,850.70 | USD 6,634.10 |

## Limitations

- Public EOD preservation mirror; hashes establish file identity, not exchange or OPRA authenticity.
- Equal-dollar premium matching does not equalize delta exposure, notional, margin, assignment or max loss.
- EOD quotes are not verified fills; displayed size is a screening gate, not guaranteed multi-leg execution.
- Conservative sides: QQQ LONG enters Ask/exits Bid; SPY SHORT enters Bid/exits Ask.
- Missing exit quotes/size at expiry or source end remain unresolved; win-rate denominator is resolved episodes only.
- Option chain source ends in 2025; no 2026 performance is observed here.
- Nominal Wilson interval does not correct for regime clustering, dependence, or prior strategy selection.
- Expiry shock grid uses QQQ call and SPY put intrinsic value, charges entry-side slippage/commission once; exercise/assignment fees, broker margin, forced liquidation, financing and interim path are not modeled.
- SPY short put can dominate downside even when QQQ long call appreciates; premium credit is not a max-loss budget.
- Fixed-cohort replay does not model portfolio compounding, taxes, financing, or verified fills.

Files: trade_episodes.csv, entry_cohort.csv, entry_skips.csv, cost_sensitivity.csv, sizing_sensitivity.csv, expiry_shock_grid.csv, source_manifest.json.