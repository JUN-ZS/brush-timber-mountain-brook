# SPY Far-Tail Conditional Risk-Trigger Hedge — Research V1

> Source-pinned historical research. No broker orders were placed.

## 1. Executive decision

**Keep no hedge as the control. Do not enable unconditional tail buying based on the current evidence.** This first trigger rule tests whether premiums can be concentrated in higher-risk entry conditions. It is a pre-declared research candidate, not an optimized or validated trading rule.

At each base entry, the rule triggers if either (A) SPY is at least 5% below the high among the current and four prior entry observations in the same phase, or (B) the selected base short SPY PUT absolute Delta at signal time is at least 0.30. Five observations proxy about 20 sessions under the fixed five-session cadence. Thresholds are frozen before measuring this experiment's outcomes; they must not be tuned on a claimed holdout.

**Critical result:** for DTE45 / Hold-20, median worst-realized-trade improvement is $0.00 for all tested Delta targets at both 1x and 3x. The entry trigger reduces recurring average-P&L drag by buying protection on only about 13.5% of entries, but it did not catch the worst realized trade in the paired samples. Do not adopt this entry-only trigger on the claim that it protects the worst trade.

## 2. Frozen rule and fair accounting

- Baseline remains QQQ LONG PUT 1 : SPY SHORT PUT 3; original entries, quantities, exit policies and cadence are unchanged.
- The hedge is considered at base entry only. No mid-trade additions, rebalancing, stop, roll or future-price trigger is tested.
- Drawdown rule uses current entry spot and earlier observations only; five valid positive spots are required. Missing history cannot trigger the drawdown component. The Delta rule can trigger independently.
- Signal-time Delta is the base selected short put's recorded absolute Delta, not a recalculation at the later entry timestamp.
- Hedge targets: 2.5-delta (~−0.025), 5-delta (~−0.05), 10-delta (~−0.10) reference; quantities 1 and 3. The 2.5/5 targets share the same eligible absolute-Delta band.
- Costs and quote sides match the frozen overlay replay: ask-side buys, bid-side realized exits, $0.05 option-share slippage per side and $0.65 commission per contract per side. Displayed-size checks are not proof of fills.
- No trigger means no tail purchase and conditional P&L equals base P&L. Trigger but entry quote/size gate fails also means no modeled purchase. If the hedge was eligible to enter but lacks a valid size-gated exit quote, the realized conditional result remains missing—not zero, not a mark-to-market profit, and not the base P&L.
- The primary fair comparison is no hedge vs conditional strategy on exactly the same rows where conditional realized outcome is known. All-resolved no-hedge results are provided separately, together with outcome coverage.

## 3. Trigger frequency by phase

| Arm | Phase | Cohorts | Any trigger | Drawdown trigger | Delta trigger | Both |
|---|---:|---:|---:|---:|---:|---:|
| DTE14 | 0 | 392 | 14.80% | 13.78% | 1.53% | 0.51% |
| DTE14 | 1 | 392 | 14.03% | 13.27% | 1.28% | 0.51% |
| DTE14 | 2 | 391 | 12.79% | 12.28% | 0.77% | 0.26% |
| DTE14 | 3 | 390 | 14.36% | 13.08% | 1.54% | 0.26% |
| DTE14 | 4 | 388 | 11.08% | 10.82% | 0.26% | 0.00% |
| DTE45 | 0 | 392 | 14.29% | 13.78% | 0.51% | 0.00% |
| DTE45 | 1 | 392 | 13.52% | 13.01% | 0.51% | 0.00% |
| DTE45 | 2 | 391 | 12.28% | 12.28% | 0.00% | 0.00% |
| DTE45 | 3 | 390 | 13.59% | 13.08% | 0.51% | 0.00% |
| DTE45 | 4 | 389 | 11.31% | 10.80% | 0.51% | 0.00% |
| DTE14 phase range | — | — | 11.08–14.80% | — | — | — |
| DTE45 phase range | — | — | 11.31–14.29% | — | — | — |

Trigger rate is the fraction of opened base entry cohorts, not the probability of a future loss. Five phases overlap, so phase rates are a robustness range rather than independent evidence.

## 4. Conditional vs no hedge and unconditional references

Median of five phase values is shown for each configuration; the phases overlap. The conditional increment compares the baseline and conditional result on the exact same known-outcome rows. The unconditional figure comes from the earlier overlay's paired sample and has different coverage, so compare it only with the coverage figures alongside it.

