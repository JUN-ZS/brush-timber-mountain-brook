# state_key join guide — RelVol Phase-1 ASSOCIATION_ONLY event panel

Generated: 2026-09-08T06:04:41+08:00 (Asia/Hong_Kong)

## Contract locks (do not break)

- `ASSOCIATION_ONLY` only
- `credit_unlocked=false`, `proto_eligible=false`, `option_ev=false`
- `evidence_class` for these panels: **DESC_ONLY**
- `pack_hash=7ca13ce290d28db4`
- `DATA_HASH` (phase1) = `075f43bc66da900bdcedf47853375c55`
- Join contract: `/workspace/sp500-vol/output/inertia_state_join_contract.md`

## Canonical state_key

```
horizon|threshold|ladder_class|run_bin|shape|regime
```

Example: `DAY|P99|REVERSING|0-1|EXPANDING|DEAD_VOL`

## Panel 1 — daily threshold-crossing (`event_panel_daily_threshold_RECENT5Y.csv`)

Primary grain for day PnL / State×Return daily geography.

| field | meaning |
|---|---|
| ticker, date | join keys |
| horizon | DAY / WEEK / MONTH |
| threshold | highest exceeded of {P80,P90,P95,P99}; event rows only |
| current_vol | DAY→`day_range`; WEEK→`week_range`; MONTH→**SKIPPED** (no `month_range`; `month_pct` is 0-1 rank ≠ vol range) |
| run_len | consecutive trading days with `current_vol >=` that threshold floor |
| run_bin | 0-1 / 2-3 / 4+ |
| state_key_base / state_key | `{horizon}\|{threshold}\|UNMAPPED\|{run_bin}\|UNMAPPED\|UNMAPPED` |
| day_pct, week_pct, month_pct | **ASSOCIATION join fields only** — not inertia credit |
| evidence_class | DESC_ONLY |
| ticket | `PHASE1_EVENT_PANEL_DAILY_v1` |

### Soft map to Phase-1 state_key

Daily panel fills only **horizon|threshold|run_bin**.  
`ladder_class`, `shape`, `regime` are **UNMAPPED**.

Soft join: match `horizon`, `threshold`, `run_bin` to DISCOVERY cohorts; do **not** force-fill UNMAPPED slots from cohort labels.

- **MONTH horizon omitted** from daily panel: `returns.csv` has `day_range`/`week_range` but no `month_range`. `month_pct` is a unit-interval rank (not a range), so joining it to MONTH `thresholds_hist` would invent false P99 floods. Use asof panel for MONTH geography.
- RECENT5Y cut: `date >= 2021-01-01` (default QQQ handoff)
- Full history: WRITTEN (rows=555592)

## Panel 2 — asof snapshot (`event_panel_asof_state_key.csv`)

Sparse calendar: as_of ∈ ['2026-08-21', '2026-09-04'] (board_snapshots only).

- One row per ticker × horizon × as_of from **MAGNITUDE** board
- `ladder_class` from phase1 credit_surface CRF ladder (same knife as discovery kernel)
- `shape` / `regime` from surface/board
- `run_bin` from surface `current_run` at event threshold (fallback: board `persist_run`)
- `state_key` = full six-part key
- `in_discovery_cohort=true` when key matches DISCOVERY ASSOCIATION_ONLY candidate (exact or soft ladder/runbin wildcards)
- `date = as_of` for calendar join
- evidence_class=DESC_ONLY; ticket=`PHASE1_EVENT_PANEL_ASOF_v1`

## Illegal joins (reminder)

- Map RelVol regime / state_key → single-name HOLD/EXIT CondEV “inertia”
- Use CondEV / wr / fade as RelVol state labels
- Unlock credit because an ASSOCIATION/DESC row exists
- Treat RECOVERY as OCCFIELD state_bin
- Promote PARTIAL_REGIME_BORNE → PROTO without new pre-registered knife
- Invent Credit / Option EV columns

## Suggested join recipe (QQQ VXX 年化)

1. Day PnL: join returns on `(ticker, date)` → RECENT5Y daily panel; stratify by soft `horizon|threshold|run_bin`.
2. Label attach: left-join asof panel on `(ticker, date=as_of, horizon)` for full `state_key` on the two archive pins.
3. Cohort overlay: match `state_key` to `inertia_candidates_DISCOVERY_ASSOCIATION_ONLY.csv` (DESC only).
4. Keep `evidence_class`, `pack_hash`, `credit_unlocked=false` on every output row.
