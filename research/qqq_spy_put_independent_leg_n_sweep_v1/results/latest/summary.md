# Independent QQQ LONG PUT / SPY SHORT PUT Fixed-N Sweep V1

**Completed post-analysis of committed EOD quote-side outputs; not actual fills or a new raw-option replay.**

- Input: research/qqq_spy_put_equal_premium_v1/results/latest/trade_episodes.csv; input SHA-256 is recorded in source_manifest.json.
- Signal dates: 2018-03-01 through 2025-11-10; signal cohorts per exit policy: {'HOLD_5_SESSIONS': 44, 'HOLD_10_SESSIONS': 44, 'HOLD_20_SESSIONS': 44, 'EXIT_AT_DTE_LE_7': 44}.
- Independently fixed N=1–6 per leg. Paired grid allows QQQ N + SPY N ≤ 9.
- Contract IDs, entry dates, option entry quotes, and exit policies are held constant from the parent replay; no P&L-selected strikes.
- Fixed-N gross P&L scales each leg's own recorded quote-side result by N / parent variable quantity; costs are recalculated for each hypothetical N.
- Hypothetical fixed N is NOT re-gated against historical displayed bid/ask size. These are quote-price counterfactuals, not execution-verified sizes.
- EOD quotes are not confirmed fills. Base costs: USD 0.05 per option share per side + USD 0.65 commission per contract per side. Sensitivity includes zero cost and USD 0.10/share slippage.
- Resolved-only win rates/P&L; unresolved cases are counted separately. This is a sparse sample (44 signals), not a stable probability estimate.

## Original dynamic premium-matched pair (reference)

| Policy | Resolved/opened (unresolved) | Win rate | Mean net | Total net | Worst | Mean QQQ debit | Mean SPY credit | Mean abs mismatch | Mean SPY assignment obligation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD_5_SESSIONS | 44/44 (0) | 25.00% | USD -231.91 | USD -10,204.20 | USD -4,818.40 | USD 1,615.20 | USD 1,622.70 | USD 85.55 | USD 149,912.50 |
| HOLD_10_SESSIONS | 44/44 (0) | 27.27% | USD -331.37 | USD -14,580.20 | USD -5,406.40 | USD 1,615.20 | USD 1,622.70 | USD 85.55 | USD 149,912.50 |
| HOLD_20_SESSIONS | 44/44 (0) | 18.18% | USD -594.66 | USD -26,165.20 | USD -17,078.40 | USD 1,615.20 | USD 1,622.70 | USD 85.55 | USD 149,912.50 |
| EXIT_AT_DTE_LE_7 | 36/44 (8) | 33.33% | USD -668.12 | USD -24,052.30 | USD -13,506.40 | USD 1,615.20 | USD 1,622.70 | USD 85.55 | USD 149,912.50 |

## Independent standalone legs (base costs)

### HOLD_5_SESSIONS

| Leg | N | Resolved/opened | Wins/losses/flat | Win rate | Mean net | Total net | Worst | Mean entry premium/credit | Mean SPY assignment obligation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| QQQ_LONG_PUT | 1 | 44/44 (0) | 11/33/0 | 25.00% | USD -22.46 | USD -988.20 | USD -510.30 | USD 438.45 | USD 0.00 |
| QQQ_LONG_PUT | 2 | 44/44 (0) | 11/33/0 | 25.00% | USD -44.92 | USD -1,976.40 | USD -1,020.60 | USD 876.91 | USD 0.00 |
| QQQ_LONG_PUT | 3 | 44/44 (0) | 11/33/0 | 25.00% | USD -67.38 | USD -2,964.60 | USD -1,530.90 | USD 1,315.36 | USD 0.00 |
| QQQ_LONG_PUT | 4 | 44/44 (0) | 11/33/0 | 25.00% | USD -89.84 | USD -3,952.80 | USD -2,041.20 | USD 1,753.82 | USD 0.00 |
| QQQ_LONG_PUT | 5 | 44/44 (0) | 11/33/0 | 25.00% | USD -112.30 | USD -4,941.00 | USD -2,551.50 | USD 2,192.27 | USD 0.00 |
| QQQ_LONG_PUT | 6 | 44/44 (0) | 11/33/0 | 25.00% | USD -134.75 | USD -5,929.20 | USD -3,061.80 | USD 2,630.73 | USD 0.00 |
| SPY_SHORT_PUT | 1 | 44/44 (0) | 32/12/0 | 72.73% | USD -24.30 | USD -1,069.20 | USD -2,948.30 | USD 432.20 | USD 39,675.00 |
| SPY_SHORT_PUT | 2 | 44/44 (0) | 32/12/0 | 72.73% | USD -48.60 | USD -2,138.40 | USD -5,896.60 | USD 864.41 | USD 79,350.00 |
| SPY_SHORT_PUT | 3 | 44/44 (0) | 32/12/0 | 72.73% | USD -72.90 | USD -3,207.60 | USD -8,844.90 | USD 1,296.61 | USD 119,025.00 |
| SPY_SHORT_PUT | 4 | 44/44 (0) | 32/12/0 | 72.73% | USD -97.20 | USD -4,276.80 | USD -11,793.20 | USD 1,728.82 | USD 158,700.00 |
| SPY_SHORT_PUT | 5 | 44/44 (0) | 32/12/0 | 72.73% | USD -121.50 | USD -5,346.00 | USD -14,741.50 | USD 2,161.02 | USD 198,375.00 |
| SPY_SHORT_PUT | 6 | 44/44 (0) | 32/12/0 | 72.73% | USD -145.80 | USD -6,415.20 | USD -17,689.80 | USD 2,593.23 | USD 238,050.00 |

