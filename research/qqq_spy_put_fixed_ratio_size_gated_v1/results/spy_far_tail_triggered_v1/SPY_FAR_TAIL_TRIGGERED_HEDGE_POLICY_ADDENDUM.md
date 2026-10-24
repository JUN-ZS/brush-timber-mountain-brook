# SPY Far-Tail Triggered Hedge — Whole-Policy Evaluation Addendum V1

This addendum uses the saved trade-level replay, and includes untriggered trades as unchanged base P&L. If a trigger fires but no eligible contract/size is available, the policy leaves that trade unchanged. If a hedge was entered but its exit cannot be validly priced, that trade is marked unknown and excluded from the policy-evaluable sample—not set to zero.

## 1. Whole-policy comparison — DTE45 / Hold-20

The primary mean below includes all resolved trades that can be accounted for under the conditional rule: untriggered/blocked trades use the unchanged base P&L; successfully paired hedges use base plus net tail P&L. Unknown entered hedges are excluded and shown separately. The no-hedge mean is recomputed on the exact same policy-evaluable subset.

| Trigger | Tail | Qty | Trigger rate | Evaluable coverage | Evaluable N range | Base mean on eval set | Conditional policy mean | Incremental mean per eval trade | Worst base→policy | Same worst-base trade improvement | Unknown entered N | Premium spend total / phase median |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3PCT | 2.5-delta (~−0.025) | 1 | 32.90% | 97.91% | 373–379 | $165.68 | $157.72 | −$7.52 | −$21,325.20→−$19,899.50 | $1,452.70 | 8.0 | $6,427.00 |
| Unconditional reference | 2.5-delta (~−0.025) | 1 | Every entry scheduled | 89.38% paired coverage | 340–351 | — | — | −$29.41 per paired trade | −$21,325.20→−$17,162.50 | — | — | — |
| 3PCT | 2.5-delta (~−0.025) | 3 | 32.90% | 97.66% | 373–380 | $166.43 | $142.62 | −$22.56 | −$21,325.20→−$17,048.10 | $4,358.10 | 9.0 | $19,158.00 |
| Unconditional reference | 2.5-delta (~−0.025) | 3 | Every entry scheduled | 89.32% paired coverage | 336–350 | — | — | −$87.60 per paired trade | −$21,325.20→−$9,415.10 | — | — | — |
| 3PCT | 5-delta (~−0.05) | 1 | 32.90% | 99.48% | 381–385 | $176.32 | $166.56 | −$11.05 | −$21,325.20→−$19,084.50 | $2,240.70 | 2.0 | $11,494.00 |
| Unconditional reference | 5-delta (~−0.05) | 1 | Every entry scheduled | 97.66% paired coverage | 370–377 | — | — | −$48.22 per paired trade | −$21,325.20→−$15,965.50 | — | — | — |
| 3PCT | 5-delta (~−0.05) | 3 | 32.90% | 99.22% | 380–385 | $176.32 | $144.42 | −$32.21 | −$21,325.20→−$14,603.10 | $6,722.10 | 3.0 | $34,482.00 |
| Unconditional reference | 5-delta (~−0.05) | 3 | Every entry scheduled | 95.85% paired coverage | 366–374 | — | — | −$158.67 per paired trade | −$20,969.20→−$8,209.10 | — | — | — |
| 5PCT | 2.5-delta (~−0.025) | 1 | 18.13% | 99.22% | 379–383 | $175.07 | $174.33 | −$0.73 | −$21,325.20→−$19,720.50 | $1,604.70 | 3.0 | $3,523.00 |
| Unconditional reference | 2.5-delta (~−0.025) | 1 | Every entry scheduled | 89.38% paired coverage | 340–351 | — | — | −$29.41 per paired trade | −$21,325.20→−$17,162.50 | — | — | — |
| 5PCT | 2.5-delta (~−0.025) | 3 | 18.13% | 98.96% | 379–382 | $180.33 | $178.68 | −$1.64 | −$21,325.20→−$16,593.10 | $4,814.10 | 4.0 | $10,569.00 |
| Unconditional reference | 2.5-delta (~−0.025) | 3 | Every entry scheduled | 89.32% paired coverage | 336–350 | — | — | −$87.60 per paired trade | −$21,325.20→−$9,415.10 | — | — | — |
| 5PCT | 5-delta (~−0.05) | 1 | 18.13% | 99.74% | 381–386 | $178.33 | $178.14 | −$0.04 | −$21,325.20→−$18,961.50 | $2,446.70 | 1.0 | $5,860.00 |
| Unconditional reference | 5-delta (~−0.05) | 1 | Every entry scheduled | 97.66% paired coverage | 370–377 | — | — | −$48.22 per paired trade | −$21,325.20→−$15,965.50 | — | — | — |
| 5PCT | 5-delta (~−0.05) | 3 | 18.13% | 99.48% | 379–386 | $187.12 | $189.57 | −$6.53 | −$20,969.20→−$14,162.10 | $7,163.10 | 2.0 | $17,580.00 |
| Unconditional reference | 5-delta (~−0.05) | 3 | Every entry scheduled | 95.85% paired coverage | 366–374 | — | — | −$158.67 per paired trade | −$20,969.20→−$8,209.10 | — | — | — |

