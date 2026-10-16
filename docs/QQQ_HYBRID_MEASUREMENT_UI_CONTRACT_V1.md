# QQQ Hybrid「度量衡／范／融」Measurement UI Contract V1

**文件用途：**把 repo 長期反覆修正後的核心要求固定成可開發、可測試、可審核的 UI 契約。這是需求規格，不代表本文件列出的研究面板已全部實作，也不把任何歷史回放提升為實盤優勢證明。

## 0. 不可破壞的設計原則

1. **先量度，後建議。** 任意輸入 NAV（例如 100,000 或 1,000,000 USD）都要沿同一計算鏈得出美元／百分比尺度、風險容量和資料缺口；不可寫死「賺 $1,000」、固定合約數或固定最佳 N。
2. **操作台與研究室分隔。** Frozen Original Hybrid／正式 Operator Desk 保持既有策略契約。Put Ratio、N:1／1:N、成本敏感度、機率掃描、最佳化與回放只能在 Research / Scenario Lab，不得自動改寫正式目標倉位或交易權限。
3. **每個數字可追溯。** 所有價格、概率、勝率、成本和容量顯示資料截止時間、來源、樣本數、算法／政策版本與證據類別。不可把 proxy 當 QQQ option IV／Skew，也不可把 EOD 報價當成交。
4. **不能計算就明示。** 缺報價、時間不同步、樣本不足、買賣盤數量不足或保證金未知時，使用 PENDING／BLOCK；不可將缺失填成 0、沿用前值或假設無限成交。
5. **不設策略成敗的固定 CAGR／MaxDD 門檻。** 如實顯示觀察到的報酬、正負日比例、逐筆勝率、MaxDD、ES、尾部及樣本分母。門檻可作使用者的風險偏好情景，但不能被標成通用「通過／失敗」或策略有效性的證明。
6. **滑桿代表假設，不是預言。** 拖動任何 BAR／滑桿，只能重算可由資料及模型支持的結果；同時顯示與基準情景的差值，不得偷偷更換樣本、規則或策略定義。

## 1. UI 版圖：四層而不是一個無限長 Dashboard

### A. Decision Cockpit（日常操作）
首屏回答：資料可信嗎？目前持倉是甚麼？目標是甚麼？最大可加／可減多少？下一步做甚麼及原因？

- 狀態列：模式、資料品質、行情時間、政策版本、來源／run SHA。
- 主決策卡：**CURRENT → TARGET → Δ → ACTION → REASONS → NEXT CHECK**。
- 持倉帳：QQQ CORE、QQQ FAR CALL、VXX UNDERLYING SHORT、VXX CALL-CREDIT SPREAD 分列；現有數量、目標、差額、估值損益、最大可買／賣及原因。
- 市場快照：QQQ、VXX、VIX、VX M1／M2、合約代碼、到期日、期限結構 (S=(M2-M1)/M1)、各來源 as-of。
- Watch／Change Monitor：何種輸入變了、哪條規則接近或觸發、是否由數據新鮮度或缺失資料阻擋。
- Decision Journal：append-only 保存快照、手動覆寫、引擎建議、理由、政策版本及時間；引擎與人工意見衝突須分開記錄。

### B. Measurement / Scenario Lab（度量衡）
用滑桿、切換、矩陣與 BAR 做反事實比較；顯示選中情景與基準差異。研究輸出不自動寫入正式操作台。

### C. Replay / Probability（歷史與可能性）
可按交易日拖動時間游標，重看當時已知資料、訊號、下一個可觀察報價、延遲及當時可行的行動。嚴格區分開發樣本、已看過樣本、驗證樣本和未看過盲測樣本。

### D. Evidence / Data Quality（審計）
可展開每個數字的來源、時間、分母、缺失量、合約腿、報價數量、成本假設、模型版本、阻塞原因與原始檔位置。圖表不可取代原始 CSV／JSON 及可重現 run。

## 2. 全域輸入與切換（每項均可重設、可儲存為命名情景）

### 2.1 資金與投資組合
- NAV：任意正數 USD，數字輸入為主；可配對線性／對數滑桿。不可只支援 $100k／$1m。
- Available Cash、Buying Power、保留現金、可用風險預算、目前持倉與未平倉訂單。
- 使用者持倉可逐列輸入；空白代表「容量試算／未知持倉」，不可默認為已持倉或可自由交易。
- 同時顯示金額、NAV 百分比、每組金額、整數合約數；不得只顯示百分比而隱藏美元結果。

