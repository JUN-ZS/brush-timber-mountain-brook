# QQQ Public EOD Chain Audit — source and scope

**Status:** research-only. No strategy parameter, live sizing, or broker-order permission changes.

## Candidate source

The public GitHub preservation mirror anahatsingh-ui/options-dataset-hist lists historical EOD chains for SPY, QQQ and IWM, not VXX. Its README reports QQQ coverage from 2011–2025 and one row per contract per trading day at 4:00 PM US Eastern. The project says it is a preservation mirror of an earlier dataset; therefore this audit validates the actual downloaded data against immutable Git blob SHA and expected byte count before inspecting rows.

Pinned source files:
- QQQ 2020: 59,412,637 bytes, Git blob SHA 9d7abe1144c55e0091d28eca61deec4ac72393a5.
- QQQ 2024: 82,434,832 bytes, Git blob SHA 40c1c2fd986da9b5bcf363cd44c9d5ac3eecc8c3.
- QQQ underlying prices: 332,454 bytes, Git blob SHA f3a892bc4c88c692900b5c0071322c6db408996a.

## Pre-registered checkpoints

- 2020-03-16: COVID shock sample, sourced from the 2020 annual file.
- 2024-08-05: volatility shock sample, sourced from the 2024 annual file.

For each date, the audit reports option rows, call/put counts, percentage of rows with positive non-crossed two-sided Bid/Ask, and any Call candidates with 30–60 calendar DTE and absolute delta 0.03–0.10. Candidate samples are ranked by closeness to absolute delta 0.06, 45 DTE, then narrower Bid/Ask spread; this is a diagnostic selection, not an optimized trading rule.

## Measurement boundary

- 4:00 PM EOD quotes are not 15:45 snapshots or executable intraday fills; quotes may still be stale/illiquid.
- This source can inform QQQ call-credit calibration only; it does not supply VXX option history or OCC deliverables for adjusted VXX contracts.
- A successful row/quote audit is not a strategy backtest and does not authorize replacing the current model marks.
- Next valid use: compare the QQQ far-call model's selected strike and estimated credit to same-date observed EOD quote ranges; include slippage/commissions and report exclusions before any integration proposal.



## Measured outcome — public QQQ EOD chain audit Run #1

