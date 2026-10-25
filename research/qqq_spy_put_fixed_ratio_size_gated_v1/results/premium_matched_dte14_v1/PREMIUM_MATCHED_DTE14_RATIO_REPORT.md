# Premium-matched DTE14 QQQ LONG PUT / SPY SHORT PUT — ratio comparison

Research-only full-history replay. Source quotes are historical EOD option-chain records, not verified fills. This is the premium-matched variant, not the prior Delta-0.25 QQQ long-put variant.

## Frozen setup

- Signal selects same-expiry DTE 7–21, nearest DTE 14. SPY short put is selected by absolute Delta nearest 0.25 within the established eligible band.
- QQQ long put is selected at the signal date with Ask closest to 6 × the selected SPY short put Bid. This keeps the same target QQQ long-put contract for both 1:3 and 1:6 arms; QQQ Delta is reported, not constrained to 0.25.
- Entry schedule every five common QQQ/SPY sessions; no market filter; overlapping cohorts enabled. Entries use QQQ Ask / SPY Bid with displayed-size gates.
- Primary comparison policy: HOLD_20_OR_DTE_LE_7 (exit at 20 common sessions or remaining calendar DTE <= 7, whichever happens first), with failed/missing exit quotes treated as deferred/unresolved.
- Base costs: USD 0.05 per option-share per side plus USD 0.65 per contract per side. Each entry cohort is one long QQQ put and fixed 3 or 6 SPY short puts.

## Results

| Metric | 1:3 | 1:6 |
|---|---:|---:|
| Selected signals | 392 | 392 |
| Entered cohorts | 392 | 392 |
| Resolved trades | 391 | 391 |
| Unresolved trades | 1 | 1 |
| Win rate among resolved | 47.06% | 66.50% |
| Win-rate Wilson 95% interval | 42.16–52.01% | 61.68–70.99% |
| Net expectancy / trade | USD -127.80 | USD -92.58 |
| Median net P&L / trade | USD -38.20 | USD 192.90 |
| Total net episode P&L | USD -49,971.20 | USD -36,197.10 |
| Worst resolved trade | USD -10,542.20 | USD -26,657.10 |
| Best resolved trade | USD 2,048.80 | USD 6,112.90 |
| Profit factor | 0.606419 | 0.825457 |
| Median QQQ put |Delta| | 0.838 | 0.838 |
| QQQ put |Delta| P10–P90 | 0.729–0.934 | 0.729–0.934 |
| Median premium match at entry | 44.62% | 82.33% |
| Median signal-date QQQ Ask minus 6x SPY Bid | USD 0.005/share | USD 0.005/share |

## Interpretation limits

- Total P&L sums overlapping trade episodes; it is not a compounded account NAV return.
- Win rate uses resolved episodes only; opened, resolved, and unresolved counts must be read together.
- The replay uses one fixed-anchor schedule (phase 0); it is in-sample and may be regime-dependent.
- Capital, broker-specific margin, assignment cash needs, forced liquidation, taxes, dividends, interest, and verified multi-leg fills are not modeled in this cohort report. The separate USD 100,000 NAV replay is capital-feasibility evidence for the original Delta-0.25 QQQ long-put selector, not this premium-matched selector.
- QQQ option selection matches the signal-date premium target; next-session entry quotes may shift the actual premium ratio. The entry CSV reports actual premium match and the original target/error.
- The underlying option-chain source ends in 2025. No 2026 performance is inferred.

## Artifacts

- ratio_1x3/summary.json, ratio_1x3/trade_episodes.csv, ratio_1x3/entry_cohort.csv
- ratio_1x6/summary.json, ratio_1x6/trade_episodes.csv, ratio_1x6/entry_cohort.csv
