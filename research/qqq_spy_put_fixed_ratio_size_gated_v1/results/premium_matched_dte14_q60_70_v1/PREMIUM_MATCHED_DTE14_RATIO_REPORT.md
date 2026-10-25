# Premium-matched DTE14 QQQ LONG PUT / SPY SHORT PUT — ratio comparison

Research-only full-history replay. Source quotes are historical EOD option-chain records, not verified fills. This is the premium-matched variant, not the prior Delta-0.25 QQQ long-put variant.

## Frozen setup

- Signal selects same-expiry DTE 7–21, nearest DTE 14. SPY short put is selected by absolute Delta nearest 0.25 within the established eligible band.
- QQQ long put is constrained to absolute Delta 0.60–0.70 (target 0.65). Within that band, choose the same-expiry contract whose Ask is closest to 6 × SPY short-put Bid. If no in-band QQQ put exists, skip that signal instead of falling back to a different Delta solely to force the premium match.
- Entry schedule every five common QQQ/SPY sessions; no market filter; overlapping cohorts enabled. Entries use QQQ Ask / SPY Bid with displayed-size gates.
- Primary comparison policy: HOLD_20_OR_DTE_LE_7 (exit at 20 common sessions or remaining calendar DTE <= 7, whichever happens first), with failed/missing exit quotes treated as deferred/unresolved.
- Base costs: USD 0.05 per option-share per side plus USD 0.65 per contract per side. Each entry cohort is one long QQQ put and fixed 3 or 6 SPY short puts.

## Results

| Metric | 1:3 | 1:6 |
|---|---:|---:|
| Selected signals | 392 | 392 |
| Scheduled opportunities skipped by selector/data gate | 0 | 0 |
| Entered cohorts | 392 | 392 |
| Resolved trades | 391 | 391 |
| Unresolved trades | 1 | 1 |
| Win rate among resolved | 49.10% | 75.45% |
| Win-rate Wilson 95% interval | 44.18–54.04% | 70.95–79.45% |
| Net expectancy / trade | USD -85.59 | USD -42.89 |
| Median net P&L / trade | USD -10.20 | USD 286.90 |
| Total net episode P&L | USD -33,466.20 | USD -16,768.10 |
| Worst resolved trade | USD -10,629.20 | USD -26,768.10 |
| Best resolved trade | USD 1,830.80 | USD 6,575.90 |
| Profit factor | 0.662407 | 0.915666 |
| Median QQQ put |Delta| | 0.685 | 0.685 |
| QQQ put |Delta| P10–P90 | 0.654–0.696 | 0.654–0.696 |
| Median premium match at entry | 70.86% | 69.13% |
| Median signal-date QQQ Ask minus 6x SPY Bid | USD -4.255/share | USD -4.255/share |

## QQQ LONG PUT intrinsic value vs extrinsic-residual path

These use daily historical QQQ EOD quote sides and underlying closes for resolved HOLD_20_OR_DTE_LE_7 episodes. Both ratio arms use the same QQQ contract selection; displayed quotes do not imply verified fills.

| QQQ-leg diagnostic | 1:3 arm | 1:6 arm |
|---|---:|---:|
| Resolved QQQ-leg paths | 391 | 391 |
| QQQ PUT observed ITM at least once | 365/391 (93.35%) | 365/391 (93.35%) |
| Median extrinsic bid-residual at first ITM ($/share) | USD 1.390/share | USD 1.380/share |
| Median intrinsic-value contribution to QQQ P&L | USD -99.00 | USD -100.00 |
| Median entry-Ask to exit-Bid extrinsic-residual change | USD -131.00 | USD -131.00 |
| Resolved trades with lower extrinsic residual at exit | 87.47% | 87.21% |

Extrinsic residual = option quote minus intrinsic value. It is NOT pure Theta: changes combine time decay, IV/skew repricing, bid/ask effects and other quote changes. Intrinsic and extrinsic-residual changes add to quoted QQQ long-put P&L before costs when endpoints are present.


## Interpretation limits

- Total P&L sums overlapping trade episodes; it is not a compounded account NAV return.
- Win rate uses resolved episodes only; opened, resolved, and unresolved counts must be read together.
- The replay uses one fixed-anchor schedule (phase 0); it is in-sample and may be regime-dependent.
- Capital, broker-specific margin, assignment cash needs, forced liquidation, taxes, dividends, interest, and verified multi-leg fills are not modeled in this cohort report. The separate USD 100,000 NAV replay is capital-feasibility evidence for the original Delta-0.25 QQQ long-put selector, not this premium-matched selector.
- QQQ selection is constrained to |Delta| 0.60–0.70, then matched to 6× SPY Bid at signal date. Next-session quotes can shift actual premium ratio; the entry CSV reports the mismatch.
- QQQ intrinsic/extrinsic decomposition uses quote endpoints. Extrinsic residual is not pure Theta because IV, skew and bid/ask spreads also affect it.
- The underlying option-chain source ends in 2025. No 2026 performance is inferred.

## Artifacts

- ratio_1x3/summary.json, ratio_1x3/trade_episodes.csv, ratio_1x3/entry_cohort.csv
- ratio_1x6/summary.json, ratio_1x6/trade_episodes.csv, ratio_1x6/entry_cohort.csv