- [Windows self-hosted QQQ audit Run #1](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38002570136) completed successfully with `SAMPLE_DATES_HAVE_QQQ_CHAIN_ROWS`.
- All 3 files passed expected byte-count and Git blob SHA checks. At 2020-03-16, 5,760 QQQ option rows were returned; 89.76% had positive non-crossed two-sided Bid/Ask. At 2024-08-05, 7,704 rows were returned; 93.93% passed that basic quote test.
- The probe found 47 and 25 call rows respectively within 30–60 calendar DTE and absolute delta 0.03–0.10. That is a diagnostic candidate count, not a recommended portfolio position.
- Examples on 2020-03-16 had 68–121% spread/midpoint, including zero-volume / zero-OI quotes; the selected examples on 2024-08-05 had 7.62–15.53% spread/midpoint. This supports separating two-sided quote validity from executable liquidity and fill realism.
- Detailed report: [QQQ_PUBLIC_EOD_AUDIT_RUN1_RESULTS.md](QQQ_PUBLIC_EOD_AUDIT_RUN1_RESULTS.md). The source is an EOD preservation mirror, QQQ only; it is not VXX history, not intraday 15:45 data, and not a strategy backtest.


## Run #5 follow-up: exact listed-contract comparison

[Windows self-hosted Run #5](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38004657651) passed source blob pins and compared the preserved QQQ model with same-date public EOD chain contracts. Full results and caveats are in [QQQ_ADJUSTED_VS_RAW_SPOT_BASIS.md](QQQ_ADJUSTED_VS_RAW_SPOT_BASIS.md). Key finding: at identical listed strikes, replacing the repo adjusted-series spot with raw close raises the model's conservative credit by $0.33–$0.42/share; however the raw-close proxy mark remains around $1.30–$1.46/share above the snapshot's short-Bid-minus-wing-Ask credit on the raw-target pairs. The nominal-price correction is real but not sufficient. The next probe must include exact per-leg source IV and isolate spot basis from the VIX→QQQ-IV proxy; no strategy replay or policy change is approved from two dates.


## Run #8: per-leg IV attribution

Windows self-hosted [Run #8](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38005010981) passed the pinned file/source hash checks, pairing tests, and QQQ EOD chain audit with per-leg source IVs. Proxy IV was 1.37×–1.62× source IV for selected short legs and 1.40×–1.77× for wings. Raw-spot repricing with source IV reproduced the source's midpoint values closely, but this is not independent validation because IV may have been calculated from the same quote mark. The model spread haircut remained far too narrow on the 2020 shock-day legs; see QQQ_ADJUSTED_VS_RAW_SPOT_BASIS.md and raw JSON QQQ_MODEL_PRICE_ALIGNMENT_RUN8.json. Do not promote any strategy result from this two-date probe.


## Next step: preselected multi-regime QQQ quote diagnostic

The next audit version samples eight dates from the already hash-pinned 2020 and 2024 annual Parquet files: 2020-01-15, 2020-03-16, 2020-06-08, 2020-10-30, 2024-02-01, 2024-04-15, 2024-08-05 and 2024-11-06. They are intended to cover lower-volatility, shock, rebound/rotation and recovery contexts. This expands regime coverage without adding new annual-file downloads. Because the date set was chosen after reviewing initial results, it is a development diagnostic—not blind OOS. Report the row/quote quality and price-basis × IV-basis comparisons at each date; do not collapse these observations into a strategy CAGR claim.


## Run #11: eight-date regime diagnostic

[Windows self-hosted Run #11](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38005508316) passed all hash/source gates and all 8 preselected date queries. There were 4,712–8,560 option rows per date, with 89.76%–98.65% positive non-crossed two-sided quotes. Repo spot was 0.90%–3.73% below raw close on every date. The VIX proxy/source-IV ratio varied by regime (raw-target short leg 0.88×–1.62×, wing 0.84×–1.70×); on 2020-01-15, adjusted-input target Delta was 0.527/0.396 versus 0.143/0.075 for raw-spot target. This indicates regime-dependent error compensation, not validation. Raw output is pinned in QQQ_MULTI_REGIME_ALIGNMENT_RUN11.json; report and next-stage proposal are in QQQ_ADJUSTED_VS_RAW_SPOT_BASIS.md.


## Run #16 — streamed full-history QQQ quote-alignment audit

[Windows self-hosted Run #16](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38006925584) completed with all pinned source/model SHA checks verified. The script streamed the eight annual QQQ files and returned 1,956 chain dates and 1,946 raw-target matched pairs across its observed source span. **Important correction:** although the request window is 2018-03-01 to 2025-12-31, both the raw underlying-price source and QQQ option chain stop at **2025-12-15**. The repo universe has 1,971 expected sessions in the requested interval; 11 sessions after the source cutoff are not covered, in addition to four missing chain dates inside the source span (2018-11-06, 2019-09-03, 2020-06-23, 2021-11-04). The original Run #16 denominator intersected dates with raw spot first and therefore understated the missing-tail problem; the follow-up code uses the full universe date index and separately reports price, chain, and pair coverage.

### Run #16 source-alignment measurements

| Year | Expected universe sessions | Chain dates | Raw-target pairs | Median repo input vs raw close | Median proxy credit gap ($/share) | Median absolute chain-IV credit gap ($/share) | Short haircut too narrow | Wing haircut too narrow |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2018 | 211 | 210 | 210 | -4.96% | +0.130 | 0.031 | 86.2% | 99.0% |
| 2019 | 252 | 251 | 251 | -4.14% | +0.125 | 0.025 | 59.8% | 92.8% |
| 2020 | 253 | 252 | 244 | -3.36% | +0.394 | 0.040 | 36.9% | 75.0% |
| 2021 | 252 | 251 | 251 | -2.95% | +0.475 | 0.060 | 40.6% | 80.9% |
| 2022 | 251 | 251 | 251 | -2.41% | +0.170 | 0.061 | 5.2% | 29.5% |
| 2023 | 250 | 250 | 248 | -1.72% | -0.023 | 0.096 | 2.0% | 15.3% |
| 2024 | 252 | 252 | 252 | -1.04% | +0.019 | 0.106 | 4.4% | 21.4% |
| 2025 (through Dec 15 only) | 250 | 239 | 239 | -0.48% | +0.421 | 0.090 | 13.0% | 50.2% |

Across 1,946 pairs, the median proxy model-minus-observed short-Bid/wing-Ask credit was **+$0.181/share** (median absolute gap **$0.196/share**); chain-IV repricing reduced the absolute median gap to **$0.060/share**, but this is not independent validation. Across all source dates, the modeled half-spread was narrower than observed leg half-spreads on 30.0% of short legs and 57.2% of wings. In 54 paired observations with VIX >=35, these were 81.5% and 100.0%. This diagnostic contains no strategy return/P&L and does not approve trade replay. Use raw nominal spot for option strikes/pricing, observed quote sides or documented adverse fills, and keep VXX history labelled unavailable / DERIVED_BS_VIX / NOT_OPRA.

The initial Run #16 notes are retained for provenance, but the source-overlap denominator is superseded by corrected Run #18, which uses the full 1,971-session repo-universe index.


### Corrected full-window coverage — Run #18

[Run #18 Actions](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38009943427) completed successfully against branch head `8e983afe2f30711a0b6abf6e3da41c3c3944519a`; all nine market-data files and all three pinned repo/model source blobs verified. The denominator is **1,971** repository-universe sessions: raw underlying closes on **1,960/1,971 (99.44%)**, QQQ option rows on **1,956/1,971 (99.24%)**, and raw-target pairs on **1,946/1,971 (98.73%)**. Both raw underlying and chain data end **2025-12-15**, leaving 11 expected sessions uncovered through 2025-12-31. Four additional option dates are missing inside the earlier source span; 10 dates have chain rows but no valid raw-target pair. The earlier source-overlap denominator is superseded.

Across 1,946 pairs, median repository QQQ input vs raw nominal close is **-2.72%**. VIX-proxy model-minus-observed short-Bid/wing-Ask credit gap median is **+$0.181/share**, median absolute gap **$0.196**. Source-IV repricing's median absolute gap is **$0.060**, with the source-IV circularity caveat. Spread-haircut-too-narrow rates are **30.0% short / 57.2% wing**, rising to **81.5% / 100.0%** for VIX ≥35 (54 pairs).

Full report: [Run #18 Markdown](https://github.com/JUN-ZS/brush-timber-mountain-brook/blob/feat/qqq-hybrid-operator-terminal-v1-20261009/research/qqq_hybrid_operator_terminal_v1/QQQ_FULL_HISTORY_ALIGNMENT_RUN18.md) and [machine-readable summary JSON](https://github.com/JUN-ZS/brush-timber-mountain-brook/blob/feat/qqq-hybrid-operator-terminal-v1-20261009/research/qqq_hybrid_operator_terminal_v1/QQQ_FULL_HISTORY_ALIGNMENT_RUN18.json). This is quote/price-basis evidence only, not a strategy backtest or trade-replay approval. No frozen policy or broker-order boundary changed.
