# SPY far-tail hedge: single-account NAV replay V1

Research only; no broker, no live orders. Phases are independent account simulations and are not summed.

## Rules and account accounting

- Fixed base lot: QQQ long PUT 1 : SPY short PUT 3, original HOLD_20_OR_DTE_LE_7 entry/exit schedule.
- Comparison: no tail hedge versus the frozen OR trigger buying the same-expiry SPY 10-delta tail PUT next session, 1 or 3 contracts; hold to original base exit.
- Starting NAV cases: $100k, $250k, $500k and $1m. Fixed lot size; NAV returns compound, but contract quantity is not increased as NAV grows.
- SPY short-put collateral reserves strike × 100 × contracts for every open position. No borrowing or QQQ/SPY margin netting. New base entries and hedge buys are skipped if post-debit cash cannot retain the collateral reserve.
- Entry/exit cash uses historical Ask/Bid sides and includes $0.05 per option-share per side plus $0.65 per contract per side. NAV marks longs at Bid and shorts at Ask, with estimated close costs.
- No forward fill. A missing quote for any live leg makes that day's NAV missing. Quotes are daily EOD proxies, not guaranteed fills.

## Source controls

- Base source-ledger rows: 3907; conditional trigger rows: 7814.
- SHA-pinned chain and underlying files: 18; chain dates 2018-03-02 to 2025-12-12.
- Source ledger hashes reconciled: True; resolved-trade P&L mismatches: 0.
- Simulated accounts: 120; selected daily NAV rows: 47016.

## Results: median across five phase accounts

These medians describe five separate schedules, not pooled account profit. Range values are shown in the CSV output.

| Arm | Start NAV | Tail qty | Median end NAV | Median total return | Median CAGR | Median observed MaxDD | End NAVs available | Median base trades skipped | Median hedge buys skipped | NAV coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DTE14 | $100,000 | 0 | $88,823 | -11.18% | -1.53% | 15.65% | 4/5 | $328 | $0 | 99.85% |
| DTE14 | $100,000 | 1 | $86,007 | -13.99% | -1.92% | 9.02% | 1/5 | $325 | $0 | 13.50% |
| DTE14 | $100,000 | 3 | — | — | — | 7.69% | 0/5 | $324 | $0 | 10.62% |
| DTE14 | $250,000 | 0 | $247,441 | -1.02% | -0.13% | 10.34% | 1/5 | $91 | $0 | 27.26% |
| DTE14 | $250,000 | 1 | — | — | — | 4.75% | 0/5 | $95 | $0 | 13.50% |
| DTE14 | $250,000 | 3 | — | — | — | 3.35% | 0/5 | $95 | $0 | 10.62% |
| DTE14 | $500,000 | 0 | $496,065 | -0.79% | -0.10% | 5.17% | 1/5 | $0 | $0 | 27.26% |
| DTE14 | $500,000 | 1 | — | — | — | 2.37% | 0/5 | $0 | $0 | 13.50% |
| DTE14 | $500,000 | 3 | — | — | — | 1.68% | 0/5 | $0 | $0 | 10.62% |
| DTE14 | $1,000,000 | 0 | $996,065 | -0.39% | -0.05% | 2.59% | 1/5 | $0 | $0 | 27.26% |
| DTE14 | $1,000,000 | 1 | — | — | — | 1.19% | 0/5 | $0 | $0 | 13.50% |
| DTE14 | $1,000,000 | 3 | — | — | — | 0.84% | 0/5 | $0 | $0 | 10.62% |
| DTE45 | $100,000 | 0 | $103,964 | 3.96% | 0.50% | 14.68% | 5/5 | $361 | $0 | 99.85% |
| DTE45 | $100,000 | 1 | $102,471 | 2.47% | 0.31% | 13.18% | 3/5 | $361 | $0 | 99.85% |
| DTE45 | $100,000 | 3 | $99,578 | -0.42% | -0.05% | 7.78% | 3/5 | $362 | $0 | 99.85% |
| DTE45 | $250,000 | 0 | $290,818 | 16.33% | 1.97% | 6.25% | 1/5 | $280 | $0 | 11.92% |
| DTE45 | $250,000 | 1 | $283,845 | 13.54% | 1.65% | 5.84% | 1/5 | $280 | $0 | 11.75% |
| DTE45 | $250,000 | 3 | $263,156 | 5.26% | 0.66% | 5.03% | 1/5 | $287 | $0 | 11.75% |
| DTE45 | $500,000 | 0 | $544,370 | 8.87% | 1.10% | 6.15% | 1/5 | $137 | $0 | 11.92% |
| DTE45 | $500,000 | 1 | — | — | — | 5.65% | 0/5 | $137 | $0 | 11.75% |
| DTE45 | $500,000 | 3 | — | — | — | 4.86% | 0/5 | $127 | $0 | 11.75% |
| DTE45 | $1,000,000 | 0 | $1,071,795 | 7.18% | 0.90% | 3.10% | 1/5 | $13 | $0 | 11.92% |
| DTE45 | $1,000,000 | 1 | — | — | — | 2.84% | 0/5 | $16 | $0 | 11.75% |
| DTE45 | $1,000,000 | 3 | — | — | — | 2.45% | 0/5 | $18 | $0 | 11.75% |

