# QQQ LIVE HEDGE DESK V2

用途：把 V22 dynamic near-long research logic 放到盤中可使用的 manual-execution state engine。

V2 不改 alpha。`risk_state()`、far/near 合約選擇、dynamic target stack、+50% harvest、DTE<=2 roll、spot>=far strike emergency 都保留；V2 只加上層的 campaign memory、ticket、對帳、fill ledger 和事件紀錄。

## Safety boundary

這個 desk 絕不自動下單：

- 不呼叫 `unlock_trade`
- 不呼叫 `place_order`
- 不呼叫 `modify_order`
- 不代替你在 Futu 送出任何 order

它只讀 Futu/OpenD 的即時行情、期權鏈、持倉、open orders，以及 live account 可取得的 deals。若 ticket 在 watcher restart / outage 之間可能漏掉今日 deal，active ticket 會以 ticket issuance timestamp 作為 historical-deal recovery 起點；recovery 仍是 broker observation，不是推測。

它也維持兩層 ownership fence：near LONG 必須與 strategy lot 對得上；far SHORT 必須有明確的 managed baseline。任何未解釋的 broker/manual position change 都會先 BLOCK，而不是自動 repair。

## State machine

`IDLE → ARMING → OPEN → HARVESTING / REDUCING / ROLLING`

每張 manual ticket 都停在 reconciliation loop。

遇到 far strike touch：

`OPEN/* → EMERGENCY_CLOSE → RECONCILE_WAIT → IDLE`

signal 熄滅不會自動關閉已開 campaign。

## One-primary rule

每個 cycle 最多只產生一張 primary ticket。

priority：

`EMERGENCY_CLOSE > REPAIR_FAR > HARVEST_NEAR > ROLL_NEAR > REPRICE_OR_CANCEL > REDUCE_NEAR > ADD_NEAR > SELL_FAR`

其餘條件留在 `candidate_actions` / `next_triggers`，只供觀察，不會同輪再發第二張單。

## Position-delta semantics

The ticket separates the strategy position delta from the broker transaction verb:

- open far short: `SHORT 0 -> 10`; broker evidence may be `SELL_SHORT` or `SELL`
- close far short: `SHORT 10 -> 0`; broker evidence may be `BUY_BACK` or `BUY`
- add near long: `LONG n -> n+k`; broker evidence is `BUY`
- harvest/reduce near long: `LONG n -> n-k`; broker evidence is `SELL`

Futu documents `SELL_SHORT` and `BUY_BACK` as returned/display directions for US order/deal queries; place-order input should use `BUY` or `SELL`. citeturn625513search0turn625513search6

## Partial fills

A same-direction position change smaller than the ticket target is `PARTIAL` and keeps the ticket open. An opposite-direction change or an overfill is `SUPERSEDED` and recorded as a manual position change.

## Ticket / reconciliation

每張 ticket 有：

`ticket_id / campaign_id / action / issued_at / legs / expected before qty / expected target qty / status`

狀態：

`OPEN / PARTIAL / FILLED / SUPERSEDED`

下一 cycle 用真實 Futu 持倉對 expected target：

- exact delta → `FILLED`
- 小於 target → `PARTIAL`
- qty 有變，但不是 ticket 所期待的 delta → `MANUAL_POSITION_CHANGE` + ticket `SUPERSEDED`
- qty 無變 → ticket 繼續 OPEN

成交價是「自 ticket issuance 起累計」的 fill VWAP，不是每個 cycle 的增量價。

Completed ticket application is crash-idempotent：重跑同一 completed ticket 不會重複建立 near lot 或再次扣減 LONG lot。Far ownership 只由 broker execution evidence 推進，不由 current position 反推。

