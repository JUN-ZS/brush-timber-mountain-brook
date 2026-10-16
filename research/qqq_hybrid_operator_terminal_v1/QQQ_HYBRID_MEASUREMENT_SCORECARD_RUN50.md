# QQQ Hybrid Measurement Scorecard — Run #50 / Grok Bot Run #4

**Disposition:** Accuracy for trade-performance use is **BLOCKED**; Generality is **NOT DEMONSTRATED**; Integration **FAILS_CURRENT_BASE_SCREEN**. The FAR CALL overlay remains research-only and is not approved for the Frozen Original Hybrid.

## Verified code and runs

- Validated code head: `b906026307890f35b980d0e600972f57e12c2bf8`
- Windows listed-contract replay + V2 decomposition: [Far-Call Run #50](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38112339211) — SUCCESS.
- Linux replay, quote audit and terminal regression: [Grok Bot Linux Run #4](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38112339543) — SUCCESS on `grokbot-box-linux-x64`.
- Windows app QA: [Terminal Run #162](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38112339146) — SUCCESS.
- Windows public QQQ EOD quote audit: [Audit Run #79](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38112339179) — SUCCESS.

These pass results establish that the tested code, regressions and diagnostic pipeline run. They do not establish live fill quality or strategy profitability. Artifact upload in Far-Call Run #50 was rejected by GitHub Actions storage quota; the completed job log contains the decomposition and confirms the output files existed.

## The three axes

| Axis | Status | Evidence and decision |
|---|---|---|
| **Accuracy** | **BLOCKED for trade performance** | The internal closed-trade cash-flow audit passes on 1,688 / 1,688 rows, with zero reconciliation failures above USD 0.01 and maximum absolute error USD 0.00. However, historical source coverage ends 2025-12-15, leaving 11 expected sessions missing; the repo spot differs from raw QQQ close by median −2.72%; the VIX-derived model credit is +USD 0.181/share above observed EOD-side credit at the median; modeled half-spread haircuts are narrower than observed on 30.0% of short legs and 57.2% of wings. EOD sides are not confirmed fills. Accounting sub-gate PASS does not offset these critical trade-accuracy blocks. |
| **Generality** | **NOT DEMONSTRATED** | The 2018–2025 period has been repeatedly inspected and is development evidence, not a virgin holdout. The source misses 11 terminal expected sessions; 24 daily NAV comparisons are unmatched in the zero-cost source max-loss arm. A full-composite daily return series and untouched chronological holdout are not available, so regime/rolling robustness and final OOS performance are not passed. |
| **Integration** | **FAILS_CURRENT_BASE_SCREEN** | In the zero-extra-cost 0.8% NAV maximum-loss budget arm, 106 positions opened and 105 closed. Gross entry credit USD 10,782 minus gross exit debit USD 16,428 produces closed-trade net P&L **−USD 5,646**. The last observed paired-date NAV difference versus the no-call control is **−USD 5,552** across 1,947 matched dates; 24 dates are unmatched and the last paired date is 2025-12-15. There is one unresolved/open position at the end. The control uses the same 42% QQQ core total-return proxy plus static 58% cash and no option trades; it is **not** the full Frozen Original Hybrid composite. |

The paired comparison also recorded 32 positive NAV-gap days out of 1,947 matched dates. That is a descriptive count of paired marks, not a complete strategy return metric.

## Pre-registered integration bars (unchanged)

The Measurement Contract sets three alternative primary objectives. Every objective still requires the Accuracy hard gates and Generality evidence to pass, no same-close lookahead, disclosed limitations, an economic explanation beyond one isolated event, and human review before any integration.

1. **Return enhancement:** net-of-cost final OOS CAGR improvement of at least +0.50 percentage points; MaxDD worsens by no more than 1.00 percentage point; Sharpe (risk-free rate 0) drops by no more than 0.05.
2. **Downside protection:** final OOS MaxDD improves by at least 2.00 percentage points **and** daily-return ES95 improves by at least 10%, while CAGR give-up is no more than 0.50 percentage points. ES95 is the arithmetic mean of the worst 5% of daily portfolio returns.
3. **Capital deployment / timing:** either the downside-protection gate passes, or net-of-cost terminal NAV is no worse than 0.50% below baseline and one pre-selected deployment metric improves: average unallocated cash / NAV falls by at least 5.00 percentage points, or time to the same target allocation falls by at least 20%. All capital, margin and option-risk gates must also pass.

No CAGR, daily MTM MaxDD, Sharpe or ES95 is calculated from this partial paired-mark series. They are **UNAVAILABLE**, not zero. No aggregate Accuracy score is published because the current contract has not preregistered item-level numeric weights; categorical hard gates remain binding and cannot be averaged into a PASS.

## Next permitted work

- Do not tune delta, DTE, stop thresholds, quote-width cutoffs, or cost assumptions to rescue the reviewed period.
- Resolve the terminal source gap and the unresolved position, and obtain timestamped execution evidence or prospective paper observations before attempting an execution-aware evaluation.
- For any new strategy hypothesis, preregister its primary objective, data window, cost model, metric thresholds and trial ledger before examining the final lockbox. The already reviewed 2018–2025 interval must remain development evidence.
- Keep FAR CALL outside Frozen Original Hybrid; do not change main, live sizing, or broker-order permissions.

Full thresholds and source rules: [RESEARCH_MEASUREMENT_CONTRACT.md](RESEARCH_MEASUREMENT_CONTRACT.md). Related diagnostic: [QQQ_FAR_CALL_INCREMENTAL_VALUE_V2_RUN45.md](QQQ_FAR_CALL_INCREMENTAL_VALUE_V2_RUN45.md).
