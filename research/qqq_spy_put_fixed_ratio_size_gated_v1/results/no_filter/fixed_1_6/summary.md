# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 44 checks; 44 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 6; entry and exit require displayed side size for every contract; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 437.43 / USD 2,590.64; mean absolute mismatch USD 2,153.20; mean match score 16.41%.
- Actual selected contract ratios: {'1:6': 44}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 44; entered cohorts: 44; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 44/44 | 33/11/0 | 75.00% (60.56–85.43%) | USD -156.55 | USD 508.40 | USD -6,888.40 | USD -15,946.10 | 0 |
| HOLD_10_SESSIONS | 44/44 | 32/12/0 | 72.73% (58.15–83.65%) | USD -296.37 | USD 769.90 | USD -13,040.40 | USD -16,388.10 | 0 |
| HOLD_20_SESSIONS | 44/44 | 35/9/0 | 79.55% (65.50–88.85%) | USD -607.53 | USD 1,519.90 | USD -26,731.40 | USD -51,851.10 | 0 |
| EXIT_AT_DTE_LE_7 | 37/44 | 29/8/0 | 78.38% (62.80–88.61%) | USD -995.61 | USD 1,835.90 | USD -36,837.70 | USD -37,043.10 | 7 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -12.14 | USD -65.32 |
| HOLD_10_SESSIONS | USD -7.82 | USD -209.45 |
| HOLD_20_SESSIONS | USD -42.57 | USD -485.86 |
| EXIT_AT_DTE_LE_7 | USD 11.86 | USD -928.38 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 44 | 75.00% | USD -77.45 | USD -3,408.00 | USD -15,867.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 44 | 75.00% | USD -86.55 | USD -3,808.40 | USD -15,876.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 44 | 75.00% | USD -112.45 | USD -4,948.00 | USD -15,902.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 44 | 75.00% | USD -121.55 | USD -5,348.40 | USD -15,911.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 44 | 75.00% | USD -147.45 | USD -6,488.00 | USD -15,937.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 44 | 75.00% | USD -156.55 | USD -6,888.40 | USD -15,946.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 44 | 75.00% | USD -217.45 | USD -9,568.00 | USD -16,007.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 44 | 75.00% | USD -226.55 | USD -9,968.40 | USD -16,016.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 44 | 75.00% | USD -217.27 | USD -9,560.00 | USD -16,309.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 44 | 75.00% | USD -226.37 | USD -9,960.40 | USD -16,318.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 44 | 72.73% | USD -252.27 | USD -11,100.00 | USD -16,344.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 44 | 72.73% | USD -261.37 | USD -11,500.40 | USD -16,353.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 44 | 72.73% | USD -287.27 | USD -12,640.00 | USD -16,379.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 44 | 72.73% | USD -296.37 | USD -13,040.40 | USD -16,388.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 44 | 72.73% | USD -357.27 | USD -15,720.00 | USD -16,449.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 44 | 72.73% | USD -366.37 | USD -16,120.40 | USD -16,458.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 44 | 79.55% | USD -528.43 | USD -23,251.00 | USD -51,772.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 44 | 79.55% | USD -537.53 | USD -23,651.40 | USD -51,781.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 44 | 79.55% | USD -563.43 | USD -24,791.00 | USD -51,807.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 44 | 79.55% | USD -572.53 | USD -25,191.40 | USD -51,816.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 44 | 79.55% | USD -598.43 | USD -26,331.00 | USD -51,842.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 44 | 79.55% | USD -607.53 | USD -26,731.40 | USD -51,851.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 44 | 79.55% | USD -668.43 | USD -29,411.00 | USD -51,912.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 44 | 79.55% | USD -677.53 | USD -29,811.40 | USD -51,921.10 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 37 | 78.38% | USD -916.51 | USD -33,911.00 | USD -36,964.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 37 | 78.38% | USD -925.61 | USD -34,247.70 | USD -36,973.10 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 37 | 78.38% | USD -951.51 | USD -35,206.00 | USD -36,999.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 37 | 78.38% | USD -960.61 | USD -35,542.70 | USD -37,008.10 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 37 | 78.38% | USD -986.51 | USD -36,501.00 | USD -37,034.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 37 | 78.38% | USD -995.61 | USD -36,837.70 | USD -37,043.10 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 37 | 78.38% | USD -1,056.51 | USD -39,091.00 | USD -37,104.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 37 | 78.38% | USD -1,065.61 | USD -39,427.70 | USD -37,113.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 44/44 (0) | 36.36% (23.78–51.13%) | USD -45.62 | USD -2,007.40 | USD -1,204.60 |
| HOLD_5_SESSIONS | 1 : 6 | 44/44 (0) | 75.00% (60.56–85.43%) | USD -156.55 | USD -6,888.40 | USD -15,946.10 |
| HOLD_5_SESSIONS | 6 : 1 | 44/44 (0) | 22.73% (12.84–36.99%) | USD -162.80 | USD -7,163.40 | USD -2,665.10 |
| HOLD_5_SESSIONS | 4 : 5 | 44/44 (0) | 59.09% (44.41–72.31%) | USD -204.68 | USD -9,005.80 | USD -7,766.70 |
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
| -100% | 0/44 | 0.00% | USD -204,713.48 | USD -331,969.55 |
| -75% | 0/44 | 0.00% | USD -150,843.06 | USD -245,058.80 |
| -50% | 0/44 | 0.00% | USD -96,972.63 | USD -158,148.05 |
| -40% | 0/44 | 0.00% | USD -75,424.46 | USD -123,383.75 |
| -30% | 0/44 | 0.00% | USD -53,876.29 | USD -88,619.45 |
| -25% | 0/44 | 0.00% | USD -43,102.20 | USD -71,237.30 |
| -20% | 0/44 | 0.00% | USD -32,328.12 | USD -53,855.15 |
| -15% | 0/44 | 0.00% | USD -21,554.03 | USD -36,955.60 |
| -10% | 2/44 | 4.55% | USD -10,767.05 | USD -20,952.95 |
| -5% | 20/44 | 45.45% | USD -772.89 | USD -6,851.20 |
| 0% | 44/44 | 100.00% | USD 2,113.65 | USD 696.45 |
| 5% | 44/44 | 100.00% | USD 2,113.65 | USD 696.45 |
| 10% | 44/44 | 100.00% | USD 2,113.65 | USD 696.45 |
| 20% | 44/44 | 100.00% | USD 2,113.65 | USD 696.45 |

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

Files: trade_episodes.csv, entry_cohort.csv, entry_skips.csv, cost_sensitivity.csv, sizing_sensitivity.csv, expiry_shock_grid.csv, source_manifest.json.