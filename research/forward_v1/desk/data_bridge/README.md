# Desk DATA_BRIDGE（MINIMUM RUN V1.2）

## 繁中說明
呢層係 **DATA → SIGNAL → EVENT → OUTCOME** 嘅資料橋，專供信股慣性台 `LIVE_FORWARD`：

1. **PRIMARY**：優先讀 `/workspace/juniper-kite/cache/bars`（原 Yahoo live cache）
2. **YAHOO_FALLBACK**：用 `yfinance` 補 post-anchor 缺口；每條 bar 必須標  
   `source=YAHOO_FALLBACK` + `data_asof` + `retrieved_at` + `frequency` + `ticker`  
   — **永唔可以標 `ORIGINAL_LIVE`**
3. 寫出 `bars/{TICKER}.json` 同 `DATA_BRIDGE_STATUS.json`
4. Resolver 用真實 **stock OHLC + QQQ OHLC**；有日曆無價 → 仍然 `WAITING_FOR_FUTURE_BARS`

## 硬鎖
- T0 不可改寫
- `evaluation_clock=LIVE_FORWARD`
- `book_ADD ≠ MARK_BUY`
- 唔好同 Cap-Rail/RelVol `REPLAY_FORWARD` win-rate 混池
- 唔發明價格

## 用法
```bash
python3 research/forward_v1/desk/tools/data_bridge.py --repo-root .
python3 research/forward_v1/desk/tools/resolve_5d.py --repo-root .
python3 research/forward_v1/desk/tools/write_forward_system_status.py --repo-root . --refresh
```
