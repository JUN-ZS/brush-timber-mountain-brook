# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 966 checks; 111 qualified; 855 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 455.89 / USD 2,639.29; mean absolute mismatch USD 2,183.40; mean match score 17.08%.
- Actual selected contract ratios: {'1:6': 110}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 111; entered cohorts: 110; skipped entries: 1.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 110/110 | 66/44/0 | 60.00% (50.66–68.67%) | USD 74.58 | USD 370.40 | USD 8,204.00 | USD -4,827.10 | 0 |
| HOLD_10_SESSIONS | 109/110 | 82/27/0 | 75.23% (66.36–82.38%) | USD 324.17 | USD 828.90 | USD 35,334.10 | USD -10,453.10 | 1 |
| HOLD_20_SESSIONS | 107/110 | 86/21/0 | 80.37% (71.85–86.79%) | USD 850.72 | USD 1,344.90 | USD 91,027.30 | USD -9,376.10 | 3 |
| EXIT_AT_DTE_LE_7 | 94/110 | 77/17/0 | 81.91% (72.93–88.39%) | USD 488.42 | USD 1,532.40 | USD 45,911.60 | USD -20,318.10 | 16 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -56.26 | USD 209.95 |
| HOLD_10_SESSIONS | USD -115.76 | USD 519.03 |
| HOLD_20_SESSIONS | USD -214.10 | USD 1,143.93 |
| EXIT_AT_DTE_LE_7 | USD -147.69 | USD 715.21 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 110 | 61.82% | USD 153.68 | USD 16,905.00 | USD -4,748.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 110 | 61.82% | USD 144.58 | USD 15,904.00 | USD -4,757.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 110 | 61.82% | USD 118.68 | USD 13,055.00 | USD -4,783.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 110 | 60.91% | USD 109.58 | USD 12,054.00 | USD -4,792.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 110 | 60.00% | USD 83.68 | USD 9,205.00 | USD -4,818.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 110 | 60.00% | USD 74.58 | USD 8,204.00 | USD -4,827.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 110 | 59.09% | USD 13.68 | USD 1,505.00 | USD -4,888.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 110 | 57.27% | USD 4.58 | USD 504.00 | USD -4,897.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 109 | 77.06% | USD 403.27 | USD 43,956.00 | USD -10,374.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 109 | 77.06% | USD 394.17 | USD 42,964.10 | USD -10,383.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 109 | 77.06% | USD 368.27 | USD 40,141.00 | USD -10,409.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 109 | 77.06% | USD 359.17 | USD 39,149.10 | USD -10,418.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 109 | 75.23% | USD 333.27 | USD 36,326.00 | USD -10,444.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 109 | 75.23% | USD 324.17 | USD 35,334.10 | USD -10,453.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 109 | 75.23% | USD 263.27 | USD 28,696.00 | USD -10,514.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 109 | 75.23% | USD 254.17 | USD 27,704.10 | USD -10,523.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 107 | 81.31% | USD 929.82 | USD 99,491.00 | USD -9,297.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 107 | 81.31% | USD 920.72 | USD 98,517.30 | USD -9,306.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 107 | 81.31% | USD 894.82 | USD 95,746.00 | USD -9,332.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 107 | 81.31% | USD 885.72 | USD 94,772.30 | USD -9,341.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 107 | 81.31% | USD 859.82 | USD 92,001.00 | USD -9,367.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 107 | 80.37% | USD 850.72 | USD 91,027.30 | USD -9,376.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 107 | 80.37% | USD 789.82 | USD 84,511.00 | USD -9,437.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 107 | 80.37% | USD 780.72 | USD 83,537.30 | USD -9,446.10 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 94 | 81.91% | USD 567.52 | USD 53,347.00 | USD -20,239.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 94 | 81.91% | USD 558.42 | USD 52,491.60 | USD -20,248.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 94 | 81.91% | USD 532.52 | USD 50,057.00 | USD -20,274.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 94 | 81.91% | USD 523.42 | USD 49,201.60 | USD -20,283.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 94 | 81.91% | USD 497.52 | USD 46,767.00 | USD -20,309.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 94 | 81.91% | USD 488.42 | USD 45,911.60 | USD -20,318.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 94 | 81.91% | USD 427.52 | USD 40,187.00 | USD -20,379.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 94 | 81.91% | USD 418.42 | USD 39,331.60 | USD -20,388.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 110/110 (0) | 30.00% (22.23–39.12%) | USD -43.87 | USD -4,826.00 | USD -430.60 |
| HOLD_5_SESSIONS | 1 : 6 | 110/110 (0) | 60.00% (50.66–68.67%) | USD 74.58 | USD 8,204.00 | USD -4,827.10 |
| HOLD_5_SESSIONS | 6 : 1 | 110/110 (0) | 30.00% (22.23–39.12%) | USD -381.69 | USD -41,986.00 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 110/110 (0) | 48.18% (39.06–57.42%) | USD -151.80 | USD -16,698.00 | USD -2,439.70 |
| HOLD_10_SESSIONS | 1 : 1 | 109/110 (1) | 31.19% (23.26–40.40%) | USD -51.86 | USD -5,652.40 | USD -790.60 |
| HOLD_10_SESSIONS | 1 : 6 | 109/110 (1) | 75.23% (66.36–82.38%) | USD 324.17 | USD 35,334.10 | USD -10,453.10 |
| HOLD_10_SESSIONS | 6 : 1 | 109/110 (1) | 18.35% (12.20–26.65%) | USD -687.16 | USD -74,900.90 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 109/110 (1) | 53.21% (43.89–62.31%) | USD -132.22 | USD -14,412.30 | USD -4,602.70 |
| HOLD_20_SESSIONS | 1 : 1 | 107/110 (3) | 37.38% (28.80–46.84%) | USD -46.05 | USD -4,927.20 | USD -792.60 |
| HOLD_20_SESSIONS | 1 : 6 | 107/110 (3) | 80.37% (71.85–86.79%) | USD 850.72 | USD 91,027.30 | USD -9,376.10 |
| HOLD_20_SESSIONS | 6 : 1 | 107/110 (3) | 17.76% (11.67–26.08%) | USD -1,173.06 | USD -125,517.70 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 107/110 (3) | 69.16% (59.87–77.12%) | USD -4.84 | USD -517.90 | USD -4,305.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 94/110 (16) | 35.11% (26.22–45.17%) | USD -51.09 | USD -4,802.40 | USD -952.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 94/110 (16) | 81.91% (72.93–88.39%) | USD 488.42 | USD 45,911.60 | USD -20,318.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 94/110 (16) | 18.09% (11.61–27.07%) | USD -846.05 | USD -79,528.40 | USD -4,190.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 94/110 (16) | 72.34% (62.56–80.37%) | USD -96.46 | USD -9,066.80 | USD -7,641.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/110 | 0.00% | USD -206,006.75 | USD -334,060.55 |
| -75% | 0/110 | 0.00% | USD -151,741.95 | USD -247,449.30 |
| -50% | 0/110 | 0.00% | USD -97,477.15 | USD -160,838.05 |
| -40% | 0/110 | 0.00% | USD -75,771.24 | USD -126,193.55 |
| -30% | 0/110 | 0.00% | USD -54,065.32 | USD -91,549.05 |
| -25% | 0/110 | 0.00% | USD -43,212.36 | USD -74,226.80 |
| -20% | 0/110 | 0.00% | USD -32,359.40 | USD -56,904.55 |
| -15% | 0/110 | 0.00% | USD -21,506.44 | USD -39,582.30 |
| -10% | 1/110 | 0.91% | USD -10,656.86 | USD -23,103.25 |
| -5% | 51/110 | 46.36% | USD -429.73 | USD -8,803.90 |
| 0% | 110/110 | 100.00% | USD 2,143.85 | USD 589.45 |
| 5% | 110/110 | 100.00% | USD 2,143.85 | USD 589.45 |
| 10% | 110/110 | 100.00% | USD 2,143.85 | USD 589.45 |
| 20% | 110/110 | 100.00% | USD 2,143.85 | USD 589.45 |

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