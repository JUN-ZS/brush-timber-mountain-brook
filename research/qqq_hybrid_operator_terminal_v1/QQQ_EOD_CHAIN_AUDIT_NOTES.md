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
