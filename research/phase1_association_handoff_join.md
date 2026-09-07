# Phase-1 ASSOCIATION handoff join

> From 波動 RelVol Phase-1. **ASSOCIATION_ONLY**. `credit_unlocked=false`. CRF ≠ credit.

- pack `7ca13ce290d28db4` · DATA_HASH `075f43bc66da900bdcedf47853375c55` · tickers 1490
- candidates ASSOCIATION_ONLY: **80** · TOP30 DESC labels

## Non-claims

- CRF ≠ credit
- candidates ≠ trading signal
- VALIDATION_PENDING / OOS_PENDING on discovery rows
- no Option EV
- no daily event calendar in this handoff — cannot yet slice V2.2 daily PnL by composite state_key

## TOP30 composition

- ladder: {'REVERSING': 16, 'ACCELERATING': 2, 'MONOTONIC': 11, 'DECELERATING': 1}
- horizon: {'DAY': 30}
- threshold: {'P99': 15, 'P90': 4, 'P95': 9, 'P80': 2}
- shape: {'EXPANDING': 14, 'STRONGLY_EXPANDING': 12, '*': 4}
- regime: {'UNCLASSIFIED': 9, 'DEAD_VOL': 10, 'STABLE_LOW_VOL': 7, '*': 4}
- soft assoc_v22: {'UNMAPPED': 13, 'CALM': 17}

## TOP30 by soft `assoc_v22` (+ frozen V2.2 path DESC)

| assoc_v22 | n_keys | mean CRF | Δ vs baseline | V2.2 CAGR | V2.2 MaxDD | V2.2 mean/day |
| --- | --- | --- | --- | --- | --- | --- |
| CALM | 17 | 0.8629 | -0.005 | 6.2% | -16.4% | 0.000564 |
| UNMAPPED | 13 | 0.8634 | -0.003 | — | — | None |

## Top 10 state_key (DESC)

| state_key | assoc_v22 | n | mean_crf | Δ baseline | STATUS |
| --- | --- | --- | --- | --- | --- |
| `DAY|P99|REVERSING|0-1|EXPANDING|UNCLASSIFIED` | UNMAPPED | 85 | 0.8231 | -0.0753 | DISCOVERY |
| `DAY|P99|REVERSING|0-1|EXPANDING|DEAD_VOL` | CALM | 72 | 0.8163 | -0.0821 | DISCOVERY |
| `DAY|P99|REVERSING|0-1|EXPANDING|STABLE_LOW_VOL` | CALM | 88 | 0.8305 | -0.0679 | DISCOVERY |
| `DAY|P99|REVERSING|0-1|STRONGLY_EXPANDING|STABLE_LOW_VOL` | CALM | 87 | 0.8354 | -0.063 | DISCOVERY |
| `DAY|P99|REVERSING|0-1|STRONGLY_EXPANDING|DEAD_VOL` | CALM | 51 | 0.8522 | -0.0461 | DISCOVERY |
| `DAY|P99|REVERSING|0-1|STRONGLY_EXPANDING|UNCLASSIFIED` | UNMAPPED | 88 | 0.8505 | -0.0479 | DISCOVERY |
| `DAY|P99|REVERSING|*|*|*` | UNMAPPED | 506 | 0.8356 | -0.0628 | DISCOVERY |
| `DAY|P99|ACCELERATING|*|*|*` | UNMAPPED | 63 | 0.9555 | 0.0571 | DISCOVERY |
| `DAY|P99|MONOTONIC|0-1|STRONGLY_EXPANDING|STABLE_LOW_VOL` | CALM | 107 | 0.9456 | 0.0473 | DISCOVERY |
| `DAY|P99|MONOTONIC|0-1|EXPANDING|DEAD_VOL` | CALM | 55 | 0.9422 | 0.0439 | DISCOVERY |

## Verdict

- TOP30 主導：`DAY|P99|REVERSING|0-1|EXPANDING|…`
- CRF **低於** hz×thr 基線（Δ 為負）→ DESC 解讀為「較少回歸／較多延續」，**唔係** credit unlock
- VALIDATION/OOS 仍 PENDING → 不可當生存證據
- 未有 event calendar → **未能**直接切 V2.2 日報酬；而家只做標籤地理平行閱讀

Next: ask 波動 for `ticker,date,state_key` event panel if we want true PnL geography.
