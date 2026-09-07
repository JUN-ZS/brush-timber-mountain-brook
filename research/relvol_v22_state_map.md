# RelVol ↔ V2.2 state map

> **ASSOCIATION_ONLY** — not the same classifier. Do not optimize annualized returns off this table.

Source: 波動 (`regime.ts` classifyFromParts) · synced 2026-09-07 into brush-timber research pack.

## RelVol single-name regime (own-history WEEK)

| RelVol | Rule (summary) |
| --- | --- |
| DEAD_VOL | weekPct&lt;0.2 and ratioToMean&lt;0.7 |
| STABLE_LOW_VOL | weekPct&lt;0.5 and tail≠EXPANDING |
| STABLE_HIGH_VOL | 0.55≤weekPct&lt;0.92, tail≠EXPANDING, P99freq≤0.03, pCont≥0.45 |
| EXPANDING_VOL | tail EXPANDING and weekPct≥0.5 |
| CHAOTIC_VOL | P99freq&gt;0.04 and pCont&lt;0.4 |
| EXTREME_TAIL | weekPct≥0.95 |
| UNCLASSIFIED | else |

## RelVol market dispersion

`LOW_INDEX_LOW_DISPERSION` / `LOW_INDEX_HIGH_DISPERSION` / `HIGH_INDEX_*`  
(index weekPct ≤0.35 or ≥0.7; dispersion thresholds ~0.14 / 0.22)

「綠偏黃」is alert prose, not an enum: 綠≈ index DEAD/STABLE_LOW；黃≈ `LOW_INDEX_HIGH_DISPERSION`.

## Suggested association to V2.2

| V2.2 | RelVol nearest | Caution |
| --- | --- | --- |
| CALM | DEAD_VOL ∪ STABLE_LOW_VOL; market often LOW_INDEX_* and not EXTREME cluster | RelVol calm = own low percentile ≠ low VIX |
| UNSTABLE | EXPANDING_VOL ∪ CHAOTIC_VOL; or HIGH_INDEX_HIGH_DISPERSION | CHAOTIC ≠ one-way trend |
| TAIL | EXTREME_TAIL (strict); secondary EXPANDING_VOL | Strict TAIL = EXTREME_TAIL only |
| RECOVERY | **No same-name tag.** Approx: era life REVERSING/STABILIZING, or EXTREME→low percentile revert | Join via era/transition / Event Replay fade — do not hard-map one regime |

## Join keys

- Index leg: QQQ/SPY RelVol `regime` + `weekPct`
- Market leg: `dispersion.state`
- V2.2 RECOVERY: RelVol `era.life` or Event Replay WIN/LOSS fade — not regime literal

## Example (2026-09-04)

QQQ DEAD_VOL week≈P9; SPY STABLE_LOW week≈P20; dispersion `LOW_INDEX_HIGH_DISPERSION`  
→ geography leans V2.2 **CALM + dispersion yellow**, not TAIL.
