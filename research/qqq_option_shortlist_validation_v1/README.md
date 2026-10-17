# QQQ Option Shortlist Validation V1

Audit of the already completed QQQ option shortlist event replay. It locks the source trades.csv by its Git blob SHA, recalculates zero/base/doubled-slippage costs, splits the fixed events into descriptive time ranges, reports Wilson intervals for win rates, recomputes terminal-loss size feasibility and compares call debit against call debit plus a long put on the same signal dates.

No signals or contracts are reselected. The later-period split has already been viewed and is not a virgin holdout. The source option history ends 2025-12-15; any confirmatory next step must use prospective timestamped option quote records or a newly verified archival source. Outputs are research-only, not confirmed fills, broker-approved capacity or a portfolio CAGR/MaxDD claim.
