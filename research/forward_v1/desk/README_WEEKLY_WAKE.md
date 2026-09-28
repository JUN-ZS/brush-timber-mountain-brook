# Desk WEEKLY WAKE → SELF-DUE → RUN ONLY IF DUE

## CADENCE ≠ WAKE FREQUENCY

- **Weekly wake only ASKS self-due.** It does not mean “run Desk every week as if cadence were weekly.”
- **SHORT / MEDIUM / LONG** (`1d` observation atom; maturity `5 / 21 / 63 / 126 / 252` trading days) are **information / maturity scales**, not commands to run daily or every N calendar days.
- Wake ≠ due. Same completed bars + identical ORIGINAL_ENGINE emit → `due_now=false` → **STOP** (anti-loop; `knowledge_delta=NONE`).

Source of truth: `TEMPORAL_SELF_AUDIT.json` (`DUE_RULE` / `WAIT_RULE` / `DUE_NOT_DUE_TEMPLATE`).

## Entry (local CLI)

```bash
cd /path/to/brush-timber-mountain-brook
python research/forward_v1/desk/tools/weekly_wake.py --now
```

Evaluate only (no capture/resolver even if due):

```bash
python research/forward_v1/desk/tools/self_due.py
python research/forward_v1/desk/tools/weekly_wake.py --now --dry-run
```

## Behavior

1. **ALWAYS** evaluate self-due → write `status/SELF_DUE_STATUS.json`
2. **IF WAIT** (`due_now=false`): write status, `knowledge_delta=NONE`, **STOP** — no reprocess
3. **IF DUE**: run only due lane(s)
   - `signal_capture` → existing `t1_capture.py` (AS_EMITTED; never invent T1)
   - `maturity_*` → existing `live_forward_resolver.py --horizons …`
4. Action map: new bar+emit → `RUN_SHORT`; maturity by horizon bucket → `RUN_SHORT` / `RUN_MEDIUM` / `RUN_LONG`; none → `WAIT`

## Ops note

No GitHub Actions cloud cron is required (OAuth may lack workflow scope). **Grok Bot weekly routine** should call this CLI.

## Hard locks

No formula change · no new H · no T0 rewrite · no T1 invent · no Yahoo-as-geometry · discovery ≠ confirmation.
