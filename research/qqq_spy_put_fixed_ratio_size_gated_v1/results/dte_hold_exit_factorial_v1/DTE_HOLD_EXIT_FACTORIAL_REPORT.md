# DTE × holding duration × exit guard factorial replay

- Period: 2018-03-01 to 2025-12-15 (7.792 calendar years).
- Cadence: every 10 common QQQ/SPY sessions; five predeclared phase anchors: 0, 2, 4, 6, 8.
- Fixed legs: QQQ LONG PUT 1 : SPY SHORT PUT 6; same expiry; nearest absolute Delta 0.25 on both legs.
- Costs: USD 0.05/share/side slippage + USD 0.65/contract/side commission; no entry filter.
- DTE target bands: DTE20: 14–26; DTE30: 24–36; DTE45: 39–51; DTE60: 54–66.
- Exit rules: max hold 5/10/15/20 sessions × no guard / remaining DTE ≤ 7 / remaining DTE ≤ 14. Guard exits use OR logic with maximum hold.
- 20 source-pinned replay runs (4 DTE targets × 5 phases); all 12 exit policies run on each selected entry stream, yielding 240 phase cells and 48 phase-aggregated settings.

## Main effects

Each factor level is the median annual resolved-trade P&L across the other settings and five phase anchors. Spread is max minus min of level medians; descriptive screening only, not causal or account return.

| Factor | Level | Median annual P&L across other settings | Factor level spread |
|---|---:|---:|---:|
| Opening DTE target | DTE20 | $1,436 | $5,184 |
| Opening DTE target | DTE30 | $4,026 | $5,184 |
| Opening DTE target | DTE45 | $6,108 | $5,184 |
| Opening DTE target | DTE60 | $6,620 | $5,184 |
| Max holding sessions | 5 sessions | $2,356 | $5,096 |
| Max holding sessions | 10 sessions | $4,608 | $5,096 |
| Max holding sessions | 15 sessions | $7,135 | $5,096 |
| Max holding sessions | 20 sessions | $7,452 | $5,096 |
| Early-exit DTE guard | No DTE guard | $3,916 | $641 |
| Early-exit DTE guard | Remaining DTE ≤ 7 | $4,498 | $641 |
| Early-exit DTE guard | Remaining DTE ≤ 14 | $4,557 | $641 |

## Same exit: hold up to 20 sessions OR remaining DTE ≤ 7

| Opening DTE target (band) | Median annual P&L | Min–max by phase | Phases ≥ USD12k | Median win rate | Median worst trade |
|---:|---:|---:|---:|---:|---:|
| DTE20 (14–26) | $3,241 | $-3,577–$7,438 | 0/5 | 81.87% | $-23,526.10 |
| DTE30 (24–36) | $8,199 | $5,285–$10,313 | 0/5 | 83.51% | $-32,761.10 |
| DTE45 (39–51) | $12,350 | $6,901–$14,995 | 3/5 | 82.76% | $-44,015.10 |
| DTE60 (54–66) | $7,452 | $4,971–$15,711 | 1/5 | 81.25% | $-39,349.10 |

## Same DTE target: DTE45 (band 39–51)

