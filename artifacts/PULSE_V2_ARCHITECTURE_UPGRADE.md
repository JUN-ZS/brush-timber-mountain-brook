# EVB → PULSE v2 — 第二層架構升級母規格
#  incremental spec，不是推翻重做，不是從零開始

版本：pulse_capture.v2  
地位：加在既有 EVB 證據層與 PULSE v1 之上  
鎖定：Evolution · Capital · FINAL_OOS · LIVE 仍鎖  
核心不變：殺錯的能力 > 找冠軍的能力

---

## 0. 這份規格解決什麼

上一輪 PULSE 已對的部分保留：

- 不從零開始
- EVB 管「什麼證據可以信」
- PULSE 管「現在有沒有短暫非對稱機會」
- NO_TRADE 合法
- Shadow ≠ Live
- 不把 screen_fitness 當成 formal fitness
- 不因 candidate_pool = 0 放寬規則

上一輪必須立刻改掉的部分：

- 把 PULSE 當 Strategy 而不是 Event
- 把 2023–2026 直接叫 secondary OOS
- 把 execution 固定成「次日開盤」
- 只用單資產價格加速度定義動能
- 用 21 筆影子交易談 edge
- Harvest / Watcher / Trade DB 不是一等公民
- PULSE 沒有自己的殺刀
- 學習結果有機會偷跑回 fitness

---

## 1. 分層（不可合併）

```text
MARKET DATA
    │
    ▼
EVB                         什麼資料 / 實驗 / 血統可以信
    │
    ▼
PULSE                       有沒有 PULSE EVENT 值得小代價下注
    │
    ├── NO_TRADE
    └── ENTRY_CANDIDATE
            │
            ▼
EXECUTION                   用哪一種進場表達這個 Event
            │
            ▼
WATCHER                     進場後路徑監控
            │
     ┌──────┼──────┐
     ▼      ▼      ▼
   HOLD   HARVEST  EXIT
            │
            ▼
         RUNNER
            │
            ▼
      MOMENTUM DECAY → EXIT → LEARN（不得直接回灌 fitness）
```

四個引擎權限不同：

| 引擎 | 可做 | 不可做 |
|---|---|---|
| EVB | 證據、血統、協議 hash、裁決 | 產生交易訊號 |
| PULSE | 偵測 Event、估計非對稱性 | 改 EVB 規則、寫 formal fitness |
| HARVEST | 分段收割、留 Runner | 發明新進場理由 |
| WATCHER | 監測已開倉路徑 | 把未驗證路徑標成 PASS |

Auditor ≠ Experimenter。改門檻必須開新 protocol_version。

---

## 2. 核心單位：PULSE EVENT，不是 Strategy

禁止再把主物件叫 Strategy / Gene / Champion。

主物件：

```text
PulseEvent
```

生命週期：

```text
QUIET
  → STATE_TRANSITION
  → PULSE_EVENT
  → ASYMMETRY_SCORE
  → ENTRY_ELIGIBLE | REJECTED | NO_TRADE
  → ACTIVE
  → HARVESTING
  → RUNNER
  → DECAY
  → EXIT
  → JOURNALED
  → ATTACKED
  → FALSE_PULSE | FRAGILE | INSUFFICIENT | SURVIVING_EVENT | RECURRING_CLASS
```

Event 必須能回答：

1. WHAT changed?
2. WHY is it unusual?
3. HOW strong is the transition?
4. HOW long does this class usually persist?
5. WHAT invalidates it?
6. HOW much can I lose before confirmation?
7. WHERE should I harvest?
8. WHEN should I leave a runner?
9. WHEN has the pulse died?

答不出這九題 → 不得進 ENTRY_ELIGIBLE。

---

## 3. 資料切分：禁止再寫「這是 OOS」就算數

正式切分，缺一不可：

```text
TRAIN
VALIDATION
FROZEN_OOS
SHADOW
LIVE
```

規則：

