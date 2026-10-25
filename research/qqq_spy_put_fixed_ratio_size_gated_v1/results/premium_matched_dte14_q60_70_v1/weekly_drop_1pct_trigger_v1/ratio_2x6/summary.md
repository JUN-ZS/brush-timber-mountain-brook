# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: spy_weekly_drop_1pct — SPY rolling 5-session close return crosses from above -1% to <= -1%; no correlation gate; entry next observed common session.
- Filter evaluation: 1950 checks; 138 qualified; 1812 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 2 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,015.49 / USD 1,623.52; mean absolute mismatch USD 623.48; mean match score 64.23%.
- Actual selected contract ratios: {'2:6': 138}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 138; entered cohorts: 138; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 137/138 | 103/34/0 | 75.18% (67.33–81.66%) | USD -36.66 | USD 211.60 | USD -5,022.80 | USD -16,800.40 | 1 |
| HOLD_10_SESSIONS | 8/138 | 8/0/0 | 100.00% (67.56–100.00%) | USD 857.35 | USD 301.60 | USD 6,858.80 | USD 85.60 | 130 |
| HOLD_20_SESSIONS | 0/138 | 0/0/0 | — | — | — | — | — | 138 |
| HOLD_20_OR_DTE_LE_7 | 138/138 | 104/34/0 | 75.36% (67.55–81.80%) | USD -22.75 | USD 221.60 | USD -3,139.20 | USD -12,850.40 | 0 |
| EXIT_AT_DTE_LE_7 | 138/138 | 104/34/0 | 75.36% (67.55–81.80%) | USD -22.75 | USD 221.60 | USD -3,139.20 | USD -12,850.40 | 0 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -154.20 | USD 207.94 |
| HOLD_10_SESSIONS | USD -691.00 | USD 1,638.75 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -185.78 | USD 253.43 |
| EXIT_AT_DTE_LE_7 | USD -185.78 | USD 253.43 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 137 | 79.56% | USD 53.74 | USD 7,362.00 | USD -16,710.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 137 | 79.56% | USD 43.34 | USD 5,937.20 | USD -16,720.40 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 137 | 78.83% | USD 13.74 | USD 1,882.00 | USD -16,750.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 137 | 78.10% | USD 3.34 | USD 457.20 | USD -16,760.40 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 137 | 75.91% | USD -26.26 | USD -3,598.00 | USD -16,790.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 137 | 75.18% | USD -36.66 | USD -5,022.80 | USD -16,800.40 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 137 | 68.61% | USD -106.26 | USD -14,558.00 | USD -16,870.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 137 | 67.88% | USD -116.66 | USD -15,982.80 | USD -16,880.40 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 8 | 100.00% | USD 947.75 | USD 7,582.00 | USD 176.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 8 | 100.00% | USD 937.35 | USD 7,498.80 | USD 165.60 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 8 | 100.00% | USD 907.75 | USD 7,262.00 | USD 136.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 8 | 100.00% | USD 897.35 | USD 7,178.80 | USD 125.60 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 8 | 100.00% | USD 867.75 | USD 6,942.00 | USD 96.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 8 | 100.00% | USD 857.35 | USD 6,858.80 | USD 85.60 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 8 | 100.00% | USD 787.75 | USD 6,302.00 | USD 16.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 8 | 100.00% | USD 777.35 | USD 6,218.80 | USD 5.60 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 138 | 82.61% | USD 67.65 | USD 9,336.00 | USD -12,760.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 138 | 81.88% | USD 57.25 | USD 7,900.80 | USD -12,770.40 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 138 | 79.71% | USD 27.65 | USD 3,816.00 | USD -12,800.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 138 | 78.26% | USD 17.25 | USD 2,380.80 | USD -12,810.40 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 138 | 76.09% | USD -12.35 | USD -1,704.00 | USD -12,840.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 138 | 75.36% | USD -22.75 | USD -3,139.20 | USD -12,850.40 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 138 | 69.57% | USD -92.35 | USD -12,744.00 | USD -12,920.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 138 | 66.67% | USD -102.75 | USD -14,179.20 | USD -12,930.40 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 138 | 82.61% | USD 67.65 | USD 9,336.00 | USD -12,760.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 138 | 81.88% | USD 57.25 | USD 7,900.80 | USD -12,770.40 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 138 | 79.71% | USD 27.65 | USD 3,816.00 | USD -12,800.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 138 | 78.26% | USD 17.25 | USD 2,380.80 | USD -12,810.40 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 138 | 76.09% | USD -12.35 | USD -1,704.00 | USD -12,840.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 138 | 75.36% | USD -22.75 | USD -3,139.20 | USD -12,850.40 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 138 | 69.57% | USD -92.35 | USD -12,744.00 | USD -12,920.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 138 | 66.67% | USD -102.75 | USD -14,179.20 | USD -12,930.40 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 137/138 (1) | 24.09% (17.70–31.89%) | USD -65.05 | USD -8,911.20 | USD -729.60 |
| HOLD_5_SESSIONS | 1 : 6 | 137/138 (1) | 79.56% (72.05–85.46%) | USD 51.74 | USD 7,088.30 | USD -20,860.10 |
| HOLD_5_SESSIONS | 6 : 1 | 137/138 (1) | 29.20% (22.23–37.29%) | USD -507.06 | USD -69,466.70 | USD -14,124.10 |
| HOLD_5_SESSIONS | 5 : 5 | 137/138 (1) | 24.09% (17.70–31.89%) | USD -325.23 | USD -44,556.00 | USD -3,648.00 |
| HOLD_10_SESSIONS | 1 : 1 | 8/138 (130) | 12.50% (2.24–47.09%) | USD -94.97 | USD -759.80 | USD -403.60 |
| HOLD_10_SESSIONS | 1 : 6 | 8/138 (130) | 100.00% (67.56–100.00%) | USD 1,214.15 | USD 9,713.20 | USD 209.90 |
| HOLD_10_SESSIONS | 6 : 1 | 8/138 (130) | 12.50% (2.24–47.09%) | USD -1,878.97 | USD -15,031.80 | USD -7,070.10 |
| HOLD_10_SESSIONS | 5 : 5 | 8/138 (130) | 12.50% (2.24–47.09%) | USD -474.88 | USD -3,799.00 | USD -2,018.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/138 (138) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/138 (138) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/138 (138) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/138 (138) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 138/138 (0) | 24.64% (18.20–32.45%) | USD -73.25 | USD -10,108.80 | USD -685.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 138/138 (0) | 81.16% (73.83–86.81%) | USD 81.44 | USD 11,239.20 | USD -15,885.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 138/138 (0) | 26.09% (19.48–33.99%) | USD -594.21 | USD -82,000.80 | USD -12,159.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 138/138 (0) | 24.64% (18.20–32.45%) | USD -366.26 | USD -50,544.00 | USD -3,428.00 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 138/138 (0) | 24.64% (18.20–32.45%) | USD -73.25 | USD -10,108.80 | USD -685.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 138/138 (0) | 81.16% (73.83–86.81%) | USD 81.44 | USD 11,239.20 | USD -15,885.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 138/138 (0) | 26.09% (19.48–33.99%) | USD -594.21 | USD -82,000.80 | USD -12,159.10 |
| EXIT_AT_DTE_LE_7 | 5 : 5 | 138/138 (0) | 24.64% (18.20–32.45%) | USD -366.26 | USD -50,544.00 | USD -3,428.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/138 | 0.00% | USD -172,563.98 | USD -273,543.20 |
| -75% | 0/138 | 0.00% | USD -127,744.17 | USD -203,070.20 |
| -50% | 0/138 | 0.00% | USD -82,924.37 | USD -132,597.20 |
| -40% | 0/138 | 0.00% | USD -64,996.44 | USD -104,408.00 |
| -30% | 0/138 | 0.00% | USD -47,068.52 | USD -76,218.80 |
| -25% | 0/138 | 0.00% | USD -38,104.56 | USD -62,124.20 |
| -20% | 0/138 | 0.00% | USD -29,140.60 | USD -48,029.60 |
| -15% | 0/138 | 0.00% | USD -20,176.64 | USD -33,935.00 |
| -10% | 2/138 | 1.45% | USD -11,241.27 | USD -20,072.60 |
| -5% | 23/138 | 16.67% | USD -2,516.11 | USD -6,996.30 |
| 0% | 130/138 | 94.20% | USD 738.64 | USD -311.20 |
| 5% | 128/138 | 92.75% | USD 564.56 | USD -311.20 |
| 10% | 128/138 | 92.75% | USD 562.83 | USD -311.20 |
| 20% | 128/138 | 92.75% | USD 562.83 | USD -311.20 |

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