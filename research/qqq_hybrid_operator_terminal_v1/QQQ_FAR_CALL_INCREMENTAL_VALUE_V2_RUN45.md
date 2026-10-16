# QQQ FAR CALL Incremental-Value Decomposition V2 — Run #45

**Disposition: do not integrate FAR CALL into Frozen Original Hybrid.** This is a research diagnostic using observed EOD quote sides; it is not an executable-fill replay or approved portfolio-performance estimate.

- Actions: https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38091317818
- Workflow result: SUCCESS, Windows self-hosted runner.
- Validated head: \`c4ea8eb569b31d21de68a8d25dadd6f8b5872770\`
- PR #99 remains Draft and unmerged.
- Frozen Original Hybrid, \`main\`, live sizing, and broker-order permissions were not changed.

## What passed

The workflow completed the pinned historical quote replay, the existing regression tests, the new V2 offline decomposition tests, and the decomposition itself. All required local outputs were present and checked:

- \`QQQ_FAR_CALL_INCREMENTAL_DECOMPOSITION_RUN.json\`
- \`qqq_far_call_incremental_decomposition.json\`
- \`qqq_far_call_incremental_decomposition.md\`
- \`qqq_far_call_incremental_decomposition.csv\`

The JSON/Markdown/CSV outputs were rendered to the Actions log and the Markdown was appended to the persistent job summary. Artifact upload was attempted but rejected because GitHub Actions artifact storage quota was full; this does not negate the completed test/replay steps, but the detail files are not downloadable from this run's artifacts.

## Independent cash-flow audit

Across the 16 separate budget/cost arms, the decomposition independently rechecked all **1,688 closed-trade rows**. Results:

- 1,688 rows rechecked.
- 0 rows blocked.
- 0 reconciliation failures above USD 0.01.
- Maximum absolute reconciliation error: USD 0.00.

Identity independently checked on every complete row:

gross entry credit − entry costs − gross exit debit − exit costs = recorded realized net P&L.

This proves internal closed-trade cash-flow consistency, not that EOD quote sides were executable fills.

## Primary budget: 0.8% NAV maximum-loss interpretation

| Slippage per leg | Commission per contract/side | Opens / closes | Closed-trade net P&L | Last observed paired NAV difference | Matched / unmatched NAV days |
|---:|---:|---:|---:|---:|---:|
| $0.000 | $0.00 | 106 / 105 | -$5,646.00 | -$5,552.00 | 1,947 / 24 |
| $0.000 | $0.65 | 106 / 105 | -$6,068.20 | -$5,976.80 | 1,947 / 24 |
| $0.025 | $0.00 | 107 / 106 | -$6,730.00 | -$6,646.00 | 1,947 / 24 |
| $0.025 | $0.65 | 107 / 106 | -$7,185.00 | -$7,103.60 | 1,947 / 24 |
| $0.050 | $0.00 | 107 / 106 | -$8,566.00 | -$8,492.00 | 1,947 / 24 |
| $0.050 | $0.65 | 107 / 106 | -$9,013.60 | -$8,942.20 | 1,947 / 24 |
| $0.100 | $0.00 | 108 / 108 | -$11,268.00 | -$11,268.00 | 1,947 / 24 |
| $0.100 | $0.65 | 108 / 108 | -$11,369.20 | -$11,369.20 | 1,946 / 25 |

The zero-extra-cost arm's closed-trade cash-flow totals are gross entry credit **$10,782** and gross exit debit **$16,428**, producing **-$5,646 before additional costs**. Therefore the adverse result is not explained by commissions/slippage alone. The zero-cost arm opened 106 positions and closed 105; one position remains unresolved/open at the end of this source window.

## Existing exit-mechanism attribution

Base arm: source max-loss budget, zero additional slippage and zero commission.

| Existing exit reason | Closed trades | Net P&L | Mean holding days | Exit basis |
|---|---:|---:|---:|---|
| DTE <= 7 | 62 | -$4,746.00 | 24.61 | EOD short Ask minus wing Bid |
| P&L / max loss <= -0.55 | 9 | -$4,150.00 | 18.22 | EOD short Ask minus wing Bid |
| Expiry intrinsic settlement proxy | 34 | +$3,250.00 | 28.24 | Intrinsic-value proxy, not confirmed exercise/fill |
| **Total** | **105** | **-$5,646.00** | — | — |

The 9 stop-exit trades all lost, averaging about -$461 each. This is a descriptive grouping, not proof that the stop threshold caused the losses. Do not change the exit threshold based on this table alone.

## Additional strata from the same Run #45 replay log

These post-hoc categories are diagnostic only. They are not entry/exit filters and must not be tuned into a new strategy without a new, predeclared experiment.

### By the existing 20-session QQQ momentum label on exit date

| Exit-date momentum bucket | Trades | Closed-trade net P&L |
|---|---:|---:|
| QQQ up >= 2% over 20 sessions | 60 | -$10,171.00 |
| Range, absolute move < 2% | 24 | +$2,314.00 |
| QQQ down <= -2% over 20 sessions | 21 | +$2,211.00 |
| **Total** | **105** | **-$5,646.00** |

The exit-date uptrend bucket dominates the aggregate losses, while range/down buckets offset part of them. This is consistent with short-call spread exposure suffering during persistent QQQ advances, but it does **not** establish causality: the groups are classified using the realized exit date and differ in duration/exit reason. It is not a valid standalone rule to enter only in a particular trend state.

### By signal-day VIX bucket

| Signal-day VIX bucket | Trades | Closed-trade net P&L |
|---|---:|---:|
| Below 15 | 26 | -$3,474.00 |
| 15 to below 25 | 60 | -$2,076.00 |
| 25 to below 35 | 16 | +$388.00 |
| 35 or above | 3 | -$484.00 |
| **Total** | **105** | **-$5,646.00** |

The high-VIX sample has only 3 trades, and the elevated bucket has 16. These small observational subgroups are insufficient to justify regime filters or optimization. Notably, the loss is also present in the low- and normal-VIX groups.

### Entry quote width is not enough to explain it

In the base arm, the entry quote-width diagnostic grouped closed trades as:

- Tight (both legs <=10% spread/mid): 80 trades, -$3,908.
- Moderate (widest leg >10% and <=25%): 17 trades, -$826.
- Wide (widest leg >25%): 8 trades, -$912.

Even the 'tight' group was negative. These bins use EOD displayed Bid/Ask width and do not prove that a live order could fill at those prices.

## Data and measurement gates still blocked

- Expected sessions: 1,971 (2018-03-01 through 2025-12-31).
- Sessions with QQQ option-chain rows: 1,956.
- Last source observation: **2025-12-15**; 11 requested terminal sessions remain uncovered.
- 24 unmatched NAV-mark sessions in the base arm; the last observed NAV difference excludes those unmatched dates.
- One open/unresolved position remains in the base zero-cost arm.
- EOD quote sides have no verified exact tick timestamp and are not confirmed fills.
- The 2018–2025 interval has been repeatedly inspected; it is not a virgin holdout.

Consequently CAGR, daily MTM MaxDD, Sharpe and ES95 remain blocked and are not estimated from this incomplete matched-day series. The legacy 1.2% NAV credit-budget interpretation also remains separate; it produced materially larger closed-trade losses and is not risk-equivalent to the 0.8% max-loss budget.

## Decision and next step

1. Treat this as a **negative incremental-value screen** for the currently tested FAR CALL implementation, not a profitable overlay awaiting parameter polish.
2. Do not tune Delta, DTE, stop, credit budget or quote-width cutoffs to rescue the reviewed period.
3. Keep FAR CALL outside Frozen Original Hybrid. If further work is justified, investigate the existing trade-level rows around entry credit versus subsequent exit debit and the persistent-uptrend loss concentration, using a predeclared analysis rather than a parameter search.
4. Before any future strategy-level claim, first recover/resolve the terminal source gap and unresolved position, and obtain stronger timestamped execution evidence or conduct prospective paper tracking.
5. No main merge, Frozen Original Hybrid mutation, live sizing change or broker order activation is authorized.

The new analysis is reproducible at the recorded Actions head, but storage quota prevented artifact download. The actual completed job log contains the decomposition output and confirms that every required output file existed before upload.
