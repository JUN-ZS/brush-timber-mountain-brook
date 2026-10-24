# DTE14 QQQ:SPY Put Ratios — $100,000 Single-Account NAV with FAR TAIL Collateral

Research-only historical replay. No broker orders. Five phase schedules overlap; report their medians/ranges, never add the phases together.

## Frozen strategy and collateral model

- DTE14 base selection and fixed exit policy: HOLD_20_OR_DTE_LE_7, inherited from the source-pinned QQQ long PUT / SPY short PUT replay.
- Start NAV is exactly $100,000 for every phase. Each account replays a fixed QQQ long PUT 1 contract and SPY short PUT quantity of 3 or 6; lot size is not automatically scaled with NAV.
- FAR TAIL is the source-pinned same-entry-date, same-expiry SPY TAIL_10_DELTA long PUT. It is purchased at the ask at the same entry event, not assumed to appear later as collateral.
- Comparisons: 1:3 with 0 or 3 tails; 1:6 with 0, 3 or 6 tails. The full-coverage variants pair each SPY short PUT with one lower-strike same-expiry SPY long PUT. The 1:6 / 3-tail variant leaves three SPY shorts uncovered.
- Reserve proxy = (short strike − tail strike) × 100 × paired spreads + short strike × 100 × uncovered short puts. Tail strikes must be strictly below the SPY short strike. Reserve is a conservative defined-risk collateral proxy, not a broker margin quote.
- A QQQ long PUT does not collateralize SPY short PUTs. Only same-underlying, same-expiry, lower-strike SPY puts count as vertical-spread coverage. One tail contract only covers one short put; unmatched shorts retain full strike-notional reserve.
- Entry and exit use exact contract Bid/Ask sides and displayed-size gates. Costs are $0.05 per option-share per side plus $0.65 per contract per side. Daily EOD quotes are not verified fills.
- If any leg of the vertical package cannot pass the exit quote/size gate on the scheduled exit day, none of the package legs is separately closed. Remaining positions are marked to intrinsic at expiry when underlying closes are available; this is an assignment/liquidation proxy.

## Account-level results (median across five phase accounts)

| Ratio | SPY short qty | FAR TAIL qty | Median end NAV | Median cumulative profit | Total return | CAGR | Observed MaxDD | Peak reserve | Median entries opened | Median capital rejections | NAV coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1:3 | 3 | 0 | $90,047 | $-9,953 | -9.95% | -1.34% | 16.13% | $93,900 | 80.0 | 312.0 | 99.85% |
| 1:3 | 3 | 3 | $59,014 | $-40,986 | -40.99% | -6.55% | 41.00% | $23,700 | 380.0 | 0.0 | 99.69% |
| 1:6 | 6 | 0 | $100,000 | $0 | 0.00% | 0.00% | 0.00% | $0 | 0.0 | 386.0 | 100.00% |
| 1:6 | 6 | 3 | $91,458 | $-8,542 | -8.54% | -1.14% | 19.22% | $96,900 | 53.0 | 328.0 | 99.90% |
| 1:6 | 6 | 6 | $50,077 | $-49,923 | -49.92% | -9.00% | 68.65% | $51,600 | 371.0 | 0.0 | 99.64% |

## Calendar-year account profit

A full calendar-year result is only reported when a complete year-end NAV mark exists. 2018 begins at account inception; 2025 ends at 2025-12-12. Previous incomplete year-end marks are not forward-filled.

