# Desk FORWARD CONTROL PLANE (node slice)

Machine-readable SoT: [`FORWARD_CONTROL_PLANE_STATUS.json`](./FORWARD_CONTROL_PLANE_STATUS.json)

## Truthful Desk state (at CONTROL PLANE V1 land)

| Field | Value |
|-------|-------|
| T0 | `T0_FROZEN` — path `T0_20260921T183800/` immutable |
| T1 | `T1_CAPTURED` — `market_bar_asof=2026-09-25`, 7× `book_ADD` |
| Confirmation | `CONFIRMATION_OPEN` |
| Outcomes | `WAIT_OUTCOME_MATURITY` / `WAITING_FOR_FUTURE_BARS` |
| H | 39 UNTESTED / 0 PENDING / 0 CONFIRMED / 0 REJECTED |

## Hard flags

- `t0_maturity_is_not_t1_confirmation=true` — `resolved_5d=7` on T0 anchors is **discovery maturity**, not T1 confirmation
- `book_ADD_is_not_mark_buy=true`
- Anti-loop: identical `source_hash`+`engine_run_id`+`asof` → `CAPTURED_ALREADY`, `new_signals=0`

Do not invent T1, do not add H, do not Yahoo-as-geometry, do not merge discovery into confirmation pools.
