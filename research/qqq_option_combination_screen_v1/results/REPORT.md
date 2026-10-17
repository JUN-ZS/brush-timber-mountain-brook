# QQQ + Options Combination Screen V1

**Status: research-only; no live sizing changes and no broker orders.**

## Prespecified candidates

- CORE_ONLY: buy-and-hold QQQ shares sized to 42% of initial NAV; the remaining cash stays uninvested.
- CORE_PLUS_PUT_DEBIT: the same core plus a 18–35 DTE QQQ put debit vertical (buy approximately 25-delta put, sell lower-strike approximately 10-delta put). Entry debit budget: 2% of prior observed NAV.
- CORE_PLUS_CALL_CREDIT: the same core plus a 18–35 DTE QQQ call credit vertical (sell approximately 16-delta call, buy higher-strike approximately 8-delta protective call). Budget: 0.8% of prior observed NAV in conservative vertical max loss.
- CORE_PLUS_CALL_AND_PUT: both option sleeves at their single-sleeve budgets. This has a larger combined nominal budget, so raw CAGR is not a matched-total-risk comparison.

Candidates are selected from the prior observed session and entered next session using the exact same contract IDs. Invalid/missing quotes are not replaced or interpolated. Existing positions are closed using exact held-contract side quotes when DTE reaches 7 calendar days or less.

## Source and execution

- Underlying/option date range: 2011-03-23 to 2025-12-15.
- SHA-256 options: 1f831556cd87ec9d7af43d3b47a69a829ffb2fb199cfcef4ff55d289badf8734; underlying: 78c015fd7fa9d493cd798d5ae81b3c2ae6dc3b8176e25e7bb90cd4114b103351.
- BASE: $0.05/leg/share slippage per side + $0.65 per contract/leg/side commission. STRESS doubles slippage to $0.10; commission is unchanged.
- Entry/exit use historical bid/ask plus modeled slippage; daily marks use exact-contract bid/ask midpoints. These are quote-side simulations, not authenticated broker fills or displayed-depth replay.
- QQQ core returns are close-to-close price-only; dividends are not fabricated/inferred. Core shares are not rebalanced.
- P&L is attributed to QQQ core, put debit spread, and call credit spread. NAV reconciliation must be within one cent on complete marks.

## Results

| variant                | cost_case   |   initial_nav_usd |   final_nav_usd |   cagr_pct |   maxdd_observed_marks_pct |   worst_observed_calendar_year_pct |   worst_observed_daily_return_pct |   entries |   exits |   missing_or_incomplete_nav_marks |
|:-----------------------|:------------|------------------:|----------------:|-----------:|---------------------------:|-----------------------------------:|----------------------------------:|----------:|--------:|----------------------------------:|
| CORE_ONLY              | BASE        |        80000.0000 |     414562.4900 |    11.8146 |                   -29.9179 |                           -27.7100 |                           -8.5555 |         0 |       0 |                                 0 |
| CORE_PLUS_PUT_DEBIT    | BASE        |        80000.0000 |     368159.0900 |    10.9173 |                   -43.1397 |                           -33.0698 |                          -11.9784 |        45 |      45 |                                 0 |
| CORE_PLUS_CALL_CREDIT  | BASE        |        80000.0000 |     372188.0900 |    10.9993 |                   -33.8612 |                           -31.5491 |                          -10.4682 |       338 |     337 |                                 9 |
| CORE_PLUS_CALL_AND_PUT | BASE        |        80000.0000 |     341295.7900 |    10.3483 |                   -45.1317 |                           -36.0446 |                          -13.9127 |       379 |     378 |                                 9 |
| CORE_ONLY              | STRESS      |        80000.0000 |     414562.4900 |    11.8146 |                   -29.9179 |                           -27.7100 |                           -8.5555 |         0 |       0 |                                 0 |
| CORE_PLUS_PUT_DEBIT    | STRESS      |        80000.0000 |     368099.6900 |    10.9161 |                   -47.5109 |                           -33.0780 |                          -11.9846 |        37 |      37 |                                 0 |
| CORE_PLUS_CALL_CREDIT  | STRESS      |        80000.0000 |     363885.8900 |    10.8294 |                   -34.7521 |                           -32.3728 |                          -10.4274 |       290 |     289 |                                 9 |
| CORE_PLUS_CALL_AND_PUT | STRESS      |        80000.0000 |     334608.9900 |    10.2002 |                   -47.8807 |                           -36.9705 |                          -14.0643 |       326 |     325 |                                 9 |
| CORE_ONLY              | BASE        |      1000000.0000 |    5182863.3700 |    11.8158 |                   -29.9195 |                           -27.7116 |                           -8.5564 |         0 |       0 |                                 0 |
| CORE_PLUS_PUT_DEBIT    | BASE        |      1000000.0000 |    4601503.1700 |    10.9165 |                   -43.5272 |                           -33.0852 |                          -11.9900 |        42 |      42 |                                 0 |
| CORE_PLUS_CALL_CREDIT  | BASE        |      1000000.0000 |    4590948.9700 |    10.8992 |                   -34.2677 |                           -31.9597 |                          -10.6492 |       338 |     337 |                                 9 |
| CORE_PLUS_CALL_AND_PUT | BASE        |      1000000.0000 |    4218623.1700 |    10.2644 |                   -46.0383 |                           -36.5220 |                          -14.1550 |       379 |     378 |                                 9 |
| CORE_ONLY              | STRESS      |      1000000.0000 |    5182863.3700 |    11.8158 |                   -29.9195 |                           -27.7116 |                           -8.5564 |         0 |       0 |                                 0 |
| CORE_PLUS_PUT_DEBIT    | STRESS      |      1000000.0000 |    4599024.7700 |    10.9124 |                   -47.8142 |                           -33.1126 |                          -12.0106 |        36 |      36 |                                 0 |
| CORE_PLUS_CALL_CREDIT  | STRESS      |      1000000.0000 |    4461882.6700 |    10.6848 |                   -35.4839 |                           -33.1057 |                          -10.7253 |       290 |     289 |                                 9 |
| CORE_PLUS_CALL_AND_PUT | STRESS      |      1000000.0000 |    4102244.8700 |    10.0552 |                   -48.8238 |                           -37.8104 |                          -14.4640 |       325 |     324 |                                 9 |

## Interpretation limits

- MaxDD and annual results are observed-mark metrics. Missing held-leg marks stay unknown, so the observed MaxDD may understate losses; no forward fill is used.
- The combined portfolio adds the two sleeve budgets. It should not be declared superior based on raw CAGR alone.
- No VXX stock short, no VXX option leg and no QQQ 1:5 ratio is included in these candidate portfolios.
- The source option history ends on its last observed chain date; there is no QQQ option-chain evidence past that date.
- The four candidates are a prespecified screen, not independent trials or a claim that any candidate is deployable.
