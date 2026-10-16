# QQQ FAR CALL Incremental-Value Study V2

**Status:** pre-registered descriptive decomposition; research-only; no strategy approval.

## Purpose

Separate the observed QQQ FAR CALL overlay effect into four measurable components before considering any policy change:

A. Entry economics and selection.
B. Daily marking and capital occupancy.
C. Existing exit lifecycle.
D. Source completeness and paired incremental value.

This is a post-processing layer over the pinned listed-contract replay. It does not alter the replay's contract picker, sizing, DTE, stop/take-profit thresholds, trade timing, source data, or quote-validity policy. It is not an attempt to find parameters that turn the result positive.

## Inputs and provenance

The tool consumes the summary JSON, trade CSV, event CSV, and daily CSV produced by the existing Windows self-hosted replay workflow. It refuses to proceed if any required file is absent.

The underlying options are EOD quote snapshots from a public preservation mirror. The README-reported observation time is 16:00 US Eastern; exact quote tick timestamps remain unverified. Bid/Ask side prices are not exchange-confirmed fills. Commissions and per-leg slippage remain hypothetical scenarios.

The requested date window ends 2025-12-31, while available pinned option-chain rows stop on 2025-12-15. The source gap must remain visible. The reviewed 2018–2025 period is development evidence and is not a virgin holdout.

## Four measurement dimensions

### A — Entry economics

For each separately identified budget/cost scenario, report observed gross credit, modeled entry costs, net credit, quantities, opens, skips/blocks and their logged reasons, plus entry quote-width categories. Entry events and closed trades are reported separately so that cost-dependent selection and size changes are not hidden.

No quote-width category is converted into a new entry filter.

### B — Marking and capital occupancy

Recompute overlay-minus-no-call NAV differences only on dates where both NAV values are present. Report matched and unmatched observations, first/last matched dates, observed minimum/maximum and positive-mark-day share. Also report position-open-but-unmarked sessions, pending exit sessions, and mark statuses.

Missing values are excluded, never interpolated or forward-filled. The paired difference is a descriptive marked-value diagnostic, not a complete return series. No CAGR, daily MTM MaxDD, Sharpe or ES95 is computed.

### C — Existing exit lifecycle

Group the closed-trade ledger by the existing exit reason. Show trade count, net cash-flow P&L, mean holding duration, deferred-quote sessions, and exit basis (observed EOD exit-side quotes versus intrinsic-value settlement proxy). This is descriptive attribution: group outcomes do not establish that the exit reason caused a loss and do not authorize new thresholds.

### D — Completeness and incremental value

Preserve expected sessions, chain sessions, source endpoint, terminal source-gap dates, mark gaps, unresolved/open positions, ledger reconciliation, and the paired NAV diagnostics.

The zero-slippage/zero-commission arm using the source max-loss budget is the baseline screen. If both its closed-trade net P&L and last observed paired NAV difference are negative, record FAILS_CURRENT_BASE_SCREEN. This screen is not an investment-performance approval gate: even a non-negative screen does not pass data-timing, fill, completeness, or untouched-holdout requirements.

## Ledger identity and hard check

For every closed trade with complete cash-flow fields, independently recompute:

gross entry credit cash − entry execution costs − gross exit debit cash − exit execution costs = recorded net P&L.

Any discrepancy greater than USD 0.01 fails the ledger check. A missing component blocks the check. Scenario arms are never added together.

## Cost comparison

Slippage per leg remains 0.00 / 0.025 / 0.05 / 0.10 USD and commission remains 0.00 / 0.65 USD per contract per side, per the existing replay contract. Cost-arm differences are not pure fee subtraction: net credit, quantities, entry eligibility, trade count and terminal positions may change under each independent replay.

The two budget meanings remain separately labelled: 0.8% NAV maximum-loss budget and legacy 1.2% NAV credit budget. They are not comparable risk budgets.

## Disposition rule

- The current Run #36 paired-NAV result is negative under every source max-loss tested cost arm. It is a warning against integration, not a complete strategy return series.
- If this decomposition continues to show negative economics after ledger checks, keep FAR CALL out of Frozen Original Hybrid; do not search thresholds to rescue it.
- If any integrity check fails, stop interpreting the decomposition until the defect is resolved.
- If the result ever appears positive, source completeness, executable timestamps/fills, contract integrity, full capital accounting, and genuinely untouched future/prospective validation are still required.
- This study never changes main, Frozen Original Hybrid, live sizing, or broker-order permissions.

## Reproduction

The existing Windows self-hosted replay runs first. It then runs the new stdlib-only decomposition against the replay outputs and writes JSON, Markdown, and CSV diagnostics under:

artifacts/qqq_far_call_replay/incremental_decomposition/

The summary is also emitted to the GitHub Actions step summary. Artifact upload remains non-blocking because the repository Actions artifact quota has previously been exhausted; the workflow separately verifies that all required output files exist before upload.
