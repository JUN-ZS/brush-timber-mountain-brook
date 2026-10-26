# DTE × holding duration × exit guard factorial replay

- Period: 2018-03-01 to 2025-12-15 (7.792 calendar years).
- Cadence: every 10 common QQQ/SPY sessions; five predeclared phase anchors: 0, 2, 4, 6, 8.
- Fixed legs: QQQ LONG CALL 1 : SPY SHORT CALL 6; same expiry; nearest absolute Delta 0.25 on both legs.
- Costs: USD 0.05/share/side slippage + USD 0.65/contract/side commission; no entry filter.
- DTE target bands: DTE20: 14–26; DTE30: 24–36; DTE45: 39–51; DTE60: 54–66.
- Exit rules: max hold 5/10/15/20 sessions × no guard / remaining DTE ≤ 7 / remaining DTE ≤ 14. Guard exits use OR logic with maximum hold.
- 20 source-pinned replay runs (4 DTE targets × 5 phases); all 12 exit policies run on each selected entry stream, yielding 240 phase cells and 48 phase-aggregated settings.

## Main effects

Each factor level is the median annual resolved-trade P&L across the other settings and five phase anchors. Spread is max minus min of level medians; descriptive screening only, not causal or account return.

| Factor | Level | Median annual P&L across other settings | Factor level spread |
|---|---:|---:|---:|
| Opening DTE target | DTE20 | $-3,757 | $2,342 |
| Opening DTE target | DTE30 | $-5,635 | $2,342 |
| Opening DTE target | DTE45 | $-6,099 | $2,342 |
| Opening DTE target | DTE60 | $-4,588 | $2,342 |
| Max holding sessions | 5 sessions | $-3,907 | $1,840 |
| Max holding sessions | 10 sessions | $-5,374 | $1,840 |
| Max holding sessions | 15 sessions | $-5,746 | $1,840 |
| Max holding sessions | 20 sessions | $-5,684 | $1,840 |
| Early-exit DTE guard | No DTE guard | $-5,193 | $426 |
| Early-exit DTE guard | Remaining DTE ≤ 7 | $-5,191 | $426 |
| Early-exit DTE guard | Remaining DTE ≤ 14 | $-4,768 | $426 |

## Same exit: hold up to 20 sessions OR remaining DTE ≤ 7

| Opening DTE target (band) | Median annual P&L | Min–max by phase | Phases ≥ USD12k | Median win rate | Median worst trade |
|---:|---:|---:|---:|---:|---:|
| DTE20 (14–26) | $-5,191 | $-7,834–$-2,740 | 0/5 | 60.82% | $-7,777.10 |
| DTE30 (24–36) | $-7,145 | $-10,751–$-6,248 | 0/5 | 60.38% | $-10,567.10 |
| DTE45 (39–51) | $-8,027 | $-9,263–$-5,862 | 0/5 | 58.33% | $-11,242.10 |
| DTE60 (54–66) | $-4,902 | $-6,467–$-3,842 | 0/5 | 55.14% | $-8,416.10 |

## Same DTE target: DTE45 (band 39–51)

