# Mode C: Capacity-gated DTE × holding × exit comparison

- Replay period: 2018-03-01 through 2025-12-15 (7.792 calendar years).
- Strategy: QQQ LONG CALL 1 : SPY SHORT CALL 6; same expiry; both legs nearest absolute Delta 0.20; fixed 10-common-session signal cadence; five phase anchors 0, 2, 4, 6, 8.
- Costs: USD 0.05 per option-share per side slippage and USD 0.65 per contract per side commission.
- Mode C semantics: each holding/exit policy owns an independent book; admit a new signal only if live cohort reservations are below cap 1 or 2; skip blocked signals without re-anchoring; unresolved/expired-without-executable-exit cohorts reserve capacity through source end.
- Capacity gating is a chronological admission simulation over the same source-pinned, per-cohort quote-side outcomes. Blocked cohorts contribute no P&L; because positions are separately simulated, their hypothetical paths do not affect later cohorts.
- Annual P&L is resolved episode net P&L summed then divided by 7.792 calendar years; not CAGR, account return, or proof of USD 100,000 buying-power feasibility.
- Peak gross call-delivery notional is the sum of SPY short-call strike × 100 × short contracts across concurrently open admitted cohorts; it is not broker margin or maximum loss.
- Unresolved episodes are excluded from P&L but keep their capacity slot through source end. EOD quote-side prices are not verified fills.

## Shortlist across DTE and capacity limits

