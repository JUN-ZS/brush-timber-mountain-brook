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
- Fresh bid at exit; if unavailable within five days, use intrinsic value as a conservative fallback and count it.
- Commissions and taxes excluded; observed bid/ask spread is included when quoted.

## Entry quote coverage

         kind  entry_dates_tested  entry_dates_with_candidate  candidate_coverage_pct  median_selected_delta  median_selected_dte  median_otm_pct  median_entry_ask_per_share  median_entry_cost_per_contract_usd  median_spread_per_share  median_volume
  weekly_7dte                 741                         613               82.726046                0.04980                  8.0        0.038034                        0.10                                10.0                     0.01          175.0
annual_365dte                1723                        1075               62.391178                0.05055                353.0        0.296114                        0.68                                68.0                     0.18            0.0

## Ten-year results

        strategy  windows  mean_terminal_nav_usd  median_terminal_nav_usd  p10_terminal_nav_usd  p25_terminal_nav_usd  p75_terminal_nav_usd  p90_terminal_nav_usd  mean_profit_usd  median_profit_usd  positive_window_pct  ending_below_7000_pct  median_xirr_pct  mean_xirr_pct  p10_xirr_pct  p90_xirr_pct  any_contracts_bought_pct  all_contract_payouts_zero_pct_when_traded  near_total_loss_pct  median_contracts_bought  median_positions_closed  median_premium_paid_usd  median_exit_payout_usd  median_candidate_misses  observed_bid_exit_share_pct
   spot_buy_hold      239             39154.6205               37785.5319            33581.3091            35282.6941            41027.5005            49305.9872       32154.6205         30785.5319             100.0000                 0.0000          18.3637        18.6770       16.9804       21.5537                    0.0000                                        NaN               0.0000                   0.0000                   0.0000                   0.0000                  0.0000                   0.0000                       0.0000
  weekly_5d_call      239                25.6444                  16.0000                5.0000               11.0000               24.0000               40.2000       -6974.3556         -6984.0000               0.0000               100.0000         -99.9172       -97.2388      -99.9996      -87.9633                  100.0000                                     0.0000              95.3975                1774.0000                 372.0000               11122.0000               4172.0000                 131.0000                     100.0000
annual_365d_call      239             18657.1423                 120.0000               25.0000               60.0000             1812.5000            15691.2000       11657.1423         -6880.0000              13.3891                81.1715         -85.4317       -58.1508      -96.5905       14.2945                   94.5607                                    12.3894              28.0335                 279.0000                   7.0000               20991.0000              22635.0000                   3.0000                      96.9925

## How to read this

- Positive-window percentage means terminal account NAV exceeds the full $7,000 contribution budget.
- XIRR uses actual contribution dates and terminal NAV; this is more appropriate than a simple ten-year CAGR for staggered contributions.
- All-contract-payouts-zero is conditional on at least one contract having been bought.
- Near-total-loss means terminal account NAV is at or below $70 (1% of total contributions).
- The overlapping windows are not independent statistical trials.
- The fully invested spot benchmark and the ten-year contribution-funded Call strategies have different capital-at-risk timing.

## Provenance

- Workflow source commit: ed5e2c147846db143d2f2e8210cb3f665592ccde
- Hashes and exact coverage are in run_manifest.json.
- window_results.csv has each window; aggregate_summary.csv has summary statistics; candidate_coverage.csv has option availability.