| Max hold | Guard | Median annual P&L | Min–max by phase | Phases ≥ USD12k | Median expectancy/trade | Median worst trade |
|---:|---|---:|---:|---:|---:|---:|
| 5 sessions | DTE≤7 | $2,356 | $37–$3,450 | 0/5 | $109.26 | $-17,582.10 |
| 5 sessions | DTE≤14 | $2,356 | $37–$3,450 | 0/5 | $109.26 | $-17,582.10 |
| 5 sessions | None | $2,356 | $37–$3,450 | 0/5 | $109.26 | $-17,582.10 |
| 10 sessions | DTE≤7 | $5,081 | $125–$8,035 | 0/5 | $221.17 | $-18,603.10 |
| 10 sessions | DTE≤14 | $5,081 | $125–$8,035 | 0/5 | $221.17 | $-18,603.10 |
| 10 sessions | None | $5,081 | $125–$8,035 | 0/5 | $221.17 | $-18,603.10 |
| 15 sessions | DTE≤7 | $7,135 | $6,289–$11,779 | 0/5 | $312.32 | $-34,139.10 |
| 15 sessions | DTE≤14 | $7,135 | $6,289–$11,779 | 0/5 | $312.32 | $-34,139.10 |
| 15 sessions | None | $7,135 | $6,289–$11,779 | 0/5 | $312.32 | $-34,139.10 |
| 20 sessions | DTE≤7 | $12,350 | $6,901–$14,995 | 3/5 | $543.67 | $-44,015.10 |
| 20 sessions | DTE≤14 | $13,329 | $6,801–$15,627 | 3/5 | $583.47 | $-44,015.10 |
| 20 sessions | None | $12,350 | $6,901–$14,995 | 3/5 | $543.67 | $-44,015.10 |

## All 48 settings across five phases

