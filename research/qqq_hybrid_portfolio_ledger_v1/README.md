# QQQ Hybrid Portfolio Ledger V1

Independent portfolio accounting layer for the QQQ Hybrid deployment project.

## Purpose

This app answers a different question from the V3 Strategy Decision Terminal:

> What do I actually own, what did it cost, what is it worth now, and what profit/loss came from the recorded transactions?

It does not alter the Original Hybrid policy and it does not generate a strategy signal by itself.

Architecture:

    Market / broker marks
            |
    Portfolio Ledger V1
      fills + cashflows
            |
    position / cost / P&L / NAV
            |
    optional read-only V3 bridge (future)

## Accounting contract

The user records transactions, not P&L:

- FILL: timestamp, symbol, asset type, BUY/SELL, quantity, fill price, multiplier, fees.
- CASHFLOW: deposit/withdrawal amount.
- MARK: current observable price per unit.

The engine derives:

- open position by symbol
- FIFO cost lots
- realized P&L
- unrealized P&L
- fees
- market value
- cash
- equity / NAV
- net P&L
- external cash flow

Option contracts use a multiplier of 100 by default. Shares use 1.

No entry or exit P&L is stored as user truth. It is derived from the recorded fills and marks.

## Period P&L

For a period with a valid starting valuation:

    period P&L = ending equity - starting equity - net external cash flow during period

A period return is only shown when the starting equity is known and non-zero.

For an arbitrary historical start date, the operator must provide the start-date marks for positions that were already held. Without those marks, the UI labels the period return as incomplete rather than fabricating a number.

## P&L and strategy signals are intentionally separate

Portfolio profit does not change the strategy signal.

The V3 engine remains the source of truth for:

    BUY / HOLD / REDUCE
    frozen Original Hybrid policy
    current -> target -> action

Ledger V1 is the source of truth for:

    actual recorded position
    cost basis
    cash
    NAV
    realized / unrealized P&L

A future bridge may display a V3 recommendation next to actual portfolio state, but must not re-implement or silently modify V3 policy.

## Safety

- signal / accounting support only
- no broker order submission
- append-only transaction journal
- no DELETE transaction API
- corrections should be represented by a compensating transaction
- live marks are advisory MTM, never edited into historical fills

## Local run (Windows CMD)

    cd C:\path\to\brush-timber-mountain-brook\research\qqq_hybrid_portfolio_ledger_v1
    RUN.cmd

Then open:

    http://127.0.0.1:8790

Futu OpenD is optional. With futu-api installed and OpenD on 127.0.0.1:11111, the app can request live marks for the exact codes recorded in the ledger. QQQ/VXX also have a Yahoo fallback.

## Current V1 boundary

Implemented now:

- transaction journal
- FIFO accounting
- current NAV / P&L
- period P&L with explicit start marks
- live mark endpoint
- import/export JSON in the browser
- read-only V3 decision bridge
- defensible QQQ / VXX actual-vs-target reconciliation
- explicit option position identity with campaign / spread / leg metadata
- deterministic option spread pairing
- server-side validation of event and identity metadata

### Position identity contract

Option spread pairing is never inferred from contract names, strikes, quantities, or nearby fills.

An option fill may carry:

    positionIdentity: {
      campaignId?: "...",
      spreadId: "...",
      legRole: "LONG" | "SHORT",
      strategyRole?: "..."
    }

The same spreadId is the only binding between legs. A spread is PAIRED only when exactly one active LONG contract and one active SHORT contract remain and their absolute open quantities match. Identity also records whether that spread has ever reached a valid paired state; a history that merely ends with both legs at zero but was never paired remains INCOMPLETE.

Visible non-paired states are:

- INCOMPLETE: one leg is missing
- IMBALANCED: both legs exist but quantities differ
- MULTI_CONTRACT: more than one active contract remains on either leg role

This layer is identity / pairing only. It does not attribute P&L by spread, does not infer credit vs debit, and does not modify V3 policy. V3 option targets remain UNMAPPED in reconciliation because the current target is a budget percentage, not an explicit spread count.

Not yet wired:

- broker fill ingestion
- corporate-action normalization
- tax-lot/reporting rules
- time-weighted return series
- money-weighted IRR

These stay separate increments so accounting, identity, and future attribution can each be tested independently.

### Spread-level P&L Attribution V1

For a spread that is PAIRED, attribution uses the explicit spreadId + legRole identity and keeps each option leg's accounting independent.

