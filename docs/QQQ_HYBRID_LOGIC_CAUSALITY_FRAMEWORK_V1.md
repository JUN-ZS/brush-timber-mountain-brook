# QQQ Hybrid — Logic, Causality & Evidence Framework V1

**狀態：**架構契約／待驗收，不代表每個子系統已實作。先完成此文件與各項契約測試，才可把研究輸出接進 UI。本文不批准新策略、不改 Frozen Original Hybrid、不改任何 live sizing，也不開啟券商訂單。

**配套文件：**[Measurement UI Contract V1](./QQQ_HYBRID_MEASUREMENT_UI_CONTRACT_V1.md) · [Shared Data Contracts V1](./QQQ_HYBRID_SHARED_DATA_CONTRACTS_V1.md)  
**現有實作基準：**V3 `engine.js`、`RECONSTRUCTION_CONTRACT.md`；獨立 Put Ratio replay 與 `SCALE_VOLATILITY_CONTRACT_V1.md`。規格中的「Observed／Code-reviewed」是已讀取的資料或程式；「Derived」是可由規則推導；「Hypothesis」是待測因果解釋；「Unknown」是尚無足夠資料的事項。

---

## 0. 第一原則：先定義什麼可以被推論，再定義畫面

系統不是「輸入 NAV → 算數量」的單一公式。它是一串有明確邊界的轉換：

```
RAW SOURCES
  → NORMALIZED, TIMESTAMPED FACTS
  → DATA-QUALITY / PROVENANCE GATE
  → DERIVED MARKET FEATURES
  → REGIME CLASSIFICATION (only if eligible)
  → FROZEN POLICY TARGETS
  → CURRENT LEDGER RECONCILIATION
  → RISK / CASH / MARGIN / QUOTE-DEPTH CONSTRAINTS
  → TARGET + MAX BUY / MAX SELL + ACTION + REASONS
  → HUMAN REVIEW / EXECUTION (outside this engine)
  → ACTUAL FILL / POSITION / COST RECORDS
  → APPEND-ONLY JOURNAL + LATER RESEARCH
```

這條鏈的因果方向不可倒轉：未來報價、未來損益或回測最終結果，不得流回歷史決策點；UI 手動選擇也不得偷偷改變 Frozen Policy。研究輸出只可成為新版本的候選證據，不能直接覆寫現有策略。

### 0.1 四種因果陳述

- **OBSERVED（觀察）**：來源確實提供的值、合約、時間戳、size、成交記錄或持倉記錄。必須有來源與 as-of。
- **DERIVED（推導）**：例如 (S=(M2-M1)/M1)、市值、NAV 比例、價差或由明確公式得到的 target。必須列出輸入欄位與版本。
- **ESTIMATED（估計）**：例如從模型推算的 Greeks、價格概率區間、滑點假設下的結果。必須列出模型與假設，不能冒充觀察值。
- **HYPOTHETICAL（假設）**：未觀察過的極端情景，例如 QQQ 歸零、IV 跳升、size 減少、保證金上調。只用來找邊界，不可混進歷史勝率分母。

**相關不等於因果。** 同一市場狀態可能同時造成 option spread 擴大與策略勝率下降。沒有配對事件、合理比較與能排除替代解釋的設計，不得說某個變量「造成」盈利或虧損。

---

## 1. 系統框架地圖：一個資料根、一套狀態語義、多個獨立引擎

| 子系統 | 主要輸入 | 輸出 | 可改變什麼 | 不得做什麼 |
|---|---|---|---|---|
| A. Source / Provenance | 原始來源、版本、請求時間、資料時間、hash | 帶來源與時間的原始事實 | 資料新鮮度與可信度 | 不可在來源失敗時悄悄換成未標示的 proxy |
| B. Normalizer / Clock | 價格、合約、日期、時區、欄位 | 統一單位及時間的資料列 | 欄位可否比較 | 不可把缺值補 0、把不同時間當同一快照 |
| C. Data Gate | 必要欄位、age、時間差、完整性 | FRESH／STALE／MIXED／PENDING／BLOCKED | 可否計算／可否提出行動 | 不可由行情有值就推論期權腿也有有效報價 |
| D. Feature Engine | 通過 gate 的已知事實 | term slope、RV、DTE、spread、exposure | 只產生可追溯特徵 | 不可從未來或非同步資料生成當時訊號 |
| E. Frozen Regime / Policy | 特徵、現有凍結規則與版本 | regime、policy target、原因 | 原政策所允許的目標 | 不可由研究最佳化直接改政策常數 |
| F. Ledger / Accounting | NAV、現金、持倉、訂單、fill、費用 | Current、市值、成本、損益、對帳差 | 對帳及暴露 | 不可把建議委託當已成交持倉 |
| G. Capacity / Risk | target delta、tail payoff、現金、margin、腿 size | MAX BUY／MAX SELL／binding constraint | 限制可行數量 | 不可只靠 NAV 或 premium 算容量 |
| H. Option Contract Engine | 合約 ID、expiry、strike、type、bid/ask/size、Greeks 來源 | 合約候選、價差、payoff、每組風險 | 候選是否完整及可計算 | 不可靜默代換缺腿或混用不同到期 |
| I. Research Replay | 合約固定規則、時間序列、執行規則、成本 | 每事件結果、觸發、延遲、未解決狀態 | 研究假設的對照比較 | 不可把 EOD marker 寫成真實 fill |
| J. Probability / Statistics | 逐事件結果、狀態、完整分母 | 頻率、勝率、區間、分布 | 不確定性與樣本可信度 | 不可混用正收益日率、標的跌幅與策略勝率 |
| K. UI / Journal | 經驗證的 engine output、使用者選擇 | 視覺化、比較、人工備註、append-only history | 展示與審核 | 不可對計算作隱性修正、不可產生自動下單權限 |

