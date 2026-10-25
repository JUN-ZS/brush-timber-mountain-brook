# DTE45 cadence grid — overlapping 1:6 replay

- Frozen window: 2018-03-01 to 2025-12-15 (7.792 calendar years).
- Fixed legs: QQQ LONG PUT 1 : SPY SHORT PUT 6; DTE 30–60, target 45; both legs abs Delta target 0.25; no entry filter.
- Exit: hold up to 20 sessions, or exit when remaining DTE <= 7, whichever comes first.
- Costs: USD 0.05 per option-share per side + USD 0.65 per contract per side.
- Cadence grid: every 5, 7, 10, 15 or 20 common sessions; five predeclared phase starts per stride. The stride-5 set covers every phase; longer strides use five spread phases, not exhaustive phase enumeration.
- Phase accounts are separate schedules. They are summarized by median and range; their P&L is not pooled as if independent.

## Annual additive trade-P&L by cadence

| Entry stride | Phase runs | Median annual resolved-trade P&L | Min–max annual P&L | Phases >= $12k/year | Median entries | Median unresolved | Median peak concurrent cohorts | Median peak gross SPY assignment obligation |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 sessions | 5 | $24,716 | $23,537 to $29,063 | 5/5 | 391 | 7 | 7 | $1,960,200 |
| 7 sessions | 5 | $18,562 | $17,516 to $21,860 | 5/5 | 279 | 4 | 5 | $1,564,800 |
| 10 sessions | 5 | $12,996 | $8,542 to $15,435 | 4/5 | 195 | 3 | 3 | $1,173,600 |
| 15 sessions | 5 | $8,802 | $7,427 to $10,908 | 0/5 | 131 | 2 | 2 | $787,200 |
| 20 sessions | 5 | $6,192 | $4,134 to $8,116 | 0/5 | 98 | 2 | 2 | $790,200 |

## All phase results

