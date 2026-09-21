# Desk LIVE LOOP / MINIMUM RUN V1.2 審計

## 繁中結論（2026-09-21 HKT）
- T0（PR #7）不可改寫：7 `book_ADD` / `MARK_BUY=0` / `maturity_anchor=2026-09-18`
- PRE #8、Resolver #9、LIVE LOOP #10 已 MERGED
- **V1.2** 補上：`data_bridge.py`（PRIMARY → `YAHOO_FALLBACK`）+ 真實 stock/QQQ OHLC `resolve_5d`
- 完成 session 最新 bar 仍 = **2026-09-18**（同 Cap-Rail）；盤中 9/21 incomplete bar 已標示並排除 resolve 日曆
- `post_anchor_trading_days=0` → `resolved_5d=0` / `WAITING_FOR_FUTURE_BARS`（誠實，唔發明價）
- T1：`NO_NEW_SIGNAL`（同 bar as T0；唔係 `DATA_STALE`）

## Hard locks
- `evaluation_clock=LIVE_FORWARD`
- `book_ADD ≠ MARK_BUY`
- `score ≠ probability`
- `YAHOO_FALLBACK` 永唔標 `ORIGINAL_LIVE`
- 唔同 Cap-Rail/RelVol `REPLAY_FORWARD` win-rate 混池

## 指令
```bash
python3 research/forward_v1/desk/tools/data_bridge.py --repo-root .
python3 research/forward_v1/desk/tools/resolve_5d.py --repo-root .
python3 research/forward_v1/desk/tools/live_forward_resolver.py --repo-root .
python3 research/forward_v1/desk/tools/write_forward_system_status.py --repo-root . --refresh
```
