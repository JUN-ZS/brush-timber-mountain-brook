# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 195 checks; 195 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 54–66 (target 60); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 277.30 / USD 1,497.76; mean absolute mismatch USD 1,220.45; mean match score 18.56%.
- Actual selected contract ratios: {'1:6': 115}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 115; entered cohorts: 115; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 115/115 | 57/58/0 | 49.57% (40.59–58.57%) | USD -290.18 | USD -24.10 | USD -33,370.50 | USD -3,784.10 | 0 |
| HOLD_5_OR_DTE_LE_7 | 115/115 | 57/58/0 | 49.57% (40.59–58.57%) | USD -290.18 | USD -24.10 | USD -33,370.50 | USD -3,784.10 | 0 |
| HOLD_5_OR_DTE_LE_14 | 115/115 | 57/58/0 | 49.57% (40.59–58.57%) | USD -290.18 | USD -24.10 | USD -33,370.50 | USD -3,784.10 | 0 |
| HOLD_10_SESSIONS | 114/115 | 50/64/0 | 43.86% (35.10–53.02%) | USD -397.43 | USD -118.60 | USD -45,307.40 | USD -5,113.10 | 1 |
| HOLD_10_OR_DTE_LE_7 | 114/115 | 50/64/0 | 43.86% (35.10–53.02%) | USD -397.43 | USD -118.60 | USD -45,307.40 | USD -5,113.10 | 1 |
| HOLD_10_OR_DTE_LE_14 | 114/115 | 50/64/0 | 43.86% (35.10–53.02%) | USD -397.43 | USD -118.60 | USD -45,307.40 | USD -5,113.10 | 1 |
| HOLD_15_SESSIONS | 114/115 | 54/60/0 | 47.37% (38.44–56.47%) | USD -354.96 | USD -90.60 | USD -40,465.40 | USD -6,267.10 | 1 |
| HOLD_15_OR_DTE_LE_7 | 114/115 | 54/60/0 | 47.37% (38.44–56.47%) | USD -354.96 | USD -90.60 | USD -40,465.40 | USD -6,267.10 | 1 |
| HOLD_15_OR_DTE_LE_14 | 114/115 | 54/60/0 | 47.37% (38.44–56.47%) | USD -354.96 | USD -90.60 | USD -40,465.40 | USD -6,267.10 | 1 |
| HOLD_20_SESSIONS | 113/115 | 66/47/0 | 58.41% (49.19–67.07%) | USD -336.02 | USD 195.90 | USD -37,970.30 | USD -6,419.10 | 2 |
| HOLD_20_OR_DTE_LE_7 | 113/115 | 66/47/0 | 58.41% (49.19–67.07%) | USD -336.02 | USD 195.90 | USD -37,970.30 | USD -6,419.10 | 2 |
| HOLD_20_OR_DTE_LE_14 | 113/115 | 66/47/0 | 58.41% (49.19–67.07%) | USD -336.02 | USD 195.90 | USD -37,970.30 | USD -6,419.10 | 2 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 35.44 | USD -246.52 |
| HOLD_5_OR_DTE_LE_7 | USD 35.44 | USD -246.52 |
| HOLD_5_OR_DTE_LE_14 | USD 35.44 | USD -246.52 |
| HOLD_10_SESSIONS | USD 66.56 | USD -384.89 |
| HOLD_10_OR_DTE_LE_7 | USD 66.56 | USD -384.89 |
| HOLD_10_OR_DTE_LE_14 | USD 66.56 | USD -384.89 |
| HOLD_15_SESSIONS | USD 49.14 | USD -325.00 |
| HOLD_15_OR_DTE_LE_7 | USD 49.14 | USD -325.00 |
| HOLD_15_OR_DTE_LE_14 | USD 49.14 | USD -325.00 |
| HOLD_20_SESSIONS | USD 54.12 | USD -311.04 |
| HOLD_20_OR_DTE_LE_7 | USD 54.12 | USD -311.04 |
| HOLD_20_OR_DTE_LE_14 | USD 54.12 | USD -311.04 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 115 | 52.17% | USD -211.08 | USD -24,274.00 | USD -3,705.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 115 | 51.30% | USD -220.18 | USD -25,320.50 | USD -3,714.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 115 | 51.30% | USD -246.08 | USD -28,299.00 | USD -3,740.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 115 | 51.30% | USD -255.18 | USD -29,345.50 | USD -3,749.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 115 | 49.57% | USD -281.08 | USD -32,324.00 | USD -3,775.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 115 | 49.57% | USD -290.18 | USD -33,370.50 | USD -3,784.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 115 | 45.22% | USD -351.08 | USD -40,374.00 | USD -3,845.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 115 | 45.22% | USD -360.18 | USD -41,420.50 | USD -3,854.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 115 | 52.17% | USD -211.08 | USD -24,274.00 | USD -3,705.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 115 | 51.30% | USD -220.18 | USD -25,320.50 | USD -3,714.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 115 | 51.30% | USD -246.08 | USD -28,299.00 | USD -3,740.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 115 | 51.30% | USD -255.18 | USD -29,345.50 | USD -3,749.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 115 | 49.57% | USD -281.08 | USD -32,324.00 | USD -3,775.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 115 | 49.57% | USD -290.18 | USD -33,370.50 | USD -3,784.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 115 | 45.22% | USD -351.08 | USD -40,374.00 | USD -3,845.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 115 | 45.22% | USD -360.18 | USD -41,420.50 | USD -3,854.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 115 | 52.17% | USD -211.08 | USD -24,274.00 | USD -3,705.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 115 | 51.30% | USD -220.18 | USD -25,320.50 | USD -3,714.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 115 | 51.30% | USD -246.08 | USD -28,299.00 | USD -3,740.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 115 | 51.30% | USD -255.18 | USD -29,345.50 | USD -3,749.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 115 | 49.57% | USD -281.08 | USD -32,324.00 | USD -3,775.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 115 | 49.57% | USD -290.18 | USD -33,370.50 | USD -3,784.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 115 | 45.22% | USD -351.08 | USD -40,374.00 | USD -3,845.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 115 | 45.22% | USD -360.18 | USD -41,420.50 | USD -3,854.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 114 | 46.49% | USD -318.33 | USD -36,290.00 | USD -5,034.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 114 | 46.49% | USD -327.43 | USD -37,327.40 | USD -5,043.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 114 | 44.74% | USD -353.33 | USD -40,280.00 | USD -5,069.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 114 | 44.74% | USD -362.43 | USD -41,317.40 | USD -5,078.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 114 | 43.86% | USD -388.33 | USD -44,270.00 | USD -5,104.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 114 | 43.86% | USD -397.43 | USD -45,307.40 | USD -5,113.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 114 | 40.35% | USD -458.33 | USD -52,250.00 | USD -5,174.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 114 | 40.35% | USD -467.43 | USD -53,287.40 | USD -5,183.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 114 | 46.49% | USD -318.33 | USD -36,290.00 | USD -5,034.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 114 | 46.49% | USD -327.43 | USD -37,327.40 | USD -5,043.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 114 | 44.74% | USD -353.33 | USD -40,280.00 | USD -5,069.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 114 | 44.74% | USD -362.43 | USD -41,317.40 | USD -5,078.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 114 | 43.86% | USD -388.33 | USD -44,270.00 | USD -5,104.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 114 | 43.86% | USD -397.43 | USD -45,307.40 | USD -5,113.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 114 | 40.35% | USD -458.33 | USD -52,250.00 | USD -5,174.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 114 | 40.35% | USD -467.43 | USD -53,287.40 | USD -5,183.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 114 | 46.49% | USD -318.33 | USD -36,290.00 | USD -5,034.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 114 | 46.49% | USD -327.43 | USD -37,327.40 | USD -5,043.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 114 | 44.74% | USD -353.33 | USD -40,280.00 | USD -5,069.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 114 | 44.74% | USD -362.43 | USD -41,317.40 | USD -5,078.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 114 | 43.86% | USD -388.33 | USD -44,270.00 | USD -5,104.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 114 | 43.86% | USD -397.43 | USD -45,307.40 | USD -5,113.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 114 | 40.35% | USD -458.33 | USD -52,250.00 | USD -5,174.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 114 | 40.35% | USD -467.43 | USD -53,287.40 | USD -5,183.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 114 | 50.00% | USD -275.86 | USD -31,448.00 | USD -6,188.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 114 | 49.12% | USD -284.96 | USD -32,485.40 | USD -6,197.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 114 | 47.37% | USD -310.86 | USD -35,438.00 | USD -6,223.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 114 | 47.37% | USD -319.96 | USD -36,475.40 | USD -6,232.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 114 | 47.37% | USD -345.86 | USD -39,428.00 | USD -6,258.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 114 | 47.37% | USD -354.96 | USD -40,465.40 | USD -6,267.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 114 | 44.74% | USD -415.86 | USD -47,408.00 | USD -6,328.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 114 | 44.74% | USD -424.96 | USD -48,445.40 | USD -6,337.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 114 | 50.00% | USD -275.86 | USD -31,448.00 | USD -6,188.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 114 | 49.12% | USD -284.96 | USD -32,485.40 | USD -6,197.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 114 | 47.37% | USD -310.86 | USD -35,438.00 | USD -6,223.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 114 | 47.37% | USD -319.96 | USD -36,475.40 | USD -6,232.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 114 | 47.37% | USD -345.86 | USD -39,428.00 | USD -6,258.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 114 | 47.37% | USD -354.96 | USD -40,465.40 | USD -6,267.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 114 | 44.74% | USD -415.86 | USD -47,408.00 | USD -6,328.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 114 | 44.74% | USD -424.96 | USD -48,445.40 | USD -6,337.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 114 | 50.00% | USD -275.86 | USD -31,448.00 | USD -6,188.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 114 | 49.12% | USD -284.96 | USD -32,485.40 | USD -6,197.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 114 | 47.37% | USD -310.86 | USD -35,438.00 | USD -6,223.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 114 | 47.37% | USD -319.96 | USD -36,475.40 | USD -6,232.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 114 | 47.37% | USD -345.86 | USD -39,428.00 | USD -6,258.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 114 | 47.37% | USD -354.96 | USD -40,465.40 | USD -6,267.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 114 | 44.74% | USD -415.86 | USD -47,408.00 | USD -6,328.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 114 | 44.74% | USD -424.96 | USD -48,445.40 | USD -6,337.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 113 | 60.18% | USD -256.92 | USD -29,032.00 | USD -6,340.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 113 | 60.18% | USD -266.02 | USD -30,060.30 | USD -6,349.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 113 | 60.18% | USD -291.92 | USD -32,987.00 | USD -6,375.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 113 | 60.18% | USD -301.02 | USD -34,015.30 | USD -6,384.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 113 | 58.41% | USD -326.92 | USD -36,942.00 | USD -6,410.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 113 | 58.41% | USD -336.02 | USD -37,970.30 | USD -6,419.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 113 | 54.87% | USD -396.92 | USD -44,852.00 | USD -6,480.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 113 | 54.87% | USD -406.02 | USD -45,880.30 | USD -6,489.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 113 | 60.18% | USD -256.92 | USD -29,032.00 | USD -6,340.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 113 | 60.18% | USD -266.02 | USD -30,060.30 | USD -6,349.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 113 | 60.18% | USD -291.92 | USD -32,987.00 | USD -6,375.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 113 | 60.18% | USD -301.02 | USD -34,015.30 | USD -6,384.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 113 | 58.41% | USD -326.92 | USD -36,942.00 | USD -6,410.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 113 | 58.41% | USD -336.02 | USD -37,970.30 | USD -6,419.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 113 | 54.87% | USD -396.92 | USD -44,852.00 | USD -6,480.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 113 | 54.87% | USD -406.02 | USD -45,880.30 | USD -6,489.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 113 | 60.18% | USD -256.92 | USD -29,032.00 | USD -6,340.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 113 | 60.18% | USD -266.02 | USD -30,060.30 | USD -6,349.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 113 | 60.18% | USD -291.92 | USD -32,987.00 | USD -6,375.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 113 | 60.18% | USD -301.02 | USD -34,015.30 | USD -6,384.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 113 | 58.41% | USD -326.92 | USD -36,942.00 | USD -6,410.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 113 | 58.41% | USD -336.02 | USD -37,970.30 | USD -6,419.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 113 | 54.87% | USD -396.92 | USD -44,852.00 | USD -6,480.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 113 | 54.87% | USD -406.02 | USD -45,880.30 | USD -6,489.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 115/115 (0) | 28.70% (21.22–37.55%) | USD -28.24 | USD -3,248.00 | USD -369.60 |
| HOLD_5_SESSIONS | 1 : 6 | 115/115 (0) | 49.57% (40.59–58.57%) | USD -290.18 | USD -33,370.50 | USD -3,784.10 |
| HOLD_5_SESSIONS | 6 : 1 | 115/115 (0) | 40.00% (31.51–49.14%) | USD 92.47 | USD 10,634.50 | USD -1,928.10 |
| HOLD_5_SESSIONS | 5 : 5 | 115/115 (0) | 28.70% (21.22–37.55%) | USD -141.22 | USD -16,240.00 | USD -1,848.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 115/115 (0) | 28.70% (21.22–37.55%) | USD -28.24 | USD -3,248.00 | USD -369.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 115/115 (0) | 49.57% (40.59–58.57%) | USD -290.18 | USD -33,370.50 | USD -3,784.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 115/115 (0) | 40.00% (31.51–49.14%) | USD 92.47 | USD 10,634.50 | USD -1,928.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 115/115 (0) | 28.70% (21.22–37.55%) | USD -141.22 | USD -16,240.00 | USD -1,848.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 115/115 (0) | 28.70% (21.22–37.55%) | USD -28.24 | USD -3,248.00 | USD -369.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 115/115 (0) | 49.57% (40.59–58.57%) | USD -290.18 | USD -33,370.50 | USD -3,784.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 115/115 (0) | 40.00% (31.51–49.14%) | USD 92.47 | USD 10,634.50 | USD -1,928.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 115/115 (0) | 28.70% (21.22–37.55%) | USD -141.22 | USD -16,240.00 | USD -1,848.00 |
| HOLD_10_SESSIONS | 1 : 1 | 114/115 (1) | 28.95% (21.42–37.85%) | USD -20.19 | USD -2,301.40 | USD -791.60 |
| HOLD_10_SESSIONS | 1 : 6 | 114/115 (1) | 43.86% (35.10–53.02%) | USD -397.43 | USD -45,307.40 | USD -5,113.10 |
| HOLD_10_SESSIONS | 6 : 1 | 114/115 (1) | 42.98% (34.27–52.15%) | USD 256.12 | USD 29,197.60 | USD -2,397.10 |
| HOLD_10_SESSIONS | 5 : 5 | 114/115 (1) | 28.95% (21.42–37.85%) | USD -100.94 | USD -11,507.00 | USD -3,958.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 114/115 (1) | 28.95% (21.42–37.85%) | USD -20.19 | USD -2,301.40 | USD -791.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 114/115 (1) | 43.86% (35.10–53.02%) | USD -397.43 | USD -45,307.40 | USD -5,113.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 114/115 (1) | 42.98% (34.27–52.15%) | USD 256.12 | USD 29,197.60 | USD -2,397.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 114/115 (1) | 28.95% (21.42–37.85%) | USD -100.94 | USD -11,507.00 | USD -3,958.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 114/115 (1) | 28.95% (21.42–37.85%) | USD -20.19 | USD -2,301.40 | USD -791.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 114/115 (1) | 43.86% (35.10–53.02%) | USD -397.43 | USD -45,307.40 | USD -5,113.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 114/115 (1) | 42.98% (34.27–52.15%) | USD 256.12 | USD 29,197.60 | USD -2,397.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 114/115 (1) | 28.95% (21.42–37.85%) | USD -100.94 | USD -11,507.00 | USD -3,958.00 |
| HOLD_15_SESSIONS | 1 : 1 | 114/115 (1) | 28.95% (21.42–37.85%) | USD -27.63 | USD -3,149.40 | USD -601.60 |
| HOLD_15_SESSIONS | 1 : 6 | 114/115 (1) | 47.37% (38.44–56.47%) | USD -354.96 | USD -40,465.40 | USD -6,267.10 |
| HOLD_15_SESSIONS | 6 : 1 | 114/115 (1) | 38.60% (30.17–47.77%) | USD 161.58 | USD 18,419.60 | USD -2,932.10 |
| HOLD_15_SESSIONS | 5 : 5 | 114/115 (1) | 28.95% (21.42–37.85%) | USD -138.13 | USD -15,747.00 | USD -3,008.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 114/115 (1) | 28.95% (21.42–37.85%) | USD -27.63 | USD -3,149.40 | USD -601.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 114/115 (1) | 47.37% (38.44–56.47%) | USD -354.96 | USD -40,465.40 | USD -6,267.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 114/115 (1) | 38.60% (30.17–47.77%) | USD 161.58 | USD 18,419.60 | USD -2,932.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 114/115 (1) | 28.95% (21.42–37.85%) | USD -138.13 | USD -15,747.00 | USD -3,008.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 114/115 (1) | 28.95% (21.42–37.85%) | USD -27.63 | USD -3,149.40 | USD -601.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 114/115 (1) | 47.37% (38.44–56.47%) | USD -354.96 | USD -40,465.40 | USD -6,267.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 114/115 (1) | 38.60% (30.17–47.77%) | USD 161.58 | USD 18,419.60 | USD -2,932.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 114/115 (1) | 28.95% (21.42–37.85%) | USD -138.13 | USD -15,747.00 | USD -3,008.00 |
| HOLD_20_SESSIONS | 1 : 1 | 113/115 (2) | 31.86% (23.99–40.92%) | USD -20.32 | USD -2,295.80 | USD -726.60 |
| HOLD_20_SESSIONS | 1 : 6 | 113/115 (2) | 58.41% (49.19–67.07%) | USD -336.02 | USD -37,970.30 | USD -6,419.10 |
| HOLD_20_SESSIONS | 6 : 1 | 113/115 (2) | 39.82% (31.27–49.04%) | USD 193.80 | USD 21,899.70 | USD -2,839.10 |
| HOLD_20_SESSIONS | 5 : 5 | 113/115 (2) | 31.86% (23.99–40.92%) | USD -101.58 | USD -11,479.00 | USD -3,633.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 113/115 (2) | 31.86% (23.99–40.92%) | USD -20.32 | USD -2,295.80 | USD -726.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 113/115 (2) | 58.41% (49.19–67.07%) | USD -336.02 | USD -37,970.30 | USD -6,419.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 113/115 (2) | 39.82% (31.27–49.04%) | USD 193.80 | USD 21,899.70 | USD -2,839.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 113/115 (2) | 31.86% (23.99–40.92%) | USD -101.58 | USD -11,479.00 | USD -3,633.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 113/115 (2) | 31.86% (23.99–40.92%) | USD -20.32 | USD -2,295.80 | USD -726.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 113/115 (2) | 58.41% (49.19–67.07%) | USD -336.02 | USD -37,970.30 | USD -6,419.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 113/115 (2) | 39.82% (31.27–49.04%) | USD 193.80 | USD 21,899.70 | USD -2,839.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 113/115 (2) | 31.86% (23.99–40.92%) | USD -101.58 | USD -11,479.00 | USD -3,633.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 115/115 | 100.00% | USD 1,180.90 | USD 271.45 |
| -75% | 115/115 | 100.00% | USD 1,180.90 | USD 271.45 |
| -50% | 115/115 | 100.00% | USD 1,180.90 | USD 271.45 |
| -40% | 115/115 | 100.00% | USD 1,180.90 | USD 271.45 |
| -30% | 115/115 | 100.00% | USD 1,180.90 | USD 271.45 |
| -25% | 115/115 | 100.00% | USD 1,180.90 | USD 271.45 |
| -20% | 115/115 | 100.00% | USD 1,180.90 | USD 271.45 |
| -15% | 115/115 | 100.00% | USD 1,180.90 | USD 271.45 |
| -10% | 115/115 | 100.00% | USD 1,180.90 | USD 271.45 |
| -5% | 115/115 | 100.00% | USD 1,180.90 | USD 271.45 |
| 0% | 115/115 | 100.00% | USD 1,180.90 | USD 271.45 |
| 5% | 73/115 | 63.48% | USD -10.54 | USD -5,072.00 |
| 10% | 6/115 | 5.22% | USD -9,985.05 | USD -19,784.35 |
| 20% | 0/115 | 0.00% | USD -32,276.59 | USD -52,364.15 |

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