| Arm | Exit | Tail | Qty | Trigger rate median (range) | Entry coverage median (range) | Exit-pair coverage median (range) | Outcome coverage median (range) | No-hedge matched mean median (range) | Conditional matched mean median (range) | Conditional Δ mean median (range) | Unconditional Δ mean median | Worst-trade improvement median (range) | Modeled entry debit median (range) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DTE14 | Hold-10 / DTE≤7 | 2.5-delta (~−0.025) | 1 | 14.07% (11.14% to 14.62%) | 97.96% (96.43% to 100.00%) | 85.71% (85.19% to 89.47%) | 98.45% (97.94% to 98.46%) | −$29.41 (−$50.85 to $7.81) | −$32.17 (−$53.15 to $7.72) | −$2.30 (−$2.75 to $0.66) | — | $620.70 ($69.00 to $972.70) | $2,009.10 ($1,767.30 to $2,413.70) |
| DTE14 | Hold-10 / DTE≤7 | 2.5-delta (~−0.025) | 3 | 14.07% (11.14% to 14.62%) | 97.67% (95.92% to 100.00%) | 85.11% (83.33% to 89.47%) | 98.19% (97.68% to 98.46%) | −$29.67 (−$50.85 to $7.88) | −$30.08 (−$57.74 to $7.98) | −$6.89 (−$7.44 to $2.19) | — | $1,551.00 ($69.00 to $2,918.10) | $6,027.30 ($5,301.90 to $7,241.10) |
| DTE14 | Hold-10 / DTE≤7 | 5-delta (~−0.05) | 1 | 14.07% (11.14% to 14.62%) | 97.96% (96.43% to 100.00%) | 94.74% (92.86% to 98.15%) | 99.23% (99.22% to 99.74%) | −$18.99 (−$46.49 to $19.06) | −$23.60 (−$49.25 to $18.53) | −$2.76 (−$4.61 to $2.09) | — | $1,098.70 ($69.00 to $1,497.70) | $3,466.10 ($2,959.30 to $3,894.70) |
| DTE14 | Hold-10 / DTE≤7 | 5-delta (~−0.05) | 3 | 14.07% (11.14% to 14.62%) | 97.96% (96.43% to 100.00%) | 92.98% (90.74% to 98.15%) | 99.22% (98.72% to 99.74%) | −$18.45 (−$30.13 to $19.06) | −$28.39 (−$34.97 to $17.48) | −$9.94 (−$18.16 to $6.26) | — | $1,312.10 ($0.00 to $3,547.00) | $10,398.30 ($8,877.90 to $11,684.10) |
| DTE14 | Hold-10 / DTE≤7 | 10-delta (~−0.10) | 1 | 14.07% (11.14% to 14.62%) | 98.21% (97.96% to 100.00%) | 98.18% (95.35% to 100.00%) | 99.74% (99.48% to 100.00%) | −$14.37 (−$28.70 to $19.06) | −$21.16 (−$33.94 to $17.92) | −$5.12 (−$6.79 to $3.57) | — | $1,551.00 ($69.00 to $2,278.70) | $6,680.10 ($5,796.95 to $7,487.70) |
| DTE14 | Hold-10 / DTE≤7 | 10-delta (~−0.10) | 3 | 14.07% (11.14% to 14.62%) | 98.21% (97.96% to 100.00%) | 94.74% (93.02% to 98.18%) | 99.23% (99.22% to 99.74%) | −$18.40 (−$31.41 to $19.06) | −$31.43 (−$37.35 to $15.64) | −$13.63 (−$18.95 to $12.68) | — | $2,466.00 ($69.00 to $3,547.00) | $20,040.30 ($17,390.85 to $22,463.10) |
| DTE14 | Hold-20 / DTE≤7 | 2.5-delta (~−0.025) | 1 | 14.07% (11.14% to 14.62%) | 97.96% (96.43% to 100.00%) | 85.71% (85.19% to 89.47%) | 98.45% (97.94% to 98.46%) | −$29.41 (−$50.85 to $7.81) | −$32.17 (−$53.15 to $7.72) | −$2.30 (−$2.75 to $0.66) | — | $620.70 ($69.00 to $972.70) | $2,009.10 ($1,767.30 to $2,413.70) |
| DTE14 | Hold-20 / DTE≤7 | 2.5-delta (~−0.025) | 3 | 14.07% (11.14% to 14.62%) | 97.67% (95.92% to 100.00%) | 85.11% (83.33% to 89.47%) | 98.19% (97.68% to 98.46%) | −$29.67 (−$50.85 to $7.88) | −$30.08 (−$57.74 to $7.98) | −$6.89 (−$7.44 to $2.19) | — | $1,551.00 ($69.00 to $2,918.10) | $6,027.30 ($5,301.90 to $7,241.10) |
| DTE14 | Hold-20 / DTE≤7 | 5-delta (~−0.05) | 1 | 14.07% (11.14% to 14.62%) | 97.96% (96.43% to 100.00%) | 94.74% (92.86% to 98.15%) | 99.23% (99.22% to 99.74%) | −$18.99 (−$46.49 to $19.06) | −$23.60 (−$49.25 to $18.53) | −$2.76 (−$4.61 to $2.09) | — | $1,098.70 ($69.00 to $1,497.70) | $3,466.10 ($2,959.30 to $3,894.70) |
| DTE14 | Hold-20 / DTE≤7 | 5-delta (~−0.05) | 3 | 14.07% (11.14% to 14.62%) | 97.96% (96.43% to 100.00%) | 92.98% (90.74% to 98.15%) | 99.22% (98.72% to 99.74%) | −$18.45 (−$30.13 to $19.06) | −$28.39 (−$34.97 to $17.48) | −$9.94 (−$18.16 to $6.26) | — | $1,312.10 ($0.00 to $3,547.00) | $10,398.30 ($8,877.90 to $11,684.10) |
| DTE14 | Hold-20 / DTE≤7 | 10-delta (~−0.10) | 1 | 14.07% (11.14% to 14.62%) | 98.21% (97.96% to 100.00%) | 98.18% (95.35% to 100.00%) | 99.74% (99.48% to 100.00%) | −$14.37 (−$28.70 to $19.06) | −$21.16 (−$33.94 to $17.92) | −$5.12 (−$6.79 to $3.57) | — | $1,551.00 ($69.00 to $2,278.70) | $6,680.10 ($5,796.95 to $7,487.70) |
| DTE14 | Hold-20 / DTE≤7 | 10-delta (~−0.10) | 3 | 14.07% (11.14% to 14.62%) | 98.21% (97.96% to 100.00%) | 94.74% (93.02% to 98.18%) | 99.23% (99.22% to 99.74%) | −$18.40 (−$31.41 to $19.06) | −$31.43 (−$37.35 to $15.64) | −$13.63 (−$18.95 to $12.68) | — | $2,466.00 ($69.00 to $3,547.00) | $20,040.30 ($17,390.85 to $22,463.10) |
| DTE45 | Hold-10 / DTE≤7 | 2.5-delta (~−0.025) | 1 | 13.62% (11.37% to 14.40%) | 98.11% (97.92% to 100.00%) | 100.00% (100.00% to 100.00%) | 100.00% (100.00% to 100.00%) | $53.57 ($25.95 to $93.96) | $54.47 ($20.89 to $88.55) | −$1.54 (−$5.41 to $0.90) | — | $791.70 ($623.00 to $1,499.70) | $3,611.80 ($3,127.60 to $3,982.75) |
| DTE45 | Hold-10 / DTE≤7 | 2.5-delta (~−0.025) | 3 | 13.62% (11.37% to 14.40%) | 98.11% (96.23% to 100.00%) | 100.00% (98.18% to 100.00%) | 100.00% (99.74% to 100.00%) | $53.57 ($25.95 to $86.73) | $56.28 ($10.78 to $73.54) | −$4.63 (−$15.17 to $2.71) | — | $2,303.10 ($623.00 to $4,499.10) | $10,791.45 ($9,382.80 to $11,948.25) |
| DTE45 | Hold-10 / DTE≤7 | 5-delta (~−0.05) | 1 | 13.62% (11.37% to 14.40%) | 98.11% (97.92% to 100.00%) | 100.00% (100.00% to 100.00%) | 100.00% (100.00% to 100.00%) | $53.57 ($25.95 to $93.96) | $54.79 ($19.11 to $86.25) | −$1.46 (−$7.71 to $1.23) | — | $1,392.00 ($623.00 to $2,306.70) | $6,149.80 ($5,386.60 to $6,640.75) |
| DTE45 | Hold-10 / DTE≤7 | 5-delta (~−0.05) | 3 | 13.62% (11.37% to 14.40%) | 98.11% (97.92% to 100.00%) | 100.00% (100.00% to 100.00%) | 100.00% (100.00% to 100.00%) | $53.57 ($25.95 to $93.96) | $57.25 ($5.45 to $76.46) | −$4.39 (−$23.12 to $3.68) | — | $3,848.10 ($623.00 to $4,737.00) | $18,449.40 ($16,159.80 to $19,922.25) |
| DTE45 | Hold-10 / DTE≤7 | 10-delta (~−0.10) | 1 | 13.62% (11.37% to 14.40%) | 98.21% (98.11% to 100.00%) | 100.00% (100.00% to 100.00%) | 100.00% (100.00% to 100.00%) | $53.57 ($25.95 to $93.96) | $51.70 ($14.61 to $81.05) | −$3.31 (−$12.91 to $1.41) | — | $2,143.70 ($623.00 to $3,078.70) | $11,864.80 ($10,270.60 to $12,623.75) |
| DTE45 | Hold-10 / DTE≤7 | 10-delta (~−0.10) | 3 | 13.62% (11.37% to 14.40%) | 98.21% (96.23% to 100.00%) | 97.92% (96.15% to 100.00%) | 99.74% (99.49% to 100.00%) | $55.52 ($50.09 to $93.96) | $48.03 ($6.11 to $77.81) | −$8.44 (−$49.41 to $4.92) | — | $4,737.00 ($0.00 to $5,914.00) | $35,594.40 ($30,811.80 to $37,871.25) |
| DTE45 | Hold-20 / DTE≤7 | 2.5-delta (~−0.025) | 1 | 13.54% (11.23% to 14.32%) | 98.11% (97.92% to 100.00%) | 80.39% (76.92% to 85.19%) | 97.40% (96.89% to 97.92%) | $146.91 ($114.39 to $179.81) | $144.17 ($107.75 to $172.66) | −$4.64 (−$7.15 to −$2.74) | −$29.41 | $0.00 ($0.00 to $0.00) | $3,611.80 ($3,127.60 to $3,982.75) |
| DTE45 | Hold-20 / DTE≤7 | 2.5-delta (~−0.025) | 3 | 13.54% (11.23% to 14.32%) | 98.08% (96.23% to 100.00%) | 79.07% (76.47% to 85.19%) | 97.40% (96.89% to 97.92%) | $156.09 ($114.39 to $179.81) | $143.98 ($94.45 to $158.36) | −$13.93 (−$21.45 to −$8.20) | −$87.60 | $0.00 ($0.00 to $0.00) | $10,791.45 ($9,382.80 to $11,948.25) |
| DTE45 | Hold-20 / DTE≤7 | 5-delta (~−0.05) | 1 | 13.54% (11.23% to 14.32%) | 98.11% (97.92% to 100.00%) | 96.15% (93.02% to 98.15%) | 99.48% (99.22% to 99.74%) | $174.89 ($138.09 to $197.15) | $167.01 ($126.28 to $185.01) | −$8.09 (−$12.14 to −$5.59) | −$48.22 | $0.00 ($0.00 to $0.00) | $6,149.80 ($5,386.60 to $6,640.75) |
| DTE45 | Hold-20 / DTE≤7 | 5-delta (~−0.05) | 3 | 13.54% (11.23% to 14.32%) | 98.11% (97.92% to 100.00%) | 94.12% (93.02% to 96.30%) | 99.22% (99.22% to 99.48%) | $174.52 ($138.09 to $194.94) | $153.66 ($102.66 to $159.53) | −$22.61 (−$35.43 to −$16.76) | −$158.67 | $0.00 ($0.00 to $0.00) | $18,449.40 ($16,159.80 to $19,922.25) |
| DTE45 | Hold-20 / DTE≤7 | 10-delta (~−0.10) | 1 | 13.54% (11.23% to 14.32%) | 98.18% (98.08% to 100.00%) | 100.00% (100.00% to 100.00%) | 100.00% (100.00% to 100.00%) | $179.30 ($148.41 to $199.30) | $168.37 ($128.11 to $178.63) | −$13.21 (−$20.67 to −$7.26) | −$79.90 | $0.00 ($0.00 to $0.00) | $11,864.80 ($10,270.60 to $12,623.75) |
| DTE45 | Hold-20 / DTE≤7 | 10-delta (~−0.10) | 3 | 13.54% (11.23% to 14.32%) | 98.18% (96.23% to 100.00%) | 96.30% (93.02% to 98.04%) | 99.48% (99.22% to 99.74%) | $183.77 ($155.64 to $216.20) | $133.35 ($89.98 to $165.54) | −$50.66 (−$65.66 to −$19.44) | −$242.93 | $0.00 ($0.00 to $0.00) | $35,594.40 ($30,811.80 to $37,871.25) |

