# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 54–66 (target 60); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 275.47 / USD 1,471.20; mean absolute mismatch USD 1,195.73; mean match score 18.71%.
- Actual selected contract ratios: {'1:6': 115}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 115; entered cohorts: 115; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 114/115 | 56/58/0 | 49.12% (40.13–58.18%) | USD -212.45 | USD -7.10 | USD -24,219.40 | USD -3,874.10 | 1 |
| HOLD_5_OR_DTE_LE_7 | 114/115 | 56/58/0 | 49.12% (40.13–58.18%) | USD -212.45 | USD -7.10 | USD -24,219.40 | USD -3,874.10 | 1 |
| HOLD_5_OR_DTE_LE_14 | 114/115 | 56/58/0 | 49.12% (40.13–58.18%) | USD -212.45 | USD -7.10 | USD -24,219.40 | USD -3,874.10 | 1 |
| HOLD_10_SESSIONS | 114/115 | 60/54/0 | 52.63% (43.53–61.56%) | USD -306.98 | USD 99.90 | USD -34,995.40 | USD -5,389.10 | 1 |
| HOLD_10_OR_DTE_LE_7 | 114/115 | 60/54/0 | 52.63% (43.53–61.56%) | USD -306.98 | USD 99.90 | USD -34,995.40 | USD -5,389.10 | 1 |
| HOLD_10_OR_DTE_LE_14 | 114/115 | 60/54/0 | 52.63% (43.53–61.56%) | USD -306.98 | USD 99.90 | USD -34,995.40 | USD -5,389.10 | 1 |
| HOLD_15_SESSIONS | 113/115 | 64/49/0 | 56.64% (47.43–65.41%) | USD -307.39 | USD 172.90 | USD -34,735.30 | USD -8,425.10 | 2 |
| HOLD_15_OR_DTE_LE_7 | 113/115 | 64/49/0 | 56.64% (47.43–65.41%) | USD -307.39 | USD 172.90 | USD -34,735.30 | USD -8,425.10 | 2 |
| HOLD_15_OR_DTE_LE_14 | 113/115 | 64/49/0 | 56.64% (47.43–65.41%) | USD -307.39 | USD 172.90 | USD -34,735.30 | USD -8,425.10 | 2 |
| HOLD_20_SESSIONS | 113/115 | 56/57/0 | 49.56% (40.51–58.64%) | USD -445.95 | USD -15.10 | USD -50,392.30 | USD -7,642.10 | 2 |
| HOLD_20_OR_DTE_LE_7 | 113/115 | 56/57/0 | 49.56% (40.51–58.64%) | USD -445.95 | USD -15.10 | USD -50,392.30 | USD -7,642.10 | 2 |
| HOLD_20_OR_DTE_LE_14 | 113/115 | 56/57/0 | 49.56% (40.51–58.64%) | USD -445.95 | USD -15.10 | USD -50,392.30 | USD -7,642.10 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 15.18 | USD -148.53 |
| HOLD_5_OR_DTE_LE_7 | USD 15.18 | USD -148.53 |
| HOLD_5_OR_DTE_LE_14 | USD 15.18 | USD -148.53 |
| HOLD_10_SESSIONS | USD 37.02 | USD -264.89 |
| HOLD_10_OR_DTE_LE_7 | USD 37.02 | USD -264.89 |
| HOLD_10_OR_DTE_LE_14 | USD 37.02 | USD -264.89 |
| HOLD_15_SESSIONS | USD 59.28 | USD -287.58 |
| HOLD_15_OR_DTE_LE_7 | USD 59.28 | USD -287.58 |
| HOLD_15_OR_DTE_LE_14 | USD 59.28 | USD -287.58 |
| HOLD_20_SESSIONS | USD 83.84 | USD -450.69 |
| HOLD_20_OR_DTE_LE_7 | USD 83.84 | USD -450.69 |
| HOLD_20_OR_DTE_LE_14 | USD 83.84 | USD -450.69 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 114 | 55.26% | USD -133.35 | USD -15,202.00 | USD -3,795.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 114 | 52.63% | USD -142.45 | USD -16,239.40 | USD -3,804.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 114 | 51.75% | USD -168.35 | USD -19,192.00 | USD -3,830.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 114 | 51.75% | USD -177.45 | USD -20,229.40 | USD -3,839.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 114 | 50.00% | USD -203.35 | USD -23,182.00 | USD -3,865.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 114 | 49.12% | USD -212.45 | USD -24,219.40 | USD -3,874.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 114 | 47.37% | USD -273.35 | USD -31,162.00 | USD -3,935.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 114 | 46.49% | USD -282.45 | USD -32,199.40 | USD -3,944.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 114 | 55.26% | USD -133.35 | USD -15,202.00 | USD -3,795.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 114 | 52.63% | USD -142.45 | USD -16,239.40 | USD -3,804.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 114 | 51.75% | USD -168.35 | USD -19,192.00 | USD -3,830.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 114 | 51.75% | USD -177.45 | USD -20,229.40 | USD -3,839.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 114 | 50.00% | USD -203.35 | USD -23,182.00 | USD -3,865.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 114 | 49.12% | USD -212.45 | USD -24,219.40 | USD -3,874.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 114 | 47.37% | USD -273.35 | USD -31,162.00 | USD -3,935.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 114 | 46.49% | USD -282.45 | USD -32,199.40 | USD -3,944.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 114 | 55.26% | USD -133.35 | USD -15,202.00 | USD -3,795.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 114 | 52.63% | USD -142.45 | USD -16,239.40 | USD -3,804.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 114 | 51.75% | USD -168.35 | USD -19,192.00 | USD -3,830.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 114 | 51.75% | USD -177.45 | USD -20,229.40 | USD -3,839.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 114 | 50.00% | USD -203.35 | USD -23,182.00 | USD -3,865.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 114 | 49.12% | USD -212.45 | USD -24,219.40 | USD -3,874.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 114 | 47.37% | USD -273.35 | USD -31,162.00 | USD -3,935.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 114 | 46.49% | USD -282.45 | USD -32,199.40 | USD -3,944.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 114 | 57.02% | USD -227.88 | USD -25,978.00 | USD -5,310.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 114 | 56.14% | USD -236.98 | USD -27,015.40 | USD -5,319.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 114 | 55.26% | USD -262.88 | USD -29,968.00 | USD -5,345.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 114 | 54.39% | USD -271.98 | USD -31,005.40 | USD -5,354.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 114 | 53.51% | USD -297.88 | USD -33,958.00 | USD -5,380.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 114 | 52.63% | USD -306.98 | USD -34,995.40 | USD -5,389.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 114 | 50.88% | USD -367.88 | USD -41,938.00 | USD -5,450.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 114 | 50.88% | USD -376.98 | USD -42,975.40 | USD -5,459.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 114 | 57.02% | USD -227.88 | USD -25,978.00 | USD -5,310.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 114 | 56.14% | USD -236.98 | USD -27,015.40 | USD -5,319.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 114 | 55.26% | USD -262.88 | USD -29,968.00 | USD -5,345.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 114 | 54.39% | USD -271.98 | USD -31,005.40 | USD -5,354.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 114 | 53.51% | USD -297.88 | USD -33,958.00 | USD -5,380.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 114 | 52.63% | USD -306.98 | USD -34,995.40 | USD -5,389.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 114 | 50.88% | USD -367.88 | USD -41,938.00 | USD -5,450.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 114 | 50.88% | USD -376.98 | USD -42,975.40 | USD -5,459.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 114 | 57.02% | USD -227.88 | USD -25,978.00 | USD -5,310.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 114 | 56.14% | USD -236.98 | USD -27,015.40 | USD -5,319.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 114 | 55.26% | USD -262.88 | USD -29,968.00 | USD -5,345.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 114 | 54.39% | USD -271.98 | USD -31,005.40 | USD -5,354.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 114 | 53.51% | USD -297.88 | USD -33,958.00 | USD -5,380.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 114 | 52.63% | USD -306.98 | USD -34,995.40 | USD -5,389.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 114 | 50.88% | USD -367.88 | USD -41,938.00 | USD -5,450.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 114 | 50.88% | USD -376.98 | USD -42,975.40 | USD -5,459.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 113 | 61.95% | USD -228.29 | USD -25,797.00 | USD -8,346.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 113 | 61.06% | USD -237.39 | USD -26,825.30 | USD -8,355.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 113 | 60.18% | USD -263.29 | USD -29,752.00 | USD -8,381.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 113 | 59.29% | USD -272.39 | USD -30,780.30 | USD -8,390.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 113 | 56.64% | USD -298.29 | USD -33,707.00 | USD -8,416.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 113 | 56.64% | USD -307.39 | USD -34,735.30 | USD -8,425.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 113 | 55.75% | USD -368.29 | USD -41,617.00 | USD -8,486.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 113 | 55.75% | USD -377.39 | USD -42,645.30 | USD -8,495.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 113 | 61.95% | USD -228.29 | USD -25,797.00 | USD -8,346.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 113 | 61.06% | USD -237.39 | USD -26,825.30 | USD -8,355.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 113 | 60.18% | USD -263.29 | USD -29,752.00 | USD -8,381.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 113 | 59.29% | USD -272.39 | USD -30,780.30 | USD -8,390.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 113 | 56.64% | USD -298.29 | USD -33,707.00 | USD -8,416.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 113 | 56.64% | USD -307.39 | USD -34,735.30 | USD -8,425.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 113 | 55.75% | USD -368.29 | USD -41,617.00 | USD -8,486.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 113 | 55.75% | USD -377.39 | USD -42,645.30 | USD -8,495.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 113 | 61.95% | USD -228.29 | USD -25,797.00 | USD -8,346.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 113 | 61.06% | USD -237.39 | USD -26,825.30 | USD -8,355.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 113 | 60.18% | USD -263.29 | USD -29,752.00 | USD -8,381.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 113 | 59.29% | USD -272.39 | USD -30,780.30 | USD -8,390.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 113 | 56.64% | USD -298.29 | USD -33,707.00 | USD -8,416.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 113 | 56.64% | USD -307.39 | USD -34,735.30 | USD -8,425.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 113 | 55.75% | USD -368.29 | USD -41,617.00 | USD -8,486.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 113 | 55.75% | USD -377.39 | USD -42,645.30 | USD -8,495.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 113 | 55.75% | USD -366.85 | USD -41,454.00 | USD -7,563.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 113 | 55.75% | USD -375.95 | USD -42,482.30 | USD -7,572.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 113 | 53.98% | USD -401.85 | USD -45,409.00 | USD -7,598.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 113 | 51.33% | USD -410.95 | USD -46,437.30 | USD -7,607.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 113 | 49.56% | USD -436.85 | USD -49,364.00 | USD -7,633.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 113 | 49.56% | USD -445.95 | USD -50,392.30 | USD -7,642.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 113 | 47.79% | USD -506.85 | USD -57,274.00 | USD -7,703.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 113 | 47.79% | USD -515.95 | USD -58,302.30 | USD -7,712.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 113 | 55.75% | USD -366.85 | USD -41,454.00 | USD -7,563.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 113 | 55.75% | USD -375.95 | USD -42,482.30 | USD -7,572.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 113 | 53.98% | USD -401.85 | USD -45,409.00 | USD -7,598.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 113 | 51.33% | USD -410.95 | USD -46,437.30 | USD -7,607.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 113 | 49.56% | USD -436.85 | USD -49,364.00 | USD -7,633.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 113 | 49.56% | USD -445.95 | USD -50,392.30 | USD -7,642.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 113 | 47.79% | USD -506.85 | USD -57,274.00 | USD -7,703.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 113 | 47.79% | USD -515.95 | USD -58,302.30 | USD -7,712.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 113 | 55.75% | USD -366.85 | USD -41,454.00 | USD -7,563.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 113 | 55.75% | USD -375.95 | USD -42,482.30 | USD -7,572.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 113 | 53.98% | USD -401.85 | USD -45,409.00 | USD -7,598.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 113 | 51.33% | USD -410.95 | USD -46,437.30 | USD -7,607.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 113 | 49.56% | USD -436.85 | USD -49,364.00 | USD -7,633.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 113 | 49.56% | USD -445.95 | USD -50,392.30 | USD -7,642.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 113 | 47.79% | USD -506.85 | USD -57,274.00 | USD -7,703.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 113 | 47.79% | USD -515.95 | USD -58,302.30 | USD -7,712.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 114/115 (1) | 22.81% (16.07–31.32%) | USD -32.18 | USD -3,668.40 | USD -537.60 |
| HOLD_5_SESSIONS | 1 : 6 | 114/115 (1) | 49.12% (40.13–58.18%) | USD -212.45 | USD -24,219.40 | USD -3,874.10 |
| HOLD_5_SESSIONS | 6 : 1 | 114/115 (1) | 40.35% (31.80–49.53%) | USD -12.80 | USD -1,459.40 | USD -1,776.10 |
| HOLD_5_SESSIONS | 5 : 5 | 114/115 (1) | 22.81% (16.07–31.32%) | USD -160.89 | USD -18,342.00 | USD -2,688.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 114/115 (1) | 22.81% (16.07–31.32%) | USD -32.18 | USD -3,668.40 | USD -537.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 114/115 (1) | 49.12% (40.13–58.18%) | USD -212.45 | USD -24,219.40 | USD -3,874.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 114/115 (1) | 40.35% (31.80–49.53%) | USD -12.80 | USD -1,459.40 | USD -1,776.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 114/115 (1) | 22.81% (16.07–31.32%) | USD -160.89 | USD -18,342.00 | USD -2,688.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 114/115 (1) | 22.81% (16.07–31.32%) | USD -32.18 | USD -3,668.40 | USD -537.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 114/115 (1) | 49.12% (40.13–58.18%) | USD -212.45 | USD -24,219.40 | USD -3,874.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 114/115 (1) | 40.35% (31.80–49.53%) | USD -12.80 | USD -1,459.40 | USD -1,776.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 114/115 (1) | 22.81% (16.07–31.32%) | USD -160.89 | USD -18,342.00 | USD -2,688.00 |
| HOLD_10_SESSIONS | 1 : 1 | 114/115 (1) | 31.58% (23.77–40.59%) | USD -29.73 | USD -3,389.40 | USD -832.60 |
| HOLD_10_SESSIONS | 1 : 6 | 114/115 (1) | 52.63% (43.53–61.56%) | USD -306.98 | USD -34,995.40 | USD -5,389.10 |
| HOLD_10_SESSIONS | 6 : 1 | 114/115 (1) | 38.60% (30.17–47.77%) | USD 98.86 | USD 11,269.60 | USD -1,993.10 |
| HOLD_10_SESSIONS | 5 : 5 | 114/115 (1) | 31.58% (23.77–40.59%) | USD -148.66 | USD -16,947.00 | USD -4,163.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 114/115 (1) | 31.58% (23.77–40.59%) | USD -29.73 | USD -3,389.40 | USD -832.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 114/115 (1) | 52.63% (43.53–61.56%) | USD -306.98 | USD -34,995.40 | USD -5,389.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 114/115 (1) | 38.60% (30.17–47.77%) | USD 98.86 | USD 11,269.60 | USD -1,993.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 114/115 (1) | 31.58% (23.77–40.59%) | USD -148.66 | USD -16,947.00 | USD -4,163.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 114/115 (1) | 31.58% (23.77–40.59%) | USD -29.73 | USD -3,389.40 | USD -832.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 114/115 (1) | 52.63% (43.53–61.56%) | USD -306.98 | USD -34,995.40 | USD -5,389.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 114/115 (1) | 38.60% (30.17–47.77%) | USD 98.86 | USD 11,269.60 | USD -1,993.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 114/115 (1) | 31.58% (23.77–40.59%) | USD -148.66 | USD -16,947.00 | USD -4,163.00 |
| HOLD_15_SESSIONS | 1 : 1 | 113/115 (2) | 34.51% (26.39–43.66%) | USD -11.25 | USD -1,270.80 | USD -560.60 |
| HOLD_15_SESSIONS | 1 : 6 | 113/115 (2) | 56.64% (47.43–65.41%) | USD -307.39 | USD -34,735.30 | USD -8,425.10 |
| HOLD_15_SESSIONS | 6 : 1 | 113/115 (2) | 37.17% (28.82–46.36%) | USD 228.67 | USD 25,839.70 | USD -2,245.10 |
| HOLD_15_SESSIONS | 5 : 5 | 113/115 (2) | 34.51% (26.39–43.66%) | USD -56.23 | USD -6,354.00 | USD -2,803.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 113/115 (2) | 34.51% (26.39–43.66%) | USD -11.25 | USD -1,270.80 | USD -560.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 113/115 (2) | 56.64% (47.43–65.41%) | USD -307.39 | USD -34,735.30 | USD -8,425.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 113/115 (2) | 37.17% (28.82–46.36%) | USD 228.67 | USD 25,839.70 | USD -2,245.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 113/115 (2) | 34.51% (26.39–43.66%) | USD -56.23 | USD -6,354.00 | USD -2,803.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 113/115 (2) | 34.51% (26.39–43.66%) | USD -11.25 | USD -1,270.80 | USD -560.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 113/115 (2) | 56.64% (47.43–65.41%) | USD -307.39 | USD -34,735.30 | USD -8,425.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 113/115 (2) | 37.17% (28.82–46.36%) | USD 228.67 | USD 25,839.70 | USD -2,245.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 113/115 (2) | 34.51% (26.39–43.66%) | USD -56.23 | USD -6,354.00 | USD -2,803.00 |
| HOLD_20_SESSIONS | 1 : 1 | 113/115 (2) | 32.74% (24.78–41.84%) | USD -13.87 | USD -1,567.80 | USD -739.60 |
| HOLD_20_SESSIONS | 1 : 6 | 113/115 (2) | 49.56% (40.51–58.64%) | USD -445.95 | USD -50,392.30 | USD -7,642.10 |
| HOLD_20_SESSIONS | 6 : 1 | 113/115 (2) | 43.36% (34.59–52.57%) | USD 348.83 | USD 39,417.70 | USD -2,662.10 |
| HOLD_20_SESSIONS | 5 : 5 | 113/115 (2) | 32.74% (24.78–41.84%) | USD -69.37 | USD -7,839.00 | USD -3,698.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 113/115 (2) | 32.74% (24.78–41.84%) | USD -13.87 | USD -1,567.80 | USD -739.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 113/115 (2) | 49.56% (40.51–58.64%) | USD -445.95 | USD -50,392.30 | USD -7,642.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 113/115 (2) | 43.36% (34.59–52.57%) | USD 348.83 | USD 39,417.70 | USD -2,662.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 113/115 (2) | 32.74% (24.78–41.84%) | USD -69.37 | USD -7,839.00 | USD -3,698.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 113/115 (2) | 32.74% (24.78–41.84%) | USD -13.87 | USD -1,567.80 | USD -739.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 113/115 (2) | 49.56% (40.51–58.64%) | USD -445.95 | USD -50,392.30 | USD -7,642.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 113/115 (2) | 43.36% (34.59–52.57%) | USD 348.83 | USD 39,417.70 | USD -2,662.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 113/115 (2) | 32.74% (24.78–41.84%) | USD -69.37 | USD -7,839.00 | USD -3,698.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 115/115 | 100.00% | USD 1,156.18 | USD 266.45 |
| -75% | 115/115 | 100.00% | USD 1,156.18 | USD 266.45 |
| -50% | 115/115 | 100.00% | USD 1,156.18 | USD 266.45 |
| -40% | 115/115 | 100.00% | USD 1,156.18 | USD 266.45 |
| -30% | 115/115 | 100.00% | USD 1,156.18 | USD 266.45 |
| -25% | 115/115 | 100.00% | USD 1,156.18 | USD 266.45 |
| -20% | 115/115 | 100.00% | USD 1,156.18 | USD 266.45 |
| -15% | 115/115 | 100.00% | USD 1,156.18 | USD 266.45 |
| -10% | 115/115 | 100.00% | USD 1,156.18 | USD 266.45 |
| -5% | 115/115 | 100.00% | USD 1,156.18 | USD 266.45 |
| 0% | 115/115 | 100.00% | USD 1,156.18 | USD 266.45 |
| 5% | 67/115 | 58.26% | USD -255.48 | USD -5,659.85 |
| 10% | 7/115 | 6.09% | USD -10,067.25 | USD -20,863.15 |
| 20% | 1/115 | 0.87% | USD -32,373.98 | USD -53,683.75 |

