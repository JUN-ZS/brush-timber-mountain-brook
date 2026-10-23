# QQQ/SPY Fixed-Ratio Temporal Stability Audit V1

## Purpose
Audit time dependence of the completed 1:6, 4:5, 2:4 and 1:3 size-gated replay outputs. Consume only committed trade_episodes.csv files; do not redownload source data, rerun the strategy, or adjust parameters.

## Frozen scope
- Group by signal date for each year and eras 2018-2021, 2022-2023, 2024-2025.
- Policies: 5-session, 10-session, 20-session, and DTE <= 7.
- Retain existing base-cost P&L and exact resolved/unresolved statuses.
- Verify identical episode IDs and signal dates across ratios before comparison.

## Required metrics
By ratio, year/era and policy: opened/resolved/unresolved, wins/losses/flats, resolved-only win rate and Wilson interval, mean/median/total/worst P&L, profit factor, QQQ/SPY leg attribution and available marked adverse-P&L summaries. Unresolved trades must never be assigned zero or silently removed from coverage counts.

## Interpretation boundaries
- This is an in-sample temporal robustness audit, not an untouched out-of-sample test.
- Ratios were explored after reviewing this history; positive results require a frozen prospective paper replay on genuinely new quotes before a robust-alpha claim.
- Era cohorts are small; Wilson intervals are nominal and do not correct serial dependence, overlapping regimes or prior strategy selection.
- EOD displayed-size screens are not confirmed multi-leg fills.
- SPY short-put P&L and assignment obligation are not risk-free carry, broker margin or capped maximum loss.
- No merge to main, app sizing changes, broker connection or live orders.

## Outputs
- results/temporal_stability_audit/temporal_stability.csv: per-year and per-era results.
- results/temporal_stability_audit/report.md: comparison report.
- results/temporal_stability_audit/audit.json: complete metrics, input hashes and cohort reconciliation.
