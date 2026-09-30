# QQQ LIVE HEDGE DESK V1

用途：將 V22 dynamic near-long 邏輯變成真正可以盤中使用的策略器。

每一個 cycle 讀取：
1. QQQ 即時 quote + 日線歷史
2. CALL chain，涵蓋 near 7/14/21/30D 與 far 90/120/180D
3. Futu US 真實持倉
4. Futu US 未完成／最近掛單

然後輸出 action ticket：
SELL_FAR / REPAIR_FAR / ADD_NEAR / REDUCE_NEAR / HARVEST_NEAR / ROLL_NEAR / CLOSE_FAR_EMERGENCY / CLOSE_NEAR / REPRICE_OR_CANCEL。

策略器本身不偷偷下單。你在 Futu 手動執行 ticket；下一 cycle 重新讀真實持倉，所以它會知道你之前加了、減了、roll 了多少。

核心：
- far short 固定 10 張
- extreme-high signal 才開新 campaign
- near stack = f(far delta, strike distance, far gamma, delta jump)
- near +50% → harvest
- near DTE <= 2 → roll
- spot >= far strike → close campaign
- pending order 超過 120 秒 → requote / modify-or-cancel 建議
- quote / account stale 或 unavailable → BLOCK，不猜價格

Windows:
    cd C:\path\to\brush-timber-mountain-brook
    pip install -r requirements-futu.txt
    python -m research.live_hedge_v1.run_live_desk

測試帳戶：
    python -m research.live_hedge_v1.run_live_desk --simulate-account

輸出：
    research/live_hedge_v1/live_state.json
    research/live_hedge_v1/state.json

Futu 官方接口現時提供 option chain、動態 option quote、position_list_query、order_list_query，以及 place_order / modify_order；本 V1 只使用前四項讀取，刻意不調用下單/改单接口。
