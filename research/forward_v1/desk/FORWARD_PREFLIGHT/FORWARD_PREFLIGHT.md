# Desk FORWARD PREFLIGHT — PHASE A

SOURCE OF TRUTH = GitHub merged [PR #7](https://github.com/JUN-ZS/brush-timber-mountain-brook/pull/7) (`86fc12a`)

## Counts (from GitHub files, not chat)

| metric | value |
| --- | --- |
| events | **7** |
| unique tickers | **7** |
| outcomes | **35** |
| WAITING | **35** |
| resolved | **0** |
| MARK_BUY / ARMED / TRUST_UP / book_ADD | 0 / 0 / 0 / 7 |

## Locks

- model_version: `DESK_CORE_V1`
- code_commit: `fd0e5d9`
- signal_timestamp: `2026-09-21T18:38:00+08:00`
- market_bar_asof: `2026-09-18`
- universe_asof: `FIXED_UNIVERSE_DEFAULT_SYMBOLS_fd0e5d9`
- provenance: `yahoo_live_scan`
- score_label: `NOT_A_PROBABILITY`
- claimed_p all null: True
- benchmark: `QQQ`
- horizons: [5, 21, 63, 126, 252]

## Audits

- event_id unique: True
- duplicate event+horizon: 0
- price_at_signal present: 7 / missing: 0 → `OK`
- STALE_REFERENCE (timestamp date > bar asof): **7** — preserved as-is, not rewritten
- mismatches vs run_report: none

## Gate

**PASS → B_MID** · audit_status=`PASS`

T0 immutable. No re-scan. No win rates. Outcomes append-only in PHASE B.