- 標籤不是因為被叫 OOS 就自動成為 OOS。
- 任何 threshold / harvest 分數 / execution 偏好，若在看過某段結果後改過，該段立刻降級為 VALIDATION 或更髒。
- FROZEN_OOS 在 protocol_hash 鎖定後才存在。鎖定後改規則 = 該段作廢。
- SHADOW 可以重播 FROZEN_OOS，但結果 evidence_tag = HYPOTHETICAL，不得當 PASS。
- LIVE 鎖死。SHADOW P&L 不得寫入 EVB gene fitness。

每一個 PulseEvent 必須帶：

```text
data_split: TRAIN | VALIDATION | FROZEN_OOS | SHADOW | LIVE
protocol_id
protocol_hash
seen_by_tuning: true | false
```

`seen_by_tuning = true` 的結果，禁止自稱 FROZEN_OOS。

上一輪「secondary OOS（2023–2026）」預設判定：

```text
CONTRADICTED / UNPROVEN_OOS
```

除非能證明：規則確定時間 ≤ 該段起點，且其間沒有因結果改 threshold。
現階段做不到這證明，就不要叫它 OOS。

---

## 4. Signal 與 Execution 必須拆開

禁止系統預設：

```text
signal → next open fill
```

Signal Engine 只輸出 Event。  
Execution Engine 只輸出「如何表達這個 Event」。

允許的 execution family（研究對象，不是預設冠軍）：

```text
IMMEDIATE
DELAYED
NEXT_OPEN
PULLBACK
CONFIRMATION
```

每個 Event class 必須比較各 execution 的：

- fill quality
- missed move
- MAE
- time-to-MFE
- cost death point
- false-start rate

裁決不是「哪個賺最多」，而是「哪個在真實成本下仍不把 Event 殺死，同時不把假脈衝放大」。

未完成這場比較前，NEXT_OPEN 只能標：

```text
EXECUTION_HYPOTHESIS
```

不得寫成系統預設事實。

表達工具與進場時機分開：

```text
INSTRUMENT:  SPOT | ETF | PAIR | BASKET | OPTION | HEDGE | COMBO
TIMING:      IMMEDIATE | DELAYED | NEXT_OPEN | PULLBACK | CONFIRMATION
```

PULSE 先決定「市場出現了什麼值得買其後續路徑的東西」。  
Execution 再決定「哪種工具最便宜取得這份 exposure」。

---

## 5. Radar 搜尋的是狀態轉換結構，不是預先定義的 momentum 公式

禁止把動能寫死成：

```text
price accel + volume spike + RSI + vol
```

Radar 觀察的最小原子是 State Transition：

```text
price_state
vol_state
rel_state
breadth_state
corr_state
liq_state
regime
cross_asset_state
```

搜尋層級：

```text
SINGLE     單一標的
PAIR       A/B relative
BASKET     industry vs benchmark
CROSS      equity / vol / rates / commodity / fx
COMPOSITE  price + volume + vol + breadth + RS + corr-break + liquidity
```

資料沒有的軸，標 MISSING，禁止插補後假裝 Observed。

套件現況：

- 有 QQQ / SPY / TLT / VIX / VXX 面板者：只准用已存在欄位
- VXX 末端 null：該家族 DISABLE，不插補
- fwd* 欄位：LOOKAHEAD，禁止進 Radar
- 沒有單股 / options tape / sector breadth：那些 Event class 標 CAPABILITY_MISSING，不准用假資料補

研究問題不是「怎樣定義動能」，而是：

> 哪一類 State Transition 之後，歷史上出現過可交易的 continuation？  
> 哪一類只是假脈衝？

Event class 由證據長出來，不由作者先命名冠軍。

---

## 6. PULSE 自己的殺刀（從 EVB 移植）

每個 Event class 必須接受固定裁決鏈：

```text
Family → State → Path → Cost → Crisis → Survival
```

順序不可改。

一個漂亮的 PULSE-001 不是成功。成功是系統能把它殺掉。

