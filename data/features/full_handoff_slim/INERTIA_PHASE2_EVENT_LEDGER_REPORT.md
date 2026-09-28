# INERTIA DISCOVERY KERNEL Phase-2 — Event → Forward Outcome

**generated_at_hk:** `2026-09-08T06:14:42+08:00`
**pack_hash:** `7ca13ce290d28db4`
**DATA_HASH (Phase-1 pin):** `075f43bc66da900bdcedf47853375c55`
**credit_unlocked:** `false` | **option_ev:** `false` | **proto_eligible:** `false`

## What 1490 Is (Search Universe Framing)

### 1490 是什麼 / What 1490 IS
- **Search universe** for Historical Analog / Relation Discovery（歷史類比／關係發現的搜尋宇宙）
- Cross-sectional inertia library 的原料（dates × horizons × thresholds）
- 足夠的「過去世界」來問：今天的幾何以前曾經怎麼走

### 1490 不是什麼 / What 1490 IS NOT
- 不是「誰最有慣性」的 ticker 排行榜
- 不是 Phase-1 DESC candidates 已是交易訊號的證明
- Primary ranked object = **Relation / state cohort**，ticker 只是載體

## TRUE Temporal Now vs Still Missing

### Now true (本 Phase 已落地)
- Event panel (RECENT5Y) → **real returns calendar** forward T+1 / T+5 / T+21
- Vol-continuation / reversion 二元結果（DAY→day_range，WEEK→week_range ≥ event threshold floor）
- Probability ledger with **dual lifts**: `continue_lift` and `revert_lift`
- Run-length life-cycle + of_p90 elasticity preview
- Baseline = all events same event-horizon（同 horizon 事件無條件率）

### Still missing（尚未完成）
- Full **vector Analog NN**（多維 state 向量最近鄰搜尋）
- Relation Discovery UI / Historical Analog explorer
- OOS survival / VALIDATION unlock（現況 VALIDATION_PENDING / OOS_PENDING）
- Credit / Option EV / STATEHOLD / PROTO（**SEALED**）
- Signed return path MFA/MAD（archive `returns.day` 為非負 abs move，無符號報酬）

## Outcome Definitions (documented)

```json
{
  "continuation": "vol-continuation: at forward trading day T+h, the same horizon vol proxy (DAY→day_range, WEEK→week_range) is still ≥ the event-row threshold floor (p80/p90/p95/p99 matching event.threshold). MONTH omitted (no month_range).",
  "reversion": "not continuation (vol proxy fell below event threshold floor at T+h).",
  "flat": "not used in v1 primary metric (vol-threshold binary); reserved for return-based alt.",
  "fwd_ret": "fwd_abs_day_sum_h = sum of returns.day over trading days (event_idx+1 .. event_idx+h). returns.day is non-negative absolute daily move in this archive (no signed return column); therefore max_favorable/max_adverse signed path metrics are N/A and omitted.",
  "calendar": "ticker-local trading-day calendar from returns.csv (sorted by date).",
  "baseline": "baseline_p_continue / baseline_p_revert = unconditional rates among ALL events with the same event-horizon (DAY or WEEK), for the same forward h. Lift is therefore interpretable vs same-horizon event base rate (not full returns universe).",
  "lift": "continue_lift = p_continue / baseline_p_continue (equiv. (1-CRF)/(1-baseline_CRF) with CRF=p_revert); revert_lift = p_revert / baseline_p_revert. Primary rank uses these dual lifts — NOT abs(delta)."
}
```

## Coverage

- Input events: **406874** (RECENT5Y DAY+WEEK)
- Ledger rows aligned: **406874**
- Event tickers: **1489** (search universe framing remains 1490 board pin)
- Forward OK rates: T+1=0.9966, T+5=0.9933, T+21=0.9803

### Baseline P (all events, same horizon)

