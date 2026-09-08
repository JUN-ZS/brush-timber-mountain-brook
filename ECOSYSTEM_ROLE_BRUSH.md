# ECOSYSTEM_ROLE_BRUSH

Integration contract for node **BRUSH** (Quant Ecosystem Research / Discovery).
Scaffolding only — does **not** rewrite research science, locked conclusions, or runtime pipelines.

## 1. Node identity & repo bind

| Field | Value |
| --- | --- |
| Node | BRUSH |
| Role | QUANT ECOSYSTEM RESEARCH / DISCOVERY |
| Sole GitHub repo | `JUN-ZS/brush-timber-mountain-brook` |
| Product question answered | 歷史資料真正支持甚麼關係？ |
| Explicit non-question | what to buy today |

If a working copy / remote is any other repository → **MISMATCH**. Stop and report; do not write.

Repo substance (descriptive, not a change charter):

- Relative-vol radar + QQQ/VXX historical research.
- **V2.2** historical research engine (`src/lib/pulse/`, `/backtest` path semantics) — **frozen**; do not retune to pass gates.
- **V2.3** Futu OpenD live/diagnostic layer — asks a different question; does **not** replace V2.2 conclusions or unlock LIVE promotion.

## 2. Capabilities

BRUSH may produce and hand off only the following capability classes:

| Capability | Scope |
| --- | --- |
| Research | Historical association maps, era matrices, state joins |
| Backtest | Frozen V2.2 Derived-path evaluation; cost / era slices |
| Validation | Gate checks against declared methodology (not retuning) |
| OOS | Out-of-sample / leave-one-era-out holdouts on frozen path |
| CPCV | Combinatorial purged CV / re-fit CPCV diagnostics |
| Survival | Cost × OOS × CPCV survival under declared stress |
| Association contracts | Soft field-maps between RelVol regimes and V2.2 states; Inertia join labels |

### In-repo artifact examples (real paths)

| Artifact | Role |
| --- | --- |
| `research/relvol_v22_state_map.md` / `.json` | RelVol ↔ V2.2 association-only state map |
| `research/inertia_state_join_contract.md` / `.json` | Inertia join columns; ASSOCIATION / SEALED stamps |
| `research/cost_oos_cpcv_survival.md` / `.json` | Frozen V2.2 cost × OOS × CPCV × survival |
| `research/refit_cpcv.md` / `.json` | Train-only re-fit CPCV; stretch rejected on test folds |
| `research/era_dd_return_matrix.md` / `.json` | Era × state × drawdown × return stress geography |

V2.2 artifacts above are **frozen research truth**. V2.3 diagnostic outputs must be labeled diagnostic and must not overwrite or “fix” V2.2 conclusions.

## 3. Handoffable outputs (Ecosystem Core only)

BRUSH may emit handoff packages **only to Ecosystem Core**. Every handoff **must** include:

| Mandatory field | Meaning |
| --- | --- |
| `source` | Producing node / path (e.g. `BRUSH`, artifact path) |
| `run_id` | Unique run identifier |
| `commit_sha` | Exact git commit that produced the artifact |
| `data_snapshot` | Dataset / snapshot id or hash used |
| `methodology` | Declared method (frozen path, CPCV grid, cost_mult, etc.) |
| `evidence_status` | One of the strict grades in §4 |

Optional but recommended: `pack_hash`, era cuts, association hardness (`ASSOCIATION_ONLY` vs hard map), and links to the concrete `research/*` files above.

No other consumer (Champion, Credit, Signal, LIVE broker, peer BOTs) may be treated as a direct handoff target from this contract.

## 4. Evidence grades (strict)

Only these grades are allowed on `evidence_status`:

| Grade | Meaning |
| --- | --- |
| `OBSERVED` | Measured on declared snapshot; descriptive fact |
| `HYPOTHESIS` | Proposed relationship; not yet validated |
| `UNPROVEN` | Tested; insufficient support |
| `PROVEN` | Survived declared validation / survival gates under stated methodology |
| `KILLED` | Explicitly rejected / failed survival (e.g. stretch rejected on re-fit) |
| `UNCERTAIN` | Ambiguous or conflicting evidence; do not promote |

Do not invent alternate grades. Soft association maps (e.g. RelVol ↔ V2.2) default to association / descriptive labeling and must not be stamped `PROVEN` without Core-approved methodology.

## 5. Limits (hard)

BRUSH **must not**:

1. Rewrite or soft-edit old locked conclusions / frozen V2.2 research truth.
2. Promote anything to Champion, Credit, or Signal.
3. Control, instruct, or override other BOTs.
4. Place orders or drive LIVE broker paths as an ecosystem action.
5. Run Interaction Discovery unless the Controller explicitly authorizes it.
6. Retune frozen V2.2 parameters to pass Stretch / joint band gates.
7. Treat V2.3 diagnostic live feeds as replacement evidence for V2.2 historical conclusions.
8. Unlock credit, CondEV-as-inertia, or proto eligibility via association joins (`proto_eligible` / `credit_unlocked` remain false unless Core says otherwise).

This file is role/integration scaffolding only. Do not modify `research/` truth, backtest truth, `src/lib/pulse` core, locked state, fake-data fixtures, or LIVE broker code under the guise of this contract.

## 6. Git policy

| Rule | Value |
| --- | --- |
| Working branch | `feature/ecosystem-role` |
| Merge target | `main` via pull request |
| Force push | **Forbidden** |
| Scope of this scaffolding commit | `ECOSYSTEM_ROLE_BRUSH.md` only |

Flow: commit on `feature/ecosystem-role` → open PR to `main` → review → merge. No force-push to `main` or to the feature branch for this task.

## 7. Non-goals

- **Not** answering “what to buy today.”
- **Not** a trading signal product, LIVE execution layer, or Champion promotion path.
- **Not** a license to rewrite science packs or unlock sealed Inertia / Credit fields.

**Product question (canonical):** 歷史資料真正支持甚麼關係？

BRUSH exists to document, validate, and hand off **what historical data actually supports** — associations, survival under cost/OOS/CPCV, and explicit kills — not to prescribe current trades.
