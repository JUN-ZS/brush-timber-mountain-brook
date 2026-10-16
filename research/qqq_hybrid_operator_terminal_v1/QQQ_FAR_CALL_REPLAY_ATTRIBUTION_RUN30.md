# QQQ Far-Call Listed-Contract EOD Replay — Attribution Run #30

**Evidence class:** observed EOD option quote sides + derived replay cash flows; not exchange-confirmed fills.
**Run:** [Windows self-hosted Actions Run #30](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38079917754)
**Replay source head:** `1b1db48653c9b19b5f4fe06e3ceca43466ae8d75`
**Scope:** QQQ core proxy plus QQQ call-credit overlay only. Not the full QQQ/VXX Hybrid.
**Decision:** keep the overlay research-only; do not integrate.

## Verification and reproducibility

- The Run #30 replay workflow completed successfully on the recorded head, including compilation, offline regressions, SHA-pinned history replay, and output-file existence checks.
- **1,688 closed-trade rows across the 16 budget/cost scenarios:** 1,688 cash-flow reconciliations passed, 0 failed, 0 were blocked. The recomputation is gross entry credit minus entry costs minus gross exit debit minus exit costs, tolerance $0.01.
- The script wrote the replay summary, trade/event/daily CSVs, and attribution JSON/CSV to the runner. GitHub rejected the artifact upload because the repository artifact-storage quota was full; therefore the individual CSV/JSON files are not downloadable from this run. The numbers below were read from the actual job log, not invented from a narrative.
- Coverage remains incomplete: 1,971 expected sessions from 2018-03-01 to 2025-12-31; 1,956 sessions with chain rows; public data stop at 2025-12-15, including 11 terminal sessions without source observations and 4 missing sessions earlier in the range.
- Mark diagnostics are incomplete for portfolio performance: 1,698 daily marks OK, 257 `INVALID_EXIT_QUOTE`, 5 `CONTRACT_ROW_MISSING`, and 11 `CORE_TOTAL_RETURN_PRICE_MISSING`. There were 273 missing position-mark sessions. Do not publish CAGR, daily MTM MaxDD, Sharpe or ES95 from this path.

## Closed-trade results: source 0.8% NAV maximum-loss budget

All amounts USD; all are quote-side replay results, not guaranteed fills.

| Extra slippage / leg | Commission / contract / side | Opened | Closed | Closed-trade net P&L | Mean per closed trade | Missing position marks |
|---:|---:|---:|---:|---:|---:|---:|
| $0.000 | $0.00 | 106 | 105 | -$4,255.00 | -$40.52 | 273 |
| $0.000 | $0.65 | 106 | 105 | -$4,643.00 | -$44.22 | 273 |
| $0.025 | $0.00 | 107 | 106 | -$5,136.00 | -$48.45 | 253 |
| $0.025 | $0.65 | 107 | 106 | -$5,583.20 | -$52.67 | 253 |
| $0.050 | $0.00 | 107 | 106 | -$6,895.00 | -$65.05 | 253 |
| $0.050 | $0.65 | 107 | 106 | -$7,382.80 | -$69.65 | 253 |
| $0.100 | $0.00 | 108 | 108 | -$11,281.00 | -$104.45 | 258 |
| $0.100 | $0.65 | 108 | 108 | -$11,379.60 | -$105.37 | 254 |

## Closed-trade results: legacy 1.2% NAV credit budget

This is a separate, non-equivalent sizing interpretation; it is not a maximum-loss budget.

| Extra slippage / leg | Commission / contract / side | Opened | Closed | Closed-trade net P&L | Mean per closed trade | Missing position marks |
|---:|---:|---:|---:|---:|---:|---:|
| $0.000 | $0.00 | 106 | 105 | -$49,316.00 | -$469.68 | 284 |
| $0.000 | $0.65 | 106 | 105 | -$57,206.60 | -$544.82 | 284 |
| $0.025 | $0.00 | 107 | 106 | -$70,119.00 | -$661.50 | 264 |
| $0.025 | $0.65 | 107 | 106 | -$76,622.80 | -$722.86 | 264 |
| $0.050 | $0.00 | 107 | 106 | -$99,334.00 | -$937.11 | 264 |
| $0.050 | $0.65 | 107 | 106 | -$107,840.40 | -$1,017.36 | 264 |
| $0.100 | $0.00 | 107 | 107 | -$142,282.00 | -$1,329.74 | 229 |
| $0.100 | $0.65 | 97 | 97 | -$147,984.40 | -$1,525.61 | 216 |

## Attribution: base-cost maximum-loss-budget scenario

For the selected base scenario (zero extra slippage and zero commission), exit reasons decompose the -$4,255 closed-trade result as follows:

| Exit reason | Closed trades | Net P&L | Win fraction | Interpretation |
|---|---:|---:|---:|---|
| `DTE_LE_7` | 62 | -$4,028.00 | 50.0% | Time-based exit group net negative despite half winning |
| `PNL_OVER_MAXLOSS_LE_NEG_0P55` | 8 | -$3,810.00 | 0.0% | Loss-stop group is the most negative per trade |
| `EXPIRY_INTRINSIC_SETTLEMENT` | 35 | +$3,583.00 | 100.0% | Positive intrinsic-settlement proxy, not confirmed exercise/fill |

The three groups are exhaustive for the 105 closed spreads in this scenario. They do **not** prove which exit rule causes the loss, and the EOD event/quote timing is not independently verified.

The post-hoc exit-date momentum groups are also descriptive: the 60 trades exiting while the 20-session raw QQQ trend was up by at least 2% had -$9,030 P&L; 19 down-trend exits had +$2,186 and 26 range exits had +$2,589. These sums reconcile to -$4,255. This is an **exit-state correlation**, not a causal edge or a license to add a trend filter. Entry-time trend groups were all negative except the single insufficient-history row: down 21 trades/-$527, range 22/-$1,071, up 61/-$2,715. The entry trend split therefore does not isolate an obvious profitable regime.

## Decision

1. The current listed-contract quote-side replay does not show positive closed-trade incremental P&L in any of the 16 budget/cost combinations.
2. This result is strong enough to reject the *current tested overlay* from integration, but it does not prove every QQQ call-credit strategy is unprofitable.
3. The next engineering step is to decompose the 257 invalid exit marks by cause and leg. The previous code grouped missing/zero/crossed bid/ask on either leg into one `INVALID_EXIT_QUOTE` bucket, hiding whether the primary issue was a missing leg quote, crossed market, or inconsistent vertical mark. Do not tune exits until this mark path is understood.
4. No CAGR/MaxDD conclusion is allowed until the full marked NAV path is valid and source coverage/timing limitations are resolved.
5. This run does not cover VXX option history and is not a full Hybrid backtest. VXX short-stock carry remains a separate 3% annual borrow-cost assumption from user input, not verified historical borrow records.

## Guardrails

The replay is an EOD quote-side proxy. Extra slippage/commission rows are hypothetical cost scenarios. The period has already been inspected and is not a virgin holdout. Original Hybrid, `main`, live sizing and broker-order permissions remain unchanged.