## 2. Annual whole-policy behavior — DTE45 / Hold-20

Calendar year is taken from the frozen base exit date. The five phases are overlapping robustness schedules and are summarized by medians; they are not independent observations.

| Exit year | Trigger | Tail | Qty | Trigger rate | Evaluable coverage | Eval N range | Base mean on eval set | Conditional strategy mean | Incremental mean | Worst base→policy | Same worst-base trade improvement |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2018 | 3PCT | 2.5-delta (~−0.025) | 1 | 36.84% | 100.00% | 36–38 | −$147.01 | −$153.25 | −$12.29 | −$4,090.20→−$4,125.50 | −$24.30 |
| 2018 | 3PCT | 2.5-delta (~−0.025) | 3 | 36.84% | 100.00% | 36–38 | −$147.01 | −$165.73 | −$36.88 | −$4,090.20→−$4,196.10 | −$72.90 |
| 2018 | 3PCT | 5-delta (~−0.05) | 1 | 36.84% | 100.00% | 36–38 | −$147.01 | −$153.41 | −$17.72 | −$4,090.20→−$4,125.50 | −$27.30 |
| 2018 | 3PCT | 5-delta (~−0.05) | 3 | 36.84% | 100.00% | 36–38 | −$147.01 | −$166.23 | −$51.17 | −$4,090.20→−$4,014.10 | −$81.90 |
| 2018 | 5PCT | 2.5-delta (~−0.025) | 1 | 23.68% | 100.00% | 36–38 | −$147.01 | −$152.38 | −$6.32 | −$4,090.20→−$4,106.50 | −$11.30 |
| 2018 | 5PCT | 2.5-delta (~−0.025) | 3 | 23.68% | 100.00% | 36–38 | −$147.01 | −$163.12 | −$18.96 | −$4,090.20→−$4,139.10 | −$33.90 |
| 2018 | 5PCT | 5-delta (~−0.05) | 1 | 23.68% | 100.00% | 36–38 | −$147.01 | −$153.07 | −$8.71 | −$4,090.20→−$4,095.50 | −$1.30 |
| 2018 | 5PCT | 5-delta (~−0.05) | 3 | 23.68% | 100.00% | 36–38 | −$147.01 | −$165.21 | −$26.14 | −$4,090.20→−$4,106.10 | −$3.90 |
| 2019 | 3PCT | 2.5-delta (~−0.025) | 1 | 32.00% | 96.00% | 46–50 | $221.60 | $214.24 | −$7.83 | −$2,612.20→−$2,646.50 | −$34.30 |
| 2019 | 3PCT | 2.5-delta (~−0.025) | 3 | 32.00% | 96.00% | 46–50 | $221.60 | $199.52 | −$23.50 | −$2,612.20→−$2,715.10 | −$102.90 |
| 2019 | 3PCT | 5-delta (~−0.05) | 1 | 32.00% | 100.00% | 48–50 | $236.86 | $222.69 | −$14.17 | −$2,612.20→−$2,653.50 | −$52.30 |
| 2019 | 3PCT | 5-delta (~−0.05) | 3 | 32.00% | 100.00% | 48–50 | $236.86 | $194.35 | −$42.51 | −$2,612.20→−$2,736.10 | −$156.90 |
| 2019 | 5PCT | 2.5-delta (~−0.025) | 1 | 12.00% | 98.00% | 47–50 | $226.33 | $223.47 | −$2.98 | −$2,612.20→−$2,648.50 | −$36.30 |
| 2019 | 5PCT | 2.5-delta (~−0.025) | 3 | 12.00% | 98.00% | 47–50 | $226.33 | $217.75 | −$8.95 | −$2,612.20→−$2,721.10 | −$108.90 |
| 2019 | 5PCT | 5-delta (~−0.05) | 1 | 12.00% | 100.00% | 48–50 | $236.95 | $230.78 | −$6.16 | −$2,612.20→−$2,666.50 | −$54.30 |
| 2019 | 5PCT | 5-delta (~−0.05) | 3 | 12.00% | 100.00% | 48–50 | $236.95 | $218.46 | −$18.49 | −$2,612.20→−$2,775.10 | −$162.90 |
| 2020 | 3PCT | 2.5-delta (~−0.025) | 1 | 39.22% | 94.00% | 46–48 | −$563.39 | −$532.04 | $47.29 | −$21,325.20→−$19,899.50 | $1,452.70 |
| 2020 | 3PCT | 2.5-delta (~−0.025) | 3 | 39.22% | 94.00% | 46–48 | −$563.39 | −$427.91 | $141.86 | −$21,325.20→−$17,048.10 | $4,358.10 |
| 2020 | 3PCT | 5-delta (~−0.05) | 1 | 39.22% | 98.04% | 49–51 | −$430.32 | −$380.76 | $52.74 | −$21,325.20→−$19,084.50 | $2,240.70 |
| 2020 | 3PCT | 5-delta (~−0.05) | 3 | 39.22% | 98.00% | 49–51 | −$418.16 | −$195.33 | $155.87 | −$21,325.20→−$14,603.10 | $6,722.10 |
| 2020 | 5PCT | 2.5-delta (~−0.025) | 1 | 25.49% | 98.00% | 48–50 | −$459.00 | −$412.05 | $46.95 | −$21,325.20→−$19,720.50 | $1,604.70 |
| 2020 | 5PCT | 2.5-delta (~−0.025) | 3 | 25.49% | 98.00% | 47–50 | −$459.00 | −$318.16 | $140.84 | −$21,325.20→−$16,593.10 | $4,814.10 |
| 2020 | 5PCT | 5-delta (~−0.05) | 1 | 25.49% | 100.00% | 49–51 | −$418.16 | −$345.93 | $72.24 | −$21,325.20→−$18,961.50 | $2,446.70 |
| 2020 | 5PCT | 5-delta (~−0.05) | 3 | 25.49% | 98.00% | 49–51 | −$311.04 | −$103.71 | $162.02 | −$20,969.20→−$14,162.10 | $7,163.10 |
| 2021 | 3PCT | 2.5-delta (~−0.025) | 1 | 22.00% | 97.96% | 48–50 | $665.38 | $655.29 | −$10.09 | −$467.20→−$467.20 | $0.00 |
| 2021 | 3PCT | 2.5-delta (~−0.025) | 3 | 22.00% | 97.96% | 48–50 | $665.38 | $635.11 | −$30.27 | −$467.20→−$467.20 | $0.00 |
| 2021 | 3PCT | 5-delta (~−0.05) | 1 | 22.00% | 100.00% | 49–51 | $667.13 | $648.15 | −$18.96 | −$467.20→−$467.20 | $0.00 |
| 2021 | 3PCT | 5-delta (~−0.05) | 3 | 22.00% | 100.00% | 49–51 | $667.13 | $610.21 | −$56.88 | −$467.20→−$505.10 | $0.00 |
| 2021 | 5PCT | 2.5-delta (~−0.025) | 1 | 1.96% | 100.00% | 49–51 | $667.13 | $666.65 | −$0.38 | −$467.20→−$467.20 | $0.00 |
| 2021 | 5PCT | 2.5-delta (~−0.025) | 3 | 1.96% | 100.00% | 49–51 | $667.13 | $665.70 | −$1.14 | −$467.20→−$467.20 | $0.00 |
| 2021 | 5PCT | 5-delta (~−0.05) | 1 | 1.96% | 100.00% | 49–51 | $667.13 | $666.49 | −$0.55 | −$467.20→−$467.20 | $0.00 |
| 2021 | 5PCT | 5-delta (~−0.05) | 3 | 1.96% | 100.00% | 49–51 | $667.13 | $665.21 | −$1.66 | −$467.20→−$467.20 | $0.00 |
| 2022 | 3PCT | 2.5-delta (~−0.025) | 1 | 62.00% | 98.00% | 48–51 | −$71.26 | −$97.63 | −$28.38 | −$6,244.20→−$6,300.50 | −$50.30 |
| 2022 | 3PCT | 2.5-delta (~−0.025) | 3 | 62.00% | 98.00% | 48–51 | −$71.26 | −$150.37 | −$85.13 | −$6,244.20→−$6,413.10 | −$150.90 |
| 2022 | 3PCT | 5-delta (~−0.05) | 1 | 62.00% | 100.00% | 50–51 | −$76.08 | −$113.47 | −$44.21 | −$6,244.20→−$6,315.50 | −$69.30 |
| 2022 | 3PCT | 5-delta (~−0.05) | 3 | 62.00% | 100.00% | 49–50 | −$76.08 | −$188.24 | −$127.31 | −$6,244.20→−$6,458.10 | −$207.90 |
| 2022 | 5PCT | 2.5-delta (~−0.025) | 1 | 48.00% | 98.00% | 49–51 | −$71.26 | −$89.02 | −$18.83 | −$6,244.20→−$6,294.50 | −$50.30 |
| 2022 | 5PCT | 2.5-delta (~−0.025) | 3 | 48.00% | 98.00% | 49–51 | −$71.26 | −$124.54 | −$56.48 | −$6,244.20→−$6,395.10 | −$150.90 |
| 2022 | 5PCT | 5-delta (~−0.05) | 1 | 48.00% | 100.00% | 50–51 | −$76.08 | −$104.13 | −$29.39 | −$6,244.20→−$6,320.50 | −$76.30 |
| 2022 | 5PCT | 5-delta (~−0.05) | 3 | 48.00% | 100.00% | 49–50 | −$76.08 | −$160.93 | −$86.33 | −$6,244.20→−$6,473.10 | −$228.90 |
| 2023 | 3PCT | 2.5-delta (~−0.025) | 1 | 32.00% | 100.00% | 48–50 | $347.27 | $338.56 | −$11.19 | −$2,458.20→−$2,449.50 | −$28.30 |
| 2023 | 3PCT | 2.5-delta (~−0.025) | 3 | 32.00% | 100.00% | 48–50 | $347.27 | $315.81 | −$33.58 | −$2,458.20→−$2,495.10 | −$84.90 |
| 2023 | 3PCT | 5-delta (~−0.05) | 1 | 32.00% | 100.00% | 49–50 | $347.27 | $333.06 | −$18.21 | −$2,458.20→−$2,451.50 | −$41.30 |
| 2023 | 3PCT | 5-delta (~−0.05) | 3 | 32.00% | 100.00% | 49–50 | $347.27 | $290.31 | −$54.64 | −$2,458.20→−$2,534.10 | −$123.90 |
| 2023 | 5PCT | 2.5-delta (~−0.025) | 1 | 12.24% | 100.00% | 49–50 | $347.27 | $343.80 | −$3.78 | −$2,458.20→−$2,458.20 | −$19.30 |
| 2023 | 5PCT | 2.5-delta (~−0.025) | 3 | 12.24% | 100.00% | 49–50 | $347.27 | $336.87 | −$11.33 | −$2,458.20→−$2,458.20 | −$57.90 |
| 2023 | 5PCT | 5-delta (~−0.05) | 1 | 12.24% | 100.00% | 49–50 | $347.27 | $341.68 | −$6.06 | −$2,458.20→−$2,458.20 | −$22.30 |
| 2023 | 5PCT | 5-delta (~−0.05) | 3 | 12.24% | 100.00% | 49–50 | $347.27 | $330.51 | −$18.17 | −$2,458.20→−$2,458.20 | −$66.90 |
| 2024 | 3PCT | 2.5-delta (~−0.025) | 1 | 18.75% | 98.04% | 47–50 | $489.84 | $481.47 | −$8.37 | −$1,784.20→−$1,826.50 | $75.70 |
| 2024 | 3PCT | 2.5-delta (~−0.025) | 3 | 18.75% | 100.00% | 48–51 | $489.05 | $464.43 | −$24.63 | −$1,784.20→−$1,762.10 | $227.10 |
| 2024 | 3PCT | 5-delta (~−0.05) | 1 | 18.75% | 100.00% | 48–50 | $489.84 | $476.17 | −$12.18 | −$1,784.20→−$1,763.50 | $225.70 |
| 2024 | 3PCT | 5-delta (~−0.05) | 3 | 18.75% | 100.00% | 48–50 | $489.84 | $448.82 | −$36.54 | −$1,784.20→−$1,780.10 | $677.10 |
| 2024 | 5PCT | 2.5-delta (~−0.025) | 1 | 8.33% | 100.00% | 48–51 | $489.05 | $485.02 | −$3.64 | −$1,784.20→−$1,816.50 | $0.00 |
| 2024 | 5PCT | 2.5-delta (~−0.025) | 3 | 8.33% | 100.00% | 48–51 | $489.05 | $476.94 | −$10.91 | −$1,784.20→−$1,881.10 | $0.00 |
| 2024 | 5PCT | 5-delta (~−0.05) | 1 | 8.33% | 100.00% | 48–51 | $489.05 | $482.65 | −$5.72 | −$1,784.20→−$1,836.50 | $0.00 |
| 2024 | 5PCT | 5-delta (~−0.05) | 3 | 8.33% | 100.00% | 48–51 | $489.05 | $469.83 | −$17.16 | −$1,784.20→−$1,941.10 | $0.00 |
| 2025 | 3PCT | 2.5-delta (~−0.025) | 1 | 29.79% | 100.00% | 47–48 | $208.84 | $180.70 | −$27.55 | −$5,867.20→−$5,874.50 | −$7.30 |
| 2025 | 3PCT | 2.5-delta (~−0.025) | 3 | 29.79% | 100.00% | 46–48 | $199.30 | $119.24 | −$80.06 | −$5,867.20→−$5,889.10 | −$21.90 |
| 2025 | 3PCT | 5-delta (~−0.05) | 1 | 29.79% | 100.00% | 47–48 | $214.63 | $178.55 | −$36.09 | −$5,867.20→−$5,690.50 | $176.70 |
| 2025 | 3PCT | 5-delta (~−0.05) | 3 | 29.79% | 100.00% | 47–48 | $214.63 | $106.37 | −$108.26 | −$5,867.20→−$5,503.10 | $530.10 |
| 2025 | 5PCT | 2.5-delta (~−0.025) | 1 | 17.02% | 100.00% | 47–48 | $214.63 | $192.76 | −$19.23 | −$5,867.20→−$5,891.50 | −$24.30 |
| 2025 | 5PCT | 2.5-delta (~−0.025) | 3 | 17.02% | 100.00% | 46–48 | $214.63 | $149.00 | −$55.44 | −$5,867.20→−$5,940.10 | −$72.90 |
| 2025 | 5PCT | 5-delta (~−0.05) | 1 | 17.02% | 100.00% | 47–48 | $214.63 | $190.44 | −$24.15 | −$5,867.20→−$5,849.50 | −$8.30 |
| 2025 | 5PCT | 5-delta (~−0.05) | 3 | 17.02% | 100.00% | 47–48 | $214.63 | $142.06 | −$72.45 | −$5,867.20→−$5,814.10 | −$24.90 |

