# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 392 checks; 392 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 7–21 (target 14); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 1,394.85 / USD 700.24; mean absolute mismatch USD 702.84; mean match score 47.62%.
- Actual selected contract ratios: {'1:3': 392}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 392; entered cohorts: 392; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 391/392 | 193/198/0 | 49.36% (44.44–54.30%) | USD -62.16 | USD -4.20 | USD -24,305.20 | USD -7,446.20 | 1 |
| HOLD_10_SESSIONS | 63/392 | 28/35/0 | 44.44% (32.85–56.68%) | USD -468.34 | USD -67.20 | USD -29,505.60 | USD -14,547.20 | 329 |
| HOLD_20_SESSIONS | 0/392 | 0/0/0 | — | — | — | — | — | 392 |
| HOLD_20_OR_DTE_LE_7 | 391/392 | 184/207/0 | 47.06% (42.16–52.01%) | USD -127.80 | USD -38.20 | USD -49,971.20 | USD -10,542.20 | 1 |
| EXIT_AT_DTE_LE_7 | 391/392 | 184/207/0 | 47.06% (42.16–52.01%) | USD -127.80 | USD -38.20 | USD -49,971.20 | USD -10,542.20 | 1 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -214.27 | USD 197.31 |
| HOLD_10_SESSIONS | USD -106.57 | USD -316.57 |
| HOLD_20_SESSIONS | — | — |
| HOLD_20_OR_DTE_LE_7 | USD -148.63 | USD 66.03 |
| EXIT_AT_DTE_LE_7 | USD -148.63 | USD 66.03 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 391 | 54.22% | USD -16.96 | USD -6,632.00 | USD -7,401.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 391 | 53.96% | USD -22.16 | USD -8,665.20 | USD -7,406.20 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 391 | 52.17% | USD -36.96 | USD -14,452.00 | USD -7,421.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 391 | 51.66% | USD -42.16 | USD -16,485.20 | USD -7,426.20 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 391 | 50.38% | USD -56.96 | USD -22,272.00 | USD -7,441.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 391 | 49.36% | USD -62.16 | USD -24,305.20 | USD -7,446.20 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 391 | 46.80% | USD -96.96 | USD -37,912.00 | USD -7,481.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 391 | 46.04% | USD -102.16 | USD -39,945.20 | USD -7,486.20 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 63 | 46.03% | USD -423.14 | USD -26,658.00 | USD -14,502.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 63 | 46.03% | USD -428.34 | USD -26,985.60 | USD -14,507.20 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 63 | 44.44% | USD -443.14 | USD -27,918.00 | USD -14,522.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 63 | 44.44% | USD -448.34 | USD -28,245.60 | USD -14,527.20 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 63 | 44.44% | USD -463.14 | USD -29,178.00 | USD -14,542.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 63 | 44.44% | USD -468.34 | USD -29,505.60 | USD -14,547.20 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 63 | 42.86% | USD -503.14 | USD -31,698.00 | USD -14,582.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 63 | 42.86% | USD -508.34 | USD -32,025.60 | USD -14,587.20 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 0 | — | — | — | — |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 0 | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 391 | 51.66% | USD -82.60 | USD -32,298.00 | USD -10,497.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 391 | 50.38% | USD -87.80 | USD -34,331.20 | USD -10,502.20 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 391 | 49.10% | USD -102.60 | USD -40,118.00 | USD -10,517.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 391 | 48.85% | USD -107.80 | USD -42,151.20 | USD -10,522.20 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 391 | 47.57% | USD -122.60 | USD -47,938.00 | USD -10,537.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 391 | 47.06% | USD -127.80 | USD -49,971.20 | USD -10,542.20 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 391 | 45.52% | USD -162.60 | USD -63,578.00 | USD -10,577.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 391 | 45.27% | USD -167.80 | USD -65,611.20 | USD -10,582.20 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 391 | 51.66% | USD -82.60 | USD -32,298.00 | USD -10,497.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 391 | 50.38% | USD -87.80 | USD -34,331.20 | USD -10,502.20 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 391 | 49.10% | USD -102.60 | USD -40,118.00 | USD -10,517.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 391 | 48.85% | USD -107.80 | USD -42,151.20 | USD -10,522.20 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 391 | 47.57% | USD -122.60 | USD -47,938.00 | USD -10,537.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 391 | 47.06% | USD -127.80 | USD -49,971.20 | USD -10,542.20 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 391 | 45.52% | USD -162.60 | USD -63,578.00 | USD -10,577.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 391 | 45.27% | USD -167.80 | USD -65,611.20 | USD -10,582.20 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 391/392 (1) | 35.29% (30.72–40.15%) | USD -171.10 | USD -66,900.60 | USD -2,398.60 |
| HOLD_5_SESSIONS | 1 : 6 | 391/392 (1) | 67.77% (62.99–72.21%) | USD 101.25 | USD 39,587.90 | USD -17,572.10 |
| HOLD_5_SESSIONS | 6 : 1 | 391/392 (1) | 33.76% (29.25–38.58%) | USD -1,298.96 | USD -507,892.10 | USD -16,560.10 |
| HOLD_5_SESSIONS | 5 : 5 | 391/392 (1) | 35.29% (30.72–40.15%) | USD -855.51 | USD -334,503.00 | USD -11,993.00 |
| HOLD_10_SESSIONS | 1 : 1 | 63/392 (329) | 33.33% (22.95–45.63%) | USD -234.70 | USD -14,785.80 | USD -2,320.60 |
| HOLD_10_SESSIONS | 1 : 6 | 63/392 (329) | 79.37% (67.83–87.52%) | USD -818.81 | USD -51,585.30 | USD -32,887.10 |
| HOLD_10_SESSIONS | 6 : 1 | 63/392 (329) | 34.92% (24.33–47.25%) | USD -824.05 | USD -51,915.30 | USD -12,137.10 |
| HOLD_10_SESSIONS | 5 : 5 | 63/392 (329) | 33.33% (22.95–45.63%) | USD -1,173.48 | USD -73,929.00 | USD -11,603.00 |
| HOLD_20_SESSIONS | 1 : 1 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 1 : 6 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 6 : 1 | 0/392 (392) | — | — | — | — |
| HOLD_20_SESSIONS | 5 : 5 | 0/392 (392) | — | — | — | — |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 391/392 (1) | 36.57% (31.95–41.46%) | USD -149.22 | USD -58,346.60 | USD -2,199.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 391/392 (1) | 66.24% (61.42–70.75%) | USD -95.67 | USD -37,408.10 | USD -24,688.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 391/392 (1) | 34.78% (30.23–39.63%) | USD -948.90 | USD -371,018.10 | USD -19,207.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 391/392 (1) | 36.57% (31.95–41.46%) | USD -746.12 | USD -291,733.00 | USD -10,998.00 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 391/392 (1) | 36.57% (31.95–41.46%) | USD -149.22 | USD -58,346.60 | USD -2,199.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 391/392 (1) | 66.24% (61.42–70.75%) | USD -95.67 | USD -37,408.10 | USD -24,688.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 391/392 (1) | 34.78% (30.23–39.63%) | USD -948.90 | USD -371,018.10 | USD -19,207.10 |
| EXIT_AT_DTE_LE_7 | 5 : 5 | 391/392 (1) | 36.57% (31.95–41.46%) | USD -746.12 | USD -291,733.00 | USD -10,998.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 0/392 | 0.00% | USD -87,985.25 | USD -138,911.60 |
| -75% | 0/392 | 0.00% | USD -65,143.53 | USD -103,205.10 |
| -50% | 0/392 | 0.00% | USD -42,301.81 | USD -67,498.60 |
| -40% | 0/392 | 0.00% | USD -33,165.13 | USD -53,432.40 |
| -30% | 0/392 | 0.00% | USD -24,028.44 | USD -39,367.70 |
| -25% | 0/392 | 0.00% | USD -19,460.09 | USD -32,335.35 |
| -20% | 0/392 | 0.00% | USD -14,891.75 | USD -25,303.00 |
| -15% | 2/392 | 0.51% | USD -10,323.41 | USD -18,270.65 |
| -10% | 6/392 | 1.53% | USD -5,763.13 | USD -11,238.30 |
| -5% | 76/392 | 19.39% | USD -1,272.04 | USD -4,561.10 |
| 0% | 376/392 | 95.92% | USD 552.30 | USD -221.60 |
| 5% | 27/392 | 6.89% | USD -533.84 | USD -1,528.60 |
| 10% | 7/392 | 1.79% | USD -684.48 | USD -1,963.60 |
| 20% | 4/392 | 1.02% | USD -711.59 | USD -2,187.60 |

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