## Yearly account returns: DTE45 medians

2018 is partial from account inception. 2025 ends at 2025-12-12. A missing year-end mark is not forward-filled, so the next annual return may also be unavailable.

| Start NAV | Tail qty | Year | Period | Median P&L | Median account return | Valid phase returns |
|---:|---:|---:|---|---:|---:|---:|
| $250,000 | 0 | 2018 | PARTIAL_FROM_INCEPTION | $-3,443 | -1.38% | 5/5 |
| $250,000 | 0 | 2019 | CALENDAR_YEAR | $7,888 | 3.20% | 2/5 |
| $250,000 | 0 | 2020 | PREVIOUS_ENDPOINT_UNAVAILABLE | $9,316 | 3.65% | 2/5 |
| $250,000 | 0 | 2021 | PREVIOUS_ENDPOINT_UNAVAILABLE | $13,788 | 5.22% | 2/5 |
| $250,000 | 0 | 2022 | PREVIOUS_ENDPOINT_UNAVAILABLE | $-4,370 | -1.58% | 2/5 |
| $250,000 | 0 | 2023 | PREVIOUS_ENDPOINT_UNAVAILABLE | $6,654 | 2.43% | 2/5 |
| $250,000 | 0 | 2024 | PREVIOUS_ENDPOINT_UNAVAILABLE | $4,956 | 1.81% | 1/5 |
| $250,000 | 0 | 2025 | PARTIAL_TO_DATA_END_2025-12-12 | $11,444 | 4.10% | 1/5 |
| $250,000 | 1 | 2018 | PARTIAL_FROM_INCEPTION | $-5,692 | -2.28% | 4/5 |
| $250,000 | 1 | 2019 | CALENDAR_YEAR | $8,632 | 3.53% | 1/5 |
| $250,000 | 1 | 2020 | PREVIOUS_ENDPOINT_UNAVAILABLE | $4,030 | 1.59% | 1/5 |
| $250,000 | 1 | 2021 | PREVIOUS_ENDPOINT_UNAVAILABLE | $13,232 | 5.15% | 1/5 |
| $250,000 | 1 | 2022 | PREVIOUS_ENDPOINT_UNAVAILABLE | $-5,612 | -2.08% | 1/5 |
| $250,000 | 1 | 2023 | PREVIOUS_ENDPOINT_UNAVAILABLE | $5,093 | 1.92% | 1/5 |
| $250,000 | 1 | 2024 | PREVIOUS_ENDPOINT_UNAVAILABLE | $4,248 | 1.58% | 1/5 |
| $250,000 | 1 | 2025 | PARTIAL_TO_DATA_END_2025-12-12 | $9,915 | 3.62% | 1/5 |
| $250,000 | 3 | 2018 | PARTIAL_FROM_INCEPTION | $-7,326 | -2.93% | 4/5 |
| $250,000 | 3 | 2019 | CALENDAR_YEAR | $9,165 | 3.77% | 1/5 |
| $250,000 | 3 | 2020 | PREVIOUS_ENDPOINT_UNAVAILABLE | $-2,350 | -0.93% | 1/5 |
| $250,000 | 3 | 2021 | PREVIOUS_ENDPOINT_UNAVAILABLE | $12,065 | 4.83% | 1/5 |
| $250,000 | 3 | 2022 | PREVIOUS_ENDPOINT_UNAVAILABLE | $-1,875 | -0.72% | 1/5 |
| $250,000 | 3 | 2023 | PREVIOUS_ENDPOINT_UNAVAILABLE | $1,837 | 0.71% | 1/5 |
| $250,000 | 3 | 2024 | PREVIOUS_ENDPOINT_UNAVAILABLE | $1,526 | 0.58% | 1/5 |
| $250,000 | 3 | 2025 | PARTIAL_TO_DATA_END_2025-12-12 | $-400 | -0.15% | 1/5 |
| $1,000,000 | 0 | 2018 | PARTIAL_FROM_INCEPTION | $-9,274 | -0.93% | 5/5 |
| $1,000,000 | 0 | 2019 | CALENDAR_YEAR | $17,585 | 1.77% | 2/5 |
| $1,000,000 | 0 | 2020 | PREVIOUS_ENDPOINT_UNAVAILABLE | $-17,015 | -1.69% | 2/5 |
| $1,000,000 | 0 | 2021 | PREVIOUS_ENDPOINT_UNAVAILABLE | $34,284 | 3.46% | 2/5 |
| $1,000,000 | 0 | 2022 | PREVIOUS_ENDPOINT_UNAVAILABLE | $-3,809 | -0.37% | 2/5 |
| $1,000,000 | 0 | 2023 | PREVIOUS_ENDPOINT_UNAVAILABLE | $16,392 | 1.60% | 2/5 |
| $1,000,000 | 0 | 2024 | PREVIOUS_ENDPOINT_UNAVAILABLE | $21,299 | 2.07% | 1/5 |
| $1,000,000 | 0 | 2025 | PARTIAL_TO_DATA_END_2025-12-12 | $19,478 | 1.85% | 1/5 |
| $1,000,000 | 1 | 2018 | PARTIAL_FROM_INCEPTION | $-10,932 | -1.09% | 4/5 |
| $1,000,000 | 1 | 2019 | CALENDAR_YEAR | — | — | 0/5 |
| $1,000,000 | 1 | 2020 | PREVIOUS_ENDPOINT_UNAVAILABLE | — | — | 0/5 |
| $1,000,000 | 1 | 2021 | PREVIOUS_ENDPOINT_UNAVAILABLE | — | — | 0/5 |
| $1,000,000 | 1 | 2022 | PREVIOUS_ENDPOINT_UNAVAILABLE | — | — | 0/5 |
| $1,000,000 | 1 | 2023 | PREVIOUS_ENDPOINT_UNAVAILABLE | — | — | 0/5 |
| $1,000,000 | 1 | 2024 | PREVIOUS_ENDPOINT_UNAVAILABLE | — | — | 0/5 |
| $1,000,000 | 1 | 2025 | PARTIAL_TO_DATA_END_2025-12-12 | — | — | 0/5 |
| $1,000,000 | 3 | 2018 | PARTIAL_FROM_INCEPTION | $-14,207 | -1.42% | 4/5 |
| $1,000,000 | 3 | 2019 | CALENDAR_YEAR | — | — | 0/5 |
| $1,000,000 | 3 | 2020 | PREVIOUS_ENDPOINT_UNAVAILABLE | — | — | 0/5 |
| $1,000,000 | 3 | 2021 | PREVIOUS_ENDPOINT_UNAVAILABLE | — | — | 0/5 |
| $1,000,000 | 3 | 2022 | PREVIOUS_ENDPOINT_UNAVAILABLE | — | — | 0/5 |
| $1,000,000 | 3 | 2023 | PREVIOUS_ENDPOINT_UNAVAILABLE | — | — | 0/5 |
| $1,000,000 | 3 | 2024 | PREVIOUS_ENDPOINT_UNAVAILABLE | — | — | 0/5 |
| $1,000,000 | 3 | 2025 | PARTIAL_TO_DATA_END_2025-12-12 | — | — | 0/5 |

## Limits

- CAGR uses starting account capital and the exact data-end quoted NAV, never mean trade P&L.
- Observed MaxDD uses complete available daily marks and may understate troughs when quotes are missing.
- The full cash-collateral rule is intentionally conservative and does not represent any named broker's margin engine.
- No margin borrowing, interest, financing, assignment/early exercise, forced liquidation, taxes, dividends, or timestamp-verified execution.
- Failed scheduled exits remain open and unresolved; they are not silently filled with a later price.

See account_phase_summary.csv, account_summary_by_capital.csv, account_annual_returns.csv, account_annual_median_by_phase.csv, account_nav_selected.csv, capital_gates.csv and account_manifest.json.