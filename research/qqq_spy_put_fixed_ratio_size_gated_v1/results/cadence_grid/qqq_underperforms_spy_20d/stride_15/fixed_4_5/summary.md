# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: qqq_underperforms_spy_20d — Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session.
- Filter evaluation: 834 checks; 81 qualified; 753 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 4 : SPY SHORT PUT 5; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,829.73 / USD 2,197.96; mean absolute mismatch USD 441.91; mean match score 79.99%.
- Actual selected contract ratios: {'4:5': 81}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 81; entered cohorts: 81; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 80/81 | 37/43/0 | 46.25% (35.75–57.10%) | USD -131.95 | USD -74.70 | USD -10,556.00 | USD -2,180.70 | 1 |
| HOLD_10_SESSIONS | 80/81 | 41/39/0 | 51.25% (40.49–61.89%) | USD -291.20 | USD 11.80 | USD -23,296.00 | USD -7,319.70 | 1 |
| HOLD_20_SESSIONS | 78/81 | 55/23/0 | 70.51% (59.62–79.48%) | USD -1.34 | USD 163.80 | USD -104.60 | USD -3,888.70 | 3 |
| EXIT_AT_DTE_LE_7 | 70/81 | 49/21/0 | 70.00% (58.46–79.46%) | USD -157.73 | USD 188.30 | USD -11,041.00 | USD -8,108.70 | 11 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -7.75 | USD -22.50 |
| HOLD_10_SESSIONS | USD -212.75 | USD 23.25 |
| HOLD_20_SESSIONS | USD -459.64 | USD 560.00 |
| EXIT_AT_DTE_LE_7 | USD -395.31 | USD 339.29 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 80 | 51.25% | USD -30.25 | USD -2,420.00 | USD -2,079.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 80 | 50.00% | USD -41.95 | USD -3,356.00 | USD -2,090.70 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 80 | 50.00% | USD -75.25 | USD -6,020.00 | USD -2,124.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 80 | 48.75% | USD -86.95 | USD -6,956.00 | USD -2,135.70 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 80 | 46.25% | USD -120.25 | USD -9,620.00 | USD -2,169.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 80 | 46.25% | USD -131.95 | USD -10,556.00 | USD -2,180.70 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 80 | 35.00% | USD -210.25 | USD -16,820.00 | USD -2,259.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 80 | 33.75% | USD -221.95 | USD -17,756.00 | USD -2,270.70 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 80 | 61.25% | USD -189.50 | USD -15,160.00 | USD -7,218.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 80 | 61.25% | USD -201.20 | USD -16,096.00 | USD -7,229.70 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 80 | 55.00% | USD -234.50 | USD -18,760.00 | USD -7,263.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 80 | 53.75% | USD -246.20 | USD -19,696.00 | USD -7,274.70 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 80 | 52.50% | USD -279.50 | USD -22,360.00 | USD -7,308.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 80 | 51.25% | USD -291.20 | USD -23,296.00 | USD -7,319.70 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 80 | 43.75% | USD -369.50 | USD -29,560.00 | USD -7,398.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 80 | 40.00% | USD -381.20 | USD -30,496.00 | USD -7,409.70 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 78 | 74.36% | USD 100.36 | USD 7,828.00 | USD -3,787.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 78 | 74.36% | USD 88.66 | USD 6,915.40 | USD -3,798.70 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 78 | 73.08% | USD 55.36 | USD 4,318.00 | USD -3,832.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 78 | 73.08% | USD 43.66 | USD 3,405.40 | USD -3,843.70 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 78 | 73.08% | USD 10.36 | USD 808.00 | USD -3,877.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 78 | 70.51% | USD -1.34 | USD -104.60 | USD -3,888.70 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 78 | 56.41% | USD -79.64 | USD -6,212.00 | USD -3,967.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 78 | 56.41% | USD -91.34 | USD -7,124.60 | USD -3,978.70 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 70 | 75.71% | USD -56.03 | USD -3,922.00 | USD -8,007.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 70 | 75.71% | USD -67.73 | USD -4,741.00 | USD -8,018.70 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 70 | 72.86% | USD -101.03 | USD -7,072.00 | USD -8,052.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 70 | 71.43% | USD -112.73 | USD -7,891.00 | USD -8,063.70 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 70 | 70.00% | USD -146.03 | USD -10,222.00 | USD -8,097.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 70 | 70.00% | USD -157.73 | USD -11,041.00 | USD -8,108.70 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 70 | 60.00% | USD -236.03 | USD -16,522.00 | USD -8,187.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 70 | 60.00% | USD -247.73 | USD -17,341.00 | USD -8,198.70 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 80/81 (1) | 31.25% (22.15–42.07%) | USD -29.04 | USD -2,323.00 | USD -430.60 |
| HOLD_5_SESSIONS | 1 : 6 | 80/81 (1) | 56.25% (45.34–66.59%) | USD -108.04 | USD -8,643.00 | USD -4,827.10 |
| HOLD_5_SESSIONS | 6 : 1 | 80/81 (1) | 31.25% (22.15–42.07%) | USD -95.22 | USD -7,618.00 | USD -3,928.10 |
| HOLD_5_SESSIONS | 4 : 5 | 80/81 (1) | 46.25% (35.75–57.10%) | USD -131.95 | USD -10,556.00 | USD -2,180.70 |
| HOLD_10_SESSIONS | 1 : 1 | 80/81 (1) | 30.00% (21.06–40.77%) | USD -71.14 | USD -5,691.00 | USD -1,001.60 |
| HOLD_10_SESSIONS | 1 : 6 | 80/81 (1) | 72.50% (61.86–81.08%) | USD -104.39 | USD -8,351.00 | USD -18,784.10 |
| HOLD_10_SESSIONS | 6 : 1 | 80/81 (1) | 22.50% (14.73–32.79%) | USD -393.57 | USD -31,486.00 | USD -4,023.10 |
| HOLD_10_SESSIONS | 4 : 5 | 80/81 (1) | 51.25% (40.49–61.89%) | USD -291.20 | USD -23,296.00 | USD -7,319.70 |
| HOLD_20_SESSIONS | 1 : 1 | 78/81 (3) | 30.77% (21.63–41.71%) | USD -25.51 | USD -1,989.80 | USD -612.60 |
| HOLD_20_SESSIONS | 1 : 6 | 78/81 (3) | 79.49% (69.25–86.96%) | USD 477.99 | USD 37,283.20 | USD -12,548.10 |
| HOLD_20_SESSIONS | 6 : 1 | 78/81 (3) | 19.23% (12.02–29.33%) | USD -656.56 | USD -51,211.80 | USD -4,716.10 |
| HOLD_20_SESSIONS | 4 : 5 | 78/81 (3) | 70.51% (59.62–79.48%) | USD -1.34 | USD -104.60 | USD -3,888.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 70/81 (11) | 32.86% (23.00–44.50%) | USD -53.57 | USD -3,750.00 | USD -1,422.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 70/81 (11) | 82.86% (72.38–89.91%) | USD 229.21 | USD 16,045.00 | USD -23,852.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 70/81 (11) | 12.86% (6.91–22.66%) | USD -604.21 | USD -42,295.00 | USD -4,207.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 70/81 (11) | 70.00% (58.46–79.46%) | USD -157.73 | USD -11,041.00 | USD -8,108.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/81 | 0.00% | USD -74,208.10 | USD -94,322.85 |
| -75% | 0/81 | 0.00% | USD -55,090.93 | USD -70,290.60 |
| -50% | 0/81 | 0.00% | USD -35,973.77 | USD -46,476.35 |
| -40% | 0/81 | 0.00% | USD -28,326.90 | USD -37,150.25 |
| -30% | 0/81 | 0.00% | USD -20,680.04 | USD -28,013.15 |
| -25% | 0/81 | 0.00% | USD -16,856.61 | USD -23,444.60 |
| -20% | 0/81 | 0.00% | USD -13,033.17 | USD -18,876.05 |
| -15% | 0/81 | 0.00% | USD -9,209.74 | USD -14,307.50 |
| -10% | 2/81 | 2.47% | USD -5,378.94 | USD -9,738.95 |
| -5% | 27/81 | 33.33% | USD -1,346.04 | USD -5,170.40 |
| 0% | 70/81 | 86.42% | USD 317.38 | USD -1,801.85 |
| 5% | 70/81 | 86.42% | USD 317.38 | USD -1,801.85 |
| 10% | 70/81 | 86.42% | USD 317.38 | USD -1,801.85 |
| 20% | 70/81 | 86.42% | USD 317.38 | USD -1,801.85 |

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