# Desk ledgers（research shadow）

| 檔 | 用途 |
|---|---|
| `positions.jsonl` | shadow 持倉（現政策下應為空） |
| `trades.jsonl` | shadow 成交（唔由 book_ADD 發明） |
| `signal_trade_map.jsonl` | event_id → trade_id（無可執行訊號時為空） |
| `portfolio_daily.jsonl` | 日結組合（無倉 → NET_PNL=NOT_AVAILABLE） |
| `execution_gate_log.jsonl` | 每次 FORWARD NOW 閘門紀錄 |

**政策**：`desk.book_ADD` = OBSERVATION only → `EMPTY_BY_POLICY`