Per leg:

    realizedPnl = FIFO realized P&L from fills in that spread leg
    unrealizedPnl = current mark P&L on the remaining open lots
    totalPnl = realizedPnl + unrealizedPnl - fees

For the currently open exposure:

    entryDebit  = cost of active LONG/open debit lots
    entryCredit = proceeds of active SHORT/open credit lots
    netEntryCredit = entryCredit - entryDebit
    currentValue = signed marked market value of both legs

currentValue is valuation context only. It is never used as the spread P&L calculation. For a rolled spread, historical realized P&L and fees from closed contracts remain in the spread totals, while current value and unrealized P&L continue to use only active contracts.

Closed quantities remain represented through realized P&L; they are not silently folded back into the current entry premium.

Attribution is blocked as INCOMPLETE when the position identity is not paired, active LONG / SHORT direction is inconsistent with the declared leg role, or a current mark required for either active leg is missing.

No spread-level P&L is fabricated in those states.

This increment remains accounting-only. It does not modify V3 BUY / HOLD / REDUCE logic and has no broker-order path.

### Campaign / Period Portfolio Performance V1

The performance layer has two separate authorities:

- portfolio period P&L comes from Ledger V1 periodMetrics
- campaign period P&L comes from the change in cumulative identified-spread P&L between start and end

For each identified spread:

    periodPnl = cumulativeEndPnl - cumulativeStartPnl

A spread not present at the start has startPnl = 0. A fully closed spread remains attributable at period end as CLOSED, retaining realized P&L. If start or end attribution is incomplete, that spread produces no period P&L.

Campaign rows group spreads by explicit campaignId. Missing campaignId is shown as UNASSIGNED rather than silently assigned to a strategy.

The campaign layer reports:

    startPnl
    current / end cumulative P&L
    period P&L
    spread count
    paired / closed / incomplete counts

It does not calculate a campaign return percentage because a defensible campaign capital denominator is not part of the current ledger contract. The existing portfolio period return remains the only return percentage shown.

Scope is explicitly IDENTIFIED_OPTION_SPREADS_ONLY. Campaign-attributed option P&L is not expected to equal whole-portfolio P&L when QQQ core, VXX, or unassigned option activity is outside the campaign identity scope.

### Campaign Timeline / Attribution History V1

The timeline is an event-sourced accounting history for explicit option fills. It records state transitions such as:

    OPEN → ROLL_START / ROLL_COMPLETE → PARTIAL_CLOSE → FULL_CLOSE

The transition detector observes the explicit campaignId / spreadId / legRole identity and never infers a spread from contract similarity. A roll is visible as a multi-contract transition followed by a paired state on the new active contract. Partial and full closes are based on the remaining active quantities; a fully closed spread remains CLOSED for attribution.

For each timeline point the ledger can report:

    realized net P&L = cumulative realized spread P&L - cumulative fees
    total P&L = realized + unrealized - fees, only when a point-in-time mark exists
    campaign cumulative realized net P&L

Historical marks are supplied as an optional ordered series of { timestamp, marks }. At each event the timeline carries the latest observation forward per symbol, but never across the event timestamp. Each timeline row also exposes per-symbol mark observation timestamps so a carried mark cannot be mistaken for a fresh quote. Current live marks are never reused to backfill history. Without a historical mark, an open spread shows realized-only accounting and total P&L remains unpriced rather than fabricated.

This increment is accounting-only. It does not alter V3 strategy policy, BUY / HOLD / REDUCE logic, reconciliation targets, or broker routing.


### Edge-case audit contract

The accounting audit locks the following conservative rules:

- Partial close: the two legs may temporarily become IMBALANCED between fills; the next valid PAIRED state is classified from the last stable paired quantity, so a one-unit reduction across two fills is still recorded as PARTIAL_CLOSE.
- Roll: a new contract may create MULTI_CONTRACT / ROLL_START before the old contract closes. Historical realized P&L and fees from the closed leg remain attributable to the same spreadId after ROLL_COMPLETE.
- Multi-spread campaign: independent spreadIds under one campaign aggregate only when every identified spread has complete period attribution. One incomplete spread blocks the campaign aggregate rather than partially fabricating a campaign number; complete spread rows remain individually attributable.
- Incomplete history: a spread that never reached a valid paired state is not promoted to CLOSED merely because both active quantities later reach zero. Its spread and timeline P&L remain unpriced.
- Historical marks: mark observations are carried forward per symbol. Only observations timestamped at or before the event can be used; future marks never leak backward.

These rules are accounting-only and do not modify V3 strategy policy, reconciliation, BUY / HOLD / REDUCE logic, or broker routing.