每一個引擎都應可單獨測試；跨引擎只透過明確資料契約交接。任何一個引擎失敗，必須保留失敗狀態，不能用另一個引擎的成功結果遮蓋。

---

## 2. 時間、來源及資料狀態框架

### 2.1 每一個值的最小資料契約

每個會影響決策或結果的欄位都應能追溯：

- `value`、`unit`、`field_name`
- `source_id`、`source_class`、`source_version_or_hash`
- `observed_at`（實際觀察時間，如來源提供）、`as_of`（資料代表時間）、`received_at`
- `status`、`evidence_class`、`transformation_id`
- `parent_fields`（這個派生值依賴哪些來源欄位）
- `missing_reason`、`freshness_age`、`quote_size`（適用時）

如果來源沒有精確 quote timestamp，應填「來源沒有提供／未知」，不可自行把日期標籤當成確認的逐筆 timestamp。

### 2.2 FRESH 不等於真實；多個來源也不自動更可信

- **FRESH**：必要來源時間在政策容許範圍內、欄位完整、時鐘與單位合理。
- **STALE**：來源超過已明示的最大資料年齡。
- **MIXED**：關鍵資料來自不同時間點，時間差可能改變狀態或可成交性。
- **PENDING**：資料理論上可補，但目前不完整，例如缺一條期權腿、quote size 或必要 timestamp。
- **BLOCKED**：來源完整性失敗、必須欄位無法確認、政策所需市場狀態不可計算，或正式工作模式不允許該研究操作。
- **ESTIMATED ONLY**：可以算出情景數字，但關鍵輸入為代理或估算；結果不可當成實際行情／成交。
- **INCONCLUSIVE**：計算有效，但樣本資訊不足以支撐比較。

狀態可以同時出現在不同層。例如標的行情 FRESH，但期權鏈 PENDING；不能將整個系統只顯示一個綠色 FRESH。

### 2.3 時間狀態邊界

- 必須分開 calendar age、交易 session age、來源 timestamp 的時間差。
- 缺 timestamp 時，不能把 age 預設為 0 或判定 FRESH。
- 未來 timestamp、系統時鐘不一致、時區解析錯誤、日期格式不明，都應阻止依賴該欄位的決策並給出理由。
- 使用 `max_age` 需依資料型態設定：延遲 VX、日終期權鏈、即時標的和手動截圖不應共用同一個 freshness 規則。
- 同一事件各欄位要保留原始時間，不得只留下合成的「最新時間」而失去不同步證據。

---

## 3. 市場狀態框架：先辨識狀態，再套用 Frozen Policy

### 3.1 期限結構的語義

`M1` 與 `M2` 必須是由實際到期日排序後的標準月度 VX 前兩個有效合約，且 expiry 大於指定 as-of。排除週合約、VXM、VXMT、TAS 等不符合既定研究契約的行。期限斜率：

`S_pct = 100 × (M2 - M1) / M1`

每個 M1／M2 都要保留合約代碼、到期日、來源、as-of 及價格；不准拿 VIX 現貨作 M2，不准把合約平均值或 synthetic term 寫成 observed VX。

### 3.2 V3 Frozen Regime：目前程式所定義的狀態與規則

以下是現有 V3 engine 的**已觀察程式邏輯**，不是新優化結果，也不表示歷史門檻已被證明最佳：