### HOLD_10_SESSIONS

| Leg | N | Resolved/opened | Wins/losses/flat | Win rate | Mean net | Total net | Worst | Mean entry premium/credit | Mean SPY assignment obligation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| QQQ_LONG_PUT | 1 | 44/44 (0) | 9/35/0 | 20.45% | USD -29.89 | USD -1,315.20 | USD -619.30 | USD 438.45 | USD 0.00 |
| QQQ_LONG_PUT | 2 | 44/44 (0) | 9/35/0 | 20.45% | USD -59.78 | USD -2,630.40 | USD -1,238.60 | USD 876.91 | USD 0.00 |
| QQQ_LONG_PUT | 3 | 44/44 (0) | 9/35/0 | 20.45% | USD -89.67 | USD -3,945.60 | USD -1,857.90 | USD 1,315.36 | USD 0.00 |
| QQQ_LONG_PUT | 4 | 44/44 (0) | 9/35/0 | 20.45% | USD -119.56 | USD -5,260.80 | USD -2,477.20 | USD 1,753.82 | USD 0.00 |
| QQQ_LONG_PUT | 5 | 44/44 (0) | 9/35/0 | 20.45% | USD -149.45 | USD -6,576.00 | USD -3,096.50 | USD 2,192.27 | USD 0.00 |
| QQQ_LONG_PUT | 6 | 44/44 (0) | 9/35/0 | 20.45% | USD -179.35 | USD -7,891.20 | USD -3,715.80 | USD 2,630.73 | USD 0.00 |
| SPY_SHORT_PUT | 1 | 44/44 (0) | 33/11/0 | 75.00% | USD -38.00 | USD -1,672.20 | USD -3,007.30 | USD 432.20 | USD 39,675.00 |
| SPY_SHORT_PUT | 2 | 44/44 (0) | 33/11/0 | 75.00% | USD -76.01 | USD -3,344.40 | USD -6,014.60 | USD 864.41 | USD 79,350.00 |
| SPY_SHORT_PUT | 3 | 44/44 (0) | 33/11/0 | 75.00% | USD -114.01 | USD -5,016.60 | USD -9,021.90 | USD 1,296.61 | USD 119,025.00 |
| SPY_SHORT_PUT | 4 | 44/44 (0) | 33/11/0 | 75.00% | USD -152.02 | USD -6,688.80 | USD -12,029.20 | USD 1,728.82 | USD 158,700.00 |
| SPY_SHORT_PUT | 5 | 44/44 (0) | 33/11/0 | 75.00% | USD -190.02 | USD -8,361.00 | USD -15,036.50 | USD 2,161.02 | USD 198,375.00 |
| SPY_SHORT_PUT | 6 | 44/44 (0) | 33/11/0 | 75.00% | USD -228.03 | USD -10,033.20 | USD -18,043.80 | USD 2,593.23 | USD 238,050.00 |

### HOLD_20_SESSIONS

