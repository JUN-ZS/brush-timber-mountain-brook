# Original Hybrid Policy-Fidelity Audit

As of 2026-10-25. Research only; separate branch; no strategy/live sizing change.

## Key conclusion

The replay in \`research/qqq_hybrid_dynamic_deployment_v1_1_replay.py\` has been successfully reproduced against its prior PR #98 result. That proves **internal simulator reproducibility**, not exact fidelity to the recovered Original Hybrid policy in \`JUN-ZS/timber-blade-kind-dawn/src/engine/policy.ts\`.

The recovered policy and the replay function differ in several economically material ways. Therefore the 12.7530% / 12.9710% results below are diagnostic outputs of the preserved simulator, not a re-certification of the prior Original Hybrid reference (12.7049% CAGR / -23.1837% daily MTM MaxDD / $276,508 terminal NAV).

## Source-level differences

| Behavior | Recovered source policy (\`src/engine/policy.ts\`) | Current preserved replay (\`research/qqq_hybrid_dynamic_deployment_v1_1_replay.py\`) | Impact |
|---|---|---|---|
| QQQ call-credit risk | 0.8% normally; 1.2% when \`rQ > 0.006\` or \`hv20q > 0.22\` | Legacy baseline opens every QQQ call-credit at 0.8%; the dynamic variant follows a separate downshift state machine | Risk size and premium income differ |
| QQQ call-credit during Shock | Shock decision returns only 42% QQQ core exposure; QQQ call-credit target is zero | Baseline still opens a 0.8% QQQ call-credit spread in the Shock state; V1.1 has its own path-dependent deployment gate | Adds short-call exposure when source policy would target none |
| VXX short-stock notional | 18% NAV when VIX < 28; 10% NAV otherwise | Replay opens VXX short stock at 18% whenever its \`wantV\` gate passes | High-VIX, non-Shock days can be oversized versus policy |
| VXX seller response to a QQQ Shock day | The recovered state classifier treats QQQ daily return < -3% as Shock; terminal policy says reduce VXX seller legs first | Existing VXX short exit test checks VXX daily rise >6%, VIX >35, term proxy <0, DTE, or loss; it does not explicitly exit on QQQ daily return < -3% | Existing VXX short may persist through a QQQ-triggered Shock if no other exit fires |
| Term structure | \`termSlope(VIX, VIX_MA20)\` is a synthetic proxy, not observed VX futures | The replay uses the same VIX/20-session-mean proxy | The run cannot validate historical real-VX M1/M2 behavior |
| Option prices | Black–Scholes estimates with modeled spreads | Black–Scholes/VIX-derived marks with modeled spread haircuts | These are not OPRA history or verified executable fills |

Source references:
- Recovered original policy: https://github.com/JUN-ZS/timber-blade-kind-dawn/blob/main/src/engine/policy.ts
- Recovered option/pricing code: https://github.com/JUN-ZS/timber-blade-kind-dawn/blob/main/src/engine/book.ts
- Recovered term/IV proxy: https://github.com/JUN-ZS/timber-blade-kind-dawn/blob/main/src/engine/radar.ts
- Preserved simulator under audit: https://github.com/JUN-ZS/brush-timber-mountain-brook/blob/research/original-hybrid-cagr-audit-v1-20261025/research/qqq_hybrid_dynamic_deployment_v1_1_replay.py
- Prior simulator parity study: https://github.com/JUN-ZS/brush-timber-mountain-brook/pull/98

## Replayed account-NAV values

Starting NAV: USD 100,000. The window begins 2018-03-01. The source-input SHA and preserved-simulator SHA are recorded in \`results/replay_summary.json\`.

| End date | Variant | CAGR | Daily MTM MaxDD | Final NAV | Delta to claimed reference NAV |
|---|---|---:|---:|---:|---:|
| 2025-12-15 | Legacy baseline | 12.7530% | -23.0213% | $254,787.62 | -$21,720.38 |
| 2025-12-15 | Deploy V1.1 | 12.9710% | -22.8480% | $258,651.97 | -$17,856.03 |
| 2026-09-04 | Legacy baseline | 13.6992% | -23.0213% | $298,267.22 | +$21,759.22 |
| 2026-09-04 | Deploy V1.1 | 13.9210% | -22.8480% | $303,257.38 | +$27,210.38 |

The PR #98 same-code parity check passes: extended-window baseline NAV is $298,267.223964, only $0.004 away from the previously rounded $298,267.22 output. Yet neither replay reproduces the prior reference at the same 2026-09-04 endpoint. The issue is not just date truncation: this simulator's policy behavior differs from the recovered original source policy, and its exact historical reference inputs remain unpinned.

## Required next replay

To legitimately reproduce the prior 12.7049% / -23.1837% / $276,508 result, the next implementation must first freeze a policy-faithful mapping of the recovered source decision rules into the ledger/replay, including:
1. VIX-dependent 18%/10% VXX short-stock sizing;
2. QQQ call-credit 0.8%/1.2% state sizing and no new QQQ call-credit in Shock;
3. the existing-position Shock exit behavior for VXX sellers;
4. contract/expiry/position lifecycle and the exact terminal NAV mark convention;
5. the original source-data hash and exact end date used for the historical headline.

This should be a separate fixed-rule implementation, not a parameter search to force-match the prior figures. Keep daily NAV, all components, source/contract references and each closed position available for independent review. Even after it matches, the output remains DERIVED_BS_VIX unless actual historical option-chain quotes and fills are independently supplied.