1. **資料不完整／STALE／MIXED**：進入 data blocked / hold 路徑，不新增部署動作。
2. **SHOCK**：VIX ≥ 28 且 (S≤0)。原策略優先降低 VXX seller risk，保留 QQQ core。
3. **PRE-SHOCK / backwardation**：(S≤0) 但未同時觸發 SHOCK。停止新增 carry，降低 seller exposure。
4. **PRE-SHOCK / high VIX**：VIX ≥ 28 且 (S>0)。封頂／降低 seller exposure，停止加碼 carry。
5. **WEAKENING**：(0<S≤5%) 且 VIX < 28。維持觀察，不新增 seller carry。
6. **CARRY**：VIX < 28 且 (S>5%)。凍結基準允許原 carry sleeves 向 baseline target 恢復。

Frozen baseline 常數目前包含 QQQ core 42%、VIX<28 時 VXX seller 18%、VIX≥28 時 10%、VXX call sleeve 2%、QQQ far-call sleeve 1.2%、term safe line 5%。這些只是一套歷史研究所保留的政策常數；它們不是從此文件推出的新建議，也不可被 Research Lab 自動調參。

### 3.3 規則優先序

同時有多個訊號時，執行順序應固定且可測：

```
(1) Schema / source integrity
(2) Data freshness / timestamp alignment
(3) Active mode + policy permission
(4) Frozen market regime and its risk classification
(5) Per-leg contract / exposure validity
(6) Cash, stress-risk, quote-size and margin constraints
(7) Current → Target → MAX BUY / MAX SELL
(8) Human review and journal
(9) Broker execution (separate system; not enabled here)
```

上游的無效狀態不得被下游的高勝率或看似有利的價差覆蓋。容量上限可以把增加風險的數量降為 0；但資料缺失時不能偽造一個「安全減倉委託」。依現有 Reconstruction Contract，關鍵 term source 被 BLOCK 時應保持 CURRENT=TARGET、不新增部署且不自動 REDUCE，同時要把風險未解決清楚呈現給人類。

### 3.4 門檻附近的非線性

必須測試而不是只測一般行情：
- (S=-ε, 0, +ε)；(S=5-ε, 5, 5+ε)。
- VIX (=28-ε, 28, 28+ε)。
- 同一天不同 as-of、同一狀態但不同流動性。
- 一個必要欄位剛好缺失、剛好 stale、剛好超過容許時間差。
- 進入與離開狀態時是否因日間抖動反覆翻轉；如要引入滯後／hysteresis，必須先作研究版新政策，有版本號、有成對比較，不能默默更改 Frozen baseline。

---

## 4. 投資組合與會計框架

### 4.1 Current、Target、Executable Action 是三個不同物件

- **Current**：由已成交持倉／人工確認持倉帳與可核對價格計算。
- **Target**：由 Frozen Policy 或指定 Research Scenario 推導出的目標狀態。
- **Executable Action**：在當前報價、size、現金、風險、保證金及交易規則下可執行的變動上限。
- **Actual Fill**：券商確認的成交，才更新真實成交均價、費用、餘額與已實現 P&L。

因此 `Target ≠ Order`，`Order ≠ Fill`，`Mark-to-market ≠ Realized P&L`。操作台不能把 target delta 直接變成訂單，也不能因手動改動目標就覆蓋原有持倉紀錄。

### 4.2 分腿、不同會計風險不可互相抵銷隱藏

- QQQ CORE：股數、市值、平均成本、未實現損益與 NAV exposure。
- QQQ FAR CALL：期權合約、方向、數量、權利金／成本、價差最大損失與 roll／close 狀態。
- VXX UNDERLYING SHORT：空頭股數、市值、borrow fee、可借量及召回風險。
- VXX CALL-CREDIT SPREAD：分腿合約、credit、width、最大損失與買賣側平倉成本。
- PUT RATIO：僅為 Research Scenario，長短腿、N、到期及 tail payoff 全部獨立；未經核准不能混入 Frozen Hybrid book。

### 4.3 NAV 與可動用資金並非同一個量

至少分別量度 NAV、cash、buying power、已佔用保證金、reserve cash、未成交委託占用、現有壓力風險。不能由 NAV × 某百分比直接斷言能買入或維持相同的整數合約數。

每一組期權的 premium cash flow、max loss、terminal loss、interim liquidation stress 及 broker margin 都應獨立欄位。當實際 margin 不明時，理論 sizing 不能標為 live capacity。

---

## 5. Option Contract / Payoff / Budget 框架

### 5.1 合約身份優先於 Delta 排名

