# BACKTEST V2.1

Data: 2004-01-02 → 2026-09-04 (5706 bars, 5644 observations)

VXX coverage: 2018-01-25 → 2026-09-04 (2165 bars, first adj close 1770.24)
Missing VXX bars = 0 return in QQQ_VXX. Official window was NOT shrunk.

Split: TRAIN 2004-03-30 → 2017-09-11 · VAL → 2022-03-07 · OOS 2022-03-08 → 2026-09-04

Benchmark (historical, not this run): CAGR 12.52%  MaxDD -23.51%

## Layers

| Layer | What | CAGR | MaxDD | OOS CAGR | OOS MaxDD | Gate |
| --- | --- | --- | --- | --- | --- | --- |
| Observed | QQQ 100% price path | 15.12% | -53.40% | 19.69% | -29.56% | FAIL |
| Derived | Frozen spot QQQ | 0.81% | -5.64% | 0.42% | -4.56% | FAIL |
| Hypothetical | Frozen CONVEX_PROXY | 66.74% | -4.26% | 118.46% | -1.80% | PASS |

Observed QQQ 100% (no overlay):
- TRAIN 11.95% / -53.40%
- VALIDATION 20.41% / -28.56%
- OOS 19.69% / -29.56%
- FULL 15.12% / -53.40%

Selected Strategy (all 5 compete on validation only): **CONVEX_PROXY**
Kind: **HYPOTHETICAL OPTION PROXY** — 5.5bps/day debit toy, not OPRA

Selected Policy:
- CALM 100.00%
- UNSTABLE 65.00%
- TAIL 10.00%
- RECOVERY 70.00%
- VXX hedge 0.00%
- DD brake 3.50%

| Split | CAGR | MaxDD | Sharpe | Sortino | ES | nDays |
| --- | --- | --- | --- | --- | --- | --- |
| TRAIN | 48.68% | -4.26% | 4.80 | 183.87 | -0.06% | 3387 |
| VALIDATION | 79.54% | -3.68% | 5.89 | 272.27 | -0.05% | 1129 |
| OOS | 118.46% | -1.80% | 6.73 | 347.76 | -0.05% | 1128 |
| FULL | 66.74% | -4.26% | 5.43 | 235.13 | -0.06% | 5644 |

TARGET (OOS only, official champion):
- CAGR >= 12%: PASS (118.46%)
- MaxDD >= -5%: PASS (-1.80%)
- FINAL: **PASS** (HYPOTHETICAL PROXY — not a tradable result)

Spot-only frozen champion (QQQ / QQQ_VXX, same freeze): **QQQ**
- VAL 2.94% / -4.68%
- OOS 0.42% / -4.56%
- Gate: **FAIL**
- Policy: unst 35.00% tail 2.00% hedge 0.00% brake 1.50%

OOS leakage: **false** (selection window ends 2022-03-07)
vxxHedge live: **true** (sample 2018-01-29: hedge0=-0.004856 hedge18=-0.017350)

Do not treat 12.52% / -23.51% as V2.1 output.
