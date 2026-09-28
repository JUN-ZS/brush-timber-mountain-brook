# INERTIA DISCOVERY KERNEL — Phase-1 VALIDATION Report
# 慣性發現核心 — 第一階段「下一未見區間」驗證報告

**Generated (HK):** 2026-09-08T06:01:18+08:00
**Pack hash:** `7ca13ce290d28db4`
**DATA_HASH:** `075f43bc66da900bdcedf47853375c55`
**Phase-1 → Validation bridge:** 見 `VALIDATION_BRIDGE.json`
**Cut date (TRUE_TEMPORAL):** `2024-01-01` （discovery < cut；validation ≥ cut）
**State labels frozen as_of:** `2026-09-04`
**Candidates validated:** 80 （STATUS=DISCOVERY 且 ladder_class≠INSUFFICIENT）

---

## 0. Locks honored / 已遵守鎖定

| Lock | Honored |
|---|---|
| Archive-only | YES |
| Credit SEALED (`credit_unlocked=false`) | YES |
| Option EV SEALED / BLOCKED | YES — options rows=0 |
| STATEHOLD / PROTO SEALED | YES |
| No Personality / No F5·RUNLEN·OCCEDGE revive | YES |
| No 972-cell compete | YES |

---

## 1. What is TRUE temporal vs still DESC

### TRUE_TEMPORAL（本階段主驗證）
- **誠實限制 / label freeze：** `ladder_class` / `shape` / `regime` / `run_bin` 成員資格凍結自 Phase-1 `as_of=2026-09-04` 全樣本 persistence+board（其 CRF 統計本身含 cut 之後資訊）。因此本驗證回答的是「**Phase-1 已發現 cohort 成員**在未見區間的 CRF 是否仍偏離基線」，**不是**「僅用 discovery 窗重標籤後再獨立發現」。outcome（validation-window CRF）為時間外推；state 標籤非純 OOS 再估計。
- 使用 `returns` + `thresholds_hist` 依 **run-start CRF**（`abs(day|week|month) > threshold` 連續超標段為事件；len==1 → revert）在日期切開後重算。
- Discovery window: dates **< 2024-01-01**
- Validation window: dates **≥ 2024-01-01**
- Cohort 成員（shape / regime / ladder_class / run_bin）**凍結**自 Phase-1 `as_of=2026-09-04` 標籤；驗證的是「這些被發現的狀態成員，在未見區間是否仍呈現異常 CRF」。

### DESC / INSUFFICIENT（非主結論）
- **as_of 2026-08-21 vs 2026-09-04**：persistence 在 2026-08-21 僅 **1** ticker（幾乎只有 LBRDA），無法做 cohort 級 as_of CRF 驗證 → **INSUFFICIENT**。
- `fwd_abs_day_vs_baseline`：驗證期 mean|day| 相對橫截面，僅 DESC 輔助，**不是**交易訊號。
- Horizon-weight agreement：DESC rank preview。

---

## 2. STATUS counts / 驗證結果計數

| STATUS | count | rate |
|---|---:|---:|
| VALIDATION_PASS | 50 | 62.5% |
| VALIDATION_WEAK | 7 | 8.8% |
| VALIDATION_FAIL | 23 | 28.7% |
| INSUFFICIENT | 0 | 0.0% |

**PASS 規則：** sign(Δ_val)==sign(Δ_disc) 且 |Δ_val| ≥ ½|Δ_disc| 且 n_val ≥ 40
**FAIL 誠實率：** 28.7% （含符號翻轉或 |Δ| 崩潰）
**DISCOVERY_ARTIFACT flags：** 0

---

## 3. SEED questions / 種子問題

### Q1. 哪些狀態在 OOS（未見區間）仍異常重現？
### Which states recur abnormally OOS?

**Top PASS：**

1. `DAY|P99|REVERSING|0-1|EXPANDING|UNCLASSIFIED` — n_val=84 Δ_disc=-0.0922 Δ_val=-0.0623 ratio=0.6750659568714155 sign_agree=True artifact=False
2. `DAY|P99|REVERSING|0-1|STRONGLY_EXPANDING|STABLE_LOW_VOL` — n_val=86 Δ_disc=-0.0678 Δ_val=-0.0611 ratio=0.9019862623831575 sign_agree=True artifact=False
3. `DAY|P90|ACCELERATING|*|*|*` — n_val=63 Δ_disc=-0.0418 Δ_val=-0.0603 ratio=1.444413475947554 sign_agree=True artifact=False
4. `DAY|P99|REVERSING|0-1|STRONGLY_EXPANDING|DEAD_VOL` — n_val=51 Δ_disc=-0.0504 Δ_val=-0.0536 ratio=1.0631099237043626 sign_agree=True artifact=False
5. `DAY|P99|REVERSING|*|*|*` — n_val=503 Δ_disc=-0.0718 Δ_val=-0.0462 ratio=0.6434121288264297 sign_agree=True artifact=False

**Top WEAK：**