| event_horizon | fwd_h | n | baseline_p_continue | baseline_p_revert |
|---|---:|---:|---:|---:|
| DAY | 1 | 191583 | 0.459837 | 0.540163 |
| DAY | 5 | 190933 | 0.416733 | 0.583267 |
| DAY | 21 | 188327 | 0.413987 | 0.586013 |
| WEEK | 1 | 213918 | 0.715082 | 0.284918 |
| WEEK | 5 | 213225 | 0.440333 | 0.559667 |
| WEEK | 21 | 210545 | 0.426555 | 0.573445 |

## Top Relations by continue_lift

Primary relation_kind = `horizon|threshold|run_bin`, STATUS=DISCOVERY (n≥200).

| relation_key | fwd_h | n | p_continue | baseline | continue_lift | revert_lift |
|---|---:|---:|---:|---:|---:|---:|
| `DAY|P80|4+` | 5 | 23042 | 0.6953 | 0.4167 | **1.6685** | 0.5223 |
| `DAY|P80|4+` | 21 | 22343 | 0.6866 | 0.4140 | **1.6585** | 0.5348 |
| `WEEK|P80|4+` | 21 | 28078 | 0.7023 | 0.4266 | **1.6463** | 0.5192 |
| `WEEK|P80|4+` | 5 | 28713 | 0.7060 | 0.4403 | **1.6034** | 0.5253 |
| `DAY|P80|4+` | 1 | 23177 | 0.7189 | 0.4598 | **1.5634** | 0.5204 |

## Top Relations by revert_lift

| relation_key | fwd_h | n | p_revert | baseline | revert_lift | continue_lift |
|---|---:|---:|---:|---:|---:|---:|
| `DAY|P99|0-1` | 5 | 4847 | 0.9486 | 0.5833 | **1.6264** | 0.1233 |
| `DAY|P99|0-1` | 21 | 4809 | 0.9470 | 0.5860 | **1.6160** | 0.1281 |
| `WEEK|P99|0-1` | 21 | 8832 | 0.9034 | 0.5734 | **1.5754** | 0.2264 |
| `WEEK|P99|0-1` | 5 | 9014 | 0.8601 | 0.5597 | **1.5368** | 0.3177 |
| `WEEK|P95|0-1` | 21 | 28071 | 0.8131 | 0.5734 | **1.4180** | 0.4381 |

## Explicit Non-Claims

- **No Credit** — `credit_unlocked=false`; CRF/probability ≠ credit_score
- **No Option EV** — `option_ev=false`
- **No proto_eligible** — sealed
- **No ticker champion board** as primary product（不產 ticker 慣性冠軍榜）
- **No fake MONTH daily** — month_range absent; MONTH omitted
- **No abs(delta) primary rank** — dual lifts only
- ASSOCIATION / DESC geography only — not trade signals

## Deliverables

- `/workspace/sp500-vol/output/INERTIA_DISCOVERY_KERNEL_PHASE2/event_ledger_forward.csv.gz`
- `/workspace/sp500-vol/output/INERTIA_DISCOVERY_KERNEL_PHASE2/probability_ledger.csv`
- `/workspace/sp500-vol/output/INERTIA_DISCOVERY_KERNEL_PHASE2/cohort_aggregated_ledger.csv`
- `/workspace/sp500-vol/output/INERTIA_DISCOVERY_KERNEL_PHASE2/lifecycle_run_forward.csv`
- `/workspace/sp500-vol/output/INERTIA_DISCOVERY_KERNEL_PHASE2/elasticity_of_p90.csv`
- `/workspace/sp500-vol/output/INERTIA_DISCOVERY_KERNEL_PHASE2/preview_top_continue_lift.csv` / `preview_top_revert_lift.csv`
- `/workspace/sp500-vol/output/INERTIA_DISCOVERY_KERNEL_PHASE2/OUTCOME_DEFINITIONS.json`

## Next

1. Historical Analog **vector search** (full NN over relation vectors)
2. Relation Discovery / explorer
3. OOS survival gates (exit VALIDATION_PENDING)
4. Only later: Credit → Champion/Challenger → Option（仍 sealed）

---
*Phase-2 SEED locks honored. Engine evolves in-repo — no second research stack.*