| DTE band | Max cohorts | Hold | Exit guard | Median annual P&L | Phase range | P&L retained vs unlimited | Peak delivery-notional reduction | Median skipped | Worst trade across phases | Peak call-delivery notional |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 20 (14-26) | 1 | 15 | none | 0 | 0–0 | 0.0% | 99.7% | 194.0 / 195.0 (99.5%) | n/a | 170,400 |
| 20 (14-26) | 1 | 20 | none | 0 | 0–0 | n/a% | 99.7% | 194.0 / 195.0 (99.5%) | n/a | 170,400 |
| 20 (14-26) | 2 | 10 | DTE <= 7 | 112 | -200–228 | n/a% | 93.8% | 188.0 / 195.0 (95.9%) | -1,111 | 346,200 |
| 20 (14-26) | 2 | 15 | DTE <= 7 | 112 | -200–228 | n/a% | 93.8% | 188.0 / 195.0 (95.9%) | -1,111 | 346,200 |
| 20 (14-26) | UNLIMITED | 20 | none | 0 | 0–0 | n/a% | 0.0% | 0.0 / 195.0 (0.0%) | n/a | 50,214,300 |
| 20 (14-26) | UNLIMITED | 15 | none | -398 | -2,137–311 | 100.0% | 0.0% | 0.0 / 195.0 (0.0%) | -12,865 | 49,775,100 |
| 30 (24-36) | 1 | 20 | none | 0 | 0–0 | n/a% | 99.6% | 194.0 / 195.0 (99.5%) | n/a | 171,000 |
| 30 (24-36) | 1 | 20 | DTE <= 7 | 0 | 0–21 | n/a% | 98.0% | 194.0 / 195.0 (99.5%) | -917 | 177,600 |
| 30 (24-36) | 1 | 15 | DTE <= 7 | 0 | -35–132 | n/a% | 97.3% | 193.0 / 195.0 (99.5%) | -1,272 | 178,800 |
| 30 (24-36) | 2 | 15 | DTE <= 7 | 120 | -19–393 | n/a% | 94.4% | 184.0 / 195.0 (94.3%) | -1,272 | 355,800 |
| 30 (24-36) | 2 | 15 | none | 43 | -26–357 | n/a% | 95.7% | 184.0 / 195.0 (94.3%) | -1,272 | 355,800 |
| 30 (24-36) | UNLIMITED | 5 | DTE <= 7 | -4,633 | -6,564–-3,296 | n/a% | 0.0% | 0.0 / 195.0 (0.0%) | -6,973 | 426,600 |
| 30 (24-36) | UNLIMITED | 5 | DTE <= 14 | -4,633 | -6,564–-3,296 | n/a% | 0.0% | 0.0 / 195.0 (0.0%) | -6,973 | 426,600 |
| 30 (24-36) | UNLIMITED | 15 | none | -7,537 | -10,683–-5,710 | n/a% | 0.0% | 0.0 / 195.0 (0.0%) | -15,128 | 9,221,700 |
| 45 (39-51) | 1 | 20 | DTE <= 7 | 175 | -2,176–214 | n/a% | 94.3% | 165.0 / 176.0 (95.9%) | -7,213 | 296,400 |
| 45 (39-51) | 1 | 20 | none | 175 | -2,176–214 | n/a% | 94.3% | 165.0 / 176.0 (95.9%) | -7,213 | 296,400 |
| 45 (39-51) | 1 | 15 | DTE <= 7 | -393 | -5,190–31 | n/a% | 85.2% | 144.0 / 176.0 (85.2%) | -9,115 | 429,000 |
| 45 (39-51) | 2 | 20 | DTE <= 7 | -85 | -2,395–221 | n/a% | 88.7% | 159.0 / 176.0 (91.1%) | -7,213 | 478,200 |
| 45 (39-51) | 2 | 20 | none | -85 | -2,395–221 | n/a% | 88.7% | 159.0 / 176.0 (91.1%) | -7,213 | 478,200 |
| 45 (39-51) | 2 | 10 | DTE <= 7 | -4,539 | -6,863–-3,130 | n/a% | 0.0% | 0.0 / 176.0 (0.0%) | -6,837 | 847,800 |
| 45 (39-51) | UNLIMITED | 5 | DTE <= 7 | -4,021 | -6,393–-2,717 | n/a% | 0.0% | 0.0 / 176.0 (0.0%) | -7,899 | 429,000 |
| 45 (39-51) | UNLIMITED | 5 | DTE <= 14 | -4,021 | -6,393–-2,717 | n/a% | 0.0% | 0.0 / 176.0 (0.0%) | -7,899 | 429,000 |
| 45 (39-51) | UNLIMITED | 15 | DTE <= 7 | -6,825 | -8,467–-5,125 | n/a% | 0.0% | 0.0 / 176.0 (0.0%) | -14,156 | 1,410,600 |
| 60 (54-66) | 1 | 20 | DTE <= 7 | -1,847 | -3,426–145 | n/a% | 66.5% | 59.0 / 115.0 (51.3%) | -9,216 | 431,400 |
| 60 (54-66) | 1 | 20 | DTE <= 14 | -1,847 | -3,426–145 | n/a% | 66.5% | 59.0 / 115.0 (51.3%) | -9,216 | 431,400 |
| 60 (54-66) | 1 | 10 | DTE <= 7 | -2,351 | -4,205–-1,964 | n/a% | 50.3% | 30.0 / 115.0 (26.7%) | -5,888 | 432,000 |
| 60 (54-66) | 2 | 5 | DTE <= 7 | -3,108 | -4,283–-2,417 | n/a% | 0.0% | 0.0 / 115.0 (0.0%) | -4,487 | 435,000 |
| 60 (54-66) | 2 | 5 | DTE <= 14 | -3,108 | -4,283–-2,417 | n/a% | 0.0% | 0.0 / 115.0 (0.0%) | -4,487 | 435,000 |
| 60 (54-66) | 2 | 10 | DTE <= 7 | -4,274 | -5,815–-2,869 | n/a% | 0.0% | 0.0 / 115.0 (0.0%) | -5,982 | 867,000 |
| 60 (54-66) | UNLIMITED | 5 | DTE <= 7 | -3,108 | -4,283–-2,417 | n/a% | 0.0% | 0.0 / 115.0 (0.0%) | -4,487 | 435,000 |
| 60 (54-66) | UNLIMITED | 5 | DTE <= 14 | -3,108 | -4,283–-2,417 | n/a% | 0.0% | 0.0 / 115.0 (0.0%) | -4,487 | 435,000 |
| 60 (54-66) | UNLIMITED | 10 | DTE <= 7 | -4,274 | -5,815–-2,869 | n/a% | 0.0% | 0.0 / 115.0 (0.0%) | -5,982 | 867,000 |

## How to interpret it

- Cap 1 serializes the portfolio; cap 2 allows up to two open/reserved cohorts; UNLIMITED is the control.
- Annual median must be read with phase range, skipped-entry rate, worst trade, unresolved counts, peak simultaneous cohorts and gross call-delivery notional.
- Cap reduces admitted opportunities, so lower total P&L can coexist with similar per-trade expectancy. It is useful only if lower stacked exposure is worth the income surrendered.
- A high win rate does not neutralize the 1:6 structure's short-call tail risk. Account cash, broker margin, forced liquidation, financing, tax, compounding and TAIL cost are not modeled.
- Before choosing any configuration for live use, validate the underlying quote history, fills and the actual broker's assignment/margin treatment.

Machine-readable outputs: mode_c_capacity_matrix.csv (720 phase cells), mode_c_capacity_config_summary.csv (144 configurations), mode_c_capacity_calendar_year_pnl.csv, and mode_c_selected_episodes.csv.
