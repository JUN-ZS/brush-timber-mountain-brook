# Desk LIVE_FORWARD resolution（MINIMUM RUN V1.2）

## 繁中摘要
- `evaluation_clock`: `LIVE_FORWARD`（唔好同 Cap-Rail/RelVol `REPLAY_FORWARD` win-rate 混池）
- Gate: `MAIN_B_MID_ACTIVE`（PRE #8 merged；Resolver #9 / LIVE LOOP #10 已上 main）
- T0 PR #7 **不可改寫**
- 全部事件：`desk.book_ADD`（MARK_BUY/ARMED/TRUST_UP 維持 0）
- Benchmark: QQQ
- **真實 OHLC**：stock close + QQQ close；日曆有日但缺價 → 仍 `WAITING_FOR_FUTURE_BARS`
- 資料橋：`../data_bridge/`（PRIMARY → YAHOO_FALLBACK；Yahoo 永唔標 `ORIGINAL_LIVE`）

## Latest
- run: `desk_resolve_20260921T154319Z`
- resolved_5d: `0`
- waiting: `35`
- qqq_latest / post_anchor_days: `2026-09-18` / `0`
