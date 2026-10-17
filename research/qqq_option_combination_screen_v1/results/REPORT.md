# QQQ + Options Combination Screen V1

**Status: research-only; no live sizing changes and no broker orders.**

## Prespecified candidates

- CORE_ONLY: buy-and-hold QQQ shares sized to 42% of initial NAV; the remaining cash stays uninvested.
- CORE_PLUS_PUT_DEBIT: the same core plus a 18–35 DTE QQQ put debit vertical (buy approximately 25-delta put, sell lower-strike approximately 10-delta put). Annualized gross premium budget: 2% of NAV, prorated by planned exposure days (entry DTE minus the 7-day roll threshold).
- CORE_PLUS_CALL_CREDIT: the same core plus a 18–35 DTE QQQ call credit vertical (sell approximately 16-delta call, buy higher-strike approximately 8-delta protective call). Budget: 0.8% of prior observed NAV in conservative vertical max loss.
- CORE_PLUS_CALL_AND_PUT: both option sleeves at their single-sleeve budgets. This has a larger combined nominal budget, so raw CAGR is not a matched-total-risk comparison.

Candidates are selected from the prior observed session and entered next session using the exact same contract IDs. Each package midpoint/entry/exit value must respect zero-to-width vertical payoff bounds. Invalid quotes are not replaced or interpolated. Existing positions are closed using exact held-contract side quotes when DTE reaches 7 calendar days or less; if a position survives expiry because no valid close quote was available, it is settled with the last observed QQQ close on or before expiry as an explicitly labelled intrinsic-payoff proxy plus two-leg commission, not as official exchange settlement.

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
| CORE_PLUS_PUT_DEBIT    | BASE        |        80000.0000 |     398713.6900 |    11.5192 |                   -30.3689 |                           -28.1480 |                           -9.0717 |       308 |     291 |                                16 |
| CORE_PLUS_CALL_CREDIT  | BASE        |        80000.0000 |     372105.6900 |    10.9976 |                   -33.8721 |                           -31.5595 |                          -10.4747 |       338 |     337 |                                15 |
| CORE_PLUS_CALL_AND_PUT | BASE        |        80000.0000 |     363836.4900 |    10.8284 |                   -34.2334 |                           -31.8348 |                          -11.0250 |       574 |     561 |                                20 |
| CORE_ONLY              | STRESS      |        80000.0000 |     414562.4900 |    11.8146 |                   -29.9179 |                           -27.7100 |                           -8.5555 |         0 |       0 |                                 0 |
| CORE_PLUS_PUT_DEBIT    | STRESS      |        80000.0000 |     396844.8900 |    11.4836 |                   -30.5773 |                           -28.2116 |                           -9.1744 |       294 |     280 |                                13 |
| CORE_PLUS_CALL_CREDIT  | STRESS      |        80000.0000 |     364120.0900 |    10.8343 |                   -34.7196 |                           -32.3421 |                          -10.4086 |       289 |     287 |                                10 |
| CORE_PLUS_CALL_AND_PUT | STRESS      |        80000.0000 |     354656.5900 |    10.6363 |                   -36.0614 |                           -33.6089 |                          -11.3474 |       476 |     460 |                                13 |
| CORE_ONLY              | BASE        |      1000000.0000 |    5182863.3700 |    11.8158 |                   -29.9195 |                           -27.7116 |                           -8.5564 |         0 |       0 |                                 0 |
| CORE_PLUS_PUT_DEBIT    | BASE        |      1000000.0000 |    4913577.3700 |    11.4116 |                   -31.0359 |                           -28.6912 |                           -9.0821 |       359 |     345 |                                15 |
| CORE_PLUS_CALL_CREDIT  | BASE        |      1000000.0000 |    4589446.3700 |    10.8967 |                   -34.2872 |                           -31.9756 |                          -10.6580 |       338 |     337 |                                15 |
| CORE_PLUS_CALL_AND_PUT | BASE        |      1000000.0000 |    4464454.1700 |    10.6891 |                   -35.7735 |                           -33.3731 |                          -11.2622 |       579 |     566 |                                17 |
| CORE_ONLY              | STRESS      |      1000000.0000 |    5182863.3700 |    11.8158 |                   -29.9195 |                           -27.7116 |                           -8.5564 |         0 |       0 |                                 0 |
| CORE_PLUS_PUT_DEBIT    | STRESS      |      1000000.0000 |    4854112.9700 |    11.3196 |                   -31.5892 |                           -29.2108 |                           -9.2627 |       359 |     345 |                                15 |
| CORE_PLUS_CALL_CREDIT  | STRESS      |      1000000.0000 |    4465688.2700 |    10.6912 |                   -35.4376 |                           -33.0616 |                          -10.7008 |       289 |     287 |                                10 |
| CORE_PLUS_CALL_AND_PUT | STRESS      |      1000000.0000 |    4343295.7700 |    10.4826 |                   -36.9895 |                           -34.5226 |                          -11.5882 |       497 |     482 |                                12 |

## Interpretation limits

- MaxDD and annual results are observed-mark metrics. Missing held-leg marks stay unknown, so the observed MaxDD may understate losses; no forward fill is used. Expiry intrinsic values use the last observed QQQ close on/before expiry only when the position could not be closed on valid quotes; this is a close-based proxy, not official settlement.
- The combined portfolio adds the two sleeve budgets. It should not be declared superior based on raw CAGR alone.
- No VXX stock short, no VXX option leg and no QQQ 1:5 ratio is included in these candidate portfolios.
- The source option history ends on its last observed chain date; there is no QQQ option-chain evidence past that date.
- The four candidates are a prespecified screen, not independent trials or a claim that any candidate is deployable.