在選出候選前，先驗證：
- 完整標的 root、Put/Call type、合約 ID 與 strike 編碼一致。
- 所有需要組合的腿都是同一個標的、相容的 expiry／contract multiplier，且日期有效。
- Bid／Ask 是有限、非負且方向可用；如 bid>ask，必須標記交叉／品質異常，不可照常使用。
- 每腿的 quote timestamp、bid size、ask size 和來源可確認。
- Delta／IV 是 provider observed 還是 model estimate，必須有來源標籤。
- 使用者手動指定的合約，除非使用者明示更改，不可靜默換到別的 strike／expiry。

先確保整組是可識別且可估值的，再排 DTE／Delta／距離。Delta 接近目標不能拯救不完整或不可成交的腿。

### 5.2 方向、成交側與損益

對保守 quote-side 入場估值：
- 買入腿以 Ask 估值；賣出腿以 Bid 估值。
- 保守平倉：買回 short 以 Ask，賣出 long 以 Bid。
- Midpoint 只是一個對照標記，不是可成交價格。
- 所有組合都要呈現每腿價格、張數、乘數、買賣方向、gross cash flow、commission、slippage 及 net liquidation estimate。

### 5.3 Credit budget 與 max-loss budget 必須分開

這是進入 UI 之前的強制決策：**「用多少權利金預算」不等於「願意承擔多少風險」。**

對價差：
- Net credit 是入場資金流量，不等於最大可能損失。
- 對有限風險 vertical spread，理論最大損失需依寬度與淨 credit 計算；若缺一腿或 payoff contract 不成立，最大損失就是未知，不准假設為零。
- Ratio 結構的尾部風險不能用收到的總 credit 代理。
- 須分開展示：premium/cash budget、scenario risk budget、expiry payoff tail、interim mark-to-market stress、broker margin cap。

只有使用者明確選定 budget semantics 及公式後，才可計算張數。現有 V3 的 `optionQty(nav, budgetPct, credit)` 以正 credit 計算整數數量；在不另加 max-loss 約束的情況下，這只能解讀為以 credit 流量做的預算公式，不能標示為最大損失受控或已通過容量審核。

### 5.4 Put Ratio 方向與極端損失

- SHORT-HEAVY 1 Long / N Short 與 LONG-HEAVY N Long / 1 Short 是不同 payoff；N=1 才是同一個一長一短結構。
- 對每組都必須按完整 payoff 在 0、每個 strike／payoff knot 及必要區間檢查最大 terminal loss，不可只測單一 QQQ=0 值就推斷所有 N 的最大損失。
- Terminal expiry loss、每日 mark-to-market loss、margin call、forced liquidation loss 是不同變量。第一項無法代替另外三項。
- 整數容量要依單組壓力損失與所選 NAV risk budget 計算，然後再次受腿 size、現金和 broker margin 限制。
- 如果容量為 0，UI 仍需展示「為甚麼為 0」與假設邊界，而不是隱藏該策略或把 N 自動換成較小比例。

---

## 6. Capacity Engine：多個上限取最嚴格者

對任何組合增加部位的候選數量 (q)：

```
q_risk   = largest integer units within chosen scenario-loss budget
q_cash   = largest integer units within available cash / buying-power limit
q_margin = largest integer units within verified broker margin limit
q_depth  = largest units executable across EVERY required leg's correct-side quote size
q_borrow = available borrow capacity, for short underlying when relevant

MAX_BUY = max(0, min(q_risk, q_cash, q_margin, q_depth, q_borrow))
```

其中 broker margin 或 quote depth 缺失，不能將該上限預設成 infinity。可在研究畫面另展示「不考慮未知限制的 theoretical capacity」，但必須明示這不是 live capacity。

MAX SELL／REDUCE 不等於上面一式：
- 不得賣出超過已確認的 current holding。
- 期權平倉要按買回 short 的 Ask size、賣出 long 的 Bid size 分別計算；多腿完整風險移除能力受最窄腿限制。
- 如果只能完成一部分，須量度剩餘未對沖腿風險；不能只用平掉的腿數顯示「已減風險」。
- 沒有可用 quote／size 時，應顯示「需要處理，但當前無法核實可執行數量」並進入 PENDING/BLOCK，而非宣稱可以零成本平倉。

每次輸出要指出 binding constraint：risk／cash／margin／depth／borrow／integer unit／data gate。瓶頸隨市場狀態改變，不是 NAV 的固定函數。

---

## 7. 成本因果框架：價差、滑點與流動性不是同一件事

成本至少拆成：
1. 入場 Bid/Ask 差造成的保守側估值差。
2. 出場 Bid/Ask 差造成的平倉估值差。
3. 額外 slippage per leg／side。
4. Commission／fees。
5. VXX underlying borrow carry、召回及其他已知成本。
6. exercise／assignment／margin 相關成本（未知時保持未知）。
7. 行動延遲期間標的與期權報價變化。

