# QQQ Full-History EOD Quote Alignment — Run #22

**Status:** hash-verified source/quote diagnostic; **not** a strategy backtest.  
**Actions:** [Run #22 — Windows self-hosted](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38015730909) · **PR:** [#99](https://github.com/JUN-ZS/brush-timber-mountain-brook/pull/99) · **Branch head:** `28532f97b2694138b1b85a08cb498001061358b5`  
**Requested window:** 2018-03-01 to 2025-12-31 · **Last source observation:** 2025-12-15.  
**Result:** `HASH_VERIFIED_SOURCE_COVERAGE_DIAGNOSTIC`; source data/model integrity and full-history streaming job succeeded.

## Decision-grade result

The QQQ option quote layer remains **BLOCKED for trade replay**. Across **1,946 raw-spot target pairs**, the repository QQQ input is below contemporaneous raw nominal close by median **-2.72%**. The selected short contract differs between adjusted-input and raw-spot target geometry on **96.61%** of matched dates; the selected wing differs on **95.84%**. When the repository adjusted-series input is used to select the pair, median short/wing deltas are **0.28174 / 0.16985**, versus intended **0.16 / 0.08**.

The VIX-proxy model's conservative credit minus observed EOD **short Bid − wing Ask** has median **+$0.181/share** (median absolute gap **$0.196/share**). Its per-leg spread haircut is narrower than observed on **30.0%** of short legs and **57.2%** of wings. Source-IV-based repricing yields a median absolute gap of **$0.060/share**, but that is **not independent validation** because reported IV may be derived from the same quote midpoint.

### Adverse-fill sensitivity (hypothetical only)

For each case, subtract the scenario slippage **per leg × two legs** from observed EOD short Bid − wing Ask. These are analyst-selected stress assumptions, **not measured fills, commissions, or a strategy backtest**.

| Extra adverse slippage / leg | Two-leg deduction / share | Pairs with credit ≤ $0 | Median proxy-model minus stressed credit | Median source-IV-model minus stressed credit | Median stressed observed-side credit |
|---:|---:|---:|---:|---:|---:|
| $0.000 | $0.00 | 0.41% | $0.181 | $-0.004 | $0.580 |
| $0.010 | $0.02 | 0.57% | $0.201 | $0.016 | $0.560 |
| $0.025 | $0.05 | 1.23% | $0.231 | $0.046 | $0.530 |
| $0.050 | $0.10 | 2.93% | $0.281 | $0.096 | $0.480 |
| $0.100 | $0.20 | 13.62% | $0.381 | $0.196 | $0.380 |

At **$0.025/leg** ($0.05/share across two legs), non-positive credit occurs on **1.23%** of matched pairs and the median proxy-model gap rises to **$0.231/share**. At **$0.05/leg**, these become **2.93%** and **$0.281/share**. At **$0.10/leg**, they become **13.62%** and **$0.381/share**. These sensitivities are not evidence those slippages are the true costs.

## Corrected source coverage

| Measure | Observed | Coverage of all expected sessions |
|---|---:|---:|
| Repo-universe expected sessions | 1,971 | 100% denominator |
| Raw underlying closes | 1,960 | 9944.19% |
| QQQ option rows | 1,956 | 9923.90% |
| Raw-spot target pairs | 1,946 | 9873.16% |
| Target pairs / option dates | 1946 / 1956 | 9948.88% |

**Not full-window-complete:** raw underlying and option sources both stop on **2025-12-15**. The 11 expected terminal sessions not covered are: 2025-12-16, 2025-12-17, 2025-12-18, 2025-12-19, 2025-12-22, 2025-12-23, 2025-12-24, 2025-12-26, 2025-12-29, 2025-12-30, 2025-12-31. Option rows are also absent inside the earlier source span on: 2018-11-06, 2019-09-03, 2020-06-23, 2021-11-04, 2025-12-16, 2025-12-17, 2025-12-18, 2025-12-19, 2025-12-22, 2025-12-23, 2025-12-24, 2025-12-26, 2025-12-29, 2025-12-30, 2025-12-31. On 10 dates option rows exist but no valid raw-target pair was found: 2020-03-13, 2020-03-30, 2020-04-06, 2020-04-07, 2020-04-08, 2020-04-20, 2020-08-26, 2020-09-02, 2023-12-27, 2023-12-28.

The [daily pair CSV](https://github.com/JUN-ZS/brush-timber-mountain-brook/blob/feat/qqq-hybrid-operator-terminal-v1-20261009/research/qqq_hybrid_operator_terminal_v1/QQQ_FULL_HISTORY_DAILY_PAIRS_RUN22.csv) contains 1,956 rows, including dates with chain data but no valid raw-target pair; missing expected dates are explicitly listed above and in the JSON summary.

## Annual diagnostics

Pair coverage below is measured against the **full expected session count per year**, not only dates with source rows. Credit gaps are model minus observed short-Bid/wing-Ask reference, USD/share; a positive proxy gap means the model's estimated credit exceeds that observed-side reference.

| Year | Expected sessions | Chain dates (% expected) | Raw-target pairs (% expected) | Median repo input vs raw close | Median proxy credit gap | Median absolute source-IV gap | Short haircut too narrow | Wing haircut too narrow |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2018 | 211 | 210 (99.53%) | 210 (99.53%) | -4.96% | $0.130 | $0.031 | 86.19% | 99.05% |
| 2019 | 252 | 251 (99.60%) | 251 (99.60%) | -4.14% | $0.125 | $0.025 | 59.76% | 92.83% |
| 2020 | 253 | 252 (99.60%) | 244 (96.44%) | -3.36% | $0.394 | $0.040 | 36.89% | 75.00% |
| 2021 | 252 | 251 (99.60%) | 251 (99.60%) | -2.95% | $0.475 | $0.060 | 40.64% | 80.88% |
| 2022 | 251 | 251 (100.00%) | 251 (100.00%) | -2.41% | $0.170 | $0.061 | 5.18% | 29.48% |
| 2023 | 250 | 250 (100.00%) | 248 (99.20%) | -1.72% | $-0.023 | $0.096 | 2.02% | 15.32% |
| 2024 | 252 | 252 (100.00%) | 252 (100.00%) | -1.04% | $0.019 | $0.106 | 4.37% | 21.43% |
| 2025 | 250 | 239 (95.60%) | 239 (95.60%) | -0.48% | $0.421 | $0.090 | 12.97% | 50.21% |

## VIX-regime diagnostics

| VIX bucket | Chain dates | Raw-target pairs (% of chain dates) | Median proxy credit gap | Median absolute source-IV gap | Short haircut too narrow | Wing haircut too narrow |
|---|---:|---:|---:|---:|---:|---:|
| ELEVATED_25_35 | 284 | 283 (9964.79%) | $0.307 | $0.048 | 23.67% | 55.12% |
| HIGH_GTE35 | 60 | 54 (9000.00%) | $0.863 | $0.054 | 81.48% | 100.00% |
| LOW_LT15 | 503 | 501 (9960.24%) | $0.078 | $0.061 | 36.13% | 53.49% |
| NORMAL_15_25 | 1109 | 1108 (9990.98%) | $0.246 | $0.063 | 26.26% | 57.31% |

In the **VIX ≥35** subset, the haircut is too narrow on **81.5%** of short legs and **100.0%** of wings (54 matched pairs). The model/proxy gap is strongly regime-dependent; a single unconditional spread/IV correction is not supported by this diagnostic.

## Source and interpretation limits

- Median valid positive, non-crossed two-sided quotes across chain dates: **93.91%**. This is row-level quote quality, not executable size or fill confirmation.
- Median VIX-proxy/source-IV ratio: short **1.102×**; wing **1.058×**.
- The source is the public `anahatsingh-ui/options-dataset-hist` QQQ EOD preservation mirror, not exchange-hosted OPRA data. README-reported 4:00 p.m. US Eastern snapshots do not prove fills at the strategy decision timestamp.
- QQQ option files do not supply VXX option history. Existing VXX option marks remain `DERIVED_BS_VIX / NOT_OPRA`.
- `trade_replay_approved=false` and `not_a_strategy_backtest=true`. No CAGR, MaxDD, deployability, or incremental-edge claim is made.

## Research decision

Keep **Option underlying price basis** and **Per-leg spread realism** gates **BLOCKED for trade replay**. Use contemporaneous raw nominal QQQ spot for option strike/quote geometry; retain adjusted-close data for core total-return accounting only. Extend adverse-fill/commission validation against actual strategy decision timestamps before considering any strategy replay. Do not tune the frozen Original Hybrid policy or infer strategy performance from this diagnostic.

## Pinned source integrity

All eight annual QQQ option Parquet files, the underlying price file, and the exact repository/model source files passed SHA/byte verification in Run #22. The JSON summary records every pinned SHA and per-year/VIX-bucket metrics.
