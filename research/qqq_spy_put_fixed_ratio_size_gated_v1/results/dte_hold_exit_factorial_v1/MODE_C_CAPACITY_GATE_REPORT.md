# Mode C: Capacity-gated DTE × holding × exit comparison

- Replay period: 2018-03-01 through 2025-12-15 (7.792 calendar years).
- Strategy: QQQ LONG PUT 1 : SPY SHORT PUT 6; same expiry; both legs nearest absolute Delta 0.25; fixed 10-common-session signal cadence; five phase anchors 0, 2, 4, 6, 8.
- Costs: USD 0.05 per option-share per side slippage and USD 0.65 per contract per side commission.
- Mode C semantics: each holding/exit policy owns an independent book; admit a new signal only if live cohort reservations are below cap 1 or 2; skip blocked signals without re-anchoring; unresolved/expired-without-executable-exit cohorts reserve capacity through source end.
- Capacity gating is a chronological admission simulation over the same source-pinned, per-cohort quote-side outcomes. Blocked cohorts contribute no P&L; because positions are separately simulated, their hypothetical paths do not affect later cohorts.
- Annual P&L is resolved episode net P&L summed then divided by 7.792 calendar years; not CAGR, account return, or proof of USD 100,000 buying-power feasibility.
- Peak gross assignment obligation is the sum of SPY short-put strike × 100 × short contracts across concurrently open admitted cohorts; it is not broker margin or maximum loss.
- Unresolved episodes are excluded from P&L but keep their capacity slot through source end. EOD quote-side prices are not verified fills.

## Shortlist across DTE and capacity limits