必須同時輸出 midpoint gross P&L、side-quote P&L、扣除已指定成本後的 net estimate 及各項 cost contribution。

成本 BAR 的核心因果問題不是「成本加多少」，而是：同一事件與合約路徑在不同成本／流動性假設下，退出是否仍然可執行、net expectancy 如何變、勝率有否只是小幅改變、尾部是否跳升。固定滑點的敏感度只能表示模型對假設的敏感度，不能證明真實市場一定會按該滑點成交。

若成本與市場狀態共同變動，還需要狀態條件：例如 VXN／RV、DTE、spread 寬度、報價量與波動 shock。不能用「全樣本平均成本」套用於流動性最差的極端狀態。

---

## 8. Replay 與因果實驗框架

### 8.1 單一事件先固定，再比較政策

每個 episode 都需要穩定身份：
- signal timestamp／data as-of。
- 固定的實際 listed contract IDs、expiry、strike 與每腿方向。
- 入場訊號、下一個有效觀察日、入場可用 quote side／size、成本情景。
- 每日狀態、可用的每腿報價、缺失／延遲、策略動作、估值與最終結算狀態。
- source end、run SHA、政策版本、scenario hash。

同一個 episode 比較不同退出規則時，應維持相同的入場合約／訊號選擇，差異只在指定的干預變量。若不同退出政策重新挑選不同的入場合約，則結果同時包含 selection effect，不能只歸因於 exit policy。

### 8.2 時間因果／禁止前視

- 時間 t 的決策只能依 t 時已知的資料。
- 若訊號來自 EOD quote，執行時點不可早於下一個實際觀察到且有效的報價。
- 不用未來最高價／最低價判斷當天曾觸及 target，除非資料真的包含盤中路徑且時間戳可靠。
- 不得 forward-fill missing option marks。缺 quote／size 時保留 action deferred、trade unresolved 或 censored 狀態。
- 不可把延後執行的結果回填為訊號日價格。
- 到期 payoff 是結算參照，不代表中途一定有能力承受該路徑或保證金。
- 2025-12-15 之後目前缺少本研究指定的歷史期權鏈；標的價格／VIX／VXN proxy 可以補市場路徑上下文，但不能補出真實 option P&L。

### 8.3 同事件配對實驗

每一輪只讓一個明確維度變動，其他條件固定：
- exit threshold；
- exit action（全平 vs 減 short）；
- action delay；
- slippage／commission；
- NAV／risk budget；
- ratio direction／N；
- quote-size limit；
- volatility state classification。

用 paired delta（同一事件的新政策結果減基準結果）報告增量結果、差異方向、樣本數和未解決事件。不只列出每條 policy 的總損益，還要分析結果是否被一兩個極端事件主導。

### 8.4 三個重要的替代解釋

1. **市場狀態是第三變量。** 高 IV 可能提高收到的 premium，同時標誌更高的標的／尾部風險；不能把 premium 多解讀為 edge。
2. **流動性是共同原因。** Spread 變寬可令回放成本增加，亦可令風險觸發後難以平倉；不能只將 net P&L 變差歸因於退出門檻。
3. **樣本選擇是第三變量。** 只有報價完整、能進入且能結算的事件不一定代表全體事件。必須另外報告跳過、未結算、missing marks、size 不足和 source-end censoring。

---

## 9. Probability / Win-rate 框架：明確分母與不確定性

### 9.1 嚴禁把三種比率混在同一個「勝率」

- **Daily positive-return ratio**：正收益日數／有效收益日數，是日收益命中率。
- **Underlying path frequency**：在指定起始狀態與持有期內達到價格門檻的窗口數／合格窗口數，是 QQQ 路徑經驗頻率。
- **Episode win rate**：已結算、可評估 episode 中，淨 P&L > 0 的事件數／可評估已結算 episode 數，才是策略逐筆勝率。

三者必須分圖、分標題、分分母。任何一項資料缺失，都不能把其值當作另外一項的代理。

### 9.2 每個百分比必須配套的數據

- numerator／denominator、wins／losses／flat／unresolved；
- 規則版本、成本情景、NAV／ratio／N、期間及狀態篩選；
- source coverage、missing quote、deferred action；
- 分位數、區間方法與寬度；
- 重疊／非重疊窗口和依賴性處理；
- data end boundary 與是否曾用於策略挑選。

