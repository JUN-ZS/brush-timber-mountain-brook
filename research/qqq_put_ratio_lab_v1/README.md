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
- 策略序列曲線：已從每個歷史 episode 的每日淨清算估值串接 13 個退出政策，保存於 `portfolio_curve.json`。直接回放與 UI 合約測試現用 GitHub Hosted Runner（`ubuntu-latest`）；受信任流程以唯讀方式驗證並將每輪回放證據上傳為 Actions artifact，不在公開 PR 測試中寫回分支。

## 最新基準結果：1 Long / 5 Short

在 $80,000 起始 NAV、每個歷史 episode 固定 1 組、不複利的序列回放下，DTE ≤ 7 基準政策的歷史勝率為 95.16%，62 組交易累計淨 P&L 為 +$18,067.60。以可觀察的 EOD option-side estimates 計算，歷史序列 MaxDD 為 −8.28%（2025-04-01 至 2025-04-08）；全期間估值覆蓋率為 99.44%，11 個交易日的估值未知且沒有補值。

這個 MaxDD 是**固定一組一組、非重疊、不複利**的研究序列。它不是 live fills 或 NAV 動態部署結果，未包括缺失日內更深的波動、券商保證金／指派、途中追加保證金或強制平倉。

## APP 回答契約（本版）

- 頂部歷史 WIN% 會隨所選退出政策切換；只對 LONG PUT 1 : SHORT PUT 5 的直接 62 組歷史樣本顯示數字。其他 N／方向不複製勝率或 MaxDD。
- 「目前獲利預警」先將 NAV × 百分比換算成金額。只有精確對應到實際重播的固定目標（USD 500／800／1,000／2,000）才顯示同額歷史 WIN、淨損益、政策觸發數與序列 MaxDD；未重播的金額不插值。
- 策略 MaxDD 分級按每個峰值至下一個新高的回撤週期計數，顯示每年平均週期數和實際發生年份。未知的每日估值保持未知；缺口可能掩蓋更深回撤。
- RV20 × 持有期限會比較 QQQ 正股跌 ≥5%／≥10% 的頻率與 ALL 基準。當下跌頻率升高，再遇上獲利線、持倉 ≥20 日或 DTE ≤7 時，顯示合併人工覆核警示。這不是 Put Ratio 損失機率，也不會自動平倉。

## 解讀與部署限制

1. 只有 LONG 1 : SHORT 5 直接引用已保存的 62 組回放勝率；其他 N 不會複製同一個勝率。
2. 以 $80,000 NAV 計，0.5%／1%／2% 的候選預警金額為 $400／$800／$1,600。固定金額政策包括直接重播的 $500／$800／$1,000／$2,000；$800 只有在 $80,000 NAV 下才等於 +1%，不因此自動成為最佳出場政策。
3. 1:5 的最差觀察 QQQ=$0 到期尾部損失約 $214,696.90，超過 $80,000 NAV；尾部風險預算 0.5%、1%、2% 都不足以容納一組完整部位。因此即使歷史 quote-mark MaxDD 看似可控，部署仍為 BLOCKED。
4. QQQ 正股回撤頻率及 RV20 時間／波動表是 underlying-only path statistics，不是 Put Ratio 虧損機率。
5. 期權回放來自 EOD 歷史報價鏡像，是保守 quote-side replay 而非確認成交；精確 tick 時間、真實 fills、券商保證金、assignment 與途中強制平倉仍未驗證。
6. 歷史資料已經被研究過，不是盲測 OOS。缺失 marks 保留為未知；策略曲線不能把未知估值當作零損益。
7. 面板只供研究與人工覆核：沒有 broker 連接，不會自動下單。

## $800 vs $1,000 fixed profit-warning recheck

<!-- PROFIT_WARNING_RESULTS_START -->

Both targets were directly re-run on the same frozen 62-episode LONG 1 / SHORT 5 cohort with shared DTE <= 7 safety fallback and next-observed-session execution. USD 800 equals +1% only at USD 80,000 NAV; the live app's current-NAV percentage alert is a separate manual-review alert, not a proportional re-run of every historical trade.

| Fixed target | Counterfactual first EOD mark hit | Actual policy triggers | Successful close actions | 5-session held-path forward n / median ΔP&L / large giveback | 10-session held-path forward n / median ΔP&L / large giveback | Net P&L | Win rate | Serial quote-mark MaxDD |
|---:|---:|---:|---|---|---|---:|---:|---|
| USD 800 | 12/62 | 6/62 (9.68%) | 6/6 | n=5; median USD 187.00; giveback 20.00% | n=1; median USD -206.00; giveback 0.00% | USD 17,091.60 | 95.16% | -5.96% (2024-05-02 → 2024-08-05) |
| USD 1,000 | 9/62 | 3/62 (4.84%) | 3/3 | n=1; median USD 1,065.90; giveback 0.00% | n=0; median —; giveback — | USD 18,067.60 | 95.16% | -8.28% (2025-04-01 → 2025-04-08) |

The 5/10-session forward metrics are **counterfactual marks for holding the original 1x5** after the warning signal; they are not realized P&L after exiting. Counterfactual first mark hits and actual policy triggers are intentionally separate. With a small trigger/forward sample and previously inspected data, these measurements do not select an optimal target.

Public EOD marks are not confirmed fills, action attempts may be deferred, and missing marks are not filled. Deployment remains **BLOCKED** pending blind OOS, verified timestamps/fills, and broker margin/assignment/forced-liquidation evidence.

<!-- PROFIT_WARNING_RESULTS_END -->

## 來源

- Study SHA: `7653cfbaea92f07b123e9377d6b720c2b37a95b9`
- Original research run: https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38778540717
- Serial portfolio curve run: https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38868892346
- Serial curve data: `research/qqq_put_ratio_lab_v1/portfolio_curve.json`
- Research branch: https://github.com/JUN-ZS/brush-timber-mountain-brook/tree/research/qqq-put-ratio-lab-v1-20261016
