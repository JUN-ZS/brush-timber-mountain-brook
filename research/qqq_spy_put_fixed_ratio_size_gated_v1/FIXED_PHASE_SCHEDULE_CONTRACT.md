# QQQ/SPY PUT Fixed-Anchor Start-Phase Robustness Contract V1

## Question
Does the apparent result for no-filter QQQ LONG PUT 1 : SPY SHORT PUT 3 entered every five common QQQ/SPY underlying sessions remain similar when the scheduled cadence is anchored correctly?

## Frozen candidate
- Entry filter: none.
- Fixed ratio: one long QQQ put and three short SPY puts per selected cohort.
- Cadence: every five common underlying sessions.
- Test five anchor phases: 0, 1, 2, 3 and 4 session indices from the first common underlying session.
- Overlapping active cohorts enabled; total account cash, NAV, broker margin and assignment capacity remain outside this stage.
- Same-expiry options; DTE 30–60 targeting 45; absolute Delta target 0.25; existing source identity pins and quote-size checks.
- Conservative marks: QQQ long enters at Ask/exits at Bid; SPY short enters at Bid/exits at Ask.
- Costs: $0.05 per option share per side slippage and $0.65 per contract per side commission.
- Source/data horizon remains 2018-03-01 through 2025-12-15, with common option observations through 2025-12-12.

## Fixed schedule semantics
- Scheduled session indices are immutable: `phase + k × stride`, where `k = 0, 1, 2, ...` and the index remains inside the observed common-session array.
- Every scheduled slot is accounted for exactly once as either a selected signal pair or a skipped scheduled slot.
- A missing chain, missing underlying close, filter rejection, absent eligible common-expiry pair, active-cohort gate or previous entry still pending must not move any later scheduled slot.
- A slot missed because a prior entry remains pending is recorded as skipped; this V1 does not queue multiple pending entry attempts.
- If a pair is selected but the next-session entry quote/size checks fail, the original selected contract continues to follow the engine's existing deferred-entry rule until expiry/source end. Later schedule slots remain fixed and are independently logged.
- Selected signals and entry skips carry their original scheduled session index. Audit fails if any selected signal or scheduled skip is off the requested phase modulo five.
- The audit requires `scheduled opportunities = selected signal pairs + skipped scheduled slots` for each phase.

## Outputs and checks
- Five independently executed full replays, each with its own contract selection, signal dates, entry attempts and exit accounting.
- Per-phase source manifests, summaries, entry cohort ledger, trade episode ledger, entry-skip ledger and scheduled-slot skip ledger.
- Reconciled 1Y, 3Y, 5Y, calendar-year and exit-policy comparisons.
- Phase-anchor integrity checks must pass before the report is considered complete.

## Limits
- EOD quote-side accounting is not verified live execution.
- P&L is additive fixed-size cohort P&L, not compounded account NAV.
- Gross SPY short-put assignment obligation is not broker margin.
- This is in-sample robustness analysis, not forward validation or an execution recommendation.