## Limitations

- Public EOD preservation mirror; hashes establish file identity, not exchange or OPRA authenticity.
- EOD quotes are not verified fills; displayed size is a screening gate, not guaranteed multi-leg execution.
- Conservative sides: QQQ LONG enters Ask/exits Bid; SPY SHORT enters Bid/exits Ask.
- Missing exit quotes/size at expiry or source end remain unresolved; win-rate denominator is resolved episodes only.
- Option chain source ends in 2025; no 2026 performance is observed here.
- Nominal Wilson interval does not correct for regime clustering, dependence, or prior strategy selection.
- Expiry shock grid charges entry-side slippage/commission once and uses intrinsic-value payoff; exercise/assignment fees, broker margin, forced liquidation, financing and interim path are not modeled.
- Equal premium debit/credit does not equalize Delta, max loss, collateral or assignment risk; SPY short call can dominate downside even when QQQ long call appreciates.
- Fixed-cohort replay does not model portfolio compounding, taxes, financing, or verified fills.
- When overlapping cohorts are enabled, multiple fixed-size trades can be open at once; total portfolio cash, margin, forced liquidation, and stacked assignment obligations are not constrained by this replay.

Files: trade_episodes.csv, entry_cohort.csv, entry_skips.csv, cost_sensitivity.csv, sizing_sensitivity.csv, expiry_shock_grid.csv, source_manifest.json.