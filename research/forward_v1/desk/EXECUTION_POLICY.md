# Desk（信股慣性台）— EXECUTION_POLICY

## BOOK_ACTION / OBSERVATION only（預設）

- `desk.book_ADD` = **BOOK_ACTION / OBSERVATION** — **永不**自動升級為 `MARK_BUY` / `ARMED` / `TRUST_UP`
- `score` / `alignScore` / `opportunity` = `NOT_A_PROBABILITY`
- `claimed_p = null` for `DESK_CORE_V1`
- T0 現況：7 × `desk.book_ADD` · `MARK_BUY=0` · `ARMED=0` · `TRUST_UP=0`
  → research shadow book = **EMPTY_BY_POLICY**（或 observation-only ledger，唔開倉）

## Executable（先決條件全部要滿足）

只有當 **原引擎已經 emit** 明確可執行動作，且系統定義為 executable，先可入 shadow execution adapter：

- 明確動詞：`MARK_BUY` / `ARMED` / `TRUST_UP`（或系統合約認定之 BUY/SELL/OPEN/CLOSE…）
- **禁止**由 runner / adapter 把 `book_ADD` promote 成上述任何一項
- `whyNotBuy` 存在時，一律 observation

## Clocks / 混池禁令

- Formal Desk：`evaluation_clock = LIVE_FORWARD` · benchmark **QQQ**
- **永不**同 Cap-Rail / RelVol `REPLAY_FORWARD` win-rate 混池
- T0 immutable；唔發明價、唔發明 fee/slippage（`NET_PNL=NOT_AVAILABLE` 若無真實來源）