### 2.2 資料來源與信任模式
- 手動輸入／貼入、截圖轉錄後人工確認、OpenD、免費延遲 Cboe VX、公開歷史代理，各來源逐欄標示，不能假設一個來源覆蓋所有欄位。
- 標記 OBSERVED、DERIVED、ESTIMATED、HYPOTHETICAL；顯示 source、as-of、quote time、stale age、欄位覆蓋率。
- 執行估值切換：Midpoint、保守買賣盤側（買入用 Ask／賣出用 Bid）、自訂滑點、歷史實際成交（若有）、壓力成交。
- 時間對齊切換：同時點快照／容許最大時間差；不同步時標 MIXED／BLOCK。
- 樣本口徑：重疊窗口／非重疊窗口、完整樣本／指定區間、開發／驗證／未見樣本。重疊窗口必須提示觀測相依性。

### 2.3 市場狀態與區間
- RV20／實現波動率分位、VIX 狀態、VXN 狀態、VX term slope (S)、期權 IV／Skew（只有真實欄位存在時）。
- 起止日期、持有期 1／3／5／10／20／30／45 個交易日及自訂天數。
- 價格變動門檻：±1%／3%／5%／10%／20%／自訂；亦可掃描跌幅 0–100% 的壓力曲線。
- 狀態分桶邊界可調，但每次變更都要顯示每桶 N、覆蓋率與區間估計。VIX／VXN 桶只是分析分組，不是固定交易訊號。

### 2.4 倉位與策略模式
主操作台既有腿須分開呈現，不能混名：

| 腿 | 必須可輸入／顯示 | 重要邊界 |
|---|---|---|
| QQQ CORE | 股票數量、參考價、目前市值、NAV 比重、目標比重 | 數量由資金／目標比重／價格推算時要標 DERIVED |
| QQQ FAR CALL | 到期、DTE、Strike、Delta、Bid／Ask、兩側 size、credit、張數、預算口徑 | 報價及信用金額不明時 PENDING，不可捏造每組固定 credit |
| VXX UNDERLYING SHORT | 股數、NAV 比重、可借數量、借券年費率（初始研究情景可用 3%，必須可改）、持有天數、借券／召回狀態 | 是 VXX 正股／ETF 的空倉，與 VXX option 完全分開 |
| VXX CALL-CREDIT SPREAD | Short／Long call 腿、到期、Strike、Delta、Bid／Ask、size、credit、最大損失、張數 | 是期權價差，不可與 VXX 正股空倉合併 |
| PUT RATIO（研究區） | 1 Long／N Short 與 N Long／1 Short；N=1–6；Put 各腿合約 ID、到期、Strike、Delta、Bid／Ask、size | 永遠獨立於正式 Hybrid；缺失腿不補假合約，不允許研究結果自動部署 |

- 策略檔案切換：Frozen Original Hybrid（只讀）、目前手動持倉、使用者副本／假設情景、研究專案。每一模式須明示能否改政策、是否只供試算。
- 腿開關：只在情景中啟用／停用某腿，旁邊顯示加入／移除的增量 P&L、尾部風險、資金占用與資料完整度。
- 比例開關：1:N／N:1、N=1–6；數量必須受每腿方向、顯示 size、整數合約、現金、風險及保證金限制。
- 期權選擇滑桿：DTE、Delta、Strike 距離／百分比、Spread Width、到期選擇規則；保留使用者手動指定合約優先，不可靜默換合約。
- 價格與 Greeks 來源：Provider 值／估算值分開呈現；BS_ESTIMATE 不得顯示成觀測 Delta／IV。

## 3. 核心 BAR／滑桿（要看拉扯，不只看單一答案）

### 3.1 NAV Risk BAR（資金度量）
- 可選 0.25%、0.5%、1%、2%、3%、5% NAV，亦容許自訂比例；即時換算美元額。
- 顯示「每組壓力損失 × 可承受組數 × 報價容量 × 保證金容量」四者中最嚴格的限制。
- 顯示 Risk Budget BAR：預算額、目前風險、加入一組後風險、剩餘風險；風險超額時 MAX BUY=0 並說明是哪一道限制。
- 必須支援大、小帳戶、不可整除的 NAV、每腿合約不可分割與購買力不足情況。

