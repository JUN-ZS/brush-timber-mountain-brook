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
| DTE14 | $100,000 | 0 | $90,047 | -9.95% | -1.34% | 16.13% | 5/5 | $312 | $0 | 99.85% |
| DTE14 | $100,000 | 1 | $89,998 | -10.00% | -1.35% | 16.01% | 5/5 | $312 | $0 | 99.85% |
| DTE14 | $100,000 | 3 | $89,975 | -10.02% | -1.35% | 15.70% | 5/5 | $314 | $0 | 99.85% |
| DTE14 | $250,000 | 0 | $244,530 | -2.19% | -0.28% | 10.34% | 5/5 | $13 | $0 | 99.64% |
| DTE14 | $250,000 | 1 | $240,240 | -3.90% | -0.51% | 10.52% | 5/5 | $13 | $0 | 99.59% |
| DTE14 | $250,000 | 3 | $236,285 | -5.49% | -0.72% | 11.50% | 4/5 | $13 | $0 | 99.59% |
| DTE14 | $500,000 | 0 | $494,639 | -1.07% | -0.14% | 5.17% | 5/5 | $0 | $0 | 99.64% |
| DTE14 | $500,000 | 1 | $490,256 | -1.95% | -0.25% | 5.26% | 5/5 | $0 | $0 | 99.59% |
| DTE14 | $500,000 | 3 | $486,804 | -2.64% | -0.34% | 5.76% | 4/5 | $0 | $0 | 99.59% |
| DTE14 | $1,000,000 | 0 | $994,639 | -0.54% | -0.07% | 2.59% | 5/5 | $0 | $0 | 99.64% |
| DTE14 | $1,000,000 | 1 | $990,256 | -0.97% | -0.13% | 2.63% | 5/5 | $0 | $0 | 99.59% |
| DTE14 | $1,000,000 | 3 | $986,804 | -1.32% | -0.17% | 2.88% | 4/5 | $0 | $0 | 99.59% |
| DTE45 | $100,000 | 0 | $103,964 | 3.96% | 0.50% | 14.68% | 5/5 | $361 | $0 | 99.85% |
| DTE45 | $100,000 | 1 | $102,693 | 2.69% | 0.34% | 13.18% | 5/5 | $361 | $0 | 99.85% |
| DTE45 | $100,000 | 3 | $102,170 | 2.17% | 0.28% | 8.95% | 5/5 | $362 | $0 | 99.85% |
| DTE45 | $250,000 | 0 | $290,818 | 16.33% | 1.97% | 11.94% | 5/5 | $238 | $0 | 99.44% |
| DTE45 | $250,000 | 1 | $283,845 | 13.54% | 1.65% | 10.82% | 5/5 | $238 | $0 | 98.98% |
| DTE45 | $250,000 | 3 | $263,156 | 5.26% | 0.66% | 9.88% | 5/5 | $242 | $1 | 99.18% |
| DTE45 | $500,000 | 0 | $550,816 | 10.16% | 1.25% | 15.92% | 5/5 | $81 | $0 | 99.23% |
| DTE45 | $500,000 | 1 | $541,417 | 8.28% | 1.03% | 13.65% | 5/5 | $81 | $0 | 98.93% |
| DTE45 | $500,000 | 3 | $518,716 | 3.74% | 0.47% | 9.28% | 5/5 | $84 | $1 | 98.93% |
| DTE45 | $1,000,000 | 0 | $1,073,067 | 7.31% | 0.91% | 8.05% | 5/5 | $0 | $0 | 98.98% |
| DTE45 | $1,000,000 | 1 | $1,058,517 | 5.85% | 0.73% | 6.88% | 5/5 | $0 | $0 | 98.93% |
| DTE45 | $1,000,000 | 3 | $1,027,801 | 2.78% | 0.35% | 4.67% | 5/5 | $0 | $0 | 98.93% |

## Yearly account returns: DTE45 medians

2018 is partial from account inception. 2025 ends at 2025-12-12. A missing year-end mark is not forward-filled, so the next annual return may also be unavailable.