名義 Wilson interval 只能作二項比例的基本展示；重疊窗口、時間序列聚集或條件事件共用同一日期時，不能將名義二項區間直接聲稱為可靠的獨立樣本區間。應輔以非重疊 offset、時間區塊 bootstrap 或合適的事件單位敏感度；結果差異本身需顯示。

### 9.3 狀態條件不是免費的「更準」

切成更多 VIX／VXN／RV／DTE／N／cost buckets 會減少每格樣本並增加多重比較。UI 必須同時顯示原始 bucket N、有效事件數、區間寬度及多重掃描的選擇偏差。若某個 bucket 看起來勝率 100% 但只有很少事件，要顯示 INCONCLUSIVE，而不是把它排成第一名。

不應只尋找最高歷史勝率；應問：在樣本更新、成本擾動、延遲和狀態分桶改變後，該結論是否仍然存在？

---

## 10. 反事實與狀態依賴框架

每個研究頁面至少須可以回答以下反事實，並顯示同一事件的對照結果：

- 如果 NAV 變 10 倍，美元門檻按比例變動後，合約數是否因整數／size 限制而非線性改變？
- 如果 premium credit 增加，但 quote spread、IV 或尾部風險也上升，淨期望與容量是否仍然改善？
- 如果同一 target 不是在訊號日而是下一個有效 quote 才執行，原本的結果是否還成立？
- 如果把「全平」反轉為「減 short」，剩餘 long convexity 的價值是否足以抵銷未平短腿的風險？
- 如果把高勝率的研究政策換成沒有選擇偏差的未見時段，結論是否仍成立？
- 如果資料狀態由 FRESH 變 MIXED／STALE，原本的 BUY／REDUCE 是否仍是可計算、可執行的建議？
- 如果借券費、價差或 margin 在壓力期不是固定數，而是隨市場狀態上升，持倉容量在哪裡反轉？
- 如果過去的好結果主要由低成本／高流動性時期造成，而非 exit rule 本身，配對狀態後的差異還剩多少？

這些結果是反事實敏感度，不自動等於識別出的因果效果。只有被明確定義的干預變量、合格對照、同一事件配對與對主要替代解釋的檢查，才可使用有限度的因果措辭。

---

## 11. UI 的邏輯契約：控件是一個實驗，不是裝飾

每個滑桿／開關都要定義：
1. 它干預哪個輸入或政策參數；
2. 哪些引擎可以重新計算、哪些資料必須固定；
3. 改動會影響哪些輸出；
4. 哪些輸出不可因該控件改變；
5. 所需來源不完整時轉入哪個 status；
6. 如何恢復 baseline、重現 scenario hash 和查看 paired delta。

例子：
- 調整 NAV：可變更美元 budget、理論數量和容量，但不得改變原始 price path、合約身分或歷史 episode 的 P&L。
- 調整滑點：可改變 modeled net P&L、net win/loss classification 與 cost distribution，不可改變原始 Bid/Ask 或 signal timestamp。
- 調整 exit day：可改變退出動作與退出後路徑，但不可偷改入場腿或將未來 quote 移回訊號日。
- 調整 N／方向：必須重新算 payoff、每腿成交量與容量；不可沿用另一方向的尾部損失。
- 調整 VIX bucket：只能重分組歷史樣本，不能修改來源 VIX 或把 bucket 變成即時交易規則。
- 調整 data source：要重新驗證欄位及時間；同一個混合快照不能假裝是同來源同時點。

任何控件沒有清晰定義以上六項，就不能搬入 UI。

---

## 12. 先修正／先用測試鎖住的現有風險

以下是對現有 V3 `engine.js`（讀取基準 blob `fe83c0f0cd57102db49f90eaffdbdfa87ab8fdd9`）與其契約的 code review finding。此文件只記錄風險，不代表已修正：

### F1 — 缺 timestamp 被當成 age=0
目前 freshness logic 在缺少 term／today 或 spot／term as-of 時，部分 age/gap 分支會落到 0。這可令「沒有時間證據」被誤認為「很新」。**Required rule：**缺少決策所需的 as-of，應標 PENDING／BLOCK；不能計算成 FRESH。

### F2 — 缺期權候選時 target quantity 可能被歸零
目前 `targetLedger` 在非 BUY 路徑下會對目前 option count 與 `optionQty(..., candidate?.credit)` 結果取 `min`；候選／credit 不存在時數量函數會回 0。這可能令 PENDING candidate 被轉成 target=0，而不是保留原 current／顯示無法計算。**Required rule：**「無候選／無可用平倉報價」是資料狀態，不等同「經策略明確要求平掉全部」。必須分開 `target quantity` 與 `executable close quantity`，以 golden tests 證明無資料時不會產生隱性清倉目標。