### 3.2 Cost Drag BAR（成本拉扯）
同時顯示 Midpoint P&L 與可觀察報價側淨平倉 P&L；分拆：
- 開倉價差、平倉價差、每腿滑點、佣金、交易所／監管費（若提供）、VXX borrow carry、行使／指派相關費用（若未知則列未知）。
- 成本情景：ZERO_FRICTION_BOUND（仍保留可觀察 Bid/Ask，不等於零價差成交）、BASE、ADVERSE、CUSTOM。每個情景可調每腿每邊滑點與每合約每邊佣金；初始比較可沿用 $0／$0.025／$0.05／$0.10 每腿滑點及 $0／$0.65 每合約每邊佣金。
- 顯示 cost drag 的中位數、P75／P95、相對 NAV 比率及合格樣本數；顯示淨目標 (T) 的中點參考線 (T+CostDrag)，清楚註明這是估值換算而非成交觸發。
- BAR 應允許拖動滑點、佣金、借券年費與成交量假設，並即時看到勝率、期望值、PF、尾部指標的變化；如果成本樣本不足，顯示 PENDING 而非成本為零。

### 3.3 Profit / Stop BAR（進退價尺）
- 目標與止損可用美元或 NAV 百分比輸入，兩者互相換算；不把 $1,000 當成固定優化答案。
- 預設候選標尺可列 0.25%／0.5%／1%／2% NAV，以及使用者自訂值。
- 退出策略切換：持有到 DTE≤7 後備規則、淨盈利目標全平、淨虧損止損全平、達到目標後減少 Short、減半／指定腿數、剩餘最大利潤百分比目標、特定日數無盈利則退出／減倉。
- 時間切換：第 3／5／10／20 日等；對同一訊號比較全平 vs 減 Short、訊號日成交假設 vs 下一個有效報價日執行，以及 0／1／2 個觀察交易日延遲（只有資料支持的延遲才能回放）。
- 顯示觸發次數、觸發後行動成功執行數、被缺價延後數、觸發至執行的延遲分布、後續 5／10 日 giveback／recovery；不可把 EOD 首次標記觸及描述成盤中確實觸及。

### 3.4 Probability BAR（概率而非裝飾性百分比）
至少提供三個互相獨立、不得混成同一個「勝率」的區域：

1. **QQQ 價格路徑頻率：**在各持有期內 P(up)、P(down)、P(drop ≥x%)、P(rise ≥x%)；顯示樣本 N、分位數 P05／P25／Median／P75／P95、名義區間及是否重疊窗口。
2. **策略逐筆結果：**P(net P&L > 0) 的 episode 勝率、勝／負／平手／未結算數、淨期望值、Profit Factor、最差／最佳單筆、P05／P95、最大回撤、ES／CVaR、QQQ→0 等壓力損失。這才是策略逐筆勝率；不可拿正收益日比例或 QQQ 跌幅頻率替代。
3. **條件概率：**按 RV20、VIX／VXN、期限結構、DTE、Delta、流動性、方向、N、成本、退出政策分層，顯示每桶樣本量與區間；樣本太少時顯示 INCONCLUSIVE。

- 勝率的分母是已結算／可評估 episode，未結算與缺價 episode 另行顯示，不可當勝或負塞入分母。
- 名義 Wilson interval 可作初步視覺化；跨時期聚集／重疊窗口須另用非重疊事件或時間區塊 bootstrap 等依賴性檢查。區間寬度及樣本選擇偏差須可見。
- 每張圖可切換原始頻率、非重疊頻率、條件頻率及估計區間；不可只展示百分比而隱藏 N。
- 顯示的是歷史經驗頻率／模型條件估計，而非承諾未來事件率。

### 3.5 Capacity / MAX BUY / MAX SELL BAR（可成交性）
- MAX BUY 不能只由 NAV 算出：取整數合約後，須同時通過可用現金／購買力、情景壓力損失、每腿顯示 Bid／Ask size、券商保證金與集中度限制。
- MAX SELL／REDUCE 受現有持倉量、可觀察平倉側 size、合約可識別性與買賣方向限制；減倉上限優先於增加風險。
- 容量 BAR 分別顯示 NAV risk cap、broker margin cap、leg quote-depth cap、available-cash cap、integer-unit cap，並指出真正 binding constraint。
- 若沒有券商保證金或即時 size，就顯示「理論容量／非實盤批准」或 BLOCK；不可默認無限可借、無限保證金或所有腿都成交。
- Current／Target／Max Buy／Max Sell／Action 必須四分開，不能把「理論目標」直接寫成下單量。