1. `DAY|P99|REVERSING|0-1|EXPANDING|STABLE_LOW_VOL` — n_val=87 Δ_disc=-0.0678 Δ_val=-0.0339 ratio=0.4996919119890263 sign_agree=True artifact=False
2. `DAY|P99|REVERSING|0-1|EXPANDING|DEAD_VOL` — n_val=72 Δ_disc=-0.1123 Δ_val=-0.0318 ratio=0.28342222056619515 sign_agree=True artifact=False
3. `DAY|P99|ACCELERATING|*|*|*` — n_val=63 Δ_disc=0.0726 Δ_val=0.0289 ratio=0.397876658889278 sign_agree=True artifact=False
4. `DAY|P99|MONOTONIC|0-1|STRONGLY_EXPANDING|STABLE_LOW_VOL` — n_val=107 Δ_disc=0.0574 Δ_val=0.0282 ratio=0.4910949301341758 sign_agree=True artifact=False
5. `DAY|P95|REVERSING|0-1|STRONGLY_EXPANDING|DEAD_VOL` — n_val=51 Δ_disc=-0.0211 Δ_val=-0.0054 ratio=0.2565589741767013 sign_agree=True artifact=False

解釋：PASS/WEAK 表示凍結 cohort 在 validation 期相對同 horizon×threshold 無條件基線的 CRF 偏離，與 discovery 期同號且未完全崩潰。**不是**可交易 edge，**不是** Personality / WR>50%。

### Q2. 期望值？ / Expectancy?
**仍 SEALED。** `credit_unlocked=false`。本驗證只談 CRF 頻率偏離的時間穩定性，**不**主張正期望值。

### Q3. 何時失效？ / When does it fail?

**Top FAIL（依 Phase-1 |Δ| 排序，顯示崩壞）：**

1. `DAY|P80|REVERSING|0-1|EXPANDING|DEAD_VOL` — n_val=72 Δ_disc=-0.0017 Δ_val=0.0322 ratio=19.140443175792857 sign_agree=False artifact=False
2. `DAY|P90|REVERSING|0-1|EXPANDING|DEAD_VOL` — n_val=72 Δ_disc=-0.0057 Δ_val=0.0374 ratio=6.614571486367885 sign_agree=False artifact=False
3. `DAY|P95|MONOTONIC|0-1|EXPANDING|STABLE_LOW_VOL` — n_val=83 Δ_disc=-0.0096 Δ_val=-0.0014 ratio=0.14364660265501553 sign_agree=True artifact=False
4. `DAY|P90|REVERSING|0-1|EXPANDING|STABLE_LOW_VOL` — n_val=88 Δ_disc=-0.0016 Δ_val=0.0305 ratio=19.607285539024776 sign_agree=False artifact=False
5. `DAY|P90|MONOTONIC|0-1|EXPANDING|STABLE_LOW_VOL` — n_val=82 Δ_disc=-0.0143 Δ_val=0.0058 ratio=0.4063520138233057 sign_agree=False artifact=False

失效模式：
- 符號翻轉（discovery 偏高/偏低，validation 相反）
- |Δ| 衰減至 < ¼ discovery（崩潰 → FAIL；¼–½ → WEAK）
- n_val < 40 → INSUFFICIENT
- DISCOVERY_ARTIFACT：Phase-1/重算 discovery |Δ| 大但 validation 失敗

### Q4. Option structure?
**BLOCKED** — options/snapshots.csv = **0** data rows；`option_ev=false`。

---

## 4. Anti-overfit

- Validation-period **shuffle null**（同一 hz×thr 內重抽 n_val 只股票）：見 `shuffle_null_p_ge`；p 高表示 |Δ_val| 與隨機cohort無異。
- Phase-1 ticker holdout 既有結果不覆蓋；本檔延伸日期 holdout。
- as_of 雙快照驗證因 2026-08-21 稀疏而跳過（誠實標記 INSUFFICIENT）。

---

## 5. Horizon-weight preview agreement

| pair | agreement_rate | note |
|---|---:|---|
| equal_vs_sqrt_n | 1.00 | DESC rank preview on recomputed |delta_disc|; not adaptive |
| equal_vs_log_n | 1.00 | DESC rank preview on recomputed |delta_disc|; not adaptive |
| sqrt_n_vs_log_n | 1.00 | DESC rank preview on recomputed |delta_disc|; not adaptive |
| equal_top15_in_PASS_or_WEAK | 1.00 | fraction of equal-weight top15 that validated PASS/WEAK |

（DESC ok — 完整 adaptive 權重未啟用）

---

## 6. Explicit non-claims

- CRF ≠ credit；無 credit_score
- 無 WR>50% / Personality
- 無 Option EV / 無 payoff
- 無 972-cell OOS compete
- 不復甦 F5 / RUNLEN / OCCEDGE
- Freeze labels ≠ 獨立再發現；驗證的是「已發現狀態成員」的時間外推

---

## 7. Paths

- Validation out: `/workspace/sp500-vol/output/INERTIA_DISCOVERY_KERNEL_PHASE1_VALIDATION`
- Phase-1: `/workspace/sp500-vol/output/INERTIA_DISCOVERY_KERNEL_PHASE1`
- Runner: `/workspace/sp500-vol/scripts/run_inertia_discovery_kernel_phase1_validation.py`
- Archive: `/workspace/sp500-vol/output/archive_csv`
- Light zip: `/workspace/sp500-vol/output/RELEASE/RelVol_INERTIA_DISCOVERY_KERNEL_PHASE1_VALIDATION_LIGHT.zip`

---

## 8. STATUS summary JSON

```json
{
  "credit_unlocked": false,
  "option_ev": false,
  "status_counts": {
    "VALIDATION_PASS": 50,
    "VALIDATION_FAIL": 23,
    "VALIDATION_WEAK": 7
  },
  "fail_rate": 0.2875,
  "pass_rate": 0.625,
  "n_candidates": 80,
  "cut_date": "2024-01-01",
  "artifact_flags": 0
}
```
