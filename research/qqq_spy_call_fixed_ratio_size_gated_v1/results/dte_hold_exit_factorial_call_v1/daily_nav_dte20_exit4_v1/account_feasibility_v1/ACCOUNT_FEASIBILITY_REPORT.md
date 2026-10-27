# QQQ/SPY PUT + CALL account feasibility and margin stress

- Strategy input: existing audited DTE20 / remaining calendar DTE <= 4 daily NAV replay; not a new strategy optimization.
- Legs: QQQ LONG PUT 1 : SPY SHORT PUT 6 (target abs-Delta 0.25) and QQQ LONG CALL 1 : SPY SHORT CALL 6 (target abs-Delta 0.20), same expiry for strict paired baskets.
- Current QQQ holding input is USD 63,694 at USD 712.20 on 2026-10-26, equivalent to 89.4327 shares. The fixed share count is backcast over 2018-2025; its start value is USD 14,709.90. This is a counterfactual position-history assumption, not proof the account actually held these shares in 2018.
- Account equity is cash + QQQ market value + signed option liquidation value less estimated closing costs. Initial cash = scenario capital minus the historical starting QQQ value. Option entry/exit cash flows include USD 0.05/share/side slippage and USD 0.65/contract/side commission.
- New baskets are rejected if post-entry equity is below the modeled initial-margin requirement. Existing options are liquidated at EOD liquidation-side marks if equity is nonpositive or below modeled maintenance margin; once this occurs, the simulator stops opening new baskets.
- Timing limit: checks occur at end-of-day only. Intraday margin calls, gap-through fills, borrow availability, interest, exercise/assignment fees, taxes and broker-specific house margin are not simulated.
- Margin proxy applies an Interactive Brokers-published uncovered stock-option formula separately to each short SPY option, with no cross-leg offsets; it adds 50% of QQQ stock value for initial margin and 25% for maintenance. 1.5x and 2.0x variants are hypothetical house-margin stress multipliers, not official broker settings.
- Full SPY short-PUT strike notional is reported as a cash-secured assignment reserve, separately from the margin proxy. Short-call delivery notional is not the same as cash required or maximum loss.
- Stress scenarios apply hypothetical QQQ/SPY spot shocks and assumed multipliers on remaining option extrinsic value. They are sensitivities, not forecasts or full option-pricing outputs, and cannot bound naked short-call losses.
- The prior daily NAV added stock market value to option P&L but omitted initial account cash. Therefore its >100% drawdown percentages were not account-return percentages. This report rebases each run to explicit starting account capital.

## Capital scenarios (1.0x margin proxy; worst phase)

| Starting capital | Worst max DD USD | Worst max DD % | Lowest end equity | Blocked baskets | Forced liquidations | Peak put assignment reserve | Peak call delivery notional | Peak cash gap vs put reserve |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| USD 100,000 | USD -47,092.57 | -34.44% | USD 112,575.60 | 170 | 2 | USD 399,600.00 | USD 418,800.00 | USD 271,470.85 |
| USD 250,000 | USD -66,221.54 | -23.10% | USD 253,985.40 | 0 | 0 | USD 404,400.00 | USD 422,400.00 | USD 203,343.25 |
| USD 500,000 | USD -66,221.54 | -12.34% | USD 503,985.40 | 0 | 0 | USD 404,400.00 | USD 422,400.00 | USD 0.00 |
| USD 750,000 | USD -66,221.54 | -8.42% | USD 753,985.40 | 0 | 0 | USD 404,400.00 | USD 422,400.00 | USD 0.00 |
| USD 1,000,000 | USD -66,221.54 | -6.39% | USD 1,003,985.40 | 0 | 0 | USD 404,400.00 | USD 422,400.00 | USD 0.00 |

## Margin sensitivity across capital sizes

| Starting capital | Margin multiplier | Phases with forced liquidation | Total blocked baskets | Worst max DD % | Lowest stressed margin cushion |
|---:|---:|---:|---:|---:|---:|
| USD 100,000 | 1.0x | 2 | 170 | -34.44% | USD -755,819.31 |
| USD 100,000 | 1.5x | 3 | 431 | -18.35% | USD -543,178.29 |
| USD 100,000 | 2.0x | 2 | 516 | -10.83% | USD -527,247.42 |
| USD 250,000 | 1.0x | 0 | 0 | -23.10% | USD -676,654.71 |
| USD 250,000 | 1.5x | 0 | 6 | -23.10% | USD -966,455.36 |
| USD 250,000 | 2.0x | 1 | 38 | -17.43% | USD -1,240,856.16 |
| USD 500,000 | 1.0x | 0 | 0 | -12.34% | USD -426,654.72 |
| USD 500,000 | 1.5x | 0 | 0 | -12.34% | USD -732,751.02 |
| USD 500,000 | 2.0x | 0 | 0 | -12.34% | USD -1,038,847.32 |
| USD 750,000 | 1.0x | 0 | 0 | -8.42% | USD -176,654.72 |
| USD 750,000 | 1.5x | 0 | 0 | -8.42% | USD -482,751.02 |
| USD 750,000 | 2.0x | 0 | 0 | -8.42% | USD -788,847.32 |
| USD 1,000,000 | 1.0x | 0 | 0 | -6.39% | USD 73,345.28 |
| USD 1,000,000 | 1.5x | 0 | 0 | -6.39% | USD -232,751.02 |
| USD 1,000,000 | 2.0x | 0 | 0 | -6.39% | USD -538,847.32 |

## Interpretation boundaries

- A cash-only put seller needs full exercise cash for the short puts; this portfolio also sells uncovered SPY calls. The QQQ shares and QQQ long options do not contractually cover SPY short calls.
- The listed-option margin calculation is a broker-specific reference formula, not a guarantee of buying-power acceptance. Actual brokers can impose higher house requirements and liquidate intraday.
- An uncovered short call has theoretically unlimited loss. A +100% stress case is only one finite scenario, not a maximum-loss estimate.
- A backtest pass confirms code/data reconciliation, not that a broker would allow these trades or that historical EOD marks were executable fills.

References: Interactive Brokers — https://www.interactivebrokers.com/en/trading/margin-options.php ; Options Industry Council naked-call risk — https://www.optionseducation.org/strategies/all-strategies/naked-call-uncovered-call-short-call .

Files: phase_margin_summary.csv, capital_summary.csv, daily_account_nav.csv, entry_decisions.csv, margin_events.csv, stress_scenario_summary.csv, account_feasibility_audit.json.