### F3 — Premium-credit sizing 不等於風險預算容量
目前 `optionQty` 以正 credit 與 NAV budget 計算數量。若 budget 被理解成 max loss，這種計算法沒有達成該語義。**Required rule：**credit／cash budget、最大到期損失、盤中 MTM stress、broker margin 分欄計算；未確定 budget semantics 前不可用單一 qty 代表風險已受控。

### F4 — 候選合約的身份／深度必須先通過完整契約
候選掃描需要證明同一 expiry、同一 root/right、有效且同步的 Bid/Ask、雙邊 size、乘數和完整每腿身份。只有價格及 Delta 近似值不足以認定整組可成交。**Required rule：**chain candidate 與 capacity engine 分開；candidate found 不等於 READY、READY 不等於 executable。

### F5 — Data block、position risk 與可執行減倉的衝突
現有 Reconstruction Contract 規定資料 BLOCK 時 CURRENT=TARGET、不新增部署、不自動 REDUCE；這能避免假資料觸發未經驗證的交易，但也代表市場風險可能在 stale 時無法被量化。**Required rule：**同時顯示「不可計算／不可自動行動」及「目前風險未解決、需人工確認」，不可將 HOLD 文案表達成持倉安全。

### F6 — 保證金、指派與中途強平缺口
目前 Put Ratio 研究的 terminal payoff 不包含完整券商初始／維持保證金、早行使／指派、盤中 IV 擴張與強制平倉路徑。**Required rule：**這些維持 UNKNOWN／HYPOTHETICAL；不得以 terminal tail loss 或 95% historical win rate 代替。

### F7 — NAV、持倉與 option cashflow 語義須統一
現有 UI、budget 常數與研究版本曾以不同口徑使用 credit／budget。**Required rule：**先定義 NAV source、cash／buying power、各腿權利金與 max loss 的公式和方向，並用算例確認 ledger 守恆，再建控制面板。

---

## 13. 邊界／故障驗收矩陣

| 類別 | 注入條件 | 正確結果 | 禁止結果 |
|---|---|---|---|
| 時間 | as-of 缺失／未來時間／timezone 無法解析 | PENDING／BLOCK + 明確原因 | age=0／FRESH |
| 混合來源 | spot 與 term 超出容許差 | MIXED；按操作契約禁止新增部署 | 只展示最近值並標 FRESH |
| Term | M1/M2 缺值、expiry 不合法、排序反轉 | BLOCK；不建立 S | VIX 替代 M2 |
| Term boundary | (S=-ε,0,+ε,5-ε,5,5+ε) | 狀態與原因符合凍結規則 | 隱性四捨五入改變狀態 |
| VIX boundary | (28-ε,28,28+ε) | 依定義的 (geq 28) 分界 | 不同頁使用不同比較符號 |
| Option | 缺一腿／到期不同／root 不符 | PENDING/BLOCK；無虛構組合 | 靜默換腿 |
| Quote | bid/ask 非有限、bid>ask、size=0 | 標記 quote-quality／容量阻塞 | 把無價差看成零成本 |
| Candidate | 缺 chain 或 credit | current 持倉不被候選缺失改寫 | target option qty 默默變 0 |
| Budget | positive credit 但 max loss 超預算 | 風險上限限制 MAX BUY=0 或降低組數 | 只用 credit qty 通過 |
| Ratio | N=1 兩方向 | 1:1 payoffs／容量一致 | 當成兩個獨立策略證據 |
| Ratio | N=2..6，兩方向 | 每一 N 重新算 payoff、size、成本、風險 | 沿用其他 N 的 max loss |
| Depth | 任一腿 size 不足整組 | 按最窄腿限制或 PENDING | 每腿分別有 size 就假設全組可成交 |
| Exit | EOD signal，缺下一日報價 | action deferred／unresolved | 在訊號日成交 |
| P&L | 手續費／slippage 改變盈虧符號 | 更新 net classification，保留 gross 觀測 | 只更新成本文字不更新勝率 |
| Probability | 0 合格事件／小樣本／未解決高 | INCONCLUSIVE + 分母 | 顯示看似精確的勝率 |
| Sampling | 重疊窗口切為非重疊 | 顯示 N 及區間變化 | 隱藏依賴性 |
| NAV | 任意小額／大額／不可整除數 | 金額換算與整數容量一致 | 固定 $100k 或固定單位 |
| Persistence | Artifact quota hit | 研究輸出另有可追溯保存 | 報告成功卻無原始輸出 |
| Replay | 相同 SHA、資料與設定 | 結果可重現、輸出可核對 | 依執行時間／未來資料變更結果 |
| Mode | Research policy 在場景中變更 | 只影響研究情景 | 改寫 Frozen Original Hybrid |
| Execution | 手動 target／建議被保存 | journal 保留人機分歧 | 把建議當 fill／自動下單 |

