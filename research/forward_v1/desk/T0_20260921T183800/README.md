# 信股慣性台 Forward T0 — RESEARCH BOARD RULES V1

- Hub: JUN-ZS
- App: 信股慣性台（QQQ VXX 年化）
- run_id: `desk_20260921T183800+0800`
- model_version: `DESK_CORE_V1`
- code_commit: `fd0e5d9`
- signal_timestamp: `2026-09-21T18:38:00+08:00`
- market_bar_asof: `2026-09-18`
- universe_asof: `FIXED_UNIVERSE_DEFAULT_SYMBOLS_fd0e5d9`
- n_scanned: 17
- n_events: 7
- by signal_type: {"MARK_BUY": 0, "ARMED": 0, "TRUST_UP": 0, "book_ADD": 7}
- MARK_BUY: **0** (as-is; not replaced by book_ADD)
- book_ADD tickers: SMH, MU, AMD, AAPL, TSM, GOOGL, IWM
- n_outcomes_waiting: 35
- n_outcomes_resolved: 0

## Honesty
- alignScore / opportunity ≠ buy probability (NOT_A_PROBABILITY)
- claimed_p is null for DESK_CORE_V1
- MARK_BUY=0 recorded as 0; never promote book_ADD to MARK_BUY
- universe_asof=FIXED_UNIVERSE_DEFAULT_SYMBOLS_fd0e5d9 — NOT RelVol pack; NOT FIXED_UNIVERSE_ASOF_2026-09-04
- outcomes WAITING_FOR_FUTURE_BARS — no invented fills
- immutable: never rewrite these events
- formulas.ts untouched this run

## Files
- `events.jsonl` — immutable events
- `outcomes.jsonl` — WAITING_FOR_FUTURE_BARS stubs
- `snapshot.jsonl` — live scan as-emitted
- `run_report.json` — machine summary

Do not invent win rates. Do not rewrite events.