| Start NAV | Tail qty | Year | Period | Median P&L | Median account return | Valid phase returns |
|---:|---:|---:|---|---:|---:|---:|
| $250,000 | 0 | 2018 | PARTIAL_FROM_INCEPTION | $-3,443 | -1.38% | 5/5 |
| $250,000 | 0 | 2019 | CALENDAR_YEAR | $8,529 | 3.46% | 5/5 |
| $250,000 | 0 | 2020 | CALENDAR_YEAR | $4,089 | 1.57% | 5/5 |
| $250,000 | 0 | 2021 | CALENDAR_YEAR | $13,823 | 5.31% | 5/5 |
| $250,000 | 0 | 2022 | CALENDAR_YEAR | $-3,689 | -1.37% | 5/5 |
| $250,000 | 0 | 2023 | CALENDAR_YEAR | $6,780 | 2.53% | 5/5 |
| $250,000 | 0 | 2024 | CALENDAR_YEAR | $4,956 | 1.81% | 5/5 |
| $250,000 | 0 | 2025 | PARTIAL_TO_DATA_END_2025-12-12 | $5,641 | 2.11% | 5/5 |
| $250,000 | 1 | 2018 | PARTIAL_FROM_INCEPTION | $-5,691 | -2.28% | 5/5 |
| $250,000 | 1 | 2019 | CALENDAR_YEAR | $8,101 | 3.28% | 5/5 |
| $250,000 | 1 | 2020 | CALENDAR_YEAR | $4,470 | 1.72% | 5/5 |
| $250,000 | 1 | 2021 | CALENDAR_YEAR | $13,004 | 5.09% | 5/5 |
| $250,000 | 1 | 2022 | CALENDAR_YEAR | $-5,274 | -1.96% | 5/5 |
| $250,000 | 1 | 2023 | CALENDAR_YEAR | $5,684 | 2.06% | 5/5 |
| $250,000 | 1 | 2024 | CALENDAR_YEAR | $2,700 | 1.02% | 5/5 |
| $250,000 | 1 | 2025 | PARTIAL_TO_DATA_END_2025-12-12 | $6,430 | 2.27% | 5/5 |
| $250,000 | 3 | 2018 | PARTIAL_FROM_INCEPTION | $-6,813 | -2.73% | 5/5 |
| $250,000 | 3 | 2019 | CALENDAR_YEAR | $5,224 | 2.16% | 5/5 |
| $250,000 | 3 | 2020 | CALENDAR_YEAR | $895 | 0.36% | 5/5 |
| $250,000 | 3 | 2021 | CALENDAR_YEAR | $10,203 | 4.02% | 5/5 |
| $250,000 | 3 | 2022 | CALENDAR_YEAR | $-1,875 | -0.72% | 5/5 |
| $250,000 | 3 | 2023 | CALENDAR_YEAR | $4,094 | 1.63% | 5/5 |
| $250,000 | 3 | 2024 | CALENDAR_YEAR | $1,449 | 0.55% | 5/5 |
| $250,000 | 3 | 2025 | PARTIAL_TO_DATA_END_2025-12-12 | $963 | 0.38% | 5/5 |
| $1,000,000 | 0 | 2018 | PARTIAL_FROM_INCEPTION | $-9,274 | -0.93% | 5/5 |
| $1,000,000 | 0 | 2019 | CALENDAR_YEAR | $16,996 | 1.72% | 5/5 |
| $1,000,000 | 0 | 2020 | CALENDAR_YEAR | $-20,959 | -2.07% | 5/5 |
| $1,000,000 | 0 | 2021 | CALENDAR_YEAR | $34,329 | 3.48% | 5/5 |
| $1,000,000 | 0 | 2022 | CALENDAR_YEAR | $-6,350 | -0.62% | 5/5 |
| $1,000,000 | 0 | 2023 | CALENDAR_YEAR | $17,948 | 1.77% | 5/5 |
| $1,000,000 | 0 | 2024 | CALENDAR_YEAR | $21,299 | 2.06% | 5/5 |
| $1,000,000 | 0 | 2025 | PARTIAL_TO_DATA_END_2025-12-12 | $17,333 | 1.64% | 5/5 |
| $1,000,000 | 1 | 2018 | PARTIAL_FROM_INCEPTION | $-10,052 | -1.01% | 5/5 |
| $1,000,000 | 1 | 2019 | CALENDAR_YEAR | $14,931 | 1.51% | 5/5 |
| $1,000,000 | 1 | 2020 | CALENDAR_YEAR | $-15,602 | -1.55% | 5/5 |
| $1,000,000 | 1 | 2021 | CALENDAR_YEAR | $31,040 | 3.13% | 5/5 |
| $1,000,000 | 1 | 2022 | CALENDAR_YEAR | $-9,806 | -0.96% | 5/5 |
| $1,000,000 | 1 | 2023 | CALENDAR_YEAR | $15,330 | 1.51% | 5/5 |
| $1,000,000 | 1 | 2024 | CALENDAR_YEAR | $17,269 | 1.67% | 5/5 |
| $1,000,000 | 1 | 2025 | PARTIAL_TO_DATA_END_2025-12-12 | $13,713 | 1.31% | 5/5 |
| $1,000,000 | 3 | 2018 | PARTIAL_FROM_INCEPTION | $-13,710 | -1.37% | 5/5 |
| $1,000,000 | 3 | 2019 | CALENDAR_YEAR | $10,802 | 1.10% | 5/5 |
| $1,000,000 | 3 | 2020 | CALENDAR_YEAR | $-4,646 | -0.46% | 5/5 |
| $1,000,000 | 3 | 2021 | CALENDAR_YEAR | $24,640 | 2.48% | 5/5 |
| $1,000,000 | 3 | 2022 | CALENDAR_YEAR | $-16,001 | -1.58% | 5/5 |
| $1,000,000 | 3 | 2023 | CALENDAR_YEAR | $9,803 | 0.98% | 5/5 |
| $1,000,000 | 3 | 2024 | CALENDAR_YEAR | $13,439 | 1.33% | 5/5 |
| $1,000,000 | 3 | 2025 | PARTIAL_TO_DATA_END_2025-12-12 | $3,588 | 0.35% | 5/5 |

## Limits

- CAGR uses starting account capital and the exact data-end quoted NAV, never mean trade P&L.
- Observed MaxDD uses complete available daily marks and may understate troughs when quotes are missing.
- The full cash-collateral rule is intentionally conservative and does not represent any named broker's margin engine.
- An unresolved option with no executable exit by expiry is marked to intrinsic at the underlying close, approximating exercise plus immediate same-close stock liquidation. Physical assignment, assignment fees and post-assignment share exposure are not modeled.
- No margin borrowing, interest, financing, early exercise before expiry, forced liquidation, taxes, dividends, or timestamp-verified execution.
- Failed scheduled exits remain open and unresolved; they are not silently filled with a later price.

See account_phase_summary.csv, account_summary_by_capital.csv, account_annual_returns.csv, account_annual_median_by_phase.csv, account_nav_selected.csv, capital_gates.csv and account_manifest.json.