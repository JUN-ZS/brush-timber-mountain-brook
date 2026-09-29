# QQQ ORIGINAL SENTENCE LOOP V1

Research only. Not a live signal. Does not modify V2.2.

Frozen from the user's own sentences in the uploaded threads:

1. QQQ 升很多 → SHORT CALL 近一點，SHORT PUT 更 OTM，LONG PUT 同時在。
2. 只在超過某波值才因應買賣。波 = 1 × ATR20。T 觸發，T+1 執行。
3. 跨日期半堆疊 / 儲飛尾。Max 2 overlapping vintages.
4. 臨近 SHORT CALL（S ≥ 0.98K）後一日下跌 → 先鎖至少一半 short+wing，再變陣。
5. 先試 N+50 對 1 張 ATM；2% defined-loss gate 不過就記錄 REJECT，不准偷偷縮比例。已實現正收益記入 opportunity credit 後，下一輪才可試 N+20。

Package per vintage:

+1 50Δ Call, −N 20Δ Short Call, +N 8Δ Wing, +1 25Δ Long Put, −1 10Δ Short Put.

Wave 1 only: Short Call 20Δ→30Δ, Short Put 10Δ→5Δ, Long Put retained.

Comparator on the same signals: static N=2 half-stack.

Real QQQ chain Bid/Ask. No Black-Scholes. No interpolation. No parameter search.