Modeled opening debit is the tail ask premium plus opening-side modeled friction for triggered entries that pass the displayed ask-size gate. It assumes a possible ask-side fill and is not a verified cash ledger. Outcome coverage below 100% means the conditional realized average is based on a subset; interpret means only with the coverage columns.

## 5. Annual results — DTE45 / Hold-20, 2.5-delta and 5-delta

Per-trade average P&L by realized exit year; each cell is the median across phases. Δ is conditional minus no-hedge mean on matched known outcomes.

| Exit year | Tail | Qty | Outcome N range | Outcome coverage median | Trigger rate median | No-hedge mean matched | Conditional mean matched | Δ mean | Worst-trade improvement | Opening debit median across phases |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2018 | 2.5-delta (~−0.025) | 1 | 34–38 | 97.37% | 11.11% | −$164.23 | −$170.42 | −$4.61 | $0.00 | $174.60 |
| 2018 | 2.5-delta (~−0.025) | 3 | 34–38 | 97.37% | 11.11% | −$164.23 | −$182.82 | −$13.83 | $0.00 | $523.80 |
| 2018 | 5-delta (~−0.05) | 1 | 36–38 | 100.00% | 11.11% | −$147.01 | −$147.09 | −$6.51 | $0.00 | $264.60 |
| 2018 | 5-delta (~−0.05) | 3 | 36–38 | 100.00% | 11.11% | −$147.01 | −$147.27 | −$19.52 | $0.00 | $793.80 |
| 2019 | 2.5-delta (~−0.025) | 1 | 47–49 | 95.92% | 8.00% | $214.54 | $214.54 | −$1.95 | $0.00 | $157.60 |
| 2019 | 2.5-delta (~−0.025) | 3 | 47–49 | 96.00% | 8.00% | $214.54 | $214.54 | −$5.85 | $0.00 | $472.80 |
| 2019 | 5-delta (~−0.05) | 1 | 47–50 | 98.00% | 8.00% | $214.54 | $214.54 | −$5.70 | $0.00 | $267.60 |
| 2019 | 5-delta (~−0.05) | 3 | 47–50 | 98.00% | 8.00% | $214.54 | $214.54 | −$17.11 | $0.00 | $802.80 |
| 2020 | 2.5-delta (~−0.025) | 1 | 46–49 | 96.00% | 17.65% | −$500.48 | −$499.51 | $0.97 | $0.00 | $664.20 |
| 2020 | 2.5-delta (~−0.025) | 3 | 46–49 | 96.00% | 17.65% | −$500.48 | −$497.56 | $2.92 | $0.00 | $1,992.60 |
| 2020 | 5-delta (~−0.05) | 1 | 49–51 | 100.00% | 17.65% | −$418.16 | −$401.25 | −$7.12 | $0.00 | $1,252.85 |
| 2020 | 5-delta (~−0.05) | 3 | 48–51 | 100.00% | 17.65% | −$418.16 | −$367.83 | −$11.43 | $0.00 | $3,758.55 |
| 2021 | 2.5-delta (~−0.025) | 1 | 49–51 | 100.00% | 0.00% | $667.13 | $667.13 | $0.00 | $0.00 | $0.00 |
| 2021 | 2.5-delta (~−0.025) | 3 | 49–51 | 100.00% | 0.00% | $667.13 | $667.13 | $0.00 | $0.00 | $0.00 |
| 2021 | 5-delta (~−0.05) | 1 | 49–51 | 100.00% | 0.00% | $667.13 | $667.13 | $0.00 | $0.00 | $0.00 |
| 2021 | 5-delta (~−0.05) | 3 | 49–51 | 100.00% | 0.00% | $667.13 | $667.13 | $0.00 | $0.00 | $0.00 |
| 2022 | 2.5-delta (~−0.025) | 1 | 47–49 | 96.00% | 40.00% | −$149.71 | −$181.02 | −$25.57 | $0.00 | $1,478.70 |
| 2022 | 2.5-delta (~−0.025) | 3 | 47–49 | 96.00% | 40.00% | −$149.71 | −$235.04 | −$76.70 | $0.00 | $4,436.10 |
| 2022 | 5-delta (~−0.05) | 1 | 49–51 | 100.00% | 40.00% | −$76.08 | −$114.13 | −$40.62 | $0.00 | $2,388.35 |
| 2022 | 5-delta (~−0.05) | 3 | 48–51 | 98.00% | 40.00% | −$76.08 | −$190.24 | −$121.86 | $0.00 | $7,165.05 |
| 2023 | 2.5-delta (~−0.025) | 1 | 47–49 | 97.96% | 10.00% | $324.05 | $321.85 | −$3.34 | $0.00 | $228.25 |
| 2023 | 2.5-delta (~−0.025) | 3 | 47–49 | 97.96% | 10.00% | $324.05 | $317.45 | −$10.01 | $0.00 | $684.75 |
| 2023 | 5-delta (~−0.05) | 1 | 49–50 | 100.00% | 10.00% | $347.27 | $343.79 | −$6.84 | $0.00 | $397.25 |
| 2023 | 5-delta (~−0.05) | 3 | 49–50 | 100.00% | 10.00% | $347.27 | $334.03 | −$20.52 | $0.00 | $1,191.75 |
| 2024 | 2.5-delta (~−0.025) | 1 | 48–51 | 100.00% | 2.08% | $489.05 | $485.91 | −$2.01 | $0.00 | $102.65 |
| 2024 | 2.5-delta (~−0.025) | 3 | 48–51 | 100.00% | 2.08% | $489.05 | $479.61 | −$6.02 | $0.00 | $307.95 |
| 2024 | 5-delta (~−0.05) | 1 | 48–51 | 100.00% | 2.08% | $489.05 | $483.83 | −$3.35 | $0.00 | $177.65 |
| 2024 | 5-delta (~−0.05) | 3 | 48–51 | 100.00% | 2.08% | $489.05 | $473.37 | −$10.06 | $0.00 | $532.95 |
| 2025 | 2.5-delta (~−0.025) | 1 | 45–48 | 100.00% | 14.58% | $186.55 | $185.10 | −$1.45 | $0.00 | $605.90 |
| 2025 | 2.5-delta (~−0.025) | 3 | 44–48 | 100.00% | 14.58% | $207.21 | $184.94 | −$4.34 | $0.00 | $1,817.70 |
| 2025 | 5-delta (~−0.05) | 1 | 47–48 | 100.00% | 14.58% | $214.63 | $197.36 | −$1.46 | $0.00 | $1,060.90 |
| 2025 | 5-delta (~−0.05) | 3 | 47–48 | 100.00% | 14.58% | $214.63 | $183.71 | −$4.39 | $0.00 | $3,182.70 |