### 3.6 Distribution / Sensitivity BAR（改一個條件看答案如何變）
- 雙參數 heatmap：NAV × N、N × 方向、DTE × Delta、成本 × 退出策略、VIX／VXN／RV20 × 持有期。
- 一維滑桿：資金、風險預算、N、成本、持有天數、目標／止損、延遲、成交 size、借券費、波動率衝擊。
- 圖中同時標出基準點、目前選定點、阻塞區、樣本數不足區，顯示輸入改變的增量，而不自動挑選歷史最佳點。
- 可切換「最佳歷史結果」與「在成本／滑點／資料缺失擾動後的穩健區域」，但必須標記選擇偏差；不得用反覆掃描同一段資料的最高數值作成功證明。

### 3.7 Stress BAR（邊界／奇異點）
- Underlying shock：±1／3／5／10／20／40／100% 及自訂。
- IV shock：不變、+5／+10／+20 volatility points（限 IV 有觀測或模型假設可用）；Skew shift 只有資料／模型支持時可調。
- Spread／滑點：基準、2×、3×；size：100%／50%／25%／無有效報價。
- 時間／營運壓力：缺一腿、延後一日／兩日、跨到期、早行使／指派、借券召回、保證金提高、強制平倉價格跳空。
- 顯示在哪個狀態 MAX BUY 變成 0、估計風險超過預算、條件概率反轉或結論由 READY 轉 PENDING／BLOCK。

## 4. 指標定義（所有頁面共用同一口徑）

| 指標 | 定義／呈現要求 |
|---|---|
| Episode win rate | 淨 P&L > 0 的已結算 episode ÷ 可評估已結算 episode；旁邊顯示勝／負／平手／未解決數 |
| Daily positive ratio | 正收益日 ÷ 有效收益日；明確標為日收益命中率，不是逐筆勝率 |
| Price-path probability | 選定期限和門檻達成的歷史窗口數 ÷ 合格窗口數；顯示窗口是否重疊 |
| Net P&L | 以選定成本情景及明示的買賣盤方向計算；拆出毛 P&L／成本拖累 |
| Expectancy | 總淨 P&L ÷ 可評估 episode，另顯示中位單筆結果 |
| Profit Factor | 正淨交易總盈利 ÷ 負淨交易總虧損絕對值；無虧損樣本要標明不可穩定估算，不能只顯示無限大 |
| Tail / ES | 最差單筆、P05、選定置信水準的 ES/CVaR、QQQ→0 終端情景、可行範圍內的中途 MTM 壓力 |
| Drawdown / recovery | NAV 曲線的 MaxDD、時間至恢復與未恢復時長；若無完整組合 NAV 曲線，顯示 N/A／BLOCK |
| Cost BAR | Midpoint valuation − conservative quote-side net liquidation valuation；不得稱作真實已成交成本 |
| Quote coverage | 已有效標記所需觀測數／所需觀測數；另外顯示缺失腿／日及被延後行動 |
| Capacity | 多重限制下整組可用整數單位；顯示每一上限與 binding constraint |
| Confidence / interval | 方法、分母、時間依賴性、區間寬度；不可將名義區間寫成未來保證 |

## 5. 狀態語義與輸出契約

- **READY（研究計算）**：該項計算輸入完整；不等於策略有優勢或獲券商批准。
- **PENDING**：缺少必要但可補的報價、到期／腿資訊、時間戳、size 或成本欄位；顯示缺甚麼。
- **BLOCK**：資料陳舊／衝突、風險限制超額、容量為零、無有效合約／退出價格、關鍵保證金或執行條件不可用，或正式操作模式不允許此研究策略。
- **ESTIMATED ONLY**：使用代理資料、BS Greeks、插值／壓力假設等；必須點明代理及用途。
- **INCONCLUSIVE**：樣本太少、未結算過多、條件桶過度稀疏，無法作可靠比較。
- **OBSERVED／DERIVED／ESTIMATED／HYPOTHETICAL** 為證據標籤而不是策略分數。缺失值不得靜默降級成 0。

所有輸出列必須至少包含：Scenario ID／設定 hash、NAV、方向與 N、成本情景、持有期／退出規則、樣本 N、有效報價覆蓋率、淨損益、勝率口徑、風險量度、容量、證據狀態和原因。任何一個關鍵欄位改變，都應能重現比較。

## 6. 自動驗收案例（UI 與計算契約）

