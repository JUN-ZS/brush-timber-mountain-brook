# INERTIA Analog + Relation Discovery Report

generated_at_hk=2026-09-08T06:20:08+08:00
pack_hash=7ca13ce290d28db4
DATA_HASH=075f43bc66da900bdcedf47853375c55
evidence_class=DESC_ONLY
credit_unlocked=false
option_ev=false
proto_eligible=false

## What this enables vs still missing

### Now enabled
- **Relation Discovery**: geometric cells (of_p90/of_p99 bins, run_bin, p99/p90 compression, day/week of_p90 ratio regions) with dual-track continue_lift and revert_lift at T+1/5/21 vs same-horizon baselines.
- **OOS preview**: time split <2024-01-01 train vs ≥2024-01-01 validation; VALIDATION_PASS when sign(continue_lift−1) agrees and |val−1| ≥ 0.5·|train−1| with n_val≥100.
- **Historical Analog**: standardized state vector kNN (numpy brute-force; sklearn absent) over stratified ~99997 sample; prototype CONTINUE/REVERT + real 2026 ticker queries; neighbor forward curves vs baseline.

### Still missing / sealed
- Full App UI for Analog browse
- Credit unlock / Option EV / proto eligibility (**SEALED**)
- MACD/RSI/ADX features (**not used**)
- Signed return path max_favorable/adverse (archive day abs only)
- Ticker GLOBAL scoreboard as product (explicitly not primary object)

## Explicit non-claims
- ASSOCIATION / DESC_ONLY — not causal, not investable signal license.
- Lifts are relative to same-horizon event base rates, not full market universe.
- OOS preview is a survival screen, not a full validation protocol.
- Analog neighbors are descriptive historical matches, not forecasts or trade recommendations.
- credit_unlocked=false; option_ev=false; proto_eligible=false.

## Relation Discovery summary
- relation_discovery rows: 1227
- STATUS DISCOVERY: 948; INSUFFICIENT: 279
- Families: hz|thr|run|of_p90, hz|thr|run|of_p99, hz|thr|of_p90|of_p99, hz|run|p99_over_p90, hz|thr|p99_over_p90, hz|thr|run, cross day_week_ratio regions
- of_p90/of_p99 bins: lt0.5, 0.5-0.8, 0.8-1.0, 1.0-1.2, 1.2-1.5, ge1.5

### Top continue_lift (DISCOVERY)
| kind | relation_key | fwd_h | n | continue_lift | revert_lift | STATUS |
|------|--------------|-------|---|---------------|-------------|--------|
| cross|run|day_week_ratio | DAY|4+|lt0.5 | 5 | 1667 | 1.8267 | 0.4093 | DISCOVERY |
| cross|run|day_week_ratio | DAY|4+|lt0.5 | 1 | 1673 | 1.7821 | 0.3342 | DISCOVERY |
| cross|run|day_week_ratio | DAY|4+|lt0.5 | 21 | 1586 | 1.7226 | 0.4896 | DISCOVERY |
| cross|run|day_week_ratio | DAY|4+|0.5-0.8 | 5 | 7360 | 1.7117 | 0.4915 | DISCOVERY |
| hz|run|p99_over_p90 | DAY|4+|lt0.3 | 5 | 1763 | 1.7014 | 0.4989 | DISCOVERY |
| hz|run|p99_over_p90 | DAY|4+|lt0.3 | 21 | 1745 | 1.6888 | 0.5134 | DISCOVERY |
| hz|thr|run|of_p90 | DAY|P80|4+|0.8-1.0 | 5 | 15003 | 1.6855 | 0.5102 | DISCOVERY |
| cross|run|day_week_ratio | DAY|4+|0.5-0.8 | 21 | 7135 | 1.6846 | 0.5164 | DISCOVERY |
| hz|thr|run|of_p90 | DAY|P80|4+|0.8-1.0 | 21 | 14546 | 1.6845 | 0.5164 | DISCOVERY |
| hz|thr|run|of_p99 | WEEK|P80|4+|0.5-0.8 | 21 | 4323 | 1.6828 | 0.4921 | DISCOVERY |

### Top revert_lift (DISCOVERY)
| kind | relation_key | fwd_h | n | continue_lift | revert_lift | STATUS |
|------|--------------|-------|---|---------------|-------------|--------|
| hz|thr|run|of_p99 | WEEK|P99|2-3|1.0-1.2 | 1 | 665 | 0.6940 | 1.7681 | DISCOVERY |
| hz|thr|run|of_p90 | WEEK|P95|0-1|1.0-1.2 | 1 | 862 | 0.6976 | 1.7590 | DISCOVERY |
| hz|thr|of_p90|of_p99 | WEEK|P95|1.0-1.2|0.5-0.8 | 1 | 914 | 0.7206 | 1.7011 | DISCOVERY |
| cross|thr|day_week_ratio | DAY|P99|ge2.0 | 5 | 1109 | 0.0844 | 1.6542 | DISCOVERY |
| hz|thr|run|of_p99 | DAY|P99|0-1|1.2-1.5 | 5 | 1442 | 0.0949 | 1.6467 | DISCOVERY |
| hz|thr|run|of_p99 | DAY|P99|0-1|1.0-1.2 | 5 | 2443 | 0.1002 | 1.6429 | DISCOVERY |
| hz|thr|of_p90|of_p99 | DAY|P99|ge1.5|1.0-1.2 | 5 | 2537 | 0.1012 | 1.6422 | DISCOVERY |
| cross|thr|day_week_ratio | DAY|P99|ge2.0 | 1 | 1112 | 0.2464 | 1.6415 | DISCOVERY |
| cross|thr|day_week_ratio | DAY|P99|1.2-1.5 | 5 | 993 | 0.1063 | 1.6385 | DISCOVERY |
| hz|thr|run|of_p99 | DAY|P99|0-1|1.0-1.2 | 21 | 2417 | 0.0969 | 1.6380 | DISCOVERY |

## OOS preview
- rows: 849
- status counts: {"VALIDATION_PASS": 698, "WEAK": 89, "FAIL": 50, "INSUFFICIENT": 12}
- cut: train date < 2024-01-01; val ≥ 2024-01-01

## Historical Analog example — PROTO_CONTINUE_DAY_P80_4plus (k=50)
Features: of_p90, of_p99, log1p(run_len), day_week_ratio (+ horizon one-hot).
Neighbor summary:
- T+1: n=50, p_continue=0.7200, continue_lift=1.5658, p_revert=0.2800, revert_lift=0.5184
- T+5: n=49, p_continue=0.6122, continue_lift=1.4692, p_revert=0.3878, revert_lift=0.6648
- T+21: n=48, p_continue=0.5000, continue_lift=1.2078, p_revert=0.5000, revert_lift=0.8532

Queries run: PROTO_CONTINUE_DAY_P80_4plus, PROTO_REVERT_DAY_P99_0_1, REAL_NVDA_2026-09-02, REAL_AAPL_2026-09-04, REAL_TSLA_2026-08-31, REAL_MSTR_2026-08-24, REAL_SMCI_2026-09-04
Search pool size: 99997 (stratified by horizon×threshold×year from 406874)
kNN: numpy brute-force Euclidean on standardized vectors (sklearn not installed)

## Locks
credit_unlocked=false
option_ev=false
proto_eligible=false
evidence_class=DESC_ONLY
primary_object=relation_analog_match
