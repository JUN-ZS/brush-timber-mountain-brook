# QQQ Full-History EOD Quote Alignment — Grok Bot Linux Run #2

**Result:** `HASH_VERIFIED_SOURCE_COVERAGE_DIAGNOSTIC`. This is a source/quote diagnostic, **not** a strategy backtest; `trade_replay_approved=false`.

- **Linux research workflow:** [Grok Bot Run #2](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38106167931)
- **Full-history audit job:** [Job log](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38106167931/job/114372052799)
- **Independent Windows audit:** [Public EOD Run #77](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38106167972)
- **Current code head:** `8635cc0bd9d437c75a488ae28597c2f70a88f149`
- **Window requested:** 2018-03-01 to 2025-12-31
- **Source:** `anahatsingh-ui/options-dataset-hist`, public QQQ EOD preservation mirror; pinned annual Parquet sizes / Git blob hashes passed.

## Coverage denominator

| Measure | Observed | Coverage of 1,971 expected sessions |
|---|---:|---:|
| Expected sessions | 1,971 | 100.00% denominator |
| Raw underlying price dates | 1,960 | 99.44% |
| QQQ option-chain dates | 1,956 | 99.24% |
| Valid raw-spot target-pair dates | 1,946 | 98.73% |

The last available raw underlying price and QQQ option chain both end on **2025-12-15**. All 11 expected sessions from 2025-12-16 through 2025-12-31 are absent. Four additional isolated expected sessions also have no option rows: 2018-11-06, 2019-09-03, 2020-06-23, and 2021-11-04. Ten chain-present dates had no valid target pair. None of these missing observations is forward-filled or interpolated.

## Measured price-basis and option-credit diagnostics

| Diagnostic | Result | Interpretation |
|---|---:|---|
| Repository spot vs raw nominal QQQ close | Median −2.719% (n=1,956) | Spot basis can alter target strikes / Deltas |
| VIX-derived proxy credit minus observed same-strike EOD short Bid − wing Ask | Median +$0.181/share (n=1,946) | Proxy tends to overstate conservative side credit at the median |
| Absolute VIX-proxy credit gap | Median $0.196/share (n=1,946) | Material model-fit discrepancy remains |
| Chain-IV model credit gap | Median −$0.004/share; median absolute $0.060/share (n=1,946) | Closer fit, but not independent validation because source IV may be quote-derived |
| Model half-spread haircut narrower than observed short-leg half-spread | 30.0% | Observed side spread often wider than model haircut |
| Model half-spread haircut narrower than observed wing half-spread | 57.2% | More frequent mismatch on the protective wing |

Stress-regime diagnostic: for VIX ≥35, the matched sample is only **54** pairs. The model half-spread haircut was narrower than observed for 81.5% of short legs and 100% of wings. This is a caution, not a newly approved VIX-dependent filter or correction coefficient.

## Gate and implementation consequence

1. **Source integrity passes**; the end-of-window data coverage does not.
2. The 4:00 PM US/Eastern timestamp is reported by the mirror README, but exact quote timestamps and executable decision-time fills are unverified.
3. Source-reported IV can be inferred from the same quote; it is not independent proof that the model price is correct.
4. These data do not support a claim for strategy CAGR, daily MTM MaxDD, Sharpe, ES95, or live fill quality.
5. Keep this evidence visible in the operator terminal and Option Chain Lab as a warning only. Do not silently switch adjusted/raw spot, tune spread haircuts, or create a trade signal from this report.

### Related Far-Call result

[Windows Far-Call Run #48](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38106167957) and the Linux research workflow completed successfully, and the V2 decomposition independently reconciled 1,688 closed-trade rows with zero failures over one cent and maximum absolute reconciliation error USD 0.00. However, V2 status remains `DESCRIPTIVE_DECOMPOSITION_ONLY_NOT_PERFORMANCE_APPROVED`, the source max-loss zero-cost base screen is `FAILS_CURRENT_BASE_SCREEN`, and the performance gate remains blocked by non-confirmed EOD fills and incomplete daily source coverage. This is not an approval to integrate FAR CALL into Frozen Original Hybrid.