These figures are not total yearly dollars, CAGR, NAV change or withdrawal capacity. Rows group trade episodes by realized exit year. The trigger may leave catastrophic losses unhedged when neither condition is active.

## 6. One vs three contracts: expiry stress grid

Intrinsic payoff stress on the SPY short-put sleeve only. The conditional tail is added only when the rule triggers and the entry quote/size gate passes. This is not a historical path replay or probability estimate; it excludes the QQQ long PUT, pre-expiry time value, early exercise/assignment, margin, financing and forced liquidation.

| SPY expiry shock | Tail | Qty | Mean no hedge | Mean unconditional hedge | Mean conditional hedge | Conditional Δ vs no hedge | Worst conditional sleeve | Cohorts improved | Conditional entries median |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0% | 2.5-delta (~−0.025) | 1 | $1,307.57 | $1,253.14 | $1,298.24 | −$9.21 | $361.05 | 0.00% | 52 |
| 0% | 2.5-delta (~−0.025) | 3 | $1,307.57 | $1,144.62 | $1,279.90 | −$27.64 | $361.05 | 0.00% | 51 |
| 0% | 5-delta (~−0.05) | 1 | $1,307.57 | $1,213.35 | $1,291.48 | −$15.69 | $361.05 | 0.00% | 52 |
| 0% | 5-delta (~−0.05) | 3 | $1,307.57 | $1,026.50 | $1,261.38 | −$47.06 | $358.05 | 0.00% | 52 |
| 0% | 10-delta (~−0.10) | 1 | $1,307.57 | $1,128.96 | $1,276.52 | −$30.27 | $361.05 | 0.00% | 52 |
| 0% | 10-delta (~−0.10) | 3 | $1,307.57 | $774.78 | $1,219.63 | −$90.80 | $215.10 | 0.00% | 51 |
| -10% | 2.5-delta (~−0.025) | 1 | −$6,140.07 | −$6,194.98 | −$6,148.11 | −$9.21 | −$14,641.05 | 0.00% | 52 |
| -10% | 2.5-delta (~−0.025) | 3 | −$6,140.07 | −$6,304.79 | −$6,164.19 | −$27.64 | −$14,641.05 | 0.00% | 51 |
| -10% | 5-delta (~−0.05) | 1 | −$6,140.07 | −$6,204.98 | −$6,153.92 | −$15.69 | −$14,641.05 | 0.00% | 52 |
| -10% | 5-delta (~−0.05) | 3 | −$6,140.07 | −$6,332.87 | −$6,181.61 | −$47.06 | −$14,641.05 | 0.00% | 52 |
| -10% | 10-delta (~−0.10) | 1 | −$6,140.07 | −$5,747.35 | −$6,159.19 | −$19.61 | −$14,641.05 | 1.02% | 52 |
| -10% | 10-delta (~−0.10) | 3 | −$6,140.07 | −$4,959.28 | −$6,197.44 | −$58.82 | −$14,636.55 | 1.02% | 51 |
| -20% | 2.5-delta (~−0.025) | 1 | −$18,579.86 | −$17,731.26 | −$18,564.19 | $15.67 | −$34,092.80 | 3.06% | 52 |
| -20% | 2.5-delta (~−0.025) | 3 | −$18,579.86 | −$16,033.25 | −$18,532.86 | $47.00 | −$34,227.15 | 3.06% | 51 |
| -20% | 5-delta (~−0.05) | 1 | −$18,579.86 | −$16,125.83 | −$18,458.56 | $121.30 | −$33,849.15 | 8.42% | 52 |
| -20% | 5-delta (~−0.05) | 3 | −$18,579.86 | −$11,248.35 | −$18,215.97 | $363.89 | −$33,849.15 | 8.42% | 52 |
| -20% | 10-delta (~−0.10) | 1 | −$18,579.86 | −$14,414.76 | −$18,246.24 | $328.50 | −$33,849.15 | 12.05% | 52 |
| -20% | 10-delta (~−0.10) | 3 | −$18,579.86 | −$6,084.57 | −$17,578.99 | $985.51 | −$33,849.15 | 11.79% | 51 |
| -30% | 2.5-delta (~−0.025) | 1 | −$31,016.51 | −$26,594.36 | −$30,691.81 | $306.85 | −$53,627.25 | 10.77% | 52 |
| -30% | 2.5-delta (~−0.025) | 3 | −$31,016.51 | −$17,777.54 | −$30,042.41 | $920.56 | −$53,627.25 | 10.51% | 51 |
| -30% | 5-delta (~−0.05) | 1 | −$31,016.51 | −$24,520.48 | −$30,437.69 | $553.55 | −$53,627.25 | 12.31% | 52 |
| -30% | 5-delta (~−0.05) | 3 | −$31,016.51 | −$11,632.42 | −$29,280.05 | $1,660.65 | −$53,627.25 | 12.31% | 52 |
| -30% | 10-delta (~−0.10) | 1 | −$31,016.51 | −$22,739.92 | −$30,185.71 | $809.10 | −$53,627.25 | 13.08% | 52 |
| -30% | 10-delta (~−0.10) | 3 | −$31,016.51 | −$6,191.27 | −$28,524.11 | $2,427.31 | −$53,627.25 | 12.82% | 51 |
| -40% | 2.5-delta (~−0.025) | 1 | −$43,453.16 | −$34,947.03 | −$42,654.02 | $763.85 | −$74,302.35 | 12.76% | 52 |
| -40% | 2.5-delta (~−0.025) | 3 | −$43,453.16 | −$18,003.04 | −$41,064.91 | $2,291.55 | −$74,302.35 | 12.56% | 51 |
| -40% | 5-delta (~−0.05) | 1 | −$43,453.16 | −$32,840.26 | −$42,371.78 | $1,038.41 | −$74,302.35 | 13.27% | 52 |
| -40% | 5-delta (~−0.05) | 3 | −$43,453.16 | −$11,836.56 | −$40,241.22 | $3,115.24 | −$74,302.35 | 13.27% | 52 |
| -40% | 10-delta (~−0.10) | 1 | −$43,453.16 | −$31,047.36 | −$42,107.45 | $1,301.89 | −$74,302.35 | 13.27% | 52 |
| -40% | 10-delta (~−0.10) | 3 | −$43,453.16 | −$6,288.27 | −$39,450.78 | $3,905.68 | −$74,302.35 | 13.08% | 51 |
| -50% | 2.5-delta (~−0.025) | 1 | −$55,889.80 | −$43,260.34 | −$54,581.64 | $1,251.71 | −$94,977.45 | 13.27% | 52 |
| -50% | 2.5-delta (~−0.025) | 3 | −$55,889.80 | −$18,110.45 | −$52,059.00 | $3,755.12 | −$94,977.45 | 13.08% | 51 |
| -50% | 5-delta (~−0.05) | 1 | −$55,889.80 | −$41,147.69 | −$54,293.52 | $1,531.20 | −$94,977.45 | 13.27% | 52 |
| -50% | 5-delta (~−0.05) | 3 | −$55,889.80 | −$12,025.73 | −$51,220.52 | $4,593.61 | −$94,977.45 | 13.27% | 52 |
| -50% | 10-delta (~−0.10) | 1 | −$55,889.80 | −$39,354.79 | −$54,029.19 | $1,794.68 | −$94,977.45 | 13.27% | 52 |
| -50% | 10-delta (~−0.10) | 3 | −$55,889.80 | −$6,383.76 | −$50,430.07 | $5,384.05 | −$94,977.45 | 13.08% | 51 |
| -100% | 2.5-delta (~−0.025) | 1 | −$118,102.46 | −$84,879.02 | −$114,386.80 | $3,715.66 | −$197,899.95 | 13.27% | 52 |
| -100% | 2.5-delta (~−0.025) | 3 | −$118,102.46 | −$18,559.36 | −$106,955.48 | $11,146.98 | −$197,899.95 | 13.08% | 51 |
| -100% | 5-delta (~−0.05) | 1 | −$118,102.46 | −$82,737.10 | −$114,107.31 | $3,995.15 | −$197,899.95 | 13.27% | 52 |
| -100% | 5-delta (~−0.05) | 3 | −$118,102.46 | −$12,738.21 | −$106,117.00 | $11,985.46 | −$197,899.95 | 13.27% | 52 |
| -100% | 10-delta (~−0.10) | 1 | −$118,102.46 | −$80,891.95 | −$113,843.82 | $4,258.64 | −$197,899.95 | 13.27% | 52 |
| -100% | 10-delta (~−0.10) | 3 | −$118,102.46 | −$6,861.20 | −$105,326.55 | $12,775.91 | −$197,899.95 | 13.08% | 51 |