## 3. One vs three contracts on a common whole-policy evaluation set

The 1x and 3x comparison is restricted to the same base trades that are policy-evaluable for both quantities. Untriggered or blocked entries stay at base P&L for both; entered but unpriced hedge positions are excluded from both sides of that common-set comparison.

| Trigger | Tail | Common N range | Base mean | 1x strategy mean | 3x strategy mean | 1x incremental mean | 3x incremental mean | Additional 3x drag/trade | Worst base→1x→3x |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 3PCT | 2.5-delta (~−0.025) | 373–379 | $165.68 | $157.72 | $141.81 | −$7.52 | −$22.56 | −$15.04 | −$21,325.20→−$19,899.50→−$17,048.10 |
| 3PCT | 5-delta (~−0.05) | 380–385 | $176.32 | $166.56 | $144.42 | −$10.74 | −$32.21 | −$21.47 | −$21,325.20→−$19,084.50→−$14,603.10 |
| 5PCT | 2.5-delta (~−0.025) | 379–382 | $180.33 | $179.78 | $178.68 | −$0.55 | −$1.64 | −$1.09 | −$21,325.20→−$19,720.50→−$16,593.10 |
| 5PCT | 5-delta (~−0.05) | 379–386 | $187.12 | $187.94 | $189.57 | −$2.18 | −$6.53 | −$4.35 | −$20,969.20→−$18,522.50→−$14,162.10 |

