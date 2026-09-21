# Desk T1_ENGINE_INBOX — LIVE FORWARD capture gate

Accept **only** original juniper-kite Desk engine as-emitted payloads when:

`market_bar_asof > last formal asof` (T0 formal ≈ `2026-09-18`)

## Hard locks

- T0 re-emit ≠ T1 (same bar as T0 → `NO_NEW_SIGNAL`)
- Do **not** mint fake T1 from Yahoo; Yahoo is for outcomes only when bars exist
- `book_ADD` ≠ `MARK_BUY` — observation only unless engine truly emits MARK_BUY/ARMED/TRUST_UP/BUY/SELL
- score / alignScore ≠ probability; H ≠ BUY; LIVE ≠ REPLAY mix

## Drop format

Place engine-emitted `events.jsonl` (or `desk_events_*.jsonl`) here after a genuine new completed daily bar + original engine run:

```
cd /workspace/juniper-kite/juniper-kite-shadow-frost-up-down-get
npx --yes tsx scripts/desk_run_warehouse_write.mts
# then copy AS_EMITTED events into this inbox when market_bar_asof > 2026-09-18
```

Required event fields (AS_EMITTED): `event_id`, `market_bar_asof`, `ticker`, `signal_type`, `price_at_signal`, …

## Gate statuses

| Status | Meaning |
|--------|---------|
| `BLOCKED_WAITING_NEW_BAR` | No completed daily bar newer than formal previous asof |
| `BLOCKED_WAITING_ENGINE_EMIT` | Newer bar exists but no original engine emit in inbox / engine paths |
| `READY_TO_CAPTURE` / `CAPTURED` | Genuine T1 — confirmation_cohort opens |
| `NO_NEW_SIGNAL` | Same bar as T0 (data may be fresh) |

Honesty: like RelVol #44 / BEAM #45 — document blocker; do not invent T1.
