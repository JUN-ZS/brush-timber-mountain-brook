# QQQ USD 7,000 Spot vs Budgeted Long Calls — Ten-Year Historical Study

- Status: OBSERVED_HISTORICAL_OPTION_BID_ASK_REPLAY
- Common sample: 2011-03-23 to 2025-12-15
- Complete overlapping ten-year windows: 239
- Options data SHA-256: 1f831556cd87ec9d7af43d3b47a69a829ffb2fb199cfcef4ff55d289badf8734
- Underlying data SHA-256: 78c015fd7fa9d493cd798d5ae81b3c2ae6dc3b8176e25e7bb90cd4114b103351
- Option pricing uses historical bid/ask quotes; no Black–Scholes option marks.

## Fixed rules

- QQQ spot: invest all $7,000 at the start and hold; adjusted close is used if available, otherwise price-only.
- Weekly Call: contribute $7,000 evenly over 5-session entries; target 5-delta OTM Call, 7 DTE (5–10 allowed), hold to expiration.
- Annual Call: contribute $700 at each of ten yearly entry dates; target 5-delta OTM Call, 365 DTE (330–400 allowed), hold to expiration.
- Whole contracts only; cash and proceeds are carried forward without interest.
- Expired Calls settle at intrinsic value using QQQ close on or immediately before expiration. Only Calls still open at the ten-year window end are marked to the latest bid within five days; if unavailable, use intrinsic value and count the fallback.
- Commissions and taxes excluded; observed entry ask includes the quoted spread.

## Entry quote coverage

         kind  entry_dates_tested  entry_dates_with_candidate  candidate_coverage_pct  median_selected_delta  median_selected_dte  median_otm_pct  median_entry_ask_per_share  median_entry_cost_per_contract_usd  median_spread_per_share  median_volume
  weekly_7dte                 741                         613               82.726046                0.04980                  8.0        0.038034                        0.10                                10.0                     0.01          175.0
annual_365dte                1723                        1075               62.391178                0.05055                353.0        0.296114                        0.68                                68.0                     0.18            0.0

## Ten-year results

        strategy  windows  mean_terminal_nav_usd  median_terminal_nav_usd  p10_terminal_nav_usd  p25_terminal_nav_usd  p75_terminal_nav_usd  p90_terminal_nav_usd  mean_profit_usd  median_profit_usd  positive_window_pct  ending_below_7000_pct  median_xirr_pct  mean_xirr_pct  p10_xirr_pct  p90_xirr_pct  any_contracts_bought_pct  all_expired_contracts_worthless_pct_when_traded  near_total_loss_pct  median_contracts_bought  median_contracts_expired  median_expired_worthless_contracts  median_expiry_intrinsic_settlements  median_positions_closed  median_premium_paid_usd  median_exit_payout_usd  median_candidate_misses  observed_bid_exit_share_pct
   spot_buy_hold      239             39154.6205               37785.5319            33581.3091            35282.6941            41027.5005            49305.9872       32154.6205         30785.5319             100.0000                 0.0000          18.3637        18.6770       16.9804       21.5537                    0.0000                                              NaN               0.0000                   0.0000                    0.0000                              0.0000                               0.0000                   0.0000                   0.0000                  0.0000                   0.0000                       0.0000
  weekly_5d_call      239                28.8954                  16.0000                5.0000               10.5000               23.0000               50.0000       -6971.1046         -6984.0000               0.0000               100.0000         -99.8513       -96.0051      -99.9995      -84.3545                  100.0000                                           0.0000              94.1423                1752.0000                 1751.0000                           1694.0000                             370.0000                 371.0000               11226.0000               4244.0000                 133.0000                     100.0000
annual_365d_call      239             18508.4268                 135.0000               27.6000               77.0000             2348.5000            15489.0000       11508.4268         -6865.0000              14.2259                80.3347         -84.0914       -57.2587      -96.3185       14.0687                   94.5607                                          19.4690              23.8494                 298.0000                  270.0000                            232.0000                               6.0000                   7.0000               22171.0000              23685.0000                   3.0000                      97.4359

## How to read this

- Positive-window percentage means terminal account NAV exceeds the full $7,000 contribution budget.
- XIRR uses actual contribution dates and terminal NAV; this is more appropriate than a simple ten-year CAGR for staggered contributions.
- All-expired-contracts-worthless is conditional on at least one contract purchase; it means every option contract that expired during the ten-year path had zero intrinsic settlement value. Calls still open at the window end are not counted as expired.
- Near-total-loss means terminal account NAV is at or below $70 (1% of total contributions); this is more relevant than whether every single Call expires worthless.
- The overlapping windows are not independent statistical trials.
- The fully invested spot benchmark and the ten-year contribution-funded Call strategies have different capital-at-risk timing.

## Provenance

- Workflow source commit: d921184a06bec51cd85b0b2b2a54417479c3fda3
- Hashes and exact coverage are in run_manifest.json.
- window_results.csv has each window; aggregate_summary.csv has summary statistics; candidate_coverage.csv has option availability.
