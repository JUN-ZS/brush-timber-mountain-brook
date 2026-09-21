# Desk run_history

每次 `forward_runner.py` / `--now` 寫入一份：

`FORWARD_RUN_<UTC_TIMESTAMP>.json`

append-only；即使 `NEW_EVENTS=0` / `BLOCKED` / `NO_NEW_SIGNAL` / `WAITING_FOR_FUTURE_BARS` 都要留永久紀錄。