| Max hold | Guard | Median annual P&L | Min–max by phase | Phases ≥ USD12k | Median expectancy/trade | Median worst trade |
|---:|---|---:|---:|---:|---:|---:|
| 5 sessions | DTE≤7 | $-4,021 | $-6,393–$-2,717 | 0/5 | $-186.52 | $-4,167.10 |
| 5 sessions | DTE≤14 | $-4,021 | $-6,393–$-2,717 | 0/5 | $-186.52 | $-4,167.10 |
| 5 sessions | None | $-4,021 | $-6,393–$-2,717 | 0/5 | $-186.52 | $-4,167.10 |
| 10 sessions | DTE≤7 | $-5,374 | $-6,863–$-3,130 | 0/5 | $-240.65 | $-6,646.10 |
| 10 sessions | DTE≤14 | $-5,374 | $-6,863–$-3,130 | 0/5 | $-240.65 | $-6,646.10 |
| 10 sessions | None | $-5,374 | $-6,863–$-3,130 | 0/5 | $-240.65 | $-6,646.10 |
| 15 sessions | DTE≤7 | $-6,825 | $-8,467–$-5,125 | 0/5 | $-305.63 | $-9,115.10 |
| 15 sessions | DTE≤14 | $-6,825 | $-8,467–$-5,125 | 0/5 | $-305.63 | $-9,115.10 |
| 15 sessions | None | $-6,825 | $-8,467–$-5,125 | 0/5 | $-305.63 | $-9,115.10 |
| 20 sessions | DTE≤7 | $-8,027 | $-9,263–$-5,862 | 0/5 | $-372.29 | $-11,242.10 |
| 20 sessions | DTE≤14 | $-6,997 | $-8,316–$-6,678 | 0/5 | $-322.61 | $-11,658.10 |
| 20 sessions | None | $-8,027 | $-9,263–$-5,862 | 0/5 | $-372.29 | $-11,242.10 |

## All 48 settings across five phases

