# QQQ LONG CALL / SPY SHORT CALL — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Entry filter: none — No filter; entry when standard contract selection is available.
- Filter evaluation: 196 checks; 196 qualified; 0 rejected (includes insufficient lookback).
- Position sizing: fixed QQQ LONG CALL 1 : SPY SHORT CALL 6; entry and exit require displayed side size for every contract; max total contracts = 10.
- Selection: same expiry; DTE 39–51 (target 45); each leg absolute-Delta target 0.20.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean actual entry premium debit/credit: USD 244.53 / USD 1,343.83; mean absolute mismatch USD 1,099.29; mean match score 18.29%.
- Actual selected contract ratios: {'1:6': 172}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with calls: 1956; SPY chain dates with calls: 1957; sessions with both chains: 1955.
- Selected signals: 172; entered cohorts: 172; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 171/172 | 88/83/0 | 51.46% (44.02–58.84%) | USD -232.06 | USD 9.90 | USD -39,682.10 | USD -6,589.10 | 1 |
| HOLD_5_OR_DTE_LE_7 | 171/172 | 88/83/0 | 51.46% (44.02–58.84%) | USD -232.06 | USD 9.90 | USD -39,682.10 | USD -6,589.10 | 1 |
| HOLD_5_OR_DTE_LE_14 | 171/172 | 88/83/0 | 51.46% (44.02–58.84%) | USD -232.06 | USD 9.90 | USD -39,682.10 | USD -6,589.10 | 1 |
| HOLD_10_SESSIONS | 170/172 | 97/73/0 | 57.06% (49.54–64.26%) | USD -189.36 | USD 76.40 | USD -32,192.00 | USD -6,837.10 | 2 |
| HOLD_10_OR_DTE_LE_7 | 170/172 | 97/73/0 | 57.06% (49.54–64.26%) | USD -189.36 | USD 76.40 | USD -32,192.00 | USD -6,837.10 | 2 |
| HOLD_10_OR_DTE_LE_14 | 170/172 | 97/73/0 | 57.06% (49.54–64.26%) | USD -189.36 | USD 76.40 | USD -32,192.00 | USD -6,837.10 | 2 |
| HOLD_15_SESSIONS | 170/172 | 98/72/0 | 57.65% (50.13–64.83%) | USD -335.35 | USD 166.90 | USD -57,010.00 | USD -9,115.10 | 2 |
| HOLD_15_OR_DTE_LE_7 | 170/172 | 98/72/0 | 57.65% (50.13–64.83%) | USD -335.35 | USD 166.90 | USD -57,010.00 | USD -9,115.10 | 2 |
| HOLD_15_OR_DTE_LE_14 | 170/172 | 98/72/0 | 57.65% (50.13–64.83%) | USD -335.35 | USD 166.90 | USD -57,010.00 | USD -9,115.10 | 2 |
| HOLD_20_SESSIONS | 162/172 | 93/69/0 | 57.41% (49.71–64.76%) | USD -342.70 | USD 240.40 | USD -55,518.20 | USD -9,534.10 | 10 |
| HOLD_20_OR_DTE_LE_7 | 162/172 | 93/69/0 | 57.41% (49.71–64.76%) | USD -342.70 | USD 240.40 | USD -55,518.20 | USD -9,534.10 | 10 |
| HOLD_20_OR_DTE_LE_14 | 167/172 | 97/70/0 | 58.08% (50.50–65.30%) | USD -311.59 | USD 233.90 | USD -52,035.70 | USD -9,534.10 | 5 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT CALL P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD 21.11 | USD -174.07 |
| HOLD_5_OR_DTE_LE_7 | USD 21.11 | USD -174.07 |
| HOLD_5_OR_DTE_LE_14 | USD 21.11 | USD -174.07 |
| HOLD_10_SESSIONS | USD 20.43 | USD -130.69 |
| HOLD_10_OR_DTE_LE_7 | USD 20.43 | USD -130.69 |
| HOLD_10_OR_DTE_LE_14 | USD 20.43 | USD -130.69 |
| HOLD_15_SESSIONS | USD 44.06 | USD -300.32 |
| HOLD_15_OR_DTE_LE_7 | USD 44.06 | USD -300.32 |
| HOLD_15_OR_DTE_LE_14 | USD 44.06 | USD -300.32 |
| HOLD_20_SESSIONS | USD 39.06 | USD -302.67 |
| HOLD_20_OR_DTE_LE_7 | USD 39.06 | USD -302.67 |
| HOLD_20_OR_DTE_LE_14 | USD 39.23 | USD -271.72 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 171 | 54.39% | USD -152.96 | USD -26,156.00 | USD -6,510.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 171 | 52.05% | USD -162.06 | USD -27,712.10 | USD -6,519.10 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 171 | 51.46% | USD -187.96 | USD -32,141.00 | USD -6,545.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 171 | 51.46% | USD -197.06 | USD -33,697.10 | USD -6,554.10 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 171 | 51.46% | USD -222.96 | USD -38,126.00 | USD -6,580.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 171 | 51.46% | USD -232.06 | USD -39,682.10 | USD -6,589.10 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 171 | 45.03% | USD -292.96 | USD -50,096.00 | USD -6,650.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 171 | 43.86% | USD -302.06 | USD -51,652.10 | USD -6,659.10 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.00 | 171 | 54.39% | USD -152.96 | USD -26,156.00 | USD -6,510.00 |
| HOLD_5_OR_DTE_LE_7 | 0.000 | 0.65 | 171 | 52.05% | USD -162.06 | USD -27,712.10 | USD -6,519.10 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.00 | 171 | 51.46% | USD -187.96 | USD -32,141.00 | USD -6,545.00 |
| HOLD_5_OR_DTE_LE_7 | 0.025 | 0.65 | 171 | 51.46% | USD -197.06 | USD -33,697.10 | USD -6,554.10 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.00 | 171 | 51.46% | USD -222.96 | USD -38,126.00 | USD -6,580.00 |
| HOLD_5_OR_DTE_LE_7 | 0.050 | 0.65 | 171 | 51.46% | USD -232.06 | USD -39,682.10 | USD -6,589.10 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.00 | 171 | 45.03% | USD -292.96 | USD -50,096.00 | USD -6,650.00 |
| HOLD_5_OR_DTE_LE_7 | 0.100 | 0.65 | 171 | 43.86% | USD -302.06 | USD -51,652.10 | USD -6,659.10 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.00 | 171 | 54.39% | USD -152.96 | USD -26,156.00 | USD -6,510.00 |
| HOLD_5_OR_DTE_LE_14 | 0.000 | 0.65 | 171 | 52.05% | USD -162.06 | USD -27,712.10 | USD -6,519.10 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.00 | 171 | 51.46% | USD -187.96 | USD -32,141.00 | USD -6,545.00 |
| HOLD_5_OR_DTE_LE_14 | 0.025 | 0.65 | 171 | 51.46% | USD -197.06 | USD -33,697.10 | USD -6,554.10 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.00 | 171 | 51.46% | USD -222.96 | USD -38,126.00 | USD -6,580.00 |
| HOLD_5_OR_DTE_LE_14 | 0.050 | 0.65 | 171 | 51.46% | USD -232.06 | USD -39,682.10 | USD -6,589.10 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.00 | 171 | 45.03% | USD -292.96 | USD -50,096.00 | USD -6,650.00 |
| HOLD_5_OR_DTE_LE_14 | 0.100 | 0.65 | 171 | 43.86% | USD -302.06 | USD -51,652.10 | USD -6,659.10 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 170 | 57.65% | USD -110.26 | USD -18,745.00 | USD -6,758.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 170 | 57.65% | USD -119.36 | USD -20,292.00 | USD -6,767.10 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 170 | 57.06% | USD -145.26 | USD -24,695.00 | USD -6,793.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 170 | 57.06% | USD -154.36 | USD -26,242.00 | USD -6,802.10 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 170 | 57.06% | USD -180.26 | USD -30,645.00 | USD -6,828.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 170 | 57.06% | USD -189.36 | USD -32,192.00 | USD -6,837.10 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 170 | 51.76% | USD -250.26 | USD -42,545.00 | USD -6,898.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 170 | 50.59% | USD -259.36 | USD -44,092.00 | USD -6,907.10 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.00 | 170 | 57.65% | USD -110.26 | USD -18,745.00 | USD -6,758.00 |
| HOLD_10_OR_DTE_LE_7 | 0.000 | 0.65 | 170 | 57.65% | USD -119.36 | USD -20,292.00 | USD -6,767.10 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.00 | 170 | 57.06% | USD -145.26 | USD -24,695.00 | USD -6,793.00 |
| HOLD_10_OR_DTE_LE_7 | 0.025 | 0.65 | 170 | 57.06% | USD -154.36 | USD -26,242.00 | USD -6,802.10 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.00 | 170 | 57.06% | USD -180.26 | USD -30,645.00 | USD -6,828.00 |
| HOLD_10_OR_DTE_LE_7 | 0.050 | 0.65 | 170 | 57.06% | USD -189.36 | USD -32,192.00 | USD -6,837.10 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.00 | 170 | 51.76% | USD -250.26 | USD -42,545.00 | USD -6,898.00 |
| HOLD_10_OR_DTE_LE_7 | 0.100 | 0.65 | 170 | 50.59% | USD -259.36 | USD -44,092.00 | USD -6,907.10 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.00 | 170 | 57.65% | USD -110.26 | USD -18,745.00 | USD -6,758.00 |
| HOLD_10_OR_DTE_LE_14 | 0.000 | 0.65 | 170 | 57.65% | USD -119.36 | USD -20,292.00 | USD -6,767.10 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.00 | 170 | 57.06% | USD -145.26 | USD -24,695.00 | USD -6,793.00 |
| HOLD_10_OR_DTE_LE_14 | 0.025 | 0.65 | 170 | 57.06% | USD -154.36 | USD -26,242.00 | USD -6,802.10 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.00 | 170 | 57.06% | USD -180.26 | USD -30,645.00 | USD -6,828.00 |
| HOLD_10_OR_DTE_LE_14 | 0.050 | 0.65 | 170 | 57.06% | USD -189.36 | USD -32,192.00 | USD -6,837.10 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.00 | 170 | 51.76% | USD -250.26 | USD -42,545.00 | USD -6,898.00 |
| HOLD_10_OR_DTE_LE_14 | 0.100 | 0.65 | 170 | 50.59% | USD -259.36 | USD -44,092.00 | USD -6,907.10 |
| HOLD_15_SESSIONS | 0.000 | 0.00 | 170 | 60.59% | USD -256.25 | USD -43,563.00 | USD -9,036.00 |
| HOLD_15_SESSIONS | 0.000 | 0.65 | 170 | 60.00% | USD -265.35 | USD -45,110.00 | USD -9,045.10 |
| HOLD_15_SESSIONS | 0.025 | 0.00 | 170 | 60.00% | USD -291.25 | USD -49,513.00 | USD -9,071.00 |
| HOLD_15_SESSIONS | 0.025 | 0.65 | 170 | 60.00% | USD -300.35 | USD -51,060.00 | USD -9,080.10 |
| HOLD_15_SESSIONS | 0.050 | 0.00 | 170 | 57.65% | USD -326.25 | USD -55,463.00 | USD -9,106.00 |
| HOLD_15_SESSIONS | 0.050 | 0.65 | 170 | 57.65% | USD -335.35 | USD -57,010.00 | USD -9,115.10 |
| HOLD_15_SESSIONS | 0.100 | 0.00 | 170 | 54.71% | USD -396.25 | USD -67,363.00 | USD -9,176.00 |
| HOLD_15_SESSIONS | 0.100 | 0.65 | 170 | 54.71% | USD -405.35 | USD -68,910.00 | USD -9,185.10 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.00 | 170 | 60.59% | USD -256.25 | USD -43,563.00 | USD -9,036.00 |
| HOLD_15_OR_DTE_LE_7 | 0.000 | 0.65 | 170 | 60.00% | USD -265.35 | USD -45,110.00 | USD -9,045.10 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.00 | 170 | 60.00% | USD -291.25 | USD -49,513.00 | USD -9,071.00 |
| HOLD_15_OR_DTE_LE_7 | 0.025 | 0.65 | 170 | 60.00% | USD -300.35 | USD -51,060.00 | USD -9,080.10 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.00 | 170 | 57.65% | USD -326.25 | USD -55,463.00 | USD -9,106.00 |
| HOLD_15_OR_DTE_LE_7 | 0.050 | 0.65 | 170 | 57.65% | USD -335.35 | USD -57,010.00 | USD -9,115.10 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.00 | 170 | 54.71% | USD -396.25 | USD -67,363.00 | USD -9,176.00 |
| HOLD_15_OR_DTE_LE_7 | 0.100 | 0.65 | 170 | 54.71% | USD -405.35 | USD -68,910.00 | USD -9,185.10 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.00 | 170 | 60.59% | USD -256.25 | USD -43,563.00 | USD -9,036.00 |
| HOLD_15_OR_DTE_LE_14 | 0.000 | 0.65 | 170 | 60.00% | USD -265.35 | USD -45,110.00 | USD -9,045.10 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.00 | 170 | 60.00% | USD -291.25 | USD -49,513.00 | USD -9,071.00 |
| HOLD_15_OR_DTE_LE_14 | 0.025 | 0.65 | 170 | 60.00% | USD -300.35 | USD -51,060.00 | USD -9,080.10 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.00 | 170 | 57.65% | USD -326.25 | USD -55,463.00 | USD -9,106.00 |
| HOLD_15_OR_DTE_LE_14 | 0.050 | 0.65 | 170 | 57.65% | USD -335.35 | USD -57,010.00 | USD -9,115.10 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.00 | 170 | 54.71% | USD -396.25 | USD -67,363.00 | USD -9,176.00 |
| HOLD_15_OR_DTE_LE_14 | 0.100 | 0.65 | 170 | 54.71% | USD -405.35 | USD -68,910.00 | USD -9,185.10 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 162 | 58.02% | USD -263.60 | USD -42,704.00 | USD -9,455.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 162 | 58.02% | USD -272.70 | USD -44,178.20 | USD -9,464.10 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 162 | 57.41% | USD -298.60 | USD -48,374.00 | USD -9,490.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 162 | 57.41% | USD -307.70 | USD -49,848.20 | USD -9,499.10 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 162 | 57.41% | USD -333.60 | USD -54,044.00 | USD -9,525.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 162 | 57.41% | USD -342.70 | USD -55,518.20 | USD -9,534.10 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 162 | 55.56% | USD -403.60 | USD -65,384.00 | USD -9,595.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 162 | 55.56% | USD -412.70 | USD -66,858.20 | USD -9,604.10 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.00 | 162 | 58.02% | USD -263.60 | USD -42,704.00 | USD -9,455.00 |
| HOLD_20_OR_DTE_LE_7 | 0.000 | 0.65 | 162 | 58.02% | USD -272.70 | USD -44,178.20 | USD -9,464.10 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.00 | 162 | 57.41% | USD -298.60 | USD -48,374.00 | USD -9,490.00 |
| HOLD_20_OR_DTE_LE_7 | 0.025 | 0.65 | 162 | 57.41% | USD -307.70 | USD -49,848.20 | USD -9,499.10 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.00 | 162 | 57.41% | USD -333.60 | USD -54,044.00 | USD -9,525.00 |
| HOLD_20_OR_DTE_LE_7 | 0.050 | 0.65 | 162 | 57.41% | USD -342.70 | USD -55,518.20 | USD -9,534.10 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.00 | 162 | 55.56% | USD -403.60 | USD -65,384.00 | USD -9,595.00 |
| HOLD_20_OR_DTE_LE_7 | 0.100 | 0.65 | 162 | 55.56% | USD -412.70 | USD -66,858.20 | USD -9,604.10 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.00 | 167 | 59.28% | USD -232.49 | USD -38,826.00 | USD -9,455.00 |
| HOLD_20_OR_DTE_LE_14 | 0.000 | 0.65 | 167 | 58.68% | USD -241.59 | USD -40,345.70 | USD -9,464.10 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.00 | 167 | 58.68% | USD -267.49 | USD -44,671.00 | USD -9,490.00 |
| HOLD_20_OR_DTE_LE_14 | 0.025 | 0.65 | 167 | 58.68% | USD -276.59 | USD -46,190.70 | USD -9,499.10 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.00 | 167 | 58.08% | USD -302.49 | USD -50,516.00 | USD -9,525.00 |
| HOLD_20_OR_DTE_LE_14 | 0.050 | 0.65 | 167 | 58.08% | USD -311.59 | USD -52,035.70 | USD -9,534.10 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.00 | 167 | 55.69% | USD -372.49 | USD -62,206.00 | USD -9,595.00 |
| HOLD_20_OR_DTE_LE_14 | 0.100 | 0.65 | 167 | 55.69% | USD -381.59 | USD -63,725.70 | USD -9,604.10 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 10; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 171/172 (1) | 25.15% (19.24–32.15%) | USD -30.50 | USD -5,215.60 | USD -415.60 |
| HOLD_5_SESSIONS | 1 : 6 | 171/172 (1) | 51.46% (44.02–58.84%) | USD -232.06 | USD -39,682.10 | USD -6,589.10 |
| HOLD_5_SESSIONS | 6 : 1 | 171/172 (1) | 39.18% (32.18–46.66%) | USD 18.55 | USD 3,172.90 | USD -6,657.10 |
| HOLD_5_SESSIONS | 5 : 5 | 171/172 (1) | 25.15% (19.24–32.15%) | USD -152.50 | USD -26,078.00 | USD -2,078.00 |
| HOLD_5_OR_DTE_LE_7 | 1 : 1 | 171/172 (1) | 25.15% (19.24–32.15%) | USD -30.50 | USD -5,215.60 | USD -415.60 |
| HOLD_5_OR_DTE_LE_7 | 1 : 6 | 171/172 (1) | 51.46% (44.02–58.84%) | USD -232.06 | USD -39,682.10 | USD -6,589.10 |
| HOLD_5_OR_DTE_LE_7 | 6 : 1 | 171/172 (1) | 39.18% (32.18–46.66%) | USD 18.55 | USD 3,172.90 | USD -6,657.10 |
| HOLD_5_OR_DTE_LE_7 | 5 : 5 | 171/172 (1) | 25.15% (19.24–32.15%) | USD -152.50 | USD -26,078.00 | USD -2,078.00 |
| HOLD_5_OR_DTE_LE_14 | 1 : 1 | 171/172 (1) | 25.15% (19.24–32.15%) | USD -30.50 | USD -5,215.60 | USD -415.60 |
| HOLD_5_OR_DTE_LE_14 | 1 : 6 | 171/172 (1) | 51.46% (44.02–58.84%) | USD -232.06 | USD -39,682.10 | USD -6,589.10 |
| HOLD_5_OR_DTE_LE_14 | 6 : 1 | 171/172 (1) | 39.18% (32.18–46.66%) | USD 18.55 | USD 3,172.90 | USD -6,657.10 |
| HOLD_5_OR_DTE_LE_14 | 5 : 5 | 171/172 (1) | 25.15% (19.24–32.15%) | USD -152.50 | USD -26,078.00 | USD -2,078.00 |
| HOLD_10_SESSIONS | 1 : 1 | 170/172 (2) | 29.41% (23.08–36.66%) | USD -23.95 | USD -4,072.00 | USD -635.60 |
| HOLD_10_SESSIONS | 1 : 6 | 170/172 (2) | 57.06% (49.54–64.26%) | USD -189.36 | USD -32,192.00 | USD -6,837.10 |
| HOLD_10_SESSIONS | 6 : 1 | 170/172 (2) | 33.53% (26.87–40.92%) | USD 21.69 | USD 3,688.00 | USD -2,302.10 |
| HOLD_10_SESSIONS | 5 : 5 | 170/172 (2) | 29.41% (23.08–36.66%) | USD -119.76 | USD -20,360.00 | USD -3,178.00 |
| HOLD_10_OR_DTE_LE_7 | 1 : 1 | 170/172 (2) | 29.41% (23.08–36.66%) | USD -23.95 | USD -4,072.00 | USD -635.60 |
| HOLD_10_OR_DTE_LE_7 | 1 : 6 | 170/172 (2) | 57.06% (49.54–64.26%) | USD -189.36 | USD -32,192.00 | USD -6,837.10 |
| HOLD_10_OR_DTE_LE_7 | 6 : 1 | 170/172 (2) | 33.53% (26.87–40.92%) | USD 21.69 | USD 3,688.00 | USD -2,302.10 |
| HOLD_10_OR_DTE_LE_7 | 5 : 5 | 170/172 (2) | 29.41% (23.08–36.66%) | USD -119.76 | USD -20,360.00 | USD -3,178.00 |
| HOLD_10_OR_DTE_LE_14 | 1 : 1 | 170/172 (2) | 29.41% (23.08–36.66%) | USD -23.95 | USD -4,072.00 | USD -635.60 |
| HOLD_10_OR_DTE_LE_14 | 1 : 6 | 170/172 (2) | 57.06% (49.54–64.26%) | USD -189.36 | USD -32,192.00 | USD -6,837.10 |
| HOLD_10_OR_DTE_LE_14 | 6 : 1 | 170/172 (2) | 33.53% (26.87–40.92%) | USD 21.69 | USD 3,688.00 | USD -2,302.10 |
| HOLD_10_OR_DTE_LE_14 | 5 : 5 | 170/172 (2) | 29.41% (23.08–36.66%) | USD -119.76 | USD -20,360.00 | USD -3,178.00 |
| HOLD_15_SESSIONS | 1 : 1 | 170/172 (2) | 25.88% (19.88–32.95%) | USD -28.59 | USD -4,860.00 | USD -561.60 |
| HOLD_15_SESSIONS | 1 : 6 | 170/172 (2) | 57.65% (50.13–64.83%) | USD -335.35 | USD -57,010.00 | USD -9,115.10 |
| HOLD_15_SESSIONS | 6 : 1 | 170/172 (2) | 35.88% (29.06–43.33%) | USD 135.24 | USD 22,990.00 | USD -2,787.10 |
| HOLD_15_SESSIONS | 5 : 5 | 170/172 (2) | 25.88% (19.88–32.95%) | USD -142.94 | USD -24,300.00 | USD -2,808.00 |
| HOLD_15_OR_DTE_LE_7 | 1 : 1 | 170/172 (2) | 25.88% (19.88–32.95%) | USD -28.59 | USD -4,860.00 | USD -561.60 |
| HOLD_15_OR_DTE_LE_7 | 1 : 6 | 170/172 (2) | 57.65% (50.13–64.83%) | USD -335.35 | USD -57,010.00 | USD -9,115.10 |
| HOLD_15_OR_DTE_LE_7 | 6 : 1 | 170/172 (2) | 35.88% (29.06–43.33%) | USD 135.24 | USD 22,990.00 | USD -2,787.10 |
| HOLD_15_OR_DTE_LE_7 | 5 : 5 | 170/172 (2) | 25.88% (19.88–32.95%) | USD -142.94 | USD -24,300.00 | USD -2,808.00 |
| HOLD_15_OR_DTE_LE_14 | 1 : 1 | 170/172 (2) | 25.88% (19.88–32.95%) | USD -28.59 | USD -4,860.00 | USD -561.60 |
| HOLD_15_OR_DTE_LE_14 | 1 : 6 | 170/172 (2) | 57.65% (50.13–64.83%) | USD -335.35 | USD -57,010.00 | USD -9,115.10 |
| HOLD_15_OR_DTE_LE_14 | 6 : 1 | 170/172 (2) | 35.88% (29.06–43.33%) | USD 135.24 | USD 22,990.00 | USD -2,787.10 |
| HOLD_15_OR_DTE_LE_14 | 5 : 5 | 170/172 (2) | 25.88% (19.88–32.95%) | USD -142.94 | USD -24,300.00 | USD -2,808.00 |
| HOLD_20_SESSIONS | 1 : 1 | 162/172 (10) | 27.78% (21.46–35.13%) | USD -33.98 | USD -5,505.20 | USD -836.60 |
| HOLD_20_SESSIONS | 1 : 6 | 162/172 (10) | 57.41% (49.71–64.76%) | USD -342.70 | USD -55,518.20 | USD -9,534.10 |
| HOLD_20_SESSIONS | 6 : 1 | 162/172 (10) | 36.42% (29.40–44.06%) | USD 104.83 | USD 16,981.80 | USD -2,781.10 |
| HOLD_20_SESSIONS | 5 : 5 | 162/172 (10) | 27.78% (21.46–35.13%) | USD -169.91 | USD -27,526.00 | USD -4,183.00 |
| HOLD_20_OR_DTE_LE_7 | 1 : 1 | 162/172 (10) | 27.78% (21.46–35.13%) | USD -33.98 | USD -5,505.20 | USD -836.60 |
| HOLD_20_OR_DTE_LE_7 | 1 : 6 | 162/172 (10) | 57.41% (49.71–64.76%) | USD -342.70 | USD -55,518.20 | USD -9,534.10 |
| HOLD_20_OR_DTE_LE_7 | 6 : 1 | 162/172 (10) | 36.42% (29.40–44.06%) | USD 104.83 | USD 16,981.80 | USD -2,781.10 |
| HOLD_20_OR_DTE_LE_7 | 5 : 5 | 162/172 (10) | 27.78% (21.46–35.13%) | USD -169.91 | USD -27,526.00 | USD -4,183.00 |
| HOLD_20_OR_DTE_LE_14 | 1 : 1 | 167/172 (5) | 28.74% (22.42–36.02%) | USD -28.65 | USD -4,785.20 | USD -836.60 |
| HOLD_20_OR_DTE_LE_14 | 1 : 6 | 167/172 (5) | 58.08% (50.50–65.30%) | USD -311.59 | USD -52,035.70 | USD -9,534.10 |
| HOLD_20_OR_DTE_LE_14 | 6 : 1 | 167/172 (5) | 34.73% (27.93–42.22%) | USD 111.01 | USD 18,539.30 | USD -2,751.10 |
| HOLD_20_OR_DTE_LE_14 | 5 : 5 | 167/172 (5) | 28.74% (22.42–36.02%) | USD -143.27 | USD -23,926.00 | USD -4,183.00 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 172/172 | 100.00% | USD 1,059.74 | USD 230.45 |
| -75% | 172/172 | 100.00% | USD 1,059.74 | USD 230.45 |
| -50% | 172/172 | 100.00% | USD 1,059.74 | USD 230.45 |
| -40% | 172/172 | 100.00% | USD 1,059.74 | USD 230.45 |
| -30% | 172/172 | 100.00% | USD 1,059.74 | USD 230.45 |
| -25% | 172/172 | 100.00% | USD 1,059.74 | USD 230.45 |
| -20% | 172/172 | 100.00% | USD 1,059.74 | USD 230.45 |
| -15% | 172/172 | 100.00% | USD 1,059.74 | USD 230.45 |
| -10% | 172/172 | 100.00% | USD 1,059.74 | USD 230.45 |
| -5% | 172/172 | 100.00% | USD 1,059.74 | USD 230.45 |
| 0% | 172/172 | 100.00% | USD 1,058.16 | USD 230.45 |
| 5% | 56/172 | 32.56% | USD -1,754.24 | USD -7,487.50 |
| 10% | 3/172 | 1.74% | USD -11,951.42 | USD -22,960.45 |
| 20% | 1/172 | 0.58% | USD -33,256.18 | USD -57,053.35 |

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