## 4. Decision readout

- The triggered-paired mean answers whether the hedge leg paid on trades it actually covered. The whole-policy mean answers a different question: what happened across all resolved trades that could be evaluated, including trades that never triggered and therefore stayed unhedged. Both are needed.
- The policy-evaluable coverage denominator is all resolved base trades. Unknown entered hedges are excluded rather than guessed; check their count and coverage before drawing a conclusion.
- A trigger may reduce expected insurance spending without improving average return. Treat positive changes in isolated crash years as protection evidence, not proof of a persistent return stream.
- The trigger rule was predeclared, but it was researched on the same historical period. Holdout/forward validation is still required.
- End-of-day quotes and displayed size do not prove actual fills. The five phases overlap. No complete QQQ+SPY NAV, margin, forced liquidation or assignment model is included.

## 5. Related source artifacts

- [Triggered paired analysis](SPY_FAR_TAIL_TRIGGERED_HEDGE_REPORT.md)
- [Triggered phase summary](triggered_summary.csv)
- [Whole-policy phase summary](triggered_policy_summary.csv)
- [Whole-policy annual results](triggered_policy_annual.csv)
- [Full triggered trade ledger](triggered_trade_level.csv)
- [Unconditional hedge baseline report](../spy_far_tail_hedge_v1/SPY_FAR_TAIL_DECISION_REPORT.md)