以上 boundary tests 應在 UI 拿到資料前先存在於 engine contract tests；測試失敗時應阻止介面顯示 READY 數值，而不是只顯示紅色警告。

---

## 14. 驗證框架：證明邏輯一致，然後才討論有效性

驗證分成不能互相替代的五層：

1. **Schema tests**：欄位、單位、日期、expiry、contract ID、缺失狀態。
2. **Deterministic/golden tests**：同一輸入同一輸出；狀態邊界、比例／成本算式、ledger 守恆。
3. **Replay integrity tests**：SHA、來源截止日、沒有前視、沒有 forward fill、每個 episode 可追溯。
4. **Statistical validity tests**：分母、重疊依賴、條件桶 N、區間、未解決與選擇偏差。
5. **Economic/execution validity**：可成交 bid/ask/size、滑點／費用、margin／assignment／interim MTM。回測通過前四層不等於這一層通過。

Monte Carlo 只能在指定模型和參數條件下檢查結果分布，不能單獨證明模型或策略有優勢。歷史上最好的參數點不代表穩健；應比較 baseline、局部擾動、跨狀態與真正未見資料，並保存所有嘗試以辨識多重掃描。

**不使用固定 CAGR／MaxDD 作通用 PASS/FAIL 門檻。** 是否符合特定使用者風險偏好可以作一個清楚標記的個人限制；它不能替代證據品質、可交易性與因果識別。

---

## 15. 分階段 Gate：什麼完成後，才准搬進 UI

### Gate 0 — 邏輯文件（本階段）
- 子系統、資料流、因果邊界、狀態語義、凍結政策、容量公式、統計口徑、未解問題與測試矩陣已寫明。
- UI 控件不能先行獨立設計並自行定義計算語義。

### Gate 1 — 現有引擎風險修正與 golden tests
- 首先處理 F1–F7；至少 F1–F3 要以可重現測試鎖定。
- 保留原始 baseline outputs，對照修正前後差異；不以修正為理由更改原策略參數。
- 所有變更先在獨立分支，不合併主線、不允許 broker order。

### Gate 2 — 共用資料／決策 schema
- 定義 MarketSnapshot、OptionLeg、PositionLedger、ScenarioConfig、DataStatus、RiskCapacity、DecisionOutput、ReplayEpisode、ProbabilityEstimate、EvidenceManifest。
- 每個輸出帶 source / as-of / version / status / blockers / parent fields，並有 JSON fixtures 與 schema tests。

### Gate 3 — 研究引擎的配對可重現性
- 固定 episode 与合約、政策與成本的配對比較可重跑；缺失、延遲、未結算不被隱藏。
- 每張矩陣可回到原始事件；輸出 manifest 帶 source end、tested SHA、run ID 和配置 hash。

### Gate 4 — UI 只呈現已定義的數據契約
- 先接 Current / Target / Action / Reasons / Status / Evidence。
- 每個 BAR 控件要有明確干預變量及 paired delta；未知容量不能顯示 live-ready 數量。
- Research Lab 與 Frozen Decision Cockpit 使用明確 mode boundary。

### Gate 5 — 經獨立審核才考慮融合
- 新規則要證明不是單純掃描最佳值，並通過未見資料、成本、流動性及操作限制。
- 透過獨立 PR、版本化 policy、差異報告和回滾計劃才能納入正式策略。
- 此 Gate 不等於授權自動交易；交易權限需獨立、明確審核。

---

## 16. 最後的架構定義

核心函數不是：

`Output = f(NAV)`

而是：

`Output = f(source facts, timestamp, data quality, NAV, cash, current positions, market state, contract identity, quote depth, policy version, budget semantics, cost model, action delay, broker constraints, position history)`

並且必須保留其依賴關係：

`output.value + output.status + output.evidence + output.inputs + output.version + output.blockers`

系統的成功不是每個情景都能產生一個買賣數量，而是：
- 有足夠證據時，能算出可重現且可核查的結果；
- 變量改變時，能指出哪條因果鏈令結果改變；
- 超出資料或模型邊界時，能精確說出不能推出什麼；
- 發現矛盾時，保留當前與目標、假設與觀測、引擎與人工的差異；
- 沒有可信答案時，能誠實地輸出 PENDING／BLOCK／INCONCLUSIVE。

**在 Gate 0–3 之前，不搬新的研究功能進正式 UI。先使邏輯可檢驗，再讓介面替這些邏輯服務。**
