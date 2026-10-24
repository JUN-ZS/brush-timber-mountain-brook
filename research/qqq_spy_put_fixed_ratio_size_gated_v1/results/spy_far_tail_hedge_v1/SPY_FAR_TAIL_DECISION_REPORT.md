# SPY Far-Tail Hedge — Full Decision Report V1

> Research-only report generated from completed, source-pinned replay outputs. Report date: 2026-10-24.

## 1. Decision

**Do not adopt unconditional far-tail PUT buying as the default entry overlay on current evidence.** It offsets modeled SPY short-put sleeve losses in severe expiry shocks, but recurring hedge cost reduces average realized P&L in most calendar years. The next experiment should test pre-declared, risk-triggered hedging against the frozen baseline; this report does not authorize live execution.

### Main findings

- DTE45 / Hold-20 / 2.5-delta / 1x: median incremental P&L −$29.41 per paired trade (phase range −$31.55 to −$20.11); paired coverage median 89.38% (88.54–91.41%).
- Comparable 5-delta / 1x: median incremental P&L −$48.22, coverage median 97.66%. Extra drag relative to 2.5-delta is approximately $18.81 per paired episode using the phase medians.
- With 3 contracts, median incremental P&L is −$87.60 (2.5-delta), −$158.67 (5-delta), and −$242.93 (10-delta) per paired episode.
- Phase-median worst paired-trade improvement is $4,534.70 for 2.5-delta / 1x and $13,250.10 for 2.5-delta / 3x. This is trade-level evidence, not portfolio maximum drawdown.
- 2020 is the clearest favorable historical year for the hedge; many other years give back P&L through carry cost. Do not extrapolate a crisis year into a stable annual income estimate.

### Current research status

| Candidate | Assessment |
|---|---|
| Unconditional hedge on every base entry | Not supported by average-P&L evidence |
| 2.5-delta, 1 contract | Lower carry among tested DTE45/Hold-20 cases; lower quote coverage; protection concentrated in deeper shocks |
| 5-delta, 1 contract | Better quote coverage and stronger offset in some moderate/deep shocks, at higher carry |
| 3 contracts | Stronger modeled deep-shock offset; materially larger drag and win-rate impact |
| Live orders | Not performed; out of scope |

## 2. Frozen setup and source lineage