| Leg | N | Resolved/opened | Wins/losses/flat | Win rate | Mean net | Total net | Worst | Mean entry premium/credit | Mean SPY assignment obligation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| QQQ_LONG_PUT | 1 | 44/44 (0) | 9/35/0 | 20.45% | USD -55.91 | USD -2,460.20 | USD -870.30 | USD 438.45 | USD 0.00 |
| QQQ_LONG_PUT | 2 | 44/44 (0) | 9/35/0 | 20.45% | USD -111.83 | USD -4,920.40 | USD -1,740.60 | USD 876.91 | USD 0.00 |
| QQQ_LONG_PUT | 3 | 44/44 (0) | 9/35/0 | 20.45% | USD -167.74 | USD -7,380.60 | USD -2,610.90 | USD 1,315.36 | USD 0.00 |
| QQQ_LONG_PUT | 4 | 44/44 (0) | 9/35/0 | 20.45% | USD -223.65 | USD -9,840.80 | USD -3,481.20 | USD 1,753.82 | USD 0.00 |
| QQQ_LONG_PUT | 5 | 44/44 (0) | 9/35/0 | 20.45% | USD -279.57 | USD -12,301.00 | USD -4,351.50 | USD 2,192.27 | USD 0.00 |
| QQQ_LONG_PUT | 6 | 44/44 (0) | 9/35/0 | 20.45% | USD -335.48 | USD -14,761.20 | USD -5,221.80 | USD 2,630.73 | USD 0.00 |
| SPY_SHORT_PUT | 1 | 44/44 (0) | 35/9/0 | 79.55% | USD -91.37 | USD -4,020.20 | USD -9,516.30 | USD 432.20 | USD 39,675.00 |
| SPY_SHORT_PUT | 2 | 44/44 (0) | 35/9/0 | 79.55% | USD -182.74 | USD -8,040.40 | USD -19,032.60 | USD 864.41 | USD 79,350.00 |
| SPY_SHORT_PUT | 3 | 44/44 (0) | 35/9/0 | 79.55% | USD -274.10 | USD -12,060.60 | USD -28,548.90 | USD 1,296.61 | USD 119,025.00 |
| SPY_SHORT_PUT | 4 | 44/44 (0) | 35/9/0 | 79.55% | USD -365.47 | USD -16,080.80 | USD -38,065.20 | USD 1,728.82 | USD 158,700.00 |
| SPY_SHORT_PUT | 5 | 44/44 (0) | 35/9/0 | 79.55% | USD -456.84 | USD -20,101.00 | USD -47,581.50 | USD 2,161.02 | USD 198,375.00 |
| SPY_SHORT_PUT | 6 | 44/44 (0) | 35/9/0 | 79.55% | USD -548.21 | USD -24,121.20 | USD -57,097.80 | USD 2,593.23 | USD 238,050.00 |

### EXIT_AT_DTE_LE_7

| Leg | N | Resolved/opened | Wins/losses/flat | Win rate | Mean net | Total net | Worst | Mean entry premium/credit | Mean SPY assignment obligation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| QQQ_LONG_PUT | 1 | 36/44 (8) | 10/26/0 | 27.78% | USD 3.42 | USD 123.20 | USD -878.30 | USD 438.45 | USD 0.00 |
| QQQ_LONG_PUT | 2 | 36/44 (8) | 10/26/0 | 27.78% | USD 6.84 | USD 246.40 | USD -1,756.60 | USD 876.91 | USD 0.00 |
| QQQ_LONG_PUT | 3 | 36/44 (8) | 10/26/0 | 27.78% | USD 10.27 | USD 369.60 | USD -2,634.90 | USD 1,315.36 | USD 0.00 |
| QQQ_LONG_PUT | 4 | 36/44 (8) | 10/26/0 | 27.78% | USD 13.69 | USD 492.80 | USD -3,513.20 | USD 1,753.82 | USD 0.00 |
| QQQ_LONG_PUT | 5 | 36/44 (8) | 10/26/0 | 27.78% | USD 17.11 | USD 616.00 | USD -4,391.50 | USD 2,192.27 | USD 0.00 |
| QQQ_LONG_PUT | 6 | 36/44 (8) | 10/26/0 | 27.78% | USD 20.53 | USD 739.20 | USD -5,269.80 | USD 2,630.73 | USD 0.00 |
| SPY_SHORT_PUT | 1 | 36/44 (8) | 28/8/0 | 77.78% | USD -175.05 | USD -6,301.80 | USD -6,733.30 | USD 432.20 | USD 39,675.00 |
| SPY_SHORT_PUT | 2 | 36/44 (8) | 28/8/0 | 77.78% | USD -350.10 | USD -12,603.60 | USD -13,466.60 | USD 864.41 | USD 79,350.00 |
| SPY_SHORT_PUT | 3 | 36/44 (8) | 28/8/0 | 77.78% | USD -525.15 | USD -18,905.40 | USD -20,199.90 | USD 1,296.61 | USD 119,025.00 |
| SPY_SHORT_PUT | 4 | 36/44 (8) | 28/8/0 | 77.78% | USD -700.20 | USD -25,207.20 | USD -26,933.20 | USD 1,728.82 | USD 158,700.00 |
| SPY_SHORT_PUT | 5 | 36/44 (8) | 28/8/0 | 77.78% | USD -875.25 | USD -31,509.00 | USD -33,666.50 | USD 2,161.02 | USD 198,375.00 |
| SPY_SHORT_PUT | 6 | 36/44 (8) | 28/8/0 | 77.78% | USD -1,050.30 | USD -37,810.80 | USD -40,399.80 | USD 2,593.23 | USD 238,050.00 |