| Target DTE (band) | Hold | Guard | Median annual P&L | Min–max | ≥USD12k phases | Resolved | Unresolved | Win rate | Worst trade | Peak overlaps |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DTE20 (14–26) | 5 | ≤7 | $2,960 | $-1,743–$6,824 | 0/5 | 194 | 1 | 75.26% | $-18,773.10 | 1 |
| DTE20 (14–26) | 5 | ≤14 | $151 | $-1,204–$4,354 | 0/5 | 194 | 1 | 72.68% | $-18,773.10 | 1 |
| DTE20 (14–26) | 5 | none | $2,960 | $-1,743–$6,824 | 0/5 | 194 | 1 | 75.26% | $-18,773.10 | 1 |
| DTE20 (14–26) | 10 | ≤7 | $3,611 | $-3,177–$9,749 | 0/5 | 193 | 2 | 81.35% | $-20,563.10 | 2 |
| DTE20 (14–26) | 10 | ≤14 | $1,436 | $-1,629–$4,674 | 0/5 | 194 | 1 | 73.33% | $-18,773.10 | 1 |
| DTE20 (14–26) | 10 | none | $-470 | $-2,422–$3,950 | 0/5 | 161 | 33 | 80.72% | $-26,010.10 | 2 |
| DTE20 (14–26) | 15 | ≤7 | $3,241 | $-3,577–$7,438 | 0/5 | 192 | 3 | 81.87% | $-23,526.10 | 2 |
| DTE20 (14–26) | 15 | ≤14 | $1,436 | $-1,629–$4,674 | 0/5 | 194 | 1 | 73.33% | $-18,773.10 | 1 |
| DTE20 (14–26) | 15 | none | $-899 | $-6,104–$309 | 0/5 | 4 | 192 | 50.00% | $-4,904.10 | 2 |
| DTE20 (14–26) | 20 | ≤7 | $3,241 | $-3,577–$7,438 | 0/5 | 192 | 3 | 81.87% | $-23,526.10 | 2 |
| DTE20 (14–26) | 20 | ≤14 | $1,436 | $-1,629–$4,674 | 0/5 | 194 | 1 | 73.33% | $-18,773.10 | 1 |
| DTE20 (14–26) | 20 | none | n/a | n/a–n/a | 0/5 | 0 | 195 | n/a | n/a | 2 |
| DTE30 (24–36) | 5 | ≤7 | $3,565 | $-1,372–$5,599 | 0/5 | 194 | 1 | 70.92% | $-18,183.10 | 1 |
| DTE30 (24–36) | 5 | ≤14 | $3,565 | $-1,372–$5,599 | 0/5 | 194 | 1 | 70.92% | $-18,183.10 | 1 |
| DTE30 (24–36) | 5 | none | $3,565 | $-1,372–$5,599 | 0/5 | 194 | 1 | 70.92% | $-18,183.10 | 1 |
| DTE30 (24–36) | 10 | ≤7 | $3,916 | $1,432–$8,186 | 0/5 | 194 | 1 | 77.95% | $-20,317.10 | 2 |
| DTE30 (24–36) | 10 | ≤14 | $4,136 | $547–$8,402 | 0/5 | 194 | 1 | 77.72% | $-20,317.10 | 2 |
| DTE30 (24–36) | 10 | none | $3,916 | $1,432–$8,186 | 0/5 | 194 | 1 | 77.95% | $-20,317.10 | 2 |
| DTE30 (24–36) | 15 | ≤7 | $7,308 | $4,750–$11,455 | 0/5 | 189 | 6 | 83.07% | $-34,120.10 | 3 |
| DTE30 (24–36) | 15 | ≤14 | $4,978 | $1,846–$6,864 | 0/5 | 194 | 1 | 77.72% | $-29,537.10 | 2 |
| DTE30 (24–36) | 15 | none | $9,627 | $4,018–$9,850 | 0/5 | 182 | 13 | 81.87% | $-34,120.10 | 3 |
| DTE30 (24–36) | 20 | ≤7 | $8,199 | $5,285–$10,313 | 0/5 | 183 | 11 | 83.51% | $-32,761.10 | 3 |
| DTE30 (24–36) | 20 | ≤14 | $4,978 | $1,846–$6,864 | 0/5 | 194 | 1 | 77.72% | $-29,537.10 | 2 |
| DTE30 (24–36) | 20 | none | $-2,422 | $-10,552–$3,534 | 0/5 | 31 | 165 | 73.68% | $-29,606.10 | 3 |
| DTE45 (39–51) | 5 | ≤7 | $2,356 | $37–$3,450 | 0/5 | 176 | 1 | 69.05% | $-17,582.10 | 1 |
| DTE45 (39–51) | 5 | ≤14 | $2,356 | $37–$3,450 | 0/5 | 176 | 1 | 69.05% | $-17,582.10 | 1 |
| DTE45 (39–51) | 5 | none | $2,356 | $37–$3,450 | 0/5 | 176 | 1 | 69.05% | $-17,582.10 | 1 |
| DTE45 (39–51) | 10 | ≤7 | $5,081 | $125–$8,035 | 0/5 | 175 | 1 | 77.09% | $-18,603.10 | 2 |
| DTE45 (39–51) | 10 | ≤14 | $5,081 | $125–$8,035 | 0/5 | 175 | 1 | 77.09% | $-18,603.10 | 2 |
| DTE45 (39–51) | 10 | none | $5,081 | $125–$8,035 | 0/5 | 175 | 1 | 77.09% | $-18,603.10 | 2 |
| DTE45 (39–51) | 15 | ≤7 | $7,135 | $6,289–$11,779 | 0/5 | 175 | 2 | 78.65% | $-34,139.10 | 2 |
| DTE45 (39–51) | 15 | ≤14 | $7,135 | $6,289–$11,779 | 0/5 | 175 | 2 | 78.65% | $-34,139.10 | 2 |
| DTE45 (39–51) | 15 | none | $7,135 | $6,289–$11,779 | 0/5 | 175 | 2 | 78.65% | $-34,139.10 | 2 |
| DTE45 (39–51) | 20 | ≤7 | $12,350 | $6,901–$14,995 | 3/5 | 174 | 3 | 82.76% | $-44,015.10 | 3 |
| DTE45 (39–51) | 20 | ≤14 | $13,329 | $6,801–$15,627 | 3/5 | 174 | 2 | 83.13% | $-44,015.10 | 3 |
| DTE45 (39–51) | 20 | none | $12,350 | $6,901–$14,995 | 3/5 | 174 | 3 | 82.76% | $-44,015.10 | 3 |
| DTE60 (54–66) | 5 | ≤7 | $1,722 | $54–$3,006 | 0/5 | 113 | 0 | 66.37% | $-8,501.10 | 2 |
| DTE60 (54–66) | 5 | ≤14 | $1,722 | $54–$3,006 | 0/5 | 113 | 0 | 66.37% | $-8,501.10 | 2 |
| DTE60 (54–66) | 5 | none | $1,722 | $54–$3,006 | 0/5 | 113 | 0 | 66.37% | $-8,501.10 | 2 |
| DTE60 (54–66) | 10 | ≤7 | $5,788 | $2,357–$10,503 | 0/5 | 113 | 1 | 76.79% | $-14,701.10 | 2 |
| DTE60 (54–66) | 10 | ≤14 | $5,788 | $2,357–$10,503 | 0/5 | 113 | 1 | 76.79% | $-14,701.10 | 2 |
| DTE60 (54–66) | 10 | none | $5,788 | $2,357–$10,503 | 0/5 | 113 | 1 | 76.79% | $-14,701.10 | 2 |
| DTE60 (54–66) | 15 | ≤7 | $9,656 | $4,356–$10,604 | 0/5 | 112 | 2 | 80.53% | $-19,568.10 | 2 |
| DTE60 (54–66) | 15 | ≤14 | $9,656 | $4,356–$10,604 | 0/5 | 112 | 2 | 80.53% | $-19,568.10 | 2 |
| DTE60 (54–66) | 15 | none | $9,656 | $4,356–$10,604 | 0/5 | 112 | 2 | 80.53% | $-19,568.10 | 2 |
| DTE60 (54–66) | 20 | ≤7 | $7,452 | $4,971–$15,711 | 1/5 | 112 | 2 | 81.25% | $-39,349.10 | 3 |
| DTE60 (54–66) | 20 | ≤14 | $7,452 | $4,971–$15,711 | 1/5 | 112 | 2 | 81.25% | $-39,349.10 | 3 |
| DTE60 (54–66) | 20 | none | $7,452 | $4,971–$15,711 | 1/5 | 112 | 2 | 81.25% | $-39,349.10 | 3 |