- 對增加持倉的 leg，優先用 ticket issuance 時凍結的 `before_qty + before_avg_cost` 與當前持倉均價計出累計成本；因此 `last_positions` 推進不會把累計成交量或價格重置。
- broker deal evidence 以 `deal_id` 去重並跨 cycle 累積；broker order evidence 按 `order_id` 保存最新的 cumulative `dealt_qty/dealt_avg_price`。deal 與 order 兩個資料域不相加，避免同一成交被算兩次。
- 沒有足夠 broker fill evidence 時，只在能由 aggregate position average cost 推算時使用 `DERIVED_TICKET_POSITION_DELTA`；不冒充 broker direct fill。
- `TICKET_PARTIAL_PROGRESS` 的 `fill` 是自 ticket issuance 起的 cumulative snapshot，不是可跨事件逐行相加的 delta。
- broker evidence 只有在累計 evidence 數量足以覆蓋當前 ticket fill 數量時才可作為完整 VWAP；不足時標成 `BROKER_EVIDENCE_INCOMPLETE`，不會把最後一筆 partial fill 當成整張票的價格。

## Lot ledger

成功的 `ADD_NEAR` / `ROLL_NEAR` BUY LONG fill 會建立 strategy lot：

`lot_id / ticket_id / code / qty / avg_cost / opened_at / price_source`

`HARVEST_NEAR` 優先用已記錄 lot 的 fill cost 檢查：

`near_bid / lot_avg_cost - 1 >= 0.50`

賣出後按指定 lot 或 FIFO 減少 lot。

## Strict QQQ universe

只有 `US.QQQ...` 期權會進入這個 hedge campaign；`US.QQQ` 正股本身不會被算成 near；`US.QCOM...` 等相似字首不會再混入。

如果 QQQ option `position_side` 缺失或未知，desk 會 `BLOCKED_UNKNOWN_POSITION_SIDE`，不會猜成 SHORT。

現有未被 desk 認領的 QQQ option short 亦不會自動變成 campaign。確認確實屬於此 strategy 後才可：

```cmd
python -m research.live_hedge_v1.run_live_desk --adopt-existing-far
```

只接受「剛好一張 QQQ option short」的 adopt。

若升級前已有 active campaign，而舊 state 沒有 `managed_far_qty` ownership baseline，desk 不會從當前持倉自動猜 baseline，會 `BLOCKED_FAR_OWNERSHIP_UNBASELINED`。人工核實 broker 持倉後才可顯式 rebaseline：

```cmd
python -m research.live_hedge_v1.run_live_desk --rebaseline-existing-far
```

這個 rebaseline 只接受：campaign 已 active、沒有 active ticket、而且 broker 只有一張 QQQ option short 且 code 正好等於 `campaign.far_code`。rebaseline 會留下 `FAR_OWNERSHIP_REBASELINED` event。

## Files

- `campaign.py` — campaign state、ticket、reconciliation、primary priority
- `engine.py` — 原始 signal/risk/contract selection + candidate actions
- `state.py` — atomic persistent state + append-only events
- `futu_trade_reader.py` — read-only positions/orders/deals
- `run_live_desk.py` — single cycle
- `watch_live_desk.py` — default 15s loop
- `dashboard.html` — 5s polling dashboard
- `events.jsonl` — 邊沿事件 ledger
- `live_cycles.jsonl` — raw watcher cycle log
- `state.json` — persistent campaign/ticket/lot state
- `live_state.json` — current desk snapshot

## Windows

在 repo 根目錄：

```cmd
pip install -r requirements-futu.txt
python -m research.live_hedge_v1.run_live_desk
```

只測讀取：

```cmd
python -m research.live_hedge_v1.run_live_desk --simulate-account
```

持續監察：

```cmd
python -m research.live_hedge_v1.watch_live_desk --interval 15
```

Dashboard：

```cmd
python -m research.live_hedge_v1.serve_dashboard
```

開：

`http://127.0.0.1:8765/research/live_hedge_v1/dashboard.html`

## 策略邊界

預設研究 profile：

`far DTE 120 / far |Delta| 0.08 / near DTE 30 / coverage 1.50 / near TP +50%`

這不是已證明的 live 最佳參數，只是目前 V22 research candidate profile。

V2 的主要新增價值不是再搜尋參數，而是令「當時發出甚麼 → 你做了甚麼 → Futu 真正成交甚麼 → 下一 cycle 如何對帳」形成一條持續 append-only 的事件鏈。