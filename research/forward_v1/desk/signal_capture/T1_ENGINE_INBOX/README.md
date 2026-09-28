# T1_ENGINE_INBOX — Desk original-engine drop zone

Drop **ORIGINAL** juniper-kite Desk engine emits here after a genuine new US daily bar.

## Acceptance (machine-checkable — ALL required)

Filename `engine_emit_*.jsonl` alone is **NEVER** enough.

Each accepted emit must carry:

```
source = ORIGINAL_ENGINE
engine_id
engine_version
engine_run_id
market_bar_asof   (> formal T0 asof 2026-09-18)
source_hash
```

Plus Desk geometry from the original emit (as available):

`alignScore / opportunity / desk_state / regime / shape / trustUp / hot /
 bandPosPct / relVol20 / book_addScore / book_trimScore / whyNotBuy`

Prefer a sibling `source_provenance.json` next to the jsonl.

## Rejects → BLOCKED_WAITING_ENGINE_EMIT

- Yahoo-invented geometry / signals
- T0 re-label / same-bar re-emit
- Missing provenance keys
- Filename-only `engine_emit_*.jsonl` without ORIGINAL_ENGINE content

## How to produce

```
cd /workspace/juniper-kite/juniper-kite-shadow-frost-up-down-get
npx --yes tsx scripts/desk_run_warehouse_write.mts
# then: capture_as_emitted.py --mode live_engine  (stamps provenance into this inbox)
```

Yahoo OK for outcome/OHLC maturity only — never for Desk ranking geometry.
