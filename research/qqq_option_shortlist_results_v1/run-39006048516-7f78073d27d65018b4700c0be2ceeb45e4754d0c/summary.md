# QQQ Option Shortlist Replay V1

Evidence: OBSERVED_EOD_QUOTES_WITH_DERIVED_QUOTE_SIDE_REPLAY_NOT_CONFIRMED_FILLS

- Signals: 28; processed: 28; sessions: 1960 (2018-03-01 to 2025-12-15).
- Matched QQQ-core control: {"episodes": 28, "resolved": 28, "mean_10_session_pnl_on_1000_usd_notional": 13.15, "median_10_session_pnl_on_1000_usd_notional": 20.59, "worst_10_session_pnl_on_1000_usd_notional": -74.4, "positive_10_session_ratio_pct": 60.7143, "note": "Underlying-only matched price-path control; not option P&L or a $80k portfolio return."}

## Strategy results (one unit per episode)

| Strategy | Opened | Resolved | Win rate | Mean P&L | Worst P&L | PF | Episodes sizeable at 1% NAV tail budget |
|---|---:|---:|---:|---:|---:|---:|---:|
| CALL_DEBIT_50D_10D | 28 | 28 | 57.1429 | 92.72 | -972.6 | 1.40138 | 7 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 24 | 24 | 58.3333 | 49.02 | -984.9 | 1.20505 | 3 |
| PUT_LONG_HEAVY_1x1 | 28 | 28 | 25.0 | -154.28 | -578.6 | 0.27842 | 27 |
| PUT_LONG_HEAVY_2x1 | 28 | 28 | 25.0 | -354.97 | -1375.9 | 0.28939 | 7 |
| PUT_LONG_HEAVY_3x1 | 28 | 28 | 25.0 | -555.66 | -2173.2 | 0.29238 | 2 |
| PUT_LONG_HEAVY_4x1 | 28 | 28 | 25.0 | -756.36 | -2970.5 | 0.29377 | 2 |
| PUT_LONG_HEAVY_5x1 | 28 | 28 | 25.0 | -957.05 | -3767.8 | 0.29458 | 0 |
| PUT_LONG_HEAVY_6x1 | 27 | 27 | 25.9259 | -1031.54 | -4444.1 | 0.32763 | 0 |
| PUT_SHORT_HEAVY_1x1 | 28 | 28 | 25.0 | -154.28 | -578.6 | 0.27842 | 27 |
| PUT_SHORT_HEAVY_1x2 | 28 | 28 | 28.5714 | -107.86 | -445.9 | 0.2402 | 0 |
| PUT_SHORT_HEAVY_1x3 | 28 | 28 | 32.1429 | -61.45 | -494.2 | 0.31226 | 0 |
| PUT_SHORT_HEAVY_1x4 | 28 | 28 | 53.5714 | -15.04 | -763.5 | 0.77929 | 0 |
| PUT_SHORT_HEAVY_1x5 | 28 | 28 | 78.5714 | 31.38 | -1226.8 | 1.41137 | 0 |
| PUT_SHORT_HEAVY_1x6 | 28 | 28 | 78.5714 | 77.79 | -1690.1 | 1.77115 | 0 |

## Interpretation guardrails

- Source option chains end 2025-12-15; no option P&L beyond that date.
- Quotes are public EOD preservation snapshots reported as 16:00 ET; exact tick timestamp and fills are unverified.
- Episode results are a matched fixed-horizon event study, not compounded portfolio CAGR/MaxDD.
- No broker margin, assignment, early exercise, forced liquidation, multi-leg fill sequencing, or market impact model.
- Terminal loss is intrinsic payoff at strike knots using observed entry-side prices; it does not bound interim liquidation losses.
- Candidate selection is fixed by DTE/delta and not optimized on P&L; the signal-family thresholds are a research hypothesis and require a later unseen holdout.
