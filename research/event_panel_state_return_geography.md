# Event panel × V2.2 State×Return geography

> QQQ events from 波動 RECENT5Y panel × frozen V2.2 curve. **DESC_ONLY / ASSOCIATION_ONLY**. Credit sealed.

- Event rows joined: **266** · unique days **185** · range 2021-01-08→2026-08-07
- pack `7ca13ce290d28db4` · daily state_key ladder/shape/regime = UNMAPPED (by design)

## Event days vs rest (V2.2 path)

| Slice | n days | mean/day | CAGR | MaxDD | hit+ |
| --- | --- | --- | --- | --- | --- |
| All days in range | 1400 | 0.00041 | 9.19% | -35.24% | 0.5271 |
| Event days | 185 | -0.000186 | -0.84% | -19.87% | 0.4703 |
| Non-event days | 1215 | 0.000501 | 10.14% | -30.15% | 0.5358 |

## Forward windows from event day (compound)

- fwd_1d: n=185 mean=-0.000186 hit+=0.4703
- fwd_5d: n=185 mean=0.001429 hit+=0.5081
- fwd_20d: n=185 mean=0.006124 hit+=0.5405

## By threshold

| thr | n days | mean/day | CAGR | MaxDD |
| --- | --- | --- | --- | --- |
| P80 | 121 | 0.000384 | 0.70% | -14.40% |
| P90 | 67 | -0.000641 | -0.86% | -12.20% |
| P95 | 43 | -0.000515 | -0.49% | -7.91% |
| P99 | 7 | -0.002132 | -0.50% | -3.40% |

## By horizon

| hz | n days | mean/day | CAGR | MaxDD |
| --- | --- | --- | --- | --- |
| DAY | 98 | -0.002263 | -4.09% | -23.30% |
| WEEK | 168 | 0.000158 | 0.28% | -14.28% |

## By run_bin

| run_bin | n days | mean/day | CAGR | MaxDD |
| --- | --- | --- | --- | --- |
| 0-1 | 106 | -8.5e-05 | -0.31% | -13.88% |
| 2-3 | 64 | -0.000876 | -1.09% | -10.39% |
| 4+ | 57 | -0.001111 | -1.26% | -12.19% |

## Threshold × V2.2 regime (n≥5)

| key | n | mean/day | CAGR | MaxDD |
| --- | --- | --- | --- | --- |
| P80|CALM | 40 | 0.001599 | 1.24% | -4.07% |
| P80|RECOVERY | 7 | 0.008862 | 1.53% | -1.17% |
| P80|TAIL | 17 | 0.003331 | 1.32% | -3.72% |
| P80|UNSTABLE | 57 | -0.002389 | -2.55% | -16.30% |
| P90|CALM | 10 | -0.004691 | -0.94% | -5.93% |
| P90|RECOVERY | 10 | 0.001316 | 0.50% | -2.60% |
| P90|TAIL | 12 | -0.001997 | -0.58% | -5.15% |
| P90|UNSTABLE | 35 | 0.000422 | 0.22% | -8.66% |
| P95|TAIL | 16 | 0.001177 | 0.35% | -4.26% |
| P95|UNSTABLE | 21 | -0.003279 | -1.31% | -7.53% |
| P99|TAIL | 5 | -0.00361 | -0.62% | -1.91% |

## Verdict

- Sparse QQQ threshold events vs full calendar — treat as **geography**, not a sleeve.
- Credit / Option EV remain sealed; discovery VALIDATION/OOS still pending on Phase-1 labels.
- Daily state_key lacks ladder/shape/regime — asof panel still needed for full cohort keys.