| Ratio | Tail qty | Year | Period | Median account P&L | Min–max across phases | Median return | Valid phases |
|---|---:|---:|---|---:|---:|---:|---:|
| 1:3 | 0 | 2018 | PARTIAL_FROM_INCEPTION | $-9,041 | $-9,692 to $-6,018 | -9.04% | 5/5 |
| 1:3 | 0 | 2019 | CALENDAR_YEAR | $89 | $-654 to $4,157 | 0.10% | 5/5 |
| 1:3 | 0 | 2020 | CALENDAR_YEAR | $-4,944 | $-13,626 to $1,820 | -5.20% | 5/5 |
| 1:3 | 0 | 2021 | CALENDAR_YEAR | $0 | $0 to $0 | 0.00% | 5/5 |
| 1:3 | 0 | 2022 | CALENDAR_YEAR | $0 | $0 to $0 | 0.00% | 5/5 |
| 1:3 | 0 | 2023 | CALENDAR_YEAR | $0 | $0 to $0 | 0.00% | 5/5 |
| 1:3 | 0 | 2024 | CALENDAR_YEAR | $0 | $0 to $0 | 0.00% | 5/5 |
| 1:3 | 0 | 2025 | PARTIAL_TO_DATA_END_2025-12-12 | $0 | $0 to $0 | 0.00% | 5/5 |
| 1:3 | 3 | 2018 | PARTIAL_FROM_INCEPTION | $-7,979 | $-8,529 to $-7,716 | -7.98% | 5/5 |
| 1:3 | 3 | 2019 | CALENDAR_YEAR | $-2,414 | $-4,276 to $-1,081 | -2.62% | 5/5 |
| 1:3 | 3 | 2020 | CALENDAR_YEAR | $-9,189 | $-16,865 to $-3,543 | -10.48% | 5/5 |
| 1:3 | 3 | 2021 | CALENDAR_YEAR | $-752 | $-1,589 to $629 | -0.96% | 5/5 |
| 1:3 | 3 | 2022 | CALENDAR_YEAR | $-7,970 | $-9,297 to $-5,693 | -10.25% | 5/5 |
| 1:3 | 3 | 2023 | CALENDAR_YEAR | $-3,649 | $-6,508 to $-2,981 | -5.21% | 5/5 |
| 1:3 | 3 | 2024 | CALENDAR_YEAR | $-3,881 | $-7,343 to $-2,365 | -5.48% | 5/5 |
| 1:3 | 3 | 2025 | PARTIAL_TO_DATA_END_2025-12-12 | $-1,460 | $-8,113 to $1,201 | -2.14% | 5/5 |
| 1:6 | 0 | 2018 | PARTIAL_FROM_INCEPTION | $0 | $0 to $0 | 0.00% | 5/5 |
| 1:6 | 0 | 2019 | CALENDAR_YEAR | $0 | $0 to $0 | 0.00% | 5/5 |
| 1:6 | 0 | 2020 | CALENDAR_YEAR | $0 | $0 to $0 | 0.00% | 5/5 |
| 1:6 | 0 | 2021 | CALENDAR_YEAR | $0 | $0 to $0 | 0.00% | 5/5 |
| 1:6 | 0 | 2022 | CALENDAR_YEAR | $0 | $0 to $0 | 0.00% | 5/5 |
| 1:6 | 0 | 2023 | CALENDAR_YEAR | $0 | $0 to $0 | 0.00% | 5/5 |
| 1:6 | 0 | 2024 | CALENDAR_YEAR | $0 | $0 to $0 | 0.00% | 5/5 |
| 1:6 | 0 | 2025 | PARTIAL_TO_DATA_END_2025-12-12 | $0 | $0 to $0 | 0.00% | 5/5 |
| 1:6 | 3 | 2018 | PARTIAL_FROM_INCEPTION | $-16,418 | $-18,411 to $-6,298 | -16.42% | 5/5 |
| 1:6 | 3 | 2019 | CALENDAR_YEAR | $1,502 | $1,285 to $2,400 | 1.83% | 5/5 |
| 1:6 | 3 | 2020 | CALENDAR_YEAR | $5,416 | $-3,555 to $15,526 | 6.48% | 5/5 |
| 1:6 | 3 | 2021 | CALENDAR_YEAR | $0 | $0 to $0 | 0.00% | 5/5 |
| 1:6 | 3 | 2022 | CALENDAR_YEAR | $0 | $0 to $0 | 0.00% | 5/5 |
| 1:6 | 3 | 2023 | CALENDAR_YEAR | $0 | $0 to $0 | 0.00% | 5/5 |
| 1:6 | 3 | 2024 | CALENDAR_YEAR | $0 | $0 to $0 | 0.00% | 5/5 |
| 1:6 | 3 | 2025 | PARTIAL_TO_DATA_END_2025-12-12 | $0 | $0 to $0 | 0.00% | 5/5 |
| 1:6 | 6 | 2018 | PARTIAL_FROM_INCEPTION | $-17,180 | $-18,552 to $-16,284 | -17.18% | 5/5 |
| 1:6 | 6 | 2019 | CALENDAR_YEAR | $-3,116 | $-4,904 to $-1,377 | -3.72% | 5/5 |
| 1:6 | 6 | 2020 | CALENDAR_YEAR | $-17,813 | $-32,181 to $9,031 | -22.86% | 5/5 |
| 1:6 | 6 | 2021 | CALENDAR_YEAR | $4,804 | $3,142 to $8,413 | 8.43% | 5/5 |
| 1:6 | 6 | 2022 | CALENDAR_YEAR | $-18,640 | $-19,195 to $-10,505 | -29.45% | 5/5 |
| 1:6 | 6 | 2023 | CALENDAR_YEAR | $-2,462 | $-9,160 to $-464 | -4.02% | 5/5 |
| 1:6 | 6 | 2024 | CALENDAR_YEAR | $-6,008 | $-11,674 to $-300 | -8.02% | 5/5 |
| 1:6 | 6 | 2025 | PARTIAL_TO_DATA_END_2025-12-12 | $1,399 | $-2,323 to $2,984 | 3.15% | 4/5 |

## Interpretation and limitations

- The principal decision metric is median annual account profit on the single $100k NAV path, not total P&L summed over overlapping trade episodes.
- Tail PUT premiums reduce account NAV. Lower reserved collateral does not mean the hedge is free or the package is low-risk; compare premium drag with both worst trade and portfolio MaxDD.
- MaxDD is computed from available daily NAV marks; gaps with missing quotes can understate risk. EOD prices and displayed sizes do not establish real fills.
- A vertical-spread reserve calculated from strike width is not an exact broker initial/maintenance margin calculation. Actual brokers can add house requirements, fees, assignment/exercise cash needs, and liquidity buffers.
- No margin borrowing, interest, taxes, dividends, early assignment fees, forced-liquidation engine, or verified fills is modeled. Source option chains end on 2025-12-12.
- Five phase schedules overlap and are not independent samples or confidence intervals. No phases are pooled or summed.

Supporting outputs: account_phase_summary.csv, account_summary_by_config.csv, account_annual_returns.csv, account_annual_median.csv, account_nav_daily.csv, capital_gates.csv, trade_results.csv and account_manifest.json.