## Calendar-year concentration: DTE45 / hold 20 / guard 7

Resolved P&L grouped by exit year, shown per phase anchor.

| Phase | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | $-197 | $12,818 | $-2,820 | $37,049 | $-16,676 | $28,804 | $25,989 | $20,145 |
| 2 | $-1,590 | $12,403 | $-21,525 | $42,233 | $-2,615 | $18,233 | $25,247 | $-18,611 |
| 4 | $-3,916 | $11,991 | $-11,450 | $40,983 | $-14,076 | $20,710 | $33,678 | $18,312 |
| 6 | $-9,936 | $19,148 | $-34,351 | $34,748 | $9,650 | $13,669 | $31,709 | $3,482 |
| 8 | $-1,567 | $22,070 | $-34,026 | $41,002 | $9,742 | $23,638 | $30,982 | $24,999 |

## Limits

- Annual number is resolved trade P&L summed and divided by calendar years, not CAGR, account return, or proof USD 100,000 can fund the positions. Unresolved trades are excluded from P&L statistics and separately counted.
- EOD quote-side estimates are not verified fills. File hashes pin the data files but do not independently authenticate original exchange/OPRA provenance.
- Five phase anchors are a robustness sample, not all 10 possible anchors. Results that move across anchors are phase-sensitive.
- Gross SPY assignment obligation is not broker margin. Account cash, buying power, assignment funding, forced liquidation, financing, tax, compounding and TAIL cost are not modeled.
- Assess phase range, worst trade, unresolved episodes and calendar-year concentration alongside annual P&L; do not select the highest average alone.

Machine-readable outputs: factorial_matrix.csv (240 phase cells), factorial_config_summary.csv (48 settings), factorial_main_effects.csv, factorial_calendar_year_pnl.csv.
