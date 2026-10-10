# QQQ Full-History EOD Quote Alignment — Run #18

**Status:** hash-verified source/quote diagnostic; **not** a strategy backtest.  
**Actions:** [Run #18 — Windows self-hosted](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38009943427) · **PR:** [#99](https://github.com/JUN-ZS/brush-timber-mountain-brook/pull/99) · **Branch head:** `8e983afe2f30711a0b6abf6e3da41c3c3944519a`  
**Requested window:** 2018-03-01 to 2025-12-31 · **Last source observation:** 2025-12-15.  
**Result:** `HASH_VERIFIED_SOURCE_COVERAGE_DIAGNOSTIC`; source/data integrity and streaming job succeeded.

## Key finding

The option quote layer is **not ready for trade replay**. Across 1,946 raw-spot target pairs, the repository's QQQ input is below contemporaneous raw nominal close by median **—%**. The VIX-proxy model's conservative credit minus observed EOD **short Bid − wing Ask** has median **+— per share** (median absolute gap **—**). The modeled per-leg half-spread haircut is narrower than observed on **—%** of short legs and **—%** of wings.

Replacing proxy IV with source-reported per-leg IV lowers the median absolute gap to **— per share**. This is **not independent validation**, because source IV may be derived from the same quote midpoint. In the VIX ≥35 subset (54 pairs), the haircut is too narrow on **81.5%** of short legs and **100.0%** of wings.

## Corrected source coverage

| Measure | Observed | Coverage of all expected sessions |
|---|---:|---:|
| Repo-universe expected sessions | 1,971 | 100% denominator |
| Raw underlying closes | 1,960 | 9944.2% |
| QQQ option rows | 1,956 | 9923.9% |
| Raw-spot target pairs | 1,946 | 9873.2% |
| Target pairs / option dates | 1946 / 1956 | 9948.9% |

**Not full-window-complete:** both raw underlying data and option rows stop on **2025-12-15**. The 11 expected terminal sessions not covered are: 2025-12-16, 2025-12-17, 2025-12-18, 2025-12-19, 2025-12-22, 2025-12-23, 2025-12-24, 2025-12-26, 2025-12-29, 2025-12-30, 2025-12-31. Option rows are also absent inside the earlier source span on: 2018-11-06, 2019-09-03, 2020-06-23, 2021-11-04. On 10 dates option rows exist but no valid raw-target pair was found: 2020-03-13, 2020-03-30, 2020-04-06, 2020-04-07, 2020-04-08, 2020-04-20, 2020-08-26, 2020-09-02, 2023-12-27, 2023-12-28.

## Annual diagnostics

Pair coverage below is shown against the **full expected session count per year**, not only days where the source has rows. Credit gaps are model minus observed short-Bid/wing-Ask reference, USD/share; a positive proxy gap means model credit is greater than the observed-side reference.

| Year | Expected sessions | Chain dates (% expected) | Raw-target pairs (% expected) | Median repo input vs raw close | Median proxy credit gap | Median absolute source-IV gap | Short haircut too narrow | Wing haircut too narrow |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2018 | 211 | 210 (99.5%) | 210 (99.5%) | -4.96% | $0.130 | $0.031 | 86.2% | 99.0% |
| 2019 | 252 | 251 (99.6%) | 251 (99.6%) | -4.14% | $0.125 | $0.025 | 59.8% | 92.8% |
| 2020 | 253 | 252 (99.6%) | 244 (96.4%) | -3.36% | $0.394 | $0.040 | 36.9% | 75.0% |
| 2021 | 252 | 251 (99.6%) | 251 (99.6%) | -2.95% | $0.475 | $0.060 | 40.6% | 80.9% |
| 2022 | 251 | 251 (100.0%) | 251 (100.0%) | -2.41% | $0.170 | $0.061 | 5.2% | 29.5% |
| 2023 | 250 | 250 (100.0%) | 248 (99.2%) | -1.72% | $-0.023 | $0.096 | 2.0% | 15.3% |
| 2024 | 252 | 252 (100.0%) | 252 (100.0%) | -1.04% | $0.019 | $0.106 | 4.4% | 21.4% |
| 2025 | 250 | 239 (95.6%) | 239 (95.6%) | -0.48% | $0.421 | $0.090 | 13.0% | 50.2% |

## VIX-regime diagnostics

| VIX bucket | Chain dates | Raw-target pairs (% of chain dates) | Median proxy credit gap | Median absolute source-IV gap | Short haircut too narrow | Wing haircut too narrow |
|---|---:|---:|---:|---:|---:|---:|
| LOW_LT15 | 503 | 501 (99.6%) | $0.078 | $0.061 | 36.1% | 53.5% |
| NORMAL_15_25 | 1109 | 1108 (99.9%) | $0.246 | $0.063 | 26.3% | 57.3% |
| ELEVATED_25_35 | 284 | 283 (99.6%) | $0.307 | $0.048 | 23.7% | 55.1% |
| HIGH_GTE35 | 60 | 54 (90.0%) | $0.863 | $0.054 | 81.5% | 100.0% |

## Source and interpretation limits

- Median share of rows with valid positive non-crossed two-sided quotes on option dates: **93.91%**. Valid quotes do not establish executable size or fills.
- Median proxy/source-IV ratio: short **1.102×**; wing **1.058×**. The ratio is regime-dependent; these results do not establish a single stable correction.
- The dataset is the public `anahatsingh-ui/options-dataset-hist` QQQ EOD preservation mirror, not exchange-hosted OPRA data. The reported snapshot is 4:00 p.m. US Eastern and does not prove a fill at the strategy decision timestamp.
- QQQ option files do not supply VXX option history. Existing VXX option marks remain `DERIVED_BS_VIX / NOT_OPRA`.
- `trade_replay_approved=false` and `not_a_strategy_backtest=true`. No CAGR, MaxDD, deployability or incremental-edge claim is made.

## Decision / next research step

Keep **Option underlying price basis** and **Per-leg spread realism** accuracy gates **BLOCKED for trade replay**. Separate contemporaneous raw nominal spot for option strike/quote geometry from adjusted-close data used for core total-return accounting, then rerun with observed-side and adverse-fill sensitivity. Do not tune the frozen Original Hybrid policy, infer strategy performance from this diagnostic, or authorize broker orders on its basis.

## Pinned market-data files

| File | Bytes | Git blob SHA | Check |
|---|---:|---|---|
| `options_2018.parquet` | 29215815 | `4a130fe579ee141c5836ccaaf093c0cb752ebb19` | CACHED_HASH_VERIFIED |
| `options_2019.parquet` | 30998008 | `95386cb37a6b1ca757e7fd6a0b0fd458c91e04ca` | CACHED_HASH_VERIFIED |
| `options_2020.parquet` | 59412637 | `9d7abe1144c55e0091d28eca61deec4ac72393a5` | CACHED_HASH_VERIFIED |
| `options_2021.parquet` | 74224966 | `3488cffd498a8851861a8dca7d1849a748bc759d` | CACHED_HASH_VERIFIED |
| `options_2022.parquet` | 69941736 | `e9bcb16986835e3eba304300aeb6d6a8ed56bbe9` | CACHED_HASH_VERIFIED |
| `options_2023.parquet` | 71647343 | `bbaa5aeefc54c76628142a6e95c7424995049063` | CACHED_HASH_VERIFIED |
| `options_2024.parquet` | 82434832 | `40c1c2fd986da9b5bcf363cd44c9d5ac3eecc8c3` | CACHED_HASH_VERIFIED |
| `options_2025.parquet` | 85765453 | `e92ad6b5c2e757d2c869f747a94853e630142cbf` | CACHED_HASH_VERIFIED |
| `underlying_prices.parquet` | 332454 | `f3a892bc4c88c692900b5c0071322c6db408996a` | CACHED_HASH_VERIFIED |

## Pinned repository/model source files

| File | Bytes | Git blob SHA | Check |
|---|---:|---|---|
| `research/qqq_hybrid_dynamic_deployment_v1_1_replay.py` | 15102 | `ac74b3812c826ad491fb829108f26397322e45eb` | HASH_VERIFIED |
| `research/qqq_hybrid_operator_terminal_v1/audit_qqq_public_eod_options.py` | 21085 | `99337743e4133a6905c2904d889cf1b566997e9e` | HASH_VERIFIED |
| `src/data/universe.json` | 1045161 | `43c1b3053d17b278cfc01bb0b87e41679f3e85c9` | HASH_VERIFIED |