## Paired fixed-N matrix: mean net P&L per resolved cohort (base costs)

### HOLD_5_SESSIONS

| QQQ LONG N / SPY SHORT N | 1 | 2 | 3 | 4 | 5 | 6 |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | USD -46.76 | USD -71.06 | USD -95.36 | USD -119.66 | USD -143.96 | USD -168.26 |
| 2 | USD -69.22 | USD -93.52 | USD -117.82 | USD -142.12 | USD -166.42 | USD -190.72 |
| 3 | USD -91.68 | USD -115.98 | USD -140.28 | USD -164.58 | USD -188.88 | USD -213.18 |
| 4 | USD -114.14 | USD -138.44 | USD -162.74 | USD -187.04 | USD -211.34 | — |
| 5 | USD -136.60 | USD -160.90 | USD -185.20 | USD -209.50 | — | — |
| 6 | USD -159.05 | USD -183.35 | USD -207.65 | — | — | — |

### HOLD_10_SESSIONS

| QQQ LONG N / SPY SHORT N | 1 | 2 | 3 | 4 | 5 | 6 |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | USD -67.90 | USD -105.90 | USD -143.90 | USD -181.91 | USD -219.91 | USD -257.92 |
| 2 | USD -97.79 | USD -135.79 | USD -173.80 | USD -211.80 | USD -249.80 | USD -287.81 |
| 3 | USD -127.68 | USD -165.68 | USD -203.69 | USD -241.69 | USD -279.70 | USD -317.70 |
| 4 | USD -157.57 | USD -195.57 | USD -233.58 | USD -271.58 | USD -309.59 | — |
| 5 | USD -187.46 | USD -225.46 | USD -263.47 | USD -301.47 | — | — |
| 6 | USD -217.35 | USD -255.35 | USD -293.36 | — | — | — |

### HOLD_20_SESSIONS

| QQQ LONG N / SPY SHORT N | 1 | 2 | 3 | 4 | 5 | 6 |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | USD -147.28 | USD -238.65 | USD -330.02 | USD -421.39 | USD -512.75 | USD -604.12 |
| 2 | USD -203.20 | USD -294.56 | USD -385.93 | USD -477.30 | USD -568.67 | USD -660.04 |
| 3 | USD -259.11 | USD -350.48 | USD -441.85 | USD -533.21 | USD -624.58 | USD -715.95 |
| 4 | USD -315.02 | USD -406.39 | USD -497.76 | USD -589.13 | USD -680.50 | — |
| 5 | USD -370.94 | USD -462.30 | USD -553.67 | USD -645.04 | — | — |
| 6 | USD -426.85 | USD -518.22 | USD -609.59 | — | — | — |

### EXIT_AT_DTE_LE_7

| QQQ LONG N / SPY SHORT N | 1 | 2 | 3 | 4 | 5 | 6 |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | USD -171.63 | USD -346.68 | USD -521.73 | USD -696.78 | USD -871.83 | USD -1,046.88 |
| 2 | USD -168.21 | USD -343.26 | USD -518.31 | USD -693.36 | USD -868.41 | USD -1,043.46 |
| 3 | USD -164.78 | USD -339.83 | USD -514.88 | USD -689.93 | USD -864.98 | USD -1,040.03 |
| 4 | USD -161.36 | USD -336.41 | USD -511.46 | USD -686.51 | USD -861.56 | — |
| 5 | USD -157.94 | USD -332.99 | USD -508.04 | USD -683.09 | — | — |
| 6 | USD -154.52 | USD -329.57 | USD -504.62 | — | — | — |

## Risk / execution guardrails

- QQQ LONG PUT expiry loss is limited to premium paid before costs, but interim liquidation and fills are not guaranteed.
- SPY SHORT PUT premium credit does not cap loss; its strike-based assignment obligation is reported separately and can be much larger than the credit.
- Equal premium is not equal Delta, notional, margin, assignment obligation, or tail risk. Fixed N changes exposure and cash flow together.
- Standalone results keep each selected contract fixed to isolate leg contribution. They are not a separate strategy that reselects strikes for only one ETF.
- No app sizing changes, broker connections, or live orders are authorized by this analysis.

Files: independent_leg_trade_episodes.csv, independent_leg_sizing_summary.csv, independent_leg_pair_matrix.csv, cost_sensitivity.csv, source_manifest.json.
