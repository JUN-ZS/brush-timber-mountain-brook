# QQQ Put Ratio Research Lab V1

獨立研究面板：檢視已保存的 QQQ Put Ratio 歷史回放、獲利預警、時間／波動風險、正股回撤頻率，以及從每日 option-side marks 重建的策略序列淨值回撤。**不改動 V3 Hybrid 正式決策頁、主策略、live sizing 或券商訂單權限。**

## Windows 啟動

在此資料夾執行 `RUN.cmd`，以瀏覽器開啟 `http://127.0.0.1:8765/`。需要現有 Python 3；沒有外部 JavaScript 套件或 broker API。

## 已接入的歷史資料

- 期權：2018-03-01 至 2025-12-15；62 組非重疊 LONG 1 / SHORT 5 QQQ Put episodes。
- 成本基準：每腿每邊滑點 $0.05、每張每邊佣金 $0.65。
- 正股：1,960 筆 QQQ 日收市資料；依 RV20 分組及 1／3／5／10／20／30／45 個交易日統計正股價格變動頻率。
- 退出比較：基準 DTE ≤ 7、固定金額獲利／止損、最大終端收益的 25%／50%、第 20 日非正損益的平倉／減倉政策。
- 尾部風險：LONG 1／SHORT N 與 LONG N／SHORT 1 的 N=1–6 到期情境損失統計。
- 策略序列曲線：已從每個歷史 episode 的每日淨清算估值串接 12 個退出政策，保存於 `portfolio_curve.json`。Run #13 使用 self-hosted `grokbot-box-linux-x64`，回放來源資料 62 組交易、1,960 個交易日，並將曲線保存到研究分支。

## 最新基準結果：1 Long / 5 Short

在 $80,000 起始 NAV、每個歷史 episode 固定 1 組、不複利的序列回放下，DTE ≤ 7 基準政策的歷史勝率為 95.16%，62 組交易累計淨 P&L 為 +$18,067.60。以可觀察的 EOD option-side estimates 計算，歷史序列 MaxDD 為 −8.28%（2025-04-01 至 2025-04-08）；全期間估值覆蓋率為 99.44%，11 個交易日的估值未知且沒有補值。

這個 MaxDD 是**固定一組一組、非重疊、不複利**的研究序列。它不是 live fills 或 NAV 動態部署結果，未包括缺失日內更深的波動、券商保證金／指派、途中追加保證金或強制平倉。

## 解讀與部署限制

1. 只有 LONG 1 : SHORT 5 直接引用已保存的 62 組回放勝率；其他 N 不會複製同一個勝率。
2. 以 $80,000 NAV 計，0.5%／1%／2% 的候選預警金額為 $400／$800／$1,600。已直接測試的固定獲利線是 $500／$1,000／$2,000；候選百分比不是已證明最佳的出場政策。
3. 1:5 的最差觀察 QQQ=$0 到期尾部損失約 $214,696.90，超過 $80,000 NAV；尾部風險預算 0.5%、1%、2% 都不足以容納一組完整部位。因此即使歷史 quote-mark MaxDD 看似可控，部署仍為 BLOCKED。
4. QQQ 正股回撤頻率及 RV20 時間／波動表是 underlying-only path statistics，不是 Put Ratio 虧損機率。
5. 期權回放來自 EOD 歷史報價鏡像，是保守 quote-side replay 而非確認成交；精確 tick 時間、真實 fills、券商保證金、assignment 與途中強制平倉仍未驗證。
6. 歷史資料已經被研究過，不是盲測 OOS。缺失 marks 保留為未知；策略曲線不能把未知估值當作零損益。
7. 面板只供研究與人工覆核：沒有 broker 連接，不會自動下單。

## 來源

- Study SHA: `7653cfbaea92f07b123e9377d6b720c2b37a95b9`
- Original research run: https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38778540717
- Serial portfolio curve run: https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38868892346
- Serial curve data: `research/qqq_put_ratio_lab_v1/portfolio_curve.json`
- Research branch: https://github.com/JUN-ZS/brush-timber-mountain-brook/tree/research/qqq-put-ratio-lab-v1-20261016
