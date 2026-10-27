# QQQ ATM Weekly Calls vs Actual Three-Year Long Calls

- Pricing status: historical observed option bid/ask quotes only; no Black–Scholes imputation.
- Source sample: 2011-03-23 to 2025-12-15.
- Ten-year overlapping windows: 239; three-year overlapping windows: 591.
- Pinned option rows: 15,345,882; options-date range 2011-03-23 to 2025-12-15; latest expiration date in file 2028-01-21.

## Exact rules

- Weekly Call: $7,000 total contributions spread evenly over every fifth trading session of each window. Pick the listed Call with DTE closest to 7 within 5–10 calendar days, then strike closest to QQQ spot (ATM); Delta is not an entry filter.
- Whole contracts only; buy at observed Ask. Unspent cash and proceeds are carried forward at 0% interest, so a weekly allocation too small to buy one contract accumulates rather than being spent at a fictional fractional-contract price.
- All weekly Calls are held to expiration; expired contracts settle at intrinsic value from the QQQ close on or before expiration. At a window's final date, a still-live option uses a fresh observed bid within five calendar days, otherwise intrinsic fallback.
- Three-year Call: spend up to $7,000 at the start of a three-year window on the ATM Call whose listed expiry is closest to 1,095 DTE within 900–1,200 DTE; buy at observed Ask and hold to the three-year window end/option expiration. It is only summarized for windows with an actual eligible listed contract. This is a single upfront premium budget, not a recurring contribution strategy.
- QQQ spot benchmark invests the full $7,000 at the start. The stock and option strategies therefore have different capital-at-risk timing; read them as distinct budget deployment methods.
- No commissions, taxes, or cash interest. Historical quotes and volume do not guarantee executable fills.

## Quote coverage

| kind                       |   entry_dates_tested |   entry_dates_with_candidate |   coverage_pct |   median_observed_abs_delta_not_used_for_selection |   median_selected_dte |   median_strike_vs_spot_pct |   median_entry_ask_per_share |   median_entry_cost_per_contract_usd |   median_spread_per_share |   median_volume |
|:---------------------------|---------------------:|-----------------------------:|---------------:|---------------------------------------------------:|----------------------:|----------------------------:|-----------------------------:|-------------------------------------:|--------------------------:|----------------:|
| weekly_atm_5_10dte         |                  741 |                          613 |        82.726  |                                            0.51383 |                     8 |                   0         |                         2.12 |                                  212 |                      0.04 |            2577 |
| three_year_atm_900_1200dte |                  591 |                           73 |        12.3519 |                                            0.58288 |                   990 |                  -0.0440982 |                        35.1  |                                 3510 |                      3.94 |               2 |

## Ten-year results

| strategy              |   windows |   mean_terminal_nav_usd |   median_terminal_nav_usd |   median_profit_usd |   positive_window_pct |   ending_below_7000_pct |   near_total_loss_pct |   median_premium_paid_usd |   median_contracts_bought |
|:----------------------|----------:|------------------------:|--------------------------:|--------------------:|----------------------:|------------------------:|----------------------:|--------------------------:|--------------------------:|
| qqq_spot_buy_hold_10y |       239 |               39154.6   |                   37785.5 |             30785.5 |             100       |                  0      |               0       |                         0 |                         0 |
| weekly_atm_call_10y   |       239 |                 402.335 |                     254   |             -6746   |               0.41841 |                 99.5816 |               4.60251 |                     45199 |                       368 |

## Three-year results

| strategy                      |   windows |   mean_terminal_nav_usd |   median_terminal_nav_usd |   p10_terminal_nav_usd |   p90_terminal_nav_usd |   mean_profit_usd |   median_profit_usd |   positive_window_pct |   ending_below_7000_pct |   near_total_loss_pct |   median_contracts_bought |   median_premium_paid_usd |   median_candidate_or_cash_misses |
|:------------------------------|----------:|------------------------:|--------------------------:|-----------------------:|-----------------------:|------------------:|--------------------:|----------------------:|------------------------:|----------------------:|--------------------------:|--------------------------:|----------------------------------:|
| qqq_spot_buy_hold_3y          |       591 |               11750.7   |                   11467.8 |                9544.92 |                14191.9 |           4750.68 |             4467.77 |             100       |                 0       |               0       |                         0 |                         0 |                                 0 |
| weekly_atm_call_3y            |       591 |                 750.302 |                     280   |                  77    |                 1210   |          -6249.7  |            -6720    |               1.18443 |                98.8156  |               8.79865 |                       394 |                     42349 |                                82 |
| three_year_atm_call_if_quoted |        73 |               15784.1   |                   10834   |                8048.4  |                28175   |           8784.05 |             3834    |              97.2603  |                 2.73973 |               0       |                         1 |                      6000 |                               nan |

**Coverage warning:** Actual three-year Call quotes are only available on a subset of sampled entry dates. The three-year-call summary is conditioned on windows with a real eligible quote and is not directly comparable to the full-window spot/weekly results.

## Interpretation limits

- Overlapping windows are highly correlated, not independent trials.
- ATM means closest listed strike to spot on the selected expiry; it does not mean an exact 0.50 Delta. Selected Delta is reported only as an observed diagnostic.
- The three-year Call results, when available, are conditional on observed listed quotes and should not be generalized to dates with no eligible contract.
