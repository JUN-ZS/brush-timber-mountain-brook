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
- read-only V3 bridge status placeholder

Not yet wired:

- automatic V3 decision retrieval
- broker fill ingestion
- corporate-action normalization
- tax-lot/reporting rules
- time-weighted return series
- money-weighted IRR

Those are separate increments so accounting correctness can be tested before adding integrations.