預期漏斗（示意，不是 KPI）：

```text
1000 Events
  → 700 FALSE_PULSE
  → 200 FRAGILE
  → 70  INSUFFICIENT_SAMPLE
  → 25  SURVIVING_EVENTS
  → 5   RECURRING_EVENT_CLASSES
```

狀態定義：

| 標籤 | 意義 |
|---|---|
| FALSE_PULSE | 轉換後沒有 continuation，或代價吃掉全部期望 |
| FRAGILE | 只在窄 State / 單一 path / 甜成本下活 |
| INSUFFICIENT_SAMPLE | n 或獨立家族不夠，禁止稱 edge |
| HARD_FAIL | 危機後不 beat 基準，或 cost×3 已死 |
| SURVIVING_EVENT | 通過當前鎖定 protocol，仍不是 ROBUST |
| RECURRING_CLASS | 多個獨立家族重複出現同一轉換結構 |
| ROBUST_EVENT | 尚未解鎖。沒有 CPCV≥10 + 真實成本矩陣 + 危機定義前，禁止產生 |

HARD_FAIL == 0 且 Event 很多時：停止加 Event class，先審問死亡條件為何罕見。

Family Collapse 先於計數：

- 同轉換骨架 + 同方向 + 同 regime = 一票
- 禁止 3 個 clone 當成 3 份獨立證據

---

## 7. Harvest / Runner / Decay 是交易哲學核心，不是 UI 裝飾

禁止固定 25%。

Harvest 只准看路徑，不准看「希望」：

輸入：

```text
MFE
MAE
time_to_MFE
time_to_failure
strengthening | weakening | decaying
liquidity
spread
unrealized_R
```

輸出：

```text
harvest_fraction ∈ [0, 1]
runner_allowed: true | false
invalidation_price
decay_reason
```

原則：

- 先小倉進入
- 市場確認後才加碼或留 Runner
- 有利潤先收一部分
- Runner 只在 continuation 仍在時存活
- decay 出現 → 剩餘出場
- 沒有 Pulse → NO_TRADE

未落地 MFE/MAE/time-to-MFE 之前，任何「收 25%」都是人工策略，標 HYPOTHETICAL。

---

## 8. 21 筆影子交易的正確讀法

上一輪：

```text
21 trades · 9W / 12L · paper ≈ 96,556
```

裁決：

```text
INSUFFICIENT_SAMPLE
無決策價值
不得用來主張 edge
不得用來調 threshold
```

正式研究最小報表（缺一不可）：

```text
event_count
independent_event_families
holding_time_distribution
MAE
MFE
time_to_MFE
time_to_failure
slippage
turnover
liquidity
profit_factor
expectancy
drawdown
tail_loss
state_conditional_expectancy
cost_death_point
execution_family_comparison
```

少於獨立 Event family 門檻，只准寫 INSUFFICIENT_SAMPLE。

---

## 9. Trade DB：預期 vs 實際，但是禁止偷跑回 fitness

每筆不是 BUY/SELL/PnL 三欄。最少欄位：

```text
event_id
event_class
signal_fingerprint
market_state_snapshot
entry_reason
expected_continuation
expected_duration
expected_upside
expected_downside
execution_family
instrument
fill
actual_path
MAE
MFE
harvest_actions[]
runner_duration
exit_reason
slippage
liquidity
prediction_error
data_split
protocol_hash
evidence_tag
```

學習路徑：

```text
Observed
  → Experiment
  → Validated
  → Candidate
```

禁止：

```text
shadow PnL → gene.fitness
shadow PnL → pulse threshold
shadow PnL → protocol tweak
```

預測誤差只進 Journal，進 EVB 必須重新走完整 ExperimentResult + lineage。

---

## 10. 非對稱機會，不是「只做多動能」

PULSE 搜尋的是：

> 突然出現、值得用小風險購買其後續路徑的非對稱 payoff

合法結論：

