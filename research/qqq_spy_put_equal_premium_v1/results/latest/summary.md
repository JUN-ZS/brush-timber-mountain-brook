# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1

Status: **COMPLETED_WITH_UNRESOLVEDS**. EOD quote-side estimate, not confirmed fills.

- Window requested: 2018-03-01 to 2025-12-15; last QQQ/SPY chain dates: 2025-12-15 / 2025-12-12.
- Position sizing: match LONG QQQ PUT premium debit to SHORT SPY PUT premium credit per cohort; whole-contract ratio varies by entry; max total contracts = 9.
- Selection: same expiry; DTE 30–60 (target 45); each leg absolute-Delta target 0.25.
- Base costs: slippage USD 0.050/option-share/side; USD 0.65/contract/side.
- Mean premium debit/credit: USD 1,615.20 / USD 1,622.70; mean absolute mismatch USD 85.55; mean match score 95.43%.
- Actual selected contract ratios: {'1:1': 3, '3:2': 1, '3:3': 3, '3:4': 2, '4:3': 6, '4:4': 12, '4:5': 9, '5:4': 8}.

## Coverage and source integrity

- Common underlying sessions: 1959; QQQ chain dates with puts: 1956; SPY chain dates with puts: 1957; sessions with both chains: 1955.
- Selected signals: 44; entered cohorts: 44; skipped entries: 0.
- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.

## Historical win rate — base assumed costs

| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 44/44 | 11/33/0 | 25.00% (14.57–39.44%) | USD -231.91 | USD -89.75 | USD -10,204.20 | USD -4,818.40 | 0 |
| HOLD_10_SESSIONS | 44/44 | 12/32/0 | 27.27% (16.35–41.85%) | USD -331.37 | USD -116.90 | USD -14,580.20 | USD -5,406.40 | 0 |
| HOLD_20_SESSIONS | 44/44 | 8/36/0 | 18.18% (9.51–31.96%) | USD -594.66 | USD -99.10 | USD -26,165.20 | USD -17,078.40 | 0 |
| EXIT_AT_DTE_LE_7 | 36/44 | 12/24/0 | 33.33% (20.21–49.67%) | USD -668.12 | USD -67.45 | USD -24,052.30 | USD -13,506.40 | 8 |

Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.

## Leg attribution

| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |
|---|---:|---:|
| HOLD_5_SESSIONS | USD -76.84 | USD -69.30 |
| HOLD_10_SESSIONS | USD -192.41 | USD -53.18 |
| HOLD_20_SESSIONS | USD -256.34 | USD -252.55 |
| EXIT_AT_DTE_LE_7 | USD -136.14 | USD -446.92 |

## Cost sensitivity

| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 0.000 | 0.00 | 44 | 40.91% | USD -146.14 | USD -6,430.00 | USD -4,728.00 |
| HOLD_5_SESSIONS | 0.000 | 0.65 | 44 | 38.64% | USD -156.00 | USD -6,864.20 | USD -4,738.40 |
| HOLD_5_SESSIONS | 0.025 | 0.00 | 44 | 29.55% | USD -184.09 | USD -8,100.00 | USD -4,768.00 |
| HOLD_5_SESSIONS | 0.025 | 0.65 | 44 | 27.27% | USD -193.96 | USD -8,534.20 | USD -4,778.40 |
| HOLD_5_SESSIONS | 0.050 | 0.00 | 44 | 27.27% | USD -222.05 | USD -9,770.00 | USD -4,808.00 |
| HOLD_5_SESSIONS | 0.050 | 0.65 | 44 | 25.00% | USD -231.91 | USD -10,204.20 | USD -4,818.40 |
| HOLD_5_SESSIONS | 0.100 | 0.00 | 44 | 18.18% | USD -297.95 | USD -13,110.00 | USD -4,888.00 |
| HOLD_5_SESSIONS | 0.100 | 0.65 | 44 | 15.91% | USD -307.82 | USD -13,544.20 | USD -4,898.40 |
| HOLD_10_SESSIONS | 0.000 | 0.00 | 44 | 38.64% | USD -245.59 | USD -10,806.00 | USD -5,316.00 |
| HOLD_10_SESSIONS | 0.000 | 0.65 | 44 | 38.64% | USD -255.46 | USD -11,240.20 | USD -5,326.40 |
| HOLD_10_SESSIONS | 0.025 | 0.00 | 44 | 31.82% | USD -283.55 | USD -12,476.00 | USD -5,356.00 |
| HOLD_10_SESSIONS | 0.025 | 0.65 | 44 | 31.82% | USD -293.41 | USD -12,910.20 | USD -5,366.40 |
| HOLD_10_SESSIONS | 0.050 | 0.00 | 44 | 29.55% | USD -321.50 | USD -14,146.00 | USD -5,396.00 |
| HOLD_10_SESSIONS | 0.050 | 0.65 | 44 | 27.27% | USD -331.37 | USD -14,580.20 | USD -5,406.40 |
| HOLD_10_SESSIONS | 0.100 | 0.00 | 44 | 11.36% | USD -397.41 | USD -17,486.00 | USD -5,476.00 |
| HOLD_10_SESSIONS | 0.100 | 0.65 | 44 | 11.36% | USD -407.28 | USD -17,920.20 | USD -5,486.40 |
| HOLD_20_SESSIONS | 0.000 | 0.00 | 44 | 40.91% | USD -508.89 | USD -22,391.00 | USD -16,988.00 |
| HOLD_20_SESSIONS | 0.000 | 0.65 | 44 | 36.36% | USD -518.75 | USD -22,825.20 | USD -16,998.40 |
| HOLD_20_SESSIONS | 0.025 | 0.00 | 44 | 25.00% | USD -546.84 | USD -24,061.00 | USD -17,028.00 |
| HOLD_20_SESSIONS | 0.025 | 0.65 | 44 | 25.00% | USD -556.71 | USD -24,495.20 | USD -17,038.40 |
| HOLD_20_SESSIONS | 0.050 | 0.00 | 44 | 18.18% | USD -584.80 | USD -25,731.00 | USD -17,068.00 |
| HOLD_20_SESSIONS | 0.050 | 0.65 | 44 | 18.18% | USD -594.66 | USD -26,165.20 | USD -17,078.40 |
| HOLD_20_SESSIONS | 0.100 | 0.00 | 44 | 9.09% | USD -660.70 | USD -29,071.00 | USD -17,148.00 |
| HOLD_20_SESSIONS | 0.100 | 0.65 | 44 | 9.09% | USD -670.57 | USD -29,505.20 | USD -17,158.40 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.00 | 36 | 47.22% | USD -583.06 | USD -20,990.00 | USD -13,416.00 |
| EXIT_AT_DTE_LE_7 | 0.000 | 0.65 | 36 | 47.22% | USD -592.84 | USD -21,342.30 | USD -13,426.40 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.00 | 36 | 36.11% | USD -620.69 | USD -22,345.00 | USD -13,456.00 |
| EXIT_AT_DTE_LE_7 | 0.025 | 0.65 | 36 | 33.33% | USD -630.48 | USD -22,697.30 | USD -13,466.40 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.00 | 36 | 33.33% | USD -658.33 | USD -23,700.00 | USD -13,496.00 |
| EXIT_AT_DTE_LE_7 | 0.050 | 0.65 | 36 | 33.33% | USD -668.12 | USD -24,052.30 | USD -13,506.40 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.00 | 36 | 22.22% | USD -733.61 | USD -26,410.00 | USD -13,576.00 |
| EXIT_AT_DTE_LE_7 | 0.100 | 0.65 | 36 | 22.22% | USD -743.40 | USD -26,762.30 | USD -13,586.40 |

## Position-size sensitivity (reference grid; not the premium-matched policy)

- Grid: LONG QQQ 1–6 × SHORT SPY 1–6 contracts, with combined count capped at 9; CSV contains valid combinations only.
- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.
- All sizes are no greater than the base run's size-screened quantities. Resolved/unresolved status is inherited from the base run; an unresolved exit is not reclassified just because a smaller hypothetical size might have passed a quote-size gate.
- P&L statistics use resolved episodes only; unresolved counts are shown separately.

| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |
|---|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 1 : 1 | 44/44 (0) | 36.36% (23.78–51.13%) | USD -46.76 | USD -2,057.40 | USD -1,204.60 |
| HOLD_5_SESSIONS | 1 : 6 | 44/44 (0) | 72.73% (58.15–83.65%) | USD -168.26 | USD -7,403.40 | USD -15,946.10 |
| HOLD_5_SESSIONS | 6 : 1 | 44/44 (0) | 22.73% (12.84–36.99%) | USD -159.05 | USD -6,998.40 | USD -2,665.10 |
| HOLD_5_SESSIONS | 4 : 5 | 44/44 (0) | 56.82% (42.22–70.32%) | USD -211.34 | USD -9,298.80 | USD -7,766.70 |
| HOLD_10_SESSIONS | 1 : 1 | 44/44 (0) | 43.18% (29.68–57.78%) | USD -67.90 | USD -2,987.40 | USD -1,351.60 |
| HOLD_10_SESSIONS | 1 : 6 | 44/44 (0) | 72.73% (58.15–83.65%) | USD -257.92 | USD -11,348.40 | USD -16,388.10 |
| HOLD_10_SESSIONS | 6 : 1 | 44/44 (0) | 20.45% (11.15–34.50%) | USD -217.35 | USD -9,563.40 | USD -3,121.10 |
| HOLD_10_SESSIONS | 4 : 5 | 44/44 (0) | 61.36% (46.62–74.28%) | USD -309.59 | USD -13,621.80 | USD -8,413.70 |
| HOLD_20_SESSIONS | 1 : 1 | 44/44 (0) | 38.64% (25.72–53.38%) | USD -147.28 | USD -6,480.40 | USD -4,269.60 |
| HOLD_20_SESSIONS | 1 : 6 | 44/44 (0) | 79.55% (65.50–88.85%) | USD -604.12 | USD -26,581.40 | USD -51,851.10 |
| HOLD_20_SESSIONS | 6 : 1 | 44/44 (0) | 18.18% (9.51–31.96%) | USD -426.85 | USD -18,781.40 | USD -4,371.10 |
| HOLD_20_SESSIONS | 4 : 5 | 44/44 (0) | 70.45% (55.78–81.84%) | USD -680.50 | USD -29,941.80 | USD -26,594.70 |
| EXIT_AT_DTE_LE_7 | 1 : 1 | 36/44 (8) | 38.89% (24.78–55.14%) | USD -171.63 | USD -6,178.60 | USD -3,376.60 |
| EXIT_AT_DTE_LE_7 | 1 : 6 | 36/44 (8) | 77.78% (61.92–88.28%) | USD -1,046.88 | USD -37,687.60 | USD -37,043.10 |
| EXIT_AT_DTE_LE_7 | 6 : 1 | 36/44 (8) | 25.00% (13.75–41.07%) | USD -154.52 | USD -5,562.60 | USD -4,415.10 |
| EXIT_AT_DTE_LE_7 | 4 : 5 | 36/44 (8) | 77.78% (61.92–88.28%) | USD -861.56 | USD -31,016.20 | USD -20,239.70 |

The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.


## Equal-percentage QQQ/SPY expiry shocks (hypothetical)

These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.
Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.
Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.

| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |
|---:|---:|---:|---:|---:|
| -100% | 2/44 | 4.55% | USD -35,716.66 | USD -91,946.85 |
| -75% | 2/44 | 4.55% | USD -26,788.36 | USD -68,706.60 |
| -50% | 1/44 | 2.27% | USD -17,860.06 | USD -45,466.35 |
| -40% | 1/44 | 2.27% | USD -14,288.74 | USD -36,170.25 |
| -30% | 0/44 | 0.00% | USD -10,717.42 | USD -26,874.15 |
| -25% | 0/44 | 0.00% | USD -8,931.76 | USD -22,226.10 |
| -20% | 0/44 | 0.00% | USD -7,146.10 | USD -17,578.05 |
| -15% | 0/44 | 0.00% | USD -5,360.44 | USD -12,930.00 |
| -10% | 0/44 | 0.00% | USD -3,523.19 | USD -8,485.35 |
| -5% | 3/44 | 6.82% | USD -1,220.84 | USD -4,145.45 |
| 0% | 12/44 | 27.27% | USD -35.39 | USD -349.20 |
| 5% | 12/44 | 27.27% | USD -35.39 | USD -349.20 |
| 10% | 12/44 | 27.27% | USD -35.39 | USD -349.20 |
| 20% | 12/44 | 27.27% | USD -35.39 | USD -349.20 |

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