Three tail PUTs can offset much more of a very severe expiry loss on the three-short-PUT SPY sleeve, but the rule can leave the book exposed when the pre-entry signal is inactive. No sleeve stress result is a portfolio MaxDD guarantee.

## 7. Decision and next gate

1. Keep no hedge as the control. This run is a test of a frozen candidate trigger—not evidence that the trigger is optimal.
2. Compare 2.5-delta/1x as the low-carry conditional arm with 5-delta/1x as the higher-coverage arm. Treat 3x as higher-cost disaster protection, not a return enhancer.
3. The trigger only has value if it reduces modeled insurance spend while improving worst matched losses or predeclared stress outcomes without leaving unacceptable untriggered losses. Do not judge by total debit alone.
4. Any trigger selection should be frozen and evaluated on a later, untouched chronological holdout. Do not tune thresholds using the same years on which it is reported successful.
5. Before deployment, require full QQQ+SPY path, shared NAV, margin/forced liquidation, actual quote/fill evidence, and assignment/early-exercise accounting. None are part of this overlay.

## 8. Reproducible artifacts and caveats

- trigger_flags.csv — entry-time inputs, rolling high, drawdown/Delta flags and rule reasons.
- conditional_trade_level.csv — every base row with action, missing-exit handling, baseline and conditional outcome.
- conditional_summary.csv — each phase/configuration with trigger and outcome coverage, mean P&L, worst trade and modeled entry debit.
- conditional_annual_by_phase.csv and conditional_annual_robustness.csv — annual behavior and phase ranges.
- conditional_stress_grid.csv — no-hedge, unconditional and conditional SPY-sleeve shock scenarios.
- conditional_manifest.json — source/input hashes, rule thresholds, output counts and caveats.
- Original full decision report: [SPY_FAR_TAIL_DECISION_REPORT.md](../spy_far_tail_hedge_v1/SPY_FAR_TAIL_DECISION_REPORT.md).
- The five fixed phases overlap and are not independent samples. Hash pinning proves byte identity against the public Git mirror, not exchange provenance. EOD quotes and displayed sizes are not verified fills.