1. 輸入 NAV=$100,000，再改成 $1,000,000，再改成任意金額；所有金額尺度、風險預算與容量即時變化，不把任何固定數字當答案。
2. 同一個情景切換 Midpoint／Bid-Ask／Base／Adverse：成本 BAR、淨損益、勝率和 PF 一起更新，原始觀測與假設分清。
3. 把一條腿的 bid、ask 或 size 清空：相關情景變 PENDING／BLOCK，不使用前值，也不把成本視為零。
4. 由 1:1 改成 1:5 或 5:1：每腿數量、尾部損失、整數容量、勝率分母與淨損益全部依比例重新計算；短腿增加不能只展示權利金增加。
5. 由第 5 日目標退出改成第 10／20 日、全平改減 Short、加入 1 日延遲：顯示觸發／執行差、延遲樣本與結果差，不能用觸發價當成交價。
6. 零個合資格樣本、0 個可承受整組、來源過期、歷史鏈截止日之後的選項資料缺失：分別呈現 INCONCLUSIVE／BLOCK／PENDING，而不是編出百分比。
7. 顯示 95% 勝率時，同時顯示 N、勝負數、未解決數與區間；改用日收益口徑時必須改標題和分母。
8. Research Lab 的 N:1／1:N 結果不可改寫 Frozen Original Hybrid、正式 sizing、手動帳本或券商訂單。
9. 對同一 SHA、同一設定、同一來源快照重跑，匯總數字和輸出 hash 可核對；下載失敗不影響已完成的核心計算，也不可假裝外部資料已成功。
10. 圖表每個滑桿、開關、篩選都必須改變一個清楚標示的輸出；沒有功能的裝飾控件不准出現。

## 7. 分階段實作順序（避免一次做成另一個巨型頁面）

- **Phase 0 — 契約／可信度：**所有頁面統一資料狀態、來源標籤、分母、NAV 任意輸入、缺失處理、可重現情景 ID；沿用現有 Current→Target→Action 和 journal。
- **Phase 1 — 操作必需：**資金／持倉輸入、分腿 ledger、即時價／VX M1/M2 freshness、Current／Target／MAX BUY／MAX SELL／Action／Reasons、PENDING／BLOCK。
- **Phase 2 — Research BAR：**Cost Drag、風險預算、N 方向／比例、目標止損、持有期／延遲切換、條件概率與樣本數；只讀研究輸出，不進正式 sizing。
- **Phase 3 — Replay／壓力：**時間游標、逐 episode 回放、成本與流動性壓力、尾部／ES／回撤恢復、依賴性區間。
- **Phase 4 — 融合：**只有逐項經獨立核對、資料口徑與測試過關的計算，才可從 Research Lab 提升至操作台；提升須有明確版本、差異與回滾路徑。

## 8. Linux BOT 的重研究規則

凡涉及高下載／大檔、歷史期權鏈、長區間回放、多維矩陣、外部資料補充與輸出持久化，優先交給 `grokbot-box-linux-x64`。快取必須 SHA／manifest 驗證，置於 self-hosted runner 的工作區以外，避免每次 checkout 清除；不以大型 Actions cache post-job re-upload 作日常持久化機制。必要研究輸出要帶 run SHA、來源結束日期與清單，保存到 repo 的獨立 research/recovery 位置；不可只依賴易受配額限制的 ZIP artifact。

輕量 UI／契約測試可使用對應的 self-hosted workflow。高下載工作不可靜默改派到 hosted runner；不得因加速而取消 SHA pin、缺失檢查、成本／報價限制或 BLOCK/PENDING。

## 9. 核心函數應當是狀態依賴，而不是固定參數

預期決策不是單純 `Output = f(NAV)`，而是：

`Output = f(NAV, cash, current holdings, market regime, option legs, quote depth, volatility state, DTE, cost assumptions, action delay, source quality, position history, broker constraints)`

同一筆 NAV 在不同波動／期限／流動性／已有持倉狀態下可以合理地得到不同目標；同一個概率也必須跟隨樣本區間與狀態分組，而不是被顯示成固定真理。若第三變量（例如流動性惡化）同時解釋「高成本」與「低勝率」，UI 必須讓它能被單獨切換，以免錯把相關性當直接因果。

**最終完成標準：**使用者輸入資金、提供當下可核實行情／期權腿及持倉後，系統能把已知、衍生、估計、假設與未知分開，算出可審核的目標／容量／成本 BAR／概率與勝率，並對不能安全計算的情景說清楚 PENDING 或 BLOCK 的具體原因；而不是永遠找一條漂亮曲線或把更多功能塞進首屏。
