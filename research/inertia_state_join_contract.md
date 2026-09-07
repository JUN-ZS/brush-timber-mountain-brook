# Inertia ↔ RelVol/V2.2 join contract

> **ASSOCIATION_ONLY** on both sides. No Credit unlock, no sizing, no Option EV.

Synced 2026-09-07 from 慣性信用RATIO + brush-timber `relvol_v22_state_map`.

## Inertia outputs allowed into this bot

| Kind | Status | Use here |
| --- | --- | --- |
| HOLD/EXIT/onset/runlen/dir-fade CondEV | ARCHIVE / FAIL_SIGN_FLIP | **Do not** treat as inertia object |
| OCCFIELD_DIAG (RelVol occupation diagonal vs era-shuffle null) | PASS / DESIGN_OK | Field-layer map label only |
| OCCFIELD_REGIME_RESID | PARTIAL_REGIME_BORNE (REGIME_RESID FAIL_SIGN; G5 kill-cell) | G4 low-vol memory diagonal = **DESC_ONLY** map |
| Credit / Option EV / 10-class / BOT / STATEHOLD | **SEALED** | Do not unlock via join |

Inertia may emit: ASSOCIATION / field-map tags.  
Inertia must **not** emit: sizing, credit unlock, tradable EV.

## Our headers for schema align (send to Inertia)

### RelVol index leg
- `regime`: DEAD_VOL | STABLE_LOW_VOL | STABLE_HIGH_VOL | EXPANDING_VOL | CHAOTIC_VOL | EXTREME_TAIL | UNCLASSIFIED
- `weekPct`: number in [0,1] (own-history week percentile)

### RelVol market leg
- `dispersion.state`: LOW_INDEX_LOW_DISPERSION | LOW_INDEX_HIGH_DISPERSION | HIGH_INDEX_LOW_DISPERSION | HIGH_INDEX_HIGH_DISPERSION

### V2.2 association (not causal)
- `v22_state_assoc`: CALM | UNSTABLE | TAIL | RECOVERY
- map: CALM≈DEAD∪STABLE_LOW; UNSTABLE≈EXPANDING∪CHAOTIC; TAIL≈EXTREME_TAIL strict; RECOVERY via `era.life` / Event Replay fade only

### Suggested join columns for Inertia对照
- `state_bin` ← RelVol `regime` (or dispersion.state for market leg)
- `era` ← research era id (2000-2002 … 2023-2026) or Inertia era tag
- `delta_vs_null` ← OCCFIELD Δ vs era-shuffle null (DESC_ONLY / PASS stamps only)
- `assoc_v22` ← ASSOCIATION_ONLY label from map above
- `evidence_class`: ASSOCIATION | DESC_ONLY | SEALED | FAIL_*

## Artifacts (Inertia)
- `/workspace/sp500-vol/output/INERTIA_FAIL_LOG.md`
- `/workspace/sp500-vol/output/INERTIA_FALSIFICATION_MAP_v1/MAP.md`
- `/workspace/sp500-vol/output/INERTIA_OCCFIELD_REGIME_RESID_v1/`