| Target DTE (band) | Hold | Guard | Median annual P&L | Min–max | ≥USD12k phases | Resolved | Unresolved | Win rate | Worst trade | Peak overlaps |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DTE20 (14–26) | 5 | ≤7 | $-3,792 | $-7,046–$-2,230 | 0/5 | 191 | 3 | 58.97% | $-5,200.10 | 2 |
| DTE20 (14–26) | 5 | ≤14 | $-3,670 | $-6,617–$-1,922 | 0/5 | 194 | 1 | 55.15% | $-4,344.10 | 1 |
| DTE20 (14–26) | 5 | none | $-3,792 | $-7,046–$-2,219 | 0/5 | 191 | 3 | 58.97% | $-5,200.10 | 2 |
| DTE20 (14–26) | 10 | ≤7 | $-3,757 | $-7,519–$-2,604 | 0/5 | 173 | 22 | 61.80% | $-7,777.10 | 2 |
| DTE20 (14–26) | 10 | ≤14 | $-3,577 | $-6,470–$-1,647 | 0/5 | 194 | 1 | 55.67% | $-4,344.10 | 1 |
| DTE20 (14–26) | 10 | none | $-6,571 | $-7,954–$-4,546 | 0/5 | 140 | 55 | 60.14% | $-7,125.10 | 2 |
| DTE20 (14–26) | 15 | ≤7 | $-5,191 | $-7,834–$-2,740 | 0/5 | 172 | 23 | 60.82% | $-7,777.10 | 2 |
| DTE20 (14–26) | 15 | ≤14 | $-3,577 | $-6,470–$-1,647 | 0/5 | 194 | 1 | 55.67% | $-4,344.10 | 1 |
| DTE20 (14–26) | 15 | none | $-398 | $-2,137–$311 | 0/5 | 4 | 191 | 40.00% | $-1,801.10 | 2 |
| DTE20 (14–26) | 20 | ≤7 | $-5,191 | $-7,834–$-2,740 | 0/5 | 172 | 23 | 60.82% | $-7,777.10 | 2 |
| DTE20 (14–26) | 20 | ≤14 | $-3,577 | $-6,470–$-1,647 | 0/5 | 194 | 1 | 55.67% | $-4,344.10 | 1 |
| DTE20 (14–26) | 20 | none | n/a | n/a–n/a | 0/5 | 0 | 195 | n/a | n/a | 2 |
| DTE30 (24–36) | 5 | ≤7 | $-4,633 | $-6,564–$-3,296 | 0/5 | 194 | 1 | 54.12% | $-4,489.10 | 1 |
| DTE30 (24–36) | 5 | ≤14 | $-4,633 | $-6,564–$-3,296 | 0/5 | 194 | 1 | 54.12% | $-4,489.10 | 1 |
| DTE30 (24–36) | 5 | none | $-4,633 | $-6,564–$-3,296 | 0/5 | 194 | 1 | 54.12% | $-4,489.10 | 1 |
| DTE30 (24–36) | 10 | ≤7 | $-5,586 | $-7,225–$-3,924 | 0/5 | 190 | 5 | 59.79% | $-6,660.10 | 3 |
| DTE30 (24–36) | 10 | ≤14 | $-5,417 | $-7,170–$-4,077 | 0/5 | 190 | 5 | 58.20% | $-7,379.10 | 3 |
| DTE30 (24–36) | 10 | none | $-5,586 | $-7,225–$-3,924 | 0/5 | 190 | 5 | 59.79% | $-6,660.10 | 3 |
| DTE30 (24–36) | 15 | ≤7 | $-6,952 | $-9,951–$-4,924 | 0/5 | 170 | 26 | 59.15% | $-10,567.10 | 3 |
| DTE30 (24–36) | 15 | ≤14 | $-6,299 | $-6,923–$-4,401 | 0/5 | 189 | 7 | 57.22% | $-9,431.10 | 3 |
| DTE30 (24–36) | 15 | none | $-7,537 | $-10,683–$-5,710 | 0/5 | 166 | 30 | 59.75% | $-10,567.10 | 3 |
| DTE30 (24–36) | 20 | ≤7 | $-7,145 | $-10,751–$-6,248 | 0/5 | 161 | 35 | 60.38% | $-10,567.10 | 3 |
| DTE30 (24–36) | 20 | ≤14 | $-6,299 | $-6,923–$-4,401 | 0/5 | 189 | 7 | 57.22% | $-9,431.10 | 3 |
| DTE30 (24–36) | 20 | none | $-5,684 | $-7,598–$-5,416 | 0/5 | 32 | 162 | 43.75% | $-8,788.10 | 3 |
| DTE45 (39–51) | 5 | ≤7 | $-4,021 | $-6,393–$-2,717 | 0/5 | 176 | 1 | 50.00% | $-4,167.10 | 1 |
| DTE45 (39–51) | 5 | ≤14 | $-4,021 | $-6,393–$-2,717 | 0/5 | 176 | 1 | 50.00% | $-4,167.10 | 1 |
| DTE45 (39–51) | 5 | none | $-4,021 | $-6,393–$-2,717 | 0/5 | 176 | 1 | 50.00% | $-4,167.10 | 1 |
| DTE45 (39–51) | 10 | ≤7 | $-5,374 | $-6,863–$-3,130 | 0/5 | 174 | 1 | 55.87% | $-6,646.10 | 2 |
| DTE45 (39–51) | 10 | ≤14 | $-5,374 | $-6,863–$-3,130 | 0/5 | 174 | 1 | 55.87% | $-6,646.10 | 2 |
| DTE45 (39–51) | 10 | none | $-5,374 | $-6,863–$-3,130 | 0/5 | 174 | 1 | 55.87% | $-6,646.10 | 2 |
| DTE45 (39–51) | 15 | ≤7 | $-6,825 | $-8,467–$-5,125 | 0/5 | 174 | 4 | 56.82% | $-9,115.10 | 3 |
| DTE45 (39–51) | 15 | ≤14 | $-6,825 | $-8,467–$-5,125 | 0/5 | 174 | 4 | 56.82% | $-9,115.10 | 3 |
| DTE45 (39–51) | 15 | none | $-6,825 | $-8,467–$-5,125 | 0/5 | 174 | 4 | 56.82% | $-9,115.10 | 3 |
| DTE45 (39–51) | 20 | ≤7 | $-8,027 | $-9,263–$-5,862 | 0/5 | 166 | 10 | 58.33% | $-11,242.10 | 4 |
| DTE45 (39–51) | 20 | ≤14 | $-6,997 | $-8,316–$-6,678 | 0/5 | 169 | 7 | 58.58% | $-11,658.10 | 4 |
| DTE45 (39–51) | 20 | none | $-8,027 | $-9,263–$-5,862 | 0/5 | 166 | 10 | 58.33% | $-11,242.10 | 4 |
| DTE60 (54–66) | 5 | ≤7 | $-3,108 | $-4,283–$-2,417 | 0/5 | 114 | 0 | 49.57% | $-3,874.10 | 1 |
| DTE60 (54–66) | 5 | ≤14 | $-3,108 | $-4,283–$-2,417 | 0/5 | 114 | 0 | 49.57% | $-3,874.10 | 1 |
| DTE60 (54–66) | 5 | none | $-3,108 | $-4,283–$-2,417 | 0/5 | 114 | 0 | 49.57% | $-3,874.10 | 1 |
| DTE60 (54–66) | 10 | ≤7 | $-4,274 | $-5,815–$-2,869 | 0/5 | 114 | 1 | 49.54% | $-5,389.10 | 2 |
| DTE60 (54–66) | 10 | ≤14 | $-4,274 | $-5,815–$-2,869 | 0/5 | 114 | 1 | 49.54% | $-5,389.10 | 2 |
| DTE60 (54–66) | 10 | none | $-4,274 | $-5,815–$-2,869 | 0/5 | 114 | 1 | 49.54% | $-5,389.10 | 2 |
| DTE60 (54–66) | 15 | ≤7 | $-5,193 | $-6,519–$-4,229 | 0/5 | 113 | 1 | 53.57% | $-8,425.10 | 2 |
| DTE60 (54–66) | 15 | ≤14 | $-5,193 | $-6,519–$-4,229 | 0/5 | 113 | 1 | 53.57% | $-8,425.10 | 2 |
| DTE60 (54–66) | 15 | none | $-5,193 | $-6,519–$-4,229 | 0/5 | 113 | 1 | 53.57% | $-8,425.10 | 2 |
| DTE60 (54–66) | 20 | ≤7 | $-4,902 | $-6,467–$-3,842 | 0/5 | 113 | 2 | 55.14% | $-8,416.10 | 3 |
| DTE60 (54–66) | 20 | ≤14 | $-4,902 | $-6,467–$-3,842 | 0/5 | 113 | 2 | 55.14% | $-8,416.10 | 3 |
| DTE60 (54–66) | 20 | none | $-4,902 | $-6,467–$-3,842 | 0/5 | 113 | 2 | 55.14% | $-8,416.10 | 3 |

