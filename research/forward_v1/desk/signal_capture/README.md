# Desk SIGNAL_CAPTURE — LIVE LOOP V1.0

信股慣性台（QQQ VXX 年化）· Hub [@JUN-ZS](https://github.com/JUN-ZS)

## 點樣用（原引擎，唔好另寫第二套排序）

```bash
# 1) 數據新鮮度
python research/forward_v1/desk/tools/data_factory_status.py --repo-root .

# 2) 捕捉閘（預設 status；同 T0 同一根 bar → NO_NEW_SIGNAL）
python research/forward_v1/desk/signal_capture/capture_as_emitted.py --repo-root . --mode status

# 3) 有新 US daily bar 之後先跑原引擎
cd /workspace/juniper-kite/juniper-kite-shadow-frost-up-down-get
npx --yes tsx scripts/desk_run_warehouse_write.mts
# 然後：
python research/forward_v1/desk/signal_capture/capture_as_emitted.py --repo-root . --mode live_engine
```

## 硬鎖

- GitHub main = SoT；**唔好改 T0**
- `evaluation_clock = LIVE_FORWARD`（Desk formal）
- `book_ADD ≠ MARK_BUY / ARMED / TRUST_UP` — 永唔升級
- `score / opportunity = NOT_A_PROBABILITY`；`claimed_p = null`
- 唔好發明價／未來 bar
- 唔好同 Cap-Rail / RelVol 嘅 `REPLAY_FORWARD` win-rate 混池
- SIGNAL_CAPTURE 同 OUTCOME_RESOLVER 分開工

## 狀態字義

| 狀態 | 意思 |
|------|------|
| `DATA_STALE` | yahoo cache 追唔上預期 US session |
| `SIGNAL_CAPTURE_BLOCKED_DATA_STALE` | 因數據過期擋住（**唔係**無訊號） |
| `NO_NEW_SIGNAL` | 數據新鮮，但 bar 已有 formal T0 |
| `RESOLVER_WAITING` | 等 maturity／認證 fill（唔發明） |
| `SYSTEM_NOT_RUNNING` | scheduler／workflow 未裝 |

## 原引擎路徑

- `scripts/desk_run_warehouse_write.mts`
- `scripts/live-scan-snapshot.mts`