| DTE band | Max cohorts | Hold | Exit guard | Median annual P&L | Phase range | P&L retained vs unlimited | Peak obligation reduction | Median skipped | Worst trade across phases | Peak assignment obligation |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 20 (14-26) | 1 | 5 | DTE <= 7 | 2,960 | -1,743–6,824 | 100.0% | 0.0% | 0.0 / 195.0 (0.0%) | -19,508 | 404,400 |
| 20 (14-26) | 1 | 5 | none | 2,960 | -1,743–6,824 | 100.0% | 0.0% | 0.0 / 195.0 (0.0%) | -19,508 | 404,400 |
| 20 (14-26) | 2 | 10 | DTE <= 7 | 4,651 | -2,009–7,446 | 111.5% | 39.3% | 46.0 / 195.0 (23.5%) | -28,409 | 790,800 |
| 20 (14-26) | 2 | 5 | DTE <= 7 | 2,960 | -1,743–6,824 | 100.0% | 0.0% | 0.0 / 195.0 (0.0%) | -19,508 | 404,400 |
| 20 (14-26) | UNLIMITED | 10 | DTE <= 7 | 3,611 | -3,177–9,749 | 100.0% | 0.0% | 0.0 / 195.0 (0.0%) | -30,517 | 1,063,200 |
| 20 (14-26) | UNLIMITED | 15 | DTE <= 7 | 3,241 | -3,577–7,438 | 100.0% | 0.0% | 0.0 / 195.0 (0.0%) | -30,517 | 1,219,500 |
| 20 (14-26) | UNLIMITED | 5 | DTE <= 7 | 2,960 | -1,743–6,824 | 100.0% | 0.0% | 0.0 / 195.0 (0.0%) | -19,508 | 404,400 |
| 30 (24-36) | 1 | 10 | DTE <= 7 | 5,417 | -1,072–6,186 | 66.2% | 50.6% | 97.0 / 195.0 (50.0%) | -29,537 | 401,400 |
| 30 (24-36) | 1 | 10 | none | 5,417 | -1,072–6,186 | 66.2% | 50.6% | 97.0 / 195.0 (50.0%) | -29,537 | 401,400 |
| 30 (24-36) | 2 | 10 | DTE <= 7 | 5,497 | 1,432–8,186 | 100.0% | 0.0% | 0.0 / 195.0 (0.0%) | -29,537 | 789,000 |
| 30 (24-36) | 2 | 10 | none | 5,497 | 1,432–8,186 | 100.0% | 0.0% | 0.0 / 195.0 (0.0%) | -29,537 | 789,000 |
| 30 (24-36) | 2 | 5 | DTE <= 7 | 3,565 | -1,372–5,599 | 100.0% | 0.0% | 0.0 / 195.0 (0.0%) | -19,044 | 401,400 |
| 30 (24-36) | UNLIMITED | 15 | none | 9,627 | 4,018–9,850 | 100.0% | 0.0% | 0.0 / 195.0 (0.0%) | -45,081 | 3,222,000 |
| 30 (24-36) | UNLIMITED | 20 | DTE <= 7 | 8,199 | 5,285–10,313 | 100.0% | 0.0% | 0.0 / 195.0 (0.0%) | -45,908 | 3,141,300 |
| 30 (24-36) | UNLIMITED | 5 | DTE <= 7 | 3,565 | -1,372–5,599 | 100.0% | 0.0% | 0.0 / 195.0 (0.0%) | -19,044 | 401,400 |
| 45 (39-51) | 1 | 20 | DTE <= 14 | 4,908 | -1,279–8,591 | 37.3% | 72.8% | 112.0 / 176.0 (62.2%) | -44,015 | 404,400 |
| 45 (39-51) | 1 | 10 | DTE <= 7 | 4,641 | 775–5,221 | 62.4% | 49.5% | 85.0 / 176.0 (47.2%) | -27,025 | 404,400 |
| 45 (39-51) | 2 | 20 | DTE <= 14 | 10,558 | 946–13,059 | 83.6% | 51.5% | 55.0 / 176.0 (32.0%) | -46,365 | 796,800 |
| 45 (39-51) | 2 | 15 | DTE <= 7 | 6,718 | 3,854–11,779 | 100.0% | 34.6% | 16.0 / 176.0 (9.5%) | -45,670 | 791,400 |
| 45 (39-51) | UNLIMITED | 20 | DTE <= 14 | 13,329 | 6,801–15,627 | 100.0% | 0.0% | 0.0 / 176.0 (0.0%) | -46,879 | 1,440,600 |
| 45 (39-51) | UNLIMITED | 20 | DTE <= 7 | 12,350 | 6,901–14,995 | 100.0% | 0.0% | 0.0 / 176.0 (0.0%) | -51,761 | 1,533,000 |
| 45 (39-51) | UNLIMITED | 15 | DTE <= 7 | 7,135 | 6,289–11,779 | 100.0% | 0.0% | 0.0 / 176.0 (0.0%) | -45,670 | 1,051,200 |
| 60 (54-66) | 1 | 20 | DTE <= 7 | 5,128 | 2,507–6,844 | 54.9% | 80.9% | 68.0 / 115.0 (62.4%) | -28,539 | 393,000 |
| 60 (54-66) | 1 | 20 | DTE <= 14 | 5,128 | 2,507–6,844 | 54.9% | 80.9% | 68.0 / 115.0 (62.4%) | -28,539 | 393,000 |
| 60 (54-66) | 1 | 15 | DTE <= 7 | 3,934 | 828–10,347 | 42.9% | 73.8% | 49.0 / 115.0 (44.4%) | -40,775 | 390,000 |
| 60 (54-66) | 2 | 15 | DTE <= 7 | 9,173 | 5,485–10,754 | 100.0% | 37.3% | 11.0 / 115.0 (10.1%) | -40,775 | 780,000 |
| 60 (54-66) | 2 | 15 | DTE <= 14 | 9,173 | 5,485–10,754 | 100.0% | 37.3% | 11.0 / 115.0 (10.1%) | -40,775 | 780,000 |
| 60 (54-66) | UNLIMITED | 15 | DTE <= 7 | 9,656 | 4,356–10,604 | 100.0% | 0.0% | 0.0 / 115.0 (0.0%) | -40,775 | 1,059,000 |
| 60 (54-66) | UNLIMITED | 15 | DTE <= 14 | 9,656 | 4,356–10,604 | 100.0% | 0.0% | 0.0 / 115.0 (0.0%) | -40,775 | 1,059,000 |

## How to interpret it

- Cap 1 serializes the portfolio; cap 2 allows up to two open/reserved cohorts; UNLIMITED is the control.
- Annual median must be read with phase range, skipped-entry rate, worst trade, unresolved counts, peak simultaneous cohorts and gross assignment obligation.
- Cap reduces admitted opportunities, so lower total P&L can coexist with similar per-trade expectancy. It is useful only if lower stacked exposure is worth the income surrendered.
- A high win rate does not neutralize the 1:6 structure's short-put tail risk. Account cash, broker margin, forced liquidation, financing, tax, compounding and TAIL cost are not modeled.
- Before choosing any configuration for live use, validate the underlying quote history, fills and the actual broker's assignment/margin treatment.

Machine-readable outputs: mode_c_capacity_matrix.csv (720 phase cells), mode_c_capacity_config_summary.csv (144 configurations), mode_c_capacity_calendar_year_pnl.csv, and mode_c_selected_episodes.csv.