## Calendar-year concentration: DTE45 / hold 20 / guard 7

Resolved P&L grouped by exit year, shown per phase anchor.

| Phase | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | $1,968 | $-14,264 | $-7,284 | $-6,742 | $5,713 | $-5,056 | $-14,814 | $-5,199 |
| 2 | $2,404 | $-13,884 | $-6,154 | $-11,912 | $-9,983 | $3,007 | $-25,225 | $-10,433 |
| 4 | $-2,381 | $-12,885 | $-9,568 | $-8,823 | $9,414 | $-9,630 | $-17,208 | $-11,462 |
| 6 | $175 | $-16,019 | $-12,914 | $-9,132 | $9,880 | $-14,992 | $-1,328 | $-11,188 |
| 8 | $1,541 | $-10,627 | $-17,188 | $-8,214 | $9,817 | $-17,863 | $-12,208 | $-8,625 |

## Limits

- Annual number is resolved trade P&L summed and divided by calendar years, not CAGR, account return, or proof USD 100,000 can fund the positions. Unresolved trades are excluded from P&L statistics and separately counted.
- EOD quote-side estimates are not verified fills. File hashes pin the data files but do not independently authenticate original exchange/OPRA provenance.
- Five phase anchors are a robustness sample, not all 10 possible anchors. Results that move across anchors are phase-sensitive.
- Gross SPY assignment obligation is not broker margin. Account cash, buying power, assignment funding, forced liquidation, financing, tax, compounding and TAIL cost are not modeled.
- Assess phase range, worst trade, unresolved episodes and calendar-year concentration alongside annual P&L; do not select the highest average alone.

Machine-readable outputs: factorial_matrix.csv (240 phase cells), factorial_config_summary.csv (48 settings), factorial_main_effects.csv, factorial_calendar_year_pnl.csv.
