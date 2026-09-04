# Grok Build App — PULSE v2 接管指令（可爆算力，不可開鎖）

你現在接管的不是新專案，是 EVB → PULSE 的第二層架構升級。
參考實作已在 `pulse_v2/`。先讀再寫。不要從零開始。

## 你的任務不是找出好策略

PULSE 的單位是 `PulseEvent`，不是 Strategy。
真正目標：建一台能可靠殺死 FALSE_PULSE 的研究機器。
殺錯的能力 > 找冠軍的能力。

算力可以開很大，但只准用在：

- 掃 State Transition
- 比較 5 種 execution family
- 算 MFE / MAE / time-to-MFE / time-to-failure
- Family Collapse
- 故意破壞測試
- Event class 的條件期望（依 split 分開，禁止混窗調參）

算力不准用在：

- 加 genome / 開 Evolution
- 開 Capital / LIVE / FINAL_OOS
- 開 Survival v1 並宣布 PASS
- 把 2023–2026 洗成 Frozen OOS
- 把 NEXT_OPEN 封神
- 把 shadow PnL 寫回 fitness
- 用 fwd5/fwd10/fwd15/fwd20
- 插補 VXX / 假 sector / 假 options

## 現成分層

```text
EVB     什麼證據可以信
PULSE   現在有沒有短命非對稱 Event
EXEC    哪種進場假說較不蠢（比較，不封神）
WATCH   進場後路徑
HARVEST 拿多少、留不留 Runner
JOURNAL 我以為 vs 實際
KILL    Family→State→Path→Cost→Crisis→Survival（Survival 鎖）
```

## 資料切分（寫死）

- TRAIN 1999–2015 可調參
- VALIDATION 2016–2019 可調參
- CRISIS_STUDY 2020–2022 不可當 Frozen OOS
- 2023–2026 = UNPROVEN_OOS
- FROZEN_OOS = 目前不存在
- SHADOW = 任何重播，evidence_tag=HYPOTHETICAL
- LIVE = LOCKED

OOS 不是因為被叫 OOS 就成立。
若你看了 2023–2026 結果後改 threshold，該窗永遠不能升級。

## Execution

Signal 與 Execution 拆開。
家族：IMMEDIATE / DELAYED / NEXT_OPEN / PULLBACK / CONFIRMATION
日線誠實規則：用當日收盤特徵偵測，則當日收盤成交 = 前瞻。誠實 IMMEDIATE = 次一開盤。
NEXT_OPEN 只是 EXECUTION_HYPOTHESIS，不是預設。

## Radar

不要寫死 momentum = 價格加速 + 量 + RSI。
觀察 price/vol/rel/regime/liq/cross_vol/cross_rates 的轉換。
層級：SINGLE / PAIR / BASKET / CROSS / COMPOSITE
本面板沒有的：SINGLE_STOCK、SECTOR_BASKET、OPTIONS、FX、COMMODITY → CAPABILITY_MISSING
VXX null → 該家族 DISABLE，不插補
fwd* → 刪除，進入 Radar 就是 FAIL

## Harvest

禁止固定 25%。
必算 MFE MAE time_to_MFE time_to_failure decay。
MFE 蓋不過成本 → 全出，不留 Runner。
decay → 剩餘出完。

## 殺刀

每個 Event / execution family 都攻擊。
n_paths < 10 → INSUFFICIENT_SAMPLE
mfe<=0 → FALSE_PULSE
cost×3 死 → HARD_FAIL
危機窗不對稱 → HARD_FAIL
UNPROVEN_OOS 不得畢業成 SURVIVING / ROBUST
ROBUST_EVENT 永遠 = 0（Survival 鎖）
HARD_FAIL == 0 且 Event 很多 → 停止加規則，審問為何殺不死
同 skeleton+direction+regime = 1 票

## 禁止回灌

Observed → Experiment → Validated → Candidate
shadow PnL 不得寫 gene.fitness / threshold / protocol

## UI 若你要做 App

必須能看到：

- WHY NOW / WHAT CHANGED
- NO_TRADE 是合法大字
- 資料切分標籤（UNPROVEN 不能畫成 OOS 綠燈）
- execution family 比較表，沒有冠軍徽章
- MFE/MAE 路徑
- Family Collapse 票數
- 殺刀計數：FALSE_PULSE / FRAGILE / INSUFFICIENT / HARD_FAIL / ROBUST=0
- 攻擊台：解鎖 Evolution 必須 GATE_LOCKED
- 協議 hash

不要做：買入按鈕、資金配置、冠軍排行榜、漂亮權益曲線當封面。

## BUILD ORDER

1. 把本目錄 reference 跑通（`python3 -m pulse.engine` 與故意破壞測試）
2. 對照 IMPLEMENTED / PARTIAL / MISSING / CONTRADICTED
3. 只修 P0：前瞻欄、OOS 謊言、next-open 預設、fitness 回灌、閘鎖
4. 才用算力掃全樣本 Event
5. 仍不開 Survival / Evolution / Capital / LIVE

每一個修復：修復 → 故意破壞 → REJECT → regression。
不要只測正常情況。

## 成功標準

不是 paper PnL。
不是 21 筆勝負。
是：

- 2023–2026 不再被叫 Frozen OOS
- NEXT_OPEN 不再是預設
- fwd* 進不了 Radar
- Evolution 解不開
- fitness 寫不回去
- 報告以 family 票數與 HARD_FAIL 為主
- 每個 Event 答得出 WHAT/WHY/HOW LONG/WHAT KILLS IT
- Journal 有「以為 vs 實際」

若 HARD_FAIL 仍是 0：不要加 Event，先寫「為何死不掉」。
