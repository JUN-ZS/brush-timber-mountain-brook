# inertia_state_join_contract (ASSOCIATION_ONLY)

- Pack (Inertia): `7ca13ce290d28db4`
- Credit / Option EV / 10-class / STATEHOLD / BOT: **SEALED**
- Inertia outputs for join: **ASSOCIATION / field-map labels only** — never CondEV-as-inertia, never credit unlock
- Counterpart: QQQ VXX 年化 RelVol↔State V2.2 ASSOCIATION_ONLY (brush-timber PR#3)

## Suggested join columns (canonical)

| column | type / enum | producer | notes |
|---|---|---|---|
| `state_bin` | string | both | see mapping below |
| `era` | `{eraA,eraB,ROLL1,ROLL2}` or life-era | Inertia calendar cuts; RelVol may use `era.life` | do not retune Inertia cuts mid-join |
| `delta_vs_null` | float | Inertia OCCFIELD | diagonal mass − era-shuffle null; DIAG only |
| `assoc_v22` | `{CALM,UNSTABLE,TAIL,RECOVERY,UNMAPPED}` | RelVol V2.2 collapse | RECOVERY → era.life / Event Replay — soft, not hard map |
| `evidence_class` | `{ASSOCIATION,DESC_ONLY,SEALED,FAIL_*}` | Inertia stamp | see evidence table |
| `pack_hash` | string | Inertia | `7ca13ce290d28db4` |
| `ticket` | string | Inertia | source knife id |
| `proto_eligible` | bool | Inertia | always `false` for now |
| `credit_unlocked` | bool | Inertia | always `false` |

## RelVol `regime` → join `state_bin` / `assoc_v22`

| RelVol `regime` | `assoc_v22` | Inertia `state_bin` (OCCFIELD 3-tercile) | hard? |
|---|---|---|---|
| DEAD_VOL | CALM | prefer LOW | soft — many-to-one |
| STABLE_LOW_VOL | CALM | prefer LOW | soft |
| STABLE_HIGH_VOL | UNMAPPED (or UNSTABLE if you treat high-stable as stress) | MID/HIGH | **do not force** |
| EXPANDING_VOL | UNSTABLE | prefer HIGH | soft |
| CHAOTIC_VOL | UNSTABLE | prefer HIGH | soft |
| EXTREME_TAIL | TAIL | HIGH (tail flag separate if available) | soft |
| UNCLASSIFIED | UNMAPPED | UNMAPPED | — |
| (RECOVERY path) | RECOVERY | UNMAPPED at state_bin | use `era.life` / Event Replay — **not** OCCFIELD bin |

Also keep RelVol raw fields on the row: `regime`, `weekPct`, `dispersion.state` — do not drop them when collapsing to `assoc_v22`.

## Market `dispersion.state` (RelVol) — DESC only for Inertia

Inertia REGIME_RESID used **SPY 20d RV terciles** (no VIX in pack). Treat RelVol `dispersion.state` as a **parallel DESC stratum**, not a replacement null:

| RelVol dispersion.state | Inertia use |
|---|---|
| LOW_INDEX_LOW_DISPERSION | DESC align with “calm market” narratives |
| LOW_INDEX_HIGH_DISPERSION | DESC — dispersion without index stress |
| HIGH_INDEX_LOW_DISPERSION | DESC — index stress, tight cross-section |
| HIGH_INDEX_HIGH_DISPERSION | DESC — stress + dispersion |

Do **not** rewrite Inertia `delta_vs_null` using dispersion.state. Association only.

## Inertia `evidence_class` vocabulary (frozen)

| evidence_class | meaning |
|---|---|
| ASSOCIATION | Field-level diagonal vs null (OCCFIELD_DIAG PASS/DESIGN_OK) — structure candidate only |
| DESC_ONLY | F3/F4 dir-fade/AMP; G4 VOL_LOWMEM map; OCC_CROWD |
| SEALED | STATEHOLD; Credit; Option EV; 10-class; BOT |
| FAIL_COUPLED / FAIL_SIGN_FLIP / FAIL_SIGN / FAIL_THIN / PARTIAL_REGIME_BORNE | See FAIL_LOG |

## OCCFIELD stamp (must travel with any ASSOCIATION row)

- `occfield_grade` = `PARTIAL_REGIME_BORNE`
- DIAG = `PASS_DESIGN_OK`
- RESID = `FAIL_SIGN` (G5 kill-cell: ROLL1 × MKT × SPY-RV-low Δ=−0.01234)
- G4 VOL_LOWMEM = `DESC_ONLY` map only
- `proto_eligible=false`, `credit_unlocked=false`

## Explicit non-joins (illegal)

- Map RelVol regime → single-name HOLD/EXIT CondEV “inertia”
- Use CondEV / wr / fade as RelVol state labels
- Unlock credit because ASSOCIATION row exists
- Treat RECOVERY as OCCFIELD state_bin
- Promote PARTIAL_REGIME_BORNE → PROTO without new pre-registered knife

## Paths (Inertia side)

- Fail log: `/workspace/sp500-vol/output/INERTIA_FAIL_LOG.md`
- Map: `/workspace/sp500-vol/output/INERTIA_FALSIFICATION_MAP_v1/MAP.md`
- Stamp: `/workspace/sp500-vol/output/INERTIA_OCCFIELD_REGIME_RESID_v1/{OCCFIELD_STATUS.json,FALSIFY_MAP.md,LABEL.txt}`
- This contract: `/workspace/inertia-grok/contracts/inertia_state_join_contract.md`
- JSON twin: `/workspace/inertia-grok/contracts/inertia_state_join_contract.json`
