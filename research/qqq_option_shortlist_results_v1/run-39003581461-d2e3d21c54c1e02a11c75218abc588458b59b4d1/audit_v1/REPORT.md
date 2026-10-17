# QQQ Option Shortlist V1 — Cost / Time-Split / Tail-Capacity Audit

## Evidence class

- Source run: 39003581461; replay window 2018-03-01 to 2025-12-15; 1,960 sessions, 28 signals, 387 strategy-episode rows.
- Input hashes: manifest 1a25a8857cfec8a453a25448ec59ee60297488f4d05c2986bf11345a479d93e7; summary b2b6d149d6548db32c2b7ff3764289a561d4dc1c8f79751319c1807174f4357b; trades a9ee12ab3a86d5c5f4e8e7c06574a809711c1c7252ab6d7fa358e0caa5e0f5e9.
- Evidence: OBSERVED_EOD_QUOTES_WITH_DERIVED_QUOTE_SIDE_REPLAY_NOT_CONFIRMED_FILLS. This is a persisted-data audit, not a fresh quote download or a confirmed-fill replay.
- Scenario arithmetic is applied to the already replayed exact listed-contract rows; it does not reselect contracts or refit the signal.

## Base-case outcome summary

| Strategy | Period | n | Wins | Win rate (nominal Wilson 95%) | Mean net P&L/unit | PF | Worst P&L/unit | Fits 0.5% / 1% / 2% NAV tail budget |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| CALL_DEBIT_50D_10D | ALL_2018_2025 | 28 | 16 | 57.1% (39.1–73.5%) | 92.72 | 1.40138 | -972.60 | 0 / 7 / 22 |
| CALL_DEBIT_50D_10D | EARLIER_2018_2022 | 19 | 10 | 52.6% (31.7–72.7%) | 21.66 | 1.09366 | -967.60 | 0 / 7 / 16 |
| CALL_DEBIT_50D_10D | LATER_2023_2025 | 9 | 6 | 66.7% (35.4–87.9%) | 242.73 | 2.05343 | -972.60 | 0 / 0 / 6 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | ALL_2018_2025 | 24 | 14 | 58.3% (38.8–75.5%) | 49.02 | 1.20505 | -984.90 | 0 / 3 / 18 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | EARLIER_2018_2022 | 15 | 8 | 53.3% (30.1–75.2%) | -21.30 | 0.91167 | -975.90 | 0 / 3 / 12 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | LATER_2023_2025 | 9 | 6 | 66.7% (35.4–87.9%) | 166.21 | 1.70571 | -984.90 | 0 / 0 / 6 |
| PUT_SHORT_HEAVY_1x5 | ALL_2018_2025 | 28 | 22 | 78.6% (60.5–89.8%) | 31.38 | 1.41137 | -1226.80 | 0 / 0 / 0 |
| PUT_SHORT_HEAVY_1x6 | ALL_2018_2025 | 28 | 22 | 78.6% (60.5–89.8%) | 77.79 | 1.77115 | -1690.10 | 0 / 0 / 0 |
| PUT_LONG_HEAVY_2x1 | ALL_2018_2025 | 28 | 7 | 25.0% (12.7–43.4%) | -354.97 | 0.28939 | -1375.90 | 2 / 7 / 24 |

## Cost sensitivity: mean net P&L per one structure unit

| Strategy | Period | Zero friction | Base | Stress slippage |
|---|---|---:|---:|---:|
| CALL_DEBIT_50D_10D | ALL_2018_2025 | 115.32 | 92.72 | 72.72 |
| CALL_DEBIT_50D_10D | EARLIER_2018_2022 | 44.26 | 21.66 | 1.66 |
| CALL_DEBIT_50D_10D | LATER_2023_2025 | 265.33 | 242.73 | 222.73 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | ALL_2018_2025 | 82.92 | 49.02 | 19.02 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | EARLIER_2018_2022 | 12.60 | -21.30 | -51.30 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | LATER_2023_2025 | 200.11 | 166.21 | 136.21 |
| PUT_SHORT_HEAVY_1x5 | ALL_2018_2025 | 99.18 | 31.38 | -28.62 |
| PUT_SHORT_HEAVY_1x6 | ALL_2018_2025 | 156.89 | 77.79 | 7.79 |
| PUT_LONG_HEAVY_2x1 | ALL_2018_2025 | -321.07 | -354.97 | -384.97 |

## Paired effect of adding one LONG PUT to the call debit vertical

| Period | Cost case | Matched events | Put hedge has higher net P&L | Mean incremental P&L | Median incremental P&L | Mean MAE change | MAE improves in pairs |
|---|---|---:|---:|---:|---:|---:|---:|
| ALL_2018_2025 | ZERO | 24 | 4 | -60.2917 | -77.0 | 29.075 | 12 |
| ALL_2018_2025 | BASE | 24 | 3 | -71.5917 | -88.3 | 29.075 | 12 |
| ALL_2018_2025 | STRESS | 24 | 3 | -81.5917 | -98.3 | 29.075 | 12 |
| EARLIER_2018_2022 | ZERO | 15 | 3 | -57.3333 | -91.0 | 18.1 | 7 |
| EARLIER_2018_2022 | BASE | 15 | 2 | -68.6333 | -102.3 | 18.1 | 7 |
| EARLIER_2018_2022 | STRESS | 15 | 2 | -78.6333 | -112.3 | 18.1 | 7 |
| LATER_2023_2025 | ZERO | 9 | 1 | -65.2222 | -72.0 | 47.3667 | 5 |
| LATER_2023_2025 | BASE | 9 | 1 | -76.5222 | -83.3 | 47.3667 | 5 |
| LATER_2023_2025 | STRESS | 9 | 1 | -86.5222 | -93.3 | 47.3667 | 5 |

## Decision, not a winner badge

- A positive per-unit mean is not sufficient. Capacity must be nonzero at the actual whole-contract tail-risk budget, and it must survive the adverse-cost case.
- The late-period slice contains only nine call-debit events; it is a directional consistency check, not a statistically conclusive or fully untouched holdout.
- The PUT Ratio variants with N short-heavy can show positive event-level P&L while having no full-size capacity under 0.5%/1%/2% of $80k terminal-tail budgets. Do not promote them on win rate.
- The add-on LONG PUT is a paid hedge. Judge it by paired event P&L and adverse mark changes together, not by the name 'protection'.
- No strategy is approved for HUB execution by this audit. The next promotion gate is a predeclared risk-normalized portfolio replay with same NAV, same risk capital, marked option legs, and an untouched later period.

## Limitations

- Public historical EOD quote snapshots, not authenticated fills; exact tick timestamps, broker margin, exercise/assignment, fill sequencing and market impact are not verified.
- Signal episodes and regime windows are not independent random trials. Wilson intervals are descriptive and may be too narrow.
- Episode P&L is noncompounded one-unit P&L, not portfolio CAGR, portfolio MaxDD, or a proven NAV allocation result.
- The 1xN and Nx1 PUT Ratio candidates share selected strikes but multiply different legs; large entry terminal tail losses can make every full unit infeasible even when short-period P&L is positive.
- The latest option chain date is 2025-12-15; no option result after that date is claimed.
- The terminal loss used for illustrative capacity is expiry intrinsic payoff at payoff knots; it does not cap interim liquidation, margin expansion, forced liquidation or gap losses.