```text
LONG
SHORT
PAIR
ETF
OPTION
HEDGE
COMBINATION
NO_TRADE
```

合法 Event 形態：

```text
sudden up
sudden down
vol expansion
vol compression → expansion
correlation breakdown
relative-strength reversal
liquidity air-pocket
cross-asset divergence
```

沒有對應 Observed 資料的形態，標 CAPABILITY_MISSING，不准演。

---

## 11. 對上一輪實作的正式判定

| 項目 | 判定 |
|---|---|
| 不從零開始 | ALIGNED |
| EVB / PULSE 分層 | ALIGNED |
| NO_TRADE | ALIGNED |
| Shadow replay | ALIGNED，結果僅 HYPOTHETICAL |
| Evolution / Capital 鎖定 | ALIGNED，維持 |
| 次日開盤固定 execution | CONTRADICTED — 降為 EXECUTION_HYPOTHESIS |
| 2023–2026 稱 secondary OOS | UNPROVEN_OOS — 未證明未調參 |
| 21 筆交易談績效 | INSUFFICIENT_SAMPLE |
| 單資產 radar | PARTIAL — 須升到 pair/basket/cross，資料不夠就 MISSING |
| 預先定義 momentum 公式 | CONTRADICTED — 改為研究 transition class |
| MFE/MAE/Harvest | MISSING — P0.5 |
| Watcher | MISSING — P0.5 |
| Trade DB expected vs actual | PARTIAL / MISSING |
| PULSE 殺刀 | MISSING — 必須移植 EVB 裁決鏈 |
| Protocol meta-overfit 防護 | EVB 已知，PULSE 未繼承 |

---

## 12. BUILD ORDER（仍不准一次建完）

### Phase A — 契約（現在）
- PulseEvent schema
- data split schema
- execution family schema
- trade journal schema
- event kill-matrix schema
- 把 2023–2026 從 OOS 降級
- 把 next-open 從預設降級

### Phase B — Radar 升級
- state transition 物件
- single / pair / basket / cross 探測器
- MISSING 軸顯式標記
- 不預先寫死 momentum 公式

### Phase C — Harvest + Watcher
- MFE/MAE/time-to-MFE
- 動態 harvest_fraction
- runner / decay
- 持倉中監測

### Phase D — Event 殺刀
- Family Collapse
- State × Path × Cost × Crisis
- HARD_FAIL 必須能出現
- protocol_hash 鎖定前後一致

### Phase E — 才考慮
- 更多 Event class
- 更多工具表達
- Shadow 擴大
- 仍不開 Evolution / Capital / LIVE

任何階段發現證據層不可靠：停止向上，先修 EVB。

---

## 13. 給接管 Bot 的操作禁令

不要：

- 推翻重做
- 把 PULSE 變回策略搜尋器
- 因為 21 筆交易好看或難看而改門檻
- 把 2023–2026 繼續叫純 OOS
- 把 next-open 寫死
- 用假 sector / 假 options / 假 breadth 補組合動能
- 把 shadow PnL 寫回 EVB fitness
- 解鎖 Evolution / Capital / FINAL_OOS / LIVE
- 為了製造 PASS 或 HARD_FAIL 而改規則
- 因 Event 池是 0 而放寬證據

要：

- 先落地 schema 與切分誠實性
- 先讓系統能殺死 FALSE_PULSE
- 先讓 Harvest 讀 MFE/MAE
- 先讓 Execution 成為可比較假說
- 先讓 Trade DB 留下「我以為 vs 實際」

---

## 14. 一句話

PULSE 不是每天找交易的策略引擎。

PULSE 是：

> 在市場平時什麼都不做；  
> 當狀態突然轉換、出現值得用小代價購買巨大上行（或非對稱）路徑的短生命事件時才進場；  
> 用 Watcher 看路，用 Harvest 拿錢，用 Runner 留尾，用 Decay 離場；  
> 再把每一次「以為 vs 實際」交回 EVB 殺錯，而不是交回自己改門檻。
