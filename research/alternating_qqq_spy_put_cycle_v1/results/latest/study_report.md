# QQQ / SPY PUT 配對策略 — DTE 20、每 10 個交易日交替

- 回測區間：2018-03-01 至 2025-12-12；共 1959 個共同交易日。
- 起始 NAV：USD 100,000。
- 每組：一張反向指數 LONG PUT，六張 SHORT PUT；A=SPY short／QQQ long，B=QQQ short／SPY long。
- 入場：共同到期日；精確 DTE 20 日；SHORT PUT |Delta| 目標 0.25，LONG PUT |Delta| 0.60–0.70（目標 0.65）。
- 節奏：從第 2 個共同交易日發出第一個訊號、下一日入場，其後每 10 個共同交易日開新一組；A／B 依排程交替，跳過訊號不改變方向。
- 退出：剩餘日曆 DTE <= 7，或持有達 20 個共同交易日，先到者觸發；若平倉報價／顯示張數不足，延遲至可執行報價。

| 策略 | 最終 NAV | 淨損益 | MaxDD (USD) | MaxDD (%) |
|---|---:|---:|---:|---:|
| alternate_dte20_every10_tue_anchor | USD 108,826.20 | USD 8,826.20 | USD -6,276.10 | -5.84% |