| Stride | Phase | Entries | Resolved | Unresolved | Win rate | Mean P&L/trade | Total resolved P&L | Annual average | Worst trade | Profit factor | Peak concurrent | Peak gross SPY assignment obligation |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 0 | 392 | 384 | 8 | 83.33% | $589.72 | $226,453.60 | $29,062.61 | $-51,851.10 | 1.647 | 7 | $1,960,200 |
| 5 | 1 | 392 | 384 | 8 | 82.29% | $496.87 | $190,799.60 | $24,486.84 | $-44,015.10 | 1.543 | 7 | $1,960,800 |
| 5 | 2 | 391 | 384 | 7 | 82.55% | $501.53 | $192,588.60 | $24,716.44 | $-51,761.10 | 1.520 | 7 | $1,972,800 |
| 5 | 3 | 390 | 386 | 4 | 80.83% | $475.12 | $183,397.40 | $23,536.86 | $-52,171.10 | 1.474 | 5 | $1,953,600 |
| 5 | 4 | 389 | 383 | 6 | 79.90% | $560.88 | $214,816.70 | $27,569.15 | $-46,365.10 | 1.610 | 6 | $1,945,800 |
| 7 | 0 | 280 | 276 | 4 | 81.88% | $524.02 | $144,630.40 | $18,561.58 | $-39,635.10 | 1.599 | 5 | $1,569,000 |
| 7 | 1 | 278 | 274 | 4 | 79.93% | $498.12 | $136,484.60 | $17,516.16 | $-41,069.10 | 1.515 | 5 | $1,561,800 |
| 7 | 3 | 280 | 274 | 6 | 81.02% | $522.25 | $143,096.60 | $18,364.73 | $-52,171.10 | 1.549 | 5 | $1,572,600 |
| 7 | 4 | 279 | 275 | 4 | 81.09% | $619.39 | $170,333.50 | $21,860.26 | $-46,365.10 | 1.752 | 5 | $1,564,800 |
| 7 | 6 | 278 | 273 | 5 | 83.88% | $532.07 | $145,255.70 | $18,641.83 | $-44,015.10 | 1.518 | 4 | $1,562,400 |
| 10 | 0 | 196 | 193 | 3 | 82.90% | $623.14 | $120,266.70 | $15,434.79 | $-29,813.10 | 1.707 | 4 | $1,173,600 |
| 10 | 2 | 195 | 192 | 3 | 82.81% | $346.66 | $66,558.80 | $8,542.02 | $-51,761.10 | 1.313 | 3 | $1,171,200 |
| 10 | 4 | 195 | 192 | 3 | 79.69% | $527.43 | $101,266.80 | $12,996.38 | $-46,365.10 | 1.524 | 3 | $1,161,600 |
| 10 | 6 | 196 | 191 | 5 | 82.72% | $502.36 | $95,949.90 | $12,314.02 | $-44,015.10 | 1.549 | 4 | $1,186,800 |
| 10 | 8 | 194 | 192 | 2 | 81.77% | $613.04 | $117,702.80 | $15,105.74 | $-39,445.10 | 1.729 | 3 | $1,188,000 |
| 15 | 0 | 131 | 129 | 2 | 84.50% | $531.64 | $68,582.10 | $8,801.69 | $-51,851.10 | 1.507 | 3 | $831,000 |
| 15 | 3 | 131 | 129 | 2 | 80.62% | $509.65 | $65,745.10 | $8,437.60 | $-29,316.10 | 1.566 | 2 | $786,000 |
| 15 | 6 | 131 | 128 | 3 | 81.25% | $452.13 | $57,873.20 | $7,427.33 | $-25,585.10 | 1.481 | 3 | $825,000 |
| 15 | 9 | 129 | 128 | 1 | 77.34% | $664.04 | $84,997.20 | $10,908.37 | $-28,698.10 | 1.781 | 2 | $772,200 |
| 15 | 12 | 129 | 127 | 2 | 83.46% | $667.14 | $84,726.30 | $10,873.61 | $-51,761.10 | 1.732 | 2 | $787,200 |
| 20 | 0 | 98 | 97 | 1 | 80.41% | $623.20 | $60,450.30 | $7,758.07 | $-16,732.10 | 1.778 | 2 | $777,000 |
| 20 | 4 | 98 | 96 | 2 | 77.08% | $474.30 | $45,532.40 | $5,843.54 | $-12,989.10 | 1.457 | 2 | $779,400 |
| 20 | 8 | 97 | 96 | 1 | 82.29% | $502.61 | $48,250.40 | $6,192.36 | $-39,445.10 | 1.522 | 2 | $801,000 |
| 20 | 12 | 98 | 96 | 2 | 87.50% | $335.54 | $32,211.40 | $4,133.95 | $-51,761.10 | 1.296 | 2 | $790,200 |
| 20 | 16 | 98 | 96 | 2 | 83.33% | $658.74 | $63,239.40 | $8,116.02 | $-44,015.10 | 1.786 | 2 | $795,000 |

## Interpretation limits

The $12,000/year marker refers only to the additive sum of resolved episode P&L divided by calendar years. It is not account annual profit, CAGR, or a guarantee that a $100,000 NAV can support the strategy. Unresolved trade P&L is excluded from the sum and reported separately.

Overlapping gross assignment obligations must not be read as broker margin, but they expose why cadence alone does not prove account feasibility. The replay has no integrated cash, margin, assignment funding, forced-liquidation, financing, tax, or compounding engine. Far-OTM TAIL premiums are excluded. EOD quote-side prices are not verified executions.

Select a cadence only if its phase median and range are both acceptable; do not pick the single best phase. The five phases for strides above 5 are a robustness sample, not a full enumeration of all possible anchors.

Outputs: cadence_phase_matrix.csv and per-run stride/phase summary.json, trade_episodes.csv, and CADENCE_REPORT.md files.
