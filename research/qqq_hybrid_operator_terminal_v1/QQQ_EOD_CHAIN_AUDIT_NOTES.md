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
