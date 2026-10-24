# QQQ/SPY Put Cadence Grid V1 — Research Contract

## Objective
Find a defensible increase over roughly 5–6 cohorts/year without mistaking more trades for better risk-adjusted results.

## Frozen dimensions
- Source: the same SHA-pinned historical QQQ/SPY option-chain mirror used by the fixed-ratio replay.
- Dates for source data: 2018-03-01 through 2025-12-15; common option-chain availability ends 2025-12-12.
- Decision windows: signal-date windows ending 2025-07-23: 1Y 2024-07-23–2025-07-23; 3Y 2022-07-23–2025-07-23; 5Y 2020-07-23–2025-07-23.
- Ratios: fixed QQQ LONG PUT : SPY SHORT PUT = 1:6, 4:5, 2:4, 1:3.
- Cadence grid: 5, 10, 15, 20, 30 and 45 common underlying sessions between eligible signal checks after a successful signal. No-filter signals are checked on cadence; filtered signals still require QQQ's trailing 20-session return to be below SPY's.
- Entry filters: none; qqq_underperforms_spy_20d.
- Exits: 5, 10 or 20 common sessions, and the existing DTE <= 7 policy.
- Contract selection: same expiry, DTE 30–60 targeting 45 DTE, absolute Delta target 0.25 within the existing 0.10–0.50 eligibility band.
- Trading-cost assumptions: conservative quote sides, displayed side-size gate, $0.05 option-share slippage per side and $0.65 contract commission per side.

## Critical engine change
The prior engine serialized entry cohorts with `not active`, which meant reducing the stride alone could not demonstrate genuine overlapping entries. This grid explicitly enables `--allow-overlapping-cohorts`. Every opened cohort remains fixed-size; distinct cohorts may overlap while earlier exit-policy variants remain open.

## Required outputs
- Per-window counts and net P&L, win rate, mean/median resolved trade, total and annualized resolved P&L, worst resolved trade, unresolved count and 0.10 slippage stress.
- Peak concurrent active cohorts and peak summed SPY short-put assignment obligation for each exit policy, estimated from entry to exit/last observed date. This is a gross assignment-obligation proxy, not broker margin.
- Calendar-year cohort counts and resolved P&L; all source summaries and trade ledgers.
- Pareto flags compare cadence settings only within the same window, filter, ratio and exit policy, using annualized net P&L, win rate, worst resolved trade and peak assignment obligation. No single arbitrary weighted score or hard PASS threshold is introduced.

## Interpretation limits
Results are in-sample research, not forward-alpha evidence. EOD displayed size is not a guaranteed multi-leg fill. The engine does not constrain account NAV, collateral, buying power, margin, simultaneous loss, taxes, financing, or forced liquidation. Summed cohort P&L is not a compounded account return. Contract-size ratios differ in gross exposure, so ratio comparisons require risk context. Unresolved trades are excluded from realized-P&L means/totals and separately counted.
