# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 399 checks; 36 qualified; 363 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 2 : SPY SHORT PUT 4; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 973.11 / USD 1,889.44; mean absolute mismatch USD 916.33; mean match score 50.92%.
- Actual selected contract ratios: {'2:4': 36}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 36; entered cohorts: 36; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 36/36 | 24/12/0 | 66.67% (50.33–79.79%) | USD 150.31 | USD 192.20 | USD 5,411.20 | USD -1,363.80 | 0 |
| HOLD_10_SESSIONS | 36/36 | 28/8/0 | 77.78% (61.92–88.28%) | USD 302.37 | USD 304.20 | USD 10,885.20 | USD -1,633.80 | 0 |
| HOLD_20_SESSIONS | 34/36 | 30/4/0 | 88.24% (73.38–95.33%) | USD 577.08 | USD 522.20 | USD 19,620.80 | USD -1,493.80 | 2 |
| EXIT_AT_DTE_LE_7 | 30/36 | 25/5/0 | 83.33% (66.44–92.66%) | USD 213.20 | USD 564.20 | USD 6,396.00 | USD -4,031.80 | 6 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -220.89 | USD 439.00 |
| HOLD_10_SESSIONS | USD -329.83 | USD 700.00 |
| HOLD_20_SESSIONS | USD -606.53 | USD 1,251.41 |
| EXIT_AT_DTE_LE_7 | USD -341.00 | USD 622.00 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 36 | 72.22% | USD 218.11 | USD 7,852.00 | USD -1,296.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 36 | 72.22% | USD 210.31 | USD 7,571.20 | USD -1,303.80 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 36 | 69.44% | USD 188.11 | USD 6,772.00 | USD -1,326.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 36 | 69.44% | USD 180.31 | USD 6,491.20 | USD -1,333.80 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 36 | 66.67% | USD 158.11 | USD 5,692.00 | USD -1,356.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 36 | 66.67% | USD 150.31 | USD 5,411.20 | USD -1,363.80 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 36 | 61.11% | USD 98.11 | USD 3,532.00 | USD -1,416.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 36 | 61.11% | USD 90.31 | USD 3,251.20 | USD -1,423.80 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 36 | 77.78% | USD 370.17 | USD 13,326.00 | USD -1,566.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 36 | 77.78% | USD 362.37 | USD 13,045.20 | USD -1,573.80 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 36 | 77.78% | USD 340.17 | USD 12,246.00 | USD -1,596.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 36 | 77.78% | USD 332.37 | USD 11,965.20 | USD -1,603.80 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 36 | 77.78% | USD 310.17 | USD 11,166.00 | USD -1,626.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 36 | 77.78% | USD 302.37 | USD 10,885.20 | USD -1,633.80 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 36 | 77.78% | USD 250.17 | USD 9,006.00 | USD -1,686.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 36 | 77.78% | USD 242.37 | USD 8,725.20 | USD -1,693.80 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 34 | 91.18% | USD 644.88 | USD 21,926.00 | USD -1,426.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 34 | 91.18% | USD 637.08 | USD 21,660.80 | USD -1,433.80 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 34 | 91.18% | USD 614.88 | USD 20,906.00 | USD -1,456.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 34 | 91.18% | USD 607.08 | USD 20,640.80 | USD -1,463.80 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 34 | 88.24% | USD 584.88 | USD 19,886.00 | USD -1,486.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 34 | 88.24% | USD 577.08 | USD 19,620.80 | USD -1,493.80 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 34 | 85.29% | USD 524.88 | USD 17,846.00 | USD -1,546.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 34 | 85.29% | USD 517.08 | USD 17,580.80 | USD -1,553.80 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 30 | 83.33% | USD 281.00 | USD 8,430.00 | USD -3,964.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 30 | 83.33% | USD 273.20 | USD 8,196.00 | USD -3,971.80 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 30 | 83.33% | USD 251.00 | USD 7,530.00 | USD -3,994.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 30 | 83.33% | USD 243.20 | USD 7,296.00 | USD -4,001.80 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 30 | 83.33% | USD 221.00 | USD 6,630.00 | USD -4,024.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 30 | 83.33% | USD 213.20 | USD 6,396.00 | USD -4,031.80 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 30 | 83.33% | USD 161.00 | USD 4,830.00 | USD -4,084.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 30 | 83.33% | USD 153.20 | USD 4,596.00 | USD -4,091.80 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 36/36 (0) | 33.33% (20.21–49.67%) | USD -23.29 | USD -838.60 | USD -152.60 |
| HOLD_5_SESSIONS | 1 : 6 | 36/36 (0) | 69.44% (53.14–82.00%) | USD 468.96 | USD 16,882.40 | USD -4,827.10 |
| HOLD_5_SESSIONS | 6 : 1 | 36/36 (0) | 16.67% (7.87–31.89%) | USD -632.02 | USD -22,752.60 | USD -5,569.10 |
| HOLD_5_SESSIONS | 4 : 5 | 36/36 (0) | 58.33% (42.20–72.86%) | USD 5.27 | USD 189.80 | USD -787.70 |
| HOLD_10_SESSIONS | 1 : 1 | 36/36 (0) | 36.11% (22.48–52.42%) | USD -12.52 | USD -450.60 | USD -143.60 |
| HOLD_10_SESSIONS | 1 : 6 | 36/36 (0) | 80.56% (64.97–90.25%) | USD 805.98 | USD 29,015.40 | USD -3,830.10 |
| HOLD_10_SESSIONS | 6 : 1 | 36/36 (0) | 16.67% (7.87–31.89%) | USD -893.60 | USD -32,169.60 | USD -7,173.10 |
| HOLD_10_SESSIONS | 4 : 5 | 36/36 (0) | 63.89% (47.58–77.52%) | USD 113.63 | USD 4,090.80 | USD -1,007.70 |
| HOLD_20_SESSIONS | 1 : 1 | 34/36 (2) | 41.18% (26.37–57.78%) | USD -13.01 | USD -442.40 | USD -382.60 |
| HOLD_20_SESSIONS | 1 : 6 | 34/36 (2) | 88.24% (73.38–95.33%) | USD 1,494.75 | USD 50,821.60 | USD -2,204.10 |
| HOLD_20_SESSIONS | 6 : 1 | 34/36 (2) | 5.88% (1.63–19.09%) | USD -1,585.84 | USD -53,918.40 | USD -7,649.10 |
| HOLD_20_SESSIONS | 4 : 5 | 34/36 (2) | 73.53% (56.88–85.40%) | USD 249.51 | USD 8,483.20 | USD -1,894.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 30/36 (6) | 36.67% (21.87–54.49%) | USD -37.60 | USD -1,128.00 | USD -762.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 30/36 (6) | 80.00% (62.69–90.49%) | USD 683.40 | USD 20,502.00 | USD -8,997.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 30/36 (6) | 16.67% (7.34–33.56%) | USD -946.60 | USD -28,398.00 | USD -4,765.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 30/36 (6) | 70.00% (52.12–83.34%) | USD -6.20 | USD -186.00 | USD -4,303.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/36 | 0.00% | USD -95,803.68 | USD -141,445.90 |
| -75% | 0/36 | 0.00% | USD -70,733.91 | USD -105,061.90 |
| -50% | 0/36 | 0.00% | USD -45,664.15 | USD -68,677.90 |
| -40% | 0/36 | 0.00% | USD -35,636.24 | USD -54,124.30 |
| -30% | 0/36 | 0.00% | USD -25,608.34 | USD -39,570.70 |
| -25% | 0/36 | 0.00% | USD -20,594.39 | USD -32,293.90 |
| -20% | 0/36 | 0.00% | USD -15,580.43 | USD -25,017.10 |
| -15% | 0/36 | 0.00% | USD -10,566.48 | USD -17,740.30 |
| -10% | 1/36 | 2.78% | USD -5,552.57 | USD -10,808.50 |
| -5% | 14/36 | 38.89% | USD -686.92 | USD -4,261.00 |
| 0% | 36/36 | 100.00% | USD 882.43 | USD 290.10 |
| 5% | 36/36 | 100.00% | USD 882.43 | USD 290.10 |
| 10% | 36/36 | 100.00% | USD 882.43 | USD 290.10 |
| 20% | 36/36 | 100.00% | USD 882.43 | USD 290.10 |

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