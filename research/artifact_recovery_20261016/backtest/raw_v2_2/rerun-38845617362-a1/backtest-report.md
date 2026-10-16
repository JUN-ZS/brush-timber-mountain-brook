# BACKTEST V2.2 · PROTECTED PUT OVERLAY

Data: 2004-01-02 → 2026-09-04 (5706 bars, 5644 observations)

VXX coverage (context): 2018-01-25 → 2026-09-04 (2165 bars)
Split: TRAIN 2004-03-30 → 2017-09-11 · VAL → 2022-03-07 · OOS 2022-03-08 → 2026-09-04

Official search: **PROTECTED put overlay only** (648 first-wave specs).
QQQ exposure frozen at 100%. DD brake off. Convexity, not de-risk.

Data layer: QQQ/VIX Observed · put **Derived BS(VIX as IV)** · spread **Estimated 10%** · **NOT OPRA**

Benchmark (historical, not this run): CAGR 12.52%  MaxDD -23.51%

## Layers

| Layer | What | FULL CAGR | FULL MaxDD | OOS CAGR | OOS MaxDD | OOS positive days | OOS positive-day rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Observed | QQQ 100% price path | 15.12% | -53.40% | 19.69% | -29.56% | 616/1128 | 54.61% |
| Hypothetical | Daily −1.5% floor toy | 39.65% | -15.04% | 48.85% | -11.34% | 605/1128 | 53.63% |
| Derived | Frozen put overlay | 7.02% | -53.38% | 11.64% | -28.59% | 589/1128 | 52.22% |

Selected structure:
- distance 5.00% OTM · DTE 45d · roll 7d
- PUT CALM 25.00% / UNSTABLE 75.00% / TAIL 75.00% / RECOVERY 25.00% / BUILDING 75.00%
- QQQ exposure 100% all states
- spread 10.00% estimated

| Split | CAGR | MaxDD | Positive / observed days | Positive-day rate | Sharpe | Sortino | ES | Prem drag | Prot. eff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TRAIN | 4.14% | -53.38% | 1810/3387 | 53.44% | 0.34 | 0.47 | -2.26% | 6.65% | 0.00 |
| VALIDATION | 11.38% | -19.46% | 638/1129 | 56.51% | 0.72 | 0.95 | -2.55% | 6.52% | 1.40 |
| OOS | 11.64% | -28.59% | 589/1128 | 52.22% | 0.70 | 1.09 | -2.37% | 5.98% | 0.16 |
| FULL | 7.02% | -53.38% | 3037/5644 | 53.81% | 0.50 | 0.70 | -2.35% | 6.49% | 0.00 |

## Empirical OOS daily-return frequency — no fixed pass/fail threshold
- Derived put overlay: 589/1128 positive-return sessions (52.22%).
- Observed QQQ buy-and-hold: 616/1128 positive-return sessions (54.61%).
- This is a daily positive-return frequency, not an option trade-level win rate or a claim of executable option fills. See the listed-contract quote-side replay for actual option-episode win rates.

OOS leakage: **false** (selection window ends 2022-03-07)
Put cushion guard: **true** (2008-10-15 qqq=-0.0896 overlay=-0.0146)

Do not treat 12.52% / -23.51% as V2.2 output.