- Baseline anchor commit: [c0cc1de3f196a312c00582d9ee9600c689c388d9](https://github.com/JUN-ZS/brush-timber-mountain-brook/commit/c0cc1de3f196a312c00582d9ee9600c689c388d9). Frozen baseline is QQQ LONG PUT 1 : SPY SHORT PUT 3, no entry filter, fixed 5-common-session cadence.
- Arms: DTE14 and DTE45; exits: Hold 10 or Hold 20, with the DTE≤7 guard.
- Historical SPY chain source: [anahatsingh-ui/options-dataset-hist at 37f6c456fe1a4775c875673fb8ef907d5cd2fd66](https://github.com/anahatsingh-ui/options-dataset-hist/tree/37f6c456fe1a4775c875673fb8ef907d5cd2fd66), with data through 2025-12-12. Hash pinning proves the file bytes match the referenced Git blobs; it does not independently prove OPRA provenance or executable fills.
- Replay size: 7,814 base ledger rows; 3,907 unique cohorts; 23,442 selection rows; 46,884 trade-level rows; 120 phase/config summary rows; 420 expiry stress rows.
- Tail selection: same entry date and expiry as the base SPY short PUT; standard listed PUT; strike strictly below entry spot; valid quote and positive bid. Rank by nearest absolute Delta, then displayed ask size, open interest, relative spread and contract ID.
- 2.5-delta (Put Delta about −0.025) and 5-delta (about −0.05) use the same absolute-Delta band 0.01–0.08. 10-delta (about −0.10) is a reference band 0.05–0.15. Quantities: one or three contracts.
- Modeled friction: $0.05 per option share per side slippage plus $0.65 commission per contract per side. Tail buys enter at ask and exit at bid.

## 3. All tested configurations

Each row reports the median of five phase-level values plus min–max ranges. The shifted entry phases overlap; they are robustness checks, not independent samples. Mean P&L is USD per trade episode, not annual account profit.

| Arm | Exit | Target | Qty | Paired N range | Coverage median (range) | Base mean median (range) | Hedged mean median (range) | Increment median (range) | Win rate base→hedge | Worst paired trade base→hedge | Losing trades improved / turned positive |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DTE14 | Hold 10 / DTE≤7 | 2.5-delta (Put Delta about −0.025) | 1 | 358–364 | 92.78% (91.79–94.04%) | −$50.38 (−$79.55 to −$22.88) | −$72.20 (−$97.85 to −$42.13) | −$19.25 (−$23.48 to −$18.16) | 73.61%→72.35% | −$9,164.20→−$8,297.50 | 17 / 0 |
| DTE14 | Hold 10 / DTE≤7 | 2.5-delta (Put Delta about −0.025) | 3 | 353–361 | 92.27% (90.51–93.52%) | −$42.63 (−$61.38 to −$24.19) | −$112.49 (−$118.47 to −$81.51) | −$57.32 (−$69.86 to −$56.59) | 73.74%→63.69% | −$9,164.20→−$7,056.10 | 17 / 0 |
| DTE14 | Hold 10 / DTE≤7 | 5-delta (about −0.05) | 1 | 374–381 | 97.44% (96.67–97.94%) | −$23.23 (−$54.15 to $8.16) | −$53.66 (−$74.53 to −$15.75) | −$23.91 (−$30.43 to −$18.83) | 75.00%→72.99% | −$9,164.20→−$7,819.50 | 30 / 0 |
| DTE14 | Hold 10 / DTE≤7 | 5-delta (about −0.05) | 3 | 373–379 | 96.63% (95.64–97.68%) | −$21.37 (−$37.93 to $5.78) | −$94.98 (−$112.91 to −$65.32) | −$71.10 (−$91.54 to −$56.30) | 74.80%→58.09% | −$9,164.20→−$4,671.10 | 30 / 0 |
| DTE14 | Hold 10 / DTE≤7 | 10-delta (about −0.10) | 1 | 382–386 | 98.97% (98.72–99.48%) | −$18.14 (−$32.00 to $18.30) | −$52.25 (−$57.61 to −$14.23) | −$32.53 (−$40.25 to −$22.82) | 75.26%→68.65% | −$9,164.20→−$7,193.50 | 50 / 0 |
| DTE14 | Hold 10 / DTE≤7 | 10-delta (about −0.10) | 3 | 375–381 | 98.20% (95.91–98.45%) | −$24.99 (−$34.03 to $21.58) | −$104.69 (−$142.34 to −$78.72) | −$99.70 (−$117.35 to −$66.16) | 75.59%→35.96% | −$9,164.20→−$3,779.10 | 50 / 3 |
| DTE14 | Hold 20 / DTE≤7 | 2.5-delta (Put Delta about −0.025) | 1 | 358–364 | 92.78% (91.79–94.04%) | −$50.38 (−$79.55 to −$22.88) | −$72.20 (−$97.85 to −$42.13) | −$19.25 (−$23.48 to −$18.16) | 73.61%→72.35% | −$9,164.20→−$8,297.50 | 17 / 0 |
| DTE14 | Hold 20 / DTE≤7 | 2.5-delta (Put Delta about −0.025) | 3 | 353–361 | 92.27% (90.51–93.52%) | −$42.63 (−$61.38 to −$24.19) | −$112.49 (−$118.47 to −$81.51) | −$57.32 (−$69.86 to −$56.59) | 73.74%→63.69% | −$9,164.20→−$7,056.10 | 17 / 0 |
| DTE14 | Hold 20 / DTE≤7 | 5-delta (about −0.05) | 1 | 374–381 | 97.44% (96.67–97.94%) | −$23.23 (−$54.15 to $8.16) | −$53.66 (−$74.53 to −$15.75) | −$23.91 (−$30.43 to −$18.83) | 75.00%→72.99% | −$9,164.20→−$7,819.50 | 30 / 0 |
| DTE14 | Hold 20 / DTE≤7 | 5-delta (about −0.05) | 3 | 373–379 | 96.63% (95.64–97.68%) | −$21.37 (−$37.93 to $5.78) | −$94.98 (−$112.91 to −$65.32) | −$71.10 (−$91.54 to −$56.30) | 74.80%→58.09% | −$9,164.20→−$4,671.10 | 30 / 0 |
| DTE14 | Hold 20 / DTE≤7 | 10-delta (about −0.10) | 1 | 382–386 | 98.97% (98.72–99.48%) | −$18.14 (−$32.00 to $18.30) | −$52.25 (−$57.61 to −$14.23) | −$32.53 (−$40.25 to −$22.82) | 75.26%→68.65% | −$9,164.20→−$7,193.50 | 50 / 0 |
| DTE14 | Hold 20 / DTE≤7 | 10-delta (about −0.10) | 3 | 375–381 | 98.20% (95.91–98.45%) | −$24.99 (−$34.03 to $21.58) | −$104.69 (−$142.34 to −$78.72) | −$99.70 (−$117.35 to −$66.16) | 75.59%→35.96% | −$9,164.20→−$3,779.10 | 50 / 3 |
| DTE45 | Hold 10 / DTE≤7 | 2.5-delta (Put Delta about −0.025) | 1 | 385–388 | 99.48% (99.23–99.74%) | $50.81 ($44.53 to $91.85) | $27.55 ($18.25 to $62.62) | −$26.62 (−$29.23 to −$23.26) | 75.32%→73.25% | −$11,219.20→−$9,719.50 | 31 / 0 |
| DTE45 | Hold 10 / DTE≤7 | 2.5-delta (Put Delta about −0.025) | 3 | 383–385 | 98.97% (98.46–99.48%) | $50.81 ($43.54 to $86.91) | −$18.96 (−$34.05 to −$0.57) | −$79.86 (−$87.48 to −$69.78) | 75.26%→70.39% | −$11,219.20→−$7,550.10 | 31 / 0 |
| DTE45 | Hold 10 / DTE≤7 | 5-delta (about −0.05) | 1 | 384–388 | 99.48% (98.97–99.74%) | $50.81 ($44.53 to $91.85) | $19.54 ($12.28 to $52.20) | −$35.38 (−$39.65 to −$31.27) | 75.32%→72.68% | −$11,219.20→−$8,968.50 | 44 / 0 |
| DTE45 | Hold 10 / DTE≤7 | 5-delta (about −0.05) | 3 | 380–385 | 98.20% (98.19–98.97%) | $62.31 ($47.96 to $87.22) | −$39.33 (−$51.19 to −$30.58) | −$107.75 (−$117.79 to −$94.71) | 75.39%→66.84% | −$11,219.20→−$5,903.10 | 43 / 0 |
| DTE45 | Hold 10 / DTE≤7 | 10-delta (about −0.10) | 1 | 386–388 | 99.74% (99.48–99.74%) | $52.94 ($45.97 to $91.85) | $4.51 (−$0.94 to $31.73) | −$52.37 (−$60.12 to −$46.91) | 75.39%→71.83% | −$11,219.20→−$8,295.50 | 60 / 0 |
| DTE45 | Hold 10 / DTE≤7 | 10-delta (about −0.10) | 3 | 382–387 | 98.97% (98.45–99.49%) | $75.06 ($49.68 to $88.39) | −$90.66 (−$101.02 to −$81.06) | −$157.75 (−$179.05 to −$141.33) | 75.39%→48.69% | −$11,219.20→−$3,884.10 | 60 / 1 |
| DTE45 | Hold 20 / DTE≤7 | 2.5-delta (Put Delta about −0.025) | 1 | 340–351 | 89.38% (88.54–91.41%) | $99.45 ($66.73 to $143.12) | $69.00 ($46.62 to $113.71) | −$29.41 (−$31.55 to −$20.11) | 80.00%→79.30% | −$21,325.20→−$17,162.50 | 12 / 0 |
| DTE45 | Hold 20 / DTE≤7 | 2.5-delta (Put Delta about −0.025) | 3 | 336–350 | 89.32% (87.50–91.15%) | $109.20 ($74.86 to $139.06) | $18.05 (−$0.62 to $51.46) | −$87.60 (−$94.66 to −$56.80) | 80.17%→78.43% | −$21,325.20→−$9,415.10 | 12 / 0 |
| DTE45 | Hold 20 / DTE≤7 | 5-delta (about −0.05) | 1 | 370–377 | 97.66% (96.61–98.18%) | $157.37 ($141.34 to $185.03) | $108.07 ($102.90 to $136.81) | −$48.22 (−$53.28 to −$38.44) | 81.87%→81.07% | −$21,325.20→−$15,965.50 | 24 / 0 |
| DTE45 | Hold 20 / DTE≤7 | 5-delta (about −0.05) | 3 | 366–374 | 95.85% (95.56–97.40%) | $178.34 ($150.49 to $211.91) | $31.85 ($2.80 to $43.58) | −$158.67 (−$172.25 to −$142.83) | 82.26%→77.93% | −$20,969.20→−$8,209.10 | 23 / 0 |
| DTE45 | Hold 20 / DTE≤7 | 10-delta (about −0.10) | 1 | 381–384 | 99.48% (99.22–99.74%) | $175.32 ($156.66 to $189.73) | $93.00 ($83.79 to $107.11) | −$79.90 (−$86.16 to −$72.87) | 82.20%→80.84% | −$21,325.20→−$14,488.50 | 36 / 0 |
| DTE45 | Hold 20 / DTE≤7 | 10-delta (about −0.10) | 3 | 373–380 | 98.45% (97.39–98.70%) | $181.82 ($166.99 to $254.84) | −$57.81 (−$81.64 to −$36.90) | −$242.93 (−$291.74 to −$223.16) | 82.35%→67.29% | −$21,325.20→−$5,004.10 | 35 / 1 |

Interpretation:

- The main average comparison uses only resolved base trades with a quote-valid tail entry and exact-contract exit with sufficient displayed bid size. Coverage is less than 100% in some configurations, so quote-availability selection bias remains possible.
- Base and hedged means in each row use the same paired trades. All-resolved baseline means are shown separately in the annual CSV and must not be compared directly with a paired hedged mean.
- Worst-trade values are minima within the paired sample. A hedge can improve the worst trade while lowering the mean and win rate.
- DTE14 Hold-10 and Hold-20 can produce identical outcomes where the DTE≤7 guard overrides the earlier hold limit.

## 4. Annual comparison — DTE45 / Hold-20, 2.5-delta vs 5-delta

Figures are medians across the five entry phases for each exit year, based on paired realized observations. Delta P&L = hedged minus no-hedge mean; positive is improvement and negative is carry drag.

| Exit year | Target | Qty | Paired N range | Coverage median | No-hedge mean | Hedged mean | Delta mean P&L | Worst paired trade base→hedge |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 2018 | 2.5-delta (Put Delta about −0.025) | 1 | 31–37 | 89.47% | −$230.76 | −$262.26 | −$31.01 | −$4,090.20→−$4,036.50 |
| 2018 | 2.5-delta (Put Delta about −0.025) | 3 | 31–36 | 89.47% | −$230.76 | −$325.28 | −$93.02 | −$4,090.20→−$3,929.10 |
| 2018 | 5-delta (about −0.05) | 1 | 35–38 | 97.37% | −$177.34 | −$210.84 | −$36.27 | −$4,090.20→−$3,798.50 |
| 2018 | 5-delta (about −0.05) | 3 | 35–38 | 97.37% | −$154.62 | −$263.35 | −$108.73 | −$4,090.20→−$3,240.10 |
| 2019 | 2.5-delta (Put Delta about −0.025) | 1 | 34–38 | 73.47% | $128.12 | $92.45 | −$35.27 | −$2,612.20→−$2,633.50 |
| 2019 | 2.5-delta (Put Delta about −0.025) | 3 | 34–38 | 73.47% | $128.12 | $21.11 | −$105.82 | −$2,612.20→−$2,676.10 |
| 2019 | 5-delta (about −0.05) | 1 | 44–48 | 94.00% | $202.28 | $149.98 | −$53.19 | −$2,612.20→−$2,606.50 |
| 2019 | 5-delta (about −0.05) | 3 | 44–48 | 94.00% | $202.28 | $45.38 | −$159.58 | −$2,612.20→−$2,595.10 |
| 2020 | 2.5-delta (Put Delta about −0.025) | 1 | 41–45 | 88.00% | −$649.69 | −$537.77 | $128.45 | −$21,325.20→−$17,162.50 |
| 2020 | 2.5-delta (Put Delta about −0.025) | 3 | 41–45 | 88.00% | −$649.69 | −$280.87 | $385.35 | −$21,325.20→−$9,415.10 |
| 2020 | 5-delta (about −0.05) | 1 | 48–50 | 96.00% | −$472.72 | −$337.66 | $135.06 | −$21,325.20→−$15,965.50 |
| 2020 | 5-delta (about −0.05) | 3 | 46–50 | 94.00% | −$403.35 | −$67.54 | $306.50 | −$20,969.20→−$8,209.10 |
| 2021 | 2.5-delta (Put Delta about −0.025) | 1 | 43–48 | 91.84% | $665.07 | $604.82 | −$59.54 | −$467.20→−$487.50 |
| 2021 | 2.5-delta (Put Delta about −0.025) | 3 | 42–48 | 90.20% | $665.07 | $477.94 | −$178.63 | −$467.20→−$528.10 |
| 2021 | 5-delta (about −0.05) | 1 | 47–50 | 97.96% | $664.43 | $567.34 | −$97.10 | −$467.20→−$493.50 |
| 2021 | 5-delta (about −0.05) | 3 | 45–48 | 94.12% | $664.59 | $371.77 | −$292.09 | −$467.20→−$546.10 |
| 2022 | 2.5-delta (Put Delta about −0.025) | 1 | 43–49 | 94.00% | −$149.71 | −$210.28 | −$60.57 | −$6,244.20→−$6,269.50 |
| 2022 | 2.5-delta (Put Delta about −0.025) | 3 | 43–49 | 94.00% | −$149.71 | −$331.41 | −$181.70 | −$6,244.20→−$6,320.10 |
| 2022 | 5-delta (about −0.05) | 1 | 47–51 | 98.00% | −$149.71 | −$227.97 | −$78.26 | −$6,244.20→−$6,032.50 |
| 2022 | 5-delta (about −0.05) | 3 | 47–51 | 96.00% | −$153.77 | −$379.36 | −$230.96 | −$6,244.20→−$5,285.10 |
| 2023 | 2.5-delta (Put Delta about −0.025) | 1 | 44–48 | 92.00% | $294.69 | $247.15 | −$47.73 | −$2,458.20→−$2,488.50 |
| 2023 | 2.5-delta (Put Delta about −0.025) | 3 | 44–48 | 92.00% | $294.69 | $152.07 | −$143.20 | −$2,458.20→−$2,549.10 |
| 2023 | 5-delta (about −0.05) | 1 | 48–50 | 100.00% | $347.27 | $266.83 | −$78.91 | −$2,458.20→−$2,486.50 |
| 2023 | 5-delta (about −0.05) | 3 | 48–50 | 100.00% | $348.36 | $105.96 | −$236.74 | −$2,458.20→−$2,543.10 |
| 2024 | 2.5-delta (Put Delta about −0.025) | 1 | 47–51 | 98.00% | $489.05 | $436.87 | −$51.60 | −$1,784.20→−$1,826.50 |
| 2024 | 2.5-delta (Put Delta about −0.025) | 3 | 47–51 | 97.92% | $489.05 | $332.51 | −$154.79 | −$1,784.20→−$1,747.10 |
| 2024 | 5-delta (about −0.05) | 1 | 48–51 | 100.00% | $489.05 | $407.28 | −$78.84 | −$1,784.20→−$1,674.50 |
| 2024 | 5-delta (about −0.05) | 3 | 47–51 | 98.00% | $489.05 | $243.74 | −$235.54 | −$1,784.20→−$1,645.10 |
| 2025 | 2.5-delta (Put Delta about −0.025) | 1 | 44–46 | 95.83% | $153.50 | $87.00 | −$65.21 | −$5,867.20→−$5,872.50 |
| 2025 | 2.5-delta (Put Delta about −0.025) | 3 | 43–46 | 93.75% | $191.71 | $11.92 | −$179.78 | −$5,867.20→−$5,883.10 |
| 2025 | 5-delta (about −0.05) | 1 | 46–48 | 100.00% | $197.99 | $98.03 | −$89.97 | −$5,867.20→−$5,522.50 |
| 2025 | 5-delta (about −0.05) | 3 | 46–47 | 97.92% | $227.43 | −$47.32 | −$274.75 | −$5,867.20→−$5,059.10 |

These are per-trade averages grouped by exit year, not total yearly USD, account returns, CAGR or withdrawal capacity. Paired sample sizes vary by target and quantity.

## 5. Expiry shock grid — SPY short-put sleeve only

This is an intrinsic payoff scenario from each entry spot to expiry—not a historical path replay, forecast or probability. It excludes QQQ long-PUT payoff, exit time value, assignment/exercise fees, financing, margin and forced liquidation. Figures are phase medians.

| SPY shock at expiry | Target | Qty | Mean unhedged sleeve | Mean hedged sleeve | Increment | Worst unhedged→hedged | Phases improved |
|---:|---|---:|---:|---:|---:|---:|---:|
| -10% | 2.5-delta (Put Delta about −0.025) | 1 | −$6,117.21 | −$6,172.40 | −$55.34 | −$14,442.75→−$14,522.40 | 0.00% |
| -10% | 2.5-delta (Put Delta about −0.025) | 3 | −$6,117.21 | −$6,282.78 | −$165.57 | −$14,442.75→−$14,681.70 | 0.00% |
| -10% | 5-delta (about −0.05) | 1 | −$6,117.21 | −$6,182.45 | −$61.85 | −$14,442.75→−$14,576.40 | 8.48% |
| -10% | 5-delta (about −0.05) | 3 | −$6,111.18 | −$6,306.49 | −$184.80 | −$14,442.75→−$14,843.70 | 8.57% |
| -10% | 10-delta (about −0.10) | 1 | −$6,120.59 | −$5,726.86 | $387.10 | −$14,442.75→−$13,752.00 | 55.38% |
| -10% | 10-delta (about −0.10) | 3 | −$6,125.93 | −$4,941.56 | $1,164.34 | −$14,442.75→−$14,439.30 | 55.41% |
| -20% | 2.5-delta (Put Delta about −0.025) | 1 | −$18,540.81 | −$17,690.04 | $853.94 | −$34,008.15→−$33,662.00 | 60.57% |
| -20% | 2.5-delta (Put Delta about −0.025) | 3 | −$18,519.57 | −$15,959.90 | $2,561.81 | −$34,008.15→−$33,843.30 | 60.57% |
| -20% | 5-delta (about −0.05) | 1 | −$18,540.81 | −$16,072.19 | $2,468.13 | −$34,008.15→−$30,890.40 | 90.46% |
| -20% | 5-delta (about −0.05) | 3 | −$18,516.58 | −$11,113.60 | $7,425.87 | −$34,008.15→−$26,457.90 | 90.41% |
| -20% | 10-delta (about −0.10) | 1 | −$18,540.81 | −$14,365.06 | $4,175.75 | −$34,008.15→−$27,107.20 | 98.46% |
| -20% | 10-delta (about −0.10) | 3 | −$18,540.81 | −$5,993.77 | $12,527.25 | −$34,008.15→−$20,889.90 | 98.45% |
| -30% | 2.5-delta (Put Delta about −0.025) | 1 | −$30,960.14 | −$26,526.68 | $4,433.46 | −$53,627.25→−$47,366.00 | 96.13% |
| -30% | 2.5-delta (Put Delta about −0.025) | 3 | −$30,938.67 | −$17,646.97 | $13,306.86 | −$53,627.25→−$39,723.90 | 96.12% |
| -30% | 5-delta (about −0.05) | 1 | −$30,960.14 | −$24,447.49 | $6,540.15 | −$53,627.25→−$43,328.40 | 98.97% |
| -30% | 5-delta (about −0.05) | 3 | −$30,946.48 | −$11,374.89 | $19,624.10 | −$53,627.25→−$32,652.90 | 98.96% |
| -30% | 10-delta (about −0.10) | 1 | −$30,960.14 | −$22,662.39 | $8,308.05 | −$53,627.25→−$40,437.80 | 99.74% |
| -30% | 10-delta (about −0.10) | 3 | −$30,960.66 | −$6,041.06 | $24,913.83 | −$53,627.25→−$20,889.90 | 99.74% |
| -50% | 2.5-delta (Put Delta about −0.025) | 1 | −$55,893.46 | −$43,190.14 | $12,689.70 | −$94,977.45→−$73,718.60 | 100.00% |
| -50% | 2.5-delta (Put Delta about −0.025) | 3 | −$55,834.40 | −$17,783.51 | $38,056.22 | −$94,977.45→−$45,252.90 | 100.00% |
| -50% | 5-delta (about −0.05) | 1 | −$55,893.46 | −$41,047.08 | $14,832.56 | −$94,977.45→−$69,787.60 | 100.00% |
| -50% | 5-delta (about −0.05) | 3 | −$55,874.92 | −$11,400.68 | $44,478.66 | −$94,977.45→−$32,652.90 | 100.00% |
| -50% | 10-delta (about −0.10) | 1 | −$55,865.02 | −$39,228.51 | $16,612.89 | −$94,977.45→−$66,534.60 | 100.00% |
| -50% | 10-delta (about −0.10) | 3 | −$55,916.31 | −$6,043.39 | $49,789.24 | −$94,977.45→−$20,889.90 | 100.00% |
| -100% | 2.5-delta (Put Delta about −0.025) | 1 | −$118,131.51 | −$84,682.18 | $33,449.33 | −$198,352.95→−$141,455.60 | 100.00% |
| -100% | 2.5-delta (Put Delta about −0.025) | 3 | −$118,080.69 | −$17,783.51 | $100,302.52 | −$198,352.95→−$45,252.90 | 100.00% |
| -100% | 5-delta (about −0.05) | 1 | −$118,131.51 | −$82,552.93 | $35,578.58 | −$198,352.95→−$138,018.60 | 100.00% |
| -100% | 5-delta (about −0.05) | 3 | −$118,097.49 | −$11,400.68 | $106,701.23 | −$198,352.95→−$32,652.90 | 100.00% |
| -100% | 10-delta (about −0.10) | 1 | −$118,151.34 | −$80,783.21 | $37,368.13 | −$198,352.95→−$135,084.60 | 100.00% |
| -100% | 10-delta (about −0.10) | 3 | −$118,166.04 | −$6,043.39 | $112,004.26 | −$198,352.95→−$20,889.90 | 100.00% |

The very far-OTM PUT may not offset its carrying cost in a modest decline; its modeled payoff grows only after spot crosses the tail strike. Three long PUTs align with the three short SPY PUTs and have a much larger deep-shock offset, but cost more and do not make the full QQQ/SPY book safe.

## 6. Findings and next research gate

1. **No unconditional hedge default yet.** In DTE45/Hold-20, median incremental P&L across phases is negative for all tested Delta targets at both sizes over the full sample.
2. **2.5-delta / 1x is the lower-carry candidate, not a proven winner.** It generally drags less average P&L but has lower paired coverage and is less effective before a deeper fall.
3. **5-delta / 1x is a reasonable comparator.** Its extra carry should only be accepted if the extra realized or scenario downside offset is worth it to the user’s risk budget.
4. **Three contracts behave more like disaster insurance than return enhancement.** They improve more severe expiry shock results while materially reducing average P&L and, often, win rate.
5. **Next experiment:** evaluate pre-declared risk-triggered hedge rules against no hedge and unconditional 1x candidates. Do not tune on the same years used to claim success; report protected vs unprotected years, hedge spend, quote coverage, worst trade and portfolio NAV/margin before any deployment decision.

## 7. Limitations

- End-of-day quotes and displayed sizes are not verified fills; a size gate is not execution evidence.
- Unresolved base trades remain unresolved; tail marks are not silently counted as realized P&L.
- Hashes prove byte identity against a Git mirror, not OPRA authenticity.
- No shared NAV, concurrent-position allocation, margin calls, forced liquidation or assignment/early-exercise cost is modeled.
- The stress grid covers only the SPY short-put sleeve, not the whole strategy's maximum drawdown.

## 8. Reproducible artifacts

- [Phase-level configuration summary](summary.csv)
- [Matched trade-level ledger](trade_level.csv)
- [Exact selected contracts and quote-size gates](entry_selection.csv)
- [SPY expiry shock grid](stress_grid.csv)
- [Year × phase × configuration values](annual_pnl_by_phase.csv)
- [Annual phase robustness ranges](annual_pnl_robustness.csv)
- [Annual summary report](annual_pnl_report.md)
- [Completed replay Actions run](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/40088228452)
- [Annual summary Actions run](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/40089381454)

## 9. Core decision table — DTE45 / Hold-20

| Target | Qty | Base paired mean | Hedged paired mean | Increment | Coverage median | Worst trade improvement |
|---|---:|---:|---:|---:|---:|---:|
| 2.5-delta (Put Delta about −0.025) | 1 | $99.45 | $69.00 | −$29.41 | 89.38% | $4,534.70 |
| 2.5-delta (Put Delta about −0.025) | 3 | $109.20 | $18.05 | −$87.60 | 89.32% | $13,250.10 |
| 5-delta (about −0.05) | 1 | $157.37 | $108.07 | −$48.22 | 97.66% | $5,503.70 |
| 5-delta (about −0.05) | 3 | $178.34 | $31.85 | −$158.67 | 95.85% | $14,792.10 |
| 10-delta (about −0.10) | 1 | $175.32 | $93.00 | −$79.90 | 99.48% | $6,906.70 |
| 10-delta (about −0.10) | 3 | $181.82 | −$57.81 | −$242.93 | 98.45% | $16,206.10 |

Frozen replay baseline: c0cc1de3f196a312c00582d9ee9600c689c388d9. Source chain through 2025-12-12. This research report does not place or recommend live orders.
