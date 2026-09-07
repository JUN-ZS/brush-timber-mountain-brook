# Full Handoff → brush-timber ASSOCIATION integration

> From 波動 `RelVol_INERTIA_FULL_HANDOFF_LIGHT`. **ASSOCIATION_ONLY / DESC_ONLY**. Credit & Option EV sealed.

- Dir: `/workspace/sp500-vol/output/RELEASE/RelVol_INERTIA_FULL_HANDOFF_LIGHT`
- pack `7ca13ce290d28db4` · DATA_HASH `075f43bc66da900bdcedf47853375c55`

## Locks

- NOT credit
- NOT Option EV
- NOT ticker scoreboard as product
- DESC/ASSOCIATION/DISCOVERY research layers only

## Pack map

| Layer | Role |
| --- | --- |
| phase1 | Discovery six-pack (candidates / surface / transitions / purity-ish anti-overfit) |
| phase1_validation | next-unseen cut 2024-01-01 · **PASS 50 / FAIL 23 / WEAK 7** |
| phase2 | Event→Forward T+1/5/21 dual-lift probability ledger |
| analog_relation | Relation discovery + historical analog kNN · OOS counts in STATUS |
| association | Candidate labels + event panel (QQQ geography already joined) |

## Validation (Phase-1 candidates)

- PASS **50** · FAIL **23** · WEAK **7** (pass_rate=0.625)
- DISCOVERY_ARTIFACT flags: **0**
- PASS soft assoc_v22: `{'UNMAPPED': 33, 'CALM': 17}`
- PASS ladder: `{'REVERSING': 15, 'MONOTONIC': 20, 'ACCELERATING': 3, 'DECELERATING': 7, 'RUNBIN': 5}`

### Top PASS by |Δ_val| (DESC)

| state_key | assoc_v22 | Δ_disc | Δ_val | n_val |
| --- | --- | --- | --- | --- |
| `DAY|P99|REVERSING|0-1|EXPANDING|UNCLASSIFIED` | UNMAPPED | -0.0922 | -0.0623 | 84 |
| `DAY|P99|REVERSING|0-1|STRONGLY_EXPANDING|STABLE_LOW_VOL` | CALM | -0.0678 | -0.0611 | 86 |
| `DAY|P90|ACCELERATING|*|*|*` | UNMAPPED | -0.0418 | -0.0603 | 63 |
| `DAY|P99|REVERSING|0-1|STRONGLY_EXPANDING|DEAD_VOL` | CALM | -0.0504 | -0.0536 | 51 |
| `DAY|P99|REVERSING|*|*|*` | UNMAPPED | -0.0718 | -0.0462 | 503 |
| `DAY|P95|ACCELERATING|*|*|*` | UNMAPPED | -0.0149 | -0.0402 | 63 |
| `DAY|P99|REVERSING|0-1|STRONGLY_EXPANDING|UNCLASSIFIED` | UNMAPPED | -0.0443 | -0.0401 | 88 |
| `DAY|P80|RUNBIN|2-3|*|*` | UNMAPPED | -0.0028 | -0.0381 | 59 |
| `DAY|P80|REVERSING|0-1|EXPANDING|STABLE_LOW_VOL` | CALM | 0.0049 | 0.0357 | 88 |
| `DAY|P99|MONOTONIC|0-1|EXPANDING|UNCLASSIFIED` | UNMAPPED | 0.0409 | 0.0336 | 92 |

## Phase-2 dual lift (preview tops still VAL/OOS pending)

### Continue-lift examples

| relation_key | fwd | n | continue_lift | p_continue |
| --- | --- | --- | --- | --- |
| `DAY|P80|4+` | T+5 | 23042 | 1.669 | 0.695 |
| `DAY|P80|4+` | T+21 | 22343 | 1.659 | 0.687 |
| `WEEK|P80|4+` | T+21 | 28078 | 1.646 | 0.702 |
| `WEEK|P80|4+` | T+5 | 28713 | 1.603 | 0.706 |
| `DAY|P80|4+` | T+1 | 23177 | 1.563 | 0.719 |

### Revert-lift examples

| relation_key | fwd | n | revert_lift | p_revert |
| --- | --- | --- | --- | --- |
| `DAY|P99|0-1` | T+5 | 4847 | 1.626 | 0.949 |
| `DAY|P99|0-1` | T+21 | 4809 | 1.616 | 0.947 |
| `WEEK|P99|0-1` | T+21 | 8832 | 1.575 | 0.903 |
| `WEEK|P99|0-1` | T+5 | 9014 | 1.537 | 0.86 |
| `WEEK|P95|0-1` | T+21 | 28071 | 1.418 | 0.813 |

## Analog / Relation

- relation rows: **1227** · status `{'DISCOVERY': 948, 'INSUFFICIENT': 279}`
- OOS cut `2024-01-01` · `{'VALIDATION_PASS': 698, 'WEAK': 89, 'FAIL': 50, 'INSUFFICIENT': 12}`
- Primary object: **relation_analog_match** (not ticker scoreboard)

## Bridge to frozen V2.2 (already in PR #4)

- QQQ event-day mean/day **-0.000186** vs non-event **0.000501**
- Reading: stress/threshold geography underperforms calm path days on Derived overlay — **DESC only**; does not unlock Credit/Option.

## Consumer rules for this bot

- Use VALIDATION_PASS cohorts only for stronger DESC overlays; FAIL remains documented
- Do not map CRF or continue_lift to strategy sizing
- Do not invent Option EV (options_snapshots_rows=0)
- Relation/Analog is the primary object — not ticker scoreboard

## Pointers

- Full zip on box: `RelVol_INERTIA_FULL_HANDOFF_LIGHT.zip`
- Prior joins: `event_panel_state_return_geography.md`, `phase1_association_handoff_join.md`
