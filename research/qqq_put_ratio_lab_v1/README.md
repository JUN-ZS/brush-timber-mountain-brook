# QQQ Put Ratio Research Lab V1

獨立研究面板：檢視歷史交易勝率、終端尾部損失、QQQ 正股回撤頻率及時間／波動下跌頻率。它不改動 V3 Hybrid 正式決策頁、主策略、live sizing 或券商訂單權限。

## Windows 啟動

在此資料夾執行 `RUN.cmd`，使用瀏覽器開啟本機網址 `http://127.0.0.1:8765/`。需要現有 Python 3；沒有外部 JS 套件、沒有 broker API。

## 研究資料

- 期權：2018-03-01 至 2025-12-15；62 組非重疊 LONG 1 / SHORT 5 QQQ Put episodes。
- 成本：每腿每邊滑點 $0.05、每張每邊佣金 $0.65 的基準情境。
- 正股：1,960 筆 QQQ 日收市資料；歷史機率按 RV20 狀態及 1、3、5、10、20、30、45 個交易日統計。
- 退出政策：DTE ≤ 7 短倉風險處理、固定金額獲利／止損線、25%／50% 終端最大收益比較、第 20 日非正損益退出或減倉。
- 尾部風險：兩種比例方向、N=1–6 的觀察終端損失統計。

## 解讀限制

1. 只有 LONG 1 : SHORT 5 直接引用已保存的 62 組歷史單位交易勝率；其他 N 不會複製同一個勝率。
2. $80,000 NAV 的 0.5%／1%／2% 候選提醒線為 $400／$800／$1,600。已跑的固定金額退出實驗是 $500／$1,000／$2,000；$800 本身不是已獨立驗證的最佳獲利線。
3. 回撤表是 QQQ 正股由高位至下次創新高週期的最大回撤發生頻率，不是 Put Ratio 帳戶的 MaxDD。策略帳戶 MaxDD 需要連續日度持倉 MTM、再入場、資金配置、成本及保證金／強平規則。
4. 期權回放取自 EOD 歷史報價鏡像，是保守 quote-side replay，不是確認成交。精確 tick 時間、實際成交、券商保證金、指派及途中強制平倉仍未驗證。
5. 正股價格下跌機率不是 Put Ratio 的虧損機率。期限重疊造成樣本相依，名義 Wilson 區間不是獨立樣本的保證區間。
6. 歷史資料已經被研究過，不是盲測 OOS。所有提醒只供人工覆核；部署狀態保持 BLOCKED。

## 來源

- Study SHA: `7653cfbaea92f07b123e9377d6b720c2b37a95b9`
- Actions run: https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38778540717
- Research outputs: https://github.com/JUN-ZS/brush-timber-mountain-brook/tree/research/qqq-put-ratio-exit-measurement-v1/research/qqq_put_ratio_exit_results_v1/run-7